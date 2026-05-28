# PRD: File-to-Markdown Converter Dashboard

## 1. Product Summary

The product is a lightweight internal dashboard that allows authenticated users to upload documents and convert them into clean Markdown using a FastAPI backend powered by MarkItDown.

The system is designed for an internal team of around 20 users, with around 5 users possibly converting files at the same time. The main expected file type is a normal PDF around 10 MB.

The updated architecture does **not** store source documents permanently. Uploaded source files are used only temporarily during conversion and then deleted immediately after success, failure, or timeout. Only the generated Markdown output is stored.

---

## 2. Final MVP Architecture

```txt
Next.js Dashboard on Vercel
        |
Supabase Auth
        |
FastAPI Backend on Railway
        |
Temporary source file handling
        |
MarkItDown conversion
        |
Supabase Storage for Markdown `.md` outputs
        |
Supabase Postgres for metadata/history/status
```

---

## 3. Core Product Flow

```txt
1. User logs in using Supabase Auth.
2. User uploads a file from the Next.js dashboard.
3. File is sent to FastAPI backend on Railway.
4. FastAPI stores the source file temporarily.
5. FastAPI runs MarkItDown conversion.
6. Generated Markdown is saved to Supabase Storage.
7. Source file is deleted immediately after conversion, failure, or timeout.
8. Conversion metadata is saved in Supabase Postgres.
9. User previews, copies, or downloads the Markdown output.
```

---

## 4. Key Storage Decision

### Source Documents

Source documents will **not** be permanently stored.

They will be:

```txt
Uploaded to FastAPI
Stored temporarily during conversion
Deleted immediately after conversion, failure, or timeout
```

This keeps the system lightweight, safer, and cheaper.

### Markdown Output Files

Markdown output files will be stored in:

```txt
Supabase Storage
```

Recommended bucket:

```txt
markdown-outputs
```

Postgres should store metadata and the storage path only. The full Markdown file should live in Supabase Storage so downloads, signed URLs, retention, and deletion stay simple.

### Metadata

Metadata will be stored in:

```txt
Supabase Postgres
```

Metadata includes:

```txt
user_id
file_name
file_type
file_size
conversion_status
markdown_storage_path
error_message
created_at
completed_at
```

---

## 5. Why This Is Better for MVP

This approach avoids unnecessary object storage complexity for source files.

It is better because:

```txt
No Cloudflare R2 dependency
No permanent storage of user source documents
Simpler upload workflow
Lower storage risk
Easier privacy story
Enough for 10 MB PDFs
Clean Supabase-only persistence layer
```

---

## 6. Final Infrastructure

| Layer | Tool | Purpose |
|---|---|---|
| Frontend | Next.js | Dashboard, upload UI, preview UI |
| Frontend Hosting | Vercel | Host frontend |
| Auth | Supabase Auth | Login and users |
| Backend | FastAPI | API and conversion control |
| Backend Hosting | Railway | Host FastAPI |
| Converter | MarkItDown | Convert files to Markdown |
| Output Storage | Supabase Storage | Store generated `.md` files |
| Database | Supabase Postgres | Store metadata, status, history |
| Queue | None in MVP | Not needed yet |
| Concurrency Control | In-app limiter | Prevent backend overload |

---

## 7. What We Are Not Using in MVP

```txt
Cloudflare R2
BullMQ
Redis
Docker Compose
Microservices
Browser-only conversion
Permanent source file storage
Postgres file storage
```

---

## 8. Recommended Limits

| Limit Type | MVP Limit |
|---|---:|
| Total users | ~20 |
| Simultaneous converting users | ~5 submissions |
| Active conversions | 2-3 at a time |
| Pending conversions | 10 |
| PDF file size | 25 MB max |
| Typical PDF size | ~10 MB |
| Max conversion timeout | 5 minutes |
| Files per upload batch | 1-3 |
| Original file retention | Delete immediately after conversion, failure, or timeout |
| Markdown output retention | 7-30 days |

---

## 9. Concurrency Behavior

If 5 users convert files together:

```txt
2-3 conversions start immediately
Remaining submissions wait in PENDING state
When one finishes, the next starts
```

This prevents Railway from crashing.

---

## 10. Supported MVP File Types

