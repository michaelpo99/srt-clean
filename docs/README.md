# docs/

This directory contains product and architecture specifications for `srt-clean`.

Codex should treat these documents as the source of truth before implementation.

## Files

```text
SDD-srt-clean.md
  Product specification. Defines CLI behavior, SRT parser behavior, rule types, actions, profiles, report format, decisions format, tests, exit codes, and roadmap.

SDD-ARCH-python-project-structure.md
  Architecture specification. Defines Python package layout, venv strategy, install scripts, development workflow, profile locations, README requirements, and P0 implementation order.
```

## Editing rules

When product behavior changes, update:

```text
docs/SDD-srt-clean.md
```

When architecture, packaging, install flow, or directory layout changes, update:

```text
docs/SDD-ARCH-python-project-structure.md
```

Do not bury product requirements only in code comments or tests. If a behavior is intentional and user-visible, document it here.

## Document style

Use precise implementation language.

Prefer:

```text
The CLI must write <stem>.cleaned.srt.
```

Avoid vague wording such as:

```text
The CLI should probably make a cleaned file.
```

## Numbering convention

General specs use:

```text
SDD-<topic>.md
```

Architecture specs use:

```text
SDD-ARCH-<topic>.md
```

Future change requests may use:

```text
SDD-CR-###-<slug>.md
```

Future bug fix specs may use:

```text
SDD-BUGFIX-###-<slug>.md
```
