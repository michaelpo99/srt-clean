# src/srt_clean/

This directory contains the `srt_clean` Python package.

Keep modules small, deterministic, and testable. Avoid hidden global state.

## Module responsibilities

```text
models.py
  Shared dataclasses, enums, constants, and typed result objects.

parser.py
  Parse SRT text into Cue objects. Handle BOM, CRLF, multi-line text, and parse errors with line numbers.

writer.py
  Write Cue objects back to SRT. Re-number cue indexes from 1 and preserve timecodes.

normalize.py
  Normalize cue text for rule matching. Handle whitespace, Unicode normalization, punctuation stripping, long vowel marks, and optional lowercase behavior.

profile.py
  Load, resolve, and validate YAML profiles. Profile validation errors should be actionable.

rules.py
  Evaluate configured rule types against normalized cues. Produce rule matches, not file output.

actions.py
  Apply rule decisions to cues. Implement remove, keep, keep_first, keep_first_n, compress, and report.

decisions.py
  Write report-mode decisions YAML and read apply-mode decisions. Validate source and cue hashes.

report.py
  Produce human-readable report files with summary and details.

cli.py
  Parse CLI arguments and orchestrate parser -> profile -> rules -> actions -> writer/report.
```

## Separation rules

`parser.py` should not know about profiles.

`rules.py` should not write files.

`actions.py` should not parse CLI arguments.

`report.py` should not decide what to remove.

`cli.py` should orchestrate but should not contain rule logic.

## Error handling

Raise typed exceptions or return structured error results for:

```text
SRT parse errors
profile schema errors
unsupported rule types
unsupported actions
decisions conflicts
output path conflicts
```

User-facing CLI errors should include a clear next step.

## Testing expectation

Every module should have focused tests in `tests/`.

Do not rely only on end-to-end tests.
