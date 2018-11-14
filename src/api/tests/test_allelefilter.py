"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""
import copy
import pytest

from api.allelefilter import AlleleFilter
from vardb.datamodel import allele, annotation, gene, annotationshadow, assessment, sample

import hypothesis as ht
import hypothesis.strategies as st


APP_CONFIG = {
    "classification": {
        "options": [  # Also defines sorting order
            # Adding a class needs ENUM update in DB, along with migration
            {
                "name": "Class U",
                "value": "U",
            },
            {
                "name": "Class 1",
                "value": "1"
            },
            {
                "name": "Class 2",
                "value": "2",
                "outdated_after_days": 180,  # Marked as outdated after N number of days
                "exclude_filtering_existing_assessment": True
            },
            {
                "name": "Class 3",
                "value": "3",
                "outdated_after_days": 180,
                "exclude_filtering_existing_assessment": True
            },
            {
                "name": "Class 4",
                "value": "4",
                "outdated_after_days": 180,
                "exclude_filtering_existing_assessment": True
            },
            {
                "name": "Class 5",
                "value": "5",
                "outdated_after_days": 365,
                "exclude_filtering_existing_assessment": True
            }
        ]
    },
    "filter": {
        "default_filter_config": {
            "allele_none": {},
            "allele_one_two": {},
            "allele_duplicate_one_two": {},
            "allele_three_four": {},
            "allele_five_six": {},
            "analysis_none": {},
            "analysis_one_two": {},
            "analysis_duplicate_one_two": {},
            "analysis_three_four": {},
            "analysis_five_six": {}
        }
    }
}

FILTER_CONFIG_NUM = 0


def insert_filter_config(session, filter_config):
    global FILTER_CONFIG_NUM
    FILTER_CONFIG_NUM += 1

    fc = sample.FilterConfig(
        name='Test {}'.format(FILTER_CONFIG_NUM),
        usergroup_id=1,
        filterconfig=filter_config
    )
    session.add(fc)
    session.commit()
    return fc.id


def create_filter_mock(to_remove):
    def filter_mock(key_allele_ids):
        result = dict()
        for gp_key, allele_ids in key_allele_ids.iteritems():
            result[gp_key] = set(to_remove)
        return result
    return filter_mock


