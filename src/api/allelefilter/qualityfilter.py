from sqlalchemy import or_, and_
from vardb.datamodel import sample, genotype


class QualityFilter(object):
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def filter_alleles(self, analysis_allele_ids, filter_config):
        """
        Returns allele_ids that can be filtered _out_ from an analysis.
        """
        assert filter_config.get("qual") or filter_config.get("allele_ratio")

        quality_filters = []
        if "qual" in filter_config:
            quality_filters.append(genotype.Genotype.variant_quality < filter_config["qual"])

        if "allele_ratio" in filter_config:
            quality_filters.append(
                genotype.GenotypeSampleData.allele_ratio < filter_config["allele_ratio"]
            )
        assert len(quality_filters)

        result = dict()
        for analysis_id, allele_ids in analysis_allele_ids.items():
            if not allele_ids:
                result[analysis_id] = set()
                continue

            quality_filtered = (
                self.session.query(genotype.Genotype.allele_id, genotype.Genotype.secondallele_id)
                .join(genotype.GenotypeSampleData)
                .join(sample.Sample)
                .filter(
                    or_(
                        genotype.Genotype.allele_id.in_(allele_ids),
                        genotype.Genotype.secondallele_id.in_(allele_ids),
                    ),
                    and_(*quality_filters),
                    sample.Sample.analysis_id == analysis_id,
                    sample.Sample.proband.is_(True),
                )
                .all()
            )

            quality_filtered = [a[0] for a in quality_filtered] + [
                a[1] for a in quality_filtered if a[1]
            ]

            result[analysis_id] = set(quality_filtered)

        return result
