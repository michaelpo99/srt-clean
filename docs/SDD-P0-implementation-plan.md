# SDD-P0：實作補充與任務計畫

最後更新：2026-06-23

## 1. 目的

本文件補強 P0 實作前必須定義清楚的行為，並把 Codex 實作拆成可驗收的 task。

本文件不是 CR，因為目前尚未有既有程式碼需要變更。這是 P0 初始實作規格的一部分。

主要規格仍是：

```text
docs/SDD-srt-clean.md
docs/SDD-ARCH-python-project-structure.md
```

若本文件與上述文件衝突，P0 以本文件的補充說明為準，並應在後續整理時回填到主要 SDD。

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

補充規則：

1. `apply` mode does not load profile by default.
2. `apply` mode 可以為了 reporting 讀取 decisions 內的 profile metadata，但不得重新評估 profile rules。
3. `clean` mode 不得寫出 decisions。
4. `report` mode 不得寫出 cleaned SRT。
5. 所有 modes 都必須保留原始輸入檔。

## 4. Hash 定義

### 4.1 source_sha256

`source_sha256` 必須以輸入檔的原始 bytes 計算。

演算法：

```python
hashlib.sha256(path.read_bytes()).hexdigest()
```

計算 `source_sha256` 前不得先正規化 line ending。

### 4.2 text_sha256

`text_sha256` 必須以原始 cue text lines 用 `\n` 串接後，再以 UTF-8 編碼計算。

演算法：

```python
text_for_hash = "\n".join(cue.raw_text_lines)
text_sha256 = hashlib.sha256(text_for_hash.encode("utf-8")).hexdigest()
```

`text_sha256` 不得使用 normalized text。

### 4.3 cue identity in decisions

每一筆 decision 必須包含：

```yaml
cue: 54
start: "00:25:21,413"
end: "00:25:50,050"
text_sha256: "..."
```

P0 `apply` 驗證要求這些欄位全部一致。

若任一欄位不一致，必須以 exit code 5 失敗，且不得寫出 cleaned output。

## 5. Normalization order

P0 必須使用 deterministic normalization。

對每個 cue text：

1. 將原始 `raw_text_lines` 用單一空白串接成 `text`。
2. 若 `trim=true`，去除前後空白。
3. 若 `normalize_fullwidth=true`，套用 `unicodedata.normalize("NFKC", text)`。
4. 若 `collapse_spaces=true`，將連續空白壓成單一 ASCII space。
5. 若 `lowercase=true`，套用 lowercase。
6. 若 `strip_outer_punctuation=true`，只去除外層標點。
7. 以結果建立 `normalized_text`。
8. 透過移除空白與 comparison-only punctuation 建立 `compact_text`。

在 P0 中，`normalize_long_vowels=true` 不得直接修改 `normalized_text`。

它只能影響 `compact_text` 與 regex comparison helper，把下列符號視為可比較的延長音記號：

```text
ー
〜
~
…
-
```

normalization 階段不得改動輸出字幕文字。輸出文字只能透過 `compress` 等 action 改變。

## 6. Profile schema validation policy

P0 必須對 profile 做 strict validation。

以下都屬於 profile schema error，且必須以 exit code 4 結束：

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

P0 應將 unknown fields 視為 error，而不是 warning。

原因：會刪除文字的 rule engine 不適合容忍 typo。

## 7. Rule conflict resolution

P0 必須使用 deterministic conflict resolution。

### 7.1 Evaluation phase

1. 將 SRT parse 成 cues。
2. 對 cues 做 normalization。
3. 先評估 protected rules。
4. 再評估其它 rules，產生 candidate rule matches。
5. rule evaluation 階段不得修改 cue text。

### 7.2 Merge phase

對每個 cue：

1. 若 cue 是 protected，automatic `remove` 必須被阻擋。
2. 若 cue 有一個以上可套用的 `remove` candidate，選優先度最高者作為 primary decision。
3. 其它命中的 rule ID 要以 secondary reasons 記錄在 report。
4. 若 cue 已標記為 remove，不得再套用 `compress`。
5. 若 cue 沒被 remove，且有一個以上 `compress` candidate，套用其中一個 `compress` action。
6. 若有多個 `compress` candidate，套用最先命中的 rule order。
7. `report` candidates 不得修改輸出。

### 7.3 Rule priority

P0 優先順序：

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

若實作依賴 profile rule order，仍必須強制滿足：

```text
protected blocks auto remove
remove wins over compress
compress wins over report
review does not auto-apply
```

### 7.4 Density groups

針對 `density_window`：

