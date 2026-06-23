from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests/fixtures"


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-m", "srt_clean.cli", *args]
    return subprocess.run(
        command,
        cwd=cwd or REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={"PYTHONPATH": str(REPO_ROOT / "src")},
    )


def test_clean_mode_writes_cleaned_srt_and_report(tmp_path: Path) -> None:
    input_path = tmp_path / "input.srt"
    input_path.write_text((FIXTURES / "jp_batch_bc.input.srt").read_text(encoding="utf-8"), encoding="utf-8")

    result = run_cli("--mode", "clean", "--profile", "jp-adult-soft", "--level", "moderate", str(input_path), cwd=tmp_path)

    assert result.returncode == 0
    cleaned_path = tmp_path / "input.cleaned.srt"
    report_path = tmp_path / "input.clean-report.txt"
    decisions_path = tmp_path / "input.clean-decisions.yml"
    assert cleaned_path.exists()
    assert report_path.exists()
    assert not decisions_path.exists()
    assert cleaned_path.read_text(encoding="utf-8") == (
        FIXTURES / "jp_batch_bc.expected.moderate.cleaned.srt"
    ).read_text(encoding="utf-8")


def test_clean_mode_aggressive_applies_density_window_and_review_does_not_modify_output(tmp_path: Path) -> None:
    input_path = tmp_path / "input.srt"
    input_path.write_text((FIXTURES / "jp_batch_bc.input.srt").read_text(encoding="utf-8"), encoding="utf-8")

    result = run_cli("--mode", "clean", "--profile", "jp-adult-soft", "--level", "aggressive", str(input_path), cwd=tmp_path)

    assert result.returncode == 0
    cleaned_text = (tmp_path / "input.cleaned.srt").read_text(encoding="utf-8")
    assert cleaned_text == (FIXTURES / "jp_batch_bc.expected.aggressive.cleaned.srt").read_text(encoding="utf-8")
    assert "テスト" in cleaned_text


def test_clean_mode_existing_output_fails_without_force(tmp_path: Path) -> None:
    input_path = tmp_path / "input.srt"
    input_path.write_text((FIXTURES / "jp_batch_bc.input.srt").read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "input.cleaned.srt").write_text("exists", encoding="utf-8")

    result = run_cli("--mode", "clean", "--profile", "jp-adult-soft", str(input_path), cwd=tmp_path)

    assert result.returncode == 2
    assert "output already exists" in result.stderr
