# Codex / AI Agent 執行手冊

最後更新：2026-06-24

## 1. 目的

本文件是給 Codex 或其它 AI agent 直接讀取的 execution runbook。

它不是只給使用者複製貼上用的 prompt 文件。若 agent 能讀取 repo，應直接依本文件規劃、分批實作、建立測試、執行檢查、修到通過，再回報結果。

使用者也可以把本文件中的短版啟動模板或 batch 指令複製給 Codex；但主要定位是 agent-facing。

## 2. Agent 必讀文件

每次開始實作前，agent 必須閱讀：

```text
AGENTS.md
README.md
docs/SDD-DOCS-STYLE.md
docs/SDD-ARCH-python-project-structure.md
docs/SDD-srt-clean.md
docs/SDD-P0-implementation-plan.md
docs/SDD-TESTING.md
docs/CODEX-RUNBOOK.md
```

文件以繁體中文為主，但 CLI options、YAML keys、module names、rule types、actions、severity、file paths 與 test commands 必須保留英文 token。

## 3. 執行原則

Agent 應以 batch 為單位實作，不要一次完成所有 P0 tasks。

目前本 repo 遠端預設分支是 `master`，不是 `main`。

本文件中的 branch 與 PR workflow 以 `master` 為準。若未來 repo 預設分支改變，應以遠端實際 default branch 為準並同步更新本文件。

每個 batch 內可以自主完成該 batch 的所有 scope，不需要逐 task 詢問使用者。

每個 batch 結束前必須執行：

```bash
pytest
ruff check .
```

若 `scripts/check.sh` 已存在，另執行：

```bash
bash scripts/check.sh
```

如果檢查失敗，agent 必須先修正並重新執行。只有在所有檢查通過後，才可回報 batch 完成。

## 4. PR workflow 短版啟動模板

本節是日常使用的短版 prompt。它刻意不重複每個 task 的細節，避免 prompt 與規格文件不同步。

Agent 必須從 `docs/README.md`、`docs/CODEX-RUNBOOK.md` 與各 SDD 文件取得最新 scope 與 acceptance criteria。

### 4.1 Batch A 短版 prompt

```text
請在 michaelpo99/srt-clean repo 依照 AGENTS.md、docs/README.md、docs/CODEX-RUNBOOK.md 執行。

本次只做 Batch A，不要做後續 batch。

請從最新 master 建立 branch：
codex/batch-a

請在該 branch 上依文件規定實作、建立 tests / fixtures，並執行：
pytest
ruff check .

若失敗，修到通過再停止。

完成後 commit、push branch，開 Draft PR 到 master。

PR 說明包含：
1. 完成內容
2. 變更檔案
3. pytest 結果
4. ruff 結果
5. 已知限制
```

### 4.2 Batch B 短版 prompt

```text
請在 michaelpo99/srt-clean repo 依照 AGENTS.md、docs/README.md、docs/CODEX-RUNBOOK.md 執行。

本次只做 Batch B，不要做後續 batch。

請從最新 master 建立 branch：
codex/batch-b

請在該 branch 上依文件規定實作、建立 tests / fixtures，並執行：
pytest
ruff check .

若失敗，修到通過再停止。

完成後 commit、push branch，開 Draft PR 到 master。

PR 說明包含：
1. 完成內容
2. 變更檔案
3. pytest 結果
4. ruff 結果
5. 已知限制
```

### 4.3 Batch C 短版 prompt

```text
請在 michaelpo99/srt-clean repo 依照 AGENTS.md、docs/README.md、docs/CODEX-RUNBOOK.md 執行。

本次只做 Batch C，不要做後續 batch。

請從最新 master 建立 branch：
codex/batch-c

請在該 branch 上依文件規定實作、建立 tests / fixtures，並執行：
pytest
ruff check .

若失敗，修到通過再停止。

完成後 commit、push branch，開 Draft PR 到 master。

PR 說明包含：
1. 完成內容
2. 變更檔案
3. pytest 結果
4. ruff 結果
5. 測試過的 example command，優先使用：
   srt-clean --profile jp-adult-soft --level moderate <fixture>.srt
6. 已知限制
```

