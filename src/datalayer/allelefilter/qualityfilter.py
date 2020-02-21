from vardb.datamodel import sample
from datalayer.allelefilter.genotypetable import get_genotype_temp_table
from sqlalchemy import and_


class QualityFilter(object):
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def filter_alleles(self, analysis_allele_ids, filter_config):
        """
        Returns allele_ids that can be filtered _out_ from an analysis.
        """
        assert "qual" in filter_config or "allele_ratio" in filter_config

        result = dict()
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
                genotype_extras={"qual": "variant_quality"},
                genotypesampledata_extras={"ar": "allele_ratio"},
            )

            # We consider an allele to be filtered out if it is to be filtered out in ALL proband samples it occurs in.
            # To achieve this, we work backwards, by finding all alleles that should not be filtered in each sample, and
            # subtracting it from the set of all allele ids.
            considered_allele_ids = set()
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

                variants_in_sample = self.session.query(genotype_table.c.allele_id).filter(
                    ~getattr(genotype_table.c, f"{sample_id}_genotypeid").is_(None)
                )
                considered_allele_ids |= set(variants_in_sample.scalar_all())

                not_filtered_allele_ids = variants_in_sample.filter(~and_(*filter_conditions))

                filtered_allele_ids -= set(not_filtered_allele_ids.scalar_all())
            assert considered_allele_ids == set(allele_ids)
            result[analysis_id] = filtered_allele_ids

        return result
