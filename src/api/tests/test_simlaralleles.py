from vardb.datamodel import assessment


def test_similaralleles(session, test_database, client):
    test_database.refresh()

    genepanel_name = "HBOC"
    genepanel_version = "v01"

    for aid in [1, 2]:
        aa = assessment.AlleleAssessment(
            user_id=1,
            allele_id=aid,
            classification="1",
            evaluation={},
            genepanel_name=genepanel_name,
            genepanel_version=genepanel_version,
        )
        session.add(aa)
    session.commit()

    query_ids = ["1", "2", "3", "4", "5", "6"]
    response = client.get(
        "/api/v1/workflows/similar_alleles/{}/{}/?allele_ids={}".format(
            genepanel_name, genepanel_version, ",".join(query_ids)
        )
    )
    assert response.status_code == 200
    similar_alleles = response.get_json()
    # we want an entry for each query id
    assert set(similar_alleles.keys()) == set(query_ids)
    # we want both in the same order
    assert list(similar_alleles.keys()) == query_ids
    # no identical alleles
    for qid in query_ids:
        sim_ids = list(map(lambda x: x["id"], similar_alleles[qid]))
        assert qid not in sim_ids
    # specific checks
    assert list(map(lambda x: x["id"], similar_alleles["1"])) == [2]
    assert list(map(lambda x: x["id"], similar_alleles["2"])) == [1]
    assert list(map(lambda x: x["id"], similar_alleles["3"])) == [1, 2]
    assert list(map(lambda x: x["id"], similar_alleles["4"])) == [1, 2]
    assert list(map(lambda x: x["id"], similar_alleles["5"])) == [1, 2]
    assert list(map(lambda x: x["id"], similar_alleles["6"])) == []
