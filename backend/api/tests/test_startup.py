import importlib
import json


def test_railway_start_command_uses_python_launcher() -> None:
    with open("railway.json", encoding="utf-8") as config_file:
        config = json.load(config_file)

    assert config["deploy"]["startCommand"] == "python start.py"


def test_startup_launcher_reads_port_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("PORT", "4321")
    start = importlib.import_module("start")

    assert start.get_port() == 4321


def test_railway_requirements_include_runtime_server() -> None:
    with open("requirements.txt", encoding="utf-8") as requirements_file:
        requirements = requirements_file.read()

    assert "uvicorn[standard]" in requirements
