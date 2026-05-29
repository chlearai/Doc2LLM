import os

import httpx
import pytest


def _load_env_file(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


_load_env_file(".env")
_load_env_file("../../frontend/.env")

LIVE_FRONTEND_URL = os.getenv("DOC2LLM_LIVE_FRONTEND_URL", "https://doc2md-one.vercel.app").rstrip("/")
LIVE_API_URL = os.getenv("DOC2LLM_LIVE_API_URL", "https://doc2llm-production.up.railway.app").rstrip("/")


@pytest.mark.skipif(
    not os.getenv("DOC2LLM_LIVE_AUTH_EMAIL") or not os.getenv("DOC2LLM_LIVE_AUTH_PASSWORD"),
    reason="Set DOC2LLM_LIVE_AUTH_EMAIL and DOC2LLM_LIVE_AUTH_PASSWORD to run the live deployment journey.",
)
def test_live_deployment_loads_profile_and_history() -> None:
    supabase_url = os.environ["SUPABASE_URL"].rstrip("/")
    anon_key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    assert anon_key, "SUPABASE_ANON_KEY or NEXT_PUBLIC_SUPABASE_ANON_KEY is required."

    token_response = httpx.post(
        f"{supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": anon_key, "Content-Type": "application/json"},
        json={
            "email": os.environ["DOC2LLM_LIVE_AUTH_EMAIL"],
            "password": os.environ["DOC2LLM_LIVE_AUTH_PASSWORD"],
        },
        timeout=20.0,
    )
    token_response.raise_for_status()
    access_token = token_response.json()["access_token"]

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        health_response = client.get(f"{LIVE_API_URL}/health")
        assert health_response.status_code == 200, health_response.text
        assert health_response.json() == {"status": "ok"}

        preflight_response = client.options(
            f"{LIVE_API_URL}/auth/me",
            headers={
                "Origin": LIVE_FRONTEND_URL,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        assert preflight_response.status_code == 200, preflight_response.text
        assert preflight_response.headers["access-control-allow-origin"] == LIVE_FRONTEND_URL

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Origin": LIVE_FRONTEND_URL,
        }
        me_response = client.get(f"{LIVE_API_URL}/auth/me", headers=headers)
        history_response = client.get(f"{LIVE_API_URL}/conversions", headers=headers)

    assert me_response.status_code == 200, me_response.text
    assert me_response.headers["access-control-allow-origin"] == LIVE_FRONTEND_URL
    profile = me_response.json()
    assert profile["email"] == os.environ["DOC2LLM_LIVE_AUTH_EMAIL"]
    assert profile["full_name"]

    assert history_response.status_code == 200, history_response.text
    assert history_response.headers["access-control-allow-origin"] == LIVE_FRONTEND_URL
    history = history_response.json()
    assert isinstance(history["items"], list)
