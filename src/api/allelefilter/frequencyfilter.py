import copy
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from collections import OrderedDict
from sqlalchemy import or_, and_, tuple_
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList

from vardb.datamodel import gene, annotationshadow
from api.util import queries


class FrequencyFilter(object):
    def __init__(self, session: Session, config: Dict[str, Any]) -> None:
        self.session = session
        self.config = config
        annotationshadow.check_db_consistency(self.session, self.config)

    @staticmethod
    def _get_freq_num_threshold_filter(
        num_thresholds: Dict[str, Dict[str, int]], freq_provider: str, freq_key: str
    ) -> Optional[BinaryExpression]:
        """
        Check whether we have a 'num' threshold in config for given freq_provider and freq_key (e.g. ExAC->G).
        If it's defined, the num column in allelefilter table must be greater or equal to the threshold.
        """

        if freq_provider in num_thresholds and freq_key in num_thresholds[freq_provider]:
            num_threshold = num_thresholds[freq_provider][freq_key]
            assert isinstance(
                num_threshold, int
            ), "Provided frequency num threshold is not an integer"
            return (
                getattr(
                    annotationshadow.AnnotationShadowFrequency, freq_provider + "_num." + freq_key
                )
                >= num_threshold
            )

        return None

    def _get_freq_threshold_filter(
        self,
        frequency_groups,  # frequency groups tells us what should go into e.g. 'external' and 'internal' groups
        thresholds: Dict[str, Dict[str, float]],
        num_thresholds: Dict[str, Dict[str, int]],
        threshold_func: Callable,
        combine_func: Callable,
    ) -> BooleanClauseList:

        filters = list()
        for (
            group,
            group_thresholds,
        ) in thresholds.items():  # 'external'/'internal', {'hi_freq_cutoff': 0.03, ...}}
            if group not in frequency_groups:
                raise RuntimeError(
                    "Group {} specified in freq_cutoffs, but it doesn't exist in configuration".format(
                        group
                    )
                )

            for freq_provider, freq_keys in frequency_groups[group].items():
                for freq_key in freq_keys:
                    filters.append(
                        threshold_func(num_thresholds, freq_provider, freq_key, group_thresholds)
                    )

        return combine_func(*filters)

    def _common_threshold(
        self,
        provider_numbers: Dict[str, Dict[str, int]],
        freq_provider: str,
        freq_key: str,
        thresholds: Dict[str, float],
    ) -> Union[BooleanClauseList, BinaryExpression]:
        """
        Creates SQLAlchemy filter for common threshold for a single frequency provider and key.
        Example: ExAG.G > hi_freq_cutoff
        """
        freq_key_filters = list()
        num_filter = FrequencyFilter._get_freq_num_threshold_filter(
            provider_numbers, freq_provider, freq_key
        )
        if num_filter is not None:
            freq_key_filters.append(num_filter)

        freq_key_filters.append(
            getattr(annotationshadow.AnnotationShadowFrequency, freq_provider + "." + freq_key)
            >= thresholds["hi_freq_cutoff"]
        )

        return and_(*freq_key_filters)

    def _less_common_threshold(
        self,
        provider_numbers: Dict[str, Dict[str, int]],
        freq_provider: str,
        freq_key: str,
        thresholds: Dict[str, float],
    ) -> BooleanClauseList:
        """
        Creates SQLAlchemy filter for less_common threshold for a single frequency provider and key.
        Example: ExAG.G < hi_freq_cutoff AND ExAG.G >= lo_freq_cutoff
        """
        freq_key_filters = list()
        num_filter = FrequencyFilter._get_freq_num_threshold_filter(
            provider_numbers, freq_provider, freq_key
        )
        if num_filter is not None:
            freq_key_filters.append(num_filter)

        freq_key_filters.append(
            and_(
                getattr(annotationshadow.AnnotationShadowFrequency, freq_provider + "." + freq_key)
                < thresholds["hi_freq_cutoff"],
                getattr(annotationshadow.AnnotationShadowFrequency, freq_provider + "." + freq_key)
                >= thresholds["lo_freq_cutoff"],
            )
        )

        return and_(*freq_key_filters)

    def _low_freq_threshold(
        self,
        provider_numbers: Dict[str, Dict[str, int]],
        freq_provider: str,
        freq_key: str,
        thresholds: Dict[str, float],
    ) -> Union[BooleanClauseList, BinaryExpression]:
        """
        Creates SQLAlchemy filter for low_freq threshold for a single frequency provider and key.
        Example: ExAG.G < lo_freq_cutoff
        """
        freq_key_filters = list()
        num_filter = FrequencyFilter._get_freq_num_threshold_filter(
            provider_numbers, freq_provider, freq_key
        )
        if num_filter is not None:
            freq_key_filters.append(num_filter)
        freq_key_filters.append(
            getattr(annotationshadow.AnnotationShadowFrequency, freq_provider + "." + freq_key)
            < thresholds["lo_freq_cutoff"]
        )

        return and_(*freq_key_filters)

    @staticmethod
    def _is_freq_null(
        threshhold_config: Dict[str, Dict[str, int]],
        freq_provider: str,
        freq_key: str,
        thresholds: Dict[str, float],
    ) -> BinaryExpression:
        """
        Creates SQLAlchemy filter for checking whether frequency is
        null for a single frequency provider and key.
        Example: ExAG.G IS NULL

        :note: Function signature is same as other threshold filters in order
         for them to be called dynamically.
        """
        return getattr(
            annotationshadow.AnnotationShadowFrequency, freq_provider + "." + freq_key
        ).is_(None)

    def _create_freq_filter(
        self,
        filter_config: Dict[str, Any],
        genepanels: List[gene.Genepanel],
        gp_allele_ids: Dict[Tuple[str, str], List[int]],
        threshold_func: Callable,
        combine_func: Callable,
    ) -> Dict[Tuple[str, str], BooleanClauseList]:

        gp_filter = dict()  # {('HBOC', 'v01'): <SQLAlchemy filter>, ...}

        # Filter config could be loaded from json and have string keys for 'genes'
        # hgnc ids. We want to use int, so we convert the config.
        filter_config = dict(filter_config)

        per_gene_config = filter_config.pop("genes", {})
        per_gene_config = {int(k): v for k, v in per_gene_config.items()}
        per_gene_hgnc_ids = list(per_gene_config.keys())

        for (
            gp_key,
            allele_ids,
        ) in gp_allele_ids.items():  # loop over every genepanel, with related genes

            # Create the different kinds of frequency filters
            #
            # We have three types of filters:
            # 1. Gene specific treshold overrides. Targets one gene.
            # 2. AD specific thresholds. Targets set of genes with _only_ 'AD' inheritance.
            # 3. The rest. Uses 'default' threshold, targeting all genes not in 1. and 2.

            # Since the AnnotationShadowFrequency table doesn't include gene symbol,
            # we use AnnotationShadowTranscript to find allele_ids we'll include
            # for a given set of genes, according to genepanel

            # TODO: Fix overlapping genes with one gene with specified thresholds
            # less trict than default (or other gene)

            # "Compiling" queries is slow, so cache the slowest
            ast_gp_alleles = annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids)

            gp_final_filter = list()

            # 1. Gene specific filters
            overridden_allele_ids = set()
            if per_gene_hgnc_ids:

                # Optimization: adding filters for genes not present in our alleles
                # is costly -> only filter the symbols
                # that overlap with the alleles in question.
                present_hgnc_ids = (
                    self.session.query(annotationshadow.AnnotationShadowTranscript.hgnc_id)
                    .filter(
                        annotationshadow.AnnotationShadowTranscript.hgnc_id.in_(per_gene_hgnc_ids),
                        ast_gp_alleles,
                    )
                    .distinct()
                    .all()
                )
                present_hgnc_ids = [a[0] for a in present_hgnc_ids]

                for hgnc_id in present_hgnc_ids:
                    # Create merged filter_config for this gene
                    gene_filter_config = dict(filter_config)
                    # If a gene is overridden, overiding 'thresholds' is required
                    if "thresholds" not in per_gene_config[hgnc_id]:
                        raise RuntimeError(
                            "Missing required key 'thresholds' when overriding filter config for hgnc_id {}".format(
                                hgnc_id
                            )
                        )
                    gene_filter_config.update(per_gene_config[hgnc_id])

                    allele_ids_for_genes = self.session.query(
                        annotationshadow.AnnotationShadowTranscript.allele_id
                    ).filter(
                        annotationshadow.AnnotationShadowTranscript.hgnc_id == hgnc_id,
                        ast_gp_alleles,
                    )

                    # Update overridden allele ids: This will not be filtered on AD or default
                    overridden_allele_ids.update(set([a[0] for a in allele_ids_for_genes]))
                    gp_final_filter.append(
                        and_(
                            annotationshadow.AnnotationShadowFrequency.allele_id.in_(
                                allele_ids_for_genes
                            ),
                            self._get_freq_threshold_filter(
                                filter_config["groups"],
                                gene_filter_config["thresholds"],
                                gene_filter_config["num_thresholds"],
                                threshold_func,
                                combine_func,
                            ),
                        )
                    )

            # 2. AD genes
            ad_hgnc_ids = queries.distinct_inheritance_hgnc_ids_for_genepanel(
                self.session, "AD", gp_key[0], gp_key[1]
            )
            if ad_hgnc_ids:
                ad_filters = [
                    annotationshadow.AnnotationShadowTranscript.hgnc_id.in_(ad_hgnc_ids),
                    ast_gp_alleles,
                ]

                if overridden_allele_ids:
                    ad_filters.append(
                        ~annotationshadow.AnnotationShadowTranscript.allele_id.in_(
                            overridden_allele_ids
                        )
                    )

                allele_ids_for_genes = self.session.query(
                    annotationshadow.AnnotationShadowTranscript.allele_id
                ).filter(*ad_filters)

                gp_final_filter.append(
                    and_(
                        annotationshadow.AnnotationShadowFrequency.allele_id.in_(
                            allele_ids_for_genes
                        ),
                        self._get_freq_threshold_filter(
                            filter_config["groups"],
                            filter_config["thresholds"]["AD"],
                            filter_config["num_thresholds"],
                            threshold_func,
                            combine_func,
                        ),
                    )
                )

            # 3. 'default' genes (all genes not in two above cases)
            # Keep ad_genes as subquery, or else performance goes down the drain
            # (as opposed to loading the symbols into backend and
            # merging with override_genes -> up to 30x slower)
            default_filters = [
                ~annotationshadow.AnnotationShadowTranscript.hgnc_id.in_(ad_hgnc_ids),
                ast_gp_alleles,
            ]

            if overridden_allele_ids:
                default_filters.append(
                    ~annotationshadow.AnnotationShadowTranscript.allele_id.in_(
                        overridden_allele_ids
                    )
                )

            allele_ids_for_genes = (
                self.session.query(annotationshadow.AnnotationShadowTranscript.allele_id)
                .filter(*default_filters)
                .distinct()
            )

            gp_final_filter.append(
                and_(
                    annotationshadow.AnnotationShadowFrequency.allele_id.in_(allele_ids_for_genes),
                    self._get_freq_threshold_filter(
                        filter_config["groups"],
                        filter_config["thresholds"]["default"],
                        filter_config["num_thresholds"],
                        threshold_func,
                        combine_func,
                    ),
                )
            )

            # Construct final filter for the genepanel
            gp_filter[gp_key] = or_(*gp_final_filter)
        return gp_filter

    def get_commonness_groups(
        self,
        gp_allele_ids: Dict[Tuple[str, str], List[int]],
        filter_config: Dict[str, Any],
        common_only: bool = False,
    ) -> Dict[Tuple[str, str], Dict[str, Set[int]]]:
        """
        Categorizes allele ids according to their annotation frequency
        and the thresholds in the genepanel configuration.
        There are five categories:
            'common', 'less_common', 'low_freq', 'null_freq' and 'num_threshold'.

        common:       {freq} >= 'hi_freq_cutoff'
        less_common:  'lo_freq_cutoff' >= {freq} < 'hi_freq_cutoff'
        low_freq:     {freq} < 'lo_freq_cutoff'
        null_freq:     All {freq} == null
        num_threshold: Not part of above groups, and below 'num' threshold for all relevant {freq}

        :note: Allele ids with no frequencies are not excluded from the results.

        :param gp_allele_ids: {('HBOC', 'v01'): [1, 2, 3, ...], ...}
        :param common_only: Whether to only check for 'common' group. Use when you only
                            need the common group, as it's faster.
        :returns: Structure with results for the three categories.

        Filter config example:
        {
            "num_thresholds": {
                "GNOMAD_GENOMES": {
                    "G": 5000,
                    ...
                },
                "GNOMAD_EXOMES": {
                    "G": 5000,
                    ...
                }
            },
            "thresholds": {
                "AD": {
                    "external": { "hi_freq_cutoff": 0.005, "lo_freq_cutoff": 0.001 },
                    "internal": { "hi_freq_cutoff": 0.05, "lo_freq_cutoff": 1.0 }
                },
                "default": {
                    "external": { "hi_freq_cutoff": 0.01, "lo_freq_cutoff": 1.0 },
                    "internal": { "hi_freq_cutoff": 0.05, "lo_freq_cutoff": 1.0 }
                }
            },
            "genes": {  # Optional
                "1101": {
                    "thresholds": {  # Mandatory if gene override
                        "external": { "hi_freq_cutoff": 0.005, "lo_freq_cutoff": 0.001 },
                        "internal": { "hi_freq_cutoff": 0.05, "lo_freq_cutoff": 1.0 }
                    },
                    "num_thresholds": {...}  # Optional, will use outer level if not provided
                }
            }
        }

        :note: The filter_config for this function is very similar to filter_alleles()'s
               filter_config, but they're not the same.

        Example for returned data:
        {
            ('HBOC', 'v01'): {
                'common': [1, 2, ...],
                'less_common': [5, 84, ...],
                'low_freq': [13, 40, ...],
                'null_freq': [14, 34, ...],
                'num_threshold': [50],
            }
        }
        """
        annotationshadow.check_db_consistency(
            self.session, {"frequencies": filter_config}, subset=True
        )

        # First get all genepanel object for the genepanels given in input
        genepanels = (
            self.session.query(gene.Genepanel)
            .filter(
                tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(list(gp_allele_ids.keys()))
            )
            .all()
        )

        commonness_entries: List[Tuple[str, Dict]] = [("common", dict())]
        if not common_only:
            commonness_entries += [
                ("less_common", dict()),
                ("low_freq", dict()),
                ("null_freq", dict()),
            ]
        commonness_result = OrderedDict(
            commonness_entries
        )  # Ordered to get final_result processing correct later

        threshold_funcs = {
            "common": (self._common_threshold, or_),
            "less_common": (self._less_common_threshold, or_),
            "low_freq": (self._low_freq_threshold, or_),
            "null_freq": (self._is_freq_null, and_),
        }

        for commonness_group, result in commonness_result.items():

            # Create query filter this genepanel
            gp_filters = self._create_freq_filter(
                filter_config,
                genepanels,
                gp_allele_ids,
                threshold_funcs[commonness_group][0],
                combine_func=threshold_funcs[commonness_group][1],
            )

            for gp_key, al_ids in gp_allele_ids.items():
                assert all(isinstance(a, int) for a in al_ids)
                allele_ids = (
                    self.session.query(annotationshadow.AnnotationShadowFrequency.allele_id)
                    .filter(
                        gp_filters[gp_key],
                        annotationshadow.AnnotationShadowFrequency.allele_id.in_(al_ids),
                    )
                    .distinct()
                )

                result[gp_key] = [a[0] for a in allele_ids.all()]

        # Create final result structure.
        # The database queries can place one allele id as part of many groups,
        # but we'd like to place each in the highest group only.
        final_result: Dict[Tuple[str, str], Dict[str, Set[int]]] = {
            k: dict() for k in gp_allele_ids
        }
        for gp_key in final_result:
            added_thus_far: Set = set()
            for k, v in commonness_result.items():
                final_result[gp_key][k] = set(
                    [aid for aid in v[gp_key] if aid not in added_thus_far]
                )
                added_thus_far.update(set(v[gp_key]))

            if not common_only:
                # Add all not part of the groups to a 'num_threshold' group,
                # since they must have missed freq num threshold
                final_result[gp_key]["num_threshold"] = set(gp_allele_ids[gp_key]) - added_thus_far

        return final_result

    def filter_alleles(
        self, gp_allele_ids: Dict[Tuple[str, str], List[int]], filter_config: Dict[str, Any]
    ) -> Dict[Tuple[str, str], Set[int]]:
        """
        Filters allele ids from input based on their frequency.

        Filter config example:
            "num_thresholds": {
                "GNOMAD_GENOMES": {
                    "G": 5000,
                    ...
                },
                "GNOMAD_EXOMES": {
                    "G": 5000,
                    ...
                }
            },
            "thresholds": {
                "AD": {
                    "external": 0.005,
                    "internal": 0.05
                },
                "default": {
                    "external": 0.01,
                    "internal": 0.05
                }
            }

        The frequency groups ('external' and 'internal' in above example) are
        provided in the main application config.

        :param filter_config: Filter configuration
        :param gp_allele_ids: Dict of genepanel key with corresponding
                              allele_ids {('HBOC', 'v01'): [1, 2, 3])}
        :returns: Structure similar to input, but only containing set()
                  with allele ids that have high frequency.

        :note: The returned values are allele ids that were _filtered out_
        based on frequency, i.e. they have a high frequency value, not the ones
        that should be included.
        """

        # Internally get_commonness_groups works with two thresholds,
        # hi_freq_cutoff and lo_freq_cutoff. We need to convert our simpler
        # filter config to this format. Since we request
        # common_only, we only need to provide 'hi_freq_cutoff'

        filter_config = copy.deepcopy(filter_config)
        for key in ["AD", "default"]:
            for group in filter_config["thresholds"][key]:
                filter_config["thresholds"][key][group] = {
                    "hi_freq_cutoff": filter_config["thresholds"][key][group]
                }
        for hgnc_id in filter_config.get("genes", []):
            # 'thresholds' is mandatory for gene overrides
            for group in filter_config["genes"][hgnc_id]["thresholds"]:
                filter_config["genes"][hgnc_id]["thresholds"][group] = {
                    "hi_freq_cutoff": filter_config["genes"][hgnc_id]["thresholds"][group]
                }

        commonness_result = self.get_commonness_groups(
            gp_allele_ids, filter_config, common_only=True
        )
        frequency_filtered = dict()

        for gp_key, commonness_group in commonness_result.items():
            frequency_filtered[gp_key] = commonness_group["common"]

        return frequency_filtered
