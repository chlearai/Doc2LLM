import os

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.skipif(
    not os.getenv("DOC2LLM_LIVE_AUTH_EMAIL") or not os.getenv("DOC2LLM_LIVE_AUTH_PASSWORD"),
    reason="Set DOC2LLM_LIVE_AUTH_EMAIL and DOC2LLM_LIVE_AUTH_PASSWORD to run the live Supabase auth journey.",
)
def test_live_supabase_user_can_load_profile_and_history() -> None:
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

    client = TestClient(app, raise_server_exceptions=False)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Origin": "http://localhost:3000",
    }

    me_response = client.get("/auth/me", headers=headers)
    history_response = client.get("/conversions", headers=headers)

    assert me_response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert history_response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert me_response.status_code == 200
    assert me_response.json()["email"] == os.environ["DOC2LLM_LIVE_AUTH_EMAIL"]
    assert history_response.status_code == 200
    assert "items" in history_response.json()
