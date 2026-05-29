from fastapi.testclient import TestClient

from app.main import app


def test_signup_passes_frontend_origin_as_supabase_redirect(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")

    captured: dict[str, object] = {}

    class FakeSignupResponse:
        status_code = 200

        def json(self):
            return {"id": "33333333-3333-4333-8333-333333333333"}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, headers=None, json=None, params=None, timeout=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            captured["params"] = params
            return FakeSignupResponse()

    monkeypatch.setattr("app.main.httpx.AsyncClient", FakeAsyncClient)

    client = TestClient(app)
    response = client.post(
        "/auth/signup",
        headers={"Origin": "https://markitdoc.vercel.app"},
        json={
            "email": "new-user@example.com",
            "password": "StrongPass123",
            "full_name": "New User",
        },
    )

    assert response.status_code == 200
    assert captured["url"] == "https://example.supabase.co/auth/v1/signup"
    assert captured["params"] == {"redirect_to": "https://markitdoc.vercel.app"}
    assert captured["json"] == {
        "email": "new-user@example.com",
        "password": "StrongPass123",
        "data": {"full_name": "New User"},
    }


def test_signup_redirect_falls_back_to_configured_frontend_origin(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.setenv("FRONTEND_ORIGIN", "https://custom-doc2md.example.com/")

    captured: dict[str, object] = {}

    class FakeSignupResponse:
        status_code = 200

        def json(self):
            return {"id": "33333333-3333-4333-8333-333333333333"}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, headers=None, json=None, params=None, timeout=None):
            captured["params"] = params
            return FakeSignupResponse()

    monkeypatch.setattr("app.main.httpx.AsyncClient", FakeAsyncClient)

    client = TestClient(app)
    response = client.post(
        "/auth/signup",
        json={
            "email": "new-user@example.com",
            "password": "StrongPass123",
            "full_name": "New User",
        },
    )

    assert response.status_code == 200
    assert captured["params"] == {"redirect_to": "https://custom-doc2md.example.com"}
