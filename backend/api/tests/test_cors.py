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


def test_cors_allows_live_vercel_frontend_origin():
    client = TestClient(app)

    response = client.options(
        "/auth/me",
        headers={
            "Origin": "https://markitdoc.vercel.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://markitdoc.vercel.app"
