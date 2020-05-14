from typing import Sequence, Tuple
import datetime
import pytz
from sqlalchemy import or_, and_, tuple_, func, text, literal_column
from vardb.datamodel import sample, workflow, assessment, allele, genotype, gene
from vardb.datamodel.annotationshadow import AnnotationShadowTranscript

from api.util import filterconfig_requirements
from api.config import config


def valid_alleleassessments_filter(session):
    """
    Filter for including alleleassessments that have valid (not outdated) classifications.
    """
    classification_filters = list()
    # Create classification filters, filtering on classification and optionally outdated threshold
    for option in config["classification"]["options"]:
        internal_filters = [assessment.AlleleAssessment.classification == option["value"]]
        if "outdated_after_days" in option:
            outdated_time = datetime.datetime.now(pytz.utc) - datetime.timedelta(
                days=option["outdated_after_days"]
            )
            internal_filters.append(assessment.AlleleAssessment.date_created > outdated_time)
        # Add our filter using and_
        classification_filters.append(and_(*internal_filters))
    return [or_(*classification_filters), assessment.AlleleAssessment.date_superceeded.is_(None)]


def allele_ids_with_valid_alleleassessments(session):
    """
    Query for all alleles that has no valid alleleassessments,
    as given by configuration's classification options.

    Different scenarios:
    - Allele has alleleassessment and it's not outdated
    - Allele has alleleassessment, but it's outdated
    - Allele has no alleleassessments at all.

    """
    return (
        session.query(allele.Allele.id)
        .join(assessment.AlleleAssessment)
        .filter(*valid_alleleassessments_filter(session))
    )


def workflow_by_status(
    session, model, model_id_attr, workflow_status=None, status=None, finalized=None
):
    """
    Fetches all allele_id/analysis_id where the last interpretation matches provided
    workflow status and/or status.

    :param model: AlleleInterpretation or AnalysisInterpretation
    :param model_id_attr: 'allele_id' or 'analysis_id'

    Query resembles something like this:
     SELECT s.id FROM (select DISTINCT ON (analysis_id) id, workflow_status, status
     from analysisinterpretation order by analysis_id, date_last_update desc) AS
     s where s.workflow_status = :status;

    Using DISTINCT ON and ORDER BY will select one row, giving us the latest interpretation workflow status.
    See https://www.postgresql.org/docs/10.0/static/sql-select.html#SQL-DISTINCT
    """

    if workflow_status is None and status is None and finalized is None:
        raise RuntimeError(
            "You must provide either 'workflow_status', 'status' or 'finalized' argument"
        )

    assert model_id_attr in ["allele_id", "analysis_id"]

    latest_interpretation = (
        session.query(
            getattr(model, model_id_attr), model.workflow_status, model.status, model.finalized
        )
        .order_by(getattr(model, model_id_attr), model.date_created.desc())
        .distinct(getattr(model, model_id_attr))  # DISTINCT ON
        .subquery()
    )

    filters = []
    if workflow_status:
        filters.append(latest_interpretation.c.workflow_status == workflow_status)
    if status:
        filters.append(latest_interpretation.c.status == status)
    if finalized is not None:
        if finalized:
            filters.append(latest_interpretation.c.finalized.is_(True))
        else:
            filters.append(
                or_(
                    latest_interpretation.c.finalized.is_(None),
                    latest_interpretation.c.finalized.is_(False),
                )
            )
    return session.query(
        getattr(latest_interpretation.c, model_id_attr).label(model_id_attr)
    ).filter(*filters)


def workflow_analyses_finalized(session):
    return workflow_by_status(
        session,
        workflow.AnalysisInterpretation,
        "analysis_id",
        workflow_status=None,
        status=None,
        finalized=True,
    )


def workflow_analyses_notready_not_started(session):
    return workflow_by_status(
        session,
        workflow.AnalysisInterpretation,
        "analysis_id",
        workflow_status="Not ready",
        status="Not started",
    )


def workflow_analyses_interpretation_not_started(session):
    return workflow_by_status(
        session,
        workflow.AnalysisInterpretation,
        "analysis_id",
        workflow_status="Interpretation",
        status="Not started",
    )


