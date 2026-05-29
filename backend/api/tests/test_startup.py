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
