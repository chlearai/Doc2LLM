import os
from fastapi import Depends, FastAPI, File, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.auth import AuthenticatedUser, get_current_user
from app.dependencies import get_conversion_manager
from app.errors import api_error
from app.models import (
    ConversionDetailResponse,
    ConversionListResponse,
    ConversionResponse,
    ConversionStatusResponse,
    DeleteConversionResponse,
    DownloadUrlResponse,
    MarkdownResponse,
    UserProfileResponse,
)
from app.services import ConversionManager

app = FastAPI(
    title="File-to-Markdown Converter API",
    version="0.1.0",
    description="Internal API for converting uploaded files into Markdown outputs.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

frontend_origin = os.getenv("FRONTEND_ORIGIN")
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
]
if frontend_origin:
    allowed_origins.append(frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"], summary="Check API health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/auth/me",
    response_model=UserProfileResponse,
    tags=["auth"],
    summary="Return the authenticated user",
)
def auth_me(user: AuthenticatedUser = Depends(get_current_user)) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    )


@app.post(
    "/conversions",
    response_model=ConversionResponse,
    status_code=201,
    tags=["conversions"],
    summary="Upload and convert one file",
    description="Validates an uploaded source file, converts it to Markdown, stores the Markdown output, and deletes the temporary source file.",
)
async def create_conversion(
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user),
    manager: ConversionManager = Depends(get_conversion_manager),
) -> ConversionResponse:
    record = await manager.create_conversion(user_id=user.id, file=file)
    return ConversionResponse(**record.model_dump())


@app.get(
    "/conversions",
    response_model=ConversionListResponse,
    tags=["conversions"],
    summary="List conversions",
)
def list_conversions(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: AuthenticatedUser = Depends(get_current_user),
    manager: ConversionManager = Depends(get_conversion_manager),
) -> ConversionListResponse:
    records = manager.repository.list_for_user(user.id, status=status, limit=limit, offset=offset)
    return ConversionListResponse(
        items=[ConversionDetailResponse(**record.model_dump()) for record in records],
        limit=limit,
        offset=offset,
    )


@app.get(
    "/conversions/{conversion_id}",
    response_model=ConversionDetailResponse,
    tags=["conversions"],
    summary="Get conversion detail",
)
def get_conversion(
    conversion_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    manager: ConversionManager = Depends(get_conversion_manager),
) -> ConversionDetailResponse:
    record = manager.repository.get_for_user(conversion_id, user.id)
    if not record:
        raise api_error(404, "NOT_FOUND", "Conversion does not exist.")
    return ConversionDetailResponse(**record.model_dump())


@app.get(
    "/conversions/{conversion_id}/status",
    response_model=ConversionStatusResponse,
    tags=["conversions"],
    summary="Get conversion status",
)
def get_conversion_status(
    conversion_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    manager: ConversionManager = Depends(get_conversion_manager),
) -> ConversionStatusResponse:
    record = manager.repository.get_for_user(conversion_id, user.id)
    if not record:
        raise api_error(404, "NOT_FOUND", "Conversion does not exist.")
    return ConversionStatusResponse(**record.model_dump())


@app.get(
    "/conversions/{conversion_id}/markdown",
    response_model=MarkdownResponse,
    tags=["conversions"],
    summary="Get converted Markdown",
)
def get_conversion_markdown(
    conversion_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    manager: ConversionManager = Depends(get_conversion_manager),
) -> MarkdownResponse:
    record = manager.repository.get_for_user(conversion_id, user.id)
    if not record:
        raise api_error(404, "NOT_FOUND", "Conversion does not exist.")
    if record.status != "COMPLETED" or not record.markdown_storage_path:
        raise api_error(409, "CONVERSION_NOT_READY", "Markdown is available after conversion completes.")
    markdown = manager.storage.get_markdown(record.markdown_storage_path)
    if markdown is None:
        raise api_error(404, "NOT_FOUND", "Markdown output does not exist.")
    return MarkdownResponse(id=record.id, markdown=markdown)


@app.get(
    "/conversions/{conversion_id}/download-url",
    response_model=DownloadUrlResponse,
    tags=["conversions"],
    summary="Get signed Markdown download URL",
)
def get_conversion_download_url(
    conversion_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    manager: ConversionManager = Depends(get_conversion_manager),
) -> DownloadUrlResponse:
    record = manager.repository.get_for_user(conversion_id, user.id)
    if not record:
        raise api_error(404, "NOT_FOUND", "Conversion does not exist.")
    if record.status != "COMPLETED" or not record.markdown_storage_path:
        raise api_error(409, "CONVERSION_NOT_READY", "Download is available after conversion completes.")
    download_url = manager.storage.create_signed_url(record.markdown_storage_path, expires_in=300)
    if not download_url:
        raise api_error(404, "NOT_FOUND", "Markdown output does not exist.")
    return DownloadUrlResponse(id=record.id, download_url=download_url, expires_in=300)


@app.post(
    "/conversions/{conversion_id}/retry",
    tags=["conversions"],
    summary="Explain retry policy",
)
def retry_conversion(
    conversion_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    manager: ConversionManager = Depends(get_conversion_manager),
) -> None:
    record = manager.repository.get_for_user(conversion_id, user.id)
    if not record:
        raise api_error(404, "NOT_FOUND", "Conversion does not exist.")
    raise api_error(
        400,
        "REUPLOAD_REQUIRED",
        "The source file was deleted after the previous attempt. Upload the file again to retry.",
    )


@app.delete(
    "/conversions/{conversion_id}",
    response_model=DeleteConversionResponse,
    tags=["conversions"],
    summary="Delete a conversion",
)
def delete_conversion(
    conversion_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    manager: ConversionManager = Depends(get_conversion_manager),
) -> DeleteConversionResponse:
    record = manager.repository.get_for_user(conversion_id, user.id)
    if not record:
        raise api_error(404, "NOT_FOUND", "Conversion does not exist.")
    manager.storage.delete(record.markdown_storage_path)
    deleted = manager.repository.update_status(record.id, "DELETED")
    return DeleteConversionResponse(id=(deleted or record).id, status="DELETED")
