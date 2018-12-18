def test_config(client):
    r = client.get("/api/v1/config/")
    assert r.status_code == 200
    response_keys = list(r.json.keys())
    for k in ["frequencies", "acmg"]:
        assert k in response_keys
