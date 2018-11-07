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
            gp_allele_ids = {k: set(v) for k, v in gp_allele_ids.iteritems()}
        else:
            gp_allele_ids = dict()

        analysis_genepanels = self.session.query(
            sample.Analysis.id,
            sample.Analysis.genepanel_name,
            sample.Analysis.genepanel_version,
        ).filter(
            sample.Analysis.id.in_(analysis_allele_ids.keys())
        ).all()

        analysis_genepanels = {a.id: (a.genepanel_name, a.genepanel_version) for a in analysis_genepanels}

        analysis_gp_allele_ids = dict()
        for a_id, gp_key in analysis_genepanels.iteritems():
            if gp_key not in analysis_gp_allele_ids:
                analysis_gp_allele_ids[gp_key] = set()
            analysis_gp_allele_ids[gp_key] |= set(analysis_allele_ids[a_id])

        all_gp_keys = set(analysis_gp_allele_ids.keys() + gp_allele_ids.keys())

        # Run filter functions.
        # Already filtered alleles are tracked to avoid re-filtering same alleles (for performance reasons).

        filter_config = self.session.query(sample.FilterConfig.filterconfig).filter(
            sample.FilterConfig.id == filter_config_id
        ).scalar()

        analysis_allele_result = {a_id: {"excluded_allele_ids": dict()} for a_id in analysis_allele_ids}
        gp_allele_result = {gp_key: {"excluded_allele_ids": dict()} for gp_key in gp_allele_ids}

        filters = get_filter_config(self.config, filter_config)
        for f in filters:
            name = f['name']
            if name not in self.filter_functions:
                raise RuntimeError("Requested filter {} is not a valid filter name".format(name))

            try:
                filter_config = f['config']
                exceptions_config = f['exceptions']

                filter_data_type, filter_function = self.filter_functions[name]
                assert filter_data_type in ['allele', 'analysis'], "Unknown filter data type '{}'".format(filter_data_type)

                # Create container for keeping filter results
                filtered_allele_ids = dict()

                # Run filter
                if filter_data_type == 'allele':
                    # Merge analysis_gp_allele_ids and gp_allele_ids
                    gp_alleles_merged = {gp_key: analysis_gp_allele_ids.get(gp_key, set()) | gp_allele_ids.get(gp_key, set()) for gp_key in all_gp_keys}

                    filtered = filter_function(gp_alleles_merged, filter_config)

                    filter_exceptions = self.get_filter_exceptions(
                        exceptions_config,
                        set(itertools.chain.from_iterable(filtered.values()))
                    )

                    for gp_key, allele_ids in filtered.iteritems():
                        # Subtract alleles that should be excepted from filtering
                        filtered_allele_ids[gp_key] = set(allele_ids) - filter_exceptions

                elif filter_data_type == 'analysis':
                    filtered = filter_function(analysis_allele_ids, filter_config)

                    filter_exceptions = self.get_filter_exceptions(
                        exceptions_config,
                        set(itertools.chain.from_iterable(filtered.values()))
                    )

                    for a_id, allele_ids in filtered.iteritems():
                        # Subtract alleles that should be excepted from filtering
                        filtered_allele_ids[a_id] = set(allele_ids) - filter_exceptions

                # Update data structures gp_allele_ids, analysis_gp_allele_ids, and analysis_allele_ids by removing filtered alleles from the remaining alleles
                # This is done to:
                # 1. Improve performance by not running already filtered alleles in subsequent filters
                # 2. Prevent alleles from ending up in multiple filters
                if filter_data_type == 'allele':
                    for gp_key, allele_ids in filtered_allele_ids.iteritems():
                        if gp_key in gp_allele_ids:
                            # Insert filter result in genepanel data structure to be returned
                            gp_allele_result[gp_key]["excluded_allele_ids"][name] = sorted(list(gp_allele_ids[gp_key] & allele_ids))
                            gp_allele_ids[gp_key] -= allele_ids

                        if gp_key in analysis_gp_allele_ids:
                            analysis_gp_allele_ids[gp_key] -= allele_ids

                            for a_id, analysis_gp_key in analysis_genepanels.iteritems():
                                if analysis_gp_key == gp_key:
                                    # Insert filter result in analysis data structure to be returned
                                    analysis_allele_result[a_id]["excluded_allele_ids"][name] = sorted(list(analysis_allele_ids[a_id] & allele_ids))

                                    analysis_allele_ids[a_id] -= allele_ids

                elif filter_data_type == 'analysis':
                    for a_id, allele_ids in filtered_allele_ids.iteritems():
                        # Insert filter result in analysis data structure to be returned
                        analysis_allele_result[a_id]["excluded_allele_ids"][name] = sorted(list(analysis_allele_ids[a_id] & allele_ids))
                        analysis_allele_ids[a_id] -= allele_ids

                        analysis_gp_key = analysis_genepanels[a_id]
                        analysis_gp_allele_ids[analysis_gp_key] -= allele_ids

            except Exception:
                print "Error while running filter '{}'".format(name)
                raise


        # The alleles remaining from analysis_allele_ids and gp_allele_ids are unfiltered
        for a_id in analysis_allele_result:
            analysis_allele_result[a_id]["allele_ids"] = sorted(list(analysis_allele_ids[a_id]))
        for gp_key in gp_allele_result:
            gp_allele_result[gp_key]["allele_ids"] = sorted(list(gp_allele_ids[gp_key]))

        return gp_allele_result, analysis_allele_result