### 4.4 Batch D 短版 prompt

```text
請在 michaelpo99/srt-clean repo 依照 AGENTS.md、docs/README.md、docs/CODEX-RUNBOOK.md 執行。

本次只做 Batch D，不要做 future roadmap features。

請從最新 master 建立 branch：
codex/batch-d

請在該 branch 上依文件規定實作、建立 tests / fixtures，並執行：
pytest
ruff check .

如果 scripts/check.sh 已存在，也執行：
bash scripts/check.sh

若失敗，修到通過再停止。

完成後 commit、push branch，開 Draft PR 到 master。

PR 說明包含：
1. 完成內容
2. 變更檔案
3. pytest 結果
4. ruff 結果
5. scripts/check.sh 結果，如果有執行
6. install/uninstall smoke result，如果有執行
7. 已知限制
```

### 4.5 Agent 無法開 PR 時

若 agent 的環境無法開 PR，仍應完成：

```text
從最新 master 建立 branch
在 branch 上實作
執行 pytest 與 ruff check .
commit
push branch
回報 branch name 與 commit SHA
```

使用者再手動開 PR。

### 4.6 Branch 規則

建議每個 batch 使用獨立 branch：

```text
codex/batch-a
codex/batch-b
codex/batch-c
codex/batch-d
```

每個 batch 完成並 merge 後，下一個 batch 必須從最新 `master` 重新開 branch。

不要在同一個 branch 連續做多個 batch，除非使用者明確要求。

## 5. 最小人工介入、但穩定的策略

不要一次實作 Task 1 到 Task 11。

建議分成三個 implementation batches，再加一個 install/docs batch：

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

每個 batch 結束時，agent 必須回報：

```text
變更了哪些檔案
完成了哪些 tasks
pytest 是否通過
ruff check . 是否通過
scripts/check.sh 是否通過，如果已存在
已知限制
```

## 6. 為什麼不一次跑完

一次完成 Task 1-11 的風險：

```text
parser 錯，後面的 rule tests 可能建立在錯資料上
normalization 錯，規則會大量誤判
protected 邏輯錯，會誤刪有語意短句
rule conflict resolution 錯，cleaned SRT 看似成功但內容不可信
apply mode 與 install script 會把問題混在一起，難以定位
```

分 batch 的目的不是讓使用者懂 Python，而是避免錯誤堆疊。

## 7. Batch A 指令

Agent 應在 Batch A 實作下列內容。

```text
只實作 Batch A：Task 1 through Task 4。

範圍：
- Project skeleton
- pyproject.toml
- src/srt_clean package
- minimal CLI help
- SRT parser and writer
- strict profile loader
- built-in profile files
- deterministic normalization
- 這些 tasks 需要的 pytest tests 與 synthetic fixtures

不要實作 Task 5 或後續 task。
不要實作 rule application、clean mode、report mode、apply mode、install scripts 或 documentation pass，除非 Batch A 測試必要。

請自行在 tests/fixtures/ 建立需要的小型 synthetic fixtures。
不要要求使用者提供測試檔案。
不要使用真實商業字幕樣本。

執行：
pytest
ruff check .

如果任一指令失敗，先修正問題並重新執行。
兩個指令都通過後才停止。

最後回報：
1. 變更了哪些檔案
2. 完成了哪些 tasks
3. pytest 結果
4. ruff 結果
5. 已知限制
```

## 8. Batch B 指令

Batch A 通過後，agent 才能執行 Batch B。

