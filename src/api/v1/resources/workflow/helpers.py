import datetime
import itertools
import pytz
from collections import defaultdict

from sqlalchemy import tuple_, or_
from sqlalchemy.orm import joinedload

from vardb.datamodel import user, assessment, sample, genotype, allele, workflow, gene

from api import schemas, ApiError, ConflictError
from api.allelefilter.allelefilter import AlleleFilter
from api.util.assessmentcreator import AssessmentCreator
from api.util.allelereportcreator import AlleleReportCreator
from api.util.snapshotcreator import SnapshotCreator
from api.util.alleledataloader import AlleleDataLoader
from api.util.interpretationdataloader import InterpretationDataLoader
from api.util import queries
from api.util.util import get_nested


def _check_interpretation_input(allele, analysis):
    if allele is None and analysis is None:
        raise RuntimeError("One of arguments allele or analysis is required.")


def _get_interpretation_model(allele, analysis):
    if allele is not None:
        return workflow.AlleleInterpretation
    if analysis is not None:
        return workflow.AnalysisInterpretation


def _get_interpretation_model_field(allele, analysis):
    if allele is not None:
        return workflow.AlleleInterpretation.allele_id
    if analysis is not None:
        return workflow.AnalysisInterpretation.analysis_id


def _get_interpretationsnapshot_model(allele, analysis):
    if allele is not None:
        return workflow.AlleleInterpretationSnapshot
    if analysis is not None:
        return workflow.AnalysisInterpretationSnapshot


def _get_interpretationsnapshot_field(allele, analysis):
    if allele is not None:
        return workflow.AlleleInterpretationSnapshot.alleleinterpretation_id
    if analysis is not None:
        return workflow.AnalysisInterpretationSnapshot.analysisinterpretation_id


def _get_snapshotcreator_mode(allele, analysis):
    if allele is not None:
        return "allele"
    elif analysis is not None:
        return "analysis"


def _get_interpretation_id(alleleinterpretation_id, analysisinterpretation_id):
    if alleleinterpretation_id is not None:
        return alleleinterpretation_id
    if analysisinterpretation_id is not None:
        return analysisinterpretation_id


def _get_latest_interpretation(session, allele_id, analysis_id):
    model = _get_interpretation_model(allele_id, analysis_id)
    field = _get_interpretation_model_field(allele_id, analysis_id)
    if allele_id is not None:
        model_id = allele_id
    elif analysis_id is not None:
        model_id = analysis_id
    return (
        session.query(model).filter(field == model_id).order_by(model.date_created.desc()).first()
    )


def _get_interpretation_schema(interpretation):
    if isinstance(interpretation, workflow.AnalysisInterpretation):
        return schemas.AnalysisInterpretationSchema
    elif isinstance(interpretation, workflow.AlleleInterpretation):
        return schemas.AlleleInterpretationSchema
    else:
        raise RuntimeError("Unknown interpretation class type.")


