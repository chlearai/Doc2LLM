import importlib.util


def test_supported_markitdown_optional_dependencies_are_installed():
    required_modules = [
        "mammoth",
        "pdfminer",
        "pdfplumber",
        "pptx",
        "openpyxl",
        "pandas",
        "lxml",
    ]

    missing_modules = [
        module for module in required_modules if importlib.util.find_spec(module) is None
    ]

    assert missing_modules == []
