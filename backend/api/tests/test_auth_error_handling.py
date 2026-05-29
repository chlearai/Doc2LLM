import httpx
from fastapi.testclient import TestClient

from app.dependencies import get_conversion_manager
from app.main import app


class BrokenProfileRepository:
    def get_user(self, user_id: str):
        request = httpx.Request("GET", "https://example.supabase.co/rest/v1/profiles")
        response = httpx.Response(500, request=request, text="profile lookup failed")
        raise httpx.HTTPStatusError("profile lookup failed", request=request, response=response)


class BrokenProfileManager:
    repository = BrokenProfileRepository()


def test_auth_profile_backend_errors_return_cors_json(monkeypatch):
    app.dependency_overrides[get_conversion_manager] = lambda: BrokenProfileManager()
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")

    class FakeAuthResponse:
        status_code = 200

        def json(self):
            return {
                "id": "33333333-3333-4333-8333-333333333333",
                "email": "user@example.com",
                "user_metadata": {"full_name": "Jane Doe"},
            }

    monkeypatch.setattr("app.auth.httpx.get", lambda *args, **kwargs: FakeAuthResponse())

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer real-access-token",
            "Origin": "http://localhost:3000",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.json()["detail"]["code"] == "PROFILE_UNAVAILABLE"