def get_alleles(
    session,
    allele_ids,
    genepanels,
    alleleinterpretation_id=None,
    analysisinterpretation_id=None,
    current_allele_data=False,
):
    """
    Loads all alleles for an interpretation. The interpretation model is dynamically chosen
    based on which argument (alleleinterpretation_id, analysisinterpretation_id) is given.

    If current_allele_data is True, load newest allele data instead of allele data
    at time of interpretation snapshot.

    By default, the latest connected data is loaded (e.g. latest annotations, assessments etc).
    However, if the interpretation is marked as 'Done', it's context is loaded from the snapshot,
    so any annotation, alleleassessments etc for each allele will be what was stored
    at the time of finishing the interpretation.
    """

    _check_interpretation_input(alleleinterpretation_id, analysisinterpretation_id)

    alleles = session.query(allele.Allele).filter(allele.Allele.id.in_(allele_ids)).all()

    # Get interpretation to get genepanel and check status
    interpretation_id = _get_interpretation_id(alleleinterpretation_id, analysisinterpretation_id)
    interpretation_model = _get_interpretation_model(
        alleleinterpretation_id, analysisinterpretation_id
    )
    interpretationsnapshot_model = _get_interpretationsnapshot_model(
        alleleinterpretation_id, analysisinterpretation_id
    )
    interpretationsnapshot_field = _get_interpretationsnapshot_field(
        alleleinterpretation_id, analysisinterpretation_id
    )

    interpretation = (
        session.query(interpretation_model)
        .filter(
            interpretation_model.id == interpretation_id,
            tuple_(interpretation_model.genepanel_name, interpretation_model.genepanel_version).in_(
                (gp.name, gp.version) for gp in genepanels
            ),
        )
        .one()
    )

    link_filter = (
        None
    )  # In case of loading specific data rather than latest available for annotation, custom_annotation etc..
    if not current_allele_data and interpretation.status == "Done":
        # Serve using context data from snapshot
        snapshots = (
            session.query(interpretationsnapshot_model)
            .filter(interpretationsnapshot_field == interpretation.id)
            .all()
        )

        link_filter = {
            "annotation_id": [s.annotation_id for s in snapshots if s.annotation_id is not None],
            "customannotation_id": [
                s.customannotation_id for s in snapshots if s.customannotation_id is not None
            ],
            "alleleassessment_id": [
                s.alleleassessment_id for s in snapshots if s.alleleassessment_id is not None
            ],
            "allelereport_id": [
                s.allelereport_id for s in snapshots if s.allelereport_id is not None
            ],
        }

        # For historical referenceassessments, they should all be connected to the alleleassessments used
        ra_ids = (
            session.query(assessment.ReferenceAssessment.id)
            .join(assessment.AlleleAssessment.referenceassessments)
            .filter(assessment.AlleleAssessment.id.in_(link_filter["alleleassessment_id"]))
            .all()
        )
        link_filter["referenceassessment_id"] = [i[0] for i in ra_ids]

    # Only relevant for analysisinterpretation: Include the genotype for connected samples
    analysis_id = None
    if analysisinterpretation_id is not None:
        analysis_id = interpretation.analysis_id

    kwargs = {
        "include_annotation": True,
        "include_custom_annotation": True,
        "genepanel": interpretation.genepanel,
        "analysis_id": analysis_id,
        "link_filter": link_filter,
    }

    return AlleleDataLoader(session).from_objs(alleles, **kwargs)


def load_genepanel_for_allele_ids(session, allele_ids, gp_name, gp_version):
    """
    Loads genepanel data using input allele_ids as filter
    for what transcripts and phenotypes to include.
    """
    genepanel = (
        session.query(gene.Genepanel)
        .filter(gene.Genepanel.name == gp_name, gene.Genepanel.version == gp_version)
        .one()
    )

    annotation_transcripts_genepanel = queries.annotation_transcripts_genepanel(
        session, [(gp_name, gp_version)]
    ).subquery()

    transcripts = (
        session.query(gene.Transcript)
        .options(joinedload(gene.Transcript.gene))
        .join(gene.Genepanel.transcripts)
        .filter(
            gene.Transcript.transcript_name
            == annotation_transcripts_genepanel.c.genepanel_transcript,
            annotation_transcripts_genepanel.c.allele_id.in_(allele_ids),
        )
        .all()
    )

    phenotypes = (
        session.query(gene.Phenotype)
        .options(joinedload(gene.Phenotype.gene))
        .join(gene.genepanel_phenotype)
        .filter(
            gene.Transcript.transcript_name
            == annotation_transcripts_genepanel.c.genepanel_transcript,
            annotation_transcripts_genepanel.c.allele_id.in_(allele_ids),
            gene.Phenotype.gene_id == gene.Transcript.gene_id,
            gene.genepanel_phenotype.c.genepanel_name == gp_name,
            gene.genepanel_phenotype.c.genepanel_version == gp_version,
        )
    )

    genepanel_data = schemas.GenepanelSchema().dump(genepanel).data
    genepanel_data["transcripts"] = schemas.TranscriptFullSchema().dump(transcripts, many=True).data
    genepanel_data["phenotypes"] = schemas.PhenotypeFullSchema().dump(phenotypes, many=True).data
    return genepanel_data


def update_interpretation(
    session, user_id, data, alleleinterpretation_id=None, analysisinterpretation_id=None
):
    """
    Updates the current interpretation inplace.

    **Only allowed for interpretations that are `Ongoing`**

    """

    def check_update_allowed(interpretation, user_id, patch_data):
        if interpretation.status == "Done":
            raise ConflictError("Cannot PATCH interpretation with status 'DONE'")
        elif interpretation.status == "Not started":
            raise ConflictError(
                "Interpretation not started. Call it's analysis' start action to begin interpretation."
            )

        # Check that user is same as before
        if interpretation.user_id:
            if interpretation.user_id != user_id:
                current_user = session.query(user.User).filter(user.User.id == user_id).one()
                interpretation_user = (
                    session.query(user.User).filter(user.User.id == interpretation.user_id).one()
                )
                raise ConflictError(
                    "Interpretation owned by {} {} cannot be updated by other user ({} {})".format(
                        interpretation_user.first_name,
                        interpretation.user.last_name,
                        current_user.first_name,
                        current_user.last_name,
                    )
                )

    interpretation_id = _get_interpretation_id(alleleinterpretation_id, analysisinterpretation_id)
    interpretation_model = _get_interpretation_model(
        alleleinterpretation_id, analysisinterpretation_id
    )

    interpretation = (
        session.query(interpretation_model)
        .filter(interpretation_model.id == interpretation_id)
        .one()
    )

    check_update_allowed(interpretation, user_id, data)

    # Add current state to history if new state is different:
    if data["state"] != interpretation.state:
        session.add(
            workflow.InterpretationStateHistory(
                alleleinterpretation_id=alleleinterpretation_id,
                analysisinterpretation_id=analysisinterpretation_id,
                state=interpretation.state,
                user_id=user_id,
            )
        )
    # Overwrite state fields with new values
    interpretation.state = data["state"]
    interpretation.user_state = data["user_state"]
    interpretation.date_last_update = datetime.datetime.now(pytz.utc)
    return interpretation


