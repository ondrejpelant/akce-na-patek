from typer.testing import CliRunner

from scraper.__main__ import app


def test_version():
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "scraper" in result.stdout


def test_help_lists_commands():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("update", "run", "match", "publish", "review", "add-price", "cleanup"):
        assert cmd in result.stdout
