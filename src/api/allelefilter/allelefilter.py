from sqlalchemy import literal_column, text, or_, func
from api.config import config as global_config
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
        Return the allele_ids that have Clinvar
        'clinical_significance_descr' that is 'Likely pathogenic' or 'Pathogenic'

        SELECT allele_id, clinsig FROM (SELECT allele_id, jsonb_array_elements(annotations->'external'->'CLINVAR'->'items')->>'clinical_significance_descr' AS clinsig from annotation) AS c WHERE c.clinsig ILIKE 'Pathogenic' or c.clinsig ILIKE 'Likely pathogenic'
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

    def get_exempt_filtered(self, filtered):
        """
        Checks whether any of the 'filtered' allele ids should be exempted from filtering.
        """

        # Exclude alleles with classifications from filtering
        exempt_filtering = self.get_allele_ids_with_classification(filtered)
        exempt_filtering |= self.get_allele_ids_with_pathogenic_clinvar(filtered)
        return exempt_filtering

    def filter_alleles(self, gp_allele_ids, analysis_allele_ids):
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

        CONFIG = {
            "filters": [
                {
                    "name": "frequency",
                    "config": {
                        "groups": {
                            "external": {
                                "GNOMAD_GENOMES": [
                                    "G",
                                    "AFR",
                                    "AMR",
                                    "EAS",
                                    "FIN",
                                    "NFE",
                                    "OTH",
                                    "SAS"
                                ],
                                "GNOMAD_EXOMES": [
                                    "G",
                                    "AFR",
                                    "AMR",
                                    "EAS",
                                    "FIN",
                                    "NFE",
                                    "OTH",
                                    "SAS"
                                ]
                            },
                            "internal": {
                                "inDB": [
                                    "OUSWES"
                                ]
                            }
                        },
                        "num_thresholds": {
                            "GNOMAD_GENOMES": {
                                "G": 5000,
                                "AFR": 5000,
                                "AMR": 5000,
                                "EAS": 5000,
                                "FIN": 5000,
                                "NFE": 5000,
                                "OTH": 5000,
                                "SAS": 5000
                            },
                            "GNOMAD_EXOMES": {
                                "G": 5000,
                                "AFR": 5000,
                                "AMR": 5000,
                                "EAS": 5000,
                                "FIN": 5000,
                                "NFE": 5000,
                                "OTH": 5000,
                                "SAS": 5000
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
                    }
                },
                {
                    "name": "region",
                    "config": {
                        "splice_region": [-20, 6],
                        "utr_region": [0,0]
                    }
                },
                {
                    "name": "quality",
                    "config": {
                        "score": 100,
                        "allele_ratio": {
                            "heterozygous": [0.3, 0.7],
                            "homozygous": [0.9, 1.0]
                        }
                    }
                },
                {
                    "name": "segregation",
                    "config": {}
                }
            ]
        }

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
        for f in CONFIG['filters']:
            name = f['name']
            try:
                if name not in self.filter_functions:
                    raise RuntimeError("Requested filter {} is not a valid filter name".format(name))

                filter_data_type, filter_function = self.filter_functions[name]

                if filter_data_type == 'allele':
                    filtered = filter_function(gp_alleles_remaining)
                    for gp_key, allele_ids in filtered.iteritems():
                        allele_ids = set(allele_ids)
                        if gp_key not in gp_alleles_filtered:
                            gp_alleles_filtered[gp_key] = dict()
                        gp_alleles_filtered[gp_key][name] = allele_ids
                        gp_alleles_remaining[gp_key] -= allele_ids

                        # Update analyses' remaining since they are mixed
                        # with the 'allele' ones
                        for a_id, analysis_gp_key in analysis_genepanels.iteritems():
                            if analysis_gp_key == gp_key:
                                analysis_alleles_remaining[a_id] -= allele_ids

                elif filter_data_type == 'analysis':

                    filtered = filter_function(analysis_alleles_remaining)
                    for a_id, allele_ids in filtered.iteritems():
                        if a_id not in analysis_alleles_filtered:
                            analysis_alleles_filtered[a_id] = dict()
                        analysis_alleles_filtered[a_id][name] = set(allele_ids)
                        analysis_alleles_remaining[a_id] -= set(allele_ids)
                else:
                    raise RuntimeError("Unknown filter data type '{}'".format(filter_data_type))

            except Exception:
                print "Error while running filter '{}'".format(name)
                raise

        # Create list of alleles are exempted from being filtered
        all_filtered_allele_ids = set()
        for category_result in gp_alleles_filtered.values():
            for filtered_alleles in category_result.values():
                all_filtered_allele_ids |= filtered_alleles
        for category_result in analysis_alleles_filtered.values():
            for filtered_alleles in category_result.values():
                all_filtered_allele_ids |= filtered_alleles
        exempt_filtering = self.get_exempt_filtered(all_filtered_allele_ids)

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
                filtered_allele_ids -= exempt_filtering
                remaining_allele_ids -= filtered_allele_ids
                gp_allele_result[gp_key]['excluded_allele_ids'][name] = sorted(list(allele_ids & filtered_allele_ids))

            gp_allele_result[gp_key]['allele_ids'] = sorted(list(remaining_allele_ids))

        # Prepare result for input analysis_allele_ids
        analysis_allele_result = dict()
        for a_id, allele_ids in analysis_allele_ids.iteritems():
            remaining_allele_ids = set(allele_ids)
            analysis_allele_result[a_id] = {
                'excluded_allele_ids': dict()
            }
            # Add filtered allele ids from 'analysis' based filters
            for name, filtered_allele_ids in analysis_alleles_filtered[a_id].iteritems():
                filtered_allele_ids -= exempt_filtering
                remaining_allele_ids -= filtered_allele_ids
                analysis_allele_result[a_id]['excluded_allele_ids'][name] = sorted(list(filtered_allele_ids))
            # Add filtered allele ids from 'allele' based filters
            for name, filtered_allele_ids in gp_alleles_filtered[analysis_genepanels[a_id]].iteritems():
                filtered_allele_ids -= exempt_filtering
                remaining_allele_ids -= filtered_allele_ids
                analysis_allele_result[a_id]['excluded_allele_ids'][name] = sorted(list(allele_ids & filtered_allele_ids))

            analysis_allele_result[a_id]['allele_ids'] = sorted(list(remaining_allele_ids))

        return gp_allele_result, analysis_allele_result