def get_interpretation(
    session, genepanels, user_id, alleleinterpretation_id=None, analysisinterpretation_id=None
):
    interpretation_id = _get_interpretation_id(alleleinterpretation_id, analysisinterpretation_id)
    interpretation_model = _get_interpretation_model(
        alleleinterpretation_id, analysisinterpretation_id
    )

    interpretation = (
        session.query(interpretation_model)
        .filter(
            interpretation_model.id == interpretation_id,
            tuple_(interpretation_model.genepanel_name, interpretation_model.genepanel_version).in_(
                (gp.name, gp.version) for gp in genepanels
            ),
        )
        .one()
    )
    schema = _get_interpretation_schema(interpretation)
    obj = schema().dump(interpretation).data
    return obj


def get_interpretations(
    session, genepanels, user_id, allele_id=None, analysis_id=None, filterconfig_id=None
):

    interpretation_model = _get_interpretation_model(allele_id, analysis_id)
    interpretation_model_field = _get_interpretation_model_field(allele_id, analysis_id)

    if allele_id is not None:
        model_id = allele_id
    elif analysis_id is not None:
        model_id = analysis_id

    interpretations = (
        session.query(interpretation_model)
        .filter(
            interpretation_model_field == model_id,
            tuple_(interpretation_model.genepanel_name, interpretation_model.genepanel_version).in_(
                (gp.name, gp.version) for gp in genepanels
            ),
        )
        .order_by(interpretation_model.id)
        .all()
    )

    if interpretations:
        schema = _get_interpretation_schema(interpretations[0])
        loaded_interpretations = schema().dump(interpretations, many=True).data
    else:
        loaded_interpretations = list()

    return loaded_interpretations


def override_interpretation(session, user_id, allele_id=None, analysis_id=None):

    interpretation = _get_latest_interpretation(session, allele_id, analysis_id)

    # Get user by username
    new_user = session.query(user.User).filter(user.User.id == user_id).one()

    if interpretation.status != "Ongoing":
        raise ApiError("Cannot reassign interpretation that is not 'Ongoing'.")

    # db will throw exception if user_id is not a valid id
    # since it's a foreign key
    interpretation.user = new_user
    return interpretation


def start_interpretation(session, user_id, data, allele_id=None, analysis_id=None):

    interpretation = _get_latest_interpretation(session, allele_id, analysis_id)

    # Get user by username
    start_user = session.query(user.User).filter(user.User.id == user_id).one()

    if not interpretation:
        interpretation_model = _get_interpretation_model(allele_id, analysis_id)
        interpretation = interpretation_model()
        if allele_id is not None:
            interpretation.allele_id = allele_id
        elif analysis_id is not None:
            interpretation.analysis_id = analysis_id

        session.add(interpretation)

    elif interpretation.status != "Not started":
        raise ApiError(
            "Cannot start existing interpretation where status = {}".format(interpretation.status)
        )

    # db will throw exception if user_id is not a valid id
    # since it's a foreign key
    interpretation.user = start_user
    interpretation.status = "Ongoing"
    interpretation.date_last_update = datetime.datetime.now(pytz.utc)

    if analysis_id is not None:
        analysis = session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).one()
        interpretation.genepanel = analysis.genepanel

    elif allele_id is not None:
        # For allele workflow, the user can choose genepanel context for each interpretation
        interpretation.genepanel_name = data["gp_name"]
        interpretation.genepanel_version = data["gp_version"]
    else:
        raise RuntimeError("Missing id argument")

    return interpretation


