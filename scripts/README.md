# scripts/

This directory contains installation and maintenance scripts for `srt-clean`.

Scripts should be thin wrappers around Python packaging behavior. Do not put core application logic here.

## Planned scripts

```text
install.sh
  Create or update ~/.venvs/srt-clean, install this package, and create ~/bin/srt-clean.

uninstall.sh
  Remove ~/bin/srt-clean and optionally remove ~/.venvs/srt-clean.
```

## install.sh requirements

The install script should:

1. Detect the repository root.
2. Check Python >= 3.11.
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

8. Run smoke checks:

```bash
~/bin/srt-clean --help
~/bin/srt-clean --list-profiles
```

9. Warn if `~/bin` is not in PATH.

## uninstall.sh requirements

The uninstall script should:

1. Remove `~/bin/srt-clean`.
2. Ask before deleting `~/.venvs/srt-clean`, unless `--yes` is provided.
3. Never delete user SRT files, reports, decisions, or the repository.

## Shell style

Use Bash.

Start scripts with:

```bash
#!/usr/bin/env bash
set -euo pipefail
```

Prefer clear error messages and explicit paths.

Do not require root privileges.
