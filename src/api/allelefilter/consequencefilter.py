from sqlalchemy import or_, and_, tuple_, text, func, case, Table, Column, MetaData, Integer
from sqlalchemy.types import Text
from sqlalchemy.dialects.postgresql import ARRAY
from vardb.datamodel import annotationshadow, gene

from api.util.util import query_print_table

class ConsequenceFilter(object):

    def __init__(self, session, config):
        self.session = session
        self.config = config

    def filter_alleles(self, gp_allele_ids, filter_config):
        """
        Filter alleles that have consequence in list of consequences for any of the transcripts matching
        the global include regex (if specified). Can be specified to look at genepanel genes only.
        """
        gp_csq_only = filter_config.get("genepanel_only", False)

        consequences = filter_config["consequences"]
        assert not set(consequences) - set(self.config['transcripts']['consequences']), "Invalid consequences passed to filter: {}".format(consequences)

        result = dict()
        for gp_key, allele_ids in gp_allele_ids.iteritems():
            if not allele_ids:
                result[gp_key] = set()
                continue

            allele_ids_with_consequence = self.session.query(
                annotationshadow.AnnotationShadowTranscript.allele_id,
            ).filter(
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids),
                annotationshadow.AnnotationShadowTranscript.consequences.op("&&")(consequences)
            ).distinct()

            inclusion_regex = self.config.get("transcripts", {}).get("inclusion_regex")
            if inclusion_regex:
                allele_ids_with_consequence = allele_ids_with_consequence.filter(
                    text("transcript ~ :reg").params(reg=inclusion_regex)
                )

            # Only include genes in genepanel if flag gp_csq_only
            if gp_csq_only:
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

                allele_ids_with_consequence = allele_ids_with_consequence.filter(
                    or_(
                        annotationshadow.AnnotationShadowTranscript.hgnc_id.in_(gp_gene_ids),
                        annotationshadow.AnnotationShadowTranscript.symbol.in_(gp_gene_symbols)
                    )
                )

            result[gp_key] = set([a[0] for a in allele_ids_with_consequence])

        return result
