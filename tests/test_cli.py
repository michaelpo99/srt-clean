from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-m", "srt_clean.cli", *args]
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={"PYTHONPATH": str(REPO_ROOT / "src")},
    )


def test_cli_help_returns_success() -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert "Rule-based SRT subtitle cleaner" in result.stdout


def test_cli_check_returns_success() -> None:
    fixture = REPO_ROOT / "tests/fixtures/basic_multiline.input.srt"

    result = run_cli("--check", "--profile", "jp-adult-soft", str(fixture))

    assert result.returncode == 0
    assert "check ok:" in result.stdout


def test_cli_requires_profile_for_clean_mode() -> None:
    fixture = REPO_ROOT / "tests/fixtures/basic_multiline.input.srt"

    result = run_cli(str(fixture))

    assert result.returncode == 2
    assert "--profile is required" in result.stderr


def test_cli_apply_mode_requires_decisions() -> None:
    fixture = REPO_ROOT / "tests/fixtures/basic_multiline.input.srt"

    result = run_cli("--mode", "apply", str(fixture))

    assert result.returncode == 2
    assert "--decisions is required" in result.stderr


def test_cli_clean_mode_rejects_decisions_option() -> None:
    fixture = REPO_ROOT / "tests/fixtures/basic_multiline.input.srt"

    result = run_cli("--profile", "jp-adult-soft", "--decisions", "bad.yml", str(fixture))

    assert result.returncode == 2
    assert "--decisions is not supported in --mode clean" in result.stderr