class TestAlleleFilter(object):

    @pytest.mark.aa(order=0)
    def test_configurable_filtering(self, test_database, session):
        af = AlleleFilter(session, config=APP_CONFIG)

        # Mock the built-in filters
        def filter_one_two(key_allele_ids, filter_config):
            return create_filter_mock([1, 2])(key_allele_ids)

        def filter_three_four(key_allele_ids, filter_config):
            return create_filter_mock([3, 4])(key_allele_ids)

        def filter_five_six(key_allele_ids, filter_config):
            return create_filter_mock([5, 6])(key_allele_ids)

        def filter_none(key_allele_ids, filter_config):
            return create_filter_mock([])(key_allele_ids)

        af.filter_functions = {
            'allele_one_two': ('allele', filter_one_two),
            'allele_duplicate_one_two': ('allele', filter_one_two),
            'allele_three_four': ('allele', filter_three_four),
            'allele_five_six': ('allele', filter_five_six),
            'allele_none': ('allele', filter_none),
            'analysis_one_two': ('analysis', filter_one_two),
            'analysis_duplicate_one_two': ('analysis', filter_one_two),
            'analysis_three_four': ('analysis', filter_three_four),
            'analysis_five_six': ('analysis', filter_five_six),
            'analysis_none': ('analysis', filter_none)
        }

        # Test simple allele filter
        filter_config = {
            'filters': [
                {
                    'name': 'allele_one_two'
                }
            ],
            'filter_exceptions': []
        }

        testdata = {
            'key': [1, 2],
            'key2': [1, 4]
        }

        filter_config_id = insert_filter_config(session, filter_config)

        result, _ = af.filter_alleles(
            filter_config_id,
            testdata,
            None
        )

        expected_result = {
            'key': {
                'allele_ids': [],
                'excluded_allele_ids': {
                    'allele_one_two': [1, 2]
                }
            },
            'key2': {
                'allele_ids': [4],
                'excluded_allele_ids': {
                    'allele_one_two': [1]
                }
            }
        }
        assert result == expected_result

        # Test multiple allele filters
        filter_config = {
            'filters': [
                {
                    'name': 'allele_one_two',
                },
                {
                    'name': 'allele_duplicate_one_two',
                },
                {
                    'name': 'allele_three_four',
                },
                {
                    'name': 'allele_five_six',
                },
                {
                    'name': 'allele_none'
                }
            ]
        }

        filter_config_id = insert_filter_config(session, filter_config)

        testdata = {
            'key': [1, 2, 3, 4, 5, 6, 7, 8, 9]
        }
        result, _ = af.filter_alleles(
            filter_config_id,
            testdata,
            None
        )

        expected_result = {
            'key': {
                'allele_ids': [7, 8, 9],
                'excluded_allele_ids': {
                    'allele_one_two': [1, 2],
                    'allele_duplicate_one_two': [],
                    'allele_three_four': [3, 4],
                    'allele_five_six': [5, 6],
                    'allele_none': []
                }
            }
        }
        assert result == expected_result

        # Test single analysis filter
        filter_config = {
            'filters': [
                {
                    'name': 'analysis_one_two',
                }
            ]
        }

        filter_config_id = insert_filter_config(session, filter_config)

        testdata = {
            1: [1, 2, 3, 4],
            2: [1, 4]
        }

        _, result = af.filter_alleles(
            filter_config_id,
            None,
            testdata
        )

        expected_result = {
            1: {
                'allele_ids': [3, 4],
                'excluded_allele_ids': {
                    'analysis_one_two': [1, 2],
                }
            },
            2: {
                'allele_ids': [4],
                'excluded_allele_ids': {
                    'analysis_one_two': [1],
                }
            }
        }
        assert result == expected_result

        # Test multiple analysis filters
        filter_config = {
            'filters': [
                {
                    'name': 'analysis_one_two',
                },
                {
                    'name': 'analysis_duplicate_one_two',
                },
                {
                    'name': 'analysis_three_four',
                },
                {
                    'name': 'analysis_five_six',
                },
                {
                    'name': 'analysis_none',
                }
            ]
        }

        filter_config_id = insert_filter_config(session, filter_config)

        testdata = {
            1: [1, 2, 3, 4, 5, 6, 7, 8, 9]
        }

        _, result = af.filter_alleles(filter_config_id, None, testdata)

        expected_result = {
            1: {
                'allele_ids': [7, 8, 9],
                'excluded_allele_ids': {
                    'analysis_one_two': [1, 2],
                    'analysis_duplicate_one_two': [],
                    'analysis_three_four': [3, 4],
                    'analysis_five_six': [5, 6],
                    'analysis_none': [],
                }
            }
        }
        assert result == expected_result

        # Test combining analysis and allele filters
        filter_config = {
            'filters': [
                # Overlapping allele and analysis filter
                {
                    'name': 'allele_one_two',
                },
                {
                    'name': 'analysis_one_two',
                },
                {
                    'name': 'analysis_three_four',
                },
                {
                    'name': 'allele_five_six',
                },
                {
                    'name': 'analysis_none',
                }
            ]
        }

        filter_config_id = insert_filter_config(session, filter_config)

        # Make sure that the analysis' allele ids
        # are not mixed into gp_allele_ids when it
        # shares the same genepanel (HBOC_v01)
        an1 = session.query(sample.Analysis).filter(
            sample.Analysis.id == 1
        ).one()

        assert an1.genepanel_name == 'HBOC'
        assert an1.genepanel_version == 'v01'

        allele_testdata = {
            ('HBOC', 'v01'): [],
            ('Other', 'v01'): [1, 2, 3, 4, 5, 6, 7, 8, 9]
        }

        analysis_testdata = {
            1: [1, 2, 3, 4, 5, 6, 7, 8, 9]
        }

        allele_result, analysis_result = af.filter_alleles(
            filter_config_id,
            allele_testdata,
            analysis_testdata,
        )

        expected_allele_result = {
            ('HBOC', 'v01'): {
                'allele_ids': [],
                'excluded_allele_ids': {
                    'allele_one_two': [],
                    'allele_five_six': []
                }
            },
            ('Other', 'v01'): {
                'allele_ids': [3, 4, 7, 8, 9],
                'excluded_allele_ids': {
                    'allele_one_two': [1, 2],
                    'allele_five_six': [5, 6]
                }
            }
        }
        assert allele_result == expected_allele_result

        expected_analysis_result = {
            1: {
                'allele_ids': [7, 8, 9],
                'excluded_allele_ids': {
                    'allele_one_two': [1, 2],
                    'analysis_one_two': [],
                    'analysis_three_four': [3, 4],
                    'allele_five_six': [5, 6],
                    'analysis_none': []
                }
            }
        }
        assert analysis_result == expected_analysis_result

        # Test exceptions

        # Create assessment for id 2
        two_class_five = assessment.AlleleAssessment(
            allele_id=2,
            classification='5',
            genepanel_name='HBOC',
            genepanel_version='v01'
        )

        session.add(two_class_five)
        session.commit()

        filter_config = {
            'filters': [
                {
                    'name': 'allele_one_two',
                    'exceptions': [
                        {
                            'name': 'classification'
                        }
                    ]
                },
                {
                    'name': 'allele_three_four',
                    'exceptions': [
                        {
                            'name': 'classification'
                        }
                    ]
                }
            ]
        }

        filter_config_id = insert_filter_config(session, filter_config)
        testdata = {
            'key': [1, 2, 3, 4, 5, 6],
        }

        result, _ = af.filter_alleles(
            filter_config_id,
            testdata,
            None
        )

        expected_result = {
            'key': {
                'allele_ids': [2, 5, 6],
                'excluded_allele_ids': {
                    'allele_one_two': [1],
                    'allele_three_four': [3, 4]
                }
            }
        }

        assert result == expected_result

        filter_config = {
            'filters': [
                {
                    'name': 'analysis_one_two',
                    'exceptions': [
                        {
                            'name': 'classification'
                        }
                    ]
                },
                {
                    'name': 'allele_three_four',
                    'exceptions': [
                        {
                            'name': 'classification'
                        }
                    ]
                }
            ]
        }

        filter_config_id = insert_filter_config(session, filter_config)

        testdata = {
            1: [1, 2, 3, 4, 5, 6],
        }

        _, result = af.filter_alleles(
            filter_config_id,
            None,
            testdata
        )

        expected_result = {
            1: {
                'allele_ids': [2, 5, 6],
                'excluded_allele_ids': {
                    'analysis_one_two': [1],
                    'allele_three_four': [3, 4]
                }
            }
        }

        assert result == expected_result

        filter_config = {
            'filters': [
                {
                    'name': 'analysis_one_two',
                },
                {
                    'name': 'allele_one_two',
                }
            ]
        }

        filter_config_id = insert_filter_config(session, filter_config)

        allele_testdata = {
            ("HBOC", "v01"): [1, 2, 3, 4],
        }
        analysis_testdata = {
            1: [1,2,3,4]
        }

        allele_result, analysis_result = af.filter_alleles(
            filter_config_id,
            allele_testdata,
            analysis_testdata
        )


        expected_allele_result = {
            ("HBOC", "v01"): {
                "allele_ids": [3,4],
                "excluded_allele_ids": {
                    "allele_one_two": [1,2]
                }
            }
        }

        expected_analysis_result = {
            1: {
                "allele_ids": [3,4],
                "excluded_allele_ids": {
                    "analysis_one_two": [1,2],
                    "allele_one_two": []
                }
            }
        }

        assert allele_result == expected_allele_result
        assert analysis_result == expected_analysis_result
