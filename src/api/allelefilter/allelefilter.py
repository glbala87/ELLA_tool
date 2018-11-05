import itertools
import copy

from sqlalchemy import literal_column, text, or_, func
from api.config import config as global_config, get_filter_config
from vardb.datamodel import assessment, sample, allele, genotype, annotation

from api.allelefilter.frequencyfilter import FrequencyFilter
from api.allelefilter.segregationfilter import SegregationFilter
from api.allelefilter.regionfilter import RegionFilter
from api.allelefilter.qualityfilter import QualityFilter


class AlleleFilter(object):

    def __init__(self, session, config=None):
        self.session = session
        self.config = global_config if not config else config

        self.filter_functions = {
            'frequency': ('allele', FrequencyFilter(self.session, self.config).filter_alleles),
            'region': ('allele', RegionFilter(self.session, self.config).filter_alleles),
            'quality': ('analysis', QualityFilter(self.session, self.config).filter_alleles),
            'segregation': ('analysis', SegregationFilter(self.session, self.config).filter_alleles)
        }

    def get_allele_ids_with_classification(self, allele_ids):
        """
        Return the allele ids, among the provided allele_ids,
        that have have an existing classification according with
        global config ['classification']['options'].
        """

        options = self.config['classification']['options']
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

    def get_allele_ids_with_pathogenic_clinvar(self, allele_ids):
        """
        Return the allele_ids that have >=2 Clinvar
        'clinical_significance_descr' that are 'Pathogenic'
        """

        expanded_clinvar = self.session.query(
            annotation.Annotation.allele_id,
            literal_column("jsonb_array_elements(annotations->'external'->'CLINVAR'->'items')").label('entry')
        ).filter(
            annotation.Annotation.allele_id.in_(allele_ids),
            annotation.Annotation.date_superceeded.is_(None)
        ).subquery()

        pathogenic_allele_ids = self.session.query(
            expanded_clinvar.c.allele_id,
            func.count(expanded_clinvar.c.allele_id),
        ).filter(
            text("entry->>'rcv' ILIKE 'SCV%'"),
            text("entry->>'clinical_significance_descr' ILIKE 'pathogenic'")
        ).group_by(
            expanded_clinvar.c.allele_id
        ).having(
            func.count("entry->>'clinical_significance_descr' ILIKE 'pathogenic'") > 1
        ).all()

        return set([a[0] for a in pathogenic_allele_ids])

    def get_filter_exceptions(self, exceptions_config, allele_ids):
        """
        Checks whether any of allele_ids should be excepted from filtering,
        given checks given by exceptions_config
        """

        filter_exceptions = set()
        for e in exceptions_config:
            if e['name'] == 'classification':
                filter_exceptions |= self.get_allele_ids_with_classification(allele_ids)
            # TODO: clinvar_pathogenic strategy needs refinement
            #elif e['name'] == 'clinvar_pathogenic':
            #    filter_exceptions |= self.get_allele_ids_with_pathogenic_clinvar(allele_ids)
        return filter_exceptions

    def filter_alleles(self, filter_config_id, gp_allele_ids, analysis_allele_ids):
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
        if analysis_allele_ids:
            analysis_allele_ids = {k: set(v) for k, v in analysis_allele_ids.iteritems()}
        else:
            analysis_allele_ids = dict()
        if gp_allele_ids:
            merged_gp_allele_ids = {k: set(v) for k, v in gp_allele_ids.iteritems()}
        else:
            gp_allele_ids = dict()
            merged_gp_allele_ids = dict()

        analysis_genepanels = self.session.query(
            sample.Analysis.id,
            sample.Analysis.genepanel_name,
            sample.Analysis.genepanel_version,
        ).filter(
            sample.Analysis.id.in_(analysis_allele_ids.keys())
        ).all()

        analysis_genepanels = {a.id: (a.genepanel_name, a.genepanel_version) for a in analysis_genepanels}

        for a_id, gp_key in analysis_genepanels.iteritems():
            if gp_key not in merged_gp_allele_ids:
                merged_gp_allele_ids[gp_key] = set()
            merged_gp_allele_ids[gp_key].update(analysis_allele_ids[a_id])

        gp_alleles_filtered = {gp_key: dict() for gp_key in merged_gp_allele_ids}  # {gp_key: {filter_name: set()}}
        analysis_alleles_filtered = {a_id: dict() for a_id in analysis_allele_ids}  # {analysis_id: {filter_name: set()}}
        gp_alleles_remaining = {gp_key: set(allele_ids) for gp_key, allele_ids in merged_gp_allele_ids.iteritems()}
        analysis_alleles_remaining = {analysis_id: set(allele_ids) for analysis_id, allele_ids in analysis_allele_ids.iteritems()}

        # Run filter functions.
        # Already filtered alleles are tracked to avoid re-filtering same alleles (for performance reasons).

        filter_config = self.session.query(sample.FilterConfig.filterconfig).filter(
            sample.FilterConfig.id == filter_config_id
        ).scalar()

        filters = get_filter_config(self.config, filter_config)
        for f in filters:
            name = f['name']
            if name not in self.filter_functions:
                raise RuntimeError("Requested filter {} is not a valid filter name".format(name))

            try:
                filter_config = f['config']
                exceptions_config = f['exceptions']

                filter_data_type, filter_function = self.filter_functions[name]

                if filter_data_type == 'allele':
                    filtered = filter_function(gp_alleles_remaining, filter_config)

                    filter_exceptions = self.get_filter_exceptions(
                        exceptions_config,
                        set(itertools.chain.from_iterable(filtered.values()))
                    )

                    for gp_key, allele_ids in filtered.iteritems():
                        allele_ids = set(allele_ids)
                        if gp_key not in gp_alleles_filtered:
                            gp_alleles_filtered[gp_key] = dict()

                        # Subtract alleles that should be excepted from filtering
                        allele_ids -= filter_exceptions

                        # Intersect on input to make sure "faulty" filter doesn't give us
                        # ids not belonging to input.
                        gp_alleles_filtered[gp_key][name] = gp_alleles_remaining[gp_key] & allele_ids
                        gp_alleles_remaining[gp_key] -= allele_ids

                        # Update analyses' remaining since they are mixed
                        # with the 'allele' ones
                        for a_id, analysis_gp_key in analysis_genepanels.iteritems():
                            if analysis_gp_key == gp_key:
                                analysis_alleles_remaining[a_id] -= allele_ids

                elif filter_data_type == 'analysis':

                    filtered = filter_function(analysis_alleles_remaining, filter_config)

                    filter_exceptions = self.get_filter_exceptions(
                        exceptions_config,
                        set(itertools.chain.from_iterable(filtered.values()))
                    )

                    for a_id, allele_ids in filtered.iteritems():
                        allele_ids = set(allele_ids)

                        if a_id not in analysis_alleles_filtered:
                            analysis_alleles_filtered[a_id] = dict()

                        # Subtract alleles that should be excepted from filtering
                        allele_ids -= filter_exceptions

                        # Intersect on input to make sure "faulty" filter doesn't give us
                        # ids not belonging to input.
                        analysis_alleles_filtered[a_id][name] = analysis_alleles_remaining[a_id] & allele_ids
                        analysis_alleles_remaining[a_id] -= allele_ids
                else:
                    raise RuntimeError("Unknown filter data type '{}'".format(filter_data_type))

            except Exception:
                print "Error while running filter '{}'".format(name)
                raise

        # Prepare result for input gp_allele_ids
        gp_allele_result = dict()
        for gp_key, allele_ids in gp_allele_ids.iteritems():
            remaining_allele_ids = set(allele_ids)
            gp_allele_result[gp_key] = {
                'excluded_allele_ids': dict()
            }
            # Add filtered allele ids from 'allele' based filters
            # We need to intersect on original input since gp_allele_filtered
            # have alleles mixed in from analyses
            for name, filtered_allele_ids in gp_alleles_filtered[gp_key].iteritems():
                remaining_allele_ids -= filtered_allele_ids
                gp_allele_result[gp_key]['excluded_allele_ids'][name] = sorted(list(set(allele_ids) & filtered_allele_ids))

            gp_allele_result[gp_key]['allele_ids'] = sorted(list(remaining_allele_ids))

        # Prepare result for input analysis_allele_ids
        analysis_allele_result = {k: {'excluded_allele_ids': dict()} for k in analysis_allele_ids}
        remaining_allele_ids = {k: v for k,v in analysis_allele_ids.iteritems() }

        # Go through filters in the order run, to put filtered alleles in the correct filter category
        for f in filters:
            name = f['name']
            filter_data_type, _ = self.filter_functions[name]

            for a_id, allele_ids in analysis_allele_ids.iteritems():
                gp_key = analysis_genepanels[a_id]
                # Intersect filtered allele ids with remaining allele ids, to avoid putting alleles in multiple categories
                if filter_data_type == 'allele':
                    filtered_allele_ids = gp_alleles_filtered[gp_key][name]
                    analysis_allele_result[a_id]['excluded_allele_ids'][name] = sorted(list(filtered_allele_ids & remaining_allele_ids[a_id]))
                elif filter_data_type == 'analysis':
                    filtered_allele_ids = analysis_alleles_filtered[a_id][name]

                    analysis_allele_result[a_id]['excluded_allele_ids'][name] = sorted(list(filtered_allele_ids & remaining_allele_ids[a_id]))
                remaining_allele_ids[a_id] -= filtered_allele_ids

        for a_id in remaining_allele_ids:
            analysis_allele_result[a_id]['allele_ids'] = sorted(list(remaining_allele_ids[a_id]))

        return gp_allele_result, analysis_allele_result

