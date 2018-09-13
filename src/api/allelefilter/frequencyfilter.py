from collections import OrderedDict
from sqlalchemy import or_, and_, tuple_

from vardb.datamodel import gene, annotationshadow

from api.util import queries
from api.util.genepanelconfig import GenepanelConfigResolver


class FrequencyFilter(object):

    def __init__(self, session, config):
        self.session = session
        self.config = config

    @staticmethod
    def _get_freq_num_threshold_filter(provider_numbers, freq_provider, freq_key):
        """
        Check whether we have a 'num' threshold in config for given freq_provider and freq_key (e.g. ExAC->G).
        If it's defined, the num column in allelefilter table must be greater or equal to the threshold.
        """

        if freq_provider in provider_numbers and freq_key in provider_numbers[freq_provider]:
            num_threshold = provider_numbers[freq_provider][freq_key]
            assert isinstance(num_threshold, int), 'Provided frequency num threshold is not an integer'
            return getattr(annotationshadow.AnnotationShadowFrequency, freq_provider + '_num.' + freq_key) >= num_threshold

        return None

    def _get_freq_threshold_filter(self, group_thresholds, threshold_func, combine_func):
        # frequency groups tells us what should go into e.g. 'external' and 'internal' groups
        frequency_groups = self.config['variant_criteria']['frequencies']['groups']
        frequency_provider_numbers = self.config['variant_criteria']['freq_num_thresholds']

        filters = list()
        for group, thresholds in group_thresholds.iteritems():  # 'external'/'internal', {'hi_freq_cutoff': 0.03, ...}}
            if group not in frequency_groups:
                raise RuntimeError("Group {} specified in freq_cutoffs, but it doesn't exist in configuration".format(group))

            for freq_provider, freq_keys in frequency_groups[group].iteritems():  # 'ExAC', ['G', 'SAS', ...]
                for freq_key in freq_keys:
                    filters.append(
                        threshold_func(frequency_provider_numbers, freq_provider, freq_key, thresholds)
                    )

        return combine_func(*filters)

    def _common_threshold(self, provider_numbers, freq_provider, freq_key, thresholds):
        """
        Creates SQLAlchemy filter for common threshold for a single frequency provider and key.
        Example: ExAG.G > hi_freq_cutoff
        """
        freq_key_filters = list()
        num_filter = FrequencyFilter._get_freq_num_threshold_filter(provider_numbers, freq_provider, freq_key)
        if num_filter is not None:
            freq_key_filters.append(num_filter)
        freq_key_filters.append(
            getattr(annotationshadow.AnnotationShadowFrequency, freq_provider + '.' + freq_key) >= thresholds['hi_freq_cutoff']
        )

        return and_(*freq_key_filters)

    def _less_common_threshold(self, provider_numbers, freq_provider, freq_key, thresholds):
        """
        Creates SQLAlchemy filter for less_common threshold for a single frequency provider and key.
        Example: ExAG.G < hi_freq_cutoff AND ExAG.G >= lo_freq_cutoff
        """
        freq_key_filters = list()
        num_filter = FrequencyFilter._get_freq_num_threshold_filter(provider_numbers, freq_provider, freq_key)
        if num_filter is not None:
            freq_key_filters.append(num_filter)

        freq_key_filters.append(
            and_(
                getattr(annotationshadow.AnnotationShadowFrequency, freq_provider + '.' + freq_key) < thresholds['hi_freq_cutoff'],
                getattr(annotationshadow.AnnotationShadowFrequency, freq_provider + '.' + freq_key) >= thresholds['lo_freq_cutoff']
            )
        )

        return and_(*freq_key_filters)

    def _low_freq_threshold(self, provider_numbers, freq_provider, freq_key, thresholds):
        """
        Creates SQLAlchemy filter for low_freq threshold for a single frequency provider and key.
        Example: ExAG.G < lo_freq_cutoff
        """
        freq_key_filters = list()
        num_filter = FrequencyFilter._get_freq_num_threshold_filter(provider_numbers, freq_provider, freq_key)
        if num_filter is not None:
            freq_key_filters.append(num_filter)
        freq_key_filters.append(
            getattr(annotationshadow.AnnotationShadowFrequency, freq_provider + '.' + freq_key) < thresholds['lo_freq_cutoff']
        )

        return and_(*freq_key_filters)

    @staticmethod
    def _is_freq_null(threshhold_config, freq_provider, freq_key, thresholds):
        """
        Creates SQLAlchemy filter for checking whether frequency is null for a single frequency provider and key.
        Example: ExAG.G IS NULL

        :note: Function signature is same as other threshold filters in order for them to be called dynamically.
        """
        return getattr(annotationshadow.AnnotationShadowFrequency, freq_provider + '.' + freq_key).is_(None)

    def _create_freq_filter(self, genepanels, gp_allele_ids, threshold_func, combine_func):

        gp_filter = dict()  # {('HBOC', 'v01'): <SQLAlchemy filter>, ...}

        for gp_key, gp_allele_ids in gp_allele_ids.iteritems():  # loop over every genepanel, with related genes

            genepanel = next(g for g in genepanels if g.name == gp_key[0] and g.version == gp_key[1])
            gp_config_resolver = GenepanelConfigResolver(
                self.session,
                genepanel=genepanel,
                genepanel_default=self.config['variant_criteria']['genepanel_config']
            )

            # Create the different kinds of frequency filters
            #
            # We have three types of filters:
            # 1. Gene specific treshold overrides. Targets one gene.
            # 2. AD specific thresholds. Targets set of genes with _only_ 'AD' inheritance.
            # 3. The rest. Uses 'default' threshold, targeting all genes not in 1. and 2.

            # Since the AnnotationShadowFrequency table doesn't include gene symbol,
            # we use AnnotationShadowTranscript to find allele_ids we'll include
            # for a given set of genes, according to genepanel

            # TODO: Fix overlapping genes with one gene with specified thresholds less trict than default (or other gene)

            gp_final_filter = list()

            # 1. Gene specific filters
            override_genes = gp_config_resolver.get_genes_with_overrides()
            overridden_allele_ids = set()

            # Optimization: adding filters for genes not present in our alleles is costly -> only filter the symbols
            # that overlap with the alleles in question.
            override_genes = self.session.query(annotationshadow.AnnotationShadowTranscript.symbol).filter(
                annotationshadow.AnnotationShadowTranscript.symbol.in_(override_genes),
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(gp_allele_ids),
            ).distinct().all()
            override_genes = [a[0] for a in override_genes]

            for symbol in override_genes:
                # Get merged genepanel for this gene/symbol
                symbol_group_thresholds = gp_config_resolver.resolve(symbol)['freq_cutoffs']
                allele_ids_for_genes = self.session.query(annotationshadow.AnnotationShadowTranscript.allele_id).filter(
                    # TODO: Change to HGNC id when ready
                    annotationshadow.AnnotationShadowTranscript.symbol == symbol,
                    annotationshadow.AnnotationShadowTranscript.allele_id.in_(gp_allele_ids)
                )

                # Update overridden allele ids: This will not be filtered on AD or default
                overridden_allele_ids.update(set([a[0] for a in allele_ids_for_genes]))

                gp_final_filter.append(
                    and_(
                        annotationshadow.AnnotationShadowFrequency.allele_id.in_(allele_ids_for_genes),
                        self._get_freq_threshold_filter(symbol_group_thresholds,
                                                        threshold_func,
                                                        combine_func)
                    )
                )

            # 2. AD genes
            ad_genes = queries.distinct_inheritance_genes_for_genepanel(
                self.session,
                'AD',
                gp_key[0],
                gp_key[1]
            )
            if ad_genes:
                ad_filters = [
                    annotationshadow.AnnotationShadowTranscript.symbol.in_(ad_genes),

                    annotationshadow.AnnotationShadowTranscript.allele_id.in_(gp_allele_ids)
                ]

                if overridden_allele_ids:
                    ad_filters.append(~annotationshadow.AnnotationShadowTranscript.allele_id.in_(overridden_allele_ids))

                allele_ids_for_genes = self.session.query(annotationshadow.AnnotationShadowTranscript.allele_id).filter(
                    *ad_filters
                )

                ad_group_thresholds = gp_config_resolver.get_AD_freq_cutoffs()
                gp_final_filter.append(
                    and_(
                        annotationshadow.AnnotationShadowFrequency.allele_id.in_(allele_ids_for_genes),
                        self._get_freq_threshold_filter(ad_group_thresholds,
                                                        threshold_func,
                                                        combine_func)
                    )
                )

            # 3. 'default' genes (all genes not in two above cases)
            # Keep ad_genes as subquery, or else performance goes down the drain
            # (as opposed to loading the symbols into backend and merging with override_genes -> up to 30x slower)
            default_group_thresholds = gp_config_resolver.get_default_freq_cutoffs()
            default_filters = [
                ~annotationshadow.AnnotationShadowTranscript.symbol.in_(ad_genes),
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(gp_allele_ids)
            ]

            if overridden_allele_ids:
                default_filters.append(~annotationshadow.AnnotationShadowTranscript.allele_id.in_(overridden_allele_ids),)

            allele_ids_for_genes = self.session.query(annotationshadow.AnnotationShadowTranscript.allele_id).filter(
                *default_filters
            ).distinct()

            gp_final_filter.append(
                and_(
                    annotationshadow.AnnotationShadowFrequency.allele_id.in_(allele_ids_for_genes),
                    self._get_freq_threshold_filter(default_group_thresholds,
                                                    threshold_func,
                                                    combine_func)
                )
            )

            # Construct final filter for the genepanel
            gp_filter[gp_key] = or_(*gp_final_filter)
        return gp_filter

    def get_commonness_groups(self, gp_allele_ids, common_only=False):
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
        :param common_only: Whether to only check for 'common' group. Use when you only need the common group, as it's faster.
        :returns: Structure with results for the three categories.

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

        # First get all genepanel object for the genepanels given in input
        genepanels = self.session.query(
            gene.Genepanel
        ).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(gp_allele_ids.keys())
        ).all()

        commonness_entries = [
            ('common', dict()),
        ]
        if not common_only:
            commonness_entries += [
                ('less_common', dict()),
                ('low_freq', dict()),
                ('null_freq', dict())
            ]
        commonness_result = OrderedDict(commonness_entries)  # Ordered to get final_result processing correct later

        threshold_funcs = {
            'common': (self._common_threshold, or_),
            'less_common': (self._less_common_threshold, or_),
            'low_freq': (self._low_freq_threshold, or_),
            'null_freq': (self._is_freq_null, and_)
        }

        for commonness_group, result in commonness_result.iteritems():

            # Create query filter this genepanel
            gp_filters = self._create_freq_filter(
                genepanels,
                gp_allele_ids,
                threshold_funcs[commonness_group][0],
                combine_func=threshold_funcs[commonness_group][1]
            )

            for gp_key, al_ids in gp_allele_ids.iteritems():
                assert all(isinstance(a, int) for a in al_ids)
                allele_ids = self.session.query(annotationshadow.AnnotationShadowFrequency.allele_id).filter(
                    gp_filters[gp_key],
                    annotationshadow.AnnotationShadowFrequency.allele_id.in_(al_ids)
                ).distinct()
                result[gp_key] = [a[0] for a in allele_ids.all()]

        # Create final result structure.
        # The database queries can place one allele id as part of many groups,
        # but we'd like to place each in the highest group only.
        final_result = {k: dict() for k in gp_allele_ids}
        for gp_key in final_result:
            added_thus_far = set()
            for k, v in commonness_result.iteritems():
                final_result[gp_key][k] = set([aid for aid in v[gp_key] if aid not in added_thus_far])
                added_thus_far.update(set(v[gp_key]))

            if not common_only:
                # Add all not part of the groups to a 'num_threshold' group,
                # since they must have missed freq num threshold
                final_result[gp_key]['num_threshold'] = set(gp_allele_ids[gp_key]) - added_thus_far

        return final_result

    def filter_alleles(self, gp_allele_ids):
        """
        Filters allele ids from input based on their frequency.

        The filtering will happen according to the genepanel's specified
        configuration.

        If any alleles have an existing classification according to config
        'exclude_filtering_existing_assessment', they will be excluded from the
        result.

        :param gp_allele_ids: Dict of genepanel key with corresponding allele_ids {('HBOC', 'v01'): [1, 2, 3])}
        :returns: Structure similar to input, but only containing set() with allele ids that have high frequency.

        :note: The returned values are allele ids that were _filtered out_
        based on frequency, i.e. they have a high frequency value, not the ones
        that should be included.
        """

        commonness_result = self.get_commonness_groups(gp_allele_ids, common_only=True)
        frequency_filtered = dict()

        for gp_key, commonness_group in commonness_result.iteritems():
            frequency_filtered[gp_key] = commonness_group['common']

        return frequency_filtered
