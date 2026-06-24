from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "bin/translate-with-ollama"
FIXTURE_PATH = REPO_ROOT / "tests/fixtures/translate_script.input.srt"


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


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


def write_retrying_fake_ollama(path: Path) -> None:
    script = """#!/usr/bin/env bash
set -euo pipefail

state_dir="$(dirname "$0")/.ollama-state"
mkdir -p "$state_dir"

if [[ "$1" == "list" ]]; then
  cat <<'EOF'
NAME          ID              SIZE      MODIFIED
qwen3:8b      fake-id         5 GB      now
EOF
  exit 0
fi

if [[ "$1" == "run" ]]; then
  prompt="${3:-}"
  hello_counter_file="$state_dir/hello.count"
  second_counter_file="$state_dir/second.count"

  if [[ "$prompt" == *"Hello"* ]]; then
    count=0
    if [[ -f "$hello_counter_file" ]]; then
      count="$(cat "$hello_counter_file")"
    fi
    count=$((count + 1))
    printf '%s' "$count" >"$hello_counter_file"
    if [[ "$count" -eq 1 ]]; then
      printf '   \\n'
    else
      printf 'Ni hao\\nshi jie\\n'
    fi
    exit 0
  fi

  count=0
  if [[ -f "$second_counter_file" ]]; then
    count="$(cat "$second_counter_file")"
  fi
  count=$((count + 1))
  printf '%s' "$count" >"$second_counter_file"
  printf 'Di er ge ti shi\\n'
  exit 0
fi

echo "unexpected ollama invocation: $*" >&2
exit 1
"""
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def write_empty_fake_ollama(path: Path) -> None:
    script = """#!/usr/bin/env bash
set -euo pipefail

if [[ "$1" == "list" ]]; then
  cat <<'EOF'
NAME          ID              SIZE      MODIFIED
qwen3:8b      fake-id         5 GB      now
EOF
  exit 0
fi

if [[ "$1" == "run" ]]; then
  printf '   \\n'
  exit 0
fi

echo "unexpected ollama invocation: $*" >&2
exit 1
"""
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def write_resume_only_second_cue_fake_ollama(path: Path) -> None:
    script = """#!/usr/bin/env bash
set -euo pipefail

if [[ "$1" == "list" ]]; then
  cat <<'EOF'
NAME          ID              SIZE      MODIFIED
qwen3:8b      fake-id         5 GB      now
EOF
  exit 0
fi

if [[ "$1" == "run" ]]; then
  prompt="${3:-}"
  if [[ "$prompt" == *"Hello"* ]]; then
    echo "unexpected resume attempt for cue 1" >&2
    exit 1
  fi
  printf 'Di er ge ti shi\\n'
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
    partial_path = tmp_path / "translate_script.input.zh-TW.partial.srt"
    assert output_path.exists()
    assert not partial_path.exists()
    assert (
        output_path.read_text(encoding="utf-8")
        == "1\n00:00:01,000 --> 00:00:02,500\nNi hao\nshi jie\n\n"
        "2\n00:00:03,000 --> 00:00:04,000\nDi er ge ti shi\n"
    )


def test_translate_script_retries_empty_output_and_succeeds(tmp_path: Path) -> None:
    input_path = tmp_path / FIXTURE_PATH.name
    shutil.copyfile(FIXTURE_PATH, input_path)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    write_retrying_fake_ollama(fake_bin / "ollama")

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

    assert result.returncode == 0
    assert "retrying cue 1 after model produced empty output (attempt 1/3)" in result.stderr
    assert "translated 2 cue(s)" in result.stdout


def test_translate_script_keeps_source_text_after_repeated_empty_output(tmp_path: Path) -> None:
    input_path = tmp_path / FIXTURE_PATH.name
    shutil.copyfile(FIXTURE_PATH, input_path)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    write_empty_fake_ollama(fake_bin / "ollama")

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

    output_path = tmp_path / "translate_script.input.zh-TW.srt"
    partial_path = tmp_path / "translate_script.input.zh-TW.partial.srt"

    assert result.returncode == 0
    assert "retrying cue 1 after model produced empty output (attempt 1/3)" in result.stderr
    assert "retrying cue 1 after model produced empty output (attempt 2/3)" in result.stderr
    assert "warning: using source text for cue 1 after translation failed:" in result.stderr
    assert "warning: kept source text for cue(s): 1" in result.stderr
    assert "translated 2 cue(s)" in result.stdout
    assert output_path.exists()
    assert not partial_path.exists()
    assert (
        output_path.read_text(encoding="utf-8")
        == "1\n00:00:01,000 --> 00:00:02,500\nHello\nworld\n\n"
        "2\n00:00:03,000 --> 00:00:04,000\nSecond cue\n"
    )


def test_translate_script_keeps_source_text_when_later_cue_fails(tmp_path: Path) -> None:
    input_path = tmp_path / FIXTURE_PATH.name
    shutil.copyfile(FIXTURE_PATH, input_path)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    script = """#!/usr/bin/env bash
