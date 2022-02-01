import pytest
from api.tests.workflow_helper import WorkflowHelper

FILTERCONFIG_ID = 1


class TestAnalysisOverview(object):
    @pytest.mark.overviewanalysis(order=0)
    def test_prepare_data(self, test_database, session):
        test_database.refresh()  # Reset db

    @pytest.mark.overviewanalysis(order=1)
    def test_initial_state(self, client):

        r = client.get("/api/v1/overviews/analyses/")
        assert len(r.get_json()["not_started"]) == 4
        assert len(r.get_json()["marked_review"]) == 0
        assert len(r.get_json()["marked_medicalreview"]) == 0
        assert len(r.get_json()["ongoing"]) == 0

        # Finalized
        r = client.get("/api/v1/overviews/analyses/finalized/")
        assert isinstance(r.get_json(), list) and len(r.get_json()) == 0

    @pytest.mark.overviewanalysis(order=2)
    def test_changes(self, client, session):

        FIRST_ANALYSIS_ID = 1
        wh = WorkflowHelper(
            "analysis", FIRST_ANALYSIS_ID, "HBOCUTV", "v01.0", filterconfig_id=FILTERCONFIG_ID
        )

        ##
        # Ongoing
        ##

        interpretation = wh.start_interpretation("testuser1")

        r = client.get("/api/v1/overviews/analyses/")

        assert len(r.get_json()["not_started"]) == 3
        assert len(r.get_json()["marked_review"]) == 0
        assert len(r.get_json()["marked_medicalreview"]) == 0
        assert len(r.get_json()["ongoing"]) == 1
        assert len(r.get_json()["not_ready"]) == 0

        assert r.get_json()["ongoing"][0]["id"] == FIRST_ANALYSIS_ID
        assert len(r.get_json()["ongoing"][0]["interpretations"]) == 1

        ##
        # Interpretation -> Interpretation
        ##

        wh.perform_round(
            interpretation, "Interpretation comment", new_workflow_status="Interpretation"
        )

        r = client.get("/api/v1/overviews/analyses/")

        assert len(r.get_json()["not_started"]) == 4
        assert len(r.get_json()["not_ready"]) == 0
        assert len(r.get_json()["marked_review"]) == 0
        assert len(r.get_json()["marked_medicalreview"]) == 0
        assert len(r.get_json()["ongoing"]) == 0

        ##
        # Interpretation -> Not ready
        ##

        interpretation = wh.start_interpretation("testuser1")
        wh.perform_round(interpretation, "Not ready comment", new_workflow_status="Not ready")

        r = client.get("/api/v1/overviews/analyses/")

        assert len(r.get_json()["not_started"]) == 3
        assert len(r.get_json()["not_ready"]) == 1
        assert len(r.get_json()["marked_review"]) == 0
        assert len(r.get_json()["marked_medicalreview"]) == 0
        assert len(r.get_json()["ongoing"]) == 0

        ##
        # Not ready -> Review
        ##

        interpretation = wh.start_interpretation("testuser1")
        wh.perform_round(interpretation, "Review comment", new_workflow_status="Review")

        r = client.get("/api/v1/overviews/analyses/")

        assert len(r.get_json()["not_started"]) == 3
        assert len(r.get_json()["not_ready"]) == 0
        assert len(r.get_json()["marked_review"]) == 1
        assert len(r.get_json()["marked_medicalreview"]) == 0
        assert len(r.get_json()["ongoing"]) == 0

        ##
        # Review -> Interpretation
        ##

        interpretation = wh.start_interpretation("testuser1")
        wh.perform_round(
            interpretation, "Interpretation comment", new_workflow_status="Interpretation"
        )

        r = client.get("/api/v1/overviews/analyses/")

        assert len(r.get_json()["not_started"]) == 4
        assert len(r.get_json()["marked_review"]) == 0
        assert len(r.get_json()["marked_medicalreview"]) == 0
        assert len(r.get_json()["ongoing"]) == 0
        assert len(r.get_json()["not_ready"]) == 0

        ##
        # Interpretation -> Medical review
        ##

        interpretation = wh.start_interpretation("testuser1")
        wh.perform_round(
            interpretation, "Medical review comment", new_workflow_status="Medical review"
        )

        r = client.get("/api/v1/overviews/analyses/")

        assert len(r.get_json()["not_started"]) == 3
        assert len(r.get_json()["marked_review"]) == 0
        assert len(r.get_json()["marked_medicalreview"]) == 1
        assert len(r.get_json()["ongoing"]) == 0
        assert len(r.get_json()["not_ready"]) == 0

        ##
        # Finalize
        ##

        interpretation = wh.start_interpretation("testuser2")
        wh.perform_finalize_round(interpretation, "Finalize comment")

        r = client.get("/api/v1/overviews/analyses/finalized/")
        assert isinstance(r.get_json(), list) and len(r.get_json()) == 1
        assert r.get_json()[0]["id"] == FIRST_ANALYSIS_ID
        interpretations = r.get_json()[0]["interpretations"]
        assert len(interpretations) == 6
        assert interpretations[0]["date_last_update"] < interpretations[1]["date_last_update"]
        r = client.get("/api/v1/overviews/analyses/")

        assert len(r.get_json()["not_started"]) == 3
        assert len(r.get_json()["marked_review"]) == 0
        assert len(r.get_json()["marked_medicalreview"]) == 0
        assert len(r.get_json()["ongoing"]) == 0
        assert len(r.get_json()["not_ready"]) == 0


