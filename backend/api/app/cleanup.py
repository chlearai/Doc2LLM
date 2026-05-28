from pathlib import Path
import shutil


def remove_temp_tree(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
