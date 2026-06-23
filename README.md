# srt-clean

`srt-clean` 是一支針對 ASR 輸出設計的規則式 SRT 字幕清理工具。

它會在保留有語意短句與原始 timecode 的前提下，移除、壓縮或報告低資訊、過度密集、重複或疑似幻覺的字幕 cue。

第一個目標使用情境是清理 Whisper / WhisperX 產生的 `.srt`，處理長音訊、背景噪音、重複非語義發聲、filler sound 或 ASR hallucination 造成的高密度干擾字幕。

## 產品邊界

`srt-clean` 會做：

- 解析 `.srt` 檔案。
- 套用以 YAML 設定的清理規則。
- 預設保留原始輸入檔。
- 產生清理後的 SRT。
- 產生人類可讀的 report。
- 透過 decisions 檔支援 review 與部分套用。
- 支援日文與英文清理 profile。

`srt-clean` 不會做：

- 執行 ASR。
- 由 `srt-clean` 主 CLI 直接翻譯字幕。
- 讀取音訊或影片內容。
- 用 LLM 判斷語意。
- 改寫正常字幕內容以調整風格。
- 在沒有明確規格的情況下修改 timecode。

repo 另外提供一個獨立 shell helper：

```text
translate-with-ollama
```

它不屬於 `srt-clean` 主 CLI 的 P0 核心功能。

## 文件

建議先讀：

```text
docs/SDD-srt-clean.md
docs/SDD-ARCH-python-project-structure.md
AGENTS.md
```

各文件用途：

```text
docs/SDD-srt-clean.md
  產品行為、rule engine、profiles、report 格式、decisions、parser 行為、tests 與 exit codes。

docs/SDD-ARCH-python-project-structure.md
  Python package 結構、venv 策略、install scripts、開發流程與 P0 實作順序。

AGENTS.md
  Codex / agent 的實作規則與 guardrails。
```

## 專案結構

```text
srt-clean/
├── README.md
├── AGENTS.md
├── AGENT.md
├── pyproject.toml
├── bin/
│   └── srt-clean
├── scripts/
│   ├── install.sh
│   ├── uninstall.sh
│   └── translate-with-ollama.sh
├── docs/
│   ├── README.md
│   ├── SDD-srt-clean.md
│   └── SDD-ARCH-python-project-structure.md
├── profiles/
│   ├── README.md
│   ├── jp-adult-soft.yml
│   ├── en-adult-soft.yml
│   └── en-translation-soft.yml
├── src/
│   ├── README.md
│   └── srt_clean/
│       ├── README.md
│       ├── __init__.py
│       ├── cli.py
│       ├── parser.py
│       ├── writer.py
│       ├── normalize.py
│       ├── profile.py
│       ├── rules.py
│       ├── actions.py
│       ├── decisions.py
│       ├── report.py
│       └── models.py
└── tests/
    ├── README.md
    ├── test_parser.py
    ├── test_writer.py
    ├── test_normalize.py
    ├── test_rules_jp.py
    ├── test_rules_en.py
    ├── test_decisions.py
    └── fixtures/
        └── README.md
```

## 開發環境

使用 Python 3.12.3 以上版本。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -e ".[dev]"
```

驗證方式：

```bash
srt-clean --help
srt-clean --list-profiles
pytest
ruff check .
```

## 安裝

正式安裝應使用獨立的 venv：

```text
~/.venvs/srt-clean
```

並建立這個 wrapper：

```text
~/bin/srt-clean
~/bin/translate-with-ollama
```

安裝指令：

```bash
bash scripts/install.sh
```

安裝完成後，使用者不需要手動 activate venv。

repo 驗證輔助指令：

```bash
bash scripts/check.sh
```

若要使用翻譯 helper，另需先安裝 `Ollama` 並拉取模型：

```bash
ollama pull qwen3:8b
```

## CLI 範例

清理日文 ASR 字幕：

```bash
srt-clean --profile jp-adult-soft --level moderate sample.srt
```

產生 report 與 decisions 供 review：

```bash
srt-clean --mode report --profile jp-adult-soft sample.srt
srt-clean --mode apply --decisions sample.clean-decisions.yml sample.srt
```

清理英文 ASR 字幕：

```bash
srt-clean --profile en-adult-soft --level conservative sample.en.srt
```

檢查翻譯後英文字幕：

```bash
srt-clean --profile en-translation-soft --mode report sample.translated.en.srt
```

使用 `Ollama` 進行字幕翻譯：

```bash
translate-with-ollama sample.srt zh-TW
```

這會產生：

```text
sample.zh-TW.srt
```

## 與其它工具的關係

建議流程：

```text
audio / video
  -> transcribe-audio / WhisperX
  -> raw SRT
  -> srt-clean
  -> cleaned SRT
  -> translate-srt
  -> translated SRT
```

`srt-clean` 與 `transcribe-audio` 相互獨立，但未來可以作為 `transcribe-audio` 的可選後處理步驟。

## P0 實作狀態

目前已完成範圍：

```text
Batch A
  Python package skeleton
  CLI help / --list-profiles / --check
  SRT parser and writer
  strict profile loader
  deterministic normalization

Batch B
  rule engine
  actions
  conflict resolution

Batch C
  report mode
  clean mode
  .clean-report.txt output
  .clean-decisions.yml output for report mode
  .cleaned.srt output for clean mode

Batch D
  apply mode
  install scripts
  scripts/check.sh
  repo bin wrapper
  documentation alignment
```
