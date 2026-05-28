from fastapi import HTTPException

from app.validators import validate_upload_metadata


def test_validate_upload_metadata_accepts_supported_text_file():
    metadata = validate_upload_metadata(
        filename="notes.txt",
        content_type="text/plain",
        size_bytes=12,
    )

    assert metadata.file_type == "txt"
    assert metadata.size_bytes == 12


def test_validate_upload_metadata_rejects_empty_file():
    try:
        validate_upload_metadata(
            filename="notes.txt",
            content_type="text/plain",
            size_bytes=0,
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail["code"] == "EMPTY_FILE"
    else:
        raise AssertionError("empty files must be rejected")


def test_validate_upload_metadata_rejects_unsupported_extension():
    try:
        validate_upload_metadata(
            filename="source.md",
            content_type="text/markdown",
            size_bytes=12,
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail["code"] == "UNSUPPORTED_FILE_TYPE"
    else:
        raise AssertionError("unsupported extensions must be rejected")


def test_validate_upload_metadata_rejects_pdf_over_25_mb():
    try:
        validate_upload_metadata(
            filename="large.pdf",
            content_type="application/pdf",
            size_bytes=26 * 1024 * 1024,
        )
    except HTTPException as exc:
        assert exc.status_code == 413
        assert exc.detail["code"] == "FILE_TOO_LARGE"
    else:
        raise AssertionError("oversized PDFs must be rejected")