def workflow_analyses_review_not_started(session):
    return workflow_by_status(
        session,
        workflow.AnalysisInterpretation,
        "analysis_id",
        workflow_status="Review",
        status="Not started",
    )


def workflow_analyses_medicalreview_not_started(session):
    return workflow_by_status(
        session,
        workflow.AnalysisInterpretation,
        "analysis_id",
        workflow_status="Medical review",
        status="Not started",
    )


def workflow_analyses_ongoing(session):
    return workflow_by_status(
        session,
        workflow.AnalysisInterpretation,
        "analysis_id",
        workflow_status=None,
        status="Ongoing",
    )


def workflow_analyses_for_genepanels(session, genepanels):
    return session.query(sample.Analysis.id).filter(
        tuple_(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version).in_(
            (gp.name, gp.version) for gp in genepanels
        )
    )


def allele_ids_not_started_analyses(session):
    """
    Get all allele_ids for 'Not started' analyses in either
    'Not ready' or 'Interpretation' workflow status.
    """
    return (
        session.query(allele.Allele.id)
        .join(genotype.Genotype.alleles, sample.Sample, sample.Analysis)
        .filter(
            or_(
                sample.Analysis.id.in_(workflow_analyses_interpretation_not_started(session)),
                sample.Analysis.id.in_(workflow_analyses_notready_not_started(session)),
            )
        )
    )


def workflow_alleles_finalized(session):
    return workflow_by_status(
        session,
        workflow.AlleleInterpretation,
        "allele_id",
        workflow_status=None,
        status=None,
        finalized=True,
    )


def workflow_alleles_interpretation_not_started(session):
    return workflow_by_status(
        session,
        workflow.AlleleInterpretation,
        "allele_id",
        workflow_status="Interpretation",
        status="Not started",
    )


def workflow_alleles_review_not_started(session):
    return workflow_by_status(
        session,
        workflow.AlleleInterpretation,
        "allele_id",
        workflow_status="Review",
        status="Not started",
    )


def workflow_alleles_ongoing(session):
    return workflow_by_status(
        session, workflow.AlleleInterpretation, "allele_id", workflow_status=None, status="Ongoing"
    )


def workflow_alleles_for_genepanels(session, genepanels):
    """
    Get all allele_ids connected to given genepanels.

    They are either connected via an analysis or via an alleleinterpretation.
    """
    analysis_ids = workflow_analyses_for_genepanels(session, genepanels)

    allele_ids_for_analyses = (
        session.query(allele.Allele.id)
        .join(genotype.Genotype.alleles, sample.Sample, sample.Analysis)
        .filter(sample.Analysis.id.in_(analysis_ids))
        .distinct()
    )

    allele_ids_for_alleleinterpretation = (
        session.query(workflow.AlleleInterpretation.allele_id)
        .filter(
            tuple_(
                workflow.AlleleInterpretation.genepanel_name,
                workflow.AlleleInterpretation.genepanel_version,
            ).in_((gp.name, gp.version) for gp in genepanels)
        )
        .distinct()
    )

    return session.query(allele.Allele.id).filter(
        or_(
            allele.Allele.id.in_(allele_ids_for_analyses),
            allele.Allele.id.in_(allele_ids_for_alleleinterpretation),
        )
    )


def latest_interpretationlog_field(session, model, model_id_attr, field, model_ids=None):

    filters = [~getattr(workflow.InterpretationLog, field).is_(None)]
    if model_ids:
        filters.append(getattr(model, model_id_attr).in_(model_ids))
    return (
        session.query(getattr(model, model_id_attr), getattr(workflow.InterpretationLog, field))
        .join(workflow.InterpretationLog)
        .filter(*filters)
        .order_by(getattr(model, model_id_attr), workflow.InterpretationLog.date_created.desc())
        .distinct(getattr(model, model_id_attr))
    )


def workflow_analyses_priority(session, analysis_ids=None):
    return latest_interpretationlog_field(
        session, workflow.AnalysisInterpretation, "analysis_id", "priority", model_ids=analysis_ids
    )


