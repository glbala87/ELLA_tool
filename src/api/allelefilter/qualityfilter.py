from sqlalchemy import or_
from vardb.datamodel import sample, genotype


class QualityFilter(object):
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def filter_alleles(self, analysis_allele_ids, filter_config):
        """
        Returns allele_ids that can be filtered _out_ from an analysis.
        """

        result = dict()
        for analysis_id, allele_ids in analysis_allele_ids.iteritems():
            if not allele_ids:
                result[analysis_id] = set()
                continue

            quality_filtered = (
                self.session.query(genotype.Genotype.allele_id, genotype.Genotype.secondallele_id)
                .join(sample.Sample)
                .filter(
                    or_(
                        genotype.Genotype.allele_id.in_(allele_ids),
                        genotype.Genotype.secondallele_id.in_(allele_ids),
                    ),
                    genotype.Genotype.variant_quality < filter_config["qual"],
                    sample.Sample.analysis_id == analysis_id,
                )
                .all()
            )

            quality_filtered = [a[0] for a in quality_filtered] + [
                a[1] for a in quality_filtered if a[1]
            ]
            result[analysis_id] = set(quality_filtered)

        return result
