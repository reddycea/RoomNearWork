def test_properties_api_returns_seeded_properties(client):
    response = client.get("/api/properties?city=Empangeni")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]
    assert payload["data"][0]["city"] == "Empangeni"


def test_token_login(client):
    response = client.post("/auth/api/token", json={"email": "tenant@rnw.local", "password": "TenantPass123!"})
    assert response.status_code == 200
    assert "access_token" in response.get_json()
