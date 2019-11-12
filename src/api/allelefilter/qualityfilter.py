from vardb.datamodel import sample
from api.allelefilter.genotypetable import get_genotype_temp_table


class QualityFilter(object):
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def filter_alleles(self, analysis_allele_ids, filter_config):
        """
        Returns allele_ids that can be filtered _out_ from an analysis.
        """
        assert (
            "qual" in filter_config
            or "allele_ratio" in filter_config
            or "filter_status" in filter_config
        )

        result = dict()
        for analysis_id, allele_ids in analysis_allele_ids.items():
            if not allele_ids:
                result[analysis_id] = set()
                continue

            sample_id, sample_identifier = (
                self.session.query(sample.Sample.id, sample.Sample.identifier)
                .filter(sample.Sample.analysis_id == analysis_id, sample.Sample.proband.is_(True))
                .one()
            )
            genotype_table = get_genotype_temp_table(
                self.session,
                allele_ids,
                [sample_id],
                genotype_extras={"qual": "variant_quality", "filter": "filter_status"},
                genotypesampledata_extras={"ar": "allele_ratio"},
            )

            quality_filters = []
            if "qual" in filter_config:
                quality_filters.append(
                    getattr(genotype_table.c, sample_identifier + "_qual") < filter_config["qual"]
                )

            if "allele_ratio" in filter_config:
                quality_filters.extend(
                    [
                        getattr(genotype_table.c, sample_identifier + "_ar")
                        < filter_config["allele_ratio"],
                        getattr(genotype_table.c, sample_identifier + "_ar")
                        != 0.0,  # Allele ratios can sometimes be misleading 0.0. Avoid filtering these out.
                    ]
                )

            if "filter_status" in filter_config:
                quality_filters.extend(
                    [
                        ~getattr(genotype_table.c, sample_identifier + "_filter").is_(None),
                        getattr(genotype_table.c, sample_identifier + "_filter") != ".",
                        getattr(genotype_table.c, sample_identifier + "_filter").op("~")(
                            filter_config["filter_status"]
                        ),
                    ]
                )
            assert len(quality_filters)

            quality_filtered = (
                self.session.query(genotype_table.c.allele_id).filter(*quality_filters).scalar_all()
            )

            result[analysis_id] = set(quality_filtered)

        return result
