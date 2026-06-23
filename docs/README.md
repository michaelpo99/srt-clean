# docs/

本目錄放置 `srt-clean` 的產品規格、架構規格、測試規格與 Codex / AI agent 執行手冊。

Codex 或其它 AI agent 實作前必須先閱讀這些文件，並以這些文件作為 source of truth。

## 文件清單

```text
SDD-srt-clean.md
  產品規格。定義 CLI 行為、SRT parser、rule types、actions、profiles、report、decisions、tests、exit codes 與 roadmap。

SDD-ARCH-python-project-structure.md
  架構規格。定義 Python package layout、venv 策略、install scripts、開發流程、profile 位置、README 要求與 P0 實作順序。

SDD-P0-implementation-plan.md
  P0 實作補強與 task plan。定義 P0 對模糊行為的最終決策、mode output matrix、hash 規則、normalization 順序、conflict resolution、repeated_phrase 演算法與分段實作計畫。

SDD-TESTING.md
  測試策略。定義 tests / fixtures 位置、expected output 命名、agent 每個 task 必須測什麼，以及使用者需要看哪些結果。

SDD-DOCS-STYLE.md
  文件語言與撰寫風格。定義文件以繁體中文為主，但 CLI、YAML、module、action、severity 等技術 token 保留英文。

CODEX-RUNBOOK.md
  給 Codex / AI agent 直接讀取的執行手冊。包含 batch 指令、檢查要求與最小人工介入的實作計畫。使用者也可以複製其中 batch 指令給 Codex，但這不是唯一用途。
```

## 實作閱讀順序

Codex 或其它 AI agent 應依序閱讀：

```text
1. ../AGENTS.md
2. ../README.md
3. SDD-DOCS-STYLE.md
4. SDD-ARCH-python-project-structure.md
5. SDD-srt-clean.md
6. SDD-P0-implementation-plan.md
7. SDD-TESTING.md
8. CODEX-RUNBOOK.md
```

若 `SDD-P0-implementation-plan.md` 對 P0 行為做出明確補充，而其他文件較模糊，P0 實作以該補充為準。

## 文件語言原則

本 repo 文件以繁體中文為主。

但以下 token 不翻譯：

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

範例：

```text
若輸出檔已存在且未指定 --force，CLI 必須失敗。
`protected_text` 必須先於 `remove` 規則檢查。
執行 pytest 與 ruff check . 必須通過。
```

詳細規則見：

```text
docs/SDD-DOCS-STYLE.md
```

## 修改規則

產品行為變更時，更新：

```text
docs/SDD-srt-clean.md
```

架構、packaging、install flow 或目錄 layout 變更時，更新：

```text
docs/SDD-ARCH-python-project-structure.md
```

P0 task sequence、implementation clarifications 或 acceptance criteria 變更時，更新：

```text
docs/SDD-P0-implementation-plan.md
```

測試策略、fixture 要求或 expected output 慣例變更時，更新：

```text
docs/SDD-TESTING.md
```

Codex / AI agent 執行指令或 batch plan 變更時，更新：

```text
docs/CODEX-RUNBOOK.md
```

文件語言或撰寫風格規則變更時，更新：

```text
docs/SDD-DOCS-STYLE.md
```

不要只把產品需求寫在 code comments 或 tests 裡。只要是 intentional 且 user-visible 的行為，都應該寫進 docs。

## 文件寫法

使用精確、可驗收的語句。

推薦：

```text
CLI 必須寫出 <stem>.cleaned.srt。
```

不推薦：

```text
CLI 應該大概會產生清理後檔案。
```

## 命名規則

一般規格：

```text
SDD-<topic>.md
```

架構規格：

```text
SDD-ARCH-<topic>.md
```

P0 實作規格：

```text
SDD-P0-<topic>.md
```

操作手冊：

```text
<TOOL>-RUNBOOK.md
```

未來 change request：

```text
SDD-CR-###-<slug>.md
```

未來 bug fix 規格：

```text
SDD-BUGFIX-###-<slug>.md
```
