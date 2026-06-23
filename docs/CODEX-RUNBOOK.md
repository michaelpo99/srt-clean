# Codex Runbook

最後更新：2026-06-23

## 1. 目的

本文件是給使用者直接丟給 Codex 的執行手冊。

使用者不需要記住 Python 細節，也不需要自己寫 pytest fixtures。Codex 必須讀規格、實作功能、建立測試、跑檢查、修到通過，再回報結果。

## 2. Codex 必讀文件

每次 Codex 開工前都應讀：

```text
AGENTS.md
README.md
docs/SDD-ARCH-python-project-structure.md
docs/SDD-srt-clean.md
docs/SDD-P0-implementation-plan.md
docs/SDD-TESTING.md
```

## 3. 最小人工介入、但穩定的策略

不要一次叫 Codex 做完 Task 1 到 Task 11。

建議分成三個 implementation batches，加一個 install/docs batch：

```text
Batch A: Task 1-4
  project skeleton
  SRT parser/writer
  profile loader
  normalization

Batch B: Task 5-6
  rule engine
  actions
  conflict resolution

Batch C: Task 7-8
  report mode
  clean mode

Batch D: Task 9-11
  apply mode
  install scripts
  documentation pass
```

人工介入點只放在 batch 結束時。

每個 batch 結束時，只看三件事：

```text
pytest 是否通過
ruff check . 是否通過
Codex 是否清楚列出完成內容與限制
```

若 Task 10 後已經有 `scripts/check.sh`，改看：

```bash
bash scripts/check.sh
```

## 4. 為什麼不一次跑完

一次跑完 Task 1-11 的風險：

```text
parser 錯，後面的 rule tests 可能建立在錯資料上
normalization 錯，規則會大量誤判
protected 邏輯錯，會誤刪有語意短句
rule conflict resolution 錯，cleaned SRT 看似成功但內容不可信
apply mode 與 install script 會把問題混在一起，難以定位
```

分 batch 的目的不是讓使用者懂 Python，而是避免錯誤堆疊。

## 5. Batch A prompt

把下面整段丟給 Codex：

```text
Read AGENTS.md, README.md, docs/SDD-ARCH-python-project-structure.md, docs/SDD-srt-clean.md, docs/SDD-P0-implementation-plan.md, and docs/SDD-TESTING.md.

Implement Batch A only: Tasks 1 through 4.

Scope:
- Project skeleton
- pyproject.toml
- src/srt_clean package
- minimal CLI help
- SRT parser and writer
- strict profile loader
- built-in profile files
- deterministic normalization
- pytest tests and synthetic fixtures for these tasks

Do not implement Task 5 or later.
Do not implement rule application, clean mode, report mode, apply mode, install scripts, or documentation pass except where necessary for Batch A tests.

Create all required pytest tests and small synthetic fixtures yourself under tests/fixtures/.
Do not ask me to provide test files.
Do not use real commercial subtitle samples.

Run:
pytest
ruff check .

If either command fails, fix the issues and run again.
Stop only when both pass.

At the end, report:
1. Files changed
2. Completed tasks
3. pytest result
4. ruff result
5. Known limitations
```

## 6. Batch B prompt

Use after Batch A passes.

```text
Read AGENTS.md, README.md, docs/SDD-ARCH-python-project-structure.md, docs/SDD-srt-clean.md, docs/SDD-P0-implementation-plan.md, and docs/SDD-TESTING.md.

Implement Batch B only: Tasks 5 and 6.

Scope:
- Rule engine P0 base rules
- regex_text
- single_cue
- text_in_list
- protected_text
- adjacent_duplicate
- density_window
- repeated_phrase
- actions.py
- remove, keep, keep_first, keep_first_n, compress, report
- deterministic conflict resolution
- protected blocks automatic remove
- remove wins over compress
- review does not modify output
- pytest tests and synthetic fixtures for these tasks

Do not implement report mode, clean mode, apply mode, install scripts, or documentation pass.

Create all required pytest tests and small synthetic fixtures yourself under tests/fixtures/.
Do not ask me to provide test files.
Do not use real commercial subtitle samples.

Run:
pytest
ruff check .

If either command fails, fix the issues and run again.
Stop only when both pass.

At the end, report:
1. Files changed
2. Completed tasks
3. pytest result
4. ruff result
5. Known limitations
```