def mark_interpretation(session, workflow_status, data, allele_id=None, analysis_id=None):
    """
    Marks (and copies) an interpretation for a new workflow_status,
    creating Snapshot objects to record history.
    """
    interpretation = _get_latest_interpretation(session, allele_id, analysis_id)
    interpretation_model = _get_interpretation_model(allele_id, analysis_id)

    if not interpretation.status == "Ongoing":
        raise ApiError(
            "Cannot mark as '{}' when latest interpretation is not 'Ongoing'".format(
                workflow_status
            )
        )

    SnapshotCreator(session).insert_from_data(
        data["allele_ids"],
        _get_snapshotcreator_mode(allele_id, analysis_id),
        interpretation,
        data["annotation_ids"],
        data["custom_annotation_ids"],
        data["alleleassessment_ids"],
        data["allelereport_ids"],
        excluded_allele_ids=data.get("excluded_allele_ids"),
    )

    interpretation.status = "Done"
    interpretation.finalized = False
    interpretation.date_last_update = datetime.datetime.now(pytz.utc)

    # Create next interpretation
    interpretation_next = interpretation_model.create_next(interpretation)
    interpretation_next.workflow_status = workflow_status
    session.add(interpretation_next)

    return interpretation, interpretation_next


def marknotready_interpretation(session, data, analysis_id=None):
    return mark_interpretation(session, "Not ready", data, analysis_id=analysis_id)


def markinterpretation_interpretation(session, data, allele_id=None, analysis_id=None):
    return mark_interpretation(
        session, "Interpretation", data, allele_id=allele_id, analysis_id=analysis_id
    )


def markreview_interpretation(session, data, allele_id=None, analysis_id=None):
    return mark_interpretation(
        session, "Review", data, allele_id=allele_id, analysis_id=analysis_id
    )


def markmedicalreview_interpretation(session, data, analysis_id=None):
    return mark_interpretation(session, "Medical review", data, analysis_id=analysis_id)


def reopen_interpretation(session, allele_id=None, analysis_id=None):

    interpretation = _get_latest_interpretation(session, allele_id, analysis_id)
    interpretation_model = _get_interpretation_model(allele_id, analysis_id)

    if interpretation is None:
        raise ApiError(
            "There are no existing interpretations for this item. Use the start action instead."
        )

    if not interpretation.status == "Done":
        raise ApiError("Interpretation is already 'Not started' or 'Ongoing'. Cannot reopen.")

    # Create next interpretation
    interpretation_next = interpretation_model.create_next(interpretation)
    interpretation_next.workflow_status = (
        interpretation.workflow_status
    )  # TODO: Where do we want to go?
    session.add(interpretation_next)

    return interpretation, interpretation_next


def finalize_allele(session, user_id, data, user_config, allele_id=None, analysis_id=None):
    """
    Finalizes a single allele within an analysis.

    This will create any [alleleassessment|referenceassessment|allelereport] objects for the provided allele id.

    For each assessment/report, there are two cases:
    - 'reuse=False' or reuse is missing: a new assessment/report is created in the database using the data given.
    - 'reuse=True' The id of an existing assessment/report is expected in 'presented_assessment_id'
        or 'presented_report_id'.


    **Only works for analyses with a `Ongoing` current interpretation**
    """

    assert allele_id or analysis_id

    interpretation = _get_latest_interpretation(session, allele_id, analysis_id)

    if not interpretation.status == "Ongoing":
        raise ApiError("Cannot finalize allele when latest interpretation is not 'Ongoing'")

    if allele_id:
        assert data["allele_id"] == allele_id

    if analysis_id:
        assert (
            session.query(allele.Allele)
            .join(allele.Allele.genotypes, sample.Sample, sample.Analysis)
            .filter(sample.Analysis.id == analysis_id, allele.Allele.id == data["allele_id"])
            .count()
            == 1
        )

    # Check that we can finalize allele
    workflow_type = "allele" if allele_id else "analysis"
    finalize_requirements = get_nested(
        user_config, ["workflows", workflow_type, "finalize_requirements"]
    )
    if finalize_requirements.get("workflow_status"):
        if interpretation.workflow_status not in finalize_requirements["workflow_status"]:
            raise ApiError(
                "Cannot finalize: Interpretation's workflow status is in one of required ones: {}".format(
                    ", ".join(finalize_requirements["workflow_status"])
                )
            )

    # Create/reuse assessments
    grouped_assessments = AssessmentCreator(session).create_from_data(
        user_id,
        data["allele_id"],
        data["annotation_id"],
        data["alleleassessment"],
        custom_annotation_id=data["custom_annotation_id"],
        referenceassessments=data["referenceassessments"],
        analysis_id=analysis_id,
    )

    alleleassessment = None
    if grouped_assessments["alleleassessment"]["created"]:
        session.add(grouped_assessments["alleleassessment"]["created"])
        alleleassessment = grouped_assessments["alleleassessment"]["created"]
    else:
        alleleassessment = grouped_assessments["alleleassessment"]["reused"]

    reused_referenceassessments = grouped_assessments["referenceassessments"]["reused"]
    created_referenceassessments = grouped_assessments["referenceassessments"]["created"]

    session.add_all(created_referenceassessments)

    # Create/reuse allelereports
    allelereport, allelereport_reused = AlleleReportCreator(session).create_from_data(
        user_id, data["allele_id"], data["allelereport"], alleleassessment
    )

    if not allelereport_reused:
        session.add(allelereport)

    all_referenceassessments = reused_referenceassessments + created_referenceassessments

    session.flush()

    # Create entry in interpretation log
    il_data = {"user_id": user_id, "alleleassessment_id": alleleassessment.id}
    if allele_id:
        il_data["alleleinterpretation_id"] = interpretation.id
    if analysis_id:
        il_data["analysisinterpretation_id"] = interpretation.id

    il = workflow.InterpretationLog(**il_data)
    session.add(il)

    return {
        "allelereport": schemas.AlleleReportSchema().dump(allelereport).data,
        "alleleassessment": schemas.AlleleAssessmentSchema().dump(alleleassessment).data,
        "referenceassessments": schemas.ReferenceAssessmentSchema()
        .dump(all_referenceassessments, many=True)
        .data,
    }


