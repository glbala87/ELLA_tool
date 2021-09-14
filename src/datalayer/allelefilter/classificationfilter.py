from typing import Any, Dict, List, Optional, Set, Tuple
from datalayer import queries
from sqlalchemy.orm.session import Session
from vardb.datamodel import assessment
from sqlalchemy.sql.functions import func
from sqlalchemy.dialects.postgresql import array


class ClassificationFilter(object):
    def __init__(self, session: Session, config: Optional[Dict[str, Any]]) -> None:
        self.session = session
        self.config = config

    def filter_alleles(
        self, gp_allele_ids: Dict[Tuple[str, str], List[int]], filter_config: Dict[str, List[str]]
    ) -> Dict[Tuple[str, str], Set[int]]:
        """
        Return the allele ids, among the provided allele_ids,
        that have an existing classification in the provided filter_config['classes'],
        and are not outdated per the application config, if flag `exclude_outdated` is set to True.

        `exclude_outdated` defaults to False, to keep backwards compatibility. This is suitable when used as an exception.
        Setting this to True is more suitable when sued as a forward filter, to e.g. filter out class 2 variants only if
        they have a valid date.
        """
        filter_classes = filter_config["classes"]
        available_classes = list(
            assessment.AlleleAssessment.classification.property.columns[0].type.enums
        )

        assert not set(filter_classes) - set(
            available_classes
        ), "Invalid class(es) to filter on in {}. Available classes are {}.".format(
            filter_classes, available_classes
        )

        # Only apply filter to assessments within date set in config if exclude_outdated is True.
        # Note: date_superceeded is _not_ related "outdatedness", this is to just get the latest
        # assessments for the allele (regardless of date)
        if filter_config.get("exclude_outdated", False):
            valid_assessments = queries.valid_alleleassessments_filter(self.session)
        else:
            valid_assessments = [assessment.AlleleAssessment.date_superceeded.is_(None)]

        result: Dict[Tuple[str, str], Set[int]] = dict()
        for gp_key, allele_ids in gp_allele_ids.items():
            if not allele_ids or not filter_classes:
                result[gp_key] = set()
                continue

            filtered_allele_ids = self.session.query(assessment.AlleleAssessment.allele_id).filter(
                assessment.AlleleAssessment.allele_id.in_(
                    self.session.query(func.unnest(array(allele_ids))).subquery()
                ),
                assessment.AlleleAssessment.classification.in_(filter_classes),
                *valid_assessments
            )

            result[gp_key] = set([a[0] for a in filtered_allele_ids])

        return result
