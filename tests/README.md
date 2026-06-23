# tests/

This directory contains pytest tests for `srt-clean`.

Tests are part of the specification. When adding a rule type, action, parser behavior, report behavior, or decisions behavior, add or update tests.

## Expected test files

```text
test_parser.py
  SRT parsing, BOM handling, CRLF handling, multi-line text, malformed timecodes, and parse errors.

test_writer.py
  SRT output formatting, cue re-numbering, timecode preservation, and deletion behavior.

test_normalize.py
  Unicode normalization, whitespace handling, punctuation stripping, lowercase behavior, and compact text generation.

test_rules_jp.py
  Japanese built-in profile rules and protected phrases.

test_rules_en.py
  English built-in profile rules and protected phrases.

test_decisions.py
  report-mode decisions output, apply-mode decisions input, hash validation, conflicts, and protected override behavior.
```

## Fixture rules

Fixtures belong under:

```text
tests/fixtures/
```

Use short synthetic SRT files.

Do not commit full transcripts from commercial media.

Do not commit audio or video files.

Prefer one behavior per fixture.

## Required validation

Before considering implementation complete:

```bash
pytest
ruff check .
```

## Testing philosophy

Prefer deterministic tests.

Do not depend on external services.

Do not depend on the current date or local timezone unless explicitly testing timestamp generation.

Do not require network access.
