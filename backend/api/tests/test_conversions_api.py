from pathlib import Path

from fastapi.testclient import TestClient

from app.auth import AuthenticatedUser, get_current_user
from app.dependencies import get_conversion_manager
from app.main import app
from app.models import ConversionRecord
from app.services import ConversionManager


def _user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="11111111-1111-4111-8111-111111111111",
        email="user@example.com",
        full_name="Internal User",
        role="user",
    )


def _other_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="22222222-2222-4222-8222-222222222222",
        email="other@example.com",
        full_name="Other User",
        role="user",
    )


def _client(manager: ConversionManager) -> TestClient:
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_conversion_manager] = lambda: manager
    return TestClient(app)


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_dev_token_can_convert_and_read_markdown_without_dependency_override(tmp_path: Path):
    manager = ConversionManager.for_tests(
        temp_root=tmp_path / "tmp",
        convert=lambda source: source.read_text(encoding="utf-8"),
    )
    app.dependency_overrides[get_conversion_manager] = lambda: manager
    client = TestClient(app)

    create_response = client.post(
        "/conversions",
        headers={"Authorization": "Bearer local-dev-token"},
        files={"file": ("dev.txt", b"# Dev\n\nLocal content", "text/plain")},
    )

    assert create_response.status_code == 201
    conversion_id = create_response.json()["id"]
    markdown_response = client.get(
        f"/conversions/{conversion_id}/markdown",
        headers={"Authorization": "Bearer local-dev-token"},
    )
    list_response = client.get(
        "/conversions",
        headers={"Authorization": "Bearer local-dev-token"},
    )

    _clear_overrides()
    assert markdown_response.status_code == 200
    assert "Local content" in markdown_response.json()["markdown"]
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["id"] == conversion_id


def test_completed_conversion_returns_download_url(tmp_path: Path):
    manager = ConversionManager.for_tests(
        temp_root=tmp_path / "tmp",
        convert=lambda source: source.read_text(encoding="utf-8"),
    )
    client = _client(manager)

    create_response = client.post(
        "/conversions",
        files={"file": ("download.txt", b"Download me", "text/plain")},
    )
    conversion_id = create_response.json()["id"]
    response = client.get(f"/conversions/{conversion_id}/download-url")

    _clear_overrides()
    assert response.status_code == 200
    assert response.json()["download_url"]
    assert response.json()["expires_in"] == 300


def test_post_conversions_converts_small_text_file_and_cleans_source(tmp_path: Path):
    manager = ConversionManager.for_tests(
        temp_root=tmp_path / "tmp",
        convert=lambda source: source.read_text(encoding="utf-8"),
    )
    client = _client(manager)

    response = client.post(
        "/conversions",
        files={"file": ("notes.txt", b"Alpha\n\nBeta", "text/plain")},
    )

    _clear_overrides()
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["original_file_name"] == "notes.txt"
    assert body["file_type"] == "txt"
    assert body["markdown_storage_path"].endswith("/output.md")
    assert not any((tmp_path / "tmp").glob("**/input.*"))


def test_get_conversions_returns_only_authenticated_user_items(tmp_path: Path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    owned = manager.repository.create_upload_received(
        user_id=_user().id,
        original_file_name="owned.txt",
        file_type="txt",
        mime_type="text/plain",
        file_size_bytes=5,
    )
    manager.repository.create_upload_received(
        user_id=_other_user().id,
        original_file_name="other.txt",
        file_type="txt",
        mime_type="text/plain",
        file_size_bytes=5,
    )
    client = _client(manager)

    response = client.get("/conversions")

    _clear_overrides()
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [owned.id]


def test_get_conversion_blocks_cross_user_access(tmp_path: Path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    other = manager.repository.create_upload_received(
        user_id=_other_user().id,
        original_file_name="other.txt",
        file_type="txt",
        mime_type="text/plain",
        file_size_bytes=5,
    )
    client = _client(manager)

    response = client.get(f"/conversions/{other.id}")

    _clear_overrides()
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "NOT_FOUND"


def test_markdown_and_download_url_require_completed_conversion(tmp_path: Path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    record = manager.repository.create_upload_received(
        user_id=_user().id,
        original_file_name="waiting.txt",
        file_type="txt",
        mime_type="text/plain",
        file_size_bytes=5,
    )
    client = _client(manager)

    markdown_response = client.get(f"/conversions/{record.id}/markdown")
    download_response = client.get(f"/conversions/{record.id}/download-url")

    _clear_overrides()
    assert markdown_response.status_code == 409
    assert markdown_response.json()["detail"]["code"] == "CONVERSION_NOT_READY"
    assert download_response.status_code == 409
    assert download_response.json()["detail"]["code"] == "CONVERSION_NOT_READY"


def test_retry_requires_reupload(tmp_path: Path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    record = manager.repository.create_upload_received(
        user_id=_user().id,
        original_file_name="failed.txt",
        file_type="txt",
        mime_type="text/plain",
        file_size_bytes=5,
    )
    client = _client(manager)

    response = client.post(f"/conversions/{record.id}/retry")

    _clear_overrides()
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "REUPLOAD_REQUIRED"


def test_delete_conversion_marks_deleted_and_removes_markdown(tmp_path: Path):
    manager = ConversionManager.for_tests(temp_root=tmp_path / "tmp")
    record = manager.repository.create_upload_received(
        user_id=_user().id,
        original_file_name="done.txt",
        file_type="txt",
        mime_type="text/plain",
        file_size_bytes=5,
    )
    completed = manager.repository.update_status(
        record.id,
        "COMPLETED",
        markdown_storage_path=f"markdown-outputs/{_user().id}/{record.id}/output.md",
    )
    assert isinstance(completed, ConversionRecord)
    manager.storage.upload_markdown(completed, "Done")
    client = _client(manager)

    response = client.delete(f"/conversions/{record.id}")
    markdown_response = client.get(f"/conversions/{record.id}/markdown")

    _clear_overrides()
    assert response.status_code == 200
    assert response.json()["status"] == "DELETED"
    assert markdown_response.status_code == 409