def workflow_analyses_review_comment(session, analysis_ids=None):
    return latest_interpretationlog_field(
        session,
        workflow.AnalysisInterpretation,
        "analysis_id",
        "review_comment",
        model_ids=analysis_ids,
    )


def workflow_analyses_warning_cleared(session, analysis_ids=None):
    return latest_interpretationlog_field(
        session,
        workflow.AnalysisInterpretation,
        "analysis_id",
        "warning_cleared",
        model_ids=analysis_ids,
    )


def workflow_allele_priority(session, allele_ids=None):
    return latest_interpretationlog_field(
        session, workflow.AlleleInterpretation, "allele_id", "priority", model_ids=allele_ids
    )


def workflow_allele_review_comment(session, allele_ids=None):
    return latest_interpretationlog_field(
        session, workflow.AlleleInterpretation, "allele_id", "review_comment", model_ids=allele_ids
    )


def distinct_inheritance_hgnc_ids_for_genepanel(session, inheritance, gp_name, gp_version):
    """
    Fetches all hgnc_ids with _only_ {inheritance} phenotypes.

    e.g. only 'AD' or only 'AR'
    """
    # Get phenotypes having only one kind of inheritance
    # e.g. only 'AD' or only 'AR' etc...
    hgnc_ids = (
        session.query(gene.Phenotype.gene_id.label("hgnc_id"))
        .filter(
            gene.Phenotype.id == gene.genepanel_phenotype.c.phenotype_id,
            gene.genepanel_phenotype.c.genepanel_name == gp_name,
            gene.genepanel_phenotype.c.genepanel_version == gp_version,
        )
        .group_by(
            gene.genepanel_phenotype.c.genepanel_name,
            gene.genepanel_phenotype.c.genepanel_version,
            gene.Phenotype.gene_id,
        )
        .having(func.every(gene.Phenotype.inheritance == inheritance))
    )

    return hgnc_ids


def allele_genepanels(session, genepanel_keys, allele_ids=None):

    result = (
        session.query(
            allele.Allele.id.label("allele_id"),
            gene.Genepanel.name.label("name"),
            gene.Genepanel.version.label("version"),
        )
        .join(gene.Genepanel.transcripts)
        .filter(tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(genepanel_keys))
        .filter(
            allele.Allele.chromosome == gene.Transcript.chromosome,
            or_(
                and_(
                    allele.Allele.start_position >= gene.Transcript.tx_start,
                    allele.Allele.start_position <= gene.Transcript.tx_end,
                ),
                and_(
                    allele.Allele.open_end_position > gene.Transcript.tx_start,
                    allele.Allele.open_end_position < gene.Transcript.tx_end,
                ),
            ),
        )
    )

    if allele_ids is not None:
        result = result.filter(allele.Allele.id.in_(allele_ids) if allele_ids else False)

    return result


