from pathlib import Path

from app.errors import api_error
from app.models import UploadMetadata

PDF_MAX_BYTES = 25 * 1024 * 1024
DEFAULT_MAX_BYTES = 25 * 1024 * 1024
ALLOWED_MIME_TYPES = {
    "pdf": {"application/pdf"},
    "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "pptx": {"application/vnd.openxmlformats-officedocument.presentationml.presentation"},
    "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    "csv": {"text/csv", "application/csv", "application/vnd.ms-excel"},
    "txt": {"text/plain"},
    "html": {"text/html", "application/xhtml+xml"},
}


def validate_upload_metadata(
    filename: str,
    content_type: str | None,
    size_bytes: int,
) -> UploadMetadata:
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in ALLOWED_MIME_TYPES:
        raise api_error(400, "UNSUPPORTED_FILE_TYPE", "This file type is not supported.")

    if size_bytes <= 0:
        raise api_error(400, "EMPTY_FILE", "The uploaded file is empty.")

    max_bytes = PDF_MAX_BYTES if extension == "pdf" else DEFAULT_MAX_BYTES
    if size_bytes > max_bytes:
        raise api_error(413, "FILE_TOO_LARGE", "PDF files can be up to 25 MB.")

    if content_type and content_type not in ALLOWED_MIME_TYPES[extension]:
        raise api_error(400, "UNSUPPORTED_MIME_TYPE", "This file MIME type is not supported.")

    return UploadMetadata(file_type=extension, size_bytes=size_bytes)
