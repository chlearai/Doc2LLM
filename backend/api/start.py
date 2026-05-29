import os

import uvicorn


def get_port() -> int:
    return int(os.getenv("PORT") or os.getenv("RAILWAY_PORT") or "8000")


def main() -> None:
    host = "0.0.0.0"
    port = get_port()
    print(f"Starting Doc2LLM API on {host}:{port}", flush=True)
    uvicorn.run("app.main:app", host=host, port=port)


if __name__ == "__main__":
    main()
