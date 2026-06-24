# bin/

This directory contains repo-local executable entrypoints for repository-based development.

The primary installed CLI entry point should come from `pyproject.toml`:

```toml
[project.scripts]
srt-clean = "srt_clean.cli:main"
```

## Local executables

```text
bin/srt-clean
bin/translate-with-ollama
```

`bin/srt-clean` is an optional wrapper. If implemented, it should only forward arguments to the Python package entry point.

`bin/translate-with-ollama` is the repo-local subtitle translation helper. It may contain shell-side orchestration for invoking `ollama`, but it must not contain `srt-clean` rule engine logic. When a matching `*.partial.srt` file exists, it should resume from that partial output by default.

Suggested behavior:

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$REPO_ROOT"
exec "$PYTHON_BIN" -m srt_clean.cli "$@"
```

## Rules

Do not put `srt-clean` rule engine logic in shell scripts.

Do not make this wrapper depend on user-specific absolute paths.

Formal installation should create a separate wrapper at:

```text
~/bin/srt-clean
```

that points to:

```text
~/.venvs/srt-clean/bin/srt-clean
```
