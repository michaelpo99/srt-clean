# bin/

This directory may contain local wrapper scripts for repository-based development.

The primary installed CLI entry point should come from `pyproject.toml`:

```toml
[project.scripts]
srt-clean = "srt_clean.cli:main"
```

## Planned wrapper

```text
bin/srt-clean
```

This wrapper is optional for P0. If implemented, it should only forward arguments to the Python package entry point.

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

Do not put rule engine logic in shell scripts.

Do not duplicate CLI argument parsing in shell.

Do not make this wrapper depend on user-specific absolute paths.

Formal installation should create a separate wrapper at:

```text
~/bin/srt-clean
```

that points to:

```text
~/.venvs/srt-clean/bin/srt-clean
```
