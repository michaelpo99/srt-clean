# SDD-ARCH: Python Project Structure and Installation

最後更新：2026-06-23

## 1. 目的

本文件定義 `srt-clean` 的專案架構、Python package layout、venv 策略、安裝方式、開發流程與與既有工具鏈的關係。

功能規格請見：

```text
docs/SDD-srt-clean.md
```

本文件只描述「專案要長什麼樣子」與「如何安裝、開發、執行」。

## 2. 架構決策

`srt-clean` 應採用 `transcript-polish` 類型的 Python application CLI 架構，而不是 `transcribe-audio` 類型的 Bash orchestration 架構。

原因：

1. `srt-clean` 是文字處理與規則引擎工具。
2. 核心需求是 SRT parser、YAML profile、rule engine、report、decisions 與測試。
3. 不需要 FFmpeg、WhisperX、CUDA、PyTorch 或大型模型。
4. Python 比 Bash 更適合實作可測試的字幕 parser 與規則引擎。
5. 與未來 `translate-srt` 共享 SRT parser / writer / validation 邏輯較容易。

## 3. 與既有專案的定位差異

### 3.1 transcribe-audio

`transcribe-audio` 是 Bash orchestration tool。

特徵：

```text
Bash CLI
bin/transcribe-audio
bin/media2md
install.sh
呼叫 FFmpeg / WhisperX
負責媒體掃描、抽音軌、ASR pipeline
WhisperX 使用獨立 venv
```

`srt-clean` 不應採用這種架構，因為它不是媒體 pipeline orchestrator。

### 3.2 transcript-polish

`transcript-polish` 是 Python application CLI。

特徵：

```text
pyproject.toml
src package layout
scripts/install.sh
專用 venv
~/bin wrapper
使用者不需要手動 activate venv
支援設定檔與外部規則
輸出 summary / report
```

`srt-clean` 應採用這種架構。

## 4. 技術選型

### 4.1 語言

使用 Python。

最低版本：

```text
Python >= 3.11
```

原因：

1. `dataclasses`、typing、pathlib、argparse、re、difflib 足以支援 P0。
2. SRT 解析、YAML profile 與 report 產生都適合 Python。
3. Codex 產生 Python package、pytest 與 CLI 程式碼的穩定性較高。
4. 不需要 Go / Rust 的單一 binary 或高效能優勢。

### 4.2 CLI framework

P0 使用標準庫 `argparse`。

不使用 Typer / Click 作為必要依賴。

原因：

1. 降低依賴。
2. 安裝更簡單。
3. 參數雖多，但仍可用 argparse 清楚表達。
4. 適合無互動 CLI。

### 4.3 YAML

使用：

```text
PyYAML >= 6.0.1
```

### 4.4 測試

使用：

```text
pytest
```

### 4.5 格式與 lint

使用：

```text
ruff
```

P0 可先只要求 `ruff check .`，格式化可使用 `ruff format .`。

## 5. 專案目錄結構

目標結構：

```text
srt-clean/
├── .gitignore
├── README.md
├── pyproject.toml
├── bin/
│   └── srt-clean
├── scripts/
│   ├── install.sh
│   └── uninstall.sh
├── docs/
│   ├── SDD-srt-clean.md
│   └── SDD-ARCH-python-project-structure.md
├── profiles/
│   ├── jp-adult-soft.yml
│   ├── en-adult-soft.yml
│   └── en-translation-soft.yml
├── src/
│   └── srt_clean/
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
    ├── test_parser.py
    ├── test_writer.py
    ├── test_normalize.py
    ├── test_rules_jp.py
    ├── test_rules_en.py
    ├── test_decisions.py
    └── fixtures/
        ├── jp_repeated_kana.srt
        ├── jp_protected_short.srt
        ├── en_dense_filler.srt
        └── malformed_timecode.srt
```

## 6. pyproject.toml 規格

P0 `pyproject.toml` 應包含：

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "srt-clean"
version = "0.1.0"
description = "Rule-based SRT subtitle cleaner for ASR output"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "PyYAML>=6.0.1",
]

[project.scripts]
srt-clean = "srt_clean.cli:main"

