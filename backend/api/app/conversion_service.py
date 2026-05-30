from pathlib import Path
import os
import sys

_MARKITDOWN_CLASS = None
_OPENAI_CLIENT_CLASS = None


def _ensure_local_markitdown_on_path() -> None:
    backend_dir = Path(__file__).resolve().parents[2]
    packages_dir = backend_dir / "markitdown-main" / "markitdown-main" / "packages"
    for package in ("markitdown", "markitdown-ocr"):
        src = packages_dir / package / "src"
        src_text = str(src)
        if src.exists() and src_text not in sys.path:
            sys.path.insert(0, src_text)


def warm_converter() -> None:
    global _MARKITDOWN_CLASS
    if _MARKITDOWN_CLASS is None:
        _ensure_local_markitdown_on_path()
        from markitdown import MarkItDown

        _MARKITDOWN_CLASS = MarkItDown


def _build_ocr_service(user_id: str | None, repository):
    global _OPENAI_CLIENT_CLASS

    if not os.getenv("OPENAI_API_KEY") or not user_id or repository is None:
        return None

    _ensure_local_markitdown_on_path()
    try:
        if _OPENAI_CLIENT_CLASS is None:
            from openai import OpenAI

            _OPENAI_CLIENT_CLASS = OpenAI

        from app.ocr_service import TokenTrackingOCRService

        return TokenTrackingOCRService(
            client=_OPENAI_CLIENT_CLASS(),
            repository=repository,
            user_id=user_id,
        )
    except Exception:
        return None


def convert_file_to_markdown(source_path: Path, *, user_id: str | None = None, repository=None) -> str:
    if source_path.suffix.lower() in {".txt", ".csv", ".html"}:
        return source_path.read_text(encoding="utf-8")

    warm_converter()

    ocr_service = _build_ocr_service(user_id, repository)
    converter = _MARKITDOWN_CLASS(enable_plugins=False)
    if ocr_service is not None:
        try:
            import markitdown_ocr

            markitdown_ocr.register_converters(
                converter,
                llm_client=ocr_service.client,
                llm_model=ocr_service.model,
                llm_prompt=ocr_service.default_prompt,
            )
        except Exception:
            pass

    result = converter.convert(source_path, ocr_service=ocr_service)
    return result.text_content
