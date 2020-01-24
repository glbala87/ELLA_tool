from typing import DefaultDict, List, Set, Union, Type
import datetime
import pytz
from collections import defaultdict

from sqlalchemy import tuple_, literal, func
from sqlalchemy.orm import joinedload

from vardb.datamodel import user, assessment, sample, genotype, allele, workflow, gene, annotation

from api import schemas, ApiError, ConflictError
from datalayer import (
    AlleleFilter,
    AlleleDataLoader,
    AssessmentCreator,
    AlleleReportCreator,
    SnapshotCreator,
    queries,
)
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


def override_interpretation(
    session, user_id, workflow_allele_id: int = None, workflow_analysis_id: int = None
):

    interpretation = _get_latest_interpretation(session, workflow_allele_id, workflow_analysis_id)

    # Get user by username
    new_user = session.query(user.User).filter(user.User.id == user_id).one()

    if interpretation.status != "Ongoing":
        raise ApiError("Cannot reassign interpretation that is not 'Ongoing'.")

    # db will throw exception if user_id is not a valid id
    # since it's a foreign key
    interpretation.user = new_user
    return interpretation


def start_interpretation(
    session, user_id, data, workflow_allele_id: int = None, workflow_analysis_id: int = None
):

    interpretation = _get_latest_interpretation(session, workflow_allele_id, workflow_analysis_id)

    # Get user by username
    start_user = session.query(user.User).filter(user.User.id == user_id).one()

    if not interpretation:
        interpretation_model = _get_interpretation_model(workflow_allele_id, workflow_analysis_id)
        interpretation = interpretation_model()
        if workflow_allele_id is not None:
            interpretation.allele_id = workflow_allele_id
        elif workflow_analysis_id is not None:
            interpretation.analysis_id = workflow_analysis_id

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

    if workflow_analysis_id is not None:
        analysis = (
            session.query(sample.Analysis).filter(sample.Analysis.id == workflow_analysis_id).one()
        )
        interpretation.genepanel = analysis.genepanel

    elif workflow_allele_id is not None:
        # For allele workflow, the user can choose genepanel context for each interpretation
        interpretation.genepanel_name = data["gp_name"]
        interpretation.genepanel_version = data["gp_version"]
    else:
        raise RuntimeError("Missing id argument")

    return interpretation


