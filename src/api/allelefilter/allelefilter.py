from typing import Any, Dict, List, Optional, Set, Tuple, Sequence, Union
from sqlalchemy.orm.session import Session

from api.config import config as global_config, get_filter_config
from vardb.datamodel import sample

from api.allelefilter.frequencyfilter import FrequencyFilter
from api.allelefilter.segregationfilter import SegregationFilter
from api.allelefilter.regionfilter import RegionFilter
from api.allelefilter.qualityfilter import QualityFilter
from api.allelefilter.classificationfilter import ClassificationFilter
from api.allelefilter.externalfilter import ExternalFilter
from api.allelefilter.polypyrimidinetractfilter import PolypyrimidineTractFilter
from api.allelefilter.consequencefilter import ConsequenceFilter


class AlleleFilter(object):
    def __init__(self, session: Session, config: Optional[Dict] = None) -> None:
        self.session = session
        self.config = global_config if not config else config

        self.filter_functions = {
            "frequency": ("allele", FrequencyFilter(self.session, self.config).filter_alleles),
            "region": ("allele", RegionFilter(self.session, self.config).filter_alleles),
            "classification": (
                "allele",
                ClassificationFilter(self.session, self.config).filter_alleles,
            ),
            "external": ("allele", ExternalFilter(self.session, self.config).filter_alleles),
            "ppy": ("allele", PolypyrimidineTractFilter(self.session, self.config).filter_alleles),
            "consequence": ("allele", ConsequenceFilter(self.session, self.config).filter_alleles),
            "quality": ("analysis", QualityFilter(self.session, self.config).filter_alleles),
            "segregation": (
                "analysis",
                SegregationFilter(self.session, self.config).filter_alleles,
            ),
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

    def filter_alleles(
        self,
        filter_config_id: int,
        gp_allele_ids: Optional[Dict[Tuple[str, str], Sequence[int]]],
        analysis_allele_ids: Optional[Dict[int, Sequence[int]]],
    ) -> Any:
        """

        Main function for filtering alleles. There are two kinds of
        input, standalone alleles and alleles connected to an analysis.

        Some filters work on alleles alone, while others require an analysis.
        If filtering analyses, you only need to provide the alleles as part of that
        argument, not in both.

        Input:

        gp_allele_ids:
            {
                ('HBOC', 'v01'): [1, 2, 3, ...],
                ...
            }

        analysis_allele_ids:
            {
                1: [1, 2, 3, ...],
                ...
            }

        Returns result tuple (gp_allele_ids, analysis_allele_ids):
            (
                {
                    ('HBOC', 'v01'): {
                        'allele_ids': [1, 2, 3],
                        'excluded_allele_ids': {
                            'region': [6, 7],
                            'frequency': [8, 9],
                        }
                    },
                    ...
                },

                {
                    <analysis_id>: {
                        'allele_ids': [1, 2, 3],
                        'excluded_allele_ids': {
                            'frequency': [4, 5],
                            'region': [12, 45],
                            'segregation': [6, 8],
                        }
                    },
                    ...
                }
            )
        """

        # Make copies to avoid modifying input data
        copied_analysis_allele_ids: Dict[int, Set[int]] = dict()
        if analysis_allele_ids:
            copied_analysis_allele_ids = {k: set(v) for k, v in analysis_allele_ids.items()}

        copied_gp_allele_ids: Dict[Tuple[str, str], Set[int]] = dict()
        if gp_allele_ids:
            copied_gp_allele_ids = {k: set(v) for k, v in gp_allele_ids.items()}

        analysis_genepanels = (
            self.session.query(
                sample.Analysis.id,
                sample.Analysis.genepanel_name,
                sample.Analysis.genepanel_version,
            )
            .filter(sample.Analysis.id.in_(list(copied_analysis_allele_ids.keys())))
            .all()
        )

        analysis_genepanels = {
            a.id: (a.genepanel_name, a.genepanel_version) for a in analysis_genepanels
        }

        analysis_gp_allele_ids: Dict[Tuple[str, str], Set[int]] = dict()
        for a_id, gp_key in analysis_genepanels.items():
            if gp_key not in analysis_gp_allele_ids:
                analysis_gp_allele_ids[gp_key] = set()
            analysis_gp_allele_ids[gp_key] |= set(copied_analysis_allele_ids[a_id])

        all_gp_keys = set(list(analysis_gp_allele_ids.keys()) + list(copied_gp_allele_ids.keys()))

        # Run filter functions.
        # Already filtered alleles are tracked to avoid re-filtering
        # same alleles (for performance reasons).

        filter_config = (
            self.session.query(sample.FilterConfig.filterconfig)
            .filter(sample.FilterConfig.id == filter_config_id)
            .scalar()
        )

        analysis_allele_result: Dict = {
            a_id: {"excluded_allele_ids": dict()} for a_id in copied_analysis_allele_ids
        }
        gp_allele_result: Dict = {
            gp_key: {"excluded_allele_ids": dict()} for gp_key in copied_gp_allele_ids
        }

        filters = get_filter_config(self.config, filter_config)
        for f in filters:
            name = f["name"]
            if name not in self.filter_functions:
                raise RuntimeError("Requested filter {} is not a valid filter name".format(name))

            try:
                filter_config = f["config"]
                exceptions_config = f["exceptions"]

                filter_data_type, filter_function = self.filter_functions[name]
                assert filter_data_type in [
                    "allele",
                    "analysis",
                ], "Unknown filter data type '{}'".format(filter_data_type)

                # Run filter
                if filter_data_type == "allele":
                    # Check that all exception types are of type allele. It makes no sense to run an analysis exception filter
                    # on an allele filter
                    exception_data_types = [
                        self.filter_functions[e["name"]][0] for e in exceptions_config
                    ]
                    assert all(
                        t == "allele" for t in exception_data_types
                    ), "All exception filter types must be 'allele' for an 'allele' filter"

                    # Merge analysis_gp_allele_ids and copied_gp_allele_ids
                    gp_alleles_merged = {
                        gp_key: analysis_gp_allele_ids.get(gp_key, set())
                        | copied_gp_allele_ids.get(gp_key, set())
                        for gp_key in all_gp_keys
                    }

                    filtered_gp_allele_ids = filter_function(gp_alleles_merged, filter_config)
                    filtered_analysis_allele_ids: Dict[int, Set[int]] = dict()

                elif filter_data_type == "analysis":
                    filtered_analysis_allele_ids = filter_function(
                        analysis_allele_ids, filter_config
                    )
                    filtered_gp_allele_ids = {
                        analysis_genepanels[a_id]: set() for a_id in filtered_analysis_allele_ids
                    }
                    for a_id, allele_ids in filtered_analysis_allele_ids.items():
                        filtered_gp_allele_ids[analysis_genepanels[a_id]] |= allele_ids

                filter_exceptions = self.get_filter_exceptions(
                    exceptions_config, filtered_gp_allele_ids, filtered_analysis_allele_ids
                )

                for gp_key, allele_ids in filtered_gp_allele_ids.items():
                    # Subtract alleles that should be excepted from filtering
                    filtered_gp_allele_ids[gp_key] = set(allele_ids) - filter_exceptions

                for a_id, allele_ids in filtered_analysis_allele_ids.items():
                    filtered_analysis_allele_ids[a_id] = set(allele_ids) - filter_exceptions

                # Update data structures copied_gp_allele_ids, analysis_gp_allele_ids,
                # and copied_analysis_allele_ids by removing
                # filtered alleles from the remaining alleles
                # This is done to:
                # 1. Improve performance by not running already
                #    filtered alleles in subsequent filters
                # 2. Prevent alleles from ending up in multiple filters
                if filter_data_type == "allele":
                    for gp_key, allele_ids in filtered_gp_allele_ids.items():
                        if gp_key in copied_gp_allele_ids:
                            # Insert filter result in genepanel data structure to be returned
                            gp_allele_result[gp_key]["excluded_allele_ids"][name] = sorted(
                                list(copied_gp_allele_ids[gp_key] & allele_ids)
                            )
                            copied_gp_allele_ids[gp_key] -= allele_ids

                        if gp_key in analysis_gp_allele_ids:
                            analysis_gp_allele_ids[gp_key] -= allele_ids

                            for (a_id, analysis_gp_key) in analysis_genepanels.items():
                                if analysis_gp_key == gp_key:
                                    # Insert filter result in analysis data structure to be returned
                                    analysis_allele_result[a_id]["excluded_allele_ids"][
                                        name
                                    ] = sorted(list(copied_analysis_allele_ids[a_id] & allele_ids))

                                    copied_analysis_allele_ids[a_id] -= allele_ids

                elif filter_data_type == "analysis":
                    for a_id, allele_ids in filtered_analysis_allele_ids.items():
                        # Insert filter result in analysis data structure to be returned
                        analysis_allele_result[a_id]["excluded_allele_ids"][name] = sorted(
                            list(copied_analysis_allele_ids[a_id] & allele_ids)
                        )
                        copied_analysis_allele_ids[a_id] -= allele_ids

                        analysis_gp_key = analysis_genepanels[a_id]
                        analysis_gp_allele_ids[analysis_gp_key] -= allele_ids

            except Exception:
                print("Error while running filter '{}'".format(name))
                raise

        # The alleles remaining from copied_analysis_allele_ids
        # and copied_gp_allele_ids are unfiltered
        for a_id in analysis_allele_result:
            analysis_allele_result[a_id]["allele_ids"] = sorted(
                list(copied_analysis_allele_ids[a_id])
            )
        for gp_key in gp_allele_result:
            gp_allele_result[gp_key]["allele_ids"] = sorted(list(copied_gp_allele_ids[gp_key]))

        return gp_allele_result, analysis_allele_result