def finalize_interpretation(session, user_id, data, user_config, allele_id=None, analysis_id=None):
    """
    Finalizes an interpretation.

    This sets the allele/analysis' current interpretation's status to `Done`
    and if.

    The provided data is recorded in a snapshot to be able to present user
    with the view at end of interpretation round.

    **Only works for analyses with a `Ongoing` current interpretation**
    """

    interpretation = _get_latest_interpretation(session, allele_id, analysis_id)

    if not interpretation.status == "Ongoing":
        raise ApiError("Cannot finalize when latest interpretation is not 'Ongoing'")

    # Check that we can finalize
    # There are different criterias deciding when finalization is allowed

    # exempted_classification_allele_ids = set()  # allele ids that don't need classification
    # assert reused_allele_ids & created_allele_ids == set()
    #
    workflow_type = "allele" if allele_id else "analysis"
    #
    if workflow_type == "analysis":
        excluded_allele_ids = data["excluded_allele_ids"]
    else:
        excluded_allele_ids = None
    #
    # finalize_requirements = get_nested(
    #    user_config, ["workflows", workflow_type, "finalize_requirements"]
    # )
    # if finalize_requirements.get("workflow_status"):
    #    if interpretation.workflow_status not in finalize_requirements["workflow_status"]:
    #        raise ApiError(
    #            "Cannot finalize: Interpretation's workflow status is in one of required ones: {}".format(
    #                ", ".join(finalize_requirements["workflow_status"])
    #            )
    #        )
    #
    # if finalize_requirements.get("allow_technical"):
    #    if "technical_allele_ids" not in data:
    #        raise ApiError(
    #            "Missing required key 'technical_allele_ids' when finalized requirement allow_technical is true"
    #        )
    #    exempted_classification_allele_ids.update(set(data["technical_allele_ids"]))
    #
    # if finalize_requirements.get("allow_notrelevant"):
    #    if "notrelevant_allele_ids" not in data:
    #        raise ApiError(
    #            "Missing required key 'notrelevant_allele_ids' when finalized requirement allow_notrelevant is true"
    #        )
    #    exempted_classification_allele_ids.update(set(data["notrelevant_allele_ids"]))
    #
    ## If no "unclassified" are allowed, check that all allele ids minus the
    ## exempted ones have a classification
    # if not finalize_requirements.get("allow_unclassified"):
    #    needs_classification = set(data["allele_ids"]) - exempted_classification_allele_ids
    #    missing_classification = needs_classification - (created_allele_ids | reused_allele_ids)
    #    if missing_classification:
    #        raise ApiError(
    #            "Missing alleleassessments for allele ids {}".format(
    #                ",".join(sorted(list([str(m) for m in missing_classification])))
    #            )
    #        )
    #
    # Create interpretation snapshot objects
    SnapshotCreator(session).insert_from_data(
        data["allele_ids"],
        _get_snapshotcreator_mode(allele_id, analysis_id),
        interpretation,
        data["annotation_ids"],
        data["custom_annotation_ids"],
        data["alleleassessment_ids"],
        data["allelereport_ids"],
        excluded_allele_ids=excluded_allele_ids,
    )

    # Update interpretation and return data
    interpretation.status = "Done"
    interpretation.finalized = True
    interpretation.date_last_update = datetime.datetime.now(pytz.utc)


