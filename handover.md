# Handover

## Current State

The MVP is runnable locally with a temporary local-only auth path.

Implemented sprint coverage:

- Sprint 0: project setup and MarkItDown integration scaffold.
- Sprint 2: conversion API.
- Sprint 3: authenticated frontend shell.
- Sprint 4: upload, status, preview, copy, and download workflow.
- Sprint 5: history, detail, delete, responsive/hardening pass, and local E2E verification.

Sprint 1 is still intentionally incomplete because Supabase setup is pending from the user.

## Local Run

Backend:

```txt
cd backend/api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```txt
cd frontend
npm install
npm run dev -- --port 3001
```

Open:

```txt
http://localhost:3001
```

Local dev login:

```txt
Email: dev@local.test
Password: markdown-dev
```

The local dev login works only when frontend Supabase env vars are missing. It sets a local dev cookie and sends `Bearer local-dev-token` to the backend. When real Supabase env vars are configured, the frontend switches back to Supabase Auth.

## Completed Backend Work

Backend root:

```txt
backend/api/
```

Implemented modules:

```txt
app/
  auth.py
  cleanup.py
  conversion_service.py
  dependencies.py
  errors.py
  limiter.py
  main.py
  models.py
  repository.py
  services.py
  storage.py
  validators.py
```

Implemented API:

```txt
GET /health
GET /auth/me
POST /conversions
GET /conversions
GET /conversions/{id}
GET /conversions/{id}/status
GET /conversions/{id}/markdown
GET /conversions/{id}/download-url
POST /conversions/{id}/retry
DELETE /conversions/{id}
```

Behavior implemented:

- Common JSON error shape from `docs/api_reference.md`.
- Local dev-token auth for local MVP testing.
- File extension, MIME, empty-file, and size validation.
- Temporary source file write and guaranteed cleanup.
- In-app active conversion limiter and pending queue guard.
- Conversion status lifecycle.
- User ownership checks through repository access.
- In-memory repository and Markdown storage for local/dev operation.
- Markdown preview endpoint.
- Signed-download-url-shaped endpoint.
- Delete marks records `DELETED` and removes stored Markdown output.
- CORS for local frontend origins and optional `FRONTEND_ORIGIN`.

Conversion behavior:

- `TXT`, `CSV`, and `HTML` use a direct lightweight text conversion fallback.
- Other supported file types still use local MarkItDown.
- The direct fallback was added because this Windows/Conda environment can fail loading `onnxruntime` from MarkItDown inside live uvicorn conversion requests.

## Completed Frontend Work

Frontend root:

```txt
frontend/
```

Implemented app routes:

```txt
app/
  login/page.tsx
  (app)/dashboard/page.tsx
  (app)/history/page.tsx
  (app)/settings/page.tsx
  (app)/conversions/[id]/page.tsx
```

Implemented components:

```txt
components/
  app-shell.tsx
  conversion-detail-client.tsx
  conversion-status.tsx
  conversion-table.tsx
  dashboard-client.tsx
  empty-state.tsx
  history-client.tsx
  markdown-preview.tsx
  upload-dropzone.tsx
  ui/
    badge.tsx
    button.tsx
    input.tsx
    progress.tsx
```

Implemented frontend behavior:

- Supabase login screen.
- Local-only dev login fallback.
- Protected route middleware.
- App shell with product name, nav, user context, and sign out.
- Upload dropzone and file picker.
- Frontend validation for supported extensions, empty files, and 25 MB PDF limit.
- Upload to FastAPI with auth header.
- Conversion status display.
- Markdown preview.
- Copy Markdown.
- Download generated `.md` from browser blob.
- Recent conversions on dashboard.
- History table.
- Conversion detail page.
- Delete conversion from history/detail flows.
- Loading, empty, success, and error states.
- Responsive layout for desktop and mobile widths.

Design:

- Uses sans-serif-only typography.
- Uses the restrained OKLCH design tokens from `DESIGN.md`.
- Avoids decorative metrics, gradient text, glassmorphism, nested cards, and admin-dashboard bloat.

## Verification

Last verified commands:

```txt
cd backend/api
python -m pytest -q
```

Result:

```txt
21 passed
```

```txt
cd frontend
npm run build
```

Result:

```txt
Build passed
```

Local E2E verification performed:

- Backend health returned `{ "status": "ok" }`.
- Tiny `.txt` file uploaded through `POST /conversions`.
- Conversion returned `COMPLETED`.
- `GET /conversions/{id}/markdown` returned the Markdown content.
- Browser verified local dev login.
- Browser verified dashboard upload area.
- Browser verified recent conversions.
- Browser verified history list.
- Browser verified conversion detail page.
- Browser verified Markdown preview, copy/download controls, and delete.
- Temp source cleanup checked:

```txt
D:\tmp\conversions files=0
\tmp\conversions files=0
```

## Important Caveats

### Sprint 1 Still Needed

Supabase is not wired yet.

Still required:

- Supabase migrations for `profiles`, `conversions`, and `conversion_logs`.
- Recommended indexes from `docs/data_models.md`.
- Supabase Storage bucket setup for `markdown-outputs`.
- Real Supabase JWT verification in FastAPI.
- Supabase-backed repository implementation.
- Supabase-backed Markdown storage implementation.
- Real signed URLs from Supabase Storage.
- RLS/storage policy confirmation.

Current backend persistence is in-memory, so local conversions reset when the backend process restarts.

### MarkItDown Environment Caveat

In this Windows/Conda environment, live uvicorn conversion requests can fail when MarkItDown imports `magika`/`onnxruntime`.

Observed error:

```txt
ImportError: DLL load failed while importing onnxruntime_pybind11_state: The handle is invalid.
```

Current mitigation:

- Direct fallback for `TXT`, `CSV`, and `HTML`.
- MarkItDown remains used for other supported file types.

Recommendation:

- Use a clean virtual environment for serious backend work.
- Re-test PDF/DOCX/PPTX/XLSX after the clean environment is active.

### npm Audit

`npm install` reported two moderate advisories. They were not fixed because `npm audit fix --force` may change dependency versions outside the current sprint scope.

## Environment Values Still Needed

Backend `.env`:

```txt
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
SUPABASE_STORAGE_BUCKET=markdown-outputs
FRONTEND_ORIGIN=
MAX_ACTIVE_CONVERSIONS=2
MAX_PENDING_CONVERSIONS=10
CONVERSION_TIMEOUT_SECONDS=300
PDF_MAX_BYTES=26214400
TEMP_CONVERSION_DIR=/tmp/conversions
```

Frontend `.env.local`:

```txt
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Read Before Continuing

Required context:

```txt
Agents.md
PRODUCT.md
DESIGN.md
implementation_plan.md
docs/sprints.md
docs/file_to_markdown_converter_prd_v2.md
docs/file_to_markdown_architecture.md
docs/data_models.md
docs/api_reference.md
docs/storage_and_security.md
docs/environment_config.md
```

Also read:

```txt
skills/impeccable-style-universal/README.txt
skills/impeccable-style-universal/.codex/
```

## Recommended Next Work

Do Sprint 1 properly now that the local workflow is usable:

1. Add Supabase migrations.
2. Add Supabase repository/storage implementations behind the existing interfaces.
3. Replace `local-dev-token` usage with real JWT verification when Supabase env vars are present.
4. Keep local dev auth available only for no-Supabase local development.
5. Re-run backend tests, frontend build, and a real Supabase-backed conversion check.

Do not add admin dashboard, Cloudflare R2, Redis, billing, team management, OCR, or Markdown search unless explicitly approved.
