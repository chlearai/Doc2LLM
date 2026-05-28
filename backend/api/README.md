# Markdown Dashboard API

FastAPI backend for the File-to-Markdown dashboard.

## Local Development

Install this package with development dependencies from `backend/api`:

```bash
pip install -e ".[dev]"
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Useful URLs:

```txt
GET /health
GET /docs
GET /redoc
GET /openapi.json
```

## MarkItDown Integration

This backend uses the local MarkItDown package from:

```txt
../markitdown-main/markitdown-main/packages/markitdown
```

Do not copy unrelated upstream MarkItDown repository material into this product backend.
