import copy
import pytest

from api.tests import interpretation_helper as ih


def report_template(allele_id):
    return {
        "allele_id": allele_id,
        "analysis_id": 1,
        "classification": "1",
        "evaluation": {"comment": "Some comment"},
    }


ANALYSIS_ID = 1
FILTERCONFIG_ID = 1


class TestAlleleReports(object):
    @pytest.mark.ar(order=0)
    def test_create_new(self, test_database):
        test_database.refresh()  # Reset db

        # Create one AlleleReport for each allele in the interpretation:
        filtered_alleles = ih.get_filtered_alleles(
            "analysis",
            ANALYSIS_ID,
            ih.get_interpretation_id_of_first("analysis", ANALYSIS_ID),
            FILTERCONFIG_ID,
        ).get_json()
        created_ids = list()
        for idx, allele_id in enumerate(filtered_alleles["allele_ids"]):

            # Prepare
            report_data = copy.deepcopy(report_template(allele_id))

            # POST data
            api_response = ih.create_entities("allelereports", [report_data])

            # Check response
            assert api_response.status_code == 200
            report_data = api_response.get_json()[0]
            assert report_data["allele_id"] == allele_id
            assert report_data["id"] == idx + 1
            created_ids.append(report_data["id"])

        return created_ids

    @pytest.mark.ar(order=1)
    def test_create_new_and_reuse(self, test_database):
        # Create one AlleleReport for each allele in the interpretation:
        filtered_alleles = ih.get_filtered_alleles(
            "analysis",
            ANALYSIS_ID,
            ih.get_interpretation_id_of_first("analysis", ANALYSIS_ID),
            FILTERCONFIG_ID,
        ).get_json()

        q = {"allele_id": filtered_alleles["allele_ids"], "date_superceeded": None}
        previous_reports = ih.get_entities_by_query("allelereports", q).get_json()
        previous_ids = []
        for report_data in previous_reports:
            prev_id = report_data["id"]
            previous_ids.append(prev_id)  # bookkeeping

            report_data["id"] = 1  # The Api should discard this using @request_json
            report_data["reuse"] = True
            report_data["presented_report_id"] = prev_id

            # POST data
            r = ih.create_entities("allelereports", [report_data])

            # Check response
            assert r.status_code == 200
            new_report = r.get_json()[0]
            assert new_report["allele_id"] == report_data["allele_id"]
            assert new_report["id"] != prev_id

        # Reload the previous reports and make sure they're marked as superceded
        previous_reports = ih.get_entities_by_query(
            "allelereports", {"id": previous_ids}
        ).get_json()

        assert all([p["date_superceeded"] is not None for p in previous_reports])

    @pytest.mark.ar(order=2)
    def test_update_reports(self):
        """
        Simulate updating the AlleleReport created in create_new().
        It should result in a new AlleleReport being created,
        while the existing should be superceded.
        """

        filtered_alleles = ih.get_filtered_alleles(
            "analysis",
            ANALYSIS_ID,
            ih.get_interpretation_id_of_first("analysis", ANALYSIS_ID),
            FILTERCONFIG_ID,
        ).get_json()

        q = {"allele_id": filtered_alleles["allele_ids"], "date_superceeded": None}
        previous_reports = ih.get_entities_by_query("allelereports", q).get_json()

        previous_ids = []
        for previous_report in previous_reports:
            # Prepare
            prev_id = previous_report["id"]
            previous_ids.append(prev_id)
            # Delete the id, to make the backend create a new report
            del previous_report["id"]
            previous_report["evaluation"]["comment"] = "Some new comment"

            # POST data
            api_reponse = ih.create_entities("allelereports", [previous_report])

            # Check response
            assert api_reponse.status_code == 200
            allele_report = api_reponse.json[0]
            # Check that the object is new
            assert allele_report["id"] != prev_id
            assert allele_report["evaluation"]["comment"] == "Some new comment"

        # Reload the previous allelereports and make sure
        # they're marked as superceded
        q = {"id": previous_ids}
        previous_reports = ih.get_entities_by_query("allelereports", q).get_json()

        assert all([p["date_superceeded"] is not None for p in previous_reports])

    @pytest.mark.ar(order=3)
    def test_fail_cases(self):
        """
        Test cases where it should fail to create reports.
        """

        # Test without allele_id
        data = copy.deepcopy(report_template(999))
        del data["allele_id"]

        r = ih.create_entities("allelereports", [data])
        assert r.status_code == 500
