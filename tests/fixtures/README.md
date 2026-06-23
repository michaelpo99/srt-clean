# tests/fixtures/

This directory contains small synthetic SRT fixtures for pytest.

Fixtures should be minimal and focused.

## Rules

Do:

```text
Use short artificial examples.
Cover one behavior per file when possible.
Keep files readable.
Name fixtures by behavior.
```

Do not:

```text
Commit full real-world transcripts.
Commit copyrighted transcript samples.
Commit audio or video files.
Use huge fixtures for small rule tests.
```

## Suggested fixtures

```text
jp_repeated_kana.srt
  Long repeated Japanese kana should be removed.

jp_protected_short.srt
  Protected semantic short phrases should be kept.

jp_repeated_phrase.srt
  Repeated semantic phrase should be compressed, not deleted.

en_dense_filler.srt
  Dense English low-information filler should be reduced.

en_protected_short.srt
  Meaningful English short phrases like no, stop, wait should be kept.

malformed_timecode.srt
  Parser should return a clear parse error.
```