```txt
PDF
DOCX
PPTX
XLSX
CSV
TXT
HTML
```

Recommended first release focus:

```txt
PDF
DOCX
TXT
HTML
CSV
```

---

## 11. Conversion Statuses

```txt
UPLOAD_RECEIVED
PENDING
PROCESSING
COMPLETED
FAILED
DELETED
```

| Status | Meaning |
|---|---|
| `UPLOAD_RECEIVED` | Backend received uploaded source file |
| `PENDING` | File is waiting for an available conversion slot |
| `PROCESSING` | File is being converted |
| `COMPLETED` | Markdown was generated successfully |
| `FAILED` | Conversion failed |
| `DELETED` | Conversion record/output was deleted |

---

## 12. Database Schema

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

---

## 13. API Endpoints

```txt
GET /auth/me

POST /conversions
GET /conversions
GET /conversions/{id}
GET /conversions/{id}/status
GET /conversions/{id}/download-url
POST /conversions/{id}/retry
DELETE /conversions/{id}
```

---

## 14. Main API Flow

### POST /conversions

Purpose:

```txt
Upload source file, convert it, store Markdown output, delete source file after success, failure, or timeout.
```

Flow:

```txt
1. Verify Supabase JWT.
2. Validate file type and size.
3. Save source file temporarily.
4. Create conversion record in Supabase Postgres.
5. If conversion slot is available, process immediately.
6. Run MarkItDown.
7. Save output.md to Supabase Storage.
8. Delete temporary source file.
9. Update status to COMPLETED.
10. Return conversion ID and preview/download details.
```

---

## 15. File Handling Rules

Source files:

```txt
Temporary only
Never permanently stored
Deleted after conversion
Deleted on failure
Deleted on timeout
```

Markdown outputs:

```txt
Stored in Supabase Storage
Linked from Supabase Postgres
Downloadable by owner
Can be deleted by user
```

Temporary folder example on Railway:

```txt
/tmp/conversions/{conversion_id}/input.pdf
/tmp/conversions/{conversion_id}/output.md
```

Supabase Storage path:

```txt
markdown-outputs/{user_id}/{conversion_id}/output.md
```

---

## 16. Security Requirements

The system must:

```txt
Require login
Verify Supabase JWT in FastAPI
Validate file size
Validate file type
Validate MIME type
Delete source file after conversion, failure, or timeout
Store only Markdown output
Ensure users only access their own conversions
Use signed download URLs for Markdown output
Never expose Supabase service key to frontend
```

---

## 17. Performance Expectations

For normal 10 MB PDFs:

```txt
Expected conversion time: 5-30 seconds
```

For heavier PDFs:

```txt
Expected conversion time: 30-90 seconds
```

Worst case:

```txt
Up to 5 minutes before timeout
```

---

## 18. Success Metrics

The MVP is successful if:

```txt
20 internal users can log in and use it
5 users can submit conversions together without crashing the backend
Normal 10 MB PDFs convert in 5-30 seconds
Only Markdown outputs are stored permanently
Source documents are deleted after conversion, failure, or timeout
Users can preview, copy, and download Markdown
```

---

## 19. Future Upgrade Path

Add external source file storage only if:

```txt
File sizes become too large for Railway upload handling
Conversions need to survive backend restarts
Batch files become common
Users need to re-convert originals later
Compliance requires source archive
```

Possible future storage options:

```txt
Supabase Storage for temporary source files
S3-compatible storage
```

Add queue only if:

```txt
More than 5 users frequently convert together
Conversions regularly take several minutes
Reliable retry/background processing becomes necessary
```

Future architecture if needed:

```txt
Next.js
   |
FastAPI API
   |
Redis/BullMQ or job queue
   |
Worker service
   |
MarkItDown
   |
Supabase Storage
   |
Supabase Postgres
```

---

## 20. Final Decision

The MVP will use:

```txt
Next.js on Vercel
Supabase Auth
FastAPI on Railway
MarkItDown
Supabase Storage for Markdown `.md` outputs
Supabase Postgres for metadata
Temporary source file handling only
In-app concurrency limiter
```

The MVP will not permanently store uploaded source documents.

Final product behavior:

```txt
User uploads document
Backend converts it
Markdown output is saved
Original document is deleted
User previews/copies/downloads Markdown
```
