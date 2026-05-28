from datetime import UTC, datetime
from pydantic import BaseModel, Field
from typing import Literal

from app.models import ConversionRecord, ConversionStatus


class InMemoryUserProfile(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: str = "user"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InMemoryConversionRepository:
    def __init__(self) -> None:
        self._records: dict[str, ConversionRecord] = {}
        self.logs: list[tuple[str, str, str]] = []
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

    def count_user_files(self, user_id: str) -> int:
        return sum(1 for r in self._records.values() if r.user_id == user_id and r.status != "DELETED")

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

    # Admin methods for conversions and logs
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
        # Convert raw tuple logs (conversion_id, level, message) into dicts for easy display
        # Match search in message or conversion_id
        logs_list = []
        for conv_id, lvl, msg in self.logs:
            if level and lvl != level:
                continue
            if search:
                q = search.lower()
                if q not in msg.lower() and q not in conv_id.lower():
                    continue
            
            # Find user ID from record
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

