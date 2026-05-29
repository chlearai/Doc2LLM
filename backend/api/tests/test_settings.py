import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.auth import AuthenticatedUser, get_current_user
from app.dependencies import get_conversion_manager
from app.main import app
from app.services import ConversionManager


def _user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="11111111-1111-4111-8111-111111111111",
        email="user@example.com",
        full_name="Internal User",
        role="user",
    )


def _client(manager: ConversionManager) -> TestClient:
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_conversion_manager] = lambda: manager
    return TestClient(app)


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_get_current_user_profile(tmp_path: Path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    client = _client(manager)

    response = client.get("/auth/me")
    _clear_overrides()

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "11111111-1111-4111-8111-111111111111"
    assert data["email"] == "user@example.com"
    assert data["full_name"] == "Internal User"


def test_get_current_user_profile_uses_supabase_auth_endpoint(monkeypatch, tmp_path: Path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    app.dependency_overrides[get_conversion_manager] = lambda: manager

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "id": "33333333-3333-4333-8333-333333333333",
                "email": "user@example.com",
                "user_metadata": {"full_name": "Jane Doe"},
            }

    def fake_get(url, headers=None, timeout=None):
        assert url == "https://example.supabase.co/auth/v1/user"
        assert headers["Authorization"] == "Bearer real-access-token"
        assert headers["apikey"] == "service-role-key"
        return FakeResponse()

    monkeypatch.setattr("app.auth.httpx.get", fake_get)

    client = TestClient(app)
    response = client.get("/auth/me", headers={"Authorization": "Bearer real-access-token"})
    _clear_overrides()

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "33333333-3333-4333-8333-333333333333"
    assert data["email"] == "user@example.com"
    assert data["full_name"] == "Jane Doe"
    assert data["role"] == "user"

    profile = manager.repository.get_user("33333333-3333-4333-8333-333333333333")
    assert profile is not None
    assert profile.email == "user@example.com"
    assert profile.full_name == "Jane Doe"


def test_update_profile_name(tmp_path: Path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    client = _client(manager)

    # First, make sure user exists in repo
    manager.repository.create_user(
        user_id="11111111-1111-4111-8111-111111111111",
        email="user@example.com",
        full_name="Internal User"
    )

    # Empty name check
    response_empty = client.put("/auth/me", json={"full_name": ""})
    assert response_empty.status_code == 400

    # Valid name update
    response = client.put("/auth/me", json={"full_name": "Jane Doe"})
    _clear_overrides()

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Jane Doe"
    
    # Check repo persisted it
    profile = manager.repository.get_user("11111111-1111-4111-8111-111111111111")
    assert profile.full_name == "Jane Doe"


def test_change_password_validations(tmp_path: Path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    client = _client(manager)

    # Too short password
    resp1 = client.post("/auth/change-password", json={"password": "pwd"})
    assert resp1.status_code == 400
    assert "at least 8 characters" in resp1.json()["detail"]["message"]

    # Only letters password
    resp2 = client.post("/auth/change-password", json={"password": "abcdefgh"})
    assert resp2.status_code == 400
    assert "both letters and numbers" in resp2.json()["detail"]["message"]

    # Only numbers password
    resp3 = client.post("/auth/change-password", json={"password": "12345678"})
    assert resp3.status_code == 400
    assert "both letters and numbers" in resp3.json()["detail"]["message"]

    # Valid password - mock local dev response when Supabase is not configured
    resp_ok = client.post(
        "/auth/change-password",
        headers={"Authorization": "Bearer local-dev-token"},
        json={"password": "securePass123"}
    )
    _clear_overrides()
    assert resp_ok.status_code == 200
    assert "changed successfully" in resp_ok.json()["message"]


def test_delete_account_removes_data_and_profile(tmp_path: Path):
    manager = ConversionManager.for_tests(
        temp_root=tmp_path / "tmp",
        convert=lambda source: source.read_text(encoding="utf-8")
    )
    client = _client(manager)

    # Setup profile and conversion
    user_id = "11111111-1111-4111-8111-111111111111"
    manager.repository.create_user(
        user_id=user_id,
        email="user@example.com",
        full_name="Internal User"
    )

    create_response = client.post(
        "/conversions",
        files={"file": ("test.txt", b"my test content", "text/plain")},
    )
    assert create_response.status_code == 201
    conversion_id = create_response.json()["id"]

    # Storage should have file
    conv = manager.repository.get_for_user(conversion_id, user_id)
    assert conv.markdown_storage_path
    assert manager.storage.get_markdown(conv.markdown_storage_path) == "my test content"

    # Delete account
    del_resp = client.delete("/auth/account", headers={"Authorization": "Bearer local-dev-token"})
    _clear_overrides()

    assert del_resp.status_code == 200
    assert "deleted successfully" in del_resp.json()["message"]

    # Profile should be gone
    assert manager.repository.get_user(user_id) is None

    # Conversion should be cascade deleted
    assert len(manager.repository.list_for_user(user_id)) == 0

    # Storage file should be deleted
    assert manager.storage.get_markdown(conv.markdown_storage_path) is None
