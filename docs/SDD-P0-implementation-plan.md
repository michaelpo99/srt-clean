# SDD-P0: Implementation Clarifications and Task Plan

最後更新：2026-06-23

## 1. 目的

本文件補強 P0 實作前必須定義清楚的行為，並把 Codex 實作拆成可驗收的 task。

本文件不是 CR，因為目前尚未有既有程式碼需要變更。這是 P0 初始實作規格的一部分。

主要規格仍是：

```text
docs/SDD-srt-clean.md
docs/SDD-ARCH-python-project-structure.md
```

若本文件與上述文件衝突，P0 以本文件的 clarifications 為準，並應在後續整理時回填到主要 SDD。

## 2. P0 明確決策

### 2.1 P0 不實作 profile auto detection

`docs/SDD-srt-clean.md` 曾描述預設 `profile=auto`。P0 不實作 auto detection。

P0 行為：

```text
若 --profile 未指定，CLI 必須失敗，列出可用 profiles，並提示使用者明確指定 --profile。
```

理由：

1. 日文、英文、翻譯後英文可能混雜。
2. 自動判斷容易誤用 aggressive profile。
3. 清理工具會刪除或壓縮字幕，預設不應猜測語言。

P0 可用 profiles：

```text
jp-adult-soft
en-adult-soft
en-translation-soft
```

未來若要加入 auto，必須另立規格，明確定義偵測邏輯、信心門檻與 fallback。

### 2.2 輸出檔已存在時的行為

若輸出檔已存在且未指定 `--force`，CLI 必須失敗，不得覆蓋、不得自動改名、不得跳過。

適用輸出檔：

```text
<stem>.cleaned.srt
<stem>.clean-report.txt
<stem>.apply-report.txt
<stem>.clean-decisions.yml
```

錯誤訊息必須指出：

```text
已存在的檔案路徑
可用 --force 覆蓋
或可用 --output / --report-output 指定其他位置
```

Exit code：

```text
1
```

### 2.3 P0 不實作 --in-place

`--in-place` 在 P0 不實作。

若使用者指定 `--in-place`，CLI 應回傳 CLI 參數錯誤：

```text
--in-place is not supported in P0
```

Exit code：

```text
2
```

未來若實作 `--in-place`，必須建立 `.bak`，並另立規格。

### 2.4 P0 不實作 --preview-output

`report` 模式只產生：

```text
<stem>.clean-report.txt
<stem>.clean-decisions.yml
```

P0 不實作 `--preview-output`。

若使用者指定 `--preview-output`，CLI 應回傳 CLI 參數錯誤或先不提供此參數。

### 2.5 P0 不實作 --allow-stale-decisions

P0 `apply` 模式要求 decisions 檔與 input 完全匹配。

若 `source_sha256` 不一致，直接失敗。

P0 不提供 `--allow-stale-decisions`。

未來若需要 stale decisions，必須另立規格。

### 2.6 P0 不實作 --dry-run 獨立行為

P0 可以不提供 `--dry-run`。

`report` 模式即為 dry-run 行為。

若提供 `--dry-run`，它必須完全等同：

```text
--mode report
```

但 P0 建議先不提供，避免 CLI 重複語意。

### 2.7 P0 不實作 --include-review

P0 `clean` 模式不得套用 `severity=review` 的項目。

`--include-review` 可列在 roadmap，但 P0 不實作。

若指定此參數，CLI 應回傳 CLI 參數錯誤，或先不提供。

## 3. Mode output matrix

P0 模式行為如下。

| Mode | Need `--profile` | Need `--decisions` | Writes cleaned SRT | Writes report | Writes decisions | Applies rules | Applies decisions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `report` | yes | no | no | yes, `.clean-report.txt` | yes, `.clean-decisions.yml` | yes, to generate candidates only | no |
| `clean` | yes | no | yes, `.cleaned.srt` | yes, `.clean-report.txt` | no | yes | no |
| `apply` | no | yes | yes, `.cleaned.srt` | yes, `.apply-report.txt` | no | no | yes |

Additional rules:

1. `apply` mode does not load profile by default.
2. `apply` mode may read profile metadata from decisions for reporting only, but must not re-evaluate profile rules.
3. `clean` mode must not write decisions.
4. `report` mode must not write cleaned SRT.
5. All modes must preserve the original input file.

