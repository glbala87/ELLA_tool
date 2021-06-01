from vardb.datamodel import allele, assessment
from api.v1.resources.workflow.similaralleles import nearby_alleles
from conftest import mock_allele
from api.config import config
from typing import Any, Dict, List


def test_nearbyvariants(session, test_database, client):
    genepanel_name = "HBOC"
    genepanel_version = "v01"

    def _create_allele(start: int, end: int, classification: str = None) -> allele.Allele:
        a: allele.Allele = mock_allele(
            session, {"chromosome": "TEST", "start_position": start, "open_end_position": end + 1}
        )
        if classification is not None:
            aa = assessment.AlleleAssessment(
                user_id=1,
                allele_id=a.id,
                classification=classification,
                evaluation={},
                genepanel_name=genepanel_name,
                genepanel_version=genepanel_version,
            )
            session.add(aa)
        return a

    def _assert_contains_exclusively(a_res: Dict[int, Any], a_exp: Dict[int, List[allele.Allele]]):
        # same length
        assert len(a_res) == len(a_exp)
        # we want an entry for each query id
        assert set(a_res.keys()) == set(a_exp.keys())
        # loop over keys
        for kid in a_res:
            ids_res = list(map(lambda x: x["id"], a_res[kid]))
            ids_exp = list(map(lambda x: x.id, a_exp[kid]))
            assert ids_res == ids_exp

    #       0         1         2         3         4         5         6         7
    #       012345678901234567890123456789012345678901234567890123456789012345678901234567
    # aa    1111    2222  3333
    # aa                  44
    # aq     11  3 5   6 8
    # aq      222  444  7 9  a
    #
    # aa: alleles assessments
    # aq: query alleles

    aa_1 = _create_allele(0, 3, "4")
    aa_2 = _create_allele(8, 11, "3")
    aa_3 = _create_allele(14, 17, "2")
    aa_4 = _create_allele(14, 15, "1")
    aq_1 = _create_allele(1, 2)
    aq_2 = _create_allele(2, 4)
    aq_3 = _create_allele(5, 5)
    aq_4 = _create_allele(7, 9)
    aq_5 = _create_allele(7, 7)
    aq_6 = _create_allele(11, 11)
    aq_7 = _create_allele(12, 12)
    aq_8 = _create_allele(13, 13)
    aq_9 = _create_allele(14, 14)
    aq_a = _create_allele(17, 17)
    session.flush()

    config["similar_alleles"]["max_genomic_distance"] = 0
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_1.id])
    _assert_contains_exclusively(res, {aq_1.id: [aa_1]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_2.id])
    _assert_contains_exclusively(res, {aq_2.id: [aa_1]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_3.id])
    _assert_contains_exclusively(res, {aq_3.id: []})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_4.id])
    _assert_contains_exclusively(res, {aq_4.id: [aa_2]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_5.id])
    _assert_contains_exclusively(res, {aq_5.id: []})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_6.id])
    _assert_contains_exclusively(res, {aq_6.id: [aa_2]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_7.id])
    _assert_contains_exclusively(res, {aq_7.id: []})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_8.id])
    _assert_contains_exclusively(res, {aq_8.id: []})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_9.id])
    _assert_contains_exclusively(res, {aq_9.id: [aa_3, aa_4]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_a.id])
    _assert_contains_exclusively(res, {aq_a.id: [aa_3]})

    config["similar_alleles"]["max_genomic_distance"] = 5
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_1.id])
    _assert_contains_exclusively(res, {aq_1.id: [aa_1]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_2.id])
    _assert_contains_exclusively(res, {aq_2.id: [aa_1, aa_2]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_3.id])
    _assert_contains_exclusively(res, {aq_3.id: [aa_1, aa_2]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_4.id])
    _assert_contains_exclusively(res, {aq_4.id: [aa_1, aa_2, aa_3, aa_4]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_5.id])
    _assert_contains_exclusively(res, {aq_5.id: [aa_1, aa_2]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_6.id])
    _assert_contains_exclusively(res, {aq_6.id: [aa_2, aa_3, aa_4]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_7.id])
    _assert_contains_exclusively(res, {aq_7.id: [aa_2, aa_3, aa_4]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_8.id])
    _assert_contains_exclusively(res, {aq_8.id: [aa_2, aa_3, aa_4]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_9.id])
    _assert_contains_exclusively(res, {aq_9.id: [aa_2, aa_3, aa_4]})
    res = nearby_alleles(session, genepanel_name, genepanel_version, [aq_a.id])
    _assert_contains_exclusively(res, {aq_a.id: [aa_3, aa_4]})


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
    config["similar_alleles"]["max_genomic_distance"] = 100
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
