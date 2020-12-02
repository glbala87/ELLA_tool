from typing import Dict, List, Set, Tuple
from vardb.datamodel import allele


class CallerTypeFilter(object):
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def filter_alleles(
        self, gp_allele_ids: Dict[Tuple[str, str], List[int]], filter_config: Dict[str, List[str]]
    ) -> Dict[Tuple[str, str], Set[int]]:
        """
        Return the allele ids, among the provided allele_ids,
        that have an existing callerType in the provided filter_config['callertype'].
        """

        available_callertypes = list(allele.Allele.caller_type.property.columns[0].type.enums)
        filter_callertypes = filter_config["callerTypes"]

        assert filter_callertypes, "callerTypes was not found in filterconfig"

        assert not set(filter_callertypes) - set(
            available_callertypes
        ), "Invalid callertype(s) to filter on in {}. Available callertypes are {}.".format(
            filter_callertypes, available_callertypes
        )

        result: Dict[Tuple[str, str], Set[int]] = dict()
        for gp_key, allele_ids in gp_allele_ids.items():
            if not allele_ids or not filter_callertypes:
                result[gp_key] = set()
                continue

            filtered_allele_ids = self.session.query(allele.Allele.id).filter(
                allele.Allele.id.in_(allele_ids),
                allele.Allele.caller_type.in_(filter_callertypes),
            )

            result[gp_key] = set([a[0] for a in filtered_allele_ids])

        return result
