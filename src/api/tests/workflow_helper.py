from api.tests import interpretation_helper as ih


"""
Performs various interpretation rounds for analyses and alleles.
"""


def _assert_all_interpretations_are_done(interpretations):
    expected_status = "Done"
    assert all([i['status'] == expected_status for i in interpretations]), "Expected all to be {}".format(expected_status)


def _item_connected_to_allele_is_current(allele_id, items_source, expected_comment):
    items = filter(lambda item: item['allele_id'] == allele_id, items_source)
    assert any(map(lambda a: a['date_superceeded'] is None and a['evaluation']['comment'] == expected_comment, items)),\
        "No assessment/report for allele {} that's current has comment '{}'".format(allele_id, expected_comment)


def _item_connected_to_allele_has_been_superceeded(allele_id, items_source, expected_comment):
    selected_items = filter(lambda item: item['allele_id'] == allele_id, items_source)
    assert any(map(lambda a: a['date_superceeded'] is not None and a['evaluation']['comment'] == expected_comment, selected_items)),\
               "no assessment/report for allele {} that has been superceeded has the comment '{}' ".format(allele_id, expected_comment)


def _build_dummy_annotations(allele_ids):
    custom_annotations = list()  # currently left empty
    annotations = list()
    for id in allele_ids:
        annotations.append({'allele_id': id, "annotation_id": "1"})

    return annotations, custom_annotations


