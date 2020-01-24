from typing import Any, Dict, List, Set

from sqlalchemy import and_, func, text, or_, not_
from vardb.datamodel import sample, gene, annotationshadow

from datalayer.allelefilter.genotypetable import get_genotype_temp_table


FILTER_MODES = ["recessive_non_candidates", "recessive_candidates"]


class InheritanceModelFilter(object):
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def filter_alleles(
        self, analysis_allele_ids: Dict[int, List[int]], filter_config: Dict[str, Any]
    ) -> Dict[int, Set[int]]:
        """
        Works on proband data only, does *not* use family information.
        Intended only for usage on single sample analyses.

        Filter removing variants not consistent with inheritence model.

        Filter criterias for the different modes:
            recessive_non_candidates:
                - single, heterozygous variant
                - distinct AR inheritance
            recessive_candidates:
                - single homozygous variant or multiple variants
                - not distinct AD inheritance

        "recessive_candidates" is intended to be used when filter is
        run as an exceptions filter, to rescue potentially important
        variants from being filtered by another filter.

        Config example:
        {
            "filter_mode": "recessive_non_candidates"
        }


        """

        if "filter_mode" not in filter_config:
            raise RuntimeError(f"Filter configuration is missing required config key 'filter_mode'")

        filter_mode = filter_config["filter_mode"]
        assert (
            filter_mode in FILTER_MODES
        ), f"Configuration key filter_mode must be one of: {', '.join(FILTER_MODES)}"

        result: Dict[int, Set[int]] = dict()
        for analysis_id, allele_ids in analysis_allele_ids.items():
            result[analysis_id] = set()
            if not allele_ids:
                continue

            gp_name, gp_version = (
                self.session.query(
                    sample.Analysis.genepanel_name, sample.Analysis.genepanel_version
                )
                .filter(sample.Analysis.id == analysis_id)
                .one()
            )

            # There can be multiple sample ids for a proband,
            # we need to check them all
            proband_sample_identifier_ids = (
                self.session.query(sample.Sample.identifier, sample.Sample.id)
                .filter(sample.Sample.analysis_id == analysis_id, sample.Sample.proband.is_(True))
                .all()
            )

            # We need to merge all the proband samples together into one table
            # Table we get from genotype_table looks like the following:
            # -------------------------------------------------------------------------------------
            # | allele_id | Sample 1_id | Sample 1_type | ... | Sample 2_id | Sample 2_type | ... |
            # -------------------------------------------------------------------------------------
            # | 62        | 69          | Heterozygous  | ... | None        | None          | ... |
            # | 63        | 70          | Homozygous    | ... | None        | None          | ... |
            # | 64        | None        | None          | ... | 71          | Heterozygous  | ... |
            #
            # Which we transform into the following:
            # -------------------------------
            # | allele_id | proband_genotype |
            # -------------------------------
            # | 62        | Heterozygous     |
            # | 63        | Homozygous       |
            # | 64        | Heterozygous     |

            proband_sample_ids = [p.id for p in proband_sample_identifier_ids]
            genotype_table = get_genotype_temp_table(self.session, allele_ids, proband_sample_ids)

            proband_genotype_tables = list()
            for proband_sample_name, proband_sample_id in proband_sample_identifier_ids:
                proband_genotype_tables.append(
                    self.session.query(
                        genotype_table.c.allele_id.label("allele_id"),
                        getattr(genotype_table.c, f"{proband_sample_id}_type").label(
                            "proband_genotype"
                        ),
                    ).filter(~getattr(genotype_table.c, f"{proband_sample_id}_type").is_(None))
                )

            proband_genotype_table = proband_genotype_tables[0]
            if len(proband_genotype_tables) > 1:
                for to_add_table in proband_genotype_tables[1:]:
                    proband_genotype_table = proband_genotype_table.union(to_add_table)

            proband_genotype_table = proband_genotype_table.temp_table("proband_genotype_table")

            #
            # While the criterias themselves are pretty straightforward,
            # there are some cases making it more complicated
            #
            # Simple case:
            # allele_id  hgnc_id  inheritance
            # 1          1001     AR
            # 2          1001     AR
            #
            # One variant has two genes:
            # Here we cannot simple group by hgnc_id and check,
            # we need to check across genes.
            # allele_id  hgnc_id  inheritance
            # 1          1001     AR
            # 2          1001     AR
            # 2          1002     AD
            #
            # Same as above, but different inheritance, making it more dangerous:
            # Only grouping by hgnc_id would filter wrongly,
            # since allele 2 would be filtered for mode recessive_non_candidates.
            # allele_id  hgnc_id  inheritance
            # 1          1001     AR
            # 2          1001     AR
            # 2          1002     AR
            #
            # And another variation where both has multiple genes:
            # We need to make sure the criterias are fulfilled for all genes
            # allele_id  hgnc_id  inheritance
            # 1          1001     AR
            # 1          1002     AR
            # 2          1001     AR
            # 2          1002     AR
            #

            # Get genepanel phenotypes' inheritance per hgnc id
            # ------------------------
            # | hgnc_id | inheritance |
            # ------------------------
            # | 7       | AD          |
            # | 7       | AR          |
            # | 13666   | AR          |
            # ...
            genepanel_hgnc_id_phenotype = (
                self.session.query(
                    gene.Phenotype.gene_id.label("hgnc_id"), gene.Phenotype.inheritance
                )
                .filter(
                    gene.Phenotype.id == gene.genepanel_phenotype.c.phenotype_id,
                    gene.genepanel_phenotype.c.genepanel_name == gp_name,
                    gene.genepanel_phenotype.c.genepanel_version == gp_version,
                )
                .subquery("genepanel_hgnc_id_phenotype")
            )

            # Set up column criterias from filter_config
            criteria_columns: List = []
            if filter_mode == "recessive_non_candidates":
                # - single, heterozygous variant
                # - distinct AR or distinct XR inheritance
                criteria_columns = [
                    func.bool_and(genepanel_hgnc_id_phenotype.c.inheritance == "AR").label(
                        "is_inheritance_match"
                    ),
                    and_(
                        func.count(proband_genotype_table.c.allele_id.distinct()) == 1,
                        func.bool_and(proband_genotype_table.c.proband_genotype == "Heterozygous"),
                    ).label("is_variant_match"),
                ]
            elif filter_mode == "recessive_candidates":
                # - single homozygous variant or multiple variants
                # - not distinct AD inheritance
                criteria_columns = [
                    not_(func.bool_and(genepanel_hgnc_id_phenotype.c.inheritance == "AD")).label(
                        "is_inheritance_match"
                    ),
                    or_(
                        # single homozygous
                        and_(
                            func.count(proband_genotype_table.c.allele_id.distinct()) == 1,
                            func.bool_and(
                                proband_genotype_table.c.proband_genotype == "Homozygous"
                            ),
                        ),
                        # multiple whatever genotype
                        func.count(proband_genotype_table.c.allele_id.distinct()) > 1,
                    ).label("is_variant_match"),
                ]
            else:
                raise RuntimeError("Wrong filter_mode")

            # Set up filters
            filters = []
            inclusion_regex = self.config.get("transcripts", {}).get("inclusion_regex")
            if inclusion_regex:
                filters.append(text("transcript ~ :reg").params(reg=inclusion_regex))

            # Join all data, group by hgnc_id and aggregate data to
            # generate each critera *per hgnc_id*
            # | allele_id | hgnc_id | is_inheritance_match | is_variant_match |
            # -----------------------------------------------------------------
            # | 1152      | 7       | False                | True             |
            # | 1521      | 20      | False                | True             |
            # | 1474      | 23      | True                 | False            |
            # | 1475      | 23      | True                 | False            |
            allele_ids_filter_candidates = (
                self.session.query(
                    func.unnest(func.array_agg(proband_genotype_table.c.allele_id)).label(
                        "allele_id"
                    ),
                    annotationshadow.AnnotationShadowTranscript.hgnc_id,
                    *criteria_columns,
                )
                .join(
                    annotationshadow.AnnotationShadowTranscript,
                    proband_genotype_table.c.allele_id
                    == annotationshadow.AnnotationShadowTranscript.allele_id,
                )
                .join(
                    genepanel_hgnc_id_phenotype,
                    genepanel_hgnc_id_phenotype.c.hgnc_id
                    == annotationshadow.AnnotationShadowTranscript.hgnc_id,
                )
                .filter(*filters)
                .group_by(annotationshadow.AnnotationShadowTranscript.hgnc_id)
                .order_by(annotationshadow.AnnotationShadowTranscript.hgnc_id)
                .distinct()
            )
            allele_ids_filter_candidates = allele_ids_filter_candidates.subquery()

            # Finally group by allele ids, and check criterias
            # across all the genes in the genepanel (per allele id).
            # We need to do this since alleles can overlap multiple genes.

            # If recessive_non_candidates, the criterias need to be true for all genes
            # If recessive_candidates, the criterias need to be true for one or more genes

            agg_func = None
            if filter_mode == "recessive_non_candidates":
                agg_func = func.bool_and
            elif filter_mode == "recessive_candidates":
                agg_func = func.bool_or
            else:
                raise RuntimeError("Wrong filter_mode")

            having_criteria = agg_func(
                and_(
                    allele_ids_filter_candidates.c.is_inheritance_match.is_(True),
                    allele_ids_filter_candidates.c.is_variant_match.is_(True),
                )
            )
            filtered_allele_ids = (
                self.session.query(allele_ids_filter_candidates.c.allele_id)
                .group_by(allele_ids_filter_candidates.c.allele_id)
                .having(having_criteria)
            )

            filtered_allele_ids = set(filtered_allele_ids.scalar_all())
            result[analysis_id].update(filtered_allele_ids)

        return result
