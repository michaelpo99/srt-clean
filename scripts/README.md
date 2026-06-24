# scripts/

This directory contains installation and maintenance scripts for `srt-clean`.

Scripts should be thin wrappers around Python packaging behavior. Do not put core application logic here.

## Scripts

```text
install.sh
  Create or update ~/.venvs/srt-clean, install this package, and create ~/bin/srt-clean plus ~/bin/translate-with-ollama.

uninstall.sh
  Remove ~/bin/srt-clean, remove ~/bin/translate-with-ollama, and optionally remove ~/.venvs/srt-clean.

check.sh
  Run repo validation with pytest and ruff check .
```

## install.sh requirements

The install script should:

1. Detect the repository root.
2. Check Python >= 3.12.
3. Create or reuse:

```text
~/.venvs/srt-clean
```

4. Upgrade pip, setuptools, and wheel.
5. Install the package from the repo root:

```bash
pip install -e "$REPO_ROOT"
```

6. If `--dev` is provided, install:

```bash
pip install -e "$REPO_ROOT[dev]"
```

7. Create:

```text
~/bin/srt-clean
```

8. Also create:

```text
~/bin/translate-with-ollama
```

9. Run smoke checks:

```bash
~/bin/srt-clean --help
~/bin/srt-clean --list-profiles
~/bin/translate-with-ollama --help
```

10. Warn if `~/bin` is not in PATH.

## uninstall.sh requirements

The uninstall script should:

1. Remove `~/bin/srt-clean`.
2. Remove `~/bin/translate-with-ollama`.
3. Ask before deleting `~/.venvs/srt-clean`, unless `--yes` is provided.
4. Never delete user SRT files, reports, decisions, or the repository.

## check.sh requirements

The check script should:

1. Work from the repo root.
2. Reuse or create `.venv`.
3. Install `.[dev]`.
4. Run:

```bash
pytest
ruff check .
```

## Shell style

Use Bash.

Start scripts with:

```bash
#!/usr/bin/env bash
set -euo pipefail
```

Prefer clear error messages and explicit paths.

Do not require root privileges.
