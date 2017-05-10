import pytest

from api.tests import *

"""
Test the interpretation workflow of
 - a sample/analysis
 - a single variant

 The single variant is chosen not be included in the sample/analysis. So any assessments done in either sample or variant
 workflow won't affect each other.

 The tests for variant and sample workflows are similar. The differences are handled using parametrized tests, some
  workflow specific test fixture and branching based on workflow.
"""

def item_connected_to_allele_is_current(allele_id, items_source, expected_comment):
    items = filter(lambda item: item['allele_id'] == allele_id, items_source)
    assert any(map(lambda a: a['date_superceeded'] is None and a['evaluation']['comment'] == expected_comment, items)),\
        "No assessment/report for allele {} that's current has comment '{}'".format(allele_id, expected_comment)


def item_connected_to_allele_has_been_superceeded(allele_id, items_source, expected_comment):
    selected_items = filter(lambda item: item['allele_id'] == allele_id, items_source)
    assert any(map(lambda a: a['date_superceeded'] is not None and a['evaluation']['comment'] == expected_comment, selected_items)),\
               "no assessment/report for allele {} that has been superceeded has the comment '{}' ".format(allele_id, expected_comment)


USER_ID_OF = {  # actually the index of a list of users
    ANALYSIS_WORKFLOW: {"round_1": 1, "round_2": 1, "round_3": 1},
    VARIANT_WORKFLOW: {"round_1": 1, "round_2": 1, "round_3": 1}
}

INTERPRETATION_INIT_DATA = {
    ANALYSIS_WORKFLOW: None,
    VARIANT_WORKFLOW: {"gp_name": "HBOCUTV", "gp_version": "v01"}
}

ASSESSMENT_EXTRA_DATA = {
    ANALYSIS_WORKFLOW: None,
    VARIANT_WORKFLOW: {"genepanel_name": "HBOCUTV", "genepanel_version": "v01"}
}

REFERENCEASSESSMENT_EXTRA_DATA = {
    ANALYSIS_WORKFLOW: 1,
    VARIANT_WORKFLOW: {"genepanel_name": "HBOCUTV", "genepanel_version": "v01"}
}

ID_OF = {
    ANALYSIS_WORKFLOW: 1,  # analysis_id = 1, allele 1-6
    VARIANT_WORKFLOW: 12   # allele id 12, brca2 c.1275A>G,  GRCh37/13-32906889-32906890-A-G?gp_name=HBOCUTV&gp_version=v01
}


def assert_all_interpretations_are_done(interpretations):
    expected_status = "Done"
    assert all([i['status'] == expected_status for i in interpretations]), "Expected all to be {}".format(expected_status)


