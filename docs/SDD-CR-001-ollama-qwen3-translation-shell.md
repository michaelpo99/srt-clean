# SDD-CR-001: Ollama Qwen3 翻譯 Shell Script

最後更新：2026-06-24

## 1. 目的

本 change request 定義一個未來功能：

以 shell script 呼叫本機 `Ollama`，使用 `qwen3:8b` 模型對 `.srt` 字幕進行翻譯，並輸出帶有語言別 suffix 的新檔案。

此功能是獨立工具流程，不屬於 `srt-clean` P0 核心清理能力。

## 2. 背景

目前 `srt-clean` 的核心目標是 rule-based SRT 清理，不包含 translation。

但使用者有實際需求，希望在本機透過 `Ollama` 執行字幕翻譯，並保留簡單、可重複執行的 shell workflow。

因此本 CR 將 translation 視為未來擴充流程，而不是把 LLM 翻譯邏輯混入目前的清理 engine。

## 3. Scope

本 CR 範圍包含：

1. 新增一個 shell script，例如：

```text
bin/translate-with-ollama
```

2. script 必須接受：

```text
input SRT path
target language code
optional source language code
optional model name，預設 `qwen3:8b`
```

3. script 必須呼叫本機 `ollama` CLI。
4. script 必須輸出新的 `.srt` 檔，不得覆蓋原始檔。
5. 翻譯後的輸出檔名必須帶有目標語言別。
6. script 必須保留 SRT cue index 與 timecode 結構。
7. script 必須在依賴缺失或模型不可用時提供可操作的錯誤訊息。
8. script 實作完成後，必須可安裝到 `~/bin`，讓使用者不需進 repo 目錄即可呼叫。

## 4. Non-goals

本 CR 不包含：

1. 把 translation 併入 `srt-clean` 既有 `clean` / `report` / `apply` mode。
2. 自動偵測語言。
3. 批次目錄掃描。
4. 並行翻譯多個檔案。
5. 依字幕內容做風格潤飾、摘要或重寫。
6. 保證模型輸出一定完全遵守原始段落切分。
7. GUI、Web UI 或 API server。

## 4.1 安裝目標

此 CR 不只要求 repo 內存在：

```text
bin/translate-with-ollama
```

也要求正式安裝後提供：

```text
~/bin/translate-with-ollama
```

建議方式：

1. `scripts/install.sh` 一併建立或更新 `~/bin/translate-with-ollama`。
2. `~/bin/translate-with-ollama` 可直接 wrapper 到 repo 內 script，或 wrapper 到未來正式安裝位置。
3. `scripts/uninstall.sh` 若未來擴充此功能，也應一併移除該 wrapper。

## 5. 使用方式

建議 CLI 介面：

```bash
bash bin/translate-with-ollama input.srt zh-TW
```

正式安裝後，也應支援：

```bash
translate-with-ollama input.srt zh-TW
```

支援完整參數形式：

```bash
bash bin/translate-with-ollama \
  --input input.srt \
  --target-lang zh-TW \
  --source-lang ja \
  --model qwen3:8b
```

若兩種形式同時存在，文件與 script help 必須清楚說明優先順序；P1 實作可先只支援 long options。

## 6. 輸出命名規則

若輸入檔為：

```text
movie.srt
```

目標語言為：

```text
zh-TW
```

則輸出檔必須為：

```text
movie.zh-TW.srt
```

若輸入檔為：

```text
episode.cleaned.srt
```

則輸出檔必須為：

```text
episode.cleaned.zh-TW.srt
```

規則如下：

1. 只移除最後一個 `.srt` 副檔名。
2. 在移除後的 basename 後面附加 `.<target-lang>.srt`。
3. 不得覆蓋原始檔。
4. 若輸出檔已存在且未指定未來 `--force`，script 必須失敗。
5. script 可以在同目錄寫出 `<stem>.<target-lang>.partial.srt` 作為進度暫存檔；成功時應轉成正式輸出，失敗時可保留供檢查。若同名 partial 檔已存在，script 應預設驗證後續跑，而不是無條件從頭覆寫。

## 7. 執行前置條件

環境必須具備：

