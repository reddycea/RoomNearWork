def test_recommendations(client):
    response = client.get("/api/recommendations?workplace=Empangeni&max_price=5000")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data
    assert "score" in data[0]
    assert "reasons" in data[0]
