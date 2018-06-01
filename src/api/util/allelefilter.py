from collections import OrderedDict, defaultdict
from sqlalchemy import or_, and_, tuple_, text, func, column, literal, distinct, case
from sqlalchemy.types import Text
from sqlalchemy.dialects.postgresql import ARRAY

from api.config import config as global_genepanel_default
from vardb.datamodel import assessment, gene, annotation, annotationshadow, allele

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

    def create_gene_padding_table(self, gene_ids):
        """
        Create a temporary table for the gene specific padding of the form
        ------------------------------------------------------------------------------------------------
        | hgnc_id | exon_upstream | exon_downstream | coding_region_upstream | coding_region_downstream |
        ------------------------------------------------------------------------------------------------
        | 26113   | -35           | 15              | -20                    | 20                       |
        | 28163   | -20           | 6               | -20                    | 20                       |
        | 2567    | -20           | 6               | -50                    | 50                       |

        Returns an ORM-representation of this table
        """
        from sqlalchemy import Table, Column, MetaData
        from sqlalchemy import Integer

        # DEBUG CODE
        #TODO: Replace with actual padding values when available
        intronic_region = self.global_config['variant_criteria']['intronic_region']
        utr_region = self.global_config['variant_criteria']['utr_region']
        values = []
        for gene_id in gene_ids:
            values.append(str((gene_id, intronic_region[0], intronic_region[1], utr_region[0], utr_region[1])))
        # END DEBUG CODE

        self.session.execute(
            "DROP TABLE IF EXISTS tmp_gene_padding;"
        )
        self.session.execute(
            "CREATE TEMP TABLE tmp_gene_padding (hgnc_id Integer, exon_upstream Integer, exon_downstream Integer, coding_region_upstream Integer, coding_region_downstream Integer) ON COMMIT DROP;"
        )

        if values:
            self.session.execute("INSERT INTO tmp_gene_padding VALUES {};".format(",".join(values)))

        t = Table(
            'tmp_gene_padding',
            MetaData(),
            Column('hgnc_id', Integer()),
            Column('exon_upstream', Integer()),
            Column('exon_downstream', Integer()),
            Column('coding_region_upstream', Integer()),
            Column('coding_region_downstream', Integer()),
        )
        return t

    def get_allele_ids_with_classification(self, allele_ids):
        """
        Return the allele ids, among the provided allele_ids,
        that have have an existing classification according with
        global config ['classification']['options'].
        """

        options = self.global_config['classification']['options']
        exclude_for_class = [o['value'] for o in options if o.get('exclude_filtering_existing_assessment')]

        with_classification = set()

        if allele_ids:
            with_classification = self.session.query(assessment.AlleleAssessment.allele_id).filter(
                assessment.AlleleAssessment.classification.in_(exclude_for_class),
                assessment.AlleleAssessment.allele_id.in_(allele_ids),
                assessment.AlleleAssessment.date_superceeded.is_(None)
            ).all()
            with_classification = set([t[0] for t in with_classification])

        return with_classification

    def filtered_gene(self, gp_allele_ids):
        """
        Only return the allele IDs whose gene symbol are configured to be excluded.

        Currently this is not configured, as exclusion is built into the pipeline
        producing variants to ella.
        """

        gene_filtered = dict()
        for gp_key, _ in gp_allele_ids.iteritems():
            gene_filtered[gp_key] = set()  # no alleles are filtered away based on gene symbol only

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
        :returns: Structure similar to input, but only containing set() of allele ids that are intronic.

        :note: The returned values are allele ids that were _filtered out_
        based on intronic status, i.e. they are intronic.
        """

        intronic_filtered = dict()
        # TODO: Add support for per gene/genepanel configuration when ready.
        intronic_region = self.global_config['variant_criteria']['intronic_region']
        for gp_key, allele_ids in gp_allele_ids.iteritems():

            # Determine which allele ids are in an exon (with exon_distance == None, or within intronic_region interval)
            exonic_alleles_q = self.session.query(
                annotationshadow.AnnotationShadowTranscript.allele_id,
                annotationshadow.AnnotationShadowTranscript.exon_distance,
                annotationshadow.AnnotationShadowTranscript.transcript
            ).filter(
                or_(
                    and_(
                        annotationshadow.AnnotationShadowTranscript.exon_distance.is_(None),
                        # ~annotationshadow.AnnotationShadowTranscript.hgvsc.is_(None),
                    ),
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
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids) if allele_ids else False
            )
            inclusion_regex = self.global_config.get("transcripts", {}).get("inclusion_regex")
            if inclusion_regex:
                exonic_alleles_q = exonic_alleles_q.filter(
                    text("transcript ~ :reg").params(reg=inclusion_regex)
                )
            exonic_alleles_q = exonic_alleles_q.distinct()

            annotation_shadow_allele_ids_q = self.session.query(
                annotationshadow.AnnotationShadowTranscript.allele_id
            ).filter(
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids) if allele_ids else False
            )

            exonic_allele_ids = [a[0] for a in exonic_alleles_q.all()]
            annotation_shadow_allele_ids = [a[0] for a in annotation_shadow_allele_ids_q.all()]
            intronic_filtered[gp_key] = set(annotation_shadow_allele_ids) - set(exonic_allele_ids)

        # Remove the ones with existing classification
        for gp_key, allele_ids in intronic_filtered.iteritems():
            intronic_filtered[gp_key] = intronic_filtered[gp_key] - self.get_allele_ids_with_classification(allele_ids)

        return intronic_filtered

    def filtered_region(self, gp_allele_ids):
        region_filtered = {}
        for gp_key, allele_ids in gp_allele_ids.iteritems():
            if not allele_ids:
                region_filtered[gp_key] = set()
                continue

            # Fetch all gene ids associated with the genepanel
            genepanel_genes = self.session.query(
                gene.Transcript.gene_id,
            ).join(
                 gene.genepanel_transcript,
                 and_(
                    gene.genepanel_transcript.c.transcript_id == gene.Transcript.id,
                    tuple_(gene.genepanel_transcript.c.genepanel_name, gene.genepanel_transcript.c.genepanel_version) == gp_key
                 )
            )
            genepanel_hgnc_ids = [t[0] for t in genepanel_genes]

            # Create temporary gene padding table for the genes in the genepanel
            tmp_gene_padding = self.create_gene_padding_table(genepanel_hgnc_ids)

            max_padding = self.session.query(
                func.abs(func.max(tmp_gene_padding.c.exon_upstream)),
                func.abs(func.max(tmp_gene_padding.c.exon_downstream)),
                func.abs(func.max(tmp_gene_padding.c.coding_region_upstream)),
                func.abs(func.max(tmp_gene_padding.c.coding_region_downstream)),
            )
            max_padding = max(*max_padding.all())

            # Extract transcripts associated with the genepanel
            # To potentially limit the number of regions we need to check, exclude transcripts where we have no alleles
            # overlapping in the region [tx_start-max_padding, tx_end+max_padding]. The filter clause in the query
            # should have no effect on the result, but is included only for performance
            genepanel_transcripts = self.session.query(
                gene.Transcript.id,
                gene.Transcript.gene_id,
                gene.Transcript.transcript_name,
                gene.Transcript.chromosome,
                gene.Transcript.strand,
                gene.Transcript.tx_start,
                gene.Transcript.tx_end,
                gene.Transcript.cds_start,
                gene.Transcript.cds_end,
                gene.Transcript.exon_starts,
                gene.Transcript.exon_ends,
            ).join(
                 gene.genepanel_transcript,
                 and_(
                    gene.genepanel_transcript.c.transcript_id == gene.Transcript.id,
                    tuple_(gene.genepanel_transcript.c.genepanel_name, gene.genepanel_transcript.c.genepanel_version) == gp_key
                 )
            ).filter(
                allele.Allele.id.in_(allele_ids),
                allele.Allele.chromosome == gene.Transcript.chromosome,
                or_(
                    and_(
                        allele.Allele.start_position > gene.Transcript.tx_start-max_padding,
                        allele.Allele.start_position < gene.Transcript.tx_end+max_padding,
                    ),
                    and_(
                        allele.Allele.open_end_position > gene.Transcript.tx_start-max_padding,
                        allele.Allele.open_end_position < gene.Transcript.tx_end+max_padding,
                    )
                )
            ).subquery()

            # Unwrap the exons for the genepanel transcript
            genepanel_transcript_exons = self.session.query(
                genepanel_transcripts.c.id,
                genepanel_transcripts.c.gene_id,
                genepanel_transcripts.c.chromosome,
                genepanel_transcripts.c.strand,
                genepanel_transcripts.c.cds_start,
                genepanel_transcripts.c.cds_end,
                func.unnest(genepanel_transcripts.c.exon_starts).label('exon_start'),
                func.unnest(genepanel_transcripts.c.exon_ends).label('exon_end'),
            ).subquery()

            # Create queries for
            # - Coding regions
            # - Upstream intron region
            # - Downstream intron region
            # - Upstream UTR region
            # - Downstream UTR region

            # Coding regions
            # The coding regions may start within an exon, and we truncate the exons where this is the case
            # For example, if an exon is defined by positions [10,20], but cds_start is 15, we include the region [15,20]
            coding_start = case(
                    [(genepanel_transcript_exons.c.cds_start > genepanel_transcript_exons.c.exon_start, genepanel_transcript_exons.c.cds_start)],
                    else_=genepanel_transcript_exons.c.exon_start
                )

            coding_end = case(
                    [(genepanel_transcript_exons.c.cds_end < genepanel_transcript_exons.c.exon_end, genepanel_transcript_exons.c.cds_end)],
                    else_=genepanel_transcript_exons.c.exon_end
                )

            transcript_coding_regions = self.session.query(
                genepanel_transcript_exons.c.chromosome.label('chromosome'),
                coding_start.label('region_start'),
                coding_end.label('region_end'),
            ).filter(
                # Exclude exons outside the coding region
                genepanel_transcript_exons.c.exon_start < genepanel_transcript_exons.c.cds_end,
                genepanel_transcript_exons.c.exon_end > genepanel_transcript_exons.c.cds_start
            )

            # Regions with applied padding
            def _create_region(transcripts, region_start, region_end):
                return self.session.query(
                    transcripts.c.chromosome.label('chromosome'),
                    region_start.label('region_start'),
                    region_end.label('region_end')
                ).join(
                    tmp_gene_padding,
                    tmp_gene_padding.c.hgnc_id == transcripts.c.gene_id
                ).distinct()

            # Intronic upstream
            # Include region upstream of the exon (not including exon starts or ends)
            intronic_upstream_end = case(
                [(genepanel_transcript_exons.c.strand == '-', genepanel_transcript_exons.c.exon_end-tmp_gene_padding.c.exon_upstream)],
                else_=genepanel_transcript_exons.c.exon_start-1,
            )

            intronic_upstream_start = case(
                [(genepanel_transcript_exons.c.strand == '-', genepanel_transcript_exons.c.exon_end)],
                else_=genepanel_transcript_exons.c.exon_start+tmp_gene_padding.c.exon_upstream,
            )

            intronic_region_upstream = _create_region(genepanel_transcript_exons, intronic_upstream_start, intronic_upstream_end)

            # Intronic downstream
            # Include region downstream of the exon (not including exon starts or ends)
            intronic_downstream_end = case(
                [(genepanel_transcript_exons.c.strand == '-', genepanel_transcript_exons.c.exon_start-1)],
                else_=genepanel_transcript_exons.c.exon_end+tmp_gene_padding.c.exon_downstream,
            )

            intronic_downstream_start = case(
                [(genepanel_transcript_exons.c.strand == '-', genepanel_transcript_exons.c.exon_start-tmp_gene_padding.c.exon_downstream)],
                else_=genepanel_transcript_exons.c.exon_end+1,
            )

            intronic_region_downstream = _create_region(genepanel_transcript_exons, intronic_downstream_start, intronic_downstream_end)

            # UTR upstream
            # Do not include cds_start or cds_end, as these are not in the UTR
            utr_upstream_end = case(
                [(genepanel_transcripts.c.strand == '-', genepanel_transcripts.c.cds_end-tmp_gene_padding.c.coding_region_upstream)],
                else_=genepanel_transcripts.c.cds_start-1
            )

            utr_upstream_start = case(
                [(genepanel_transcripts.c.strand == '-', genepanel_transcripts.c.cds_end+1)],
                else_=genepanel_transcripts.c.cds_start+tmp_gene_padding.c.coding_region_upstream
            )

            utr_region_upstream = _create_region(genepanel_transcripts, utr_upstream_start, utr_upstream_end)

            # UTR downstream
            # Do not include cds_start or cds_end, as these are not in the UTR
            utr_downstream_start = case(
                [(genepanel_transcripts.c.strand == '-', genepanel_transcripts.c.cds_start-tmp_gene_padding.c.coding_region_downstream)],
                else_=genepanel_transcripts.c.cds_end+1
            )

            utr_downstream_end = case(
                [(genepanel_transcripts.c.strand == '-', genepanel_transcripts.c.cds_start-1)],
                else_=genepanel_transcripts.c.cds_end+tmp_gene_padding.c.coding_region_downstream
            )
            utr_region_downstream = _create_region(genepanel_transcripts, utr_downstream_start, utr_downstream_end)

            # Union all regions together
            all_regions = transcript_coding_regions.union(
               intronic_region_upstream,
               intronic_region_downstream,
               utr_region_upstream,
               utr_region_downstream,
            ).subquery().alias('all_regions')

            # Find allele ids within genomic region
            allele_ids_in_genomic_region = self.session.query(
                allele.Allele.id,
            ).filter(
                allele.Allele.id.in_(allele_ids),
                allele.Allele.chromosome == all_regions.c.chromosome,
                or_(
                    and_(
                        allele.Allele.start_position >= all_regions.c.region_start,
                        allele.Allele.start_position <= all_regions.c.region_end,
                    ),
                    and_(
                        allele.Allele.open_end_position > all_regions.c.region_start,
                        allele.Allele.open_end_position < all_regions.c.region_end,
                    )
                )
            )

            allele_ids_in_genomic_region = [a[0] for a in allele_ids_in_genomic_region]
            allele_ids_outside_region = set(allele_ids)-set(allele_ids_in_genomic_region)

            # Discard the next filters if there are no variants left to filter on
            if not allele_ids_outside_region:
                region_filtered[gp_key] = set()
                continue

            #
            # Save alleles based on computed HGVSc distance
            #
            # We look at computed exon_distance/coding_region_distance from annotation on transcripts present in the genepanel (disregaring version number)
            # For alleles with computed distance within intronic_region or utr_region, they will not be filtered out
            # This can happen when there is a mismatch between genomic position and annotated HGVSc.
            # Observed for alleles in repeated regions: In the imported VCF, the alleles are left aligned. The VEP annotation
            # left aligns w.r.t. *transcript direction*, and therefore, there could be a mismatch in position
            # See for example https://variantvalidator.org/variantvalidation/?variant=NM_020366.3%3Ac.907-16_907-14delAAT&primary_assembly=GRCh37&alignment=splign
            annotation_transcripts_genepanel = queries.annotation_transcripts_genepanel(self.session, allele_ids, [gp_key]).subquery()

            allele_ids_in_hgvsc_region = self.session.query(
                annotationshadow.AnnotationShadowTranscript.allele_id,
                annotationshadow.AnnotationShadowTranscript.transcript,
                annotationshadow.AnnotationShadowTranscript.hgvsc,
                annotationshadow.AnnotationShadowTranscript.exon_distance,
                annotationshadow.AnnotationShadowTranscript.coding_region_distance,
                tmp_gene_padding.c.exon_upstream,
                tmp_gene_padding.c.exon_downstream,
                tmp_gene_padding.c.coding_region_upstream,
                tmp_gene_padding.c.coding_region_downstream,
            ).join(
                # Join in transcripts used in annotation
                # Note: The annotation_transcripts_genepanel only contains transcripts matching transcripts in the genepanel.
                # Therefore, we are sure that we only filter here on genepanel transcripts (disregarding version number)
                annotation_transcripts_genepanel,
                and_(
                    annotation_transcripts_genepanel.c.annotation_transcript == annotationshadow.AnnotationShadowTranscript.transcript,
                    annotation_transcripts_genepanel.c.allele_id == annotationshadow.AnnotationShadowTranscript.allele_id
                )
            ).join(
                # Join in gene padding table, to use gene specific padding
                tmp_gene_padding,
                tmp_gene_padding.c.hgnc_id == annotation_transcripts_genepanel.c.genepanel_hgnc_id
            ).filter(
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids_outside_region),
                annotationshadow.AnnotationShadowTranscript.exon_distance >= tmp_gene_padding.c.exon_upstream,
                annotationshadow.AnnotationShadowTranscript.exon_distance <= tmp_gene_padding.c.exon_downstream,
                or_(
                    # We do not save exonic UTR alleles if they are outside [coding_region_upstream, coding_region_downstream]
                    # For coding exonic variant, the coding_region_distance is None
                    annotationshadow.AnnotationShadowTranscript.coding_region_distance.is_(None),
                    and_(
                        annotationshadow.AnnotationShadowTranscript.coding_region_distance >= tmp_gene_padding.c.coding_region_upstream,
                        annotationshadow.AnnotationShadowTranscript.coding_region_distance <= tmp_gene_padding.c.coding_region_downstream,
                    ),
                )
            )

            allele_ids_in_hgvsc_region = set([a[0] for a in allele_ids_in_hgvsc_region])
            allele_ids_outside_region -= allele_ids_in_hgvsc_region

            # Discard the next filter if there are no variants left to filter on
            if not allele_ids_outside_region:
                region_filtered[gp_key] = set()
                continue

            #
            # Save alleles with a severe consequence in other transcript
            #
            # Whether a consequence is severe or not is determined by the config
            all_consequences = self.global_config.get('transcripts', {}).get('consequences')
            severe_consequence_threshold = self.global_config.get('transcripts', {}).get('severe_consequence_threshold')
            if all_consequences:
                severe_consequences = all_consequences[:all_consequences.index(severe_consequence_threshold)+1]
            else:
                severe_consequences = []

            allele_ids_severe_consequences = self.session.query(
                annotationshadow.AnnotationShadowTranscript.allele_id,
                annotationshadow.AnnotationShadowTranscript.consequences,
            ).filter(
                # && checks if two arrays overlap
                annotationshadow.AnnotationShadowTranscript.consequences.cast(ARRAY(Text)).op('&&')(severe_consequences),
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids_outside_region),
            )

            # As opposed to the HGVSc and genomic region filter, we here consider all transcript, given that they
            # match the transcript inclusion regex (if exists)
            inclusion_regex = self.global_config.get("transcripts", {}).get("inclusion_regex")
            if inclusion_regex:
                allele_ids_severe_consequences = allele_ids_severe_consequences.filter(
                    text("transcript ~ :reg").params(reg=inclusion_regex)
                )

            allele_ids_severe_consequences = set([a[0] for a in allele_ids_severe_consequences])
            allele_ids_outside_region -= allele_ids_severe_consequences

            region_filtered[gp_key] = allele_ids_outside_region


        return region_filtered


    def filtered_frequency(self, gp_allele_ids):
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
            frequency_filtered[gp_key] = commonness_group['common'] - self.get_allele_ids_with_classification(commonness_group['common'])

        return frequency_filtered

    def filtered_utr(self, gp_allele_ids):
        """
        Filters out variants that have worst consequence equal to 3_prime_UTR_variant or 5_prime_UTR_variant in any
        of the annotation transcripts included.
        :param allele_ids: allele_ids to run filter on
        :return: {gp_key: set()} with allele ids to be filtered out
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
                utr_filtered[gp_key] = set([])
                continue

            # Also return empty list if *_prime_UTR_variant is not specified in consequences_ordered
            if not any(u in consequences_ordered for u in utr_consequences):
                utr_filtered[gp_key] = set([])
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
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids) if allele_ids else False
            ).distinct()

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
            ).distinct()

            utr_filtered[gp_key] = set([a[0] for a in filtered_allele_ids.all()])
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
            #('frequency', self.filtered_frequency),
            ('region', self.filtered_region),
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
                excluded_gp_allele_ids[gp_key].update(result.get(gp_key, set([])))
                gp_allele_ids[gp_key] = set(gp_allele_ids[gp_key]) - result.get(gp_key, set([]))

        # Exclude the filtered alleles from one filter from being sent to
        # next filter, in order to improve performance. Matters a lot
        # for large samples, since the frequency filter filters most of the variants
        import time
        for filter_name, filter_func in filters:
            t1 = time.time()
            filtered = filter_func(gp_allele_ids)
            t2 = time.time()
            print filter_name, t2-t1
            update_gp_allele_ids(gp_allele_ids, excluded_gp_allele_ids, filtered)
            for gp_key in gp_allele_ids:
                result[gp_key]['excluded_allele_ids'][filter_name] = sorted(list(filtered[gp_key]))

        # Finally add the remaining allele_ids, these weren't filtered out
        for gp_key in gp_allele_ids:
            result[gp_key]['allele_ids'] = sorted(list(gp_allele_ids[gp_key]))

        return result


