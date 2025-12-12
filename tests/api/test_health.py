"""Test health check endpoint."""

from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient) -> None:
    """Test GET /api/v1/health returns 200 with correct structure."""
    response = client.get('/api/v1/health')

    assert response.status_code == 200
    data = response.json()
    assert 'status' in data
    assert 'timestamp' in data
    assert 'version' in data
    assert data['status'] == 'ok'
