# src/

This directory contains the Python source package for `srt-clean`.

Use a standard `src` layout:

```text
src/
└── srt_clean/
    ├── __init__.py
    ├── cli.py
    ├── parser.py
    ├── writer.py
    ├── normalize.py
    ├── profile.py
    ├── rules.py
    ├── actions.py
    ├── decisions.py
    ├── report.py
    └── models.py
```

## Rules

Do not place executable Python modules directly under `src/`.

All package code belongs under:

```text
src/srt_clean/
```

Tests belong under:

```text
tests/
```

Built-in user-editable profiles belong under:

```text
profiles/
```

## Development install

From the repo root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

After that, the command should resolve through `pyproject.toml`:

```bash
srt-clean --help
```
