import pytest
import json
from .util import FlaskClientProxy


@pytest.fixture
def annotation_template():
    return {"allele_id": 1, "annotations": {"test": 1}, "user_id": 1}


@pytest.fixture
def client():
    return FlaskClientProxy()


class TestCustomAnnotation(object):
    @pytest.mark.ca(order=0)
    def test_create_new(self, test_database, annotation_template, client):
        test_database.refresh()  # Reset db

        # Insert new CustomAnnotation
        insert_response = client.post("/api/v1/customannotations/", annotation_template)
        id_of_first_created = insert_response.json["id"]

        # Check that it's inserted
        insert_response = client.get(
            "/api/v1/customannotations/?q={}".format(json.dumps({"id": [id_of_first_created]}))
        ).json
        assert insert_response[0]["annotations"] == annotation_template["annotations"]
        assert insert_response[0]["date_created"]

        # Create a new one by updating an existing
        annotation_template["annotations"] = {"test": 2}
        update_response = client.post("/api/v1/customannotations/", annotation_template)
        id_of_created_by_update = update_response.json["id"]

        # Check that the new annotation exists:
        second_response = client.get(
            "/api/v1/customannotations/?q={}".format(json.dumps({"id": [id_of_created_by_update]}))
        ).json
        assert second_response[0]["annotations"] == annotation_template["annotations"]

        # Check that the "original" has been superceeded:
        first_response = client.get(
            "/api/v1/customannotations/?q={}".format(json.dumps({"id": [id_of_first_created]}))
        ).json
        assert first_response[0]["date_superceeded"]
        assert first_response[0]["annotations"]["test"] == 1
        assert first_response[0]["id"] != id_of_created_by_update
