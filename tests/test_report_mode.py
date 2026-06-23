from __future__ import annotations

import hashlib
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


def test_report_mode_writes_report_and_decisions_not_cleaned(tmp_path: Path) -> None:
    input_path = tmp_path / "input.srt"
    input_path.write_text((FIXTURES / "jp_batch_bc.input.srt").read_text(encoding="utf-8"), encoding="utf-8")

    result = run_cli("--mode", "report", "--profile", "jp-adult-soft", str(input_path), cwd=tmp_path)

    assert result.returncode == 0
    report_path = tmp_path / "input.clean-report.txt"
    decisions_path = tmp_path / "input.clean-decisions.yml"
    cleaned_path = tmp_path / "input.cleaned.srt"
    assert report_path.exists()
    assert decisions_path.exists()
    assert not cleaned_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    decisions_text = decisions_path.read_text(encoding="utf-8")
    assert "summary:" in report_text
    assert "[REMOVE]" in report_text
    assert "source_sha256:" in decisions_text


def test_report_mode_hashes_match_specification(tmp_path: Path) -> None:
    raw_bytes = (
        b"\xef\xbb\xbf1\r\n00:00:01,000 --> 00:00:01,200\r\n\xe3\x83\x86\xe3\x82\xb9\xe3\x83\x88\r\n"
    )
    input_path = tmp_path / "hash.srt"
    input_path.write_bytes(raw_bytes)

    result = run_cli("--mode", "report", "--profile", "jp-adult-soft", str(input_path), cwd=tmp_path)

    assert result.returncode == 0
    decisions_text = (tmp_path / "hash.clean-decisions.yml").read_text(encoding="utf-8")
    assert hashlib.sha256(raw_bytes).hexdigest() in decisions_text


def test_existing_report_outputs_fail_without_force(tmp_path: Path) -> None:
    input_path = tmp_path / "input.srt"
    input_path.write_text((FIXTURES / "jp_batch_bc.input.srt").read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "input.clean-report.txt").write_text("exists", encoding="utf-8")

    result = run_cli("--mode", "report", "--profile", "jp-adult-soft", str(input_path), cwd=tmp_path)

    assert result.returncode == 2
    assert "output already exists" in result.stderr
