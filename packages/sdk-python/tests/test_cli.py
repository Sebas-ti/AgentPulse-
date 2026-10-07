"""Tests for AgentPulse Typer CLI."""

from agentpulse.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_version() -> None:
    """Verify cli version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "AgentPulse CLI v0.1.0" in result.stdout
