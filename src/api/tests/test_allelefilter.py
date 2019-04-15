"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""
import pytest

from api.allelefilter import AlleleFilter
from vardb.datamodel import sample, jsonschema

import hypothesis as ht
import hypothesis.strategies as st


APP_CONFIG = {
    "filter": {
        "default_filter_config": {
            "allele_none": {},
            "allele_one": {},
            "allele_one_two": {},
            "allele_duplicate_one_two": {},
            "allele_three_four": {},
            "allele_five_six": {},
            "allele_filter_one_three_if_one": {},
            "analysis_none": {},
            "analysis_one_two": {},
            "analysis_duplicate_one_two": {},
            "analysis_three_four": {},
            "analysis_five_six": {},
            "analysis_filter_one_three_if_one": {},
        }
    }
}

FILTER_CONFIG_NUM = 0


def insert_filter_config(session, filter_config):
    global FILTER_CONFIG_NUM
    FILTER_CONFIG_NUM += 1

    # Add dummy schema that allows for any object
    jsonschema.JSONSchema.get_or_create(
        session, **{"name": "filterconfig", "version": 10000, "schema": {"type": "object"}}
    )

    fc = sample.FilterConfig(name="Test {}".format(FILTER_CONFIG_NUM), filterconfig=filter_config)
    session.add(fc)
    session.commit()
    return fc.id


def create_filter_mock(to_remove):
    def filter_mock(key_allele_ids):
        result = dict()
        for gp_key, allele_ids in key_allele_ids.items():
            result[gp_key] = set(allele_ids) & set(to_remove)
        return result

    return filter_mock


@pytest.fixture
def allele_filter(session):
    af = AlleleFilter(session, config=APP_CONFIG)

    # Mock the built-in filters
    def filter_one(key_allele_ids, filter_config):
        return create_filter_mock([1])(key_allele_ids)

    def filter_one_two(key_allele_ids, filter_config):
        return create_filter_mock([1, 2])(key_allele_ids)

    def filter_three_four(key_allele_ids, filter_config):
        return create_filter_mock([3, 4])(key_allele_ids)

    def filter_five_six(key_allele_ids, filter_config):
        return create_filter_mock([5, 6])(key_allele_ids)

    def filter_none(key_allele_ids, filter_config):
        return create_filter_mock([])(key_allele_ids)

    def filter_one_three_if_one(key_allele_ids, filter_config):
        result = dict()
        for gp_key, allele_ids in key_allele_ids.items():
            if 1 in allele_ids:
                result[gp_key] = set(allele_ids) & set([1, 3])
            else:
                result[gp_key] = set([])

        return result

    assert filter_one_three_if_one({1: [1, 3]}, None) == {1: set([1, 3])}
    assert filter_one_three_if_one({1: [3]}, None) == {1: set([])}

    af.filter_functions = {
        "allele_one": ("allele", filter_one),
        "allele_one_two": ("allele", filter_one_two),
        "allele_duplicate_one_two": ("allele", filter_one_two),
        "allele_three_four": ("allele", filter_three_four),
        "allele_five_six": ("allele", filter_five_six),
        "allele_filter_one_three_if_one": ("allele", filter_one_three_if_one),
        "allele_none": ("allele", filter_none),
        "analysis_one_two": ("analysis", filter_one_two),
        "analysis_duplicate_one_two": ("analysis", filter_one_two),
        "analysis_three_four": ("analysis", filter_three_four),
        "analysis_five_six": ("analysis", filter_five_six),
        "analysis_filter_one_three_if_one": ("analysis", filter_one_three_if_one),
        "analysis_none": ("analysis", filter_none),
    }

    return af


