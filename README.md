# srt-clean

`srt-clean` is a rule-based SRT subtitle cleaner for ASR output.

It removes, compresses, or reports low-information, dense, repeated, or likely hallucinated subtitle cues while preserving meaningful short phrases and original timecodes.

The first target use case is cleaning Whisper / WhisperX `.srt` output where long-form audio, background noise, repeated non-semantic vocalizations, filler sounds, or ASR hallucinations create subtitles that are too dense or distracting.

## Product boundary

`srt-clean` does:

- Parse `.srt` files.
- Apply YAML-configured cleaning rules.
- Preserve original input files by default.
- Output cleaned SRT files.
- Output human-readable reports.
- Support review and partial application through decisions files.
- Support Japanese and English cleaning profiles.

`srt-clean` does not:

- Run ASR.
- Translate subtitles.
- Read audio or video.
- Use LLMs for semantic judgment.
- Rewrite normal subtitle text for style.
- Change timecodes unless a future explicit feature is specified.

## Documentation

Read these first:

```text
docs/SDD-srt-clean.md
docs/SDD-ARCH-python-project-structure.md
AGENTS.md
```

Purpose of each document:

```text
docs/SDD-srt-clean.md
  Product behavior, rule engine, profiles, report format, decisions, parser behavior, tests, and exit codes.

docs/SDD-ARCH-python-project-structure.md
  Python package structure, venv strategy, install scripts, development workflow, and P0 implementation order.

AGENTS.md
  Codex / agent implementation rules and guardrails.
```

## Planned project layout

```text
srt-clean/
├── README.md
├── AGENTS.md
├── AGENT.md
├── pyproject.toml
├── bin/
│   └── srt-clean
├── scripts/
│   ├── install.sh
│   └── uninstall.sh
├── docs/
│   ├── README.md
│   ├── SDD-srt-clean.md
│   └── SDD-ARCH-python-project-structure.md
├── profiles/
│   ├── README.md
│   ├── jp-adult-soft.yml
│   ├── en-adult-soft.yml
│   └── en-translation-soft.yml
├── src/
│   ├── README.md
│   └── srt_clean/
│       ├── README.md
│       ├── __init__.py
│       ├── cli.py
│       ├── parser.py
│       ├── writer.py
│       ├── normalize.py
│       ├── profile.py
│       ├── rules.py
│       ├── actions.py
│       ├── decisions.py
│       ├── report.py
│       └── models.py
└── tests/
    ├── README.md
    ├── test_parser.py
    ├── test_writer.py
    ├── test_normalize.py
    ├── test_rules_jp.py
    ├── test_rules_en.py
    ├── test_decisions.py
    └── fixtures/
        └── README.md
```

## Development setup

Use Python 3.12.3+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -e ".[dev]"
```

Validate:

```bash
srt-clean --help
srt-clean --list-profiles
pytest
ruff check .
```

## Planned installation

Formal installation should use a dedicated venv:

```text
~/.venvs/srt-clean
```

and create this wrapper:

```text
~/bin/srt-clean
```

Expected install command:

```bash
bash scripts/install.sh
```

After installation, users should not need to manually activate the venv.

## Planned CLI examples

Clean Japanese ASR subtitles:

```bash
srt-clean --profile jp-adult-soft --level moderate sample.srt
```

Generate report and decisions for review:

```bash
srt-clean --mode report --profile jp-adult-soft sample.srt
vi sample.clean-decisions.yml
srt-clean --mode apply --decisions sample.clean-decisions.yml sample.srt
```

Clean English ASR subtitles:

```bash
srt-clean --profile en-adult-soft --level conservative sample.en.srt
```

Inspect translated English subtitles:

```bash
srt-clean --profile en-translation-soft --mode report sample.translated.en.srt
```

## Relationship to other tools

Recommended pipeline:

```text
audio / video
  -> transcribe-audio / WhisperX
  -> raw SRT
  -> srt-clean
  -> cleaned SRT
  -> translate-srt
  -> translated SRT
```

`srt-clean` is independent from `transcribe-audio`, but it may later be called by `transcribe-audio` as an optional post-processing step.

## P0 implementation status

Current implemented scope:

```text
Batch A
  Python package skeleton
  minimal CLI help / --list-profiles / --check
  SRT parser and writer
  strict profile loader
  deterministic normalization
```

Still pending:

```text
Batch B
  rule engine
  actions

Batch C
  report mode
  clean mode

Batch D
  apply mode
  install scripts
  documentation pass
```
