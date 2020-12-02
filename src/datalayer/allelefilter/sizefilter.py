import operator
from typing import List, Set, Dict, Any, Tuple
from vardb.datamodel import allele

OPERATORS = {
    "==": operator.eq,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
}


class SizeFilter(object):
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def filter_alleles(
        self, gp_allele_ids: Dict[Tuple[str, str], List[int]], filter_config: Dict[str, Any]
    ) -> Dict[Tuple[str, str], Set[int]]:
        """
        Return the allele ids, among the provided allele_ids, that have an allele
        length specified by the size in threshold, and operator set in mode.

        Example configuration:

        {
            "name": "size",
            "config": {
                "threshold": 10000,
                "mode": ">"
            }
        }

        Keeping all alleles with length above 10kb
        """

        result: Dict[Tuple[str, str], Set[int]] = dict()

        for gp_key, allele_ids in gp_allele_ids.items():
            result[gp_key] = set(
                self.session.query(allele.Allele.id)
                .filter(
                    allele.Allele.id.in_(allele_ids),
                    OPERATORS[filter_config["mode"]](
                        allele.Allele.length, filter_config["threshold"]
                    ),
                )
                .scalar_all()
            )
        return result
