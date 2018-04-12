import datetime
import pytz
from sqlalchemy import or_, and_, tuple_, func, text, literal_column
from vardb.datamodel import sample, workflow, assessment, allele, genotype, gene, annotation
from vardb.datamodel.annotationshadow import AnnotationShadowTranscript

from api.config import config


def valid_alleleassessments_filter(session):
    """
    Filter for including alleleassessments that have valid (not outdated) classifications.
    """
    classification_filters = list()
    # Create classification filters, filtering on classification and optionally outdated threshold
    for option in config['classification']['options']:
        internal_filters = [assessment.AlleleAssessment.classification == option['value']]
        if 'outdated_after_days' in option:
            outdated_time = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=option['outdated_after_days'])
            internal_filters.append(assessment.AlleleAssessment.date_created > outdated_time)
        # Add our filter using and_
        classification_filters.append(and_(*internal_filters))
    return [or_(*classification_filters),
            assessment.AlleleAssessment.date_superceeded.is_(None)]


def allele_ids_with_valid_alleleassessments(session):
    """
    Query for all alleles that has no valid alleleassessments,
    as given by configuration's classification options.

    Different scenarios:
    - Allele has alleleassessment and it's not outdated
    - Allele has alleleassessment, but it's outdated
    - Allele has no alleleassessments at all.

    """
    return session.query(allele.Allele.id).join(assessment.AlleleAssessment).filter(
        *valid_alleleassessments_filter(session)
    )


def workflow_by_status(session, model, model_id_attr, workflow_status=None, status=None):
    """
    Fetches all allele_id/analysis_id where the last interpretation matches provided
    workflow status and/or status.

    :param model: AlleleInterpretation or AnalysisInterpretation
    :param model_id_attr: 'allele_id' or 'analysis_id'

    Query resembles something like this:
     SELECT s.id FROM (select DISTINCT ON (analysis_id) id, workflow_status, status
     from analysisinterpretation order by analysis_id, date_last_update desc) AS
     s where s.workflow_status = :status;
    """

    if workflow_status is None and status is None:
        raise RuntimeError("You must provide either 'workflow_status' or 'status' argument")

    latest_interpretation = session.query(
        getattr(model, model_id_attr),
        model.workflow_status,
        model.status,
    ).order_by(
        getattr(model, model_id_attr),
        model.date_last_update.desc(),
    ).distinct(
        getattr(model, model_id_attr),  # DISTINCT ON
    ).subquery()

    filters = []
    if workflow_status:
        filters.append(
            latest_interpretation.c.workflow_status == workflow_status,
        )
    if status:
        filters.append(
            latest_interpretation.c.status == status
        )
    return session.query(getattr(latest_interpretation.c, model_id_attr)).filter(*filters)


def workflow_analyses_finalized(session):
    """
    Definition of Finalized: latest interpretation is 'Done'
    """
    return workflow_by_status(
        session,
        workflow.AnalysisInterpretation,
        'analysis_id',
        workflow_status=None,
        status='Done'
    )


def workflow_analyses_notready_not_started(session):
    return workflow_by_status(
        session,
        workflow.AnalysisInterpretation,
        'analysis_id',
        workflow_status='Not ready',
        status='Not started'
    )


def workflow_analyses_interpretation_not_started(session):
    return workflow_by_status(
        session,
        workflow.AnalysisInterpretation,
        'analysis_id',
        workflow_status='Interpretation',
        status='Not started'
    )


def workflow_analyses_review_not_started(session):
    return workflow_by_status(
        session,
        workflow.AnalysisInterpretation,
        'analysis_id',
        workflow_status='Review',
        status='Not started'
    )


def workflow_analyses_medicalreview_not_started(session):
    return workflow_by_status(
        session,
        workflow.AnalysisInterpretation,
        'analysis_id',
        workflow_status='Medical review',
        status='Not started'
    )


def workflow_analyses_ongoing(session):
    return workflow_by_status(
        session,
        workflow.AnalysisInterpretation,
        'analysis_id',
        workflow_status=None,
        status='Ongoing'
    )


def workflow_analyses_for_genepanels(session, genepanels):
    return session.query(sample.Analysis.id).filter(
        tuple_(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version).in_((gp.name, gp.version) for gp in genepanels)
    )


def allele_ids_not_started_analyses(session):
    """
    Get all allele_ids for 'Not started' analyses in either
    'Not ready' or 'Interpretation' workflow status.
    """
    return session.query(
        allele.Allele.id,
    ).join(
        genotype.Genotype.alleles,
        sample.Sample,
        sample.Analysis
    ).filter(
        or_(
            sample.Analysis.id.in_(workflow_analyses_interpretation_not_started(session)),
            sample.Analysis.id.in_(workflow_analyses_notready_not_started(session))
        )
    )


def workflow_alleles_finalized(session):
    return workflow_by_status(
        session,
        workflow.AlleleInterpretation,
        'allele_id',
        workflow_status=None,
        status='Done'
    )


