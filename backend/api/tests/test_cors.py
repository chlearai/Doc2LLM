from fastapi.testclient import TestClient

from app.main import app


def test_cors_allows_local_frontend_origin():
    client = TestClient(app)

    response = client.options(
        "/conversions",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3001"
