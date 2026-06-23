# AGENTS.md

This file gives Codex and other code-generation agents the project-specific rules for `srt-clean`.

Read this file before editing code. Also read the closest `README.md` in the directory you are modifying.

## Project purpose

`srt-clean` is a rule-based SRT subtitle cleaner for ASR output.

It removes, compresses, or reports low-information, dense, repeated, or likely hallucinated subtitle cues while preserving meaningful short phrases and original timecodes.

The tool does not perform ASR, translation, audio analysis, video analysis, or LLM-based semantic review.

## Primary specifications

Read these before implementation:

```text
docs/SDD-srt-clean.md
docs/SDD-ARCH-python-project-structure.md
```

`docs/SDD-srt-clean.md` defines product behavior, rule types, actions, profiles, reports, decisions, parser behavior, test expectations, and exit codes.

`docs/SDD-ARCH-python-project-structure.md` defines project layout, Python packaging, venv strategy, install scripts, README requirements, and P0 implementation order.

## Architecture decision

Use a Python application CLI architecture similar to `transcript-polish`.

Do not implement the core tool as a Bash orchestration script like `transcribe-audio`.

Use:

```text
Python >= 3.12
argparse
PyYAML
pytest
ruff
```

Do not add heavy dependencies unless the specs are updated.

Do not add FFmpeg, WhisperX, PyTorch, Transformers, or LLM dependencies to P0.

## Directory ownership

```text
README.md
  User-facing overview, installation, quick usage, and links to detailed docs.

AGENTS.md
  Agent instructions and implementation guardrails.

docs/
  Product and architecture specifications. Specs should be stable and detailed enough for Codex to implement from.

profiles/
  Built-in YAML rule profiles. Keep rules configurable; avoid hard-coding corpus-specific behavior in Python.

src/srt_clean/
  Python package implementation. Keep modules small and testable.

tests/
  pytest tests and SRT fixtures. Every rule type and action should have tests.

scripts/
  Install and uninstall scripts. Keep shell scripts thin and predictable.

bin/
  Optional local wrapper for repo-based execution. Main installed entry point should come from pyproject.toml.
```

## Implementation rules

1. Preserve original input SRT files by default.
2. Never overwrite input files unless an explicit future `--in-place` option is implemented with backup behavior.
3. Do not silently modify timecodes.
4. Re-number output cue indexes from 1 after deletion.
5. Keep protected semantic short phrases unless the user explicitly overrides through decisions.
6. Prefer deterministic rule behavior over model-based judgment.
7. Keep profile rules in YAML when possible; only add Python rule types when the current engine cannot express the required behavior.
8. Every new rule type must include tests.
9. Every action must be reflected in the report.
10. `clean` mode must not apply `review` severity unless an explicit option enables it.
11. `apply` mode must validate decisions against source hashes or cue hashes.
12. All user-visible errors should be actionable.

## P0 module expectations

Expected package modules:

```text
src/srt_clean/cli.py
src/srt_clean/parser.py
src/srt_clean/writer.py
src/srt_clean/normalize.py
src/srt_clean/profile.py
src/srt_clean/rules.py
src/srt_clean/actions.py
src/srt_clean/decisions.py
src/srt_clean/report.py
src/srt_clean/models.py
```

Keep responsibilities separated:

```text
parser.py
  Parse SRT into Cue objects.

writer.py
  Write cleaned Cue objects back to SRT.

normalize.py
  Normalize cue text for comparison.

profile.py
  Load and validate YAML profiles.

rules.py
  Evaluate rule matches.

actions.py
  Apply remove, keep, keep_first, keep_first_n, compress, and report actions.

decisions.py
  Read and write decisions YAML and validate hashes.

report.py
  Produce human-readable reports.

cli.py
  Parse arguments and orchestrate the pipeline.

models.py
  Shared dataclasses and typed constants.
```

## CLI behavior guardrails

Required P0 commands:

```bash
srt-clean --help
srt-clean --list-profiles
srt-clean --check --profile jp-adult-soft input.srt
srt-clean --mode report --profile jp-adult-soft input.srt
srt-clean --mode clean --profile jp-adult-soft --level moderate input.srt
srt-clean --mode apply --decisions input.clean-decisions.yml input.srt
```

Default behavior should be safe:

```text
mode=clean
level=moderate
profile=auto or explicit profile
preserve_original=true
```

If auto profile detection is not implemented yet, require `--profile` and print a clear error.

## Testing rules

Use pytest.

Minimum validation before considering work complete:

```bash
pytest
ruff check .
```

Every fixture should be small and focused. Do not commit large media files.

Do not add copyrighted transcript samples from real commercial content as full fixtures. Use short synthetic SRT snippets that reproduce the rule behavior.

## Documentation rules

When adding or changing behavior:

1. Update `docs/SDD-srt-clean.md` if product behavior changes.
2. Update `docs/SDD-ARCH-python-project-structure.md` if architecture, packaging, or install flow changes.
3. Update the nearest `README.md` if commands or directory responsibilities change.
4. Keep examples concise and runnable.

## Safety and content handling

This tool may process subtitles from many content types, including adult media, meetings, interviews, or translated captions. Implementation should operate on text patterns and timing only. Do not add content classification, moral judgment, or explicit-content-specific logic outside configurable profiles.

Use neutral naming such as `jp-adult-soft` only as a profile label for ASR-cleaning behavior. Keep rule explanations clinical and operational.

## Non-goals for P0

Do not implement these in P0 unless the specs are updated:

```text
LLM semantic review
translation
audio reading
video reading
GUI review
HTML report
Docker image
Conda environment
PyPI release
GitHub Actions
batch directory mode
merge_to_previous action
in-place overwrite
```
