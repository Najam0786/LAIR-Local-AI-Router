def test_models_endpoint_lists_registered_models(client, registered_fake_provider):
    response = client.get("/models")

    assert response.status_code == 200

    ids = {model["id"] for model in response.json()}

    assert "qwen2.5-coder-32b" in ids
    assert "qwen2.5-vl-7b" in ids


def test_models_endpoint_empty_when_no_providers(client, clean_registry):
    response = client.get("/models")

    assert response.status_code == 200
    assert response.json() == []