```text
只實作 Batch B：Task 5 and Task 6。

範圍：
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
- 這些 tasks 需要的 pytest tests 與 synthetic fixtures

不要實作 report mode、clean mode、apply mode、install scripts 或 documentation pass。

請自行在 tests/fixtures/ 建立需要的小型 synthetic fixtures。
不要要求使用者提供測試檔案。
不要使用真實商業字幕樣本。

執行：
pytest
ruff check .

如果任一指令失敗，先修正問題並重新執行。
兩個指令都通過後才停止。

最後回報：
1. 變更了哪些檔案
2. 完成了哪些 tasks
3. pytest 結果
4. ruff 結果
5. 已知限制
```

## 9. Batch C 指令

Batch B 通過後，agent 才能執行 Batch C。

```text
只實作 Batch C：Task 7 and Task 8。

範圍：
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
- 這些 tasks 需要的 pytest tests 與 synthetic fixtures

不要實作 apply mode、install scripts 或 documentation pass。
不要實作 P0 不支援的 options：--in-place、--preview-output、--allow-stale-decisions、--include-review 或 profile auto detection。

請自行在 tests/fixtures/ 建立需要的小型 synthetic fixtures。
不要要求使用者提供測試檔案。
不要使用真實商業字幕樣本。

執行：
pytest
ruff check .

如果任一指令失敗，先修正問題並重新執行。
兩個指令都通過後才停止。

最後回報：
1. 變更了哪些檔案
2. 完成了哪些 tasks
3. pytest 結果
4. ruff 結果
5. 測試過的 example command，優先使用：
   srt-clean --profile jp-adult-soft --level moderate <fixture>.srt
6. 已知限制
```

## 10. Batch D 指令

Batch C 通過，且使用者對 clean mode 方向滿意後，agent 才能執行 Batch D。

```text
只實作 Batch D：Task 9 through Task 11。

範圍：
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
- 這個 batch 需要的 tests 與 smoke checks

不要實作 future roadmap features。
不要實作 P0 不支援的 options，除非現有規格明確要求。

請自行在 tests/fixtures/ 建立需要的小型 synthetic fixtures。
不要要求使用者提供測試檔案。
不要使用真實商業字幕樣本。

執行：
pytest
ruff check .

如果 scripts/check.sh 已存在，也執行：
bash scripts/check.sh

如果任一指令失敗，先修正問題並重新執行。
所有檢查都通過後才停止。

最後回報：
1. 變更了哪些檔案
2. 完成了哪些 tasks
3. pytest 結果
4. ruff 結果
5. scripts/check.sh 結果
6. install/uninstall smoke result，如果有執行
7. 已知限制
```

## 11. 可選的快速方案

若使用者明確要求減少互動次數，可用兩段式：

```text
Fast Batch 1: Tasks 1-6
Fast Batch 2: Tasks 7-11
```

這比較快，但穩定性較低。

除非使用者明確接受較高風險，不建議一次執行 Task 1-11。

## 12. Batch C 後的人工檢查

Batch C 完成後，使用者可以用一個 repo 外的私人真實 SRT 測試：

```bash
srt-clean --profile jp-adult-soft --level moderate sample-real-01.srt
```

使用者只需要檢查：

```text
原始 SRT 沒有被改動
.cleaned.srt 有產生
.clean-report.txt 有產生
明顯重複的低資訊 cue 有減少
protected short phrases 沒有明顯被誤刪
report 看得懂
```

不要 commit 私人真實 SRT samples。

## 13. 成功定義

最小可用成功點是 Batch C 通過。

此時：

```bash
srt-clean --profile jp-adult-soft --level moderate sample.srt
```

應該產生：

```text
sample.cleaned.srt
sample.clean-report.txt
```

完整 P0 成功點是 Batch D 通過。

此時專案應支援：

```bash
srt-clean --mode report --profile jp-adult-soft sample.srt
vi sample.clean-decisions.yml
srt-clean --mode apply --decisions sample.clean-decisions.yml sample.srt
bash scripts/check.sh
```
