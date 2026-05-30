Here is the full content of the implementation plan:

```markdown
# Implementation Plan: LLM-Based OCR Integration & Token Tracking

This plan outlines the changes required to wire up the local `markitdown-ocr` package into the active FastAPI backend, implement token usage tracking in Postgres, and display token consumption stats inside the admin portal.

---

## User Review Required

> [!IMPORTANT]
> - **OpenAI Key Dependency:** A valid `OPENAI_API_KEY` must be configured in the environment variables (e.g. on Railway) for the OCR system to call the LLM vision model (`gpt-4o-mini`).
> - **OCR Fallback:** If `OPENAI_API_KEY` is not present (or when developing locally with the mock repository), conversion runs offline using the standard text extractors, skipping OCR without crashing.
> - **Database Changes:** We will introduce a new `feature_usage` table in Supabase Postgres to track token consumption.

---

## Proposed Changes

### 1. Database Schema (`docs/data_models.md`)
We will create a new table `feature_usage` to store raw token usage transactions. This allows detailed tracking per user, model, and feature (extensible to non-OCR features in the future).

#### [MODIFY] [data_models.md](file:///d:/Chlear%20Projects/Markdown%20IT%20Project/Markdown%20Dashboard/markdown-it-master/docs/data_models.md)
Add the description of the `feature_usage` table and SQL schema:
```sql
CREATE TABLE feature_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    feature TEXT NOT NULL, -- 'ocr'
    model TEXT NOT NULL, -- 'gpt-4o-mini'
    tokens INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast user aggregation
CREATE INDEX feature_usage_user_idx ON feature_usage (user_id);
```

---

### 2. Database Repositories (`backend/api/app/repository.py`)
Implement the interfaces to save and retrieve token transactions in both the persistent (Supabase) and in-memory mock repositories.

#### [MODIFY] [repository.py](file:///d:/Chlear%20Projects/Markdown%20IT%20Project/Markdown%20Dashboard/markdown-it-master/backend/api/app/repository.py)
* **`SupabaseConversionRepository`:**
  * Add `log_feature_usage(self, user_id: str, feature: str, model: str, tokens: int) -> None` to run a `POST` request inserting a row into `feature_usage`.
  * Add `get_user_tokens(self, user_id: str, feature: str = "ocr") -> int` to query and sum all token usage rows matching the `user_id` and `feature`.
* **`InMemoryConversionRepository`:**
  * Add a `self.feature_usage: list[dict]` list inside constructor.
  * Implement `log_feature_usage` (append to list) and `get_user_tokens` (return sum of matching list items).
* **`list_users`:** Update `InMemoryUserProfile` or responses to support returned tokens.

---

### 3. Schema Models & API Endpoints (`backend/api/app/models.py` & `main.py`)
Expose user token counts in the admin users list.

#### [MODIFY] [models.py](file:///d:/Chlear%20Projects/Markdown%20IT%20Project/Markdown%20Dashboard/markdown-it-master/backend/api/app/models.py)
* Add `ocr_tokens_consumed: int = 0` to the `AdminUserProfileResponse` Pydantic model.

#### [MODIFY] [main.py](file:///d:/Chlear%20Projects/Markdown%20IT%20Project/Markdown%20Dashboard/markdown-it-master/backend/api/app/main.py)
* In `/admin/users` GET route (`list_admin_users`), populate `ocr_tokens_consumed` for each profile row by calling `repo.get_user_tokens(p.id)`.

---

### 4. Custom OCR Service (`backend/api/app/ocr_service.py`)
Create a custom OCR class that overrides `LLMVisionOCRService` to enforce the customized prompt, deterministic temperature (`0`), maximum tokens (`4096`), and dynamic user header tags, while logging usage directly back to the database.

#### [NEW] [ocr_service.py](file:///d:/Chlear%20Projects/Markdown%20IT%20Project/Markdown%20Dashboard/markdown-it-master/backend/api/app/ocr_service.py)
* Inherits from `LLMVisionOCRService` in the `markitdown_ocr` package.
* Inside `extract_text`, convert the image stream to base64, issue the chat completion call to `gpt-4o-mini` with the customized prompt, and write token counts to `repository.log_feature_usage`.

---

### 5. Conversion Wiring (`backend/api/app/conversion_service.py` & `services.py`)
Integrate the local OCR library and wire the dynamic service call.

#### [MODIFY] [conversion_service.py](file:///d:/Chlear%20Projects/Markdown%20IT%20Project/Markdown%20Dashboard/markdown-it-master/backend/api/app/conversion_service.py)
* Update `_ensure_local_markitdown_on_path` to inject the `markitdown-ocr/src` source path into `sys.path`.
* Update `warm_converter` to import `markitdown_ocr` and instantiate `MarkItDown(enable_plugins=True)`.
* Adjust `convert_file_to_markdown` signature to accept `user_id` and `repository` arguments. If credentials exist, initialize the custom OCR service and supply it as `ocr_service` in the `convert` call.

#### [MODIFY] [services.py](file:///d:/Chlear%20Projects/Markdown%20IT%20Project/Markdown%20Dashboard/markdown-it-master/backend/api/app/services.py)
* In `_process_immediately`, pass `record.user_id` and `self.repository` into `self.convert()`.

#### [MODIFY] [requirements.txt](file:///d:/Chlear%20Projects/Markdown%20IT%20Project/Markdown%20Dashboard/markdown-it-master/backend/api/requirements.txt)
* Add `openai` package dependency.

---

### 6. Frontend Admin Dashboard (`frontend/app/(app)/admin/users/page.tsx`)
Display the OCR tokens consumed column in the user management interface.

#### [MODIFY] [page.tsx](file:///d:/Chlear%20Projects/Markdown%20IT%20Project/Markdown%20Dashboard/markdown-it-master/frontend/app/(app)/admin/users/page.tsx)
* Update `UserProfile` type to declare `ocr_tokens_consumed: number`.
* Insert an `OCR Tokens` header column (`<th>`) and render `{user.ocr_tokens_consumed.toLocaleString()}` cell values in the table mapping.

---

## Verification Plan

### 1. Database Migrations
* Apply the SQL table creation script to Supabase Postgres schema.

### 2. Backend Compilation & Unit Testing
* Execute backend testing scripts to verify local conversion logic is working.
* Validate repository models with mock `InMemoryConversionRepository` records.

### 3. Frontend Build Validation
* Run `npm run build` in the `frontend` directory to ensure type declarations are correctly resolved.
```