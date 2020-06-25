def check_geneassessment(result, payload, previous_assessment_id=None):
    assert result["gene_id"] == payload["gene_id"]
    assert result["evaluation"] == payload["evaluation"]
    assert result["analysis_id"] == payload.get("analysis_id")
    assert result["genepanel_name"] == payload["genepanel_name"]
    assert result["genepanel_version"] == payload["genepanel_version"]
    assert result["date_superceeded"] is None
    assert result["user_id"] == 1
    assert result["usergroup_id"] == 1
    assert result["previous_assessment_id"] == previous_assessment_id


def test_create_assessment(session, client, test_database):

    test_database.refresh()

    # Insert new geneassessment with analysis_id
    ASSESSMENT1 = {
        "gene_id": 1101,
        "evaluation": {"comment": "TEST1"},
        "analysis_id": 1,
        "genepanel_name": "Mendel",
        "genepanel_version": "v04",
    }

    r = client.post("/api/v1/geneassessments/", ASSESSMENT1)
    assert r.status_code == 200
    ga1 = r.get_json()
    check_geneassessment(ga1, ASSESSMENT1)

    # Check latest result when loading genepanel (allele_id 1 is in BRCA2)
    r = client.get("/api/v1/workflows/analyses/1/genepanels/HBOC/v01/?allele_ids=1")
    gp = r.get_json()
    assert len(gp["geneassessments"]) == 1
    check_geneassessment(gp["geneassessments"][0], ASSESSMENT1)

    # Insert new geneassessment, without analysis_id
    ASSESSMENT2 = {
        "gene_id": 1101,
        "evaluation": {"comment": "TEST2"},
        "genepanel_name": "Mendel",
        "genepanel_version": "v04",
        "presented_geneassessment_id": ga1["id"],
    }

    r = client.post("/api/v1/geneassessments/", ASSESSMENT2)
    assert r.status_code == 200
    ga2 = r.get_json()
    check_geneassessment(ga2, ASSESSMENT2, previous_assessment_id=ga1["id"])

    r = client.get("/api/v1/workflows/analyses/1/genepanels/HBOC/v01/?allele_ids=1")
    gp = r.get_json()
    assert len(gp["geneassessments"]) == 1
    check_geneassessment(gp["geneassessments"][0], ASSESSMENT2, previous_assessment_id=ga1["id"])

    # Insert new geneassessment, with wrong presented id (should fail)
    ASSESSMENT3 = {
        "gene_id": 1101,
        "evaluation": {"comment": "TEST3"},
        "genepanel_name": "Mendel",
        "genepanel_version": "v04",
        "presented_geneassessment_id": ga1["id"],
    }

    r = client.post("/api/v1/geneassessments/", ASSESSMENT3)
    assert r.status_code == 500
    ga2 = (
        r.get_json()["message"]
        == "'presented_geneassessment_id': 1 does not match latest existing geneassessment id: 2"
    )

    # Check that latest is same as before
    r = client.get("/api/v1/workflows/analyses/1/genepanels/HBOC/v01/?allele_ids=1")
    gp = r.get_json()
    assert len(gp["geneassessments"]) == 1
    check_geneassessment(gp["geneassessments"][0], ASSESSMENT2, previous_assessment_id=ga1["id"])