class TestAlleleFilter(object):
    @pytest.mark.aa(order=0)
    def test_filter_alleles(self, session, allele_filter):

        # ---------

        # Test simple allele filter
        filter_config = {"filters": [{"name": "allele_one_two"}], "filter_exceptions": []}
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = {"key": [1, 2], "key2": [1, 4]}

        result = allele_filter.filter_alleles(filter_config_id, testdata)
        expected_result = {
            "key": {"allele_ids": [], "excluded_allele_ids": {"allele_one_two": [1, 2]}},
            "key2": {"allele_ids": [4], "excluded_allele_ids": {"allele_one_two": [1]}},
        }

        # ---------

        assert result == expected_result

        # Test multiple allele filters
        filter_config = {
            "filters": [
                {"name": "allele_one_two"},
                {"name": "allele_duplicate_one_two"},
                {"name": "allele_three_four"},
                {"name": "allele_five_six"},
                {"name": "allele_none"},
            ]
        }
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = {"key": [1, 2, 3, 4, 5, 6, 7, 8, 9]}

        result = allele_filter.filter_alleles(filter_config_id, testdata)

        expected_result = {
            "key": {
                "allele_ids": [7, 8, 9],
                "excluded_allele_ids": {
                    "allele_one_two": [1, 2],
                    "allele_duplicate_one_two": [],
                    "allele_three_four": [3, 4],
                    "allele_five_six": [5, 6],
                    "allele_none": [],
                },
            }
        }
        assert result == expected_result

        # ---------

        # Test exceptions

        # Test allele exception on allele filter
        filter_config = {
            "filters": [{"name": "allele_one_two", "exceptions": [{"name": "allele_one"}]}]
        }
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = {"key": [1, 2, 3, 4]}

        result = allele_filter.filter_alleles(filter_config_id, testdata)

        expected_result = {
            "key": {"allele_ids": [1, 3, 4], "excluded_allele_ids": {"allele_one_two": [2]}}
        }

        assert result == expected_result

        # ---------
        # Test that analysis exception on allele filter fails
        filter_config = {
            "filters": [{"name": "allele_one_two", "exceptions": [{"name": "analysis_one_two"}]}]
        }

        filter_config_id = insert_filter_config(session, filter_config)
        with pytest.raises(AssertionError):
            allele_filter.filter_alleles(filter_config_id, {})

        # ---------
        # Test that exceptions only apply to the filter specified to
        filter_config = {
            "filters": [
                {"name": "allele_one_two", "exceptions": [{"name": "allele_three_four"}]},
                {"name": "allele_three_four", "exceptions": [{"name": "allele_one_two"}]},
            ]
        }
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = {"key": [1, 2, 3, 4]}

        result = allele_filter.filter_alleles(filter_config_id, testdata)

        expected_result = {
            "key": {
                "allele_ids": [],
                "excluded_allele_ids": {"allele_one_two": [1, 2], "allele_three_four": [3, 4]},
            }
        }

        assert result == expected_result

    @pytest.mark.aa(order=1)
    def test_filter_analysis(self, session, allele_filter):

        # ---------

        # Test single analysis filter
        filter_config = {"filters": [{"name": "analysis_one_two"}]}
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = [1, 2, 3, 4]

        result = allele_filter.filter_analysis(filter_config_id, 1, testdata)

        expected_result = {
            "allele_ids": [3, 4],
            "excluded_allele_ids": {"analysis_one_two": [1, 2]},
        }
        assert result == expected_result

        # ---------

        # Test multiple analysis filters
        filter_config = {
            "filters": [
                {"name": "analysis_one_two"},
                {"name": "analysis_duplicate_one_two"},
                {"name": "analysis_three_four"},
                {"name": "analysis_five_six"},
                {"name": "analysis_none"},
            ]
        }
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        result = allele_filter.filter_analysis(filter_config_id, 1, testdata)
        expected_result = {
            "allele_ids": [7, 8, 9],
            "excluded_allele_ids": {
                "analysis_one_two": [1, 2],
                "analysis_duplicate_one_two": [],
                "analysis_three_four": [3, 4],
                "analysis_five_six": [5, 6],
                "analysis_none": [],
            },
        }
        assert result == expected_result

        # ---------

        # Test combining analysis and allele filters
        filter_config = {
            "filters": [
                # Overlapping allele and analysis filter
                {"name": "allele_one_two"},
                {"name": "analysis_one_two"},
                {"name": "analysis_three_four"},
                {"name": "allele_five_six"},
                {"name": "analysis_none"},
            ]
        }
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        result = allele_filter.filter_analysis(filter_config_id, 1, testdata)

        expected_result = {
            "allele_ids": [7, 8, 9],
            "excluded_allele_ids": {
                "allele_one_two": [1, 2],
                "analysis_one_two": [],
                "analysis_three_four": [3, 4],
                "allele_five_six": [5, 6],
                "analysis_none": [],
            },
        }
        assert result == expected_result

        # ---------
        # Test allele exception on analysis filter
        filter_config = {
            "filters": [{"name": "analysis_one_two", "exceptions": [{"name": "allele_one"}]}]
        }
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = [1, 2, 3, 4]
        result = allele_filter.filter_analysis(filter_config_id, 1, testdata)

        expected_result = {
            "allele_ids": [1, 3, 4],
            "excluded_allele_ids": {"analysis_one_two": [2]},
        }

        assert result == expected_result

        # ---------
        # Test analysis exception on analysis filter
        filter_config = {
            "filters": [
                {"name": "analysis_one_two", "exceptions": [{"name": "analysis_one_two"}]},
                {"name": "analysis_three_four", "exceptions": [{"name": "analysis_one_two"}]},
            ]
        }
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = [1, 2, 3, 4]

        result = allele_filter.filter_analysis(filter_config_id, 1, testdata)

        expected_result = {
            "allele_ids": [1, 2],
            "excluded_allele_ids": {"analysis_one_two": [], "analysis_three_four": [3, 4]},
        }

        assert result == expected_result

        # ---------

        filter_config = {"filters": [{"name": "analysis_one_two"}, {"name": "allele_one_two"}]}
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = [1, 2, 3, 4]

        result = allele_filter.filter_analysis(filter_config_id, 1, testdata)

        expected_result = {
            "allele_ids": [3, 4],
            "excluded_allele_ids": {"analysis_one_two": [1, 2], "allele_one_two": []},
        }
        assert result == expected_result

        # ---------
        # Test filters working conditionally to make sure
        # previously filtered are not sent to next
        # Four cases

        # analysis -> analysis

        filter_config = {
            "filters": [{"name": "analysis_one_two"}, {"name": "analysis_filter_one_three_if_one"}]
        }
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = [1, 2, 3, 4]
        result = allele_filter.filter_analysis(filter_config_id, 1, testdata)
        expected_result = {
            "allele_ids": [3, 4],
            "excluded_allele_ids": {
                "analysis_one_two": [1, 2],
                "analysis_filter_one_three_if_one": [],
            },
        }
        assert result == expected_result

        # allele -> analysis
        filter_config = {
            "filters": [{"name": "allele_one_two"}, {"name": "analysis_filter_one_three_if_one"}]
        }
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = [1, 2, 3, 4]
        result = allele_filter.filter_analysis(filter_config_id, 1, testdata)
        expected_result = {
            "allele_ids": [3, 4],
            "excluded_allele_ids": {
                "allele_one_two": [1, 2],
                "analysis_filter_one_three_if_one": [],
            },
        }
        assert result == expected_result

        # allele -> analysis
        filter_config = {
            "filters": [{"name": "analysis_one_two"}, {"name": "allele_filter_one_three_if_one"}]
        }
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = [1, 2, 3, 4]
        result = allele_filter.filter_analysis(filter_config_id, 1, testdata)
        expected_result = {
            "allele_ids": [3, 4],
            "excluded_allele_ids": {
                "analysis_one_two": [1, 2],
                "allele_filter_one_three_if_one": [],
            },
        }
        assert result == expected_result

        # allele -> allele
        filter_config = {
            "filters": [{"name": "allele_one_two"}, {"name": "allele_filter_one_three_if_one"}]
        }
        filter_config_id = insert_filter_config(session, filter_config)

        testdata = [1, 2, 3, 4]
        result = allele_filter.filter_analysis(filter_config_id, 1, testdata)
        expected_result = {
            "allele_ids": [3, 4],
            "excluded_allele_ids": {"allele_one_two": [1, 2], "allele_filter_one_three_if_one": []},
        }
        assert result == expected_result
