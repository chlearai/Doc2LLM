from pathlib import Path

from app.cleanup import remove_temp_tree


def test_remove_temp_tree_deletes_nested_source_files(tmp_path: Path):
    conversion_dir = tmp_path / "conversion"
    conversion_dir.mkdir()
    source = conversion_dir / "input.txt"
    source.write_text("small test", encoding="utf-8")

    remove_temp_tree(conversion_dir)

    assert not conversion_dir.exists()
