# File-to-Markdown Dashboard Implementation Plan

## Goal

Build a lightweight internal dashboard that lets authenticated users upload documents, convert them to clean Markdown using MarkItDown, preview/copy/download the generated `.md` output, and view conversion history.

This MVP is for a small internal team. Keep the architecture simple and avoid enterprise-scale infrastructure until the product needs it.

## Fixed Decisions

- Use Next.js for the frontend dashboard.
- Use Supabase Auth for login.
- Use FastAPI for the conversion backend.
- Use MarkItDown as the conversion engine.
- Use Supabase Postgres for conversion metadata, history, and status.
- Use Supabase Storage for generated Markdown `.md` files.
- Do not use Cloudflare R2.
- Do not permanently store uploaded source documents.
- Store source files only temporarily during conversion.
- Delete source files immediately after successful conversion, failed conversion, or timeout.
- Store only generated Markdown output files.
- Build an admin dashboard later, not in this MVP.

## Core Product Scope

Implement:

- Authenticated internal dashboard.
- File upload flow.
- Supported file validation.
- Conversion status tracking.
- Markdown preview.
- Copy Markdown action.
- Download `.md` action.
- Conversion history.
- Clear loading, empty, processing, completed, failed, and capacity-full states.

Do not implement:

- Cloudflare R2.
- Redis.
- BullMQ.
- Docker Compose.
- Microservices.
- Permanent source file storage.
- Browser-only conversion.
- Admin dashboard.
- Complex admin roles.
- Billing.
- Team management.
- OCR unless explicitly added later.
- Search inside Markdown unless explicitly added later.

## Supported File Types

The MVP should support:

- PDF
- DOCX
- PPTX
- XLSX
- CSV
- TXT
- HTML

## Conversion Limits

Implement these limits:

| Limit | Value |
|---|---:|
| PDF max size | 25 MB |
| Active conversions | 2-3 |
| Pending conversions | 10 |
| Conversion timeout | 5 minutes |

Behavior:

- If an active conversion slot is available, start processing.
- If active slots are full and pending capacity is available, mark the conversion as `PENDING`.
- If the pending queue is full, reject the upload with a clear error.
- If conversion exceeds 5 minutes, mark it as `FAILED`, record the timeout error, and delete the source file.

## Storage Rules

Source documents:

- Temporary only.
- Written to backend temp storage during conversion.
- Never stored in Supabase Storage.
- Never stored in Supabase Postgres.
- Never stored in Cloudflare R2.
- Deleted after success, failure, or timeout.

Markdown output:

- Stored in Supabase Storage.
- Stored as `.md` files.
- Accessed through signed URLs.
- Owned by the authenticated user who created the conversion.

Storage bucket:

```txt
markdown-outputs
```

Storage path:

```txt
markdown-outputs/{user_id}/{conversion_id}/output.md
```

Postgres:

- Store metadata, status, logs, and `markdown_storage_path`.
- Do not store source document contents.
- Do not store source document binary data.

## Conversion Statuses

Implement these statuses:

- `UPLOAD_RECEIVED`
- `PENDING`
- `PROCESSING`
- `COMPLETED`
- `FAILED`
- `DELETED`

## Backend Implementation

Create a FastAPI backend that provides:

- Supabase JWT verification.
- Authenticated user extraction.
- File extension validation.
- MIME validation.
- File size validation.
- Temporary source file write.
- MarkItDown conversion wrapper.
- 5-minute timeout handling.
- Cleanup logic that always deletes source files.
- In-app concurrency limiter.
- Pending queue capacity guard.
- Supabase Storage upload for Markdown output.
- Supabase Postgres writes for conversion records.
- Supabase Postgres writes for conversion logs.
- Signed download URL generation.
- User ownership checks.

Backend endpoints:

```txt
GET /health
GET /auth/me

POST /conversions
GET /conversions
GET /conversions/{id}
GET /conversions/{id}/status
GET /conversions/{id}/download-url
POST /conversions/{id}/retry
DELETE /conversions/{id}
```

Retry behavior:

- Since source files are deleted immediately, retry cannot reuse the original uploaded file.
- For MVP, retry should require re-uploading the source file unless source retention is explicitly changed later.

## Backend Modules To Create

```txt
backend/api/
  pyproject.toml
  README.md
  .env.example
  app/
    __init__.py
    main.py
    config.py
    auth.py
    models.py
    validators.py
    limiter.py
    conversion_service.py
    storage.py
    repository.py
    cleanup.py
    routers/
      __init__.py
      health.py
      auth.py
      conversions.py
  tests/
    test_validators.py
    test_limiter.py
    test_cleanup.py
    test_conversions_api.py
```

