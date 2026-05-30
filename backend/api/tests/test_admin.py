from fastapi.testclient import TestClient

from app.auth import AuthenticatedUser, get_current_user
from app.dependencies import get_conversion_manager
from app.main import app
from app.services import ConversionManager


def _user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="11111111-1111-4111-8111-111111111111",
        email="dev@local.test",
        full_name="Local Developer",
        role="user",
    )


def _admin() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="22222222-2222-4222-8222-222222222222",
        email="admin@local.test",
        full_name="Local Admin",
        role="admin",
    )


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_admin_endpoints_blocked_for_normal_user(tmp_path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_conversion_manager] = lambda: manager
    client = TestClient(app)

    # All admin endpoints should return 403 Forbidden for a normal user
    assert client.get("/admin/stats").status_code == 403
    assert client.get("/admin/users").status_code == 403
    assert client.post("/admin/users", json={"email": "new@test.com"}).status_code == 403
    assert client.put("/admin/users/123/status", json={"is_active": False}).status_code == 403
    assert client.put("/admin/users/123/role", json={"role": "admin"}).status_code == 403
    assert client.get("/admin/conversions").status_code == 403
    assert client.post("/admin/conversions/123/cancel").status_code == 403
    assert client.post("/admin/conversions/123/retry").status_code == 403
    assert client.delete("/admin/conversions/123").status_code == 403
    assert client.get("/admin/logs").status_code == 403
    assert client.get("/admin/system-health").status_code == 403

    _clear_overrides()


def test_admin_dashboard_stats_and_health(tmp_path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    app.dependency_overrides[get_current_user] = _admin
    app.dependency_overrides[get_conversion_manager] = lambda: manager
    client = TestClient(app)

    # Verify initial stats
    response = client.get("/admin/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_users"] == 2  # dev and admin
    assert stats["total_converted_files"] == 0
    assert stats["files_processed_today"] == 0
    assert stats["failed_conversions"] == 0
    assert stats["pending_conversions"] == 0
    assert stats["system_health"] == "Healthy"

    # Verify system health endpoint
    health_resp = client.get("/admin/system-health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert health_data["railway_converter"]["status"] == "Healthy"
    assert health_data["supabase_connection"]["status"] == "Healthy"

    _clear_overrides()


def test_admin_stats_uses_repository_interface_without_private_in_memory_state(tmp_path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")

    class SupabaseStyleRepository:
        def count_users(self):
            return 3

        def count_conversions(self, *, status=None, completed_from=None):
            if status == "FAILED":
                return 1
            if completed_from is not None:
                return 2
            return 5

    manager.repository = SupabaseStyleRepository()
    app.dependency_overrides[get_current_user] = _admin
    app.dependency_overrides[get_conversion_manager] = lambda: manager
    client = TestClient(app)

    response = client.get("/admin/stats")

    _clear_overrides()
    assert response.status_code == 200
    assert response.json() == {
        "total_users": 3,
        "total_converted_files": 5,
        "files_processed_today": 2,
        "failed_conversions": 1,
        "pending_conversions": 0,
        "system_health": "Healthy",
    }


def test_admin_user_management(tmp_path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    manager.repository.log_feature_usage(
        "11111111-1111-4111-8111-111111111111",
        "ocr",
        "gpt-4o-mini",
        1250,
    )
    app.dependency_overrides[get_current_user] = _admin
    app.dependency_overrides[get_conversion_manager] = lambda: manager
    client = TestClient(app)

    # 1. List users
    list_resp = client.get("/admin/users")
    assert list_resp.status_code == 200
    users = list_resp.json()["items"]
    assert len(users) == 2
    emails = [u["email"] for u in users]
    assert "dev@local.test" in emails
    assert "admin@local.test" in emails
    dev_user = next(u for u in users if u["email"] == "dev@local.test")
    assert dev_user["ocr_tokens_consumed"] == 1250

    # 2. Create a new user
    create_resp = client.post(
        "/admin/users",
        json={"email": "new_user@test.com", "full_name": "New User", "role": "user"}
    )
    assert create_resp.status_code == 201
    new_user = create_resp.json()
    assert new_user["email"] == "new_user@test.com"
    assert new_user["role"] == "user"
    assert new_user["is_active"] is True
    assert new_user["ocr_tokens_consumed"] == 0

    # 3. Create duplicate user should fail
    dup_resp = client.post(
        "/admin/users",
        json={"email": "new_user@test.com"}
    )
    assert dup_resp.status_code == 400

    # 4. Disable user
    uid = new_user["id"]
    status_resp = client.put(f"/admin/users/{uid}/status", json={"is_active": False})
    assert status_resp.status_code == 200
    assert status_resp.json()["is_active"] is False

    # 5. Change role
    role_resp = client.put(f"/admin/users/{uid}/role", json={"role": "admin"})
    assert role_resp.status_code == 200
    assert role_resp.json()["role"] == "admin"

    _clear_overrides()


def test_admin_conversion_and_job_management(tmp_path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    # Seed a conversion for user
    record = manager.repository.create_upload_received(
        user_id="11111111-1111-4111-8111-111111111111",
        original_file_name="admin_test.txt",
        file_type="txt",
        mime_type="text/plain",
        file_size_bytes=100
    )
    
    app.dependency_overrides[get_current_user] = _admin
    app.dependency_overrides[get_conversion_manager] = lambda: manager
    client = TestClient(app)

    # 1. List conversions
    list_resp = client.get("/admin/conversions")
    assert list_resp.status_code == 200
    conversions = list_resp.json()["items"]
    assert len(conversions) == 1
    assert conversions[0]["original_file_name"] == "admin_test.txt"
    assert conversions[0]["user_id"] == "11111111-1111-4111-8111-111111111111"
    assert conversions[0]["user_email"] == "dev@local.test"
    assert conversions[0]["user_full_name"] == "Local Developer"

    # 2. Cancel conversion
    cancel_resp = client.post(f"/admin/conversions/{record.id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "FAILED"
    assert "Cancelled by administrator" in cancel_resp.json()["error_message"]

    # 3. Retry conversion
    retry_resp = client.post(f"/admin/conversions/{record.id}/retry")
    assert retry_resp.status_code == 200
    assert retry_resp.json()["status"] == "COMPLETED"

    # 4. View logs
    logs_resp = client.get("/admin/logs")
    assert logs_resp.status_code == 200
    logs = logs_resp.json()["items"]
    assert len(logs) > 0
    assert logs[0]["conversion_id"] == record.id

    # 5. Delete conversion
    del_resp = client.delete(f"/admin/conversions/{record.id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "DELETED"

    _clear_overrides()
