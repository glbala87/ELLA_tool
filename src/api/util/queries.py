import datetime
import pytz
from sqlalchemy import or_, and_, tuple_, func, text, literal_column
from vardb.datamodel import sample, workflow, assessment, allele, genotype, gene, annotation
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


def workflow_analyses_finalized(session):
    def get_sub_query(status):
        return session.query(sample.Analysis.id).join(
            workflow.AnalysisInterpretation
        ).filter(
            workflow.AnalysisInterpretation.status == status
        )

    return session.query(sample.Analysis.id).join(
        workflow.AnalysisInterpretation
    ).filter(
        ~sample.Analysis.id.in_(get_sub_query('Not started')),
        ~sample.Analysis.id.in_(get_sub_query('Ongoing')),
        sample.Analysis.id.in_(get_sub_query('Done'))
    ).distinct(sample.Analysis.id)


def workflow_analyses_not_started(session):
    def get_sub_query(status):
        return session.query(sample.Analysis.id).join(
            workflow.AnalysisInterpretation
        ).filter(
            workflow.AnalysisInterpretation.status == status
        )

    return session.query(sample.Analysis.id).join(
        workflow.AnalysisInterpretation
    ).filter(
        sample.Analysis.id.in_(get_sub_query('Not started')),
        ~sample.Analysis.id.in_(get_sub_query('Ongoing')),
        ~sample.Analysis.id.in_(get_sub_query('Done'))
    ).distinct(sample.Analysis.id)


def workflow_analyses_marked_review(session):
    def get_sub_query(status):
        return session.query(sample.Analysis.id).join(
            workflow.AnalysisInterpretation
        ).filter(
            workflow.AnalysisInterpretation.status == status
        )

    return session.query(sample.Analysis.id).join(
        workflow.AnalysisInterpretation
    ).filter(
        sample.Analysis.id.in_(get_sub_query('Not started')),
        sample.Analysis.id.in_(get_sub_query('Done')),
        ~sample.Analysis.id.in_(get_sub_query('Ongoing'))
    ).distinct(sample.Analysis.id)


def workflow_analyses_ongoing(session):
    def get_sub_query(status):
        return session.query(sample.Analysis.id).join(
            workflow.AnalysisInterpretation
        ).filter(
            workflow.AnalysisInterpretation.status == status
        )

    return session.query(sample.Analysis.id).join(
        workflow.AnalysisInterpretation
    ).filter(
        sample.Analysis.id.in_(get_sub_query('Ongoing')),
    ).distinct(sample.Analysis.id)


def workflow_analyses_for_genepanels(session, genepanels):
    return session.query(sample.Analysis.id).filter(
        tuple_(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version).in_((gp.name, gp.version) for gp in genepanels)
    )

def allele_ids_nonfinalized_analyses(session):
    return session.query(
        allele.Allele.id,
    ).join(
        genotype.Genotype.alleles,
        sample.Sample,
        sample.Analysis,
        workflow.AnalysisInterpretation
    ).filter(
        ~sample.Analysis.id.in_(workflow_analyses_finalized(session))
    )


def workflow_alleles_finalized(session):
    def get_sub_query(status):
        return session.query(allele.Allele.id).join(
            workflow.AlleleInterpretation
        ).filter(
            workflow.AlleleInterpretation.status == status
        )

    return session.query(allele.Allele.id).join(
        workflow.AlleleInterpretation
    ).filter(
        ~allele.Allele.id.in_(get_sub_query('Not started')),
        ~allele.Allele.id.in_(get_sub_query('Ongoing')),
        allele.Allele.id.in_(get_sub_query('Done'))
    ).distinct(allele.Allele.id)


def workflow_alleles_not_started(session):
    def get_sub_query(status):
        return session.query(allele.Allele.id).join(
            workflow.AlleleInterpretation
        ).filter(
            workflow.AlleleInterpretation.status == status
        )

    return session.query(allele.Allele.id).join(
        workflow.AlleleInterpretation
    ).filter(
        allele.Allele.id.in_(get_sub_query('Not started')),
        ~allele.Allele.id.in_(get_sub_query('Ongoing')),
        ~allele.Allele.id.in_(get_sub_query('Done'))
    ).distinct(allele.Allele.id)


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


def workflow_alleles_marked_review(session):
    def get_sub_query(status):
        return session.query(allele.Allele.id).join(
            workflow.AlleleInterpretation
        ).filter(
            workflow.AlleleInterpretation.status == status
        )

    return session.query(allele.Allele.id).join(
        workflow.AlleleInterpretation
    ).filter(
        allele.Allele.id.in_(get_sub_query('Not started')),
        allele.Allele.id.in_(get_sub_query('Done')),
        ~allele.Allele.id.in_(get_sub_query('Ongoing'))
    ).distinct(allele.Allele.id)


