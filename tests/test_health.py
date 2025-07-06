from fastapi import status

async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"

async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "Welcome" in response.json()["message"]
