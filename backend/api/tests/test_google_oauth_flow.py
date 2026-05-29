from pathlib import Path

from fastapi.testclient import TestClient

from app.dependencies import get_conversion_manager
from app.main import app
from app.services import ConversionManager


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


def test_google_oauth_frontend_uses_callback_redirect():
    oauth_source = (FRONTEND_ROOT / "lib" / "oauth.ts").read_text(encoding="utf-8")
    login_source = (FRONTEND_ROOT / "app" / "login" / "page.tsx").read_text(encoding="utf-8")
    callback_source = (FRONTEND_ROOT / "app" / "auth" / "callback" / "route.ts").read_text(encoding="utf-8")

    assert "provider: \"google\"" in login_source
    assert "buildOAuthRedirectTo" in login_source
    assert "/auth/callback" in oauth_source
    assert "exchangeCodeForSession" in callback_source
    assert "redirectTo" in login_source


def test_google_oauth_profile_uses_google_name_metadata(monkeypatch, tmp_path: Path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    app.dependency_overrides[get_conversion_manager] = lambda: manager

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)

    class FakeGoogleAuthResponse:
        status_code = 200

        def json(self):
            return {
                "id": "44444444-4444-4444-8444-444444444444",
                "email": "google-user@example.com",
                "user_metadata": {"name": "Google User"},
            }

    monkeypatch.setattr("app.auth.httpx.get", lambda *args, **kwargs: FakeGoogleAuthResponse())

    client = TestClient(app)
    response = client.get("/auth/me", headers={"Authorization": "Bearer google-access-token"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["full_name"] == "Google User"

    profile = manager.repository.get_user("44444444-4444-4444-8444-444444444444")
    assert profile is not None
    assert profile.full_name == "Google User"
