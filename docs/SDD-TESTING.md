# SDD: Testing Strategy

最後更新：2026-06-23

## 1. 目的

本文件定義 `srt-clean` 的測試策略、測試資料位置、expected output 慣例、pytest 測試要求，以及使用者如何用最少人工介入確認品質。

本專案的測試不是由使用者手動準備。Codex / AI 在實作每個 task 時，必須依照規格自行建立小型 synthetic fixtures、expected outputs 與 pytest 測試。

## 2. 測試答案從哪裡來

測試答案來自規格，而不是模型自由判斷。

主要依據：

```text
AGENTS.md
docs/SDD-srt-clean.md
docs/SDD-ARCH-python-project-structure.md
docs/SDD-P0-implementation-plan.md
docs/SDD-TESTING.md
```

例如規格定義：

```text
長串 ああああああああ 應被 remove。
痛い 應被 protected keep。
気持ちいい気持ちいい気持ちいい気持ちいい 應 compress 成 気持ちいい。
輸出 cue index 必須從 1 開始連續重編。
原始 input.srt 不得被覆蓋。
輸出檔存在且未 --force 時必須失敗。
```

測試必須把這些行為轉成可自動驗證的 cases。

## 3. 測試檔案位置

pytest 測試程式放在：

```text
tests/
```

測試資料放在：

```text
tests/fixtures/
```

建議結構：

```text
tests/
├── test_parser.py
├── test_writer.py
├── test_normalize.py
├── test_profile.py
├── test_rules_jp.py
├── test_rules_en.py
├── test_clean_mode.py
├── test_report_mode.py
├── test_apply_mode.py
└── fixtures/
    ├── jp_repeated_kana.input.srt
    ├── jp_repeated_kana.expected.cleaned.srt
    ├── jp_protected_short.input.srt
    ├── jp_protected_short.expected.cleaned.srt
    ├── jp_repeated_phrase.input.srt
    ├── jp_repeated_phrase.expected.cleaned.srt
    ├── en_dense_filler.input.srt
    ├── en_dense_filler.expected.cleaned.srt
    └── malformed_timecode.input.srt
```

## 4. Fixture policy

Tests must use short synthetic SRT fixtures.

Do not commit:

```text
full real-world subtitles
commercial subtitle samples
audio files
video files
large generated fixtures
user-provided private SRT samples
```

Use small artificial examples that reproduce one behavior.

Good fixture:

```srt
1
00:00:01,000 --> 00:00:02,000
ああああああああ

2
00:00:03,000 --> 00:00:04,000
痛い
```

Bad fixture:

```text
A full subtitle file copied from a real video.
```

## 5. Expected output convention

For behavior that writes cleaned SRT, create expected output files.

Naming:

```text
<case>.input.srt
<case>.expected.cleaned.srt
```

Example input:

```text
tests/fixtures/jp_repeated_phrase.input.srt
```

```srt
1
00:00:01,000 --> 00:00:03,000
気持ちいい気持ちいい気持ちいい気持ちいい

2
00:00:04,000 --> 00:00:05,000
痛い
```

Expected output:

```text
tests/fixtures/jp_repeated_phrase.expected.cleaned.srt
```

```srt
1
00:00:01,000 --> 00:00:03,000
気持ちいい

2
00:00:04,000 --> 00:00:05,000
痛い
```

pytest should compare actual output against expected output.

## 6. What Codex must test per task

### Task 1: Project skeleton

Required tests:

```text
package imports
CLI help returns success
```

### Task 2: SRT parser and writer

Required tests:

```text
basic SRT parse
multi-line cue parse
UTF-8 BOM parse
CRLF parse
non-contiguous index parse
malformed timecode error
writer re-numbers cues from 1
writer preserves timecodes
```

### Task 3: Profile loader and built-in profiles

Required tests:

```text
list built-in profiles
load each built-in profile
missing profile fails clearly
invalid YAML fails
unknown rule type exits code 4
unknown action exits code 4
regex compile error exits code 4
missing list reference exits code 4
```

### Task 4: Normalization

Required tests:

```text
trim and collapse spaces
NFKC normalization when enabled
English lowercase when enabled
outer punctuation stripping
compact_text removes comparison-only punctuation
normalization does not mutate output subtitle text
```

### Task 5: Rule engine P0 base rules

Required tests:

```text
regex_text matches repeated Japanese kana
text_in_list matches known hallucination phrase
protected_text matches protected phrase
single_cue matches short low-info cue
adjacent_duplicate detects short duplicate cue
density_window groups dense low-info cues
repeated_phrase detects repeated whole-text phrase
```

### Task 6: Actions and conflict resolution

Required tests:

```text
remove deletes cue
keep preserves cue
keep_first removes later duplicates
keep_first_n keeps only N cues in group
compress changes text but not timecode
protected blocks automatic remove
remove wins over compress
review does not modify output
```

### Task 7: Report mode and report output

Required tests:

```text
report mode writes .clean-report.txt
report mode writes .clean-decisions.yml
report mode does not write .cleaned.srt
report includes summary
report includes detail entries
source_sha256 uses exact input bytes
text_sha256 uses raw cue text lines joined with \n
existing output fails without --force
```

### Task 8: Clean mode

Required tests:

```text
clean mode writes .cleaned.srt
clean mode writes .clean-report.txt
clean mode does not write decisions
clean mode preserves original input
level conservative only applies safe
level moderate applies safe and likely_noise
level aggressive applies dense_low_info
review severity is not applied
output file exists without --force fails
```

### Task 9: Apply mode

Required tests:

```text
apply mode does not require --profile
apply mode reads decisions YAML
apply mode writes .cleaned.srt
apply mode writes .apply-report.txt
source_sha256 mismatch exits code 5
cue index/start/end/text_hash mismatch exits code 5
protected override remove is allowed only from explicit decision
protected override is reported
```

### Task 10: Install scripts

Required tests or smoke checks:

```text
bash scripts/install.sh
srt-clean --help
srt-clean --list-profiles
bash scripts/uninstall.sh --yes
```

These can be smoke checks rather than pytest unit tests.

## 7. scripts/check.sh

P0 should include:

```text
scripts/check.sh
```

Expected contents:

```bash
#!/usr/bin/env bash
set -euo pipefail

pytest
ruff check .
```

Usage:

```bash
bash scripts/check.sh
```

This gives the user one command instead of remembering separate commands.

## 8. User role in testing

The user does not need to write pytest tests.

The user should only check these final signals:

```text
pytest passed
ruff check . passed
scripts/check.sh passed
```

For real-world validation, the user may keep private SRT samples outside the repo, for example:

```text
~/Videos/srt-clean-samples/sample-real-01.srt
~/Videos/srt-clean-samples/sample-real-02.srt
```

These should not be committed.

## 9. Manual real-world smoke test

After Task 8, the user can run:

```bash
srt-clean --profile jp-adult-soft --level moderate sample-real-01.srt
```

Then check:

```text
sample-real-01.cleaned.srt exists
sample-real-01.clean-report.txt exists
original sample-real-01.srt is unchanged
obvious repeated low-information cues are reduced
protected semantic short phrases are not obviously removed
report summary is understandable
```

This manual smoke test is optional for P0 automated correctness but recommended before using on many real files.

## 10. Minimum stable gate

Do not proceed from one implementation batch to the next unless:

```bash
pytest
ruff check .
```

both pass.

If `scripts/check.sh` exists, use:

```bash
bash scripts/check.sh
```

No passing tests, no next stage.