class TestInterpretationWorkflow(object):
    """
    Tests the whole workflow of
    interpretations on one analysis.

    - One round -> mark for review
    - One round -> finalize
    - Reopen -> one round -> finalize
    """

    # ------------------------------------------------------------
    # helpers

    @staticmethod
    def build_dummy_annotations(allele_ids):
        custom_annotations = list()  # currently left empty
        annotations = list()
        for id in allele_ids:
            annotations.append({'allele_id': id, "annotation_id": "1"})

        return annotations, custom_annotations

    #  helpers end
    # ------------------------------------------------------------

    @pytest.mark.ai(order=0)
    def test_refresh_db(self, test_database):
        test_database.refresh()

    @pytest.mark.ai(order=1)
    # @pytest.mark.parametrize("workflow_type", [("variant")])
    # @pytest.mark.parametrize("workflow_type", [("analysis")])
    @pytest.mark.parametrize("workflow_type", [("variant"), ("analysis")])
    def test_round_one_review(self, workflow_type):

        users = get_users()
        user = users[USER_ID_OF[workflow_type]["round_1"]]

        # Start interpretation
        interpretation = start_interpretation(workflow_type,
                                              ID_OF[workflow_type],
                                              user,
                                              extra=INTERPRETATION_INIT_DATA[workflow_type])

        alleles = get_alleles(interpretation['allele_ids'])

        # Utilize the interpretation state to store our data between test rounds
        # The format doesn't necessarily reflect how the frontend keep it's state.
        state = {
            'alleleassessments': list(),
            'referenceassessments': list(),
            'allelereports': list()
        }

        # Put assessments and reports in the state:
        for allele in alleles:
            state['alleleassessments'].append(
                allele_assessment_template(workflow_type,
                                           ID_OF[workflow_type],
                                           allele,
                                           user,
                                           extra=ASSESSMENT_EXTRA_DATA[workflow_type])
            )

            annotation_references = allele['annotation']['references']
            ref_ids = [r['pubmed_id'] for r in annotation_references]
            q = {'pubmed_id': ref_ids}
            references = get_entities_by_query('references', q)
            for reference in references:
                state['referenceassessments'].append(
                    reference_assessment_template(workflow_type,
                                                  ID_OF[workflow_type],
                                                  allele,
                                                  reference,
                                                  user,
                                                  extra=REFERENCEASSESSMENT_EXTRA_DATA[workflow_type])
                )

            state['allelereports'].append(
                allele_report_template(workflow_type,
                                       ID_OF[workflow_type],
                                       allele,
                                       user,
                                       extra=ASSESSMENT_EXTRA_DATA[workflow_type])
            )

        interpretation['state'] = state

        save_interpretation_state(workflow_type, interpretation, ID_OF[workflow_type])

        mark_review(workflow_type, ID_OF[workflow_type], review_template())

        reloaded_interpretation = get_interpretation(workflow_type, ID_OF[workflow_type], interpretation['id'])

        assert reloaded_interpretation['status'] == 'Done'
        assert reloaded_interpretation['user']['username'] == user['username']

        # Check that new interpretation was created
        interpretations = get_interpretations(workflow_type, ID_OF[workflow_type])
        assert len(interpretations) == 2

    @pytest.mark.ai(order=2)
    # @pytest.mark.parametrize(["workflow_type",  "number_of_alleles_in_fixture"], [("variant", 1)])
    @pytest.mark.parametrize(["workflow_type",  "number_of_alleles_in_fixture"], [("variant", 1), ("analysis", 6)])
    # @pytest.mark.parametrize(["workflow_type",  "number_of_alleles_in_fixture"], [("analysis", 6)])
    def test_round_two_finalize(self, workflow_type, number_of_alleles_in_fixture):
        # Given
        users = get_users()
        user = users[USER_ID_OF[workflow_type]["round_2"]]

        interpretation = start_interpretation(workflow_type,
                                              ID_OF[workflow_type],
                                              user,
                                              extra=INTERPRETATION_INIT_DATA[workflow_type])

        # We use the state as our source of assessments and reports:
        allele_assessments = interpretation['state']['alleleassessments']
        reference_assessments = interpretation['state']['referenceassessments']
        allele_reports = interpretation['state']['allelereports']

        assert all([item['evaluation']['comment'] == 'Original comment'
                    for item in allele_assessments + reference_assessments + allele_reports])

        # Simulate updating the assessments in the state
        for s in allele_assessments + reference_assessments + allele_reports:
            s['evaluation']['comment'] = 'Updated comment'

        save_interpretation_state(workflow_type, interpretation, ID_OF[workflow_type])

        # When
        # annotations are needed when finalizing:
        annotations, custom_annotations = self.build_dummy_annotations(map(lambda a: a['allele_id'], allele_assessments))
        finalize_response = finalize(workflow_type, ID_OF[workflow_type],
                                     annotations,
                                     custom_annotations,
                                     allele_assessments,
                                     reference_assessments,
                                     allele_reports)

        # Then
        # Interpreations
        interpretations = get_interpretations(workflow_type, ID_OF[workflow_type])
        assert len(interpretations) == 2
        assert_all_interpretations_are_done(interpretations)

        # Asserts on snapshots, assessments and reports:
        snapshots = get_snapshots(workflow_type, ID_OF[workflow_type])
        assert len(snapshots) == len(allele_assessments) * 2  # review + finalize
        assert len(filter(lambda entry: entry['alleleassessment_id'] is None, snapshots)) == number_of_alleles_in_fixture  # no assessment created in review)
        assert len(filter(lambda entry: entry['alleleassessment_id'] is not None, snapshots))  == number_of_alleles_in_fixture# from finalize

        # Check the assessments/reports. We reload them from API to be sure they were stored
        for entity_type in ['alleleassessments', 'referenceassessments', 'allelereports']:
            entities_created = finalize_response[entity_type]
            for entity in entities_created:
                entity_in_db = get_entity_by_id(entity_type, entity['id'])
                if workflow_type == ANALYSIS_WORKFLOW:
                    assert entity_in_db['analysis_id'] == ID_OF[workflow_type]
                else:
                    assert entity_in_db['allele_id'] == ID_OF[workflow_type]

                assert entity_in_db['evaluation']['comment'] == 'Updated comment'

    @pytest.mark.ai(order=3)
    # @pytest.mark.parametrize("workflow_type", [("analysis")])
    @pytest.mark.parametrize("workflow_type", [("variant"), ("analysis")])
    # @pytest.mark.parametrize("workflow_type", [("variant")])
    def test_round_three_reopen_and_finalize(self, workflow_type):

        # Given
        users = get_users()
        user = users[USER_ID_OF[workflow_type]["round_3"]]
        reopen_analysis(workflow_type, ID_OF[workflow_type], user)

        interpretation = start_interpretation(workflow_type,
                                              ID_OF[workflow_type],
                                              user,
                                              extra=INTERPRETATION_INIT_DATA[workflow_type])

        assert interpretation['user']['username'] == user['username']

        # We use the state as our source of assessments and reports:
        allele_assessments = interpretation['state']['alleleassessments']
        reference_assessments = interpretation['state']['referenceassessments']
        allele_reports = interpretation['state']['allelereports']

        assert all([item['evaluation']['comment'] == 'Updated comment' for item in allele_assessments + reference_assessments + allele_reports])

        # Simulate updating the assessments again:
        for item in allele_assessments + reference_assessments + allele_reports:
            item['evaluation']['comment'] = 'Reopened comment'

        save_interpretation_state(workflow_type, interpretation, ID_OF[workflow_type])

        # annotation is required for finalization
        annotations, custom_annotations = self.build_dummy_annotations(map(lambda a: a['allele_id'], allele_assessments))

        # helper
        def _update_entity_with_context(entity, context_key, context_id):
            entity[context_key] = context_id
            entity['reuse'] = True
        # end helper

        if workflow_type == ANALYSIS_WORKFLOW:
            assert len(allele_assessments) == 6
            assert len(allele_reports) == 6
            # for convenience the entities is given themselves as context:
            _update_entity_with_context(allele_assessments[5-1], 'presented_alleleassessment_id', 6)
            _update_entity_with_context(allele_assessments[6-1], 'presented_alleleassessment_id', 7)
            _update_entity_with_context(allele_reports[5-1], 'presented_allelereport_id', 6)
            _update_entity_with_context(allele_reports[6-1], 'presented_allelereport_id', 7)
        else:  # no context set for variant workflow
            pass

        # When
        _ = finalize(workflow_type,
                     ID_OF[workflow_type],
                     annotations,
                     custom_annotations,
                     allele_assessments,
                     reference_assessments,
                     allele_reports)

        # Then
        # Interpretations
        interpretations = get_interpretations(workflow_type, ID_OF[workflow_type])
        assert_all_interpretations_are_done(interpretations)
        assert len(interpretations) == 3

        # Asserts on snapshots, assessments and reports
        snapshots = get_snapshots(workflow_type, ID_OF[workflow_type])
        assert len(snapshots) == len(allele_assessments) * 3  # one review and two finalizations

        if workflow_type == ANALYSIS_WORKFLOW:
            self.asserts_on_snapshots_and_entities_for_analysis_workflow(ID_OF[workflow_type], snapshots, interpretation['allele_ids'])
        else:
            self.asserts_on_snapshots_and_entities_for_variant_workflow(snapshots, interpretation['allele_ids'])

    def asserts_on_snapshots_and_entities_for_analysis_workflow(self, analysis_id, snapshots, allele_ids):
        snapshots_from_last_final = filter(lambda entry: entry['id'] > 12, snapshots)
        assert len(snapshots_from_last_final) == 6

        # asserts on the context of the assessments/reports:
        asserts_and_selections = [
            ("test1", lambda item: item['id'] <= 16, lambda item: item['presented_alleleassessment_id'] is None),
            ("test2", lambda item: item['id'] > 16, lambda item: item['presented_alleleassessment_id'] is not None),
            ("test3", lambda item: item['id'] <= 16, lambda item: item['presented_allelereport_id'] is None),
            ("test4", lambda item: item['id'] > 16, lambda item: item['presented_allelereport_id'] is not None)
        ]
        for name, selection, predicate in asserts_and_selections:
            assert all(map(predicate, filter(selection, snapshots_from_last_final))), "test with name {} not OK".format(name)

        # Asserts on all allele assessments:
        allele_assessments_in_db = get_allele_assessments_by_analysis(analysis_id)
        assert len(allele_assessments_in_db) == 10  # 6 + 4 (first and second finalization)

        for aid in filter(lambda allele_id: allele_id < 5, allele_ids):  # for 4 first alleles
            item_connected_to_allele_has_been_superceeded(aid, allele_assessments_in_db, 'Updated comment')  # one has been superceeded
            item_connected_to_allele_is_current(aid, allele_assessments_in_db, 'Reopened comment')  # and one is current

        for aid in filter(lambda allele_id: allele_id in [5, 6], allele_ids):  # for allele 5 and 6
            item_connected_to_allele_is_current(aid, allele_assessments_in_db, 'Updated comment')  # assessment unchanged since we reused them

        # Asserts on all allele reports:
        allele_reports_in_db = get_allele_reports_by_analysis(analysis_id)
        assert len(allele_reports_in_db) == 6 + 4  # 4 because we reused two reports

        for aid in filter(lambda allele_id: allele_id < 5, allele_ids):  # for 4 first alleles
            item_connected_to_allele_has_been_superceeded(aid, allele_reports_in_db, 'Updated comment')  # one has been superceeded
            item_connected_to_allele_is_current(aid, allele_reports_in_db, 'Reopened comment')  # and one is current
        for aid in filter(lambda allele_id: allele_id in [5, 6], allele_ids):  # for allele 5 and 6
            item_connected_to_allele_is_current(aid, allele_reports_in_db, 'Updated comment')  # reports unchanged since we reused them

        # Asserts on all reference assessments:
        reference_assessments_in_db = get_reference_assessments_by_analysis(analysis_id)
        for aid in allele_ids:
            # If there were no references in the creation step earlier, there will be no referenceassessment
            aid_ra = next((i for i in reference_assessments_in_db if i['allele_id'] == aid), None)
            if aid_ra:
                if aid_ra['date_superceeded'] is not None:
                    assert aid_ra['evaluation']['comment'] == 'Updated comment'
                else:
                    assert aid_ra['evaluation']['comment'] == 'Reopened comment'

    def asserts_on_snapshots_and_entities_for_variant_workflow(self, snapshots, allele_ids):
        snapshots_from_last_finalization = filter(lambda snap: snap['id'] == 3, snapshots)  # 1 and 2 are from previous review/finalization
        assert len(snapshots_from_last_finalization) == 1
        snapshot = snapshots_from_last_finalization[0]
        # asserts on the context of the assessments/reports:
        assert snapshot['presented_alleleassessment_id'] is None
        assert snapshot['presented_allelereport_id'] is None

        # Then
        # Asserts on all allele assessments:
        allele_assessments_in_db = get_entities_by_query("alleleassessments", {'allele_id': allele_ids})
        assert len(allele_assessments_in_db) == 1 + 1  # first and second finalization
        item_connected_to_allele_has_been_superceeded(allele_ids[0], allele_assessments_in_db, 'Updated comment')  # one has been superceeded
        item_connected_to_allele_is_current(allele_ids[0], allele_assessments_in_db, 'Reopened comment')  # and one is current

        # Asserts on all allele reports:
        allele_reports_in_db = get_entities_by_query("allelereports", {'allele_id': allele_ids})
        assert len(allele_reports_in_db) == 1 + 1  # first and second finalization
        item_connected_to_allele_has_been_superceeded(allele_ids[0], allele_reports_in_db, 'Updated comment')  # one has been superceeded
        item_connected_to_allele_is_current(allele_ids[0], allele_reports_in_db, 'Reopened comment')  # and one is current

        # Asserts on all reference assessments:
        reference_assessments_in_db = get_entities_by_query("referenceassessments", {'allele_id': allele_ids})
        for aid in allele_ids:
            # If there were no references in the creation step earlier, there will be no referenceassessment
            aid_ra = next((i for i in reference_assessments_in_db if i['allele_id'] == aid), None)
            if aid_ra:
                if aid_ra['date_superceeded'] is not None:
                    assert aid_ra['evaluation']['comment'] == 'Updated comment'
                else:
                    assert aid_ra['evaluation']['comment'] == 'Reopened comment'
