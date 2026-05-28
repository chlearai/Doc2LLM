import os
import jwt
from dataclasses import dataclass
from fastapi import Depends, Header

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
        user_id = "11111111-1111-4111-8111-111111111111"
        profile = manager.repository.get_user(user_id)
        if not profile:
            profile = manager.repository.create_user(
                user_id=user_id,
                email="dev@local.test",
                full_name="Local Developer",
                role="user"
            )
        if not profile.is_active:
            raise api_error(403, "FORBIDDEN", "Account is disabled by administrator.")
        return AuthenticatedUser(
            id=profile.id,
            email=profile.email,
            full_name=profile.full_name,
            role=profile.role,
        )

    if token == "local-admin-token":
        # Load or create local admin user in repo
        user_id = "22222222-2222-4222-8222-222222222222"
        profile = manager.repository.get_user(user_id)
        if not profile:
            profile = manager.repository.create_user(
                user_id=user_id,
                email="admin@local.test",
                full_name="Local Admin",
                role="admin"
            )
        if not profile.is_active:
            raise api_error(403, "FORBIDDEN", "Account is disabled by administrator.")
        return AuthenticatedUser(
            id=profile.id,
            email=profile.email,
            full_name=profile.full_name,
            role=profile.role,
        )

    # 2. Supabase JWT Verification
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    if not jwt_secret:
        raise api_error(
            500,
            "CONFIG_ERROR",
            "SUPABASE_JWT_SECRET is not configured on the backend server.",
        )

    try:
        # Decode using the shared Supabase JWT secret
        payload = jwt.decode(
            token,
            key=jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Supabase uses 'authenticated' audience
        )
    except jwt.ExpiredSignatureError:
        raise api_error(401, "UNAUTHORIZED", "Supabase access token has expired.")
    except jwt.InvalidTokenError as e:
        raise api_error(401, "UNAUTHORIZED", f"Invalid Supabase access token: {str(e)}")

    user_id = payload.get("sub")
    email = payload.get("email")

    if not user_id or not email:
        raise api_error(401, "UNAUTHORIZED", "Invalid token payload: missing sub or email.")

    # Fetch user profile from in-memory repository to check roles/activity
    profile = manager.repository.get_user(user_id)
    if not profile:
        # Just-in-time creation for new sign-ups seen by backend
        role = "admin" if email.lower() == "admin@local.test" else "user"
        profile = manager.repository.create_user(
            user_id=user_id,
            email=email,
            full_name=payload.get("user_metadata", {}).get("full_name"),
            role=role
        )

    if not profile.is_active:
        raise api_error(403, "FORBIDDEN", "Account is disabled by administrator.")

    return AuthenticatedUser(
        id=profile.id,
        email=profile.email,
        full_name=profile.full_name,
        role=profile.role,
    )

