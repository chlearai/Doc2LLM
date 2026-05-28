# Storage And Security

## Purpose

This document defines file storage, deletion, access control, and security requirements for the MVP.

## Storage Decisions

Use:

- Supabase Storage for generated Markdown `.md` files.
- Supabase Postgres for metadata, status, and logs.
- FastAPI local temp storage for source files during conversion only.

Do not use:

- Cloudflare R2.
- Permanent source file storage.
- Postgres binary storage for source files.
- Frontend direct writes to Markdown output storage.

## Source File Handling

Source files are temporary runtime artifacts.

Rules:

- Source files are uploaded to FastAPI.
- FastAPI validates file type, MIME type, and size.
- FastAPI writes the file to a temporary directory only when validation passes.
- FastAPI deletes the source file after success, failure, or timeout.
- Source file paths are not stored in Postgres.
- Source files are not uploaded to Supabase Storage.

Temporary path shape:

```txt
/tmp/conversions/{conversion_id}/input.{extension}
```

Cleanup requirement:

- Source cleanup must run in a `finally` block or equivalent guaranteed cleanup path.
- Timeout handling must also trigger cleanup.
- Failed conversion handling must also trigger cleanup.

## Markdown Output Storage

Bucket:

```txt
markdown-outputs
```

Path:

```txt
markdown-outputs/{user_id}/{conversion_id}/output.md
```

Rules:

- Store only generated `.md` files.
- Backend uploads Markdown output after conversion succeeds.
- Backend stores the output path in `conversions.markdown_storage_path`.
- Backend creates signed download URLs for users.
- Frontend does not receive service-role credentials.

## Access Control

The backend must enforce ownership.

Rules:

- A user can list only their own conversions.
- A user can read only their own conversion detail.
- A user can preview only their own Markdown output.
- A user can get signed download URLs only for their own Markdown output.
- A user can delete only their own conversion/output.

## Supabase Credentials

Frontend:

- Can use Supabase URL.
- Can use Supabase anon key.
- Must not use service-role key.

Backend:

- Uses Supabase URL.
- Uses service-role key for trusted database/storage operations.
- Verifies Supabase JWT on every protected API request.

## File Validation

Allowed extensions:

```txt
pdf
docx
pptx
xlsx
csv
txt
html
```

PDF max size:

```txt
25 MB
```

Other file size limits should be configured in backend settings before implementation.

Validation requirements:

- Reject unsupported extensions.
- Reject unsupported MIME types.
- Reject files over configured size.
- Reject empty files.
- Do not trust filename alone.

## Conversion Limits

Runtime limits:

```txt
Active conversions: 2-3
Pending conversions: 10
Timeout: 5 minutes
```

Behavior:

- Start conversion immediately if an active slot is available.
- Mark as `PENDING` if active slots are full and pending capacity remains.
- Reject with `QUEUE_FULL` if pending capacity is exhausted.
- Mark as `FAILED` if conversion times out.
- Delete temporary source files in all outcomes.

## Logging Rules

Allowed log content:

- Conversion ID.
- User ID.
- Status changes.
- File metadata such as extension, MIME type, and size.
- Error summaries.

Do not log:

- Source file contents.
- Markdown output contents.
- Supabase service key.
- User access tokens.

## Admin Dashboard

Admin dashboard security and access policies will be designed later.

Do not add admin-specific storage rules in this MVP.
