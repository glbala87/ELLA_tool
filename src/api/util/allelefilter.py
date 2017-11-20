from collections import OrderedDict, defaultdict
from sqlalchemy import or_, and_, tuple_, text

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
            # we join in AnnotationShadowTranscript using allele_id as key so we can
            # filter on the gene.

            gp_final_filter = list()

            # Gene specific filter
            # Example: af.symbol = "BRCA2" AND (af."ExAC.G" > 0.04 OR af."1000g.G" > 0.01)
            override_genes = gp_config_resolver.get_genes_with_overrides()

            for symbol in override_genes:
                # Get merged genepanel for this gene/symbol
                symbol_group_thresholds = gp_config_resolver.resolve(symbol)['freq_cutoffs']
                allele_ids_for_genes = self.session.query(annotationshadow.AnnotationShadowTranscript.allele_id).filter(
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

            # TODO: Performance should be better if we loop over symbols -> allele_ids,
            # rather than many big joins (?)
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

    def check_shadow_tables(self, allele_ids):
        # Check that our shadow tables are populated, if not we'll get bad results
        allele_ids = set(allele_ids)
        assert self.session.query(annotationshadow.AnnotationShadowTranscript.allele_id).filter(
            annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids)
        ).distinct().count() == len(allele_ids)
        assert self.session.query(annotationshadow.AnnotationShadowFrequency.allele_id).filter(
            annotationshadow.AnnotationShadowFrequency.allele_id.in_(allele_ids)
        ).distinct().count() == len(allele_ids)

    def filtered_gene(self, gp_allele_ids, check_shadow_tables=True):
        """
        Only return the allele IDs whose gene symbol are configured to be excluded.

        Currently this is not configured, as exclusion is built into the pipeline
        producing variants to ella.
        """

        gene_filtered = dict()
        for gp_key, _ in gp_allele_ids.iteritems():
            gene_filtered[gp_key] = list()  # no alleles are filtered away based on gene symbol only

        return gene_filtered

    def filtered_intronic(self, gp_allele_ids, check_shadow_tables=True):
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

        if check_shadow_tables:
            all_allele_ids = sum(gp_allele_ids.values(), [])
            self.check_shadow_tables(all_allele_ids)

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

    def filtered_frequency(self, gp_allele_ids, check_shadow_tables=True):
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

        if check_shadow_tables:
            all_allele_ids = sum(gp_allele_ids.values(), [])
            self.check_shadow_tables(all_allele_ids)

        commonness_result = self.get_commonness_groups(gp_allele_ids, common_only=True)
        frequency_filtered = dict()

        for gp_key, commonness_group in commonness_result.iteritems():
            frequency_filtered[gp_key] = self.remove_alleles_with_classification(commonness_group['common'])

        return frequency_filtered

    def filter_utr(self, gp_key, allele_ids, check_shadow_tables=True):
        """
        Filters out variants that have worst consequence equal to 3_prime_UTR_variant or 5_prime_UTR_variant in any
        of the annotation transcripts included.
        :param gp_key: (genepanel_name, genepanel_version) used for extracting transcripts
        :param allele_ids: allele_ids to run filter on
        :return: allele ids to be filtered out
        """

        if check_shadow_tables:
            self.check_shadow_tables(allele_ids)

        return []
        # FIXME: IMPLEMENT!!!
        # FIXME: IMPLEMENT!!!
        # FIXME: IMPLEMENT!!!
        # FIXME: IMPLEMENT!!!
        # FIXME: IMPLEMENT!!!
        # FIXME: IMPLEMENT!!!
        consequences_ordered = self.global_config["transcripts"].get("consequences")
        # An ordering of consequences has not been specified, return empty list
        if consequences_ordered is None:
            return []

        # Also return empty list if *_prime_UTR_variant is not specified in consequences_ordered
        if not ('3_prime_UTR_variant' in consequences_ordered and '5_prime_UTR_variant' in consequences_ordered):
            return []

        utr_consequence_index = min([consequences_ordered.index(c) for c in ['3_prime_UTR_variant', '5_prime_UTR_variant']])

        # Get transcripts to be included
        filtered_transcripts = queries.annotation_transcripts_filtered(
            self.session,
            allele_ids,
            self.global_config.get("transcripts", {}).get("inclusion_regex")
        ).subquery()

        # Fetch the consequences for each allele (several lines per allele id)
        allele_id_consequences = self.session.query(
            annotation.Annotation.allele_id,
            transcript_records.c.transcript.label('transcript'),
            transcript_records.c.consequences.label('consequences'),
        ).filter(
            annotation.Annotation.allele_id == filtered_transcripts.c.allele_id,
            transcript_records.c.transcript == filtered_transcripts.c.annotation_transcript,
            annotation.Annotation.date_superceeded.is_(None)  # Important!
        ).all()

        # Concatenate all consequences for each allele id
        allele_consequences = defaultdict(list)
        for allele_id, transcript, consequences in allele_id_consequences:
            if consequences is None:
                allele_consequences[allele_id] += [None]
            else:
                allele_consequences[allele_id] += consequences

        def get_consequence_index(consequences):
            return map(lambda c: consequences_ordered.index(c) if c in consequences_ordered else -1, consequences)

        # Check if it has consequence 3_prime_UTR_variant/5_prime_UTR_variant, and if so, if this is the worst consequence
        utr_filtered = []
        for allele_id, consequences in allele_consequences.iteritems():
            if '3_prime_UTR_variant' in consequences or '5_prime_UTR_variant' in consequences:
                worst_consequence_index = min(get_consequence_index(consequences))
                if worst_consequence_index >= utr_consequence_index:
                    utr_filtered.append(allele_id)

        # Remove the ones with existing classification
        utr_filtered = self.remove_alleles_with_classification(utr_filtered)

        return utr_filtered

    def filter_alleles(self, gp_allele_ids):
        result = dict()

        all_allele_ids = sum(gp_allele_ids.values(), [])
        self.check_shadow_tables(all_allele_ids)

        filtered_gene = self.filtered_gene(gp_allele_ids, check_shadow_tables=False)
        filtered_frequency = self.filtered_frequency(gp_allele_ids, check_shadow_tables=False)
        filtered_intronic = self.filtered_intronic(gp_allele_ids, check_shadow_tables=False)

        for gp_key in gp_allele_ids:
            gp_filtered_gene = filtered_gene[gp_key]
            gp_filtered_frequency = [i for i in filtered_frequency[gp_key] if i not in gp_filtered_gene]
            excluded = gp_filtered_gene + gp_filtered_frequency
            gp_filtered_intronic = [i for i in filtered_intronic[gp_key] if i not in excluded]
            excluded = excluded + gp_filtered_intronic

            # Subtract the ones we excluded to get the ones not filtered out
            not_filtered = list(set(gp_allele_ids[gp_key]) - set(excluded))

            filtered_utr = self.filter_utr(gp_key, not_filtered)
            not_filtered = list(set(not_filtered)-set(filtered_utr))

            result[gp_key] = {
                'allele_ids': not_filtered,
                'excluded_allele_ids': {
                    'gene': gp_filtered_gene,
                    'intronic': gp_filtered_intronic,
                    'frequency': gp_filtered_frequency,
                    'utr': filtered_utr,
                }
            }

        return result