[project.optional-dependencies]
dev = [
  "pytest>=8",
  "ruff>=0.5",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
srt_clean = []

[tool.ruff]
line-length = 100
target-version = "py311"
```

內建 profiles 第一版可以放在 repo-level `profiles/`，由 install script 複製或由 CLI 以相對路徑尋找。若要打包進 wheel，第二版可改放到：

```text
src/srt_clean/profiles/
```

P0 可先使用 repo-level `profiles/`，降低複雜度。

## 7. venv 策略

### 7.1 開發用 venv

開發者在 repo 內使用：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -e ".[dev]"
```

驗證：

```bash
srt-clean --help
pytest
ruff check .
```

`.venv/` 不得 commit。

### 7.2 正式安裝用 venv

正式安裝使用專用 venv：

```text
~/.venvs/srt-clean
```

安裝後使用者不需要手動 activate venv。

`~/bin/srt-clean` 應是 wrapper，內容概念如下：

```bash
#!/usr/bin/env bash
set -euo pipefail
exec "$HOME/.venvs/srt-clean/bin/srt-clean" "$@"
```

### 7.3 不使用 Conda

P0 不使用 Conda。

原因：

1. 不需要 CUDA / PyTorch / native ML dependency。
2. 專案依賴很小。
3. venv 足夠且較符合現有 CLI 工具安裝模式。

## 8. scripts/install.sh 規格

`install.sh` 應：

1. 找出 repo root。
2. 檢查 Python 版本 >= 3.11。
3. 建立或更新 `~/.venvs/srt-clean`。
4. 安裝 package：

```bash
pip install -e "$REPO_ROOT"
```

5. 若使用者指定 dev 安裝，可安裝：

```bash
pip install -e "$REPO_ROOT[dev]"
```

6. 建立 `~/bin`。
7. 寫入 `~/bin/srt-clean` wrapper。
8. 檢查 `~/bin` 是否在 PATH。
9. 執行 smoke test：

```bash
~/bin/srt-clean --help
~/bin/srt-clean --list-profiles
```

10. 顯示後續使用方式。

### 8.1 install.sh CLI

建議支援：

```text
bash scripts/install.sh
bash scripts/install.sh --dev
bash scripts/install.sh --force
```

含義：

```text
--dev
  安裝 .[dev] optional dependencies。

--force
  重建 ~/.venvs/srt-clean。
```

## 9. scripts/uninstall.sh 規格

`uninstall.sh` 應：

1. 刪除 `~/bin/srt-clean`。
2. 詢問是否刪除 `~/.venvs/srt-clean`。
3. 不刪除使用者輸出的 SRT、report、decisions。
4. 不刪除 repo。

支援：

```text
bash scripts/uninstall.sh
bash scripts/uninstall.sh --yes
```

## 10. bin/srt-clean 規格

`bin/srt-clean` 可作為 repo 內直接執行的 wrapper。

P0 有兩種可接受方式。

方式 A：不提供 `bin/srt-clean`，只依賴 `[project.scripts]`。

方式 B：提供 wrapper：

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
exec "$PYTHON_BIN" -m srt_clean.cli "$@"
```

若採方式 B，README 應說明：

```bash
pip install -e ".[dev]"
./bin/srt-clean --help
```

正式安裝後仍以 `~/bin/srt-clean` 為主要入口。

## 11. 使用者設定檔

P0 不需要使用者全域設定檔。

第二版可加入：

```text
~/.config/srt-clean/config.toml
```

可能內容：

```toml
default_profile = "jp-adult-soft"
default_level = "moderate"
explain_lang = "zh-TW"
```

優先順序：

```text
CLI explicit option
> user config
> profile defaults
> built-in defaults
```

P0 先不要實作，避免範圍過大。

## 12. Profile 搜尋路徑

P0 profile resolution 順序：

```text
1. 若 --profile 是既有檔案路徑，直接讀取該 YAML。
2. 若 --profile 是名稱，先找 repo/profiles/<name>.yml。
3. 若已安裝，找 package 或 install-time 記錄的 profiles 目錄。
4. 找不到則報錯並列出可用 profiles。
```

內建 profile 名稱：

```text
jp-adult-soft
en-adult-soft
en-translation-soft
```

## 13. README 要求

README 應包含：

1. 一句話定位。
2. 產品邊界。
3. 快速安裝。
4. 常用指令。
5. report / clean / apply 模式簡介。
6. profile 說明。
7. 開發者安裝。
8. 測試方式。
9. 與 `transcribe-audio` / `translate-srt` 的 pipeline 關係。

最小 README 範例段落：

```md
# srt-clean

`srt-clean` is a rule-based SRT subtitle cleaner for ASR output.

It removes or compresses low-information, dense, repeated, or likely hallucinated subtitle cues while preserving meaningful short phrases and original timecodes.
```

## 14. P0 實作順序

Codex 建議依下列順序實作：

```text
1. 建立 pyproject.toml、src/srt_clean、tests。
2. 實作 parser.py / writer.py。
3. 實作 cli.py，先支援 --help、--check、--list-profiles。
4. 實作 profile.py 與 profiles/*.yml。
5. 實作 normalize.py。
6. 實作 rules.py 的 regex_text / text_in_list / protected_text。
7. 實作 actions.py 的 remove / keep / compress。
8. 實作 report.py。
9. 實作 decisions.py。
10. 實作 clean / report / apply mode。
11. 加入 scripts/install.sh / uninstall.sh。
12. 補 README。
13. 跑 pytest / ruff。
```

## 15. 驗收條件

P0 完成時，以下指令應可成功：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
srt-clean --help
srt-clean --list-profiles
pytest
ruff check .
```

正式安裝應可成功：

```bash
bash scripts/install.sh
srt-clean --help
srt-clean --list-profiles
```

基本清理應可成功：

```bash
srt-clean --profile jp-adult-soft tests/fixtures/jp_repeated_kana.srt
```

並產生：

```text
tests/fixtures/jp_repeated_kana.cleaned.srt
tests/fixtures/jp_repeated_kana.clean-report.txt
```

Report / apply 應可成功：

```bash
srt-clean --mode report --profile jp-adult-soft tests/fixtures/jp_repeated_kana.srt
srt-clean --mode apply --decisions tests/fixtures/jp_repeated_kana.clean-decisions.yml tests/fixtures/jp_repeated_kana.srt
```

## 16. 非目標

P0 不做：

1. Docker image。
2. Conda environment。
3. GUI review tool。
4. Web app。
5. LLM semantic review。
6. 音訊或影片讀取。
7. 與 WhisperX 直接整合。
8. GitHub Actions，可第二版再加。
9. PyPI release，可第二版再加。

## 17. 後續 Roadmap

1. GitHub Actions：pytest + ruff。
2. JSON Schema 驗證 profile。
3. 將 profiles 打包進 Python package。
4. 加入 `~/.config/srt-clean/config.toml`。
5. 加入 batch directory mode。
6. 加入 HTML report。
7. 與 `transcribe-audio` optional post-processing 整合。
8. 與 `translate-srt` 共用 parser / writer。