def get_genepanels(session, allele_ids, user=None):
    """
    Get all genepanels overlapping the regions of the provided allele_ids.

    Is user is provided, the genepanels are restricted to the user group's panels.
    """
    if user:
        # TODO: This can turn into an perforamance issue
        gp_keys = sorted([(g.name, g.version) for g in user.group.genepanels if g.official])
    else:
        gp_keys = (
            session.query(gene.Genepanel.name, gene.Genepanel.version)
            .filter(gene.Genepanel.official.is_(True))
            .all()
        )

    allele_genepanels = queries.allele_genepanels(session, gp_keys, allele_ids=allele_ids)
    allele_genepanels = allele_genepanels.subquery()

    candidate_genepanels = (
        session.query(allele_genepanels.c.name, allele_genepanels.c.version).distinct().all()
    )

    # TODO: Sort by previously used interpretations

    result = schemas.GenepanelSchema().dump(candidate_genepanels, many=True)
    return result


def get_workflow_allele_collisions(session, allele_ids, analysis_id=None, allele_id=None):
    """
    Check for possible collisions in other allele or analysis workflows,
    which happens to have overlapping alleles with the ids given in 'allele_ids'.

    If you're checking a specific workflow, include the analysis_id or allele_id argument
    to specify which workflow to exclude from the check.
    For instance, if you want to check analysis 3, having e.g. 20 alleles, you don't want
    to include analysis 3 in the collision check as it's not informative
    to see a collision with itself. You would pass in analysis_id=3 to exclude it.

    :note: Alleles with valid alleleassessments are excluded from causing collision.
    """

    # Remove if you need to check collisions in general
    assert (analysis_id is not None) or (
        allele_id is not None
    ), "No object passed to compute collisions with"

    # Get all analysis workflows that are either Ongoing, or waiting for review
    # i.e having not only 'Not started' interpretations or not only 'Done' interpretations.
    workflow_analysis_ids = (
        session.query(sample.Analysis.id)
        .join(workflow.AnalysisInterpretation)
        .filter(
            or_(
                sample.Analysis.id.in_(queries.workflow_analyses_review_not_started(session)),
                sample.Analysis.id.in_(
                    queries.workflow_analyses_medicalreview_not_started(session)
                ),
                sample.Analysis.id.in_(queries.workflow_analyses_ongoing(session)),
            ),
            workflow.AnalysisInterpretation.status != "Done",
        )
    )

    # Exclude "ourself" if applicable
    if analysis_id is not None:
        workflow_analysis_ids = workflow_analysis_ids.filter(sample.Analysis.id != analysis_id)

    # Get all ongoing analyses connected to provided allele ids
    # For analyses we exclude alleles with valid alleleassessments
    wf_analysis_allele_ids = (
        session.query(workflow.AnalysisInterpretation.user_id, allele.Allele.id)
        .join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            workflow.AnalysisInterpretation,
        )
        .filter(
            sample.Analysis.id.in_(workflow_analysis_ids),
            allele.Allele.id.in_(allele_ids),
            ~allele.Allele.id.in_(queries.allele_ids_with_valid_alleleassessments(session)),
            workflow.AnalysisInterpretation.status != "Done",
        )
        .distinct()
    )

    # Get all allele ids for ongoing allele workflows matching provided allele_ids
    wf_allele_allele_ids = (
        session.query(
            workflow.AlleleInterpretation.user_id, workflow.AlleleInterpretation.allele_id
        )
        .filter(
            or_(
                workflow.AlleleInterpretation.allele_id.in_(
                    queries.workflow_alleles_review_not_started(session)
                ),
                workflow.AlleleInterpretation.allele_id.in_(
                    queries.workflow_alleles_ongoing(session)
                ),
            ),
            workflow.AlleleInterpretation.status != "Done",
            workflow.AlleleInterpretation.allele_id.in_(allele_ids),
        )
        .distinct()
    )

    # Exclude "ourself" if applicable
    if allele_id is not None:
        wf_allele_allele_ids = wf_allele_allele_ids.filter(
            workflow.AlleleInterpretation.allele_id != allele_id
        )

    wf_analysis_allele_ids = wf_analysis_allele_ids.all()
    wf_allele_allele_ids = wf_allele_allele_ids.all()

    # Preload the users
    user_ids = set([a[0] for a in wf_allele_allele_ids + wf_analysis_allele_ids])
    users = session.query(user.User).filter(user.User.id.in_(user_ids)).all()
    dumped_users = schemas.UserSchema().dump(users, many=True).data

    collisions = list()
    for wf_type, wf_entries in [
        ("allele", wf_allele_allele_ids),
        ("analysis", wf_analysis_allele_ids),
    ]:
        for user_id, allele_id in wf_entries:
            # If an workflow is in review, it will have no user assigned...
            dumped_user = next((u for u in dumped_users if u["id"] == user_id), None)
            collisions.append({"type": wf_type, "user": dumped_user, "allele_id": allele_id})

    return collisions


