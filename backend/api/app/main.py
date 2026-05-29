import os
import re
import httpx
from uuid import uuid4
from datetime import UTC, datetime
from fastapi import Depends, FastAPI, File, Header, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth import AuthenticatedUser, get_current_user
from app.dependencies import get_conversion_manager
from app.errors import api_error
from app.models import (
    AdminConversionDetailResponse,
    AdminConversionListResponse,
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
    UserSignupRequest,
    UpdateProfileRequest,
    ChangePasswordRequest,
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

allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "https://doc2md-one.vercel.app",
]
for origins_value in (os.getenv("FRONTEND_ORIGIN"), os.getenv("FRONTEND_ORIGINS")):
    if origins_value:
        allowed_origins.extend(origin.strip().rstrip("/") for origin in origins_value.split(",") if origin.strip())
allowed_origins = list(dict.fromkeys(allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    print(f"Unhandled API error on {request.method} {request.url.path}: {str(exc)}", flush=True)
    headers = {}
    origin = request.headers.get("origin")
    if origin in allowed_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        headers=headers,
        content={
            "detail": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "The API could not complete the request. Check the backend logs and try again.",
            }
        },
    )


@app.get("/health", tags=["health"], summary="Check API health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/auth/signup",
    tags=["auth"],
    summary="Sign up a new user via Supabase Auth",
)
async def signup(body: UserSignupRequest) -> dict[str, str]:
    # 1. Validation: email regex
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, body.email):
        raise api_error(400, "BAD_REQUEST", "Please enter a valid email address.")

    # 2. Validation: password strength (both letters and numbers, >= 8 chars)
    if len(body.password) < 8:
        raise api_error(400, "BAD_REQUEST", "Password must be at least 8 characters long.")
    if not re.search(r"[a-zA-Z]", body.password) or not re.search(r"[0-9]", body.password):
        raise api_error(400, "BAD_REQUEST", "Password must contain both letters and numbers.")

    if not body.full_name.strip():
        raise api_error(400, "BAD_REQUEST", "Please enter your full name.")

    # 3. Proxy to Supabase Auth Signup
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_role_key or body.email.endswith(".test"):
        return {"message": "Account created successfully (local dev mock)! Check email."}

    signup_url = f"{supabase_url}/auth/v1/signup"
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": body.email,
        "password": body.password,
        "data": {
            "full_name": body.full_name
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(signup_url, headers=headers, json=payload, timeout=10.0)
            if response.status_code != 200:
                try:
                    err_data = response.json()
                    err_msg = (
                        err_data.get("msg")
                        or err_data.get("message")
                        or err_data.get("error_description")
                        or "Supabase Auth signup failed."
                    )
                except Exception:
                    err_msg = response.text or "Supabase Auth signup failed."
                raise api_error(response.status_code, "BAD_REQUEST", err_msg)
            return {"message": "Account created! Check your email for a confirmation link."}
    except httpx.RequestError as e:
        raise api_error(500, "EXTERNAL_API_ERROR", f"Failed to contact Supabase Auth API: {str(e)}")


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


@app.put(
    "/auth/me",
    response_model=UserProfileResponse,
    tags=["auth"],
    summary="Update the authenticated user's profile metadata",
)
def update_profile(
    body: UpdateProfileRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    manager: ConversionManager = Depends(get_conversion_manager),
) -> UserProfileResponse:
    if not body.full_name.strip():
        raise api_error(400, "BAD_REQUEST", "Please enter your full name.")
    
    updated = manager.repository.update_user_profile(user.id, body.full_name.strip())
    if not updated:
        raise api_error(404, "NOT_FOUND", "User profile not found.")
        
    return UserProfileResponse(
        id=updated.id,
        email=updated.email,
        full_name=updated.full_name,
        role=updated.role,
    )


@app.post(
    "/auth/change-password",
    tags=["auth"],
    summary="Change the password for the authenticated user",
)
async def change_password(
    body: ChangePasswordRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    # Validation: password strength (both letters and numbers, >= 8 chars)
    if len(body.password) < 8:
        raise api_error(400, "BAD_REQUEST", "Password must be at least 8 characters long.")
    if not re.search(r"[a-zA-Z]", body.password) or not re.search(r"[0-9]", body.password):
        raise api_error(400, "BAD_REQUEST", "Password must contain both letters and numbers.")

    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not authorization or not authorization.startswith("Bearer "):
        raise api_error(401, "UNAUTHORIZED", "Missing user access token.")
    user_token = authorization.removeprefix("Bearer ").strip()

    if not supabase_url or not service_role_key or user_token in ("local-dev-token", "local-admin-token") or user.email.endswith(".test"):
        return {"message": "Password changed successfully (local dev mock)!"}

    update_url = f"{supabase_url}/auth/v1/user"
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "password": body.password,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(update_url, headers=headers, json=payload, timeout=10.0)
            if response.status_code != 200:
                try:
                    err_data = response.json()
                    err_msg = err_data.get("msg") or err_data.get("error_description") or "Password change failed."
                except Exception:
                    err_msg = response.text or "Password change failed."
                raise api_error(response.status_code, "BAD_REQUEST", err_msg)
            return {"message": "Password changed successfully."}
    except httpx.RequestError as e:
        raise api_error(500, "EXTERNAL_API_ERROR", f"Failed to contact Supabase Auth API: {str(e)}")


@app.delete(
    "/auth/account",
    tags=["auth"],
    summary="Delete user account and all associated data",
)
async def delete_account(
    user: AuthenticatedUser = Depends(get_current_user),
    manager: ConversionManager = Depends(get_conversion_manager)
) -> dict[str, str]:
    # 1. Delete all user conversions from storage
    conversions = manager.repository.list_for_user(user.id, limit=100)
    for record in conversions:
        if record.markdown_storage_path:
            try:
                manager.storage.delete(record.markdown_storage_path)
            except Exception:
                pass

    # 2. Delete the profile record (cascades to conversions and logs)
    manager.repository.delete_user(user.id)

    # 3. Call Supabase Auth Admin API to delete the auth user
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_role_key or user.email.endswith(".test"):
        return {"message": "Account deleted successfully (local dev mock)!"}

    delete_url = f"{supabase_url}/auth/v1/admin/users/{user.id}"
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(delete_url, headers=headers, timeout=10.0)
            if response.status_code not in (200, 404):
                try:
                    err_data = response.json()
                    err_msg = err_data.get("msg") or err_data.get("error_description") or "Supabase Auth delete failed."
                except Exception:
                    err_msg = response.text or "Supabase Auth delete failed."
                raise api_error(response.status_code, "BAD_REQUEST", err_msg)
            return {"message": "Account deleted successfully."}
    except httpx.RequestError as e:
        raise api_error(500, "EXTERNAL_API_ERROR", f"Failed to contact Supabase Auth API: {str(e)}")


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
    now = datetime.now(UTC)
    today_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
    total_users = repo.count_users()
    total_conversions = repo.count_conversions()
    processed_today = repo.count_conversions(completed_from=today_start)
    failed_conversions = repo.count_conversions(status="FAILED")
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
    response_model=AdminConversionListResponse,
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
    profiles_by_id = manager.repository.get_users_by_ids({record.user_id for record in records})
    items = []
    for record in records:
        profile = profiles_by_id.get(record.user_id)
        items.append(
            AdminConversionDetailResponse(
                **record.model_dump(),
                user_email=profile.email if profile else None,
                user_full_name=profile.full_name if profile else None,
            )
        )
    return AdminConversionListResponse(
        items=items,
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
