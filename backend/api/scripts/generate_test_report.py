from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


REPORT_DIR = Path("test-reports")
JUNIT_PATH = REPORT_DIR / "backend-junit.xml"
SUMMARY_PATH = REPORT_DIR / "backend-summary.md"


def main() -> int:
    REPORT_DIR.mkdir(exist_ok=True)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-vv", f"--junitxml={JUNIT_PATH}"],
        text=True,
        check=False,
    )

    tree = ET.parse(JUNIT_PATH)
    root = tree.getroot()
    cases = root.findall(".//testcase")
    failures = root.findall(".//failure")
    errors = root.findall(".//error")
    skipped = root.findall(".//skipped")

    lines = [
        "# Backend Test Report",
        "",
        f"- Total: {len(cases)}",
        f"- Passed: {len(cases) - len(failures) - len(errors) - len(skipped)}",
        f"- Failed: {len(failures)}",
        f"- Errors: {len(errors)}",
        f"- Skipped: {len(skipped)}",
        "",
        "## Test Cases",
        "",
    ]

    for case in cases:
        name = f"{case.attrib.get('classname', '')}.{case.attrib.get('name', '')}"
        status = "passed"
        detail = ""
        if case.find("failure") is not None:
            status = "failed"
            detail = case.find("failure").attrib.get("message", "")
        elif case.find("error") is not None:
            status = "error"
            detail = case.find("error").attrib.get("message", "")
        elif case.find("skipped") is not None:
            status = "skipped"
            detail = case.find("skipped").attrib.get("message", "")
        lines.append(f"- `{status}` {name} {detail}".rstrip())

    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {JUNIT_PATH}")
    print(f"Wrote {SUMMARY_PATH}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
