from pathlib import Path
import sys

_MARKITDOWN_CLASS = None


def _ensure_local_markitdown_on_path() -> None:
    backend_dir = Path(__file__).resolve().parents[2]
    markitdown_src = (
        backend_dir
        / "markitdown-main"
        / "markitdown-main"
        / "packages"
        / "markitdown"
        / "src"
    )
    markitdown_src_text = str(markitdown_src)
    if markitdown_src_text not in sys.path:
        sys.path.insert(0, markitdown_src_text)


def warm_converter() -> None:
    global _MARKITDOWN_CLASS
    if _MARKITDOWN_CLASS is None:
        _ensure_local_markitdown_on_path()
        from markitdown import MarkItDown

        _MARKITDOWN_CLASS = MarkItDown


def convert_file_to_markdown(source_path: Path) -> str:
    if source_path.suffix.lower() in {".txt", ".csv", ".html"}:
        return source_path.read_text(encoding="utf-8")

    warm_converter()

    result = _MARKITDOWN_CLASS(enable_plugins=False).convert(source_path)
    return result.text_content
