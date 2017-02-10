import copy
import pytest

from api import ApiError

from api.tests import *

ANALYSIS_ID = 1


def assessment_template():
    return {
        "allele_id"           : 1,
        "annotation_id"       : 1,
        "analysis_id"         : 1,
        "user_id"             : 1,
        "classification"      : "1",
        "evaluation"          : {
            "comment": "Some comment",
        },
        "referenceassessments": []  # populated as part of test see referenceassessment_template
    }


def referenceassessment_template(allele_id):
    return {
        "allele_id"   : allele_id,
        "analysis_id" : 1,
        "user_id"     : 1,
        "reference_id": 9,  # must exist in database
        "evaluation"  : {
            "comment": "Some comment"
        },
    }


class TestAlleleAssessment(object):
    @pytest.mark.aa(order=0)
    def test_create_new(self, test_database):
        test_database.refresh()  # Reset db

        # Create an assessment for alleles in the interpretation
        interpretation = get_interpretation("analysis", ANALYSIS_ID,
                                            get_interpretation_id_of_first("analysis", ANALYSIS_ID))
        for idx, allele_id in enumerate(interpretation['allele_ids']):
            # Prepare
            assessment_data = copy.deepcopy(assessment_template())
            assessment_data['allele_id'] = allele_id
            assessment_data['referenceassessments'] = [referenceassessment_template(allele_id)]

            annotations = [{"allele_id"    : assessment_data['allele_id'],
                            "annotation_id": assessment_data['annotation_id']}
                           ]
            custom_annotations = [{"allele_id"           : assessment_data['allele_id'],
                                   "custom_annotation_id": 1}
                                  ]

            # POST data
            api_response = api.post('/alleleassessments/', {"annotations"       : annotations,
                                                            "custom_annotations": custom_annotations,
                                                            "allele_assessments": [assessment_data]})

            # Check response
            assert api_response.status_code == 200
            created_assessment = api_response.json[0]
            assert len(created_assessment['referenceassessments']) == 1
            assert 'id' in created_assessment['referenceassessments'][0]
            assert created_assessment['referenceassessments'][0]['allele_id'] == allele_id
            assert created_assessment['allele_id'] == allele_id
            assert created_assessment['id'] == idx + 1
            assert created_assessment['annotation_id'] == assessment_data['annotation_id']
            assert created_assessment['custom_annotation_id'] == 1

    @pytest.mark.aa(order=1)
    def test_update_assessment(self):
        """
        Simulate updating the AlleleAssessment created in create_new().
        It should result in a new AlleleAssessment being created,
        while the existing should be superceded.
        """

        interpretation = get_interpretation("analysis", ANALYSIS_ID,
                                            get_interpretation_id_of_first("analysis", ANALYSIS_ID))

        q = {'allele_id': interpretation['allele_ids'], 'date_superceeded': None}
        previous_assessments = api.get('/alleleassessments/?q={}'.format(json.dumps(q))).json

        previous_ids = []
        for assessment_data in previous_assessments:
            # Build assessment data suitable for saving
            prev_id = assessment_data['id']
            previous_ids.append(prev_id)  # bookkeeping
            # Delete the id, to make the backend create a new assessment
            del assessment_data['id']
            del assessment_data['previous_assessment_id']  # remove as a null value creates an schema exception
            assessment_data['presented_alleleassessment_id'] = prev_id  # Api requirement dictated by finalization
            assessment_data['reuse'] = False
            assessment_data['evaluation']['comment'] = "A new assessment superceeding an old one"

            # Update referenceassessment
            prev_ra_id = assessment_data['referenceassessments'][0]['id']
            del assessment_data['referenceassessments'][0]['id']
            assessment_data['referenceassessments'][0]['evaluation'] = {'comment': 'Some new reference comment'}

            # POST (a single) assessment
            annotations = [
                {"allele_id": assessment_data['allele_id'], "annotation_id": assessment_data['annotation_id']}]
            r = api.post('/alleleassessments/', {"annotations"       : annotations,
                                                 "allele_assessments": [assessment_data]})

            # Check response
            assert r.status_code == 200
            new_assessment = r.json[0]  # we posted only one, so expect only one in return
            assert new_assessment['id'] != prev_id
            assert new_assessment['evaluation']['comment'] == 'A new assessment superceeding an old one'

            # Check that a new referenceassessment was created
            assert new_assessment['referenceassessments'][0]['id'] != prev_ra_id
            assert new_assessment['referenceassessments'][0]['evaluation']['comment'] == 'Some new reference comment'

        # Reload the previous alleleassessments and make sure
        # they're marked as superceded
        q = {'id': previous_ids}
        previous_assessments = api.get('/alleleassessments/?q={}'.format(json.dumps(q))).json

        assert all([p['date_superceeded'] is not None for p in previous_assessments])

    @pytest.mark.aa(order=2)
    def test_fail_cases(self):
        """
        Test cases where it should fail to create assessments.
        """

        assessment_data = copy.deepcopy(assessment_template())
        annotations = [{"annotation_id": 1, "allele_id": assessment_data['allele_id']}]

        # Test without allele_id
        del assessment_data['allele_id']

        # We don't run actual HTTP requests, everything is in python
        # so we can catch the exceptions directly
        with pytest.raises(
                Exception):  # the error is not caught at the API boundary as enforcing required fields for dict of dict isn't implemented
            api.post('/alleleassessments/', {"annotations"       : annotations,
                                             "allele_assessments": [assessment_data]})

        # Test without analysis_id
        assessment_data = copy.deepcopy(assessment_template())
        del assessment_data['analysis_id']

        with pytest.raises(ApiError):
            api.post('/alleleassessments/', {"annotations"       : annotations,
                                             "allele_assessments": [assessment_data]})