## 4. Hash definitions

### 4.1 source_sha256

`source_sha256` is computed from the exact input file bytes.

Algorithm:

```python
hashlib.sha256(path.read_bytes()).hexdigest()
```

Do not normalize line endings before source hash calculation.

### 4.2 text_sha256

`text_sha256` is computed from the original cue text lines joined with `\n` and encoded as UTF-8.

Algorithm:

```python
text_for_hash = "\n".join(cue.raw_text_lines)
text_sha256 = hashlib.sha256(text_for_hash.encode("utf-8")).hexdigest()
```

Do not use normalized text for `text_sha256`.

### 4.3 cue identity in decisions

A decision entry must include:

```yaml
cue: 54
start: "00:25:21,413"
end: "00:25:50,050"
text_sha256: "..."
```

P0 apply validation requires all of these to match.

If any mismatch occurs, fail with exit code 5 and do not write cleaned output.

## 5. Normalization order

P0 must use deterministic normalization.

For each cue text:

1. Join raw text lines with a single space for `text`.
2. Trim leading and trailing whitespace if `trim=true`.
3. Apply `unicodedata.normalize("NFKC", text)` if `normalize_fullwidth=true`.
4. Collapse consecutive whitespace to a single ASCII space if `collapse_spaces=true`.
5. Apply lowercase if `lowercase=true`.
6. Strip only outer punctuation if `strip_outer_punctuation=true`.
7. Build `normalized_text` from the result.
8. Build `compact_text` by removing whitespace and comparison-only punctuation.

`normalize_long_vowels=true` must not mutate `normalized_text` in P0.

It only affects `compact_text` and regex comparison helpers by treating these marks as comparable extension marks:

```text
ー
〜
~
…
-
```

Do not change output subtitle text during normalization. Output text changes only through actions such as `compress`.

## 6. Profile schema validation policy

P0 must validate profiles strictly.

The following are profile schema errors and must exit with code 4:

1. Missing required top-level fields: `version`, `profile`, `rules`.
2. Unsupported `version`.
3. Unknown `severity`.
4. Unknown `match.type`.
5. Unknown `action.type`.
6. Regex compile error.
7. `text.in_list`, `text.not_in_list`, or `match.list` referencing a missing list.
8. Rule missing `id`.
9. Duplicate rule `id`.
10. Rule missing `match` or `action`.
11. Invalid numeric values, such as negative duration or window size.

P0 should treat unknown fields as errors, not warnings.

Reason: typo-tolerance is dangerous in a rule engine that removes text.

## 7. Rule conflict resolution

P0 must use deterministic conflict resolution.

### 7.1 Evaluation phase

1. Parse SRT into cues.
2. Normalize cues.
3. Evaluate protected rules first.
4. Evaluate all other rules and produce candidate rule matches.
5. Do not mutate cue text during rule evaluation.

### 7.2 Merge phase

For each cue:

1. If cue is protected, automatic `remove` is blocked.
2. If cue has one or more allowed `remove` candidates, choose the highest-priority candidate as the primary decision.
3. Store other matching rule IDs as secondary reasons in the report.
4. If cue is marked for remove, do not apply `compress`.
5. If cue is not removed and has one or more `compress` candidates, apply one compress action.
6. If multiple compress candidates exist, apply the first rule order match.
7. `report` candidates do not modify output.

### 7.3 Rule priority

P0 priority order:

```text
protected_text
regex_text remove safe
text_in_list remove safe
single_cue remove safe
adjacent_duplicate keep_first safe
regex_text remove likely_noise
text_in_list remove likely_noise
single_cue remove likely_noise
repeated_phrase compress
adjacent_similarity report
density_window keep_first_n
review report
```

If implementation uses profile rule order, it must still enforce:

```text
protected blocks auto remove
remove wins over compress
compress wins over report
review does not auto-apply
```

### 7.4 Density groups

For `density_window`:

1. A cue may appear in multiple overlapping windows.
2. The implementation must deduplicate removals.
3. A cue removed by a stronger rule should not receive a separate density decision.
4. Protected cues must not be removed by density rules.
5. Report should include density group start/end and group size when available.

## 8. repeated_phrase P0 algorithm

P0 repeated phrase detection must be simple and deterministic.

Supported P0 cases:

### 8.1 Whole-text repeated substring

