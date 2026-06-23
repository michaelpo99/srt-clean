# SDD: 文件語言與撰寫風格

最後更新：2026-06-23

## 1. 目的

本文件定義 `srt-clean` repo 內規格文件與 README 的語言使用原則。

目標是讓文件對使用者容易讀，也讓 Codex / AI 實作時不產生歧義。

## 2. 基本原則

本 repo 文件以繁體中文為主。

但下列項目必須保留英文或原始程式 token：

```text
CLI option names
YAML keys
rule type names
action names
severity names
Python module names
file paths
exit code labels
test commands
package names
function / class names
```

原因：這些名稱會直接出現在程式碼、CLI、測試、YAML profile 或使用者命令中，翻譯會增加歧義。

## 3. 推薦寫法

使用中文描述行為，保留英文技術 token。

推薦：

```text
若輸出檔已存在且未指定 --force，CLI 必須失敗。
不得覆蓋。
不得自動改名。
exit code = 1。
```

不推薦：

```text
如果已經有輸出，就看情況處理。
```

推薦：

```text
`protected_text` 必須先於 `remove` 規則檢查。
protected cue 不可被自動 `remove`。
```

不推薦：

```text
保護文字規則要先跑，不能亂刪。
```

## 4. 文件分工

### 4.1 README.md

使用者入口，可以中文為主。

應保留實際命令與檔名：

```bash
srt-clean --profile jp-adult-soft --level moderate sample.srt
```

### 4.2 docs/*.md

規格文件以中文為主。

技術 key、規則名稱、CLI 參數、路徑與測試指令保留英文。

### 4.3 AGENTS.md

`AGENTS.md` 可以中英混合。

因為它是給 Codex / agent 的高層實作守則，英文 technical token 可保留較多。

若未來重寫，仍應避免把 CLI / YAML / module 名稱翻成中文。

### 4.4 CODEX-RUNBOOK.md

本文件可中文為主。

給 Codex 的 prompt 可以用中文撰寫，但必須保留精確英文 token，例如：

```text
Implement Batch A only: Tasks 1 through 4.
Do not implement Task 5 or later.
Run pytest and ruff check .
```

若 prompt 使用中文，也應保持明確命令式語氣。

## 5. Code block 規則

所有命令、路徑、YAML、TOML、Python 片段、SRT 範例都必須放在 code block。

例如：

```bash
pytest
ruff check .
```

```yaml
severity: likely_noise
action:
  type: remove
```

不要在一般段落中模糊描述會被直接執行的命令。

## 6. 驗收條件寫法

驗收條件必須可檢查。

推薦：

```text
執行 pytest 必須通過。
執行 ruff check . 必須通過。
clean mode 必須產生 <stem>.cleaned.srt。
report mode 不得產生 <stem>.cleaned.srt。
```

不推薦：

```text
大致可以清理字幕。
輸出看起來正常。
```

## 7. 不能翻譯的固定名稱

以下名稱不得翻譯：

```text
srt-clean
transcribe-audio
transcript-polish
translate-srt
pytest
ruff
PyYAML
argparse
venv
Codex
WhisperX
report
clean
apply
remove
keep
keep_first
keep_first_n
compress
regex_text
single_cue
adjacent_duplicate
adjacent_similarity
density_window
repeated_phrase
text_in_list
protected_text
safe
likely_noise
dense_low_info
review
protected
source_sha256
text_sha256
```

可以在中文中解釋含義，但實際 token 不得替換。

## 8. 未來文件更新規則

新增或更新文件時，遵守：

1. 中文為主。
2. 程式 token 保留英文。
3. 行為描述必須可驗收。
4. 避免使用「應該可以」、「看情況」、「大概」等模糊詞。
5. 若文件會被 Codex 用來實作，必須包含明確的 scope、non-goals 與 acceptance criteria。