## 7. Batch C prompt

Use after Batch B passes.

```text
Read AGENTS.md, README.md, docs/SDD-ARCH-python-project-structure.md, docs/SDD-srt-clean.md, docs/SDD-P0-implementation-plan.md, and docs/SDD-TESTING.md.

Implement Batch C only: Tasks 7 and 8.

Scope:
- report.py
- decisions.py write path for report mode
- source_sha256 and text_sha256 exactly as specified
- --mode report
- --mode clean
- clean mode full pipeline
- .clean-report.txt output
- .clean-decisions.yml output for report mode only
- .cleaned.srt output for clean mode only
- --level conservative|moderate|aggressive
- --output
- --report-output
- --force
- output-exists-without-force failure
- pytest tests and synthetic fixtures for these tasks

Do not implement apply mode, install scripts, or documentation pass.
Do not implement unsupported P0 options: --in-place, --preview-output, --allow-stale-decisions, --include-review, or profile auto detection.

Create all required pytest tests and small synthetic fixtures yourself under tests/fixtures/.
Do not ask me to provide test files.
Do not use real commercial subtitle samples.

Run:
pytest
ruff check .

If either command fails, fix the issues and run again.
Stop only when both pass.

At the end, report:
1. Files changed
2. Completed tasks
3. pytest result
4. ruff result
5. Example command tested, preferably:
   srt-clean --profile jp-adult-soft --level moderate <fixture>.srt
6. Known limitations
```

## 8. Batch D prompt

Use after Batch C passes and the user is satisfied with clean mode.

```text
Read AGENTS.md, README.md, docs/SDD-ARCH-python-project-structure.md, docs/SDD-srt-clean.md, docs/SDD-P0-implementation-plan.md, and docs/SDD-TESTING.md.

Implement Batch D only: Tasks 9 through 11.

Scope:
- apply mode
- decisions.py read path
- source hash validation
- cue identity validation
- protected override reporting
- scripts/install.sh
- scripts/uninstall.sh
- scripts/check.sh
- optional bin/srt-clean wrapper
- documentation pass to align README files with implemented P0 behavior
- tests and smoke checks for this batch

Do not implement future roadmap features.
Do not implement unsupported P0 options unless the existing specs explicitly require them.

Create all required pytest tests and small synthetic fixtures yourself under tests/fixtures/.
Do not ask me to provide test files.
Do not use real commercial subtitle samples.

Run:
pytest
ruff check .

If scripts/check.sh exists, also run:
bash scripts/check.sh

If any command fails, fix the issues and run again.
Stop only when all checks pass.

At the end, report:
1. Files changed
2. Completed tasks
3. pytest result
4. ruff result
5. scripts/check.sh result
6. install/uninstall smoke result if run
7. Known limitations
```

## 9. Optional faster plan

If the user wants fewer interactions, use this two-batch plan:

```text
Fast Batch 1: Tasks 1-6
Fast Batch 2: Tasks 7-11
```

This is faster but less stable.

Do not use a single Task 1-11 run unless the user accepts higher risk.

## 10. Manual check after Batch C

After Batch C, the user may test one private real SRT outside the repo:

```bash
srt-clean --profile jp-adult-soft --level moderate sample-real-01.srt
```

The user should check only:

```text
original SRT is unchanged
.cleaned.srt exists
.clean-report.txt exists
obvious repeated low-information cues are reduced
protected short phrases are not obviously removed
report is understandable
```

Do not commit private real SRT samples.

## 11. What counts as success

Minimum useful success is Batch C passing.

At that point:

```bash
srt-clean --profile jp-adult-soft --level moderate sample.srt
```

should produce:

```text
sample.cleaned.srt
sample.clean-report.txt
```

Full P0 success is Batch D passing.

At that point, the project should support:

```bash
srt-clean --mode report --profile jp-adult-soft sample.srt
vi sample.clean-decisions.yml
srt-clean --mode apply --decisions sample.clean-decisions.yml sample.srt
bash scripts/check.sh
```