Detect when the entire compact text is composed of the same substring repeated at least `min_repeats` times.

Example:

```text
気持ちいい気持ちいい気持ちいい気持ちいい
```

compresses to:

```text
気持ちいい
```

### 8.2 Separator-based repeated phrase

Detect when text contains repeated phrases separated by whitespace or punctuation.

Example:

```text
sorry, sorry, sorry, sorry
```

compresses to:

```text
sorry
```

### 8.3 Non-goals for P0 repeated_phrase

P0 must not attempt Japanese morphological segmentation.

P0 must not infer semantic repetition.

P0 must not compress a phrase if doing so would produce empty text.

If a cue also matches a stronger remove rule, remove wins.

## 9. en-translation-soft P0 boundary

`en-translation-soft` is a single-file inspection profile in P0.

It may detect:

1. Adjacent duplicate translated text.
2. Model meta-output such as `Translation:`, `Here is`, `Note:`, or `<think>`.
3. Empty cue text.

It must not claim to verify source/target cue count consistency in P0, because P0 only accepts one SRT input file.

Cue count and timecode consistency between source and translated SRT belongs to `translate-srt` or a future dual-file validator.

## 10. Report requirements clarified

P0 report must include:

```text
source
source_sha256
profile
mode
level when applicable
total_cues
output_cues when applicable
removed_cues
compressed_cues
protected_cues
review_cues
rule_summary
detail entries
warnings
```

Each detail entry must include:

```text
decision id
original cue index
time range
rule id
severity
action
short text preview
reason_zh
```

For compressed entries, include before and after previews.

For protected entries, include `action=keep`.

For blocked removals due to protected status, include `blocked_by_protected=true`.

## 11. Fixture policy

Tests must use short synthetic SRT fixtures.

Do not commit:

1. Full real-world subtitles.
2. Commercial transcript samples.
3. Audio files.
4. Video files.
5. Large generated fixtures.

Synthetic fixtures should be short and focused. One fixture should usually cover one behavior.

## 12. P0 task plan

P0 should be implemented as multiple small tasks, not one large Codex run.

Reason:

1. Parser and writer behavior can be tested independently.
2. Profile schema errors need strict tests.
3. Rule engine conflict resolution is easy to break if implemented together with CLI.
4. Decisions/apply mode is a separate concern.
5. Install script should be added after CLI is functional.

## 13. Task breakdown

### Task 1: Project skeleton

Goal:

```text
Create installable Python package with minimal CLI.
```

Scope:

1. `pyproject.toml`.
2. `src/srt_clean/__init__.py`.
3. `src/srt_clean/cli.py`.
4. `src/srt_clean/models.py`.
5. Basic `srt-clean --help`.
6. Minimal tests wiring.

