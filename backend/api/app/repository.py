from datetime import UTC, datetime
from pydantic import BaseModel, Field
from typing import Literal
import httpx

from app.models import ConversionRecord, ConversionStatus


class InMemoryUserProfile(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: str = "user"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SupabaseConversionRepository:
    def __init__(self, supabase_url: str, service_role_key: str) -> None:
        self.supabase_url = supabase_url.rstrip("/")
        self.service_role_key = service_role_key
        self.headers = {
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self.client = httpx.Client(headers=self.headers, timeout=10.0)

    def _count(self, table: str, params: dict[str, str] | None = None) -> int:
        headers = {**self.headers, "Prefer": "count=exact"}
        res = self.client.get(
            f"{self.supabase_url}/rest/v1/{table}",
            headers=headers,
            params={**(params or {}), "select": "id", "limit": "1"},
        )
        res.raise_for_status()
        content_range = res.headers.get("Content-Range", "")
        if "/" not in content_range:
            return 0
        total = content_range.rsplit("/", 1)[-1]
        return int(total) if total.isdigit() else 0

    def count_users(self) -> int:
        return self._count("profiles")

    def count_conversions(
        self,
        *,
        status: str | None = None,
        completed_from: datetime | None = None,
    ) -> int:
        params = {"status": "neq.DELETED"}
        if status:
            params["status"] = f"eq.{status}"
        if completed_from is not None:
            params["completed_at"] = f"gte.{completed_from.isoformat()}"
        return self._count("conversions", params)

    def create_user(
        self,
        user_id: str,
        email: str,
        full_name: str | None = None,
        role: str = "user"
    ) -> InMemoryUserProfile:
        payload = {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "role": role,
            "is_active": True
        }
        res = self.client.post(f"{self.supabase_url}/rest/v1/profiles", json=payload)
        res.raise_for_status()
        data = res.json()
        return InMemoryUserProfile(**data[0])

    def get_user(self, user_id: str) -> InMemoryUserProfile | None:
        res = self.client.get(f"{self.supabase_url}/rest/v1/profiles?id=eq.{user_id}")
        res.raise_for_status()
        data = res.json()
        if not data:
            return None
        return InMemoryUserProfile(**data[0])

    def get_user_by_email(self, email: str) -> InMemoryUserProfile | None:
        res = self.client.get(f"{self.supabase_url}/rest/v1/profiles?email=eq.{email}")
        res.raise_for_status()
        data = res.json()
        if not data:
            return None
        return InMemoryUserProfile(**data[0])

    def get_users_by_ids(self, user_ids: set[str]) -> dict[str, InMemoryUserProfile]:
        if not user_ids:
            return {}
        res = self.client.get(
            f"{self.supabase_url}/rest/v1/profiles",
            params={
                "id": f"in.({','.join(sorted(user_ids))})",
                "select": "id,email,full_name,role,is_active,created_at,updated_at",
            },
        )
        res.raise_for_status()
        profiles = [InMemoryUserProfile(**item) for item in res.json()]
        return {profile.id: profile for profile in profiles}

    def list_users(
        self,
        *,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[InMemoryUserProfile]:
        url = f"{self.supabase_url}/rest/v1/profiles?order=created_at.desc&limit={limit}&offset={offset}"
        if search:
            url += f"&or=(email.ilike.*{search}*,full_name.ilike.*{search}*)"
        res = self.client.get(url)
        res.raise_for_status()
        return [InMemoryUserProfile(**item) for item in res.json()]

    def update_user_status(self, user_id: str, is_active: bool) -> InMemoryUserProfile | None:
        payload = {"is_active": is_active, "updated_at": datetime.now(UTC).isoformat()}
        res = self.client.patch(f"{self.supabase_url}/rest/v1/profiles?id=eq.{user_id}", json=payload)
        res.raise_for_status()
        data = res.json()
        if not data:
            return None
        return InMemoryUserProfile(**data[0])

    def update_user_role(self, user_id: str, role: str) -> InMemoryUserProfile | None:
        payload = {"role": role, "updated_at": datetime.now(UTC).isoformat()}
        res = self.client.patch(f"{self.supabase_url}/rest/v1/profiles?id=eq.{user_id}", json=payload)
        res.raise_for_status()
        data = res.json()
        if not data:
            return None
        return InMemoryUserProfile(**data[0])

    def update_user_profile(self, user_id: str, full_name: str) -> InMemoryUserProfile | None:
        payload = {"full_name": full_name, "updated_at": datetime.now(UTC).isoformat()}
        res = self.client.patch(f"{self.supabase_url}/rest/v1/profiles?id=eq.{user_id}", json=payload)
        res.raise_for_status()
        data = res.json()
        if not data:
            return None
        return InMemoryUserProfile(**data[0])

    def delete_user(self, user_id: str) -> bool:
        res = self.client.delete(f"{self.supabase_url}/rest/v1/profiles?id=eq.{user_id}")
        res.raise_for_status()
        return True

    def count_user_files(self, user_id: str) -> int:
        headers = {**self.headers, "Prefer": "count=exact"}
        res = self.client.get(
            f"{self.supabase_url}/rest/v1/conversions?user_id=eq.{user_id}&status=neq.DELETED&limit=1",
            headers=headers
        )
        res.raise_for_status()
        content_range = res.headers.get("Content-Range")
        if content_range and "/" in content_range:
            return int(content_range.split("/")[-1])
        return 0

    def log_feature_usage(self, user_id: str, feature: str, model: str, tokens: int) -> None:
        payload = {
            "user_id": user_id,
            "feature": feature,
            "model": model,
            "tokens": tokens,
        }
        res = self.client.post(f"{self.supabase_url}/rest/v1/feature_usage", json=payload)
        res.raise_for_status()

    def get_user_tokens(self, user_id: str, feature: str = "ocr") -> int:
        res = self.client.get(
            f"{self.supabase_url}/rest/v1/feature_usage",
            params={
                "user_id": f"eq.{user_id}",
                "feature": f"eq.{feature}",
                "select": "tokens",
            },
        )
        res.raise_for_status()
        return sum(int(item.get("tokens") or 0) for item in res.json())

    def create_upload_received(
        self,
        *,
        user_id: str,
        original_file_name: str,
        file_type: str,
        mime_type: str | None,
        file_size_bytes: int,
    ) -> ConversionRecord:
        record = ConversionRecord(
            user_id=user_id,
            original_file_name=original_file_name,
            file_type=file_type,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            status="UPLOAD_RECEIVED",
        )
        payload = record.model_dump(mode="json")
        res = self.client.post(f"{self.supabase_url}/rest/v1/conversions", json=payload)
        res.raise_for_status()
        self.add_log(record.id, "info", "Upload received.")
        return record

    def list_for_user(
        self,
        user_id: str,
        *,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ConversionRecord]:
        url = f"{self.supabase_url}/rest/v1/conversions?user_id=eq.{user_id}&order=created_at.desc&limit={limit}&offset={offset}"
        if status:
            url += f"&status=eq.{status}"
        res = self.client.get(url)
        res.raise_for_status()
        return [ConversionRecord(**item) for item in res.json()]

    def get_for_user(self, conversion_id: str, user_id: str) -> ConversionRecord | None:
        res = self.client.get(f"{self.supabase_url}/rest/v1/conversions?id=eq.{conversion_id}&user_id=eq.{user_id}")
        res.raise_for_status()
        data = res.json()
        if not data:
            return None
        return ConversionRecord(**data[0])

    def update_status(
        self,
        conversion_id: str,
        status: ConversionStatus,
        *,
        markdown_storage_path: str | None = None,
        error_message: str | None = None,
    ) -> ConversionRecord | None:
        now = datetime.now(UTC).isoformat()
        payload = {"status": status, "updated_at": now}
        if status == "PROCESSING":
            payload["started_at"] = now
        if status in {"COMPLETED", "FAILED", "DELETED"}:
            payload["completed_at"] = now
        if markdown_storage_path is not None:
            payload["markdown_storage_path"] = markdown_storage_path
        if error_message is not None:
            payload["error_message"] = error_message

        res = self.client.patch(f"{self.supabase_url}/rest/v1/conversions?id=eq.{conversion_id}", json=payload)
        res.raise_for_status()
        data = res.json()
        if not data:
            return None

        self.add_log(conversion_id, "error" if status == "FAILED" else "info", f"Status changed to {status}.")
        return ConversionRecord(**data[0])

    def add_log(self, conversion_id: str, level: str, message: str) -> None:
        payload = {
            "conversion_id": conversion_id,
            "level": level,
            "message": message
        }
        res = self.client.post(f"{self.supabase_url}/rest/v1/conversion_logs", json=payload)
        res.raise_for_status()

    def list_all_conversions(
        self,
        *,
        status: str | None = None,
        user_id: str | None = None,
        file_type: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[ConversionRecord]:
        url = f"{self.supabase_url}/rest/v1/conversions?order=created_at.desc&limit={limit}&offset={offset}"
        if status:
            url += f"&status=eq.{status}"
        if user_id:
            url += f"&user_id=eq.{user_id}"
        if file_type:
            url += f"&file_type=eq.{file_type}"
        if search:
            url += f"&original_file_name.ilike.*{search}*"
        res = self.client.get(url)
        res.raise_for_status()
        return [ConversionRecord(**item) for item in res.json()]

    def list_all_logs(
        self,
        *,
        level: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[dict]:
        url = f"{self.supabase_url}/rest/v1/conversion_logs?order=created_at.desc&limit={limit}&offset={offset}"
        if level:
            url += f"&level=eq.{level}"
        if search:
            url += f"&message.ilike.*{search}*"
        res = self.client.get(url)
        res.raise_for_status()
        items = res.json()
        
        if items:
            conv_ids = list({item["conversion_id"] for item in items})
            # Postgrest has in query syntax: id=in.(id1,id2,...)
            conv_res = self.client.get(f"{self.supabase_url}/rest/v1/conversions?id=in.({','.join(conv_ids)})")
            conv_res.raise_for_status()
            conv_map = {c["id"]: c["user_id"] for c in conv_res.json()}
            for item in items:
                item["user_id"] = conv_map.get(item["conversion_id"], "unknown")
                item["created_at"] = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
                
        return items


class InMemoryConversionRepository:
    def __init__(self) -> None:
        self._records: dict[str, ConversionRecord] = {}
        self.logs: list[tuple[str, str, str]] = []
        self.feature_usage: list[dict] = []
        self._profiles: dict[str, InMemoryUserProfile] = {}
        
        # Seed dummy dev and admin accounts
        self.create_user(
            user_id="11111111-1111-4111-8111-111111111111",
            email="dev@local.test",
            full_name="Local Developer",
            role="user"
        )
        self.create_user(
            user_id="22222222-2222-4222-8222-222222222222",
            email="admin@local.test",
            full_name="Local Admin",
            role="admin"
        )

    def create_user(
        self,
        user_id: str,
        email: str,
        full_name: str | None = None,
        role: str = "user"
    ) -> InMemoryUserProfile:
        profile = InMemoryUserProfile(
            id=user_id,
            email=email,
            full_name=full_name,
            role=role,
            is_active=True
        )
        self._profiles[user_id] = profile
        return profile

    def get_user(self, user_id: str) -> InMemoryUserProfile | None:
        return self._profiles.get(user_id)

    def get_user_by_email(self, email: str) -> InMemoryUserProfile | None:
        for profile in self._profiles.values():
            if profile.email.lower() == email.lower():
                return profile
        return None

    def get_users_by_ids(self, user_ids: set[str]) -> dict[str, InMemoryUserProfile]:
        return {
            user_id: profile
            for user_id, profile in self._profiles.items()
            if user_id in user_ids
        }

    def list_users(
        self,
        *,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[InMemoryUserProfile]:
        users = list(self._profiles.values())
        if search:
            q = search.lower()
            users = [
                u for u in users
                if q in u.email.lower() or (u.full_name and q in u.full_name.lower())
            ]
        users.sort(key=lambda u: u.created_at, reverse=True)
        return users[offset : offset + limit]

    def update_user_status(self, user_id: str, is_active: bool) -> InMemoryUserProfile | None:
        profile = self._profiles.get(user_id)
        if not profile:
            return None
        profile.is_active = is_active
        profile.updated_at = datetime.now(UTC)
        return profile

    def update_user_role(self, user_id: str, role: str) -> InMemoryUserProfile | None:
        profile = self._profiles.get(user_id)
        if not profile:
            return None
        profile.role = role
        profile.updated_at = datetime.now(UTC)
        return profile

    def update_user_profile(self, user_id: str, full_name: str) -> InMemoryUserProfile | None:
        profile = self._profiles.get(user_id)
        if not profile:
            return None
        profile.full_name = full_name
        profile.updated_at = datetime.now(UTC)
        return profile

    def delete_user(self, user_id: str) -> bool:
        if user_id in self._profiles:
            del self._profiles[user_id]
            # cascade delete conversions
            self._records = {k: v for k, v in self._records.items() if v.user_id != user_id}
            return True
        return False

    def count_user_files(self, user_id: str) -> int:
        return sum(1 for r in self._records.values() if r.user_id == user_id and r.status != "DELETED")

    def log_feature_usage(self, user_id: str, feature: str, model: str, tokens: int) -> None:
        self.feature_usage.append(
            {
                "user_id": user_id,
                "feature": feature,
                "model": model,
                "tokens": tokens,
                "created_at": datetime.now(UTC),
            }
        )

    def get_user_tokens(self, user_id: str, feature: str = "ocr") -> int:
        return sum(
            int(item["tokens"])
            for item in self.feature_usage
            if item["user_id"] == user_id and item["feature"] == feature
        )

    def count_users(self) -> int:
        return len(self._profiles)

    def count_conversions(
        self,
        *,
        status: str | None = None,
        completed_from: datetime | None = None,
    ) -> int:
        records = [record for record in self._records.values() if record.status != "DELETED"]
        if status:
            records = [record for record in self._records.values() if record.status == status]
        if completed_from is not None:
            records = [
                record
                for record in records
                if record.completed_at and record.completed_at >= completed_from
            ]
        return len(records)

    def create_upload_received(
        self,
        *,
        user_id: str,
        original_file_name: str,
        file_type: str,
        mime_type: str | None,
        file_size_bytes: int,
    ) -> ConversionRecord:
        record = ConversionRecord(
            user_id=user_id,
            original_file_name=original_file_name,
            file_type=file_type,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            status="UPLOAD_RECEIVED",
        )
        self._records[record.id] = record
        self.add_log(record.id, "info", "Upload received.")
        return record

    def list_for_user(
        self,
        user_id: str,
        *,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ConversionRecord]:
        records = [record for record in self._records.values() if record.user_id == user_id]
        if status:
            records = [record for record in records if record.status == status]
        records.sort(key=lambda item: item.created_at, reverse=True)
        return records[offset : offset + limit]

    def get_for_user(self, conversion_id: str, user_id: str) -> ConversionRecord | None:
        record = self._records.get(conversion_id)
        if not record or record.user_id != user_id:
            return None
        return record

    def update_status(
        self,
        conversion_id: str,
        status: ConversionStatus,
        *,
        markdown_storage_path: str | None = None,
        error_message: str | None = None,
    ) -> ConversionRecord | None:
        record = self._records.get(conversion_id)
        if not record:
            return None

        now = datetime.now(UTC)
        update = {"status": status, "updated_at": now}
        if status == "PROCESSING":
            update["started_at"] = now
        if status in {"COMPLETED", "FAILED", "DELETED"}:
            update["completed_at"] = now
        if markdown_storage_path is not None:
            update["markdown_storage_path"] = markdown_storage_path
        if error_message is not None:
            update["error_message"] = error_message

        updated = record.model_copy(update=update)
        self._records[conversion_id] = updated
        self.add_log(conversion_id, "error" if status == "FAILED" else "info", f"Status changed to {status}.")
        return updated

    def add_log(self, conversion_id: str, level: str, message: str) -> None:
        self.logs.append((conversion_id, level, message))

    def list_all_conversions(
        self,
        *,
        status: str | None = None,
        user_id: str | None = None,
        file_type: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[ConversionRecord]:
        records = list(self._records.values())
        if status:
            records = [r for r in records if r.status == status]
        if user_id:
            records = [r for r in records if r.user_id == user_id]
        if file_type:
            records = [r for r in records if r.file_type == file_type]
        if search:
            q = search.lower()
            records = [r for r in records if q in r.original_file_name.lower()]
        
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records[offset : offset + limit]

    def list_all_logs(
        self,
        *,
        level: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[dict]:
        logs_list = []
        for conv_id, lvl, msg in self.logs:
            if level and lvl != level:
                continue
            if search:
                q = search.lower()
                if q not in msg.lower() and q not in conv_id.lower():
                    continue
            
            rec = self._records.get(conv_id)
            user_id = rec.user_id if rec else "unknown"
            
            logs_list.append({
                "conversion_id": conv_id,
                "user_id": user_id,
                "level": lvl,
                "message": msg,
                "created_at": rec.updated_at if rec else datetime.now(UTC)
            })
            
        logs_list.sort(key=lambda l: l["created_at"], reverse=True)
        return logs_list[offset : offset + limit]
