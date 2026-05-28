from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


ConversionStatus = Literal[
    "UPLOAD_RECEIVED",
    "PENDING",
    "PROCESSING",
    "COMPLETED",
    "FAILED",
    "DELETED",
]


class UploadMetadata(BaseModel):
    file_type: str
    size_bytes: int


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: str = "user"


class ConversionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    original_file_name: str
    file_type: str
    mime_type: str | None = None
    file_size_bytes: int
    status: ConversionStatus
    markdown_storage_path: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ConversionResponse(BaseModel):
    id: str
    status: ConversionStatus
    original_file_name: str
    file_type: str
    file_size_bytes: int
    markdown_storage_path: str | None = None
    created_at: datetime


class ConversionDetailResponse(ConversionResponse):
    mime_type: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ConversionListResponse(BaseModel):
    items: list[ConversionDetailResponse]
    limit: int
    offset: int


class ConversionStatusResponse(BaseModel):
    id: str
    status: ConversionStatus
    error_message: str | None = None
    completed_at: datetime | None = None


class MarkdownResponse(BaseModel):
    id: str
    markdown: str


class DownloadUrlResponse(BaseModel):
    id: str
    download_url: str
    expires_in: int


class DeleteConversionResponse(BaseModel):
    id: str
    status: Literal["DELETED"]
