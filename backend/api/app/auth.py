import os
import jwt
from dataclasses import dataclass
from fastapi import Depends, Header
import httpx

from app.errors import api_error
from app.dependencies import get_conversion_manager
from app.services import ConversionManager


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str
    full_name: str | None = None
    role: str = "user"


def get_current_user(
    authorization: str | None = Header(default=None),
    manager: ConversionManager = Depends(get_conversion_manager)
) -> AuthenticatedUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise api_error(401, "UNAUTHORIZED", "Missing Supabase access token.")

    token = authorization.removeprefix("Bearer ").strip()
    
    # 1. Dev token overrides
    if token == "local-dev-token":
        # Load or create local dev user in repo
        return _resolve_local_dev_user(
            manager,
            user_id="11111111-1111-4111-8111-111111111111",
            email="dev@local.test",
            full_name="Local Developer",
            role="user",
        )

    if token == "local-admin-token":
        # Load or create local admin user in repo
        return _resolve_local_dev_user(
            manager,
            user_id="22222222-2222-4222-8222-222222222222",
            email="admin@local.test",
            full_name="Local Admin",
            role="admin",
        )

    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # 2. Prefer Supabase Auth server validation so we support HS256/RS256/ES256
    if supabase_url and service_role_key:
        user = _get_supabase_user_from_auth_server(supabase_url, service_role_key, token)
        if user:
            return _resolve_authenticated_user(user, manager)

    # 3. Fallback to local JWT verification for legacy/self-hosted setups
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    if not jwt_secret:
        raise api_error(
            500,
            "CONFIG_ERROR",
            "SUPABASE_JWT_SECRET is not configured on the backend server.",
        )

    try:
        try:
            unverified_header = jwt.get_unverified_header(token)
            print(f"Token Header: {unverified_header}", flush=True)
        except Exception as eh:
            print(f"Failed to read JWT header: {str(eh)}", flush=True)

        # Decode using the shared Supabase JWT secret (trying raw and base64 fallback)
        try:
            payload = jwt.decode(
                token,
                key=jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False}  # Supabase uses 'authenticated' audience
            )
        except jwt.InvalidSignatureError:
            import base64
            try:
                padded_secret = jwt_secret + "=" * ((4 - len(jwt_secret) % 4) % 4)
                decoded_secret = base64.b64decode(padded_secret)
                payload = jwt.decode(
                    token,
                    key=decoded_secret,
                    algorithms=["HS256"],
                    options={"verify_aud": False}
                )
            except Exception:
                raise
    except jwt.ExpiredSignatureError:
        raise api_error(401, "UNAUTHORIZED", "Supabase access token has expired.")
    except jwt.InvalidTokenError as e:
        print(f"JWT Verification failed: {str(e)}", flush=True)
        raise api_error(401, "UNAUTHORIZED", f"Invalid Supabase access token: {str(e)}")

    user_id = payload.get("sub")
    email = payload.get("email")

    if not user_id or not email:
        raise api_error(401, "UNAUTHORIZED", "Invalid token payload: missing sub or email.")

    return _resolve_authenticated_user(
        {
            "id": user_id,
            "email": email,
            "user_metadata": payload.get("user_metadata", {}),
        },
        manager,
    )


def _get_supabase_user_from_auth_server(
    supabase_url: str,
    service_role_key: str,
    token: str,
) -> dict | None:
    auth_url = f"{supabase_url.rstrip('/')}/auth/v1/user"
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {token}",
    }

    try:
        response = httpx.get(auth_url, headers=headers, timeout=10.0)
    except httpx.RequestError:
        return None

    if response.status_code == 200:
        body = response.json()
        if isinstance(body, dict) and body.get("id") and body.get("email"):
            return body
        return None

    # Let the legacy JWT fallback have a chance if the auth server is unavailable.
    if response.status_code >= 500:
        return None

    detail = response.text.strip() or "Supabase Auth rejected the access token."
    raise api_error(response.status_code, "UNAUTHORIZED", detail)


def _resolve_local_dev_user(
    manager: ConversionManager,
    *,
    user_id: str,
    email: str,
    full_name: str,
    role: str,
) -> AuthenticatedUser:
    try:
        profile = manager.repository.get_user(user_id)
        if not profile:
            profile = manager.repository.create_user(
                user_id=user_id,
                email=email,
                full_name=full_name,
                role=role,
            )
        if not profile.is_active:
            raise api_error(403, "FORBIDDEN", "Account is disabled by administrator.")
        return AuthenticatedUser(
            id=profile.id,
            email=profile.email,
            full_name=profile.full_name,
            role=profile.role,
        )
    except httpx.HTTPStatusError:
        return AuthenticatedUser(
            id=user_id,
            email=email,
            full_name=full_name,
            role=role,
        )


def _resolve_authenticated_user(user: dict, manager: ConversionManager) -> AuthenticatedUser:
    user_id = str(user["id"])
    email = str(user["email"])
    full_name = (
        user.get("user_metadata", {}).get("full_name")
        if isinstance(user.get("user_metadata"), dict)
        else None
    )

    # Fetch user profile from repository to check roles/activity.
    try:
        profile = manager.repository.get_user(user_id)
        if not profile:
            profile = manager.repository.create_user(
                user_id=user_id,
                email=email,
                full_name=full_name,
                role="admin" if email.lower() == "admin@local.test" else "user",
            )
    except httpx.HTTPError as exc:
        print(f"Profile resolution failed: {str(exc)}", flush=True)
        raise api_error(
            503,
            "PROFILE_UNAVAILABLE",
            "Your account was verified, but the profile service is unavailable. Try again in a moment.",
        )

    if not profile.is_active:
        raise api_error(403, "FORBIDDEN", "Account is disabled by administrator.")

    return AuthenticatedUser(
        id=profile.id,
        email=profile.email,
        full_name=profile.full_name,
        role=profile.role,
    )
