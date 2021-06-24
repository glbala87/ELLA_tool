from vardb.datamodel import allele, assessment
from api.v1.resources.workflow.similaralleles import get_nearby_allele_ids
from conftest import mock_allele
from api.config import config
from typing import List


def test_nearbyalleles(session, test_database, client):
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

    def _test_nearby(input: allele.Allele, expected_output: List[allele.Allele]):
        res = get_nearby_allele_ids(session, [input.id])
        assert set(res[input.id]) == set(map(lambda x: x.id, expected_output))

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
    _test_nearby(aq_1, [aa_1])
    _test_nearby(aq_2, [aa_1])
    _test_nearby(aq_3, [])
    _test_nearby(aq_4, [aa_2])
    _test_nearby(aq_5, [])
    _test_nearby(aq_6, [aa_2])
    _test_nearby(aq_7, [])
    _test_nearby(aq_8, [])
    _test_nearby(aq_9, [aa_3, aa_4])
    _test_nearby(aq_a, [aa_3])

    config["similar_alleles"]["max_genomic_distance"] = 5
    _test_nearby(aq_1, [aa_1])
    _test_nearby(aq_2, [aa_1, aa_2])
    _test_nearby(aq_3, [aa_1, aa_2])
    _test_nearby(aq_4, [aa_1, aa_2, aa_3, aa_4])
    _test_nearby(aq_5, [aa_1, aa_2])
    _test_nearby(aq_6, [aa_2, aa_3, aa_4])
    _test_nearby(aq_7, [aa_2, aa_3, aa_4])
    _test_nearby(aq_8, [aa_2, aa_3, aa_4])
    _test_nearby(aq_9, [aa_2, aa_3, aa_4])
    _test_nearby(aq_a, [aa_3, aa_4])


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