Acceptance:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
srt-clean --help
pytest
ruff check .
```

### Task 2: SRT parser and writer

Goal:

```text
Parse and write SRT without cleaning.
```

Scope:

1. `parser.py`.
2. `writer.py`.
3. timecode parse/format helpers.
4. parser errors with line numbers.
5. BOM and CRLF support.
6. cue re-numbering on write.

Acceptance:

1. Basic SRT parse test passes.
2. Multi-line cue test passes.
3. CRLF/BOM test passes.
4. malformed timecode returns exit code 3 through CLI or parser-level error.

### Task 3: Profile loader and built-in profiles

Goal:

```text
Load strict YAML profiles and list built-in profiles.
```

Scope:

1. `profile.py`.
2. `profiles/jp-adult-soft.yml`.
3. `profiles/en-adult-soft.yml`.
4. `profiles/en-translation-soft.yml`.
5. `srt-clean --list-profiles`.
6. `srt-clean --check --profile <name> input.srt`.

Acceptance:

1. Known profiles list correctly.
2. Missing profile fails clearly.
3. Invalid profile schema exits code 4.
4. Unknown rule type exits code 4.
5. Regex compile error exits code 4.

### Task 4: Normalization

Goal:

```text
Generate normalized_text and compact_text deterministically.
```

Scope:

1. `normalize.py`.
2. profile-controlled normalization flags.
3. tests for whitespace, NFKC, lowercase, punctuation stripping, compact text.

Acceptance:

1. Japanese normalization tests pass.
2. English lowercase tests pass.
3. Normalization does not mutate output text.

### Task 5: Rule engine P0 base rules

Goal:

```text
Evaluate P0 rule types and produce rule matches without applying changes.
```

Scope:

1. `rules.py`.
2. rule types:
   - `regex_text`
   - `single_cue`
   - `text_in_list`
   - `protected_text`
   - `adjacent_duplicate`
   - `density_window`
   - `repeated_phrase`
3. conflict-independent match generation.

Acceptance:

1. Japanese repeated kana matches remove candidate.
2. Protected short phrase matches protected.
3. English filler matches profile rule.
4. Missing list reference fails during profile validation.

### Task 6: Actions and conflict resolution

Goal:

```text
Apply remove, keep, keep_first, keep_first_n, compress, and report deterministically.
```

Scope:

1. `actions.py`.
2. conflict resolution rules from this document.
3. protected blocks automatic remove.
4. remove wins over compress.
5. compress only changes text, not timecode.

Acceptance:

1. Long `あああ...` removed.
2. `気持ちいい気持ちいい...` compressed.
3. `痛い` kept protected.
4. density rule removes only allowed cues.
5. output cue indexes are continuous.

### Task 7: Report mode and report output

Goal:

```text
Generate human-readable clean reports and decisions YAML.
```

Scope:

1. `report.py`.
2. report summary.
3. report details.
4. `decisions.py` write path.
5. source and cue hashes.
6. `--mode report`.

Acceptance:

1. Report mode writes `.clean-report.txt`.
2. Report mode writes `.clean-decisions.yml`.
3. Report mode does not write `.cleaned.srt`.
4. Existing outputs fail without `--force`.

### Task 8: Clean mode

Goal:

```text
Run full parser -> profile -> normalize -> rules -> actions -> writer/report pipeline.
```

Scope:

1. `--mode clean`.
2. `--level conservative|moderate|aggressive`.
3. `--output`.
4. `--report-output`.
5. `--force`.

Acceptance:

1. Clean mode writes `.cleaned.srt`.
2. Clean mode writes `.clean-report.txt`.
3. Clean mode does not write decisions.
4. Review severity is not applied.
5. Existing output fails without `--force`.

### Task 9: Apply mode

Goal:

```text
Apply edited decisions file without re-running profile rules.
```

Scope:

1. `decisions.py` read path.
2. source hash validation.
3. cue identity validation.
4. protected override reporting.
5. `--mode apply`.

Acceptance:

1. Apply writes `.cleaned.srt`.
2. Apply writes `.apply-report.txt`.
3. Source hash mismatch exits code 5.
4. Protected override is allowed only from explicit decision and is reported.
5. Apply mode does not require `--profile`.

### Task 10: Install scripts

Goal:

```text
Install CLI into ~/.venvs/srt-clean and ~/bin/srt-clean.
```

Scope:

1. `scripts/install.sh`.
2. `scripts/uninstall.sh`.
3. optional `bin/srt-clean` wrapper.
4. smoke tests.

Acceptance:

```bash
bash scripts/install.sh
srt-clean --help
srt-clean --list-profiles
bash scripts/uninstall.sh --yes
```

### Task 11: Documentation pass

Goal:

```text
Update README files to match implemented behavior.
```

Scope:

1. root `README.md`.
2. `docs/README.md`.
3. `profiles/README.md` if profile behavior changed.
4. `AGENTS.md` if implementation rules changed.

Acceptance:

1. All documented commands exist or are clearly marked future.
2. No P0 unsupported option is shown as implemented.
3. P0 limitations are visible.

## 14. Suggested execution strategy

Run Codex task-by-task.

Do not ask Codex to implement all P0 at once.

Recommended prompt pattern:

```text
Read AGENTS.md, docs/SDD-srt-clean.md, docs/SDD-ARCH-python-project-structure.md, and docs/SDD-P0-implementation-plan.md. Implement Task N only. Add tests for the task. Do not implement later tasks unless needed for task acceptance.
```

After each task:

```bash
pytest
ruff check .
```

Commit after each task if tests pass.

## 15. Minimum useful milestone

The first useful milestone is after Task 8.

At that point, users can run:

```bash
srt-clean --profile jp-adult-soft --level moderate sample.srt
```

and get:

```text
sample.cleaned.srt
sample.clean-report.txt
```

Task 9 adds manual partial review through decisions.

Task 10 makes installation user-friendly.
