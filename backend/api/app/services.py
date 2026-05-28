from pathlib import Path
import asyncio
from collections.abc import Callable
import logging

from fastapi import UploadFile

from app.cleanup import remove_temp_tree
from app.conversion_service import convert_file_to_markdown
from app.errors import api_error
from app.limiter import ConversionLimiter
from app.models import ConversionRecord
from app.repository import InMemoryConversionRepository
from app.storage import InMemoryMarkdownStorage
from app.validators import validate_upload_metadata

logger = logging.getLogger(__name__)


class ConversionManager:
    def __init__(
        self,
        *,
        repository: InMemoryConversionRepository,
        storage: InMemoryMarkdownStorage,
        limiter: ConversionLimiter,
        temp_root: Path,
        timeout_seconds: int = 300,
        convert: Callable[[Path], str] | None = None,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.limiter = limiter
        self.temp_root = temp_root
        self.timeout_seconds = timeout_seconds
        self.convert = convert or convert_file_to_markdown

    @classmethod
    def for_tests(
        cls,
        *,
        temp_root: Path,
        convert: Callable[[Path], str] | None = None,
    ) -> "ConversionManager":
        return cls(
            repository=InMemoryConversionRepository(),
            storage=InMemoryMarkdownStorage(),
            limiter=ConversionLimiter(max_active=2, max_pending=10),
            temp_root=temp_root,
            timeout_seconds=300,
            convert=convert,
        )

    async def create_conversion(self, *, user_id: str, file: UploadFile) -> ConversionRecord:
        content = await file.read()
        metadata = validate_upload_metadata(
            filename=file.filename or "",
            content_type=file.content_type,
            size_bytes=len(content),
        )
        record = self.repository.create_upload_received(
            user_id=user_id,
            original_file_name=file.filename or "upload",
            file_type=metadata.file_type,
            mime_type=file.content_type,
            file_size_bytes=metadata.size_bytes,
        )

        slot = self.limiter.reserve_slot()
        if slot is None:
            self.repository.update_status(record.id, "FAILED", error_message="Queue is full.")
            raise api_error(429, "QUEUE_FULL", "Too many files are waiting right now. Try again in a few minutes.")

        if slot == "PENDING":
            return self.repository.update_status(record.id, "PENDING") or record

        return await self._process_immediately(record, content)

    async def _process_immediately(self, record: ConversionRecord, content: bytes) -> ConversionRecord:
        conversion_dir = self.temp_root / record.id
        source_path = conversion_dir / f"input.{record.file_type}"
        try:
            conversion_dir.mkdir(parents=True, exist_ok=True)
            source_path.write_bytes(content)
            processing = self.repository.update_status(record.id, "PROCESSING") or record
            markdown = await asyncio.wait_for(
                asyncio.to_thread(self.convert, source_path),
                timeout=self.timeout_seconds,
            )
            storage_path = self.storage.upload_markdown(processing, markdown)
            completed = self.repository.update_status(
                record.id,
                "COMPLETED",
                markdown_storage_path=storage_path,
            )
            return completed or processing
        except TimeoutError as exc:
            self.repository.update_status(record.id, "FAILED", error_message="Conversion timed out.")
            raise api_error(504, "CONVERSION_TIMEOUT", "Conversion exceeded 5 minutes.") from exc
        except Exception as exc:
            logger.exception("Conversion failed for %s", record.id)
            self.repository.update_status(record.id, "FAILED", error_message="Conversion failed.")
            raise api_error(500, "CONVERSION_FAILED", "MarkItDown conversion failed.") from exc
        finally:
            remove_temp_tree(conversion_dir)
            self.limiter.release_active()
