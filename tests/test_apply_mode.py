from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

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


def test_apply_mode_writes_cleaned_srt_and_apply_report_without_profile(tmp_path: Path) -> None:
    input_path = tmp_path / "input.srt"
    input_path.write_text((FIXTURES / "jp_batch_bc.input.srt").read_text(encoding="utf-8"), encoding="utf-8")
    report_result = run_cli("--mode", "report", "--profile", "jp-adult-soft", str(input_path), cwd=tmp_path)
    assert report_result.returncode == 0

    decisions_path = tmp_path / "input.clean-decisions.yml"
    apply_result = run_cli("--mode", "apply", "--decisions", str(decisions_path), str(input_path), cwd=tmp_path)

    assert apply_result.returncode == 0
    assert (tmp_path / "input.cleaned.srt").exists()
    assert (tmp_path / "input.apply-report.txt").exists()


def test_apply_mode_source_hash_mismatch_exits_code_5(tmp_path: Path) -> None:
    input_path = tmp_path / "input.srt"
    input_path.write_text((FIXTURES / "jp_batch_bc.input.srt").read_text(encoding="utf-8"), encoding="utf-8")
    report_result = run_cli("--mode", "report", "--profile", "jp-adult-soft", str(input_path), cwd=tmp_path)
    assert report_result.returncode == 0

    input_path.write_text("1\n00:00:01,000 --> 00:00:02,000\nchanged\n", encoding="utf-8")
    decisions_path = tmp_path / "input.clean-decisions.yml"
    apply_result = run_cli("--mode", "apply", "--decisions", str(decisions_path), str(input_path), cwd=tmp_path)

    assert apply_result.returncode == 5
    assert "source_sha256 mismatch" in apply_result.stderr


def test_apply_mode_reports_user_override_protected(tmp_path: Path) -> None:
    input_path = tmp_path / "input.srt"
    input_path.write_text((FIXTURES / "jp_batch_bc.input.srt").read_text(encoding="utf-8"), encoding="utf-8")
    report_result = run_cli("--mode", "report", "--profile", "jp-adult-soft", str(input_path), cwd=tmp_path)
    assert report_result.returncode == 0

    decisions_path = tmp_path / "input.clean-decisions.yml"
    decisions = yaml.safe_load(decisions_path.read_text(encoding="utf-8"))
    protected = next(item for item in decisions["decisions"] if item["severity"] == "protected")
    protected["action"] = "remove"
    decisions_path.write_text(yaml.safe_dump(decisions, allow_unicode=True, sort_keys=False), encoding="utf-8")

    apply_result = run_cli("--mode", "apply", "--decisions", str(decisions_path), str(input_path), cwd=tmp_path)

    assert apply_result.returncode == 0
    cleaned_text = (tmp_path / "input.cleaned.srt").read_text(encoding="utf-8")
    assert "痛い" not in cleaned_text
    report_text = (tmp_path / "input.apply-report.txt").read_text(encoding="utf-8")
    assert "user_override_protected=true" in report_text
