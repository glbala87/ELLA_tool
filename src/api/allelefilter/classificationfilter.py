from sqlalchemy import or_
from vardb.datamodel import assessment, allele


from api.util.util import query_print_table

class ClassificationFilter(object):

    def __init__(self, session, config):
        self.session = session
        self.config = config

    def filter_alleles(self, gp_allele_ids, filter_config):
        """
        Return the allele ids, among the provided allele_ids,
        that have have an existing classification in the provided filter_config['classes'].
        This filter does *not* check for outdated classification, these are treated as valid classifications
        """
        result = dict()
        for gp_key, allele_ids in gp_allele_ids.iteritems():
            if not allele_ids:
                result[gp_key] = set()

            filter_classes = filter_config['classes']
            available_classes = list(assessment.AlleleAssessment.classification.property.columns[0].type.enums)

            assert not set(filter_classes) - set(available_classes), "Invalid class(es) to filter on in {}. Available classes are {}.".format(filter_classes, available_classes)

            if not filter_classes:
                result[gp_key] = set()

            filtered_allele_ids = self.session.query(
                assessment.AlleleAssessment.allele_id,
            ).filter(
                assessment.AlleleAssessment.allele_id.in_(allele_ids),
                assessment.AlleleAssessment.classification.in_(filter_classes),
                assessment.AlleleAssessment.date_superceeded.is_(None)
            )

            result[gp_key] = set([a[0] for a in filtered_allele_ids])

        return result
