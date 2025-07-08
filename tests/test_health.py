from fastapi import status


async def test_health_check(test_client):
    """Тест проверки здоровья API."""
    response = await test_client.get("/health")
    data = response.json()
    print(data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"


async def test_root_endpoint(test_client):
    """Тест корневого endpoint."""
    response = await test_client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "Welcome" in response.json()["message"]
