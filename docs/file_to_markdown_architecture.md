# Architecture: File-to-Markdown Converter Dashboard

## 1. Final Architecture Summary

This system is a lightweight internal file-to-Markdown converter.

It uses a Next.js dashboard for the user interface, Supabase Auth for login, FastAPI on Railway for backend conversion, MarkItDown for file-to-Markdown conversion, Supabase Storage for Markdown `.md` output files, and Supabase Postgres for metadata/history.

The system does **not** permanently store uploaded source documents. Source files are deleted immediately after conversion, failure, or timeout.

---

## 2. Architecture Diagram

```txt
User Browser
   |
   v
Next.js Dashboard - Vercel
   |
   | Supabase login
   v
Supabase Auth
   |
   | JWT sent to backend
   v
FastAPI Backend - Railway
   |
   | temporary file save
   v
MarkItDown Conversion Engine
   |
   | output.md
   v
Supabase Storage
   |
   | metadata/status
   v
Supabase Postgres
```

---

## 3. Storage Architecture

### Source Documents

Source documents are temporary.

```txt
Uploaded to FastAPI
Stored temporarily in Railway /tmp
Converted using MarkItDown
Deleted immediately after conversion, failure, or timeout
```

Source documents are not stored in:

```txt
Cloudflare R2
Supabase Storage
Supabase Postgres
```

### Markdown Outputs

Markdown outputs are stored in:

```txt
Supabase Storage
```

Example path:

```txt
markdown-outputs/{user_id}/{conversion_id}/output.md
```

Supabase Storage is the recommended persistence layer for generated `.md` files. Supabase Postgres stores metadata and `markdown_storage_path`, not the full source document and not the full Markdown blob unless a future small-preview cache is explicitly added.

### Metadata

Metadata is stored in:

```txt
Supabase Postgres
```

Metadata includes:

```txt
conversion_id
user_id
original_file_name
file_type
file_size
status
markdown_storage_path
error_message
created_at
completed_at
```

---

## 4. Runtime Workflow

```txt
1. User logs in.
2. User uploads file.
3. FastAPI validates file.
4. FastAPI saves source file to /tmp.
5. FastAPI creates conversion metadata.
6. Conversion waits if active slots are full.
7. MarkItDown converts the file.
8. output.md is uploaded to Supabase Storage.
9. Source file is deleted after success, failure, or timeout.
10. Supabase Postgres is updated.
11. User previews/downloads Markdown.
```

---

## 5. Concurrency Model

MVP rule:

```txt
Max active conversions = 2-3
Max pending conversions = 10
PDF max size = 25 MB
Conversion timeout = 5 minutes
```

If 5 users convert together:

```txt
2-3 process immediately
2-3 wait
```

This avoids Railway CPU/RAM overload.

---

## 6. Infrastructure Table

| Component | Tool |
|---|---|
| Frontend | Next.js |
| Frontend Hosting | Vercel |
| Auth | Supabase Auth |
| Backend | FastAPI |
| Backend Hosting | Railway |
| Converter | MarkItDown |
| Output File Storage | Supabase Storage |
| Database | Supabase Postgres |
| Queue | None |
| Source File Storage | Temporary only |

---

## 7. Why No Cloudflare R2

Cloudflare R2 is not part of this product architecture.

For expected 10 MB PDFs, the backend can safely receive the file, convert it, and delete it.

If future scale requires external temporary source storage, use a Supabase-first option or another approved storage decision.

```txt
Files become very large
Upload traffic grows
Source files need to be stored temporarily outside Railway
Conversion must survive backend restarts
```

---

## 8. Final Architecture Decision

```txt
No permanent source document storage.
Delete source files immediately after conversion, failure, or timeout.
Store only Markdown `.md` outputs.
Use Supabase Storage for `.md` files.
Use Supabase Postgres for metadata and storage paths.
Use Railway temp storage only during conversion.
```

---

## 9. Security & Account Control Architecture

### CORS Security Layer
The FastAPI backend acts as an authenticated resource server. To prevent cross-origin request forgery (CSRF) and enforce browser-level security policies:
1. Every preflight request (`OPTIONS`) is handled by FastAPI CORSMiddleware.
2. Only requests originating from the configured `FRONTEND_ORIGIN` (or development local hosts) containing valid bearer JWT credentials are allowed to pass through to endpoints.

### Account Deletion Data Flow
To respect privacy and storage cleanliness, account deletion uses a coordinated cascade:
```txt
1. User clicks "Yes, delete my account" in Settings UI.
2. Next.js calls DELETE /auth/account route.
3. Backend fetches user's file conversion history.
4. Backend executes object deletion calls to Supabase Storage for all output.md objects.
5. Backend deletes the user's Profile record in Supabase Postgres.
6. Foreign key cascades (ON DELETE CASCADE) automatically drop all Conversions and Logs rows.
7. Backend issues an Admin API call to Supabase Auth using the service role key to delete the user credentials.
8. Client clears local cookies/tokens and redirects to /login.
```

