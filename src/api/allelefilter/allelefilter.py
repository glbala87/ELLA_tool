import itertools
from collections import defaultdict

from api.config import config as global_config
from vardb.datamodel import assessment, sample, allele, genotype

from api.allelefilter.frequencyfilter import FrequencyFilter
from api.allelefilter.segregationfilter import SegregationFilter
from api.allelefilter.regionfilter import RegionFilter
from api.allelefilter.qualityfilter import QualityFilter


class AlleleFilter(object):

    def __init__(self, session, config=None):
        self.session = session
        self.config = global_config if not config else config

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

    def remove_filtered_from_source(self, source, filtered):
        """
        Mutates arguments.

        Removes filtered allele_ids from the source structures allele_ids
        source: {key: set([..]), ...}
        filtered: {key: set([...]), ...}

        Allele ids that have classifications are not removed.
        """

        all_filtered_allele_ids = set(itertools.chain.from_iterable(filtered.values()))
        # Exclude alleles with classifications from filtering
        exempt_filtering = self.get_allele_ids_with_classification(all_filtered_allele_ids)
        for key in source:
            filtered[key] = filtered[key] - exempt_filtering
            source[key] = set(source[key]) - filtered[key]

    def filter_analyses(self, analyses_allele_ids):
        """

        Runs both pure allele filters and analysis based allele filters.

        Returns:
        {
            <analysis_id>: {
                'allele_ids': [1, 2, 3],
                'excluded_allele_ids': {
                    'segregation': [4, 5],
                }
            },
            ...
        }
        """

        result = {a_id: {'allele_ids': list(), 'excluded_allele_ids': dict()} for a_id in analyses_allele_ids}

        analyses_allele_ids_copy = {k: set(v) for k, v in analyses_allele_ids.iteritems()}

        # Get all alleles for provided analyses
        analyses_genepanels = self.session.query(
            sample.Analysis.id,
            sample.Analysis.genepanel_name,
            sample.Analysis.genepanel_version,
        ).filter(
            sample.Analysis.id.in_(analyses_allele_ids_copy.keys())
        ).all()

        # Group data for later
        analysis_genepanel = dict()
        for analysis_id, gp_name, gp_version in analyses_genepanels:
            analysis_genepanel[analysis_id] = (gp_name, gp_version)

        gp_allele_ids = defaultdict(set)
        for analysis_id, allele_ids in analyses_allele_ids_copy.iteritems():
            gp_key = analysis_genepanel[analysis_id]
            gp_allele_ids[gp_key].update(set(allele_ids))

        # Run the pure allele filters first, since that is the order of the filters currently
        filtered_alleles = self.filter_alleles(gp_allele_ids)

        # Insert into result and remove any already filtered alleles for performance
        for analysis_id, allele_ids in analyses_allele_ids_copy.iteritems():
            gp_key = analysis_genepanel[analysis_id]
            gp_non_filtered_allele_ids = set(filtered_alleles[(gp_key)]['allele_ids'])

            # Intersect with this analysis' allele_ids since there can be multiple analyses with same genepanel
            analyses_allele_ids_copy[analysis_id] = allele_ids & gp_non_filtered_allele_ids
            for filter_name, filtered_allele_ids in filtered_alleles[(gp_key)]['excluded_allele_ids'].iteritems():
                result[analysis_id]['excluded_allele_ids'][filter_name] = sorted(list(allele_ids & set(filtered_allele_ids)))

        # Run the analysis based allele filters
        filters = [
            ('quality', QualityFilter(self.session, self.config).filter_alleles),
            ('segregation', SegregationFilter(self.session, self.config).filter_alleles)
        ]

        for filter_name, filter_func in filters:
            filtered = filter_func(analyses_allele_ids_copy)
            self.remove_filtered_from_source(analyses_allele_ids_copy, filtered)
            for analysis_id, allele_ids in filtered.iteritems():
                result[analysis_id]['excluded_allele_ids'][filter_name] = sorted(list(allele_ids))

        # We have removed filtered allele_ids from analysis_allele_ids,
        # so what's left are the non-filtered result
        for analysis_id, allele_ids in analyses_allele_ids_copy.iteritems():
            result[analysis_id]['allele_ids'] = sorted(list(allele_ids))

        return result

    def filter_alleles(self, gp_allele_ids):
        """
        Returns:
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

        filters = [
            # Order matters!
            ('frequency', FrequencyFilter(self.session, self.config).filter_alleles),
            ('region', RegionFilter(self.session, self.config).filter_alleles),
        ]

        result = dict()
        for gp_key in gp_allele_ids:
            result[gp_key] = {
                'excluded_allele_ids': {}
            }

        # Exclude the filtered alleles from one filter from being sent to
        # next filter, in order to improve performance. Matters a lot
        # for large samples, since the frequency filter filters most of the variants
        for filter_name, filter_func in filters:
            filtered = filter_func(gp_allele_ids)
            self.remove_filtered_from_source(gp_allele_ids, filtered)
            for gp_key, allele_ids in filtered.iteritems():
                result[gp_key]['excluded_allele_ids'][filter_name] = sorted(list(allele_ids))

        # Finally add the remaining allele_ids, these weren't filtered out
        for gp_key in gp_allele_ids:
            result[gp_key]['allele_ids'] = sorted(list(gp_allele_ids[gp_key]))

        return result
