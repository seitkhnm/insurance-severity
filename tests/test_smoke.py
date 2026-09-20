def test_predict_smoke(client, good_row):
    r = client.post("/v1/predict", json=good_row)

    assert r.status_code == 200

    body = r.json()

    assert body["severity"] >= 0
    assert body["latency_ms"] >= 0
    assert body["model_version"]
    assert body["request_id"]


def test_predict_handles_missing_values(client, good_row):
    r = client.post(
        "/v1/predict",
        json={**good_row, "sum_insured": None},
    )
    assert r.status_code == 200


def test_repeated_predictions_agree(client, good_row):
    s1 = client.post(
        "/v1/predict",
        json=good_row
    ).json()["severity"]

    s2 = client.post(
        "/v1/predict",
        json=good_row
    ).json()["severity"]

    assert abs(s1 - s2) < 1e-12