from typing import Any, Dict, List, Optional, Set, Tuple, Sequence, Callable
import logging
from sqlalchemy.orm.session import Session

from api.config import config as global_config
from vardb.datamodel import sample

from datalayer.allelefilter.frequencyfilter import FrequencyFilter
from datalayer.allelefilter.segregationfilter import SegregationFilter
from datalayer.allelefilter.regionfilter import RegionFilter
from datalayer.allelefilter.qualityfilter import QualityFilter
from datalayer.allelefilter.classificationfilter import ClassificationFilter
from datalayer.allelefilter.externalfilter import ExternalFilter
from datalayer.allelefilter.polypyrimidinetractfilter import PolypyrimidineTractFilter
from datalayer.allelefilter.consequencefilter import ConsequenceFilter
from datalayer.allelefilter.inheritancemodelfilter import InheritanceModelFilter
from datalayer.allelefilter.genefilter import GeneFilter


log = logging.getLogger(__name__)


class AlleleFilter(object):
    def __init__(self, session: Session, config: Optional[Dict] = None) -> None:
        self.session = session
        self.config = global_config if not config else config

        self.filter_functions: Dict[str, Tuple[str, Callable]] = {
            "frequency": ("allele", FrequencyFilter(self.session, self.config).filter_alleles),
            "region": ("allele", RegionFilter(self.session, self.config).filter_alleles),
            "classification": (
                "allele",
                ClassificationFilter(self.session, self.config).filter_alleles,
            ),
            "external": ("allele", ExternalFilter(self.session, self.config).filter_alleles),
            "ppy": ("allele", PolypyrimidineTractFilter(self.session, self.config).filter_alleles),
            "inheritancemodel": (
                "analysis",
                InheritanceModelFilter(self.session, self.config).filter_alleles,
            ),
            "consequence": ("allele", ConsequenceFilter(self.session, self.config).filter_alleles),
            "quality": ("analysis", QualityFilter(self.session, self.config).filter_alleles),
            "segregation": (
                "analysis",
                SegregationFilter(self.session, self.config).filter_alleles,
            ),
            "gene": ("allele", GeneFilter(self.session, self.config).filter_alleles),
        }

    def get_filter_exceptions(
        self,
        exceptions_config: List[Dict[str, Any]],
        gp_allele_ids: Dict[Tuple[str, str], Set[int]],
        analysis_allele_ids: Dict[int, Set[int]],
    ) -> Set[int]:
        """
        Checks whether any of allele_ids should be excepted from filtering,
        given checks given by exceptions_config
        """
        filter_exceptions: Set = set()

        for e in exceptions_config:
            name, config = e["name"], e["config"]
            filter_type, filter_func = self.filter_functions[name]
            if filter_type == "allele":
                filter_result = filter_func(gp_allele_ids, config)
            elif filter_type == "analysis":
                filter_result = filter_func(analysis_allele_ids, config)

            for filtered_allele_ids in filter_result.values():
                filter_exceptions |= filtered_allele_ids

        return filter_exceptions

    def filter_analysis(self, filter_config_id: int, analysis_id: int, allele_ids: Sequence[int]):
        """
        Filters alleles for a single analysis.

        Returns result:
            {
                'allele_ids': [1, 2, 3],
                'excluded_allele_ids': {
                    'frequency': [4, 5],
                    'region': [12, 45],
                    'segregation': [6, 8],
                }
            }
        """

        copied_allele_ids = set(allele_ids)

        analysis_genepanel = (
            self.session.query(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version)
            .filter(sample.Analysis.id == analysis_id)
            .one()
        )

        filter_config = (
            self.session.query(sample.FilterConfig.filterconfig)
            .filter(sample.FilterConfig.id == filter_config_id)
            .scalar()
        )

        result: Dict = {"allele_ids": [], "excluded_allele_ids": dict()}

        filters = filter_config["filters"]
        for f in filters:
            name = f["name"]
            if name not in self.filter_functions:
                raise RuntimeError("Requested filter {} is not a valid filter name".format(name))

            try:
                filter_config = f["config"]
                exceptions_config = f.get("exceptions", [])

                filter_data_type, filter_function = self.filter_functions[name]
                assert filter_data_type in [
                    "allele",
                    "analysis",
                ], "Unknown filter data type '{}'".format(filter_data_type)

                if filter_data_type == "analysis":
                    filtered_allele_ids = filter_function(
                        {analysis_id: copied_allele_ids}, filter_config
                    )[analysis_id]
                elif filter_data_type == "allele":
                    filtered_allele_ids = filter_function(
                        {analysis_genepanel: copied_allele_ids}, filter_config
                    )[analysis_genepanel]

                # We send in copied_allele_ids for the exception analysis filters
                # since they might need to take all alleles before filtering into account,
                # not just the result from the filter.
                # E.g. if excepting compound heterozygote candidates,
                # while just one was filtered, you need to see all candidates
                # in the gene to see that they might be compound candidates
                filter_exceptions = self.get_filter_exceptions(
                    exceptions_config,
                    {analysis_genepanel: filtered_allele_ids},
                    {analysis_id: copied_allele_ids},
                )

                filtered_allele_ids = set(filtered_allele_ids) - filter_exceptions
                # Ensure that filter doesn't return allele_ids not part of input
                assert not copied_allele_ids - set(
                    allele_ids
                ), f"Filter {name} returned allele_ids not in input"

                result["excluded_allele_ids"][name] = sorted(list(filtered_allele_ids))
                copied_allele_ids -= filtered_allele_ids

            except Exception:
                log.error("Error while running filter '{}'".format(name))
                raise

        result["allele_ids"] = sorted(list(copied_allele_ids))
        return result

    def filter_alleles(
        self, filter_config_id: int, gp_allele_ids: Dict[Tuple[str, str], Sequence[int]]
    ) -> Any:
        """

        Filters alleles per genepanel.

        Input:

        gp_allele_ids:
            {
                ('HBOC', 'v01'): [1, 2, 3, ...],
                ...
            }

        Returns result:
            {
                ('HBOC', 'v01'): {
                    'allele_ids': [1, 2, 3],
                    'excluded_allele_ids': {
                        'region': [6, 7],
                        'frequency': [8, 9],
                    }
                },
                ...
            }
        """

        copied_gp_allele_ids: Dict[Tuple[str, str], Set[int]] = {
            k: set(v) for k, v in gp_allele_ids.items()
        }

        # Run filter functions.
        # Already filtered alleles are tracked to avoid re-filtering
        # same alleles (for performance reasons).

        filter_config = (
            self.session.query(sample.FilterConfig.filterconfig)
            .filter(sample.FilterConfig.id == filter_config_id)
            .scalar()
        )

        result: Dict = {gp_key: {"excluded_allele_ids": dict()} for gp_key in copied_gp_allele_ids}

        filters = filter_config["filters"]
        for f in filters:
            name = f["name"]
            if name not in self.filter_functions:
                raise RuntimeError("Requested filter {} is not a valid filter name".format(name))

            try:
                filter_config = f["config"]
                exceptions_config = f.get("exceptions", [])

                filter_data_type, filter_function = self.filter_functions[name]
                assert filter_data_type in [
                    "allele",
                    "analysis",
                ], "Unknown filter data type '{}'".format(filter_data_type)

                if filter_data_type == "analysis":
                    raise RuntimeError("Invalid filter type 'analysis' when filtering alleles")

                # Check that all exception types are of type allele.
                exception_data_types = [
                    self.filter_functions[e["name"]][0] for e in exceptions_config
                ]
                assert all(
                    t == "allele" for t in exception_data_types
                ), "All exception filter types must be 'allele'"

                filtered_gp_allele_ids = filter_function(copied_gp_allele_ids, filter_config)

                filter_exceptions = self.get_filter_exceptions(
                    exceptions_config, filtered_gp_allele_ids, {}
                )

                for gp_key, allele_ids in filtered_gp_allele_ids.items():
                    # Subtract alleles that should be excepted from filtering
                    filtered_gp_allele_ids[gp_key] = set(allele_ids) - filter_exceptions

                for gp_key, filtered_allele_ids in filtered_gp_allele_ids.items():
                    if gp_key in copied_gp_allele_ids:
                        # Insert filter result in genepanel data structure to be returned
                        assert not filtered_allele_ids - set(
                            gp_allele_ids[gp_key]
                        ), f"Filter {name} returned allele_ids not in input"

                        result[gp_key]["excluded_allele_ids"][name] = sorted(
                            list(filtered_allele_ids)
                        )
                        copied_gp_allele_ids[gp_key] -= filtered_allele_ids

            except Exception:
                print("Error while running filter '{}'".format(name))
                raise

        for gp_key, remaining_allele_ids in copied_gp_allele_ids.items():
            result[gp_key]["allele_ids"] = sorted(list(remaining_allele_ids))

        return result