def workflow_alleles_ongoing(session):
    def get_sub_query(status):
        return session.query(allele.Allele.id).join(
            workflow.AlleleInterpretation
        ).filter(
            workflow.AlleleInterpretation.status == status
        )

    return session.query(allele.Allele.id).join(
        workflow.AlleleInterpretation
    ).filter(
        allele.Allele.id.in_(get_sub_query('Ongoing')),
    ).distinct(allele.Allele.id)


def workflow_alleles_for_genepanels(session, genepanels):
    analysis_ids = workflow_analyses_for_genepanels(session, genepanels)
    return session.query(allele.Allele.id).join(genotype.Genotype.alleles).filter(
        genotype.Genotype.analysis_id.in_(analysis_ids)
    ).distinct()


def ad_genes_for_genepanel(session, gp_name, gp_version):
    """
    Fetches all genes with _only_ 'AD' phenotypes.
    """
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
    ).having(func.count(gene.Phenotype.inheritance) == 1).subquery()

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
        gene.Phenotype.inheritance == 'AD'
    ).distinct()


def alleles_transcript_filtered_genepanel(session, allele_ids, genepanel_keys, inclusion_regex):

    """
    Filters annotation transcripts for input allele_ids against genepanel transcripts
    for given genepanel_keys.

    genepanel_keys = [('HBOC', 'v01'), ('LYNCH', 'v01'), ...]

    Returns Query object, representing:
    -----------------------------------------------------
    | allele_id | name | version | annotation_transcript |
    -----------------------------------------------------
    | 1         | HBOC | v01     | NM_000059.3           |
    | 2         | HBOC | v01     | NM_000059.3           |
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
        gene.Transcript.refseq_name,
        gene.Transcript.ensembl_id,
        gene.Transcript.gene_id,
    ).join(gene.Genepanel.transcripts).filter(
        tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(genepanel_keys)
    ).subquery()

    # Subquery unwrapping transcripts array from annotation
    # | allele_id |     transcripts      |
    # ------------------------------------
    # | 1         | {... JSONB data ...} |
    # | 2         | {... JSONB data ...} |
    filters = [annotation.Annotation.date_superceeded.is_(None)]  # Important!
    if allele_ids is not None:
        filters.append(annotation.Annotation.allele_id.in_(allele_ids))
    unwrapped_annotation = session.query(
        annotation.Annotation.allele_id,
        func.jsonb_array_elements(annotation.Annotation.annotations['transcripts']).label('transcripts')
    ).filter(
        *filters
    ).subquery()

    # Join the tables together, using transcript as key and splitting out the
    # version number of the transcript (if it has one)
    # -----------------------------------------------------------------------------
    # | allele_id | name | version | annotation_transcript | genepanel_transcript |
    # -----------------------------------------------------------------------------
    # | 1         | HBOC | v01     | NM_000059.3           | NM_000059.3          |
    # | 1         | HBOC | v01     | ENST00000380152       | NM_000059.3          |
    # | 1         | HBOC | v01     | ENST00000530893       | NM_000059.3          |
    result = session.query(
        unwrapped_annotation.c.allele_id.label('allele_id'),
        genepanel_transcripts.c.name.label('name'),
        genepanel_transcripts.c.version.label('version'),
        literal_column("transcripts::jsonb ->> 'symbol'").label('annotation_symbol'),
        literal_column("transcripts::jsonb ->> 'transcript'").label('annotation_transcript'),
        literal_column("transcripts::jsonb ->> 'HGVSc'").label('annotation_hgvsc'),
        literal_column("transcripts::jsonb ->> 'HGVSp'").label('annotation_hgvsp'),
        genepanel_transcripts.c.gene_id.label('genepanel_symbol'),
        genepanel_transcripts.c.refseq_name.label('genepanel_transcript'),
    ).filter(
        text("transcripts::jsonb ->> 'symbol' = gene_id")
    )

    # Only filter on annotation transcripts defined in config inclusion regex and genepanel transcripts
    transcript_filters = [text("split_part(transcripts::jsonb ->> 'transcript', '.', 1) = split_part(refseq_name, '.', 1)")]

    if inclusion_regex is not None:
        transcript_filters.append(
            text("transcripts::jsonb ->> 'transcript' ~ :reg").params(reg=inclusion_regex)
        )

    result = result.filter(or_(*transcript_filters))
    result = result.distinct()

    return result