def get_interpretationlog(session, user_id, allele_id=None, analysis_id=None):

    assert (allele_id or analysis_id) and not (allele_id and analysis_id)

    if allele_id:
        workflow_id = allele_id
    if analysis_id:
        workflow_id = analysis_id

    assert workflow_id

    logs = (
        session.query(workflow.InterpretationLog)
        .join(_get_interpretation_model(allele_id, analysis_id))
        .filter(_get_interpretation_model_field(allele_id, analysis_id) == workflow_id)
    )

    latest_interpretation = _get_latest_interpretation(session, allele_id, analysis_id)

    field = "alleleinterpretation_id" if allele_id else "analysisinterpretation_id"
    editable = {
        l.id: getattr(l, field) == latest_interpretation.id
        and (not latest_interpretation.finalized or latest_interpretation.status != "Done")
        and l.user_id == user_id
        and l.message is not None
        for l in logs
    }
    loaded_logs = schemas.InterpretationLogSchema().dump(logs, many=True).data

    for loaded_log in loaded_logs:
        loaded_log["editable"] = editable[loaded_log["id"]]

    # AlleleAssessments are special, we need to load more data
    alleleassessment_ids = set([l["alleleassessment_id"] for l in loaded_logs])
    alleleassessments = (
        session.query(
            assessment.AlleleAssessment.id,
            assessment.AlleleAssessment.allele_id,
            assessment.AlleleAssessment.classification,
            assessment.AlleleAssessment.previous_assessment_id,
        )
        .filter(assessment.AlleleAssessment.id.in_(alleleassessment_ids))
        .all()
    )
    alleleassessments_by_id = {a.id: a for a in alleleassessments}

    previous_assessment_ids = [
        a.previous_assessment_id for a in alleleassessments if a.previous_assessment_id
    ]
    previous_alleleassessment_classifications = (
        session.query(assessment.AlleleAssessment.id, assessment.AlleleAssessment.classification)
        .filter(assessment.AlleleAssessment.id.in_(previous_assessment_ids))
        .all()
    )
    previous_alleleassessment_classifications_by_id = {
        a.id: a.classification for a in previous_alleleassessment_classifications
    }

    allele_ids = [a.allele_id for a in alleleassessments]
    annotation_genepanel = queries.annotation_transcripts_genepanel(
        session,
        [(latest_interpretation.genepanel_name, latest_interpretation.genepanel_version)],
        allele_ids=allele_ids,
    ).subquery()

    allele_hgvs = session.query(
        annotation_genepanel.c.allele_id,
        annotation_genepanel.c.annotation_symbol,
        annotation_genepanel.c.annotation_hgvsc,
    ).all()

    allele_hgvs_by_id = defaultdict(list)
    for a in allele_hgvs:
        allele_hgvs_by_id[a.allele_id].append(a)

    for loaded_log in loaded_logs:
        if loaded_log["alleleassessment_id"]:
            log_aa = alleleassessments_by_id[loaded_log["alleleassessment_id"]]
            loaded_log["alleleassessment"] = {
                "allele_id": log_aa.allele_id,
                "hgvsc": [f"{a[1]} {a[2]}" for a in sorted(allele_hgvs_by_id[log_aa.allele_id])],
                "classification": log_aa.classification,
                "previous_classification": previous_alleleassessment_classifications_by_id[
                    log_aa.previous_assessment_id
                ]
                if log_aa.previous_assessment_id
                else None,
            }
        del loaded_log["alleleassessment_id"]

    # Load all relevant user data
    user_ids = set([l["user_id"] for l in loaded_logs])
    users = session.query(user.User).filter(user.User.id.in_(user_ids)).all()

    loaded_users = schemas.UserSchema().dump(users, many=True).data

    return {"logs": loaded_logs, "users": loaded_users}