def workflow_alleles_interpretation_not_started(session):
    return workflow_by_status(
        session,
        workflow.AlleleInterpretation,
        'allele_id',
        workflow_status='Interpretation',
        status='Not started'
    )


def workflow_alleles_review_not_started(session):
    return workflow_by_status(
        session,
        workflow.AlleleInterpretation,
        'allele_id',
        workflow_status='Review',
        status='Not started'
    )


def workflow_alleles_ongoing(session):
    return workflow_by_status(
        session,
        workflow.AlleleInterpretation,
        'allele_id',
        workflow_status=None,
        status='Ongoing'
    )


def workflow_alleles_for_genepanels(session, genepanels):
    """
    Get all allele_ids connected to given genepanels.

    They are either connected via an analysis or via an alleleinterpretation.
    """
    analysis_ids = workflow_analyses_for_genepanels(session, genepanels)

    allele_ids_for_analyses = session.query(allele.Allele.id).join(
        genotype.Genotype.alleles,
        sample.Sample,
        sample.Analysis
    ).filter(
        sample.Analysis.id.in_(analysis_ids)
    ).distinct()

    allele_ids_for_alleleinterpretation = session.query(workflow.AlleleInterpretation.allele_id).filter(
        tuple_(workflow.AlleleInterpretation.genepanel_name, workflow.AlleleInterpretation.genepanel_version).in_(
            (gp.name, gp.version) for gp in genepanels
        )
    ).distinct()

    return session.query(allele.Allele.id).filter(
        or_(
            allele.Allele.id.in_(allele_ids_for_analyses),
            allele.Allele.id.in_(allele_ids_for_alleleinterpretation),
        )
    )


def allele_ids_no_analysis(session):
    def get_sub_query():
        return session.query(
            allele.Allele.id,
        ).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            workflow.AnalysisInterpretation
        )

    return session.query(allele.Allele.id).filter(
        ~allele.Allele.id.in_(get_sub_query()),
    )


def distinct_inheritance_genes_for_genepanel(session, inheritance, gp_name, gp_version):
    """
    Fetches all genes with _only_ {inheritance} phenotypes.

    e.g. only 'AD' or only 'AR'
    """

    # Get phenotypes having only one kind of inheritance
    # e.g. only 'AD' or only 'AR' etc...
    distinct_inheritance = session.query(
        gene.Phenotype.genepanel_name,
        gene.Phenotype.genepanel_version,
        gene.Phenotype.gene_id,
    ).filter(
        gene.Phenotype.genepanel_name == gp_name,
        gene.Phenotype.genepanel_version == gp_version
    ).group_by(
        gene.Phenotype.genepanel_name,
        gene.Phenotype.genepanel_version,
        gene.Phenotype.gene_id
    ).having(func.count(gene.Phenotype.inheritance.distinct()) == 1).subquery()

    return session.query(
        gene.Gene.hgnc_symbol,
    ).join(
        gene.Phenotype,
        gene.Phenotype.gene_id == gene.Gene.hgnc_id
    ).join(
        distinct_inheritance,
        and_(
            gene.Phenotype.genepanel_name == distinct_inheritance.c.genepanel_name,
            gene.Phenotype.genepanel_version == distinct_inheritance.c.genepanel_version,
            gene.Phenotype.gene_id == distinct_inheritance.c.gene_id
        )
    ).filter(
        gene.Phenotype.genepanel_name == gp_name,
        gene.Phenotype.genepanel_version == gp_version,
        gene.Phenotype.inheritance == inheritance
    ).distinct()


def annotation_transcripts_genepanel(session, allele_ids, genepanel_keys):

    """
    Filters annotation transcripts for input allele_ids against genepanel transcripts
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
    genepanel_transcripts = session.query(
        gene.Genepanel.name,
        gene.Genepanel.version,
        gene.Transcript.transcript_name,
        gene.Transcript.gene_id,
    ).join(gene.Genepanel.transcripts).filter(
        tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(genepanel_keys)
    ).subquery()

    # Join genepanel and annotation tables together, using transcript as key
    # and splitting out the version number of the transcript (if it has one)
    result = session.query(
        AnnotationShadowTranscript.allele_id.label('allele_id'),
        genepanel_transcripts.c.name.label('name'),
        genepanel_transcripts.c.version.label('version'),
        AnnotationShadowTranscript.transcript.label('annotation_transcript'),
        AnnotationShadowTranscript.symbol.label('annotation_symbol'),
        AnnotationShadowTranscript.hgnc_id.label('annotation_hgnc_id'),
        AnnotationShadowTranscript.hgvsc.label('annotation_hgvsc'),
        AnnotationShadowTranscript.hgvsp.label('annotation_hgvsp'),
        genepanel_transcripts.c.transcript_name.label('genepanel_transcript'),
    ).filter(
        text("split_part(transcript, '.', 1) = split_part(transcript_name, '.', 1)")
    ).distinct()

    return result
