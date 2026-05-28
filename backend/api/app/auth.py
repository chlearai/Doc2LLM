from dataclasses import dataclass

from fastapi import Header

from app.errors import api_error


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str
    full_name: str | None = None
    role: str = "user"


def get_current_user(authorization: str | None = Header(default=None)) -> AuthenticatedUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise api_error(401, "UNAUTHORIZED", "Missing Supabase access token.")

    token = authorization.removeprefix("Bearer ").strip()
    if token == "local-dev-token":
        return AuthenticatedUser(
            id="11111111-1111-4111-8111-111111111111",
            email="dev@local.test",
            full_name="Local Developer",
            role="user",
        )

    raise api_error(
        401,
        "UNAUTHORIZED",
        "Supabase JWT verification is not configured yet. Complete Sprint 1 auth wiring before using protected endpoints without a test override.",
    )