class TestAlleleOverview(object):
    @pytest.mark.overviewallele(order=0)
    def test_initial(self, test_database, client, session):
        """
        Do some initial checks.
        """
        test_database.refresh()

        r = client.get("/api/v1/overviews/alleles/")
        print(r.get_json())

        assert len(r.get_json()["ongoing"]) == 0
        assert len(r.get_json()["not_started"]) == 6
        assert len(r.get_json()["marked_review"]) == 0

        # Finalized
        r = client.get("/api/v1/overviews/alleles/finalized/")
        assert isinstance(r.get_json(), list) and len(r.get_json()) == 0

    @pytest.mark.overviewallele(order=1)
    def test_changes(self, test_database, client, session):

        # Allele id 4 has existing alleleinterpretation from testdata
        ALLELE_ID = 4
        wh = WorkflowHelper("allele", ALLELE_ID, "HBOC", "v01.0")

        ##
        # Ongoing
        ##

        interpretation = wh.start_interpretation("testuser1")

        r = client.get("/api/v1/overviews/alleles/")

        assert len(r.get_json()["not_started"]) == 5
        assert len(r.get_json()["marked_review"]) == 0
        assert len(r.get_json()["ongoing"]) == 1

        assert r.get_json()["ongoing"][0]["allele"]["id"] == ALLELE_ID
        assert len(r.get_json()["ongoing"][0]["interpretations"]) == 1

        r = client.get("/api/v1/overviews/alleles/finalized/")
        assert len(r.get_json()) == 0

        ##
        # Ongoing -> Interpretation
        ##

        wh.perform_round(
            interpretation, "Interpretation comment", new_workflow_status="Interpretation"
        )

        r = client.get("/api/v1/overviews/alleles/")

        assert len(r.get_json()["not_started"]) == 6
        assert len(r.get_json()["marked_review"]) == 0
        assert len(r.get_json()["ongoing"]) == 0

        r = client.get("/api/v1/overviews/alleles/finalized/")
        assert len(r.get_json()) == 0

        ##
        # Interpretation -> Review
        ##

        interpretation = wh.start_interpretation("testuser1")
        wh.perform_round(interpretation, "Review comment", new_workflow_status="Review")

        r = client.get("/api/v1/overviews/alleles/")

        assert len(r.get_json()["not_started"]) == 5
        assert len(r.get_json()["marked_review"]) == 1
        assert len(r.get_json()["ongoing"]) == 0

        r = client.get("/api/v1/overviews/alleles/finalized/")
        assert len(r.get_json()) == 0

        ##
        # Review -> Finalize
        ##

        interpretation = wh.start_interpretation("testuser1")
        wh.perform_finalize_round(interpretation, "Finalize comment")

        r = client.get("/api/v1/overviews/alleles/")

        assert len(r.get_json()["not_started"]) == 5
        assert len(r.get_json()["marked_review"]) == 0
        assert len(r.get_json()["ongoing"]) == 0

        r = client.get("/api/v1/overviews/alleles/finalized/")
        assert len(r.get_json()) == 1

        ##
        # Reopen (-> Review)
        ##

        wh.reopen("testuser1")

        r = client.get("/api/v1/overviews/alleles/")

        assert len(r.get_json()["not_started"]) == 5
        assert len(r.get_json()["marked_review"]) == 1
        assert len(r.get_json()["ongoing"]) == 0

        r = client.get("/api/v1/overviews/alleles/finalized/")
        assert len(r.get_json()) == 0

        ##
        # Review -> Finalize
        ##

        interpretation = wh.start_interpretation("testuser1")
        wh.perform_finalize_round(interpretation, "Finalize comment")

        r = client.get("/api/v1/overviews/alleles/")

        assert len(r.get_json()["not_started"]) == 5
        assert len(r.get_json()["marked_review"]) == 0
        assert len(r.get_json()["ongoing"]) == 0

        r = client.get("/api/v1/overviews/alleles/finalized/")
        assert len(r.get_json()) == 1
