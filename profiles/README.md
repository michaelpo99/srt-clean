# profiles/

This directory contains built-in YAML rule profiles for `srt-clean`.

Profiles define what to clean. Python code defines how to parse, evaluate, apply, and report rules.

## Planned built-in profiles

```text
jp-adult-soft.yml
  Japanese ASR cleanup profile. Focuses on repeated kana, non-semantic vocalizations, dense low-information cues, short hallucinations, and protected semantic short phrases.

en-adult-soft.yml
  English ASR cleanup profile. Focuses on low-information filler and repeated vocal sounds while protecting meaningful short phrases like no, stop, wait, please, and hurt.

en-translation-soft.yml
  Conservative profile for translated English SRT inspection. Focuses on repeated translated cues and model meta-output, not aggressive content cleanup.
```

## Profile principles

Keep rules configurable.

Do not hard-code corpus-specific word lists in Python when they can live in YAML.

Use protected rules for short phrases that may carry meaning.

Avoid unconditional deletion of short words.

A rule should usually combine text patterns with context such as:

```text
cue duration
text length
time window density
adjacent duplicate status
similarity to neighboring cue
known hallucination list
protected phrase list
```

## Required YAML shape

Profiles should follow the shape defined in:

```text
docs/SDD-srt-clean.md
```

Minimum structure:

```yaml
version: 1
profile: jp-adult-soft

defaults:
  mode: clean
  level: moderate

text_normalization: {}
levels: {}
protected: {}
lists: {}
rules: []
```

## Severity guidance

Use these severity values consistently:

```text
safe
  High-confidence automated cleanup.

likely_noise
  Likely low-information or hallucinated subtitle. Applied by moderate level.

dense_low_info
  Density-control cleanup. Applied only by aggressive level unless profile says otherwise.

review
  Report only. Do not auto-apply in normal clean mode.

protected
  Keep by default. Only explicit user decisions may override.
```

## Action guidance

P0 actions:

```text
remove
keep
keep_first
keep_first_n
compress
report
```

Do not add a new action in YAML unless the Python action engine supports it and tests cover it.

## Testing requirement

Every built-in profile rule should have at least one focused pytest fixture or unit test.

Do not use long real-world transcript samples as fixtures. Use short synthetic SRT snippets that reproduce the behavior.