if __name__ == '__main__':
    from vardb.util import DB
    db = DB()
    db.connect()
    session = db.session
    af = AlleleFilter(session)
    gp_key = ('OMIM', 'v01')
    allele_ids = range(1,576)


    res = af.filter_alleles({gp_key: allele_ids})
    print res

    # Reference result for frequency filter turned OFF
    ref = {('Ciliopati', 'v05'): {'excluded_allele_ids': {'region': [1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 15, 16, 17, 18, 19, 20, 21, 26, 27, 29, 30, 31, 34, 38, 39, 40, 42, 43, 44, 45, 46, 47, 48, 51, 52, 53, 62, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 83, 84, 85, 86, 87, 89, 90, 91, 92, 93, 97, 98, 100, 101, 102, 103, 105, 106, 112, 113, 114, 115, 120, 123, 124, 125, 126, 128, 129, 130, 131, 132, 133, 134, 135, 136, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 149, 150, 151, 152, 158, 159, 163, 164, 165, 166, 167, 170, 171, 172, 173, 180, 181, 182, 184, 185, 186, 187, 188, 189, 193, 194, 195, 196, 197, 198, 199, 201, 203, 210, 211, 212, 213, 217, 221, 223, 226, 227, 228, 232, 237, 238, 239, 240, 245, 246, 249, 250, 252, 256, 258, 259, 260, 268, 270, 271, 272, 278, 282, 283, 285, 292, 293, 294, 295, 296, 297, 298, 299, 300, 302, 303, 304, 306, 309, 312, 313, 314, 315, 318, 319, 320, 323, 328, 329, 331, 333, 334, 335, 337, 338, 342, 343, 348, 352, 353, 354, 356, 357, 358, 359, 360, 361, 362, 368, 369, 370, 374, 377, 379, 385, 386, 388, 389, 390, 391, 393, 394, 395, 397, 398, 399, 401, 402, 404, 408, 410, 411, 412, 413, 414, 416, 420, 421, 422, 424, 425, 427, 429, 433, 434, 435, 436, 437, 438, 439, 441, 442, 443, 445, 446, 447, 448, 451, 454, 456, 457, 459, 461, 463, 464, 466, 467, 470, 472, 473, 474, 476, 478, 479, 480, 483, 484, 485, 490, 497, 498, 499, 501, 502, 504, 505, 508, 510, 511, 512, 513, 515, 518, 519, 520, 521, 523, 524, 525, 528, 529, 530, 531, 538, 540, 541, 545, 546, 548, 550, 551, 560, 562, 564, 565, 566, 567, 569, 570, 572, 573, 574, 575], 'gene': []}, 'allele_ids': [2, 11, 14, 22, 23, 24, 25, 28, 32, 33, 35, 36, 37, 41, 49, 50, 54, 55, 56, 57, 58, 59, 60, 61, 63, 64, 77, 78, 79, 80, 81, 82, 88, 94, 95, 96, 99, 104, 107, 108, 109, 110, 111, 116, 117, 118, 119, 121, 122, 127, 137, 148, 153, 154, 155, 156, 157, 160, 161, 162, 168, 169, 174, 175, 176, 177, 178, 179, 183, 190, 191, 192, 200, 202, 204, 205, 206, 207, 208, 209, 214, 215, 216, 218, 219, 220, 222, 224, 225, 229, 230, 231, 233, 234, 235, 236, 241, 242, 243, 244, 247, 248, 251, 253, 254, 255, 257, 261, 262, 263, 264, 265, 266, 267, 269, 273, 274, 275, 276, 277, 279, 280, 281, 284, 286, 287, 288, 289, 290, 291, 301, 305, 307, 308, 310, 311, 316, 317, 321, 322, 324, 325, 326, 327, 330, 332, 336, 339, 340, 341, 344, 345, 346, 347, 349, 350, 351, 355, 363, 364, 365, 366, 367, 371, 372, 373, 375, 376, 378, 380, 381, 382, 383, 384, 387, 392, 396, 400, 403, 405, 406, 407, 409, 415, 417, 418, 419, 423, 426, 428, 430, 431, 432, 440, 444, 449, 450, 452, 453, 455, 458, 460, 462, 465, 468, 469, 471, 475, 477, 481, 482, 486, 487, 488, 489, 491, 492, 493, 494, 495, 496, 500, 503, 506, 507, 509, 514, 516, 517, 522, 526, 527, 532, 533, 534, 535, 536, 537, 539, 542, 543, 544, 547, 549, 552, 553, 554, 555, 556, 557, 558, 559, 561, 563, 568, 571]},
           ('OMIM', 'v01'): {'excluded_allele_ids': {'region': [1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 16, 17, 18, 19, 20, 21, 26, 27, 29, 30, 31, 34, 38, 39, 40, 42, 43, 44, 45, 46, 47, 48, 51, 52, 53, 62, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 83, 84, 85, 86, 87, 89, 90, 91, 92, 93, 97, 98, 100, 101, 102, 103, 105, 106, 112, 113, 114, 115, 120, 123, 124, 125, 126, 128, 129, 130, 131, 132, 133, 134, 135, 136, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 149, 150, 151, 152, 158, 159, 163, 164, 165, 166, 167, 170, 171, 172, 173, 180, 181, 182, 184, 185, 186, 187, 188, 189, 193, 194, 195, 196, 197, 198, 199, 201, 203, 210, 211, 212, 213, 217, 221, 223, 226, 227, 228, 232, 237, 238, 239, 240, 245, 246, 249, 250, 252, 256, 258, 259, 260, 268, 270, 271, 272, 278, 282, 283, 285, 292, 293, 294, 295, 296, 297, 298, 299, 300, 302, 303, 304, 306, 309, 312, 313, 314, 315, 318, 319, 320, 323, 328, 329, 331, 333, 334, 335, 337, 338, 342, 343, 348, 352, 353, 354, 356, 357, 358, 359, 360, 361, 362, 368, 369, 370, 374, 377, 379, 385, 386, 388, 389, 390, 391, 393, 394, 395, 397, 398, 399, 401, 402, 404, 408, 410, 411, 412, 413, 414, 416, 420, 421, 422, 424, 425, 427, 429, 433, 434, 435, 436, 438, 439, 441, 442, 443, 445, 446, 447, 448, 451, 454, 456, 457, 459, 461, 463, 464, 466, 467, 470, 472, 473, 474, 476, 478, 479, 480, 483, 484, 485, 490, 493, 497, 498, 499, 501, 502, 504, 505, 508, 510, 511, 512, 513, 515, 518, 519, 520, 521, 523, 524, 525, 528, 529, 530, 531, 538, 540, 541, 545, 546, 548, 550, 551, 560, 562, 564, 565, 566, 567, 569, 570, 572, 573, 574, 575], 'gene': []}, 'allele_ids': [2, 11, 14, 15, 22, 23, 24, 25, 28, 32, 33, 35, 36, 37, 41, 49, 50, 54, 55, 56, 57, 58, 59, 60, 61, 63, 64, 77, 78, 79, 80, 81, 82, 88, 94, 95, 96, 99, 104, 107, 108, 109, 110, 111, 116, 117, 118, 119, 121, 122, 127, 137, 148, 153, 154, 155, 156, 157, 160, 161, 162, 168, 169, 174, 175, 176, 177, 178, 179, 183, 190, 191, 192, 200, 202, 204, 205, 206, 207, 208, 209, 214, 215, 216, 218, 219, 220, 222, 224, 225, 229, 230, 231, 233, 234, 235, 236, 241, 242, 243, 244, 247, 248, 251, 253, 254, 255, 257, 261, 262, 263, 264, 265, 266, 267, 269, 273, 274, 275, 276, 277, 279, 280, 281, 284, 286, 287, 288, 289, 290, 291, 301, 305, 307, 308, 310, 311, 316, 317, 321, 322, 324, 325, 326, 327, 330, 332, 336, 339, 340, 341, 344, 345, 346, 347, 349, 350, 351, 355, 363, 364, 365, 366, 367, 371, 372, 373, 375, 376, 378, 380, 381, 382, 383, 384, 387, 392, 396, 400, 403, 405, 406, 407, 409, 415, 417, 418, 419, 423, 426, 428, 430, 431, 432, 437, 440, 444, 449, 450, 452, 453, 455, 458, 460, 462, 465, 468, 469, 471, 475, 477, 481, 482, 486, 487, 488, 489, 491, 492, 494, 495, 496, 500, 503, 506, 507, 509, 514, 516, 517, 522, 526, 527, 532, 533, 534, 535, 536, 537, 539, 542, 543, 544, 547, 549, 552, 553, 554, 555, 556, 557, 558, 559, 561, 563, 568, 571]}}

    if gp_key in ref and range(1,576) == allele_ids:
        assert res[gp_key]['excluded_allele_ids']['region'] == ref[gp_key]['excluded_allele_ids']['region']
    else:
        print "!!! Results not tested !!!"