def mark_interpretation(
    session, workflow_status, data, workflow_allele_id: int = None, workflow_analysis_id: int = None
):
    """
    Marks (and copies) an interpretation for a new workflow_status,
    creating Snapshot objects to record history.
    """
    interpretation = _get_latest_interpretation(session, workflow_allele_id, workflow_analysis_id)
    interpretation_model = _get_interpretation_model(workflow_allele_id, workflow_analysis_id)

    if not interpretation.status == "Ongoing":
        raise ApiError(
            "Cannot mark as '{}' when latest interpretation is not 'Ongoing'".format(
                workflow_status
            )
        )

    SnapshotCreator(session).insert_from_data(
        data["allele_ids"],
        _get_snapshotcreator_mode(workflow_allele_id, workflow_analysis_id),
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


def marknotready_interpretation(session, data, workflow_analysis_id: int = None):
    return mark_interpretation(
        session, "Not ready", data, workflow_analysis_id=workflow_analysis_id
    )


def markinterpretation_interpretation(
    session, data, workflow_allele_id: int = None, workflow_analysis_id: int = None
):
    return mark_interpretation(
        session,
        "Interpretation",
        data,
        workflow_allele_id=workflow_allele_id,
        workflow_analysis_id=workflow_analysis_id,
    )


def markreview_interpretation(
    session, data, workflow_allele_id: int = None, workflow_analysis_id: int = None
):
    return mark_interpretation(
        session,
        "Review",
        data,
        workflow_allele_id=workflow_allele_id,
        workflow_analysis_id=workflow_analysis_id,
    )


def markmedicalreview_interpretation(session, data, workflow_analysis_id: int = None):
    return mark_interpretation(
        session, "Medical review", data, workflow_analysis_id=workflow_analysis_id
    )


def reopen_interpretation(
    session, workflow_allele_id: int = None, workflow_analysis_id: int = None
):

    interpretation = _get_latest_interpretation(session, workflow_allele_id, workflow_analysis_id)
    interpretation_model = _get_interpretation_model(workflow_allele_id, workflow_analysis_id)

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


def finalize_allele(
    session,
    user_id: int,
    usergroup_id: int,
    data,
    user_config,
    workflow_allele_id: int = None,
    workflow_analysis_id: int = None,
):
    """
    Finalizes a single allele.

    This will create any [alleleassessment|referenceassessments|allelereport] objects for the provided allele id (in data).

    **Only works for workflows with a `Ongoing` current interpretation**
    """

    assert (
        workflow_allele_id
        or workflow_analysis_id
        and not (workflow_allele_id and workflow_analysis_id)
    )

    interpretation = _get_latest_interpretation(session, workflow_allele_id, workflow_analysis_id)

    if not interpretation.status == "Ongoing":
        raise ApiError("Cannot finalize allele when latest interpretation is not 'Ongoing'")

    if workflow_allele_id:
        assert data["allele_id"] == workflow_allele_id

    if workflow_analysis_id:
        assert (
            session.query(allele.Allele)
            .join(allele.Allele.genotypes, sample.Sample, sample.Analysis)
            .filter(
                sample.Analysis.id == workflow_analysis_id, allele.Allele.id == data["allele_id"]
            )
            .count()
            == 1
        )

    # Check annotation data
    latest_annotation_id = (
        session.query(annotation.Annotation.id)
        .filter(
            annotation.Annotation.allele_id == data["allele_id"],
            annotation.Annotation.date_superceeded.is_(None),
        )
        .scalar()
    )
    if not latest_annotation_id == data["annotation_id"]:
        raise ApiError(
            "Cannot finalize: provided annotation_id does not match latest annotation id"
        )

    latest_customannotation_id = (
        session.query(annotation.CustomAnnotation.id)
        .filter(
            annotation.CustomAnnotation.allele_id == data["allele_id"],
            annotation.CustomAnnotation.date_superceeded.is_(None),
        )
        .scalar()
    )
    if not latest_customannotation_id == data.get("custom_annotation_id"):
        raise ApiError(
            "Cannot finalize: provided custom_annotation_id does not match latest annotation id"
        )

    # Check that we can finalize allele
    workflow_type = "allele" if workflow_allele_id else "analysis"
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
    assessment_result = AssessmentCreator(session).create_from_data(
        user_id,
        usergroup_id,
        data["allele_id"],
        data["annotation_id"],
        data["custom_annotation_id"],
        interpretation.genepanel_name,
        interpretation.genepanel_version,
        data["alleleassessment"],
        data["referenceassessments"],
        analysis_id=workflow_analysis_id,
    )

    alleleassessment = None
    if assessment_result.created_alleleassessment:
        session.add(assessment_result.created_alleleassessment)
    else:
        if assessment_result.created_referenceassessments:
            raise ApiError(
                "Trying to create referenceassessments for allele, while not also creating alleleassessment"
            )

    if assessment_result.created_referenceassessments:
        session.add_all(assessment_result.created_referenceassessments)

    # Create/reuse allelereports
    report_result = AlleleReportCreator(session).create_from_data(
        user_id,
        usergroup_id,
        data["allele_id"],
        data["allelereport"],
        alleleassessment,
        analysis_id=workflow_analysis_id,
    )

    if report_result.created_allelereport:
        session.add(report_result.created_allelereport)

    session.flush()

    # Ensure that we created either alleleassessment or allelereport, otherwise finalization
    # makes no sense.
    assert assessment_result.created_alleleassessment or report_result.created_allelereport

    # Create entry in interpretation log
    il_data = {"user_id": user_id}
    if workflow_allele_id:
        il_data["alleleinterpretation_id"] = interpretation.id
    if workflow_analysis_id:
        il_data["analysisinterpretation_id"] = interpretation.id
    if assessment_result.created_alleleassessment:
        il_data["alleleassessment_id"] = assessment_result.created_alleleassessment.id
    if report_result.created_allelereport:
        il_data["allelereport_id"] = report_result.created_allelereport.id

    il = workflow.InterpretationLog(**il_data)
    session.add(il)

    return {
        "allelereport": schemas.AlleleReportSchema().dump(report_result.allelereport).data,
        "alleleassessment": schemas.AlleleAssessmentSchema()
        .dump(assessment_result.alleleassessment)
        .data,
        "referenceassessments": schemas.ReferenceAssessmentSchema()
        .dump(assessment_result.referenceassessments, many=True)
        .data,
    }


def finalize_workflow(
    session,
    user_id: int,
    data,
    user_config,
    workflow_allele_id: int = None,
    workflow_analysis_id: int = None,
):
    """
    Finalizes an interpretation.

    This sets the allele/analysis' current interpretation's status to `Done`,
    and finalized to True.

    The provided data is recorded in a snapshot to be able to present user
    with the view at end of interpretation round.

    **Only works for analyses with a `Ongoing` current interpretation**
    """

    interpretation = _get_latest_interpretation(session, workflow_allele_id, workflow_analysis_id)

    if not interpretation.status == "Ongoing":
        raise ApiError("Cannot finalize when latest interpretation is not 'Ongoing'")

    # Sanity checks
    alleleassessment_allele_ids = set(
        session.query(assessment.AlleleAssessment.allele_id)
        .filter(assessment.AlleleAssessment.id.in_(data["alleleassessment_ids"]))
        .scalar_all()
    )

    allelereport_allele_ids = set(
        session.query(assessment.AlleleReport.allele_id)
        .filter(assessment.AlleleReport.id.in_(data["allelereport_ids"]))
        .scalar_all()
    )

    assert alleleassessment_allele_ids - set(data["allele_ids"]) == set()
    assert allelereport_allele_ids - set(data["allele_ids"]) == set()

    # Check that we can finalize
    # There are different criterias deciding when finalization is allowed
    workflow_type = "allele" if workflow_allele_id else "analysis"

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

    if workflow_type == "analysis":
        assert "technical_allele_ids" in data and "notrelevant_allele_ids" in data

    if workflow_type == "allele":
        assert "technical_allele_ids" not in data and "notrelevant_allele_ids" not in data
        assert (
            "allow_technical" not in finalize_requirements
            and "allow_notrelevant" not in finalize_requirements
            and "allow_unclassified" not in finalize_requirements
        )

    if not finalize_requirements.get("allow_technical") and data.get("technical_allele_ids"):
        raise ApiError("allow_technical is set to false, but some allele ids are marked technical")

    if not finalize_requirements.get("allow_notrelevant") and data.get("notrelevant_allele_ids"):
        raise ApiError(
            "allow_notrelevant is set to false, but some allele ids are marked not relevant"
        )

    unclassified_allele_ids = (
        set(data["allele_ids"])
        - set(data.get("notrelevant_allele_ids", []))
        - set(data.get("technical_allele_ids", []))
        - alleleassessment_allele_ids
    )
    if not finalize_requirements.get("allow_unclassified") and unclassified_allele_ids:
        raise ApiError(
            "allow_unclassified is set to false, but some allele ids are missing classification"
        )

    # Create interpretation snapshot objects
    if workflow_type == "analysis":
        excluded_allele_ids = data["excluded_allele_ids"]
    else:
        excluded_allele_ids = None

    SnapshotCreator(session).insert_from_data(
        data["allele_ids"],
        _get_snapshotcreator_mode(workflow_allele_id, workflow_analysis_id),
        interpretation,
        data["annotation_ids"],
        data["custom_annotation_ids"],
        data["alleleassessment_ids"],
        data["allelereport_ids"],
        excluded_allele_ids=excluded_allele_ids,
    )

    # Update interpretation
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

    def get_collision_interpretation_model_ids(
        model: Union[Type[workflow.AnalysisInterpretation], Type[workflow.AlleleInterpretation]],
        model_attr_id: str,
    ) -> Set[int]:
        """
        Get all analysis/allele ids for workflows that have an interpretation that may contain
        work that is not commited.
        Criteria:
        1. Include if more than one interpretation and latest is not finalized.
        The first criterion (more than one) is due to single interpretations
        may be in 'Not started' status and we don't want to include those.
        2. In addition, include all Ongoing interpretations. These will naturally
        contain uncommited work. This case is partly covered in 1. above, but not
        for single interpretations.
        """

        more_than_one = (
            session.query(getattr(model, model_attr_id))
            .group_by(getattr(model, model_attr_id))
            .having(func.count(getattr(model, model_attr_id)) > 1)
            .subquery()
        )

        not_finalized = queries.workflow_by_status(
            session, model, model_attr_id, finalized=False
        ).subquery()

        ongoing = set(
            queries.workflow_by_status(session, model, model_attr_id, status="Ongoing").scalar_all()
        )

        more_than_one_not_finalized = set(
            session.query(getattr(more_than_one.c, model_attr_id))
            .join(
                not_finalized,
                getattr(not_finalized.c, model_attr_id) == getattr(more_than_one.c, model_attr_id),
            )
            .distinct()
            .scalar_all()
        )

        return ongoing | more_than_one_not_finalized

    workflow_analysis_ids = get_collision_interpretation_model_ids(
        workflow.AnalysisInterpretation, "analysis_id"
    )

    # Exclude "ourself" if applicable
    if analysis_id in workflow_analysis_ids:
        workflow_analysis_ids.remove(analysis_id)

    # Get all ongoing analyses connected to provided allele ids
    # For analyses we exclude alleles with valid alleleassessments
    wf_analysis_allele_ids = (
        session.query(
            workflow.AnalysisInterpretation.user_id,
            workflow.AnalysisInterpretation.workflow_status,
            allele.Allele.id,
            workflow.AnalysisInterpretation.analysis_id,
        )
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
        )
        .distinct(workflow.AnalysisInterpretation.analysis_id, allele.Allele.id)
        .order_by(
            workflow.AnalysisInterpretation.analysis_id,
            allele.Allele.id,
            workflow.AnalysisInterpretation.date_created.desc(),
        )
    ).all()

    # Allele workflow
    workflow_allele_ids = get_collision_interpretation_model_ids(
        workflow.AlleleInterpretation, "allele_id"
    )

    # Exclude "ourself" if applicable
    if allele_id in workflow_allele_ids:
        workflow_allele_ids.remove(allele_id)

    wf_allele_allele_ids = (
        session.query(
            workflow.AlleleInterpretation.user_id,
            workflow.AlleleInterpretation.workflow_status,
            workflow.AlleleInterpretation.allele_id,
            literal(None).label("analysis_id"),
        )
        .filter(
            workflow.AlleleInterpretation.allele_id.in_(workflow_allele_ids),
            workflow.AlleleInterpretation.allele_id.in_(allele_ids),
        )
        .distinct(workflow.AlleleInterpretation.allele_id)
        .order_by(
            workflow.AlleleInterpretation.allele_id,
            workflow.AlleleInterpretation.date_created.desc(),
        )
    ).all()

    # Preload the users
    user_ids = set([a.user_id for a in wf_allele_allele_ids + wf_analysis_allele_ids])
    users = session.query(user.User).filter(user.User.id.in_(user_ids)).all()
    dumped_users = schemas.UserSchema().dump(users, many=True).data

    # Preload the analysis names
    analysis_ids = [a.analysis_id for a in wf_analysis_allele_ids]
    analysis_id_names = (
        session.query(sample.Analysis.id, sample.Analysis.name)
        .filter(sample.Analysis.id.in_(analysis_ids))
        .all()
    )
    analysis_name_by_id = {a.id: a.name for a in analysis_id_names}

    collisions = list()
    for wf_type, wf_entries in [
        ("allele", wf_allele_allele_ids),
        ("analysis", wf_analysis_allele_ids),
    ]:
        for user_id, workflow_status, allele_id, analysis_id in wf_entries:
            # If an workflow is in review, it will have no user assigned...
            dumped_user = next((u for u in dumped_users if u["id"] == user_id), None)
            collisions.append(
                {
                    "type": wf_type,
                    "user": dumped_user,
                    "allele_id": allele_id,
                    "analysis_name": analysis_name_by_id.get(analysis_id),
                    "analysis_id": analysis_id,
                    "workflow_status": workflow_status,
                }
            )

    return collisions