## Frontend Implementation

Create a Next.js dashboard that provides:

- Login screen.
- Protected dashboard shell.
- Upload area.
- File validation feedback.
- Conversion status UI.
- Pending queue feedback.
- Markdown preview.
- Copy Markdown button.
- Download `.md` button.
- Conversion history table.
- Conversion detail view.
- Settings/account page with sign out.

Use a simple SaaS product UI:

- Task-first dashboard, not a marketing landing page.
- Restrained color palette.
- Clear navigation.
- Clear primary actions.
- Specific button labels.
- Useful empty states.
- Skeleton loading states where appropriate.
- Clear error messages that explain what happened and what to do next.

## Frontend Files To Create

```txt
frontend/
  package.json
  next.config.ts
  tsconfig.json
  .env.example
  app/
    layout.tsx
    page.tsx
    globals.css
    login/
      page.tsx
    dashboard/
      page.tsx
    conversions/
      [id]/
        page.tsx
    history/
      page.tsx
    settings/
      page.tsx
  components/
    app-shell.tsx
    upload-dropzone.tsx
    conversion-status.tsx
    markdown-preview.tsx
    conversion-table.tsx
    empty-state.tsx
    ui/
      badge.tsx
      button.tsx
      input.tsx
      progress.tsx
  lib/
    api-client.ts
    format.ts
    supabase-browser.ts
    types.ts
  middleware.ts
```

## Database Implementation

Create Supabase migrations for:

- `profiles`
- `conversions`
- `conversion_logs`

### profiles

```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### conversions

```sql
CREATE TABLE conversions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id),
    original_file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    mime_type TEXT,
    file_size_mb NUMERIC,
    markdown_storage_path TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### conversion_logs

```sql
CREATE TABLE conversion_logs (
    id UUID PRIMARY KEY,
    conversion_id UUID NOT NULL REFERENCES conversions(id),
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Supabase Storage Implementation

Create bucket:

```txt
markdown-outputs
```

Implement storage behavior:

- Backend uploads generated `.md` files.
- Backend creates signed download URLs.
- Users can access only their own conversion outputs.
- Deleting a conversion deletes the stored Markdown output.

## End-To-End Data Flow

```txt
1. User signs in with Supabase Auth.
2. User uploads a supported file from the dashboard.
3. Frontend sends file and Supabase JWT to FastAPI.
4. FastAPI verifies the JWT.
5. FastAPI validates file type, MIME type, and size.
6. FastAPI creates a conversion record.
7. FastAPI checks active and pending conversion limits.
8. FastAPI writes the source file to temporary storage.
9. FastAPI marks the conversion as PROCESSING.
10. FastAPI runs MarkItDown with a 5-minute timeout.
11. FastAPI uploads output.md to Supabase Storage.
12. FastAPI deletes the temporary source file.
13. FastAPI updates the conversion as COMPLETED.
14. Frontend shows the completed conversion.
15. User previews, copies, or downloads the Markdown output.
```

Failure flow:

```txt
1. Conversion fails, times out, or validation fails.
2. FastAPI records the error message.
3. FastAPI marks the conversion as FAILED when a conversion record exists.
4. FastAPI deletes the temporary source file if one was written.
5. Frontend shows a clear failure message.
```

## Build Order

1. Create Supabase schema migrations.
2. Create Supabase Storage bucket/policy migration.
3. Scaffold FastAPI backend.
4. Implement backend config and health endpoint.
5. Implement Supabase auth verification.
6. Implement file validators.
7. Implement temp file cleanup helper.
8. Implement conversion limiter.
9. Implement MarkItDown conversion service.
10. Implement Supabase repository layer.
11. Implement Supabase Storage layer.
12. Implement conversion endpoints.
13. Add backend tests for validators, limiter, cleanup, and API behavior.
14. Scaffold Next.js frontend.
15. Implement Supabase auth client and protected routes.
16. Build login screen.
17. Build dashboard shell.
18. Build upload flow.
19. Build conversion status UI.
20. Build Markdown preview/copy/download actions.
21. Build conversion history.
22. Build conversion detail page.
23. Add loading, empty, failed, pending, and completed states.
24. Run backend tests.
25. Run frontend lint/build.
26. Run local end-to-end conversion test.

## Later Work

Later, build an admin dashboard for internal administration.

The admin dashboard is not part of this MVP implementation plan.