def annotation_transcripts_genepanel(
    session, genepanel_keys: Sequence[Tuple[str, str]], allele_ids: Sequence[int] = None
):

    """
    Returns a joined representation of annotation transcripts against genepanel transcripts
    for given genepanel_keys.

    genepanel_keys = [('HBOC', 'v01'), ('LYNCH', 'v01'), ...]

    Returns Query object, representing:
    -----------------------------------------------------------------------------
    | allele_id | name | version | annotation_transcript | genepanel_transcript |
    -----------------------------------------------------------------------------
    | 1         | HBOC | v01     | NM_000059.2           | NM_000059.3          |
    | 1         | HBOC | v01     | ENST00000530893       | ENST00000530893      |
      etc...

    :warning: If there is no match between the genepanel and the annotation,
    the allele won't be included in the result.
    Therefore, do _not_ use this as basis for inclusion of alleles in an analysis.
    Use it only to get annotation data for further filtering,
    where a non-match wouldn't exclude the allele in the analysis.
    """

    genepanel_transcripts = (
        session.query(
            gene.Genepanel.name,
            gene.Genepanel.version,
            gene.Transcript.transcript_name,
            gene.Transcript.gene_id,
        )
        .join(gene.Genepanel.transcripts)
        .filter(tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(genepanel_keys))
        .subquery()
    )

    # Column for version difference between annotation transcript and genepanel transcript
    tx_version = literal_column(
        "substring(split_part(transcript, '.', 2) FROM '^[0-9]+')::int"  # Fetch annotation transcript version: NM_00111.2 -> 2
        + "- 0.5*(split_part(transcript, '.', 2) !~ '^[0-9]+$')::int"  # Reduce version by 0.5 if version is not an integer, e.g. NM_00111.2_dupl18
    )

    # Join genepanel and annotation tables together, using transcript as key
    # and splitting out the version number of the transcript (if it has one)
    result = session.query(
        AnnotationShadowTranscript.allele_id.label("allele_id"),
        genepanel_transcripts.c.name.label("name"),
        genepanel_transcripts.c.version.label("version"),
        genepanel_transcripts.c.gene_id.label("genepanel_hgnc_id"),
        genepanel_transcripts.c.transcript_name.label("genepanel_transcript"),
        AnnotationShadowTranscript.transcript.label("annotation_transcript"),
        AnnotationShadowTranscript.symbol.label("annotation_symbol"),
        AnnotationShadowTranscript.hgnc_id.label("annotation_hgnc_id"),
        AnnotationShadowTranscript.hgvsc.label("annotation_hgvsc"),
        AnnotationShadowTranscript.hgvsp.label("annotation_hgvsp"),
    ).filter(
        # Matches e.g. NM_12345dabla.1 with NM_12345.2
        text("transcript_name like split_part(transcript, '.', 1) || '%'"),
        genepanel_transcripts.c.gene_id == AnnotationShadowTranscript.hgnc_id,
    )

    if allele_ids is not None:
        result = result.filter(
            AnnotationShadowTranscript.allele_id.in_(allele_ids) if allele_ids else False
        )

    # Order and distinct:
    # For each distinct allele, genepanel, gene and genepanel transcript, select either:
    # - The annotation transcript that matches the genepanel transcript on version
    # - Otherwise, select the latest available transcript version
    result = result.order_by(
        AnnotationShadowTranscript.allele_id,
        genepanel_transcripts.c.name,
        genepanel_transcripts.c.version,
        genepanel_transcripts.c.gene_id,
        genepanel_transcripts.c.transcript_name,
        (genepanel_transcripts.c.transcript_name == AnnotationShadowTranscript.transcript).desc(),
        tx_version.desc().nullslast(),
    )

    result = result.distinct(
        AnnotationShadowTranscript.allele_id,
        genepanel_transcripts.c.name,
        genepanel_transcripts.c.version,
        genepanel_transcripts.c.gene_id,
        genepanel_transcripts.c.transcript_name,
    )

    return result


def get_valid_filter_configs(session, usergroup_id, analysis_id=None):
    usergroup_filterconfigs = get_usergroup_filter_configs(session, usergroup_id)
    if analysis_id is None:
        if usergroup_filterconfigs.count() > 1:
            return usergroup_filterconfigs.filter(sample.FilterConfig.requirements == [])
        else:
            return usergroup_filterconfigs

    valid_ids = []
    for fc in usergroup_filterconfigs:
        reqs_fulfilled = []
        for req in fc.requirements:
            req_fulfilled = getattr(filterconfig_requirements, req["function"])(
                session, analysis_id, req["params"]
            )
            reqs_fulfilled.append(req_fulfilled)
        if all(reqs_fulfilled):
            valid_ids.append(fc.id)

    if not valid_ids:
        raise RuntimeError(
            "Unable to find any valid filter configs for analysis id {} and usergroup id {}".format(
                analysis_id, usergroup_id
            )
        )

    return usergroup_filterconfigs.filter(sample.FilterConfig.id.in_(valid_ids))


def get_usergroup_filter_configs(session, usergroup_id):
    return (
        session.query(sample.FilterConfig)
        .join(sample.UserGroupFilterConfig)
        .filter(
            sample.UserGroupFilterConfig.usergroup_id == usergroup_id,
            sample.FilterConfig.active.is_(True),
        )
        .order_by(sample.UserGroupFilterConfig.order)
    )
