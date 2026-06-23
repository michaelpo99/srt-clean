from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/translate-with-ollama.sh"
FIXTURE_PATH = REPO_ROOT / "tests/fixtures/translate_script.input.srt"


def write_fake_ollama(path: Path, *, include_model: bool = True) -> None:
    model_lines = ""
    if include_model:
        model_lines = "qwen3:8b      fake-id         5 GB      now\n"

    script = f"""#!/usr/bin/env bash
set -euo pipefail

if [[ "$1" == "list" ]]; then
  cat <<'EOF'
NAME          ID              SIZE      MODIFIED
{model_lines}EOF
  exit 0
fi

if [[ "$1" == "run" ]]; then
  prompt="${{3:-}}"
  if [[ "$prompt" == *"Hello"* ]]; then
    printf 'Ni hao\\nshi jie\\n'
  else
    printf 'Di er ge ti shi\\n'
  fi
  exit 0
fi

echo "unexpected ollama invocation: $*" >&2
exit 1
"""
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def run_translate_script(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    write_fake_ollama(fake_bin / "ollama")

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PYTHON_BIN"] = sys.executable

    return subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def test_translate_script_creates_language_suffix_output(tmp_path: Path) -> None:
    input_path = tmp_path / FIXTURE_PATH.name
    shutil.copyfile(FIXTURE_PATH, input_path)

    result = run_translate_script(tmp_path, str(input_path), "zh-TW")

    assert result.returncode == 0
    assert "translated 2 cue(s)" in result.stdout

    output_path = tmp_path / "translate_script.input.zh-TW.srt"
    assert output_path.exists()
    assert (
        output_path.read_text(encoding="utf-8")
        == "1\n00:00:01,000 --> 00:00:02,500\nNi hao\nshi jie\n\n"
        "2\n00:00:03,000 --> 00:00:04,000\nDi er ge ti shi\n"
    )


def test_translate_script_requires_available_model(tmp_path: Path) -> None:
    input_path = tmp_path / FIXTURE_PATH.name
    shutil.copyfile(FIXTURE_PATH, input_path)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    write_fake_ollama(fake_bin / "ollama", include_model=False)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PYTHON_BIN"] = sys.executable

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), str(input_path), "zh-TW"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 1
    assert "ollama pull qwen3:8b" in result.stderr
