from sqlalchemy import or_, and_, tuple_, text, func, case, Table, Column, MetaData, Integer
from sqlalchemy.types import Text
from sqlalchemy.dialects.postgresql import ARRAY
from vardb.datamodel import annotationshadow, gene


class ConsequenceFilter(object):

    def __init__(self, session, config):
        self.session = session
        self.config = config

    def filter_alleles(self, gp_allele_ids):
        """
        Returns allele_ids that can be filtered _out_.
        """


        all_consequences = self.config.get('transcripts', {}).get('consequences')
        consequence_cutoff = self.config.get('variant_criteria', {}).get('consequence_cutoff')

        result = dict()
        for gp_key, allele_ids in gp_allele_ids.iteritems():
            if not allele_ids:
                result[gp_key] = set()
                continue

            gp_genes = self.session.query(
                gene.Transcript.gene_id,
                gene.Gene.hgnc_symbol
            ).join(
                gene.Genepanel.transcripts
            ).join(
                gene.Gene
            ).filter(
                tuple_(gene.Genepanel.name, gene.Genepanel.version) == gp_key,
            )

            gp_gene_ids, gp_gene_symbols = zip(*[(g[0], g[1]) for g in gp_genes])

            consequences_unnested = self.session.query(
                annotationshadow.AnnotationShadowTranscript.allele_id,
                func.unnest(annotationshadow.AnnotationShadowTranscript.consequences).label("unnested_consequences")
            ).filter(
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids),
                or_(
                    annotationshadow.AnnotationShadowTranscript.hgnc_id.in_(gp_gene_ids),
                    annotationshadow.AnnotationShadowTranscript.symbol.in_(gp_gene_symbols)
                )
            )

            inclusion_regex = self.config.get("transcripts", {}).get("inclusion_regex")
            if inclusion_regex:
                consequences_unnested = consequences_unnested.filter(
                    text("transcript ~ :reg").params(reg=inclusion_regex)
                )

            consequences_unnested = consequences_unnested.subquery()

            consequences_agg = self.session.query(
                consequences_unnested.c.allele_id.label('allele_id'),
                func.array_agg(consequences_unnested.c.unnested_consequences).label('consequences')
            ).group_by(
                consequences_unnested.c.allele_id
            ).subquery()

            if all_consequences and consequence_cutoff:
                severe_consequences = all_consequences[:all_consequences.index(consequence_cutoff)]
            else:
                severe_consequences = []

            # Find allele ids that have worst consequence equal to consequence cutoff
            allele_ids_worst_consequence_cutoff = self.session.query(
                consequences_agg.c.allele_id
            ).filter(
                ~consequences_agg.c.consequences.cast(ARRAY(Text)).op('&&')(severe_consequences),
                consequences_agg.c.consequences.cast(ARRAY(Text)).op('&&')([consequence_cutoff])
            )

            result[gp_key] = set([a[0] for a in allele_ids_worst_consequence_cutoff])

        return result
