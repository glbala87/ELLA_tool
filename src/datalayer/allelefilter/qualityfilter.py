from typing import List, Set, Dict, Any
from vardb.datamodel import sample
from datalayer.allelefilter.genotypetable import get_genotype_temp_table
from sqlalchemy import not_, and_, or_


class QualityFilter(object):
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def filter_alleles(
        self, analysis_allele_ids: Dict[int, List[int]], filter_config: Dict[str, Any]
    ) -> Dict[int, Set[int]]:
        """
        Returns allele_ids that can be filtered _out_ from an analysis.
        """
        assert any(k in filter_config for k in ["qual", "allele_ratio", "filter_status"])

        result: Dict[int, Set[int]] = dict()
        for analysis_id, allele_ids in analysis_allele_ids.items():
            if not allele_ids:
                result[analysis_id] = set()
                continue

            proband_sample_ids = (
                self.session.query(sample.Sample.id)
                .filter(sample.Sample.analysis_id == analysis_id, sample.Sample.proband.is_(True))
                .scalar_all()
            )

            genotype_table = get_genotype_temp_table(
                self.session,
                allele_ids,
                proband_sample_ids,
                genotype_extras={"qual": "variant_quality", "filter_status": "filter_status"},
                genotypesampledata_extras={"ar": "allele_ratio"},
            )

            # We consider an allele to be filtered out if it is to be filtered out in ALL proband samples it occurs in.
            # To achieve this, we work backwards, by finding all alleles that should not be filtered in each sample, and
            # subtracting it from the set of all allele ids.
            considered_allele_ids: Set[int] = set()
            filtered_allele_ids = set(allele_ids)

            for sample_id in proband_sample_ids:
                filter_conditions = []
                if "qual" in filter_config:
                    filter_conditions.extend(
                        [
                            ~getattr(genotype_table.c, f"{sample_id}_qual").is_(None),
                            getattr(genotype_table.c, f"{sample_id}_qual") < filter_config["qual"],
                        ]
                    )

                if "allele_ratio" in filter_config:
                    filter_conditions.extend(
                        [
                            ~getattr(genotype_table.c, f"{sample_id}_ar").is_(None),
                            getattr(genotype_table.c, f"{sample_id}_ar")
                            < filter_config["allele_ratio"],
                            getattr(genotype_table.c, f"{sample_id}_ar")
                            != 0.0,  # Allele ratios can sometimes be misleading 0.0. Avoid filtering these out.,
                        ]
                    )

                if "filter_status" in filter_config:
                    # Filter according to regex pattern
                    filter_status_pattern = getattr(
                        genotype_table.c, f"{sample_id}_filter_status"
                    ).op("~")(filter_config["filter_status"]["pattern"])

                    # If filter_empty, always filter out None or '.'
                    if filter_config["filter_status"].get("filter_empty", False):
                        filter_status_condition = or_(
                            filter_status_pattern,
                            getattr(genotype_table.c, f"{sample_id}_filter_status").is_(None),
                            getattr(genotype_table.c, f"{sample_id}_filter_status") == ".",
                        )
                    # else, never filter out None or '.' (even if regex says '\.')
                    else:
                        filter_status_condition = and_(
                            filter_status_pattern,
                            ~getattr(genotype_table.c, f"{sample_id}_filter_status").is_(None),
                            getattr(genotype_table.c, f"{sample_id}_filter_status") != ".",
                        )

                    # If inverse, run whole expression in reverse
                    if filter_config["filter_status"].get("inverse", False):
                        filter_status_condition = not_(filter_status_condition)

                    filter_conditions.append(filter_status_condition)

                alleles_in_sample = self.session.query(genotype_table.c.allele_id).filter(
                    ~getattr(genotype_table.c, f"{sample_id}_genotypeid").is_(None)
                )
                considered_allele_ids |= set(alleles_in_sample.scalar_all())

                not_filtered_allele_ids = alleles_in_sample.filter(~and_(*filter_conditions))
                filtered_allele_ids -= set(not_filtered_allele_ids.scalar_all())

            assert considered_allele_ids == set(allele_ids)
            result[analysis_id] = filtered_allele_ids

        return result
