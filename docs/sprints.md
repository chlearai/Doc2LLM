# Implementation Sprints

## Purpose

This document breaks the MVP into small implementation sprints.

Keep each sprint shippable and focused. Do not add admin dashboard work, Cloudflare R2, Redis, billing, team management, OCR, or search in this MVP.

## Sprint 0: Project Setup And MarkItDown Integration

Goal: Create the app structure and wire the conversion dependency cleanly.

Build:

- `frontend/` Next.js app scaffold.
- `backend/api/` FastAPI app scaffold.
- Backend environment config.
- Backend health endpoint.
- FastAPI docs metadata so `/docs`, `/redoc`, and `/openapi.json` are available.
- Local development README updates.
- MarkItDown integration strategy.

MarkItDown rule:

- Use the conversion implementation from `backend/markitdown-main/`.
- Do not keep unrelated upstream repository material inside the product app if it is not needed at runtime.
- Prefer installing/using only the local `packages/markitdown` package from `backend/markitdown-main/markitdown-main/packages/markitdown`.
- Keep sample plugins, upstream tests, OCR package, MCP package, and unrelated repo files out of the product backend unless a later requirement needs them.

Done when:

- FastAPI starts locally.
- `GET /health` works.
- `/docs` loads and shows the API title.
- Backend can import and call MarkItDown from the local source package.

## Sprint 1: Database, Storage, And Auth Foundation

Goal: Make the backend able to identify users and persist conversion metadata/output paths.

Build:

- Supabase migrations for `profiles`, `conversions`, and `conversion_logs`.
- Recommended indexes from `docs/data_models.md`.
- Supabase Storage bucket setup notes for `markdown-outputs`.
- Supabase JWT verification in FastAPI.
- `GET /auth/me`.
- Repository layer for conversion records.
- Conversion log writes for status changes and failures.
- Storage layer for `.md` upload and signed URLs.

Done when:

- Protected API calls reject missing/invalid JWTs.
- `GET /auth/me` returns the authenticated user profile shape from `docs/api_reference.md`.
- Backend can create/list conversion rows for the authenticated user.
- Backend can upload a test `.md` file and generate a signed URL.

## Sprint 2: Conversion API

Goal: Implement the core upload-to-Markdown backend workflow.

Build:

- `POST /conversions`
- `GET /conversions`
- `GET /conversions/{id}`
- `GET /conversions/{id}/status`
- `GET /conversions/{id}/markdown`
- `GET /conversions/{id}/download-url`
- `POST /conversions/{id}/retry` as a re-upload-required response, or omit it from implementation and document that retry is not available in MVP.
- `DELETE /conversions/{id}`
- File extension, MIME, empty-file, and size validation.
- Temporary source file handling.
- Guaranteed source cleanup after success, failure, or timeout.
- Active conversion limiter.
- Pending queue guard.
- 5-minute conversion timeout.
- Common error shape from `docs/api_reference.md`.
- User ownership checks on every conversion endpoint.

Done when:

- Supported files convert to Markdown.
- Source files are deleted in all outcomes.
- `.md` output is stored in Supabase Storage.
- Conversion status updates correctly.
- Swagger UI at `/docs` clearly shows request/response models.
- Users cannot access another user's conversions or outputs.

## Sprint 3: Authenticated Frontend Shell

Goal: Create the minimal, premium app surface.

Build:

- Supabase login screen.
- Protected routes.
- App shell with header, product name, user context, and sign out.
- Design tokens from `DESIGN.md`.
- Base UI components: button, input, badge, progress/status, empty state.
- API client with authenticated requests to FastAPI.

Done when:

- User can sign in and reach the dashboard.
- Signed-out users are redirected to login.
- UI uses sans-serif typography only.
- UI follows the minimal, calm, low-clutter design direction.
- Buttons, focus states, labels, and empty states follow `DESIGN.md`.

## Sprint 4: Upload, Status, Preview, Download

Goal: Complete the main user workflow.

Build:

- Upload dropzone.
- Upload validation feedback.
- Conversion status display.
- Polling for status.
- Markdown preview.
- Copy Markdown action.
- Download `.md` action.
- Clear error messages.
- Trust note that source files are deleted after conversion, failure, or timeout, kept brief and non-promotional.

Done when:

- A user can upload a file, wait for processing, preview Markdown, copy it, and download the `.md` file.
- Failed, pending, processing, and completed states are clear.
- Queue-full and file-too-large errors are understandable.
- The main dashboard is not busy and does not use unnecessary cards or decorative metrics.

## Sprint 5: History And Finish Pass

Goal: Add history and harden the MVP.

Build:

- Conversion history list/table.
- Conversion detail page.
- Delete conversion action.
- Empty states.
- Loading states.
- Accessibility pass.
- Responsive pass.
- Basic backend tests.
- Frontend lint/build verification.
- End-to-end local conversion check.
- Final storage/security check against `docs/storage_and_security.md`.

Done when:

- Users can find previous conversions.
- Users can delete generated Markdown outputs.
- The app works on desktop and mobile-width layouts.
- Backend tests pass.
- Frontend build passes.
- No source documents persist after conversion.
- The implementation matches the PRD, architecture, data model, API reference, environment config, storage/security doc, Product context, and Design context.

## Not In These Sprints

- Admin dashboard.
- Cloudflare R2.
- Redis or external queue.
- Billing.
- Team management.
- OCR.
- Markdown search.
- Permanent source file storage.
