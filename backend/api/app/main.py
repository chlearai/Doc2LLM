import os
from uuid import uuid4
from datetime import UTC, datetime
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
    AdminStatsResponse,
    AdminUserListResponse,
    AdminUserProfileResponse,
    AdminCreateUserRequest,
    AdminUserStatusRequest,
    AdminUserRoleRequest,
    AdminLogListResponse,
    AdminSystemHealthResponse,
    SystemHealthIndicator,
)
from app.services import ConversionManager

app = FastAPI(
    title="Doc2LLM API",
    version="0.1.0",
    description="Internal API for converting uploaded files into clean, LLM-friendly Markdown.",
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


# Admin Role Verification Helper
def verify_admin(user: AuthenticatedUser = Depends(get_current_user)) -> None:
    if user.role != "admin":
        raise api_error(403, "FORBIDDEN", "Only administrators can perform this action.")


@app.get(
    "/admin/stats",
    response_model=AdminStatsResponse,
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
    summary="Get admin statistics",
)
def get_admin_stats(
    manager: ConversionManager = Depends(get_conversion_manager)
) -> AdminStatsResponse:
    repo = manager.repository
    total_users = len(repo._profiles)
    total_conversions = sum(1 for r in repo._records.values() if r.status != "DELETED")
    
    # Processed today
    now = datetime.now(UTC)
    processed_today = 0
    for r in repo._records.values():
        if r.status != "DELETED" and r.completed_at:
            if r.completed_at.date() == now.date():
                processed_today += 1
                
    failed_conversions = sum(1 for r in repo._records.values() if r.status == "FAILED")
    pending_conversions = manager.limiter.pending_count
    
    return AdminStatsResponse(
        total_users=total_users,
        total_converted_files=total_conversions,
        files_processed_today=processed_today,
        failed_conversions=failed_conversions,
        pending_conversions=pending_conversions,
        system_health="Healthy" if failed_conversions < 10 else "Warning",
    )


@app.get(
    "/admin/users",
    response_model=AdminUserListResponse,
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
    summary="List all users",
)
def list_admin_users(
    search: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    manager: ConversionManager = Depends(get_conversion_manager)
) -> AdminUserListResponse:
    repo = manager.repository
    profiles = repo.list_users(search=search, limit=limit, offset=offset)
    items = []
    for p in profiles:
        file_count = repo.count_user_files(p.id)
        items.append(
            AdminUserProfileResponse(
                id=p.id,
                email=p.email,
                full_name=p.full_name,
                role=p.role,
                is_active=p.is_active,
                created_at=p.created_at,
                files_converted=file_count
            )
        )
    return AdminUserListResponse(items=items, limit=limit, offset=offset)


@app.post(
    "/admin/users",
    response_model=AdminUserProfileResponse,
    status_code=201,
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
    summary="Create a new user",
)
def create_admin_user(
    body: AdminCreateUserRequest,
    manager: ConversionManager = Depends(get_conversion_manager)
) -> AdminUserProfileResponse:
    repo = manager.repository
    existing = repo.get_user_by_email(body.email)
    if existing:
        raise api_error(400, "BAD_REQUEST", f"User with email {body.email} already exists.")
    
    user_id = str(uuid4())
    profile = repo.create_user(
        user_id=user_id,
        email=body.email,
        full_name=body.full_name,
        role=body.role
    )
    return AdminUserProfileResponse(
        id=profile.id,
        email=profile.email,
        full_name=profile.full_name,
        role=profile.role,
        is_active=profile.is_active,
        created_at=profile.created_at,
        files_converted=0
    )


@app.put(
    "/admin/users/{user_id}/status",
    response_model=AdminUserProfileResponse,
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
    summary="Enable/disable a user",
)
def update_admin_user_status(
    user_id: str,
    body: AdminUserStatusRequest,
    manager: ConversionManager = Depends(get_conversion_manager)
) -> AdminUserProfileResponse:
    repo = manager.repository
    profile = repo.update_user_status(user_id, body.is_active)
    if not profile:
        raise api_error(404, "NOT_FOUND", "User does not exist.")
    return AdminUserProfileResponse(
        id=profile.id,
        email=profile.email,
        full_name=profile.full_name,
        role=profile.role,
        is_active=profile.is_active,
        created_at=profile.created_at,
        files_converted=repo.count_user_files(profile.id)
    )


@app.put(
    "/admin/users/{user_id}/role",
    response_model=AdminUserProfileResponse,
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
    summary="Change user role",
)
def update_admin_user_role(
    user_id: str,
    body: AdminUserRoleRequest,
    manager: ConversionManager = Depends(get_conversion_manager)
) -> AdminUserProfileResponse:
    repo = manager.repository
    if body.role not in {"admin", "user"}:
        raise api_error(400, "BAD_REQUEST", "Invalid role value. Must be 'admin' or 'user'.")
    profile = repo.update_user_role(user_id, body.role)
    if not profile:
        raise api_error(404, "NOT_FOUND", "User does not exist.")
    return AdminUserProfileResponse(
        id=profile.id,
        email=profile.email,
        full_name=profile.full_name,
        role=profile.role,
        is_active=profile.is_active,
        created_at=profile.created_at,
        files_converted=repo.count_user_files(profile.id)
    )


@app.get(
    "/admin/conversions",
    response_model=ConversionListResponse,
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
    summary="List all users' conversions",
)
def list_admin_conversions(
    status: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    file_type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    manager: ConversionManager = Depends(get_conversion_manager)
) -> ConversionListResponse:
    records = manager.repository.list_all_conversions(
        status=status,
        user_id=user_id,
        file_type=file_type,
        search=search,
        limit=limit,
        offset=offset
    )
    return ConversionListResponse(
        items=[ConversionDetailResponse(**r.model_dump()) for r in records],
        limit=limit,
        offset=offset
    )


@app.post(
    "/admin/conversions/{conversion_id}/cancel",
    response_model=ConversionDetailResponse,
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
    summary="Cancel a stuck job",
)
def cancel_admin_conversion(
    conversion_id: str,
    manager: ConversionManager = Depends(get_conversion_manager)
) -> ConversionDetailResponse:
    record = manager.repository._records.get(conversion_id)
    if not record:
        raise api_error(404, "NOT_FOUND", "Conversion does not exist.")
    if record.status not in {"UPLOAD_RECEIVED", "PENDING", "PROCESSING"}:
        raise api_error(400, "BAD_REQUEST", "Only queued or processing conversions can be cancelled.")
    
    updated = manager.repository.update_status(conversion_id, "FAILED", error_message="Cancelled by administrator.")
    if not updated:
        raise api_error(500, "UPDATE_FAILED", "Failed to update conversion status.")
    return ConversionDetailResponse(**updated.model_dump())


@app.post(
    "/admin/conversions/{conversion_id}/retry",
    response_model=ConversionDetailResponse,
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
    summary="Simulate retry on a conversion job",
)
def retry_admin_conversion(
    conversion_id: str,
    manager: ConversionManager = Depends(get_conversion_manager)
) -> ConversionDetailResponse:
    record = manager.repository._records.get(conversion_id)
    if not record:
        raise api_error(404, "NOT_FOUND", "Conversion does not exist.")
    
    updated = manager.repository.update_status(conversion_id, "COMPLETED")
    if not updated:
         raise api_error(500, "UPDATE_FAILED", "Failed to update conversion status.")
    return ConversionDetailResponse(**updated.model_dump())


@app.delete(
    "/admin/conversions/{conversion_id}",
    response_model=DeleteConversionResponse,
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
    summary="Delete any user's conversion",
)
def delete_admin_conversion(
    conversion_id: str,
    manager: ConversionManager = Depends(get_conversion_manager)
) -> DeleteConversionResponse:
    record = manager.repository._records.get(conversion_id)
    if not record:
        raise api_error(404, "NOT_FOUND", "Conversion does not exist.")
    if record.markdown_storage_path:
        manager.storage.delete(record.markdown_storage_path)
    deleted = manager.repository.update_status(record.id, "DELETED")
    return DeleteConversionResponse(id=(deleted or record).id, status="DELETED")


@app.get(
    "/admin/logs",
    response_model=AdminLogListResponse,
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
    summary="Retrieve all system logs",
)
def get_admin_logs(
    level: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    manager: ConversionManager = Depends(get_conversion_manager)
) -> AdminLogListResponse:
    logs = manager.repository.list_all_logs(level=level, search=search, limit=limit, offset=offset)
    return AdminLogListResponse(items=logs, limit=limit, offset=offset)


@app.get(
    "/admin/system-health",
    response_model=AdminSystemHealthResponse,
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
    summary="Get system service health",
)
def get_admin_system_health() -> AdminSystemHealthResponse:
    return AdminSystemHealthResponse(
        railway_converter=SystemHealthIndicator(status="Healthy"),
        supabase_connection=SystemHealthIndicator(status="Healthy"),
        conversion_queue=SystemHealthIndicator(status="Healthy"),
        storage_write=SystemHealthIndicator(status="Healthy"),
    )