```bash
ollama --version
```

且模型可用：

```bash
ollama list
```

至少應包含：

```text
qwen3:8b
```

若模型不存在，錯誤訊息應明確提示使用者先執行：

```bash
ollama pull qwen3:8b
```

## 8. 翻譯策略

script 應將輸入 SRT 內容送給 `Ollama`，並要求模型遵守以下約束：

1. 保留原始 cue index。
2. 保留原始 timecode。
3. 只翻譯字幕文字內容。
4. 不新增說明文字、前言、結語或 markdown fence。
5. 不得輸出與 SRT 無關的評論。

建議 prompt 約束方向：

```text
Translate subtitle text into <target language>.
Keep cue numbers and timestamps exactly unchanged.
Return valid SRT only.
Do not add commentary.
```

若未來實作需要更強約束，可先把每個 cue 拆開逐段翻譯，再重組成 SRT。

## 9. 失敗處理

以下情況必須失敗並回傳非 0 exit code：

1. 輸入檔不存在。
2. 輸入檔不是 `.srt`。
3. `ollama` CLI 不存在。
4. 指定模型不可用。
5. 模型回應為空。
6. 模型回應無法重建為合法 SRT。
7. 目標輸出檔已存在。

對於第 5 與第 6 類模型輸出問題，script 可以先對單一 cue 做有限次重試；若重試後仍失敗，可以保留該 cue 原文並繼續處理其餘 cue，同時在 stderr 明確列出 fallback 的 cue index。

若使用者中斷 script，例如 `Ctrl-C`，script 應主動呼叫 `ollama stop <model>`，避免模型持續佔用 GPU。

錯誤訊息必須指出：

1. 哪個檔案或參數有問題。
2. 建議的下一步，例如安裝 `ollama`、拉取模型、刪除衝突輸出檔，或改用其他 `--target-lang`。

## 10. 與 `srt-clean` 的關係

此 script 與 `srt-clean` 主 CLI 應保持解耦。

允許的搭配流程：

```bash
srt-clean --profile en-translation-soft --mode clean input.srt
bash bin/translate-with-ollama input.cleaned.srt zh-TW
```

或：

```bash
bash bin/translate-with-ollama input.srt zh-TW
srt-clean --profile en-translation-soft --mode report input.zh-TW.srt
```

但本 CR 不要求 `srt-clean` 主 CLI 直接內建 `--translate`。

## 11. 文件更新要求

若此 CR 被實作，至少必須同步更新：

```text
README.md
docs/README.md
docs/SDD-ARCH-python-project-structure.md
```

若採用 `~/bin` 安裝入口，也必須更新：

```text
scripts/README.md
```

若決定把 script 列為正式支援 workflow，也應在 `README.md` 加入：

1. 安裝 `Ollama` 的前置說明。
2. `ollama pull qwen3:8b` 的準備步驟。
3. 一個最小可執行範例。

## 12. 驗收條件

最低驗收標準：

1. 存在可執行 script：

```text
bin/translate-with-ollama
```

且正式安裝後存在：

```text
~/bin/translate-with-ollama
```

2. 執行：

```bash
bash bin/translate-with-ollama sample.srt zh-TW
```

必須產生：

```text
sample.zh-TW.srt
```

3. 輸出檔中的 cue index 與 timecode 必須與輸入一致。
4. 輸出檔不得覆蓋原檔。
5. 當 `ollama` 不存在時，script 必須失敗並印出可操作錯誤。
6. 當 `qwen3:8b` 尚未拉取時，script 必須提示：

```bash
ollama pull qwen3:8b
```

7. 至少應有一個小型 synthetic `.srt` smoke test fixture 與對應測試或驗證腳本。
8. 執行：

```bash
~/bin/translate-with-ollama sample.srt zh-TW
```

必須可正常產生：

```text
sample.zh-TW.srt
```

## 13. 後續延伸

未來若要擴充，可另開新 CR 討論：

1. 批次翻譯整個目錄。
2. 支援多模型切換。
3. 加入 `--force`。
4. 加入 `--prompt-file`。
5. 加入分段翻譯與重試策略。
6. 加入翻譯後 QA 或格式修復流程。
