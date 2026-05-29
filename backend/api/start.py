import os

import uvicorn


def get_port() -> int:
    return int(os.getenv("PORT", "8000"))


def main() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=get_port())


if __name__ == "__main__":
    main()
