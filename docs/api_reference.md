# API Reference

## Purpose

This document defines the FastAPI contract for the File-to-Markdown dashboard.

FastAPI automatically generates interactive Swagger UI documentation from route definitions and Pydantic models. When the backend is running, the API docs should be available at:

```txt
GET /docs
```

The OpenAPI JSON schema should be available at:

```txt
GET /openapi.json
```

ReDoc should be available at:

```txt
GET /redoc
```

## Authentication

All endpoints except `GET /health` require a Supabase JWT.

Requests must include:

```txt
Authorization: Bearer <supabase_access_token>
```

The backend verifies the token, extracts the authenticated user ID, and uses that ID for ownership checks.

The Supabase service key is backend-only and must never be sent to the frontend.

## Common Error Shape

Use a consistent JSON error response:

```json
{
  "detail": {
    "code": "FILE_TOO_LARGE",
    "message": "PDF files can be up to 25 MB.",
    "request_id": "optional-request-id"
  }
}
```

Recommended error codes:

| Code | HTTP Status | Meaning |
|---|---:|---|
| `UNAUTHORIZED` | 401 | Missing or invalid JWT. |
| `FORBIDDEN` | 403 | User does not own the conversion. |
| `NOT_FOUND` | 404 | Conversion does not exist. |
| `UNSUPPORTED_FILE_TYPE` | 400 | Extension is not supported. |
| `UNSUPPORTED_MIME_TYPE` | 400 | MIME type is not supported. |
| `FILE_TOO_LARGE` | 413 | File exceeds allowed size. |
| `QUEUE_FULL` | 429 | Pending conversion limit reached. |
| `CONVERSION_TIMEOUT` | 504 | Conversion exceeded 5 minutes. |
| `CONVERSION_FAILED` | 500 | MarkItDown conversion failed. |

## Endpoints

### GET /health

Checks backend availability.

Auth: none.

Response:

```json
{
  "status": "ok"
}
```

### GET /auth/me

Returns the authenticated user profile.

Auth: required.

Response:

```json
{
  "id": "7f6d2e6a-6f0e-49e2-a62d-6d4f5d7b2e3c",
  "email": "user@example.com",
  "full_name": "Internal User",
  "role": "user"
}
```

### POST /conversions

Uploads one source file and creates a conversion.

Auth: required.

Request type:

```txt
multipart/form-data
```

Fields:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `file` | File | Yes | Supported file type only. |

Limits:

- PDF max: 25 MB.
- Active conversions: 2-3.
- Pending conversions: 10.
- Conversion timeout: 5 minutes.

Response:

```json
{
  "id": "5c4a6319-9212-42c2-86d4-4707ab6f3c89",
  "status": "PENDING",
  "original_file_name": "proposal.pdf",
  "file_type": "pdf",
  "file_size_bytes": 10485760,
  "markdown_storage_path": null,
  "created_at": "2026-05-28T09:30:00Z"
}
```

Notes:

- The backend may return `PROCESSING` if the job starts immediately.
- The backend may return `PENDING` if active slots are full.
- If pending capacity is full, return `429 QUEUE_FULL`.

### GET /conversions

Lists the authenticated user's conversions.

Auth: required.

Query parameters:

| Name | Type | Required | Default | Notes |
|---|---|---:|---|---|
| `status` | string | No | none | Filter by status. |
| `limit` | integer | No | 20 | Max 100. |
| `offset` | integer | No | 0 | Pagination offset. |

Response:

```json
{
  "items": [
    {
      "id": "5c4a6319-9212-42c2-86d4-4707ab6f3c89",
      "original_file_name": "proposal.pdf",
      "file_type": "pdf",
      "file_size_bytes": 10485760,
      "status": "COMPLETED",
      "markdown_storage_path": "markdown-outputs/USER_ID/CONVERSION_ID/output.md",
      "created_at": "2026-05-28T09:30:00Z",
      "completed_at": "2026-05-28T09:30:22Z"
    }
  ],
  "limit": 20,
  "offset": 0
}
```

### GET /conversions/{id}

Returns one conversion owned by the authenticated user.

Auth: required.

Response:

```json
{
  "id": "5c4a6319-9212-42c2-86d4-4707ab6f3c89",
  "original_file_name": "proposal.pdf",
  "file_type": "pdf",
  "mime_type": "application/pdf",
  "file_size_bytes": 10485760,
  "status": "COMPLETED",
  "markdown_storage_path": "markdown-outputs/USER_ID/CONVERSION_ID/output.md",
  "error_message": null,
  "started_at": "2026-05-28T09:30:01Z",
  "completed_at": "2026-05-28T09:30:22Z",
  "created_at": "2026-05-28T09:30:00Z"
}
```

### GET /conversions/{id}/status

Returns lightweight status for polling.

Auth: required.

Response:

```json
{
  "id": "5c4a6319-9212-42c2-86d4-4707ab6f3c89",
  "status": "PROCESSING",
  "error_message": null,
  "completed_at": null
}
```

### GET /conversions/{id}/markdown

Returns the generated Markdown text for preview/copy.

Auth: required.

Available only when status is `COMPLETED`.

Response:

```json
{
  "id": "5c4a6319-9212-42c2-86d4-4707ab6f3c89",
  "markdown": "# Converted Document\n\nMarkdown content..."
}
```

### GET /conversions/{id}/download-url

Returns a signed URL for the generated `.md` file.

Auth: required.

Available only when status is `COMPLETED`.

Response:

```json
{
  "id": "5c4a6319-9212-42c2-86d4-4707ab6f3c89",
  "download_url": "https://supabase.example/storage/v1/object/sign/...",
  "expires_in": 300
}
```

### POST /conversions/{id}/retry

Retry cannot reuse the original source file because source files are deleted immediately.

For MVP, this endpoint should either:

- Return `400` with a message that retry requires re-upload, or
- Be omitted from the first backend implementation.

Recommended MVP response:

```json
{
  "detail": {
    "code": "REUPLOAD_REQUIRED",
    "message": "The source file was deleted after the previous attempt. Upload the file again to retry."
  }
}
```

### DELETE /conversions/{id}

Deletes the conversion metadata and generated Markdown output.

Auth: required.

Behavior:

- Verify the conversion belongs to the authenticated user.
- Delete Markdown output from Supabase Storage if it exists.
- Mark the conversion as `DELETED` or delete the row, depending on final implementation preference.
- Do not delete source files because source files should already be gone.

Response:

```json
{
  "id": "5c4a6319-9212-42c2-86d4-4707ab6f3c89",
  "status": "DELETED"
}
```

## Swagger Implementation Notes

FastAPI generates Swagger automatically when routes use typed function signatures and Pydantic models.

Implementation requirements:

- Define request/response schemas in `backend/api/app/models.py`.
- Add `response_model=` to each route.
- Add `summary=` and `description=` to routes.
- Add `tags=["health"]`, `tags=["auth"]`, and `tags=["conversions"]`.
- Keep `docs_url="/docs"` enabled.
- Keep `openapi_url="/openapi.json"` enabled.

Example FastAPI app setup:

```python
app = FastAPI(
    title="File-to-Markdown Converter API",
    version="0.1.0",
    description="Internal API for converting uploaded files into Markdown outputs.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
```
