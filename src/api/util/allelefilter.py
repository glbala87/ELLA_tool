from collections import OrderedDict, defaultdict
from sqlalchemy import or_, and_, tuple_, text, func, column, literal

from api.config import config as global_genepanel_default
from vardb.datamodel import assessment, gene, annotation, annotationshadow

from api.util import queries
from api.util.genepanelconfig import GenepanelConfigResolver


class AlleleFilter(object):

    def __init__(self, session, global_config=None):
        """
        :param session:
        :param global_config: only set when testing. Else the global config in api/config.py is used
        """
        self.session = session
        self.global_config = global_genepanel_default if not global_config else global_config

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
        frequency_groups = self.global_config['variant_criteria']['frequencies']['groups']
        frequency_provider_numbers = self.global_config['variant_criteria']['freq_num_thresholds']

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
        num_filter = AlleleFilter._get_freq_num_threshold_filter(provider_numbers, freq_provider, freq_key)
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
        num_filter = AlleleFilter._get_freq_num_threshold_filter(provider_numbers, freq_provider, freq_key)
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
        num_filter = AlleleFilter._get_freq_num_threshold_filter(provider_numbers, freq_provider, freq_key)
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
                genepanel_default=self.global_config['variant_criteria']['genepanel_config']
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

            gp_final_filter = list()

            # Gene specific filters
            override_genes = gp_config_resolver.get_genes_with_overrides()

            for symbol in override_genes:
                # Get merged genepanel for this gene/symbol
                symbol_group_thresholds = gp_config_resolver.resolve(symbol)['freq_cutoffs']
                allele_ids_for_genes = self.session.query(annotationshadow.AnnotationShadowTranscript.allele_id).filter(
                    # TODO: Change to HGNC id when ready
                    annotationshadow.AnnotationShadowTranscript.symbol == symbol,
                    annotationshadow.AnnotationShadowTranscript.allele_id.in_(gp_allele_ids)
                )
                gp_final_filter.append(
                    and_(
                        annotationshadow.AnnotationShadowFrequency.allele_id.in_(allele_ids_for_genes),
                        self._get_freq_threshold_filter(symbol_group_thresholds,
                                                        threshold_func,
                                                        combine_func)
                    )
                )

            # AD genes
            ad_genes = queries.ad_genes_for_genepanel(self.session, gp_key[0], gp_key[1])
            if ad_genes:
                allele_ids_for_genes = self.session.query(annotationshadow.AnnotationShadowTranscript.allele_id).filter(
                    annotationshadow.AnnotationShadowTranscript.symbol.in_(ad_genes),
                    ~annotationshadow.AnnotationShadowTranscript.symbol.in_(override_genes),
                    annotationshadow.AnnotationShadowTranscript.allele_id.in_(gp_allele_ids)
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

            # 'default' genes (all genes not in two above cases)
            # Keep ad_genes as subquery, or else performance goes down the drain
            # (as opposed to loading the symbols into backend and merging with override_genes -> up to 30x slower)
            default_group_thresholds = gp_config_resolver.get_default_freq_cutoffs()
            allele_ids_for_genes = self.session.query(annotationshadow.AnnotationShadowTranscript.allele_id).filter(
                ~annotationshadow.AnnotationShadowTranscript.symbol.in_(ad_genes),
                ~annotationshadow.AnnotationShadowTranscript.symbol.in_(override_genes),
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(gp_allele_ids)
            )

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
                final_result[gp_key][k] = [aid for aid in v[gp_key] if aid not in added_thus_far]
                added_thus_far.update(set(v[gp_key]))

            if not common_only:
                # Add all not part of the groups to a 'num_threshold' group,
                # since they must have missed freq num threshold
                final_result[gp_key]['num_threshold'] = [aid for aid in gp_allele_ids[gp_key] if aid not in added_thus_far]

        return final_result

    def remove_alleles_with_classification(self, allele_ids):
        """
        Return the allele ids that have have an existing classification according with
        global config ['classification']['options']

        Reason: alleles with classification should be displayed to the user.

        """

        options = self.global_config['classification']['options']
        exclude_for_class = [o['value'] for o in options if o.get('exclude_filtering_existing_assessment')]

        with_classification = list()

        if allele_ids:
            with_classification = self.session.query(assessment.AlleleAssessment.allele_id).filter(
                assessment.AlleleAssessment.classification.in_(exclude_for_class),
                assessment.AlleleAssessment.allele_id.in_(allele_ids),
                assessment.AlleleAssessment.date_superceeded.is_(None)
            ).all()
            with_classification = [t[0] for t in with_classification]

        return filter(lambda i: i not in with_classification, allele_ids)

    def filtered_gene(self, gp_allele_ids):
        """
        Only return the allele IDs whose gene symbol are configured to be excluded.

        Currently this is not configured, as exclusion is built into the pipeline
        producing variants to ella.
        """

        gene_filtered = dict()
        for gp_key, _ in gp_allele_ids.iteritems():
            gene_filtered[gp_key] = list()  # no alleles are filtered away based on gene symbol only

        return gene_filtered

    def filtered_intronic(self, gp_allele_ids):
        """
        Filters allele ids from input based on their distance to nearest
        exon edge.

        The filtering will happen according to the genepanel's specified
        configuration, specifying what exon_distance defines intronic status.

        If any alleles have an existing classification according to config
        'exclude_filtering_existing_assessment', they will be excluded from the
        result.

        :param gp_allele_ids: Dict of genepanel key with corresponding allele_ids {('HBOC', 'v01'): [1, 2, 3])}
        :returns: Structure similar to input, but only containing allele ids that are intronic.

        :note: The returned values are allele ids that were _filtered out_
        based on intronic status, i.e. they are intronic.
        """

        intronic_filtered = dict()
        # TODO: Add support for per gene/genepanel configuration when ready.
        intronic_region = self.global_config['variant_criteria']['intronic_region']
        for gp_key, allele_ids in gp_allele_ids.iteritems():

            # Determine which allele ids are in an exon (with exon_distance == None, or within intronic_region)
            exonic_alleles_q = self.session.query(
                annotationshadow.AnnotationShadowTranscript.allele_id,
                annotationshadow.AnnotationShadowTranscript.exon_distance,
                annotationshadow.AnnotationShadowTranscript.transcript
            ).filter(
                or_(
                    annotationshadow.AnnotationShadowTranscript.exon_distance.is_(None),
                    or_(
                        and_(
                            annotationshadow.AnnotationShadowTranscript.exon_distance >= intronic_region[0],
                            annotationshadow.AnnotationShadowTranscript.exon_distance <= intronic_region[1],
                        ),
                        and_(
                            annotationshadow.AnnotationShadowTranscript.exon_distance <= intronic_region[1],
                            annotationshadow.AnnotationShadowTranscript.exon_distance >= intronic_region[0],
                        )
                    )
                ),
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids)
            )
            inclusion_regex = self.global_config.get("transcripts", {}).get("inclusion_regex")
            if inclusion_regex:
                exonic_alleles_q = exonic_alleles_q.filter(
                    text("transcript ~ :reg").params(reg=inclusion_regex)
                )
            exonic_alleles_q = exonic_alleles_q.distinct()

            exonic_allele_ids = [a[0] for a in exonic_alleles_q.all()]
            intronic_filtered[gp_key] = list(set(allele_ids) - set(exonic_allele_ids))

        # Remove the ones with existing classification
        for gp_key, allele_ids in intronic_filtered.iteritems():
            intronic_filtered[gp_key] = self.remove_alleles_with_classification(allele_ids)

        return intronic_filtered

    def filtered_frequency(self, gp_allele_ids):
        """
        Filters allele ids from input based on their frequency.

        The filtering will happen according to the genepanel's specified
        configuration.

        If any alleles have an existing classification according to config
        'exclude_filtering_existing_assessment', they will be excluded from the
        result.

        :param gp_allele_ids: Dict of genepanel key with corresponding allele_ids {('HBOC', 'v01'): [1, 2, 3])}
        :returns: Structure similar to input, but only containing allele ids that have high frequency.

        :note: The returned values are allele ids that were _filtered out_
        based on frequency, i.e. they have a high frequency value, not the ones
        that should be included.
        """

        commonness_result = self.get_commonness_groups(gp_allele_ids, common_only=True)
        frequency_filtered = dict()

        for gp_key, commonness_group in commonness_result.iteritems():
            frequency_filtered[gp_key] = self.remove_alleles_with_classification(commonness_group['common'])

        return frequency_filtered

    def filtered_utr(self, gp_allele_ids):
        """
        Filters out variants that have worst consequence equal to 3_prime_UTR_variant or 5_prime_UTR_variant in any
        of the annotation transcripts included.
        :param allele_ids: allele_ids to run filter on
        :return: allele ids to be filtered out
        """
        consequences_ordered = self.global_config["transcripts"].get("consequences")
        utr_consequences = [
            # If you change these to not be hard coded,
            # change code further down to avoid injection risk
            '3_prime_UTR_variant',
            '5_prime_UTR_variant'
        ]

        # TODO: Potential optimization: Since we don't care about genepanel,
        # we can merge all allele_ids into one query, then unpack afterwards
        utr_filtered = dict()
        for gp_key, allele_ids in gp_allele_ids.iteritems():

            # An ordering of consequences has not been specified, return empty list
            if not consequences_ordered:
                utr_filtered[gp_key] = []
                continue

            # Also return empty list if *_prime_UTR_variant is not specified in consequences_ordered
            if not any(u in consequences_ordered for u in utr_consequences):
                utr_filtered[gp_key] = []
                continue

            # For performance: Only get allele ids that are relevant for filtering
            candidate_filters = []
            for c in utr_consequences:
                candidate_filters.append(
                    annotationshadow.AnnotationShadowTranscript.consequences.contains(text("ARRAY['{}']::character varying[]".format(c)))
                )
            candidate_allele_ids = self.session.query(annotationshadow.AnnotationShadowTranscript.allele_id).filter(
                or_(
                    *candidate_filters
                ),
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids)
            )

            inclusion_regex = self.global_config.get("transcripts", {}).get("inclusion_regex")
            if inclusion_regex:
                candidate_allele_ids = candidate_allele_ids.filter(
                    text("transcript ~ :reg").params(reg=inclusion_regex)
                )

            # Help table: Take the config's consequences array and order it by index in array
            # --------------------------------------------
            # | consequence                    |   ord   |
            # --------------------------------------------
            # | downstream_gene_variant        | 10      |
            # | downstream_gene_variant        | 10      |
            # | non_coding_transcript_variant  | 14      |
            # ...
            consequence_order = text('''
                SELECT consequence, ord
                FROM   unnest(string_to_array(:consequences, ',')) WITH ORDINALITY t(consequence, ord)
            ''').bindparams(
                consequences=','.join(consequences_ordered)
            ).columns(column('consequence'), column('ord')).alias('consequenceorder')

            # Unnest the AnnotationShadowTranscript's consequences into rows
            # -------------------------------------------------
            # | allele_id | consequence                        |
            # -------------------------------------------------
            # | 10348     | downstream_gene_variant            |
            # | 9986      | downstream_gene_variant            |
            # | 11400     | non_coding_transcript_variant      |
            #  ...
            unpacked_consequences = self.session.query(
                annotationshadow.AnnotationShadowTranscript.allele_id,
                func.unnest(annotationshadow.AnnotationShadowTranscript.consequences).label('consequence')
            ).filter(
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(candidate_allele_ids)
            ).distinct().subquery('unpackedconsequences')

            # Join the two tables, and get index of worst consequence
            # per allele_id, where lower index means worse consequence
            # ------------------------------------
            # | allele_id | worst_consequence_ord |
            # ------------------------------------
            # | 7813      | 21                    |
            # | 8216      | 20                    |
            # ...
            allele_id_worst_consequence = self.session.query(
                unpacked_consequences.c.allele_id,
                func.min(consequence_order.c.ord).over(
                    partition_by=unpacked_consequences.c.allele_id
                ).label('worst_consequence_ord')
            ).join(
                consequence_order,
                text('unpackedconsequences.consequence = consequenceorder.consequence')
            ).distinct().subquery()

            # Get the indices of utr_consequences from our original list,
            # and filter out all allele_ids which has matching index value in 'worst_consequence_ord'
            # SQL table is 1-indexed, so add one.
            utr_consequences_idx = [consequences_ordered.index(c) + 1 for c in utr_consequences]
            filtered_allele_ids = self.session.query(
                allele_id_worst_consequence.c.allele_id
            ).filter(
                allele_id_worst_consequence.c.worst_consequence_ord.in_(utr_consequences_idx)
            )

            utr_filtered[gp_key] = [a[0] for a in filtered_allele_ids.all()]
        return utr_filtered

    def filter_alleles(self, gp_allele_ids):
        """
        Returns:
        {
            ('HBOC', 'v01'): {
                'allele_ids': [1, 2, 3],
                'excluded_allele_ids': {
                    'gene': [4, 5],
                    'intronic': [6, 7],
                    'frequency': [8, 9],
                    'utr': [10],
                }
            },
            ...
        }
        """

        filters = [
            # Order matters!
            ('gene', self.filtered_gene),
            ('frequency', self.filtered_frequency),
            ('intronic', self.filtered_intronic),
            ('utr', self.filtered_utr)
        ]

        result = dict()
        for gp_key in gp_allele_ids:
            result[gp_key] = {
                'excluded_allele_ids': {}
            }

        # Keeps track of already excluded allele_ids for optimization
        excluded_gp_allele_ids = dict()
        for key in gp_allele_ids:
            excluded_gp_allele_ids[key] = set()

        def update_gp_allele_ids(gp_allele_ids, excluded_gp_allele_ids, result):
            for gp_key in gp_allele_ids:
                excluded_gp_allele_ids[gp_key].update(result.get(gp_key, []))
                gp_allele_ids[gp_key] = set(gp_allele_ids[gp_key]) - set(result.get(gp_key, []))

        # Exclude the filtered alleles from one filter from being sent to
        # next filter, in order to improve performance. Matters a lot
        # for large samples, since the frequency filter filters most of the variants
        for filter_name, filter_func in filters:
            filtered = filter_func(gp_allele_ids)
            update_gp_allele_ids(gp_allele_ids, excluded_gp_allele_ids, filtered)
            for gp_key in gp_allele_ids:
                result[gp_key]['excluded_allele_ids'][filter_name] = sorted(list(filtered[gp_key]))

        # Finally add the remaining allele_ids, these weren't filtered out
        for gp_key in gp_allele_ids:
            result[gp_key]['allele_ids'] = sorted(list(gp_allele_ids[gp_key]))

        return result