def create_interpretationlog(session, user_id, data, allele_id=None, analysis_id=None):

    assert (allele_id or analysis_id) and not (allele_id and analysis_id)
    if allele_id:
        if not data.get("warning_cleared") is None:
            raise ApiError("warning_cleared is not supported for alleles as they have no warnings")

    latest_interpretation = _get_latest_interpretation(session, allele_id, analysis_id)

    if not latest_interpretation:
        # Shouldn't be possible for an analysis
        assert not analysis_id
        assert allele_id

        latest_interpretation = workflow.AlleleInterpretation(
            allele_id=allele_id, workflow_status="Interpretation", status="Not started"
        )
        session.add(latest_interpretation)
        session.flush()

    if analysis_id:
        data["analysisinterpretation_id"] = latest_interpretation.id
    if allele_id:
        data["alleleinterpretation_id"] = latest_interpretation.id

    data["user_id"] = user_id

    il = workflow.InterpretationLog(**data)

    session.add(il)
    return il


def patch_interpretationlog(
    session, user_id, interpretationlog_id, message, allele_id=None, analysis_id=None
):

    il = (
        session.query(workflow.InterpretationLog)
        .filter(workflow.InterpretationLog.id == interpretationlog_id)
        .one()
    )

    if il.user_id != user_id:
        raise ApiError("Cannot edit interpretation log, item doesn't match user's id.")

    latest_interpretation = _get_latest_interpretation(session, allele_id, analysis_id)

    match = False
    if allele_id:
        match = il.alleleinterpretation_id == latest_interpretation.id
    elif analysis_id:
        match = il.analysisinterpretation_id == latest_interpretation.id

    if not match:
        raise ApiError("Can only edit entries created for latest interpretation id.")

    il.message = message


def delete_interpretationlog(
    session, user_id, interpretationlog_id, allele_id=None, analysis_id=None
):

    il = (
        session.query(workflow.InterpretationLog)
        .filter(workflow.InterpretationLog.id == interpretationlog_id)
        .one()
    )

    if il.user_id != user_id:
        raise ApiError("Cannot delete interpretation log, item doesn't match user's id.")

    latest_interpretation = _get_latest_interpretation(session, allele_id, analysis_id)

    match = False
    if allele_id:
        match = il.alleleinterpretation_id == latest_interpretation.id
    elif analysis_id:
        match = il.analysisinterpretation_id == latest_interpretation.id

    if not match:
        raise ApiError("Can only delete entries created for latest interpretation id.")

    session.delete(il)


def get_filtered_alleles(session, interpretation, filter_config_id=None):
    """
    Return filter results for interpretation.
    - If AlleleInterpretation, return only allele id for interpretation (no alleles excluded)
    - If AnalysisInterpretation:
        - filter_config_id not provided: Return snapshot results. Requires interpretation to be 'Done'-
        - filter_config_id provided: Run filter on analysis, and return results.
    """
    if isinstance(interpretation, workflow.AlleleInterpretation):
        return [interpretation.allele_id], None

    elif isinstance(interpretation, workflow.AnalysisInterpretation):

        if filter_config_id is None:
            if interpretation.status != "Done":
                raise RuntimeError("Interpretation is not done, and no filter config is provided.")

            if not interpretation.snapshots:
                raise RuntimeError("Missing snapshots for interpretation.")

            categories = {
                "CLASSIFICATION": "classification",
                "FREQUENCY": "frequency",
                "REGION": "region",
                "POLYPYRIMIDINE": "ppy",
                "GENE": "gene",
                "QUALITY": "quality",
                "CONSEQUENCE": "consequence",
                "SEGREGATION": "segregation",
                "INHERITANCEMODEL": "inheritancemodel",
            }

            allele_ids = []
            excluded_allele_ids = {k: [] for k in list(categories.values())}

            for snapshot in interpretation.snapshots:
                if snapshot.filtered in categories:
                    excluded_allele_ids[categories[snapshot.filtered]].append(snapshot.allele_id)
                else:
                    allele_ids.append(snapshot.allele_id)

            return allele_ids, excluded_allele_ids
        else:
            analysis_id = interpretation.analysis_id
            analysis_allele_ids = (
                session.query(allele.Allele.id)
                .join(genotype.Genotype.alleles, sample.Sample, sample.Analysis)
                .filter(sample.Analysis.id == analysis_id)
                .scalar_all()
            )

            af = AlleleFilter(session)
            filtered_alleles = af.filter_analysis(
                filter_config_id, analysis_id, analysis_allele_ids
            )

            return (filtered_alleles["allele_ids"], filtered_alleles["excluded_allele_ids"])
    else:
        raise RuntimeError("Unknown type {}".format(interpretation))
