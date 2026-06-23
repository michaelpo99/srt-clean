# docs/

This directory contains product and architecture specifications for `srt-clean`.

Codex should treat these documents as the source of truth before implementation.

## Files

```text
SDD-srt-clean.md
  Product specification. Defines CLI behavior, SRT parser behavior, rule types, actions, profiles, report format, decisions format, tests, exit codes, and roadmap.

SDD-ARCH-python-project-structure.md
  Architecture specification. Defines Python package layout, venv strategy, install scripts, development workflow, profile locations, README requirements, and P0 implementation order.

SDD-P0-implementation-plan.md
  P0 clarification and task plan. Defines final P0 decisions for ambiguous behavior, mode output matrix, hash rules, normalization order, conflict resolution, repeated_phrase algorithm, and task-by-task implementation plan.
```

## Reading order for implementation

Codex should read documents in this order:

```text
1. ../AGENTS.md
2. SDD-ARCH-python-project-structure.md
3. SDD-srt-clean.md
4. SDD-P0-implementation-plan.md
```

If `SDD-P0-implementation-plan.md` clarifies a P0 behavior that is ambiguous in another document, use the P0 clarification for implementation.

## Editing rules

When product behavior changes, update:

```text
docs/SDD-srt-clean.md
```

When architecture, packaging, install flow, or directory layout changes, update:

```text
docs/SDD-ARCH-python-project-structure.md
```

When P0 task sequence, implementation clarifications, or acceptance criteria change, update:

```text
docs/SDD-P0-implementation-plan.md
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

P0 implementation planning specs use:

```text
SDD-P0-<topic>.md
```

Future change requests may use:

```text
SDD-CR-###-<slug>.md
```

Future bug fix specs may use:

```text
SDD-BUGFIX-###-<slug>.md
```