set -euo pipefail

if [[ "$1" == "list" ]]; then
  cat <<'EOF'
NAME          ID              SIZE      MODIFIED
qwen3:8b      fake-id         5 GB      now
EOF
  exit 0
fi

if [[ "$1" == "run" ]]; then
  prompt="${3:-}"
  if [[ "$prompt" == *"Hello"* ]]; then
    printf 'Ni hao\\nshi jie\\n'
  else
    printf '   \\n'
  fi
  exit 0
fi

echo "unexpected ollama invocation: $*" >&2
exit 1
"""
    ollama_path = fake_bin / "ollama"
    ollama_path.write_text(script, encoding="utf-8")
    ollama_path.chmod(0o755)

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

    partial_path = tmp_path / "translate_script.input.zh-TW.partial.srt"
    output_path = tmp_path / "translate_script.input.zh-TW.srt"

    assert result.returncode == 0
    assert "warning: using source text for cue 2 after translation failed:" in result.stderr
    assert "warning: kept source text for cue(s): 2" in result.stderr
    assert output_path.exists()
    assert not partial_path.exists()
    assert (
        output_path.read_text(encoding="utf-8")
        == "1\n00:00:01,000 --> 00:00:02,500\nNi hao\nshi jie\n\n"
        "2\n00:00:03,000 --> 00:00:04,000\nSecond cue\n"
    )


def test_translate_script_resumes_from_existing_partial_output(tmp_path: Path) -> None:
    input_path = tmp_path / FIXTURE_PATH.name
    shutil.copyfile(FIXTURE_PATH, input_path)

    partial_path = tmp_path / "translate_script.input.zh-TW.partial.srt"
    write_text(
        partial_path,
        "1\n00:00:01,000 --> 00:00:02,500\nNi hao\nshi jie\n",
    )

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    write_resume_only_second_cue_fake_ollama(fake_bin / "ollama")

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

    output_path = tmp_path / "translate_script.input.zh-TW.srt"

    assert result.returncode == 0
    assert "warning: resuming from partial output at" in result.stderr
    assert "starting after cue 1" in result.stderr
    assert output_path.exists()
    assert not partial_path.exists()
    assert (
        output_path.read_text(encoding="utf-8")
        == "1\n00:00:01,000 --> 00:00:02,500\nNi hao\nshi jie\n\n"
        "2\n00:00:03,000 --> 00:00:04,000\nDi er ge ti shi\n"
    )


def test_translate_script_rejects_mismatched_partial_output(tmp_path: Path) -> None:
    input_path = tmp_path / FIXTURE_PATH.name
    shutil.copyfile(FIXTURE_PATH, input_path)

    partial_path = tmp_path / "translate_script.input.zh-TW.partial.srt"
    write_text(
        partial_path,
        "1\n00:00:09,000 --> 00:00:10,000\nBad partial\n",
    )

    result = run_translate_script(tmp_path, str(input_path), "zh-TW")

    assert result.returncode == 1
    assert "error: partial output does not match source cue order or timecodes:" in result.stderr


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
