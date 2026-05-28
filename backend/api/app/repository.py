from datetime import UTC, datetime

from app.models import ConversionRecord, ConversionStatus


class InMemoryConversionRepository:
    def __init__(self) -> None:
        self._records: dict[str, ConversionRecord] = {}
        self.logs: list[tuple[str, str, str]] = []

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