def get_interpretationlog(session, user_id, allele_id=None, analysis_id=None):

    assert (allele_id or analysis_id) and not (allele_id and analysis_id)

    if allele_id:
        workflow_id = allele_id
    if analysis_id:
        workflow_id = analysis_id

    assert workflow_id

    latest_interpretation = _get_latest_interpretation(session, allele_id, analysis_id)
    # If there's no interpretations, there cannot be any logs either
    if latest_interpretation is None:
        return {"logs": [], "users": []}

    logs = (
        session.query(workflow.InterpretationLog)
        .join(_get_interpretation_model(allele_id, analysis_id))
        .filter(_get_interpretation_model_field(allele_id, analysis_id) == workflow_id)
        .order_by(workflow.InterpretationLog.date_created)
    )

    id_field = "alleleinterpretation_id" if allele_id else "analysisinterpretation_id"
    editable = {
        l.id: getattr(l, id_field) == latest_interpretation.id
        and (not latest_interpretation.finalized or latest_interpretation.status != "Done")
        and l.user_id == user_id
        and l.message is not None
        for l in logs
    }
    loaded_logs = schemas.InterpretationLogSchema().dump(logs, many=True).data

    for loaded_log in loaded_logs:
        loaded_log["editable"] = editable[loaded_log["id"]]

    # AlleleAssessments and AlleleReports are special, we need to load more data
    alleleassessment_ids = set(
        [l["alleleassessment_id"] for l in loaded_logs if l["alleleassessment_id"]]
    )
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

    allelereport_ids = set([l["allelereport_id"] for l in loaded_logs if l["allelereport_id"]])
    allelereports = (
        session.query(assessment.AlleleReport.id, assessment.AlleleReport.allele_id)
        .filter(assessment.AlleleReport.id.in_(allelereport_ids))
        .all()
    )
    allelereports_by_id = {a.id: a for a in allelereports}

    allele_ids.extend([a.allele_id for a in allelereports])
    annotation_genepanel = queries.annotation_transcripts_genepanel(
        session,
        [(latest_interpretation.genepanel_name, latest_interpretation.genepanel_version)],
        allele_ids=allele_ids,
    ).subquery()

    allele_hgvs = (
        session.query(
            allele.Allele.id,
            allele.Allele.chromosome,
            allele.Allele.vcf_pos,
            allele.Allele.vcf_ref,
            allele.Allele.vcf_alt,
            annotation_genepanel.c.annotation_symbol,
            annotation_genepanel.c.annotation_hgvsc,
        )
        .outerjoin(annotation_genepanel, annotation_genepanel.c.allele_id == allele.Allele.id)
        .filter(allele.Allele.id.in_(allele_ids))
        .all()
    )

    formatted_allele_by_id: DefaultDict[int, List] = defaultdict(list)
    for a in allele_hgvs:
        if a.annotation_hgvsc:
            formatted_allele_by_id[a.id].append(f"{a.annotation_symbol} {a.annotation_hgvsc}")
        else:
            formatted_allele_by_id[a.id].append(
                f"{a.chromosome}:{a.vcf_pos} {a.vcf_ref}>{a.vcf_alt}"
            )

    for loaded_log in loaded_logs:
        loaded_log["alleleassessment"] = {}
        loaded_log["allelereport"] = {}
        alleleassessment_id = loaded_log.pop("alleleassessment_id", None)
        if alleleassessment_id:
            log_aa = alleleassessments_by_id[alleleassessment_id]
            loaded_log["alleleassessment"].update(
                {
                    "allele_id": log_aa.allele_id,
                    "hgvsc": sorted(formatted_allele_by_id[log_aa.allele_id]),
                    "classification": log_aa.classification,
                    "previous_classification": previous_alleleassessment_classifications_by_id[
                        log_aa.previous_assessment_id
                    ]
                    if log_aa.previous_assessment_id
                    else None,
                }
            )
        allelereport_id = loaded_log.pop("allelereport_id", None)
        if allelereport_id:
            log_ar = allelereports_by_id[allelereport_id]
            loaded_log["allelereport"].update(
                {
                    "allele_id": log_ar.allele_id,
                    "hgvsc": sorted(formatted_allele_by_id[log_ar.allele_id]),
                }
            )

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
