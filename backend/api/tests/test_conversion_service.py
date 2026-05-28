from pathlib import Path

from app.conversion_service import convert_file_to_markdown


def test_convert_file_to_markdown_uses_local_markitdown_for_text_file(tmp_path: Path):
    source = tmp_path / "notes.txt"
    source.write_text("Alpha\n\nBeta\n", encoding="utf-8")

    markdown = convert_file_to_markdown(source)

    assert "Alpha" in markdown
    assert "Beta" in markdown