class WorkflowHelper(object):

    def __init__(self, workflow_type, workflow_id, genepanel=None):

        if workflow_type == 'analysis' and not genepanel:
            raise RuntimeError("Missing required genepanel tuple when workflow_type == 'analysis'")

        self.type = workflow_type
        self.id = workflow_id
        self.interpretation_extras = {'gp_name': genepanel[0], 'gp_version': genepanel[1]} if genepanel else dict()
        self.assessment_extras = {'genepanel_name': genepanel[0], 'genepanel_version': genepanel[1]} if genepanel else dict()

    def reopen(self, username):
        ih.reopen_analysis(self.type, self.id, username)

    def start_interpretation(self, username):
        return ih.start_interpretation(
            self.type,
            self.id,
            username,
            extra=self.interpretation_extras
        )

    def perform_review_round(self, interpretation):
        """
        :param interpretation: interpretation object from start_interpretation()
        """

        # Utilize the interpretation state to store our data between test rounds
        # The format doesn't necessarily reflect how the frontend keep it's state.
        interpretation['state'].update({
            'alleleassessments': list(),
            'referenceassessments': list(),
            'allelereports': list()
        })

        alleles = ih.get_alleles(
            self.type,
            self.id,
            interpretation['id'],
            interpretation['allele_ids']
        )

        # Put assessments and reports in the state:
        for allele in alleles:
            interpretation['state']['alleleassessments'].append(
                ih.allele_assessment_template(
                    self.type,
                    self.id,
                    allele,
                    extra=self.assessment_extras
                )
            )

            annotation_references = allele['annotation']['references']
            ref_ids = [r['pubmed_id'] for r in annotation_references]
            q = {'pubmed_id': ref_ids}
            references = ih.get_entities_by_query('references', q)
            for reference in references:
                interpretation['state']['referenceassessments'].append(
                    ih.reference_assessment_template(
                        self.type,
                        self.id,
                        allele,
                        reference,
                        extra=self.assessment_extras
                    )
                )

            interpretation['state']['allelereports'].append(
                ih.allele_report_template(
                    self.type,
                    self.id,
                    allele,
                    extra=self.assessment_extras
                )
            )

        ih.save_interpretation_state(
            self.type,
            interpretation,
            self.id,
            interpretation['user']['username']
        )

        # Check that new interpretation was created due to marking as review
        interpretation_cnt = len(ih.get_interpretations(self.type, self.id))

        ih.save_interpretation_state(self.type, interpretation, self.id, interpretation['user']['username'])
        ih.mark_review(
            self.type,
            self.id,
            ih.review_template(),
            interpretation['user']['username']
        )

        assert len(ih.get_interpretations(self.type, self.id)) == interpretation_cnt + 1

        # Check that data was updated like it should
        reloaded_interpretation = ih.get_interpretation(
            self.type,
            self.id,
            interpretation['id']
        )

        assert reloaded_interpretation['end_action'] == 'Mark review'
        assert reloaded_interpretation['status'] == 'Done'
        assert reloaded_interpretation['user']['username'] == interpretation['user']['username']

        self.check_interpretation(reloaded_interpretation)

    def perform_finalize_round(self, interpretation):

        # Reference new state in our round data
        interpretation['state'] = interpretation['state']

        # We use the state as our source of assessments and reports:
        allele_assessments = interpretation['state']['alleleassessments']
        reference_assessments = interpretation['state']['referenceassessments']
        allele_reports = interpretation['state']['allelereports']
        attachments = []

        assert all([item['evaluation']['comment'] == 'Original comment'
                    for item in allele_assessments + reference_assessments + allele_reports])

        # Simulate updating the assessments in the state
        for s in allele_assessments + reference_assessments + allele_reports:
            s['evaluation']['comment'] = 'Updated comment'

        ih.save_interpretation_state(
            self.type,
            interpretation,
            self.id,
            interpretation['user']['username']
        )

        # check that no new interpretation is created
        interpretation_cnt = len(ih.get_interpretations(self.type, self.id))

        # annotations are needed when finalizing since it tracks their ids
        annotations, custom_annotations = _build_dummy_annotations(map(lambda a: a['allele_id'], allele_assessments))

        ih.save_interpretation_state(self.type, interpretation, self.id, interpretation['user']['username'])
        finalize_response = ih.finalize(
            self.type,
            self.id,
            annotations,
            custom_annotations,
            allele_assessments,
            reference_assessments,
            allele_reports,
            attachments,
            interpretation['user']['username']
        )

        # Check that assessments/reports are created/exists. We reload them from API to be sure they were stored
        for entity_type in ['alleleassessments', 'referenceassessments', 'allelereports']:
            entities_created = finalize_response[entity_type]
            for entity in entities_created:
                entity_in_db = ih.get_entity_by_id(entity_type, entity['id'])
                if self.type == 'analysis':
                    assert entity_in_db['analysis_id'] == self.id
                else:
                    assert entity_in_db['allele_id'] == self.id

                assert entity_in_db['evaluation']['comment'] == 'Updated comment'

        interpretations = ih.get_interpretations(self.type, self.id)
        assert len(interpretations) == interpretation_cnt
        _assert_all_interpretations_are_done(interpretations)

        # Check that data was updated like it should
        reloaded_interpretation = ih.get_interpretation(
            self.type,
            self.id,
            interpretation['id']
        )

        assert reloaded_interpretation['end_action'] == 'Finalize'
        assert reloaded_interpretation['status'] == 'Done'
        assert reloaded_interpretation['user']['username'] == interpretation['user']['username']

        self.check_interpretation(reloaded_interpretation)

    def perform_reopened_round(self, interpretation):

        # We use the state as our source of assessments and reports:
        allele_assessments = interpretation['state']['alleleassessments']
        reference_assessments = interpretation['state']['referenceassessments']
        allele_reports = interpretation['state']['allelereports']
        attachments = []

        assert all([item['evaluation']['comment'] == 'Updated comment' for item in allele_assessments + reference_assessments + allele_reports])

        # Simulate updating the assessments again:
        for item in allele_assessments + reference_assessments + allele_reports:
            item['evaluation']['comment'] = 'Reopened comment'

        # annotation is required for finalization
        annotations, custom_annotations = _build_dummy_annotations(map(lambda a: a['allele_id'], allele_assessments))

        number_of_alleles = len(interpretation['allele_ids'])
        assert len(allele_assessments) == number_of_alleles
        assert len(allele_reports) == number_of_alleles

        alleles = ih.get_alleles(
            self.type,
            self.id,
            interpretation['id'],
            interpretation['allele_ids']
        )

        # Reuse existing assessments
        for allele in alleles:
            if 'allele_assessment' in allele:
                allele_assessment_for_allele = next(a for a in allele_assessments if a['allele_id'] == allele['id'])
                allele_assessment_for_allele['presented_alleleassessment_id'] = allele['allele_assessment']['id']
                allele_assessment_for_allele['reuse'] = True
            if 'allele_report' in allele:
                allele_report_for_allele = next(a for a in allele_reports if a['allele_id'] == allele['id'])
                allele_report_for_allele['presented_allelereport_id'] = allele['allele_report']['id']
                allele_report_for_allele['reuse'] = True

        # Finalize
        ih.save_interpretation_state(self.type, interpretation, self.id, interpretation['user']['username'])
        ih.finalize(
            self.type,
            self.id,
            annotations,
            custom_annotations,
            allele_assessments,
            reference_assessments,
            allele_reports,
            attachments,
            interpretation['user']['username']
        )

        interpretations = ih.get_interpretations(self.type, self.id)
        _assert_all_interpretations_are_done(interpretations)

        # Check that data was updated like it should
        reloaded_interpretation = ih.get_interpretation(
            self.type,
            self.id,
            interpretation['id']
        )

        assert reloaded_interpretation['end_action'] == 'Finalize'
        assert reloaded_interpretation['status'] == 'Done'
        assert reloaded_interpretation['user']['username'] == interpretation['user']['username']

        self.check_interpretation(reloaded_interpretation)

    def check_interpretation(self, interpretation):

        # Check snapshot data
        snapshots = ih.get_snapshots(self.type, self.id)
        key = '{}interpretation_id'.format(self.type)
        snapshots = [s for s in snapshots if s[key] == interpretation['id']]
        for alleleassessment in interpretation['state']['alleleassessments']:
            snapshot = next(s for s in snapshots if s['allele_id'] == alleleassessment['allele_id'])
            if 'presented_alleleassessment_id' in alleleassessment:
                assert snapshot['presented_alleleassessment_id'] == alleleassessment['presented_alleleassessment_id']
            else:
                assert snapshot['presented_alleleassessment_id'] is None

        for allelereport in interpretation['state']['allelereports']:
            snapshot = next(s for s in snapshots if s['allele_id'] == allelereport['allele_id'])
            if 'presented_allelereport_id' in allelereport:
                assert snapshot['presented_allelereport_id'] == allelereport['presented_allelereport_id']
            else:
                assert snapshot['presented_allelereport_id'] is None

        if interpretation['end_action'] == 'Finalize':

            for allele_id in interpretation['allele_ids']:

                # Check alleleassessments in database
                state_alleleassessment = next(a for a in interpretation['state']['alleleassessments'] if a['allele_id'] == allele_id)
                if not state_alleleassessment.get('reuse'):
                    allele_assessments_in_db = ih.get_allele_assessments_by_allele(allele_id)
                    assert allele_assessments_in_db
                    latest_allele_assessment = next(a for a in allele_assessments_in_db if not a['date_superceeded'])
                    assert latest_allele_assessment['classification'] == state_alleleassessment['classification']
                    assert latest_allele_assessment['evaluation']['comment'] == state_alleleassessment['evaluation']['comment']

                # Check allelereports in database
                state_allelereport = next(a for a in interpretation['state']['allelereports'] if a['allele_id'] == allele_id)
                if not state_allelereport.get('reuse'):
                    allele_reports_in_db = ih.get_allele_reports_by_allele(allele_id)
                    assert allele_reports_in_db
                    latest_allele_report = next(a for a in allele_reports_in_db if not a['date_superceeded'])
                    assert latest_allele_report['evaluation']['comment'] == state_allelereport['evaluation']['comment']

                # Check on reference assessments:
                state_referenceassessments = [a for a in interpretation['state']['referenceassessments'] if a['allele_id'] == allele_id]
                if state_referenceassessments:
                    reference_assessments_in_db = ih.get_reference_assessments_by_allele(allele_id)
                    for state_referenceassessment in state_referenceassessments:
                        matching_reference_assessment = next((
                            ra for ra in reference_assessments_in_db if ra['allele_id'] == allele_id and
                            ra['reference_id'] == state_referenceassessment['reference_id'] and
                            ra['date_superceeded'] is None
                        ))
                        assert matching_reference_assessment['evaluation']['comment'] == state_referenceassessment['evaluation']['comment']
