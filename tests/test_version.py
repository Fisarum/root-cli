from click.testing import CliRunner

from root import version as version_module
from root.cli import main


def test_version_command_shows_current_version(monkeypatch):
    monkeypatch.setattr(
        version_module,
        "check_for_update",
        lambda force=False: {
            "checked": True,
            "current": "0.1.0",
            "latest": "0.2.0",
            "update_available": True,
        },
    )
    runner = CliRunner()
    result = runner.invoke(main, ["version"])
    assert result.exit_code == 0
    assert "root v0.1.0" in result.output
    assert "Update available: v0.2.0" in result.output


def test_version_command_shows_up_to_date(monkeypatch):
    monkeypatch.setattr(
        version_module,
        "check_for_update",
        lambda force=False: {
            "checked": True,
            "current": "0.1.0",
            "latest": "0.1.0",
            "update_available": False,
        },
    )
    runner = CliRunner()
    result = runner.invoke(main, ["version"])
    assert result.exit_code == 0
    assert "You are on the latest version" in result.output


def test_update_command_requires_confirmation(monkeypatch):
    monkeypatch.setattr(
        version_module,
        "check_for_update",
        lambda force=False: {
            "checked": True,
            "current": "0.1.0",
            "latest": "0.2.0",
            "update_available": True,
        },
    )

    def should_not_run():
        raise AssertionError("run_update should not be called without confirmation")

    monkeypatch.setattr(version_module, "run_update", should_not_run)
    runner = CliRunner()
    result = runner.invoke(main, ["update"], input="n\n")
    assert result.exit_code == 0
    assert "Update cancelled" in result.output


def test_update_command_skips_confirmation_with_yes_flag(monkeypatch):
    monkeypatch.setattr(
        version_module,
        "check_for_update",
        lambda force=False: {
            "checked": True,
            "current": "0.1.0",
            "latest": "0.2.0",
            "update_available": True,
        },
    )
    monkeypatch.setattr(version_module, "run_update", lambda: (True, "0.2.0"))
    runner = CliRunner()
    result = runner.invoke(main, ["update", "--yes"])
    assert result.exit_code == 0
    assert "Update complete" in result.output
    assert "v0.2.0" in result.output


def test_is_newer_version():
    from root.version import _is_newer

    assert _is_newer("0.2.0", "0.1.0")
    assert _is_newer("1.10.0", "1.9.0")
    assert not _is_newer("0.1.0", "0.1.0")
    assert not _is_newer("0.1.0", "0.2.0")
