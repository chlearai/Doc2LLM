# Data Models

## Purpose

This document defines the application data model for the Doc2LLM dashboard.

The database stores users, conversion metadata, and conversion logs. It does not store uploaded source documents and does not store source document binary data.

Generated Markdown output files are stored in Supabase Storage. Supabase Postgres stores the storage path and metadata only.

## Tables

### profiles

Stores application profile data for authenticated Supabase users.

```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Fields:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Matches `auth.users.id`. |
| `email` | TEXT | Yes | Copied from Supabase Auth. |
| `full_name` | TEXT | No | Optional display name. |
| `role` | TEXT | Yes | MVP uses `user`. Admin dashboard comes later. |
| `created_at` | TIMESTAMPTZ | Yes | Creation timestamp. |
| `updated_at` | TIMESTAMPTZ | Yes | Last update timestamp. |

### conversions

Stores one row per uploaded conversion request.

```sql
CREATE TABLE conversions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    original_file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    mime_type TEXT,
    file_size_bytes BIGINT NOT NULL,
    file_size_mb NUMERIC GENERATED ALWAYS AS (round((file_size_bytes::numeric / 1048576), 2)) STORED,
    markdown_storage_path TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT conversions_status_check CHECK (
        status IN ('UPLOAD_RECEIVED', 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'DELETED')
    )
);
```

Fields:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Conversion ID used by API and storage path. |
| `user_id` | UUID | Yes | Owner of the conversion. |
| `original_file_name` | TEXT | Yes | Original client filename only, not a storage path. |
| `file_type` | TEXT | Yes | Normalized extension: `pdf`, `docx`, `pptx`, `xlsx`, `csv`, `txt`, `html`. |
| `mime_type` | TEXT | No | MIME type reported by upload validation. |
| `file_size_bytes` | BIGINT | Yes | Raw upload size. |
| `file_size_mb` | NUMERIC | Yes | Generated size in MB for display. |
| `markdown_storage_path` | TEXT | No | Set only after Markdown upload succeeds. |
| `status` | TEXT | Yes | One of the allowed conversion statuses. |
| `error_message` | TEXT | No | Human-readable failure reason. |
| `started_at` | TIMESTAMPTZ | No | Set when processing begins. |
| `completed_at` | TIMESTAMPTZ | No | Set on completed, failed, or deleted terminal states. |
| `created_at` | TIMESTAMPTZ | Yes | Creation timestamp. |
| `updated_at` | TIMESTAMPTZ | Yes | Last update timestamp. |

Recommended indexes:

```sql
CREATE INDEX conversions_user_created_idx
ON conversions (user_id, created_at DESC);

CREATE INDEX conversions_user_status_idx
ON conversions (user_id, status);
```

### conversion_logs

Stores important lifecycle events for each conversion.

```sql
CREATE TABLE conversion_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversion_id UUID NOT NULL REFERENCES conversions(id) ON DELETE CASCADE,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT conversion_logs_level_check CHECK (
        level IN ('info', 'warning', 'error')
    )
);
```

Fields:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Log row ID. |
| `conversion_id` | UUID | Yes | Parent conversion. |
| `level` | TEXT | Yes | `info`, `warning`, or `error`. |
| `message` | TEXT | Yes | Internal lifecycle message. Do not store source content. |
| `created_at` | TIMESTAMPTZ | Yes | Creation timestamp. |

Recommended index:

```sql
CREATE INDEX conversion_logs_conversion_created_idx
ON conversion_logs (conversion_id, created_at ASC);
```

### feature_usage

Stores token usage transactions for model-backed features such as OCR. This table is append-only from the application point of view so admin usage totals can be aggregated without storing source files or Markdown output in Postgres.

```sql
CREATE TABLE feature_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    feature TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT feature_usage_tokens_check CHECK (tokens >= 0)
);
```

Fields:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | Yes | Usage row ID. |
| `user_id` | UUID | Yes | User whose conversion triggered the usage. |
| `feature` | TEXT | Yes | Feature name, currently `ocr`. |
| `model` | TEXT | Yes | Model name, currently `gpt-4o-mini`. |
| `tokens` | INTEGER | Yes | Total request tokens reported by the model provider. |
| `created_at` | TIMESTAMPTZ | Yes | Creation timestamp. |

Recommended indexes:

```sql
CREATE INDEX feature_usage_user_idx
ON feature_usage (user_id);

CREATE INDEX feature_usage_user_feature_idx
ON feature_usage (user_id, feature);
```

## Status Lifecycle

```txt
UPLOAD_RECEIVED
   |
   v
PENDING
   |
   v
PROCESSING
   |
   +--> COMPLETED
   |
   +--> FAILED

COMPLETED or FAILED
   |
   v
DELETED
```

Rules:

- `UPLOAD_RECEIVED` is used after backend accepts and validates the upload.
- `PENDING` is used when active conversion slots are full but queue capacity remains.
- `PROCESSING` is used while MarkItDown runs.
- `COMPLETED` means Markdown exists in Supabase Storage.
- `FAILED` means conversion failed or timed out. Source file must already be deleted.
- `DELETED` means the user deleted the conversion record/output.

## Storage Path Model

Generated Markdown files use this path:

```txt
markdown-outputs/{user_id}/{conversion_id}/output.md
```

Do not store source file paths in Postgres. Temporary source paths are runtime-only and must be deleted in backend cleanup logic.

## Admin Dashboard

Admin-specific models are not part of this MVP.

Do not add admin tables or role workflows until the admin dashboard is designed later.