1. 同一個 cue 可能出現在多個重疊 window 中。
2. 實作必須對 removals 去重。
3. 若 cue 已被更高優先度規則移除，不應再產生額外的 density decision。
4. Protected cues 不得被 density rules 移除。
5. 若可取得，report 應包含 density group 的 start / end 與 group size。

## 8. repeated_phrase P0 演算法

P0 的 repeated phrase 偵測必須簡單且 deterministic。

P0 支援的情況：

### 8.1 Whole-text repeated substring

偵測整段 compact text 是否由同一個 substring 重複至少 `min_repeats` 次組成。

範例：

```text
気持ちいい気持ちいい気持ちいい気持ちいい
```

壓縮為：

```text
気持ちいい
```

### 8.2 Separator-based repeated phrase

偵測文字中是否有以空白或標點分隔的重複片語。

範例：

```text
sorry, sorry, sorry, sorry
```

壓縮為：

```text
sorry
```

### 8.3 Non-goals for P0 repeated_phrase

P0 不得嘗試日文斷詞或形態分析。

P0 不得自行推斷語意重複。

若壓縮後會得到空字串，P0 不得進行 `compress`。

若同一 cue 同時命中更高優先度的 `remove` 規則，`remove` 優先。

## 9. en-translation-soft P0 boundary

`en-translation-soft` 在 P0 中是單檔 inspection profile。

它可以偵測：

1. Adjacent duplicate translated text.
2. Model meta-output such as `Translation:`, `Here is`, `Note:`, or `<think>`.
3. Empty cue text.

P0 只接受單一 SRT 輸入，因此不得宣稱能驗證 source / target cue 數量一致性。

source 與 translated SRT 之間的 cue 數量與 timecode 一致性，屬於 `translate-srt` 或未來的雙檔 validator 範圍。

## 10. Report requirements clarified

P0 report 必須包含：

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

每一筆 detail entry 必須包含：

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

`compress` 類型的 entry 必須包含 `before` 與 `after` 預覽。

`protected` 類型的 entry 必須包含 `action=keep`。

若自動 `remove` 因 `protected` 身分被阻擋，必須包含 `blocked_by_protected=true`。

## 11. Fixture policy

tests 必須使用短小的 synthetic SRT fixtures。

不得提交：

1. Full real-world subtitles.
2. Commercial transcript samples.
3. Audio files.
4. Video files.
5. Large generated fixtures.

synthetic fixtures 應短小且聚焦。通常一個 fixture 只覆蓋一種行為。

## 12. P0 task plan

P0 應拆成多個小 task 實作，不要一次用一個大型 Codex run 完成。

原因：

1. Parser 與 writer 的行為可以獨立測試。
2. Profile schema error 需要 strict tests。
3. 若 rule engine conflict resolution 和 CLI 一起實作，較容易出錯。
4. Decisions / apply mode 是獨立議題。
5. install script 應在 CLI 可正常運作後再加入。

## 13. Task breakdown

### Task 1：Project skeleton

目標：

```text
建立可安裝的 Python package 與最小 CLI。
```

範圍：

1. `pyproject.toml`.
2. `src/srt_clean/__init__.py`.
3. `src/srt_clean/cli.py`.
4. `src/srt_clean/models.py`.
5. Basic `srt-clean --help`.
6. Minimal tests wiring.

