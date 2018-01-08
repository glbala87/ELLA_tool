import pytest

from api.tests import *
from api.tests.workflow_helper import WorkflowHelper

"""
Test the interpretation workflow of
 - a sample/analysis
 - a single variant

The single variant is chosen not be included in the sample/analysis.
So any assessments done in either sample or variant
workflow won't affect each other.

The tests for variant and sample workflows are similar.
The differences are handled using parametrized tests, some
workflow specific test fixture and branching based on workflow.

"""

ANALYSIS_ID = 2  # analysis_id = 2, allele 1-6
ALLELE_ID = 18  # allele id 18, brca2 c.1275A>G,  GRCh37/13-32906889-32906890-A-G?gp_name=HBOCUTV&gp_version=v01

ANALYSIS_ALLELE_IDS = [1, 3, 4, 7, 12, 13]

ANALYSIS_USERNAMES = ['testuser1', 'testuser2', 'testuser3']  # username for each round
ALLELE_USERNAMES = ['testuser4', 'testuser1', 'testuser2']


@pytest.fixture(scope="module")
def analysis_wh():
    return WorkflowHelper(
        'analysis',
        ANALYSIS_ID,
        genepanel=('HBOC', 'v01')
    )


@pytest.fixture(scope="module")
def allele_wh():
    return WorkflowHelper(
        'allele',
        ALLELE_ID,
        genepanel=('HBOCUTV', 'v01')
    )


class TestAnalysisInterpretationWorkflow(object):
    """
    Tests the whole workflow of
    interpretations on one analysis.

    - One round -> mark for review
    - One round -> finalize
    - Reopen -> one round -> finalize
    """

    @pytest.mark.ai(order=0)
    def test_init_data(self, test_database):
        test_database.refresh()

    @pytest.mark.ai(order=1)
    def test_round_one_review(self, analysis_wh):
        interpretation = analysis_wh.start_interpretation(ANALYSIS_USERNAMES[0])
        analysis_wh.perform_review_round(interpretation)

    @pytest.mark.ai(order=2)
    def test_round_two_finalize(self, analysis_wh):
        interpretation = analysis_wh.start_interpretation(ANALYSIS_USERNAMES[1])
        analysis_wh.perform_finalize_round(interpretation)

    @pytest.mark.ai(order=3)
    def test_round_three_reopen_and_finalize(self, analysis_wh):
        analysis_wh.reopen(ANALYSIS_USERNAMES[2])
        interpretation = analysis_wh.start_interpretation(ANALYSIS_USERNAMES[2])
        analysis_wh.perform_reopened_round(interpretation)


class TestAlleleInterpretationWorkflow(object):
    """
    Tests the whole workflow of
    interpretations on one allele.

    - One round -> mark for review
    - One round -> finalize
    - Reopen -> one round -> finalize
    """

    @pytest.mark.ai(order=0)
    def test_init_data(self, test_database):
        test_database.refresh()

    @pytest.mark.ai(order=1)
    def test_round_one_review(self, allele_wh):
        interpretation = allele_wh.start_interpretation(ALLELE_USERNAMES[0])
        allele_wh.perform_review_round(interpretation)

    @pytest.mark.ai(order=2)
    def test_round_two_finalize(self, allele_wh):
        interpretation = allele_wh.start_interpretation(ALLELE_USERNAMES[1])
        allele_wh.perform_finalize_round(interpretation)

    @pytest.mark.ai(order=3)
    def test_round_three_reopen_and_finalize(self, allele_wh):
        allele_wh.reopen(ALLELE_USERNAMES[2])
        interpretation = allele_wh.start_interpretation(ALLELE_USERNAMES[2])
        allele_wh.perform_reopened_round(interpretation)