驗收條件：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
srt-clean --help
pytest
ruff check .
```

### Task 2：SRT parser and writer

目標：

```text
在不做清理的前提下完成 SRT parse 與 write。
```

範圍：

1. `parser.py`.
2. `writer.py`.
3. timecode parse/format helpers.
4. parser errors with line numbers.
5. BOM and CRLF support.
6. cue re-numbering on write.

驗收條件：

1. Basic SRT parse test passes.
2. Multi-line cue test passes.
3. CRLF/BOM test passes.
4. malformed timecode returns exit code 3 through CLI or parser-level error.

### Task 3：Profile loader and built-in profiles

目標：

```text
載入 strict YAML profiles，並列出 built-in profiles。
```

範圍：

1. `profile.py`.
2. `profiles/jp-adult-soft.yml`.
3. `profiles/en-adult-soft.yml`.
4. `profiles/en-translation-soft.yml`.
5. `srt-clean --list-profiles`.
6. `srt-clean --check --profile <name> input.srt`.

驗收條件：

1. Known profiles list correctly.
2. Missing profile fails clearly.
3. Invalid profile schema exits code 4.
4. Unknown rule type exits code 4.
5. Regex compile error exits code 4.

### Task 4：Normalization

目標：

```text
以 deterministic 方式產生 `normalized_text` 與 `compact_text`。
```

範圍：

1. `normalize.py`.
2. profile-controlled normalization flags.
3. tests for whitespace, NFKC, lowercase, punctuation stripping, compact text.

驗收條件：

1. Japanese normalization tests pass.
2. English lowercase tests pass.
3. Normalization does not mutate output text.

### Task 5：Rule engine P0 base rules

目標：

```text
評估 P0 rule types，並在不套用修改的情況下產生 rule matches。
```

範圍：

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

驗收條件：

1. Japanese repeated kana matches remove candidate.
2. Protected short phrase matches protected.
3. English filler matches profile rule.
4. Missing list reference fails during profile validation.

### Task 6：Actions and conflict resolution

目標：

```text
以 deterministic 方式套用 `remove`、`keep`、`keep_first`、`keep_first_n`、`compress` 與 `report`。
```

範圍：

1. `actions.py`.
2. conflict resolution rules from this document.
3. protected blocks automatic remove.
4. remove wins over compress.
5. compress only changes text, not timecode.

驗收條件：

1. Long `あああ...` removed.
2. `気持ちいい気持ちいい...` compressed.
3. `痛い` kept protected.
4. density rule removes only allowed cues.
5. output cue indexes are continuous.

### Task 7：Report mode and report output

目標：

```text
產生人類可讀的 clean report 與 decisions YAML。
```

範圍：

1. `report.py`.
2. report summary.
3. report details.
4. `decisions.py` write path.
5. source and cue hashes.
6. `--mode report`.

驗收條件：

1. Report mode writes `.clean-report.txt`.
2. Report mode writes `.clean-decisions.yml`.
3. Report mode does not write `.cleaned.srt`.
4. Existing outputs fail without `--force`.

### Task 8：Clean mode

目標：

```text
執行完整的 `parser -> profile -> normalize -> rules -> actions -> writer/report` pipeline。
```

範圍：

1. `--mode clean`.
2. `--level conservative|moderate|aggressive`.
3. `--output`.
4. `--report-output`.
5. `--force`.

驗收條件：

1. Clean mode writes `.cleaned.srt`.
2. Clean mode writes `.clean-report.txt`.
3. Clean mode does not write decisions.
4. Review severity is not applied.
5. Existing output fails without `--force`.

### Task 9：Apply mode

目標：

```text
在不重新執行 profile rules 的情況下，套用使用者修改後的 decisions 檔。
```

範圍：

1. `decisions.py` read path.
2. source hash validation.
3. cue identity validation.
4. protected override reporting.
5. `--mode apply`.

驗收條件：

1. Apply writes `.cleaned.srt`.
2. Apply writes `.apply-report.txt`.
3. Source hash mismatch exits code 5.
4. Protected override is allowed only from explicit decision and is reported.
5. Apply mode does not require `--profile`.

### Task 10：Install scripts

目標：

```text
將 CLI 安裝到 `~/.venvs/srt-clean` 與 `~/bin/srt-clean`。
```

範圍：

1. `scripts/install.sh`.
2. `scripts/uninstall.sh`.
3. optional `bin/srt-clean` wrapper.
4. smoke tests.

驗收條件：

```bash
bash scripts/install.sh
srt-clean --help
srt-clean --list-profiles
bash scripts/uninstall.sh --yes
```

### Task 11：Documentation pass

目標：

```text
更新 README 類文件，使其與已實作行為一致。
```

範圍：

1. root `README.md`.
2. `docs/README.md`.
3. `profiles/README.md` if profile behavior changed.
4. `AGENTS.md` if implementation rules changed.

驗收條件：

1. All documented commands exist or are clearly marked future.
2. No P0 unsupported option is shown as implemented.
3. P0 limitations are visible.

## 14. 建議執行策略

以 task-by-task 的方式執行 Codex。

不要要求 Codex 一次完成全部 P0。

建議 prompt pattern：

```text
Read AGENTS.md, docs/SDD-srt-clean.md, docs/SDD-ARCH-python-project-structure.md, and docs/SDD-P0-implementation-plan.md. Implement Task N only. Add tests for the task. Do not implement later tasks unless needed for task acceptance.
```

每個 task 完成後：

```bash
pytest
ruff check .
```

若 tests 通過，建議每個 task 完成後就 commit。

## 15. 最小可用里程碑

第一個實用里程碑是在 Task 8 完成後。

到那個階段，使用者可以執行：

```bash
srt-clean --profile jp-adult-soft --level moderate sample.srt
```

並得到：

```text
sample.cleaned.srt
sample.clean-report.txt
```

Task 9 會加入透過 decisions 進行人工部分 review 的能力。

Task 10 會讓安裝流程對使用者更友善。
