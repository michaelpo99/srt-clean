# SDD: srt-clean

最後更新：2026-06-23

## 1. 產品目標

`srt-clean` 是一支 SRT 字幕清理 CLI。

它的主要目標是處理 ASR 產生的 `.srt` 字幕中常見的低資訊、過度密集、重複、幻覺與切分異常問題，特別是 Whisper / WhisperX 在長音訊、背景音、非語義發聲、笑聲、呼吸聲、呻吟聲、嘆息聲、片尾空白或噪音段落中產生的大量無效字幕。

固定定位：

> 保留原始時間軸與有語意內容，清理低資訊或明顯異常的字幕 cue，降低字幕遮擋畫面的程度。

第一版必須支援：

1. 讀取 `.srt`。
2. 輸出清理後的 `.cleaned.srt`。
3. 輸出清理報告 `.clean-report.txt`。
4. 以 YAML profile 設定清理規則。
5. 支援日文與英文 profile。
6. 支援 `report` / `clean` / `apply` 三種模式。
7. 預設不覆蓋原始字幕。
8. 對可能有語意的短句採保護策略，不自動刪除。

## 2. 產品邊界

### 2.1 可以做

1. 刪除或壓縮低資訊短音，例如長串單一假名、短促感嘆音、重複呼吸聲。
2. 刪除明顯 ASR 幻覺，例如孤立英數片段、長串笑聲字元、常見無關片語。
3. 偵測短時間內大量低資訊 cue 的字幕密度問題。
4. 偵測相鄰 cue 完全重複或高度相似。
5. 壓縮單一 cue 內重複過多的片語。
6. 保留或保護可能有語意的短句。
7. 產生中文可讀的報告，讓不懂日文的人也能理解清理原因。
8. 允許使用者以 decisions 檔做部分套用。

### 2.2 不應做

1. 不執行 ASR。
2. 不翻譯字幕。
3. 不重新產生語音時間軸。
4. 不讀取影片或音訊內容。
5. 不依畫面內容判斷字幕遮擋。
6. 不用 LLM 自動判斷語意。
7. 不主動改寫正常字幕句子。
8. 不自動合併不同語意的對話 cue。
9. 不做成人內容理解或分類；只處理字幕文字與時間軸格式。

## 3. 核心概念

### 3.1 Cue

一個 SRT cue 包含：

```text
index
start_time --> end_time
text lines
```

內部資料結構建議：

```python
@dataclass
class Cue:
    index: int
    start_ms: int
    end_ms: int
    text: str
    raw_text_lines: list[str]
    raw_block: str
```

### 3.2 Normalized text

規則比對不應直接使用原文，應先建立 normalized text。

建議欄位：

```python
@dataclass
class NormalizedCue:
    cue: Cue
    normalized_text: str
    compact_text: str
    char_count: int
    duration_ms: int
```

`normalized_text` 用於一般比對。
`compact_text` 用於重複音、長串字元與相似度比對，通常移除空白、標點、全半形差異與延長符號差異。

### 3.3 Severity

每個規則必須有 severity。

```text
safe
  高信心可自動處理。clean conservative 會套用。

likely_noise
  很可能是噪音或低資訊字幕。clean moderate 會套用。

dense_low_info
  與字幕密度有關，可能較積極。clean aggressive 才套用，或依 profile 決定。

review
  僅列入報告，不自動處理。

protected
  明確保留，不自動刪除。
```

### 3.4 Action

第一版至少支援：

```text
remove
  刪除該 cue。

keep
  保留該 cue。

keep_first
  對一組重複 cue 保留第一筆，移除後續筆。

keep_first_n
  對一個密度窗口或群組保留前 N 筆，移除其餘筆。

compress
  對單一 cue 內重複片語做壓縮，不移除 cue。

report
  只報告，不修改。
```

第二版可加入：

```text
merge_to_previous
  將文字合併到前一 cue，時間軸可延伸。

replace_text
  將 cue 文字替換成設定值。
```

P0 不要求 `merge_to_previous` 與 `replace_text`。

## 4. CLI 規格

### 4.1 基本用法

```bash
srt-clean input.srt
srt-clean --profile jp-adult-soft input.srt
srt-clean --profile en-adult-soft input.srt
srt-clean --profile en-translation-soft input.srt
```

預設行為：

```text
mode=clean
level=moderate
profile=auto
output=<stem>.cleaned.srt
report=<stem>.clean-report.txt
preserve_original=true
```

### 4.2 Report 模式

```bash
srt-clean --mode report --profile jp-adult-soft input.srt
```

產出：

```text
input.clean-report.txt
input.clean-decisions.yml
```

`report` 模式不產生 cleaned SRT，或只在明確指定 `--preview-output` 時產生 preview。

### 4.3 Clean 模式

```bash
srt-clean --mode clean --profile jp-adult-soft --level moderate input.srt
```

產出：

```text
input.cleaned.srt
input.clean-report.txt
```

`clean` 模式會依照 profile、level 與 severity 自動套用規則。

### 4.4 Apply 模式

```bash
srt-clean --mode apply --decisions input.clean-decisions.yml input.srt
```

產出：

```text
input.cleaned.srt
input.apply-report.txt
```

`apply` 模式只依 decisions 檔處理，不重新根據 profile 自動決策。若 decisions 檔引用的 cue index、timecode 或原文 hash 不一致，應報錯或列為 conflict。

### 4.5 建議參數

```text
--profile <name-or-path>
    指定內建 profile 名稱或 YAML 路徑。

--mode report|clean|apply
    執行模式。預設 clean。

--level conservative|moderate|aggressive
    清理強度。預設 moderate。

--output <path>
    指定 cleaned SRT 輸出路徑。

--report-output <path>
    指定報告輸出路徑。

--decisions <path>
    apply 模式使用的 decisions YAML。

--explain-lang zh-TW|en
    報告說明語言。第一版預設 zh-TW。

--in-place
    覆蓋原始檔。第一版可不實作；若實作，必須先建立 .bak。

--force
    覆蓋已存在的 cleaned / report 檔。

--check
    檢查 profile、輸入檔與輸出路徑，不執行清理。

--list-profiles
    列出內建 profiles。

--include-review
    clean 模式也套用 severity=review 的項目。預設 false。

--dry-run
    等同 report，但可顯示將輸出的統計。

--verbose
    顯示詳細處理資訊。
```

## 5. 輸入與輸出

### 5.1 輸入

只接受 `.srt`。

第一版不遞迴目錄。後續可以加：

```bash
srt-clean --dir ./subs
```

### 5.2 輸出命名

若輸入：

```text
sample.srt
```

預設輸出：

```text
sample.cleaned.srt
sample.clean-report.txt
```

Report 模式額外輸出：

```text
sample.clean-decisions.yml
```

### 5.3 SRT 輸出規則

1. 輸出 index 必須重新編號，從 1 開始連續遞增。
2. timecode 使用原始 cue 的 start / end，不任意調整。
3. 被刪除 cue 不保留空 index。
4. `compress` 只改文字，不改時間軸。
5. 若 cue 文字被壓縮成空字串，該 cue 應刪除並在 report 標明。
6. 原始換行可簡化為單行；後續再支援 line wrapping。

## 6. Profile YAML 規格

### 6.1 Profile 基本結構

```yaml
version: 1

profile: jp-adult-soft
description: Clean low-information Japanese ASR subtitles.

defaults:
  mode: clean
  level: moderate
  preserve_original: true
  output_suffix: ".cleaned"
  report: true

text_normalization:
  trim: true
  collapse_spaces: true
  normalize_fullwidth: true
  strip_outer_punctuation: true
  normalize_long_vowels: true
  normalize_repeated_marks: true

levels:
  conservative:
    apply_severity:
      - safe
  moderate:
    apply_severity:
      - safe
      - likely_noise
  aggressive:
    apply_severity:
      - safe
      - likely_noise
      - dense_low_info

protected:
  text_regex: []

lists: {}

rules: []
```

### 6.2 List

`lists` 用於儲存可被多個 rule 使用的詞表。

```yaml
lists:
  low_info_jp_vocal:
    - "あ"
    - "あっ"
    - "ん"
    - "んっ"
    - "はぁ"
```

### 6.3 Protected

`protected` 應在所有 remove / compress 前檢查。

```yaml
protected:
  text_regex:
    - "^(痛い|いたい)$"
    - "^(やめて|やめないで|やだ|嫌だ)$"
    - "^(待って|ちょっと待って)$"
    - "^(大丈夫|大丈夫です)$"
    - "^(ダメ|だめ|無理|むり)$"
    - "^(苦しい|苦しくない)$"
    - "^(気持ちいい|気持ちいいです)$"
    - "^(お願いします|ごめんなさい|すいません)$"
```

Protected 命中時：

1. 不可自動 remove。
2. 可 report。
3. 可被 `compress` 處理，但僅限同一句重複，且結果不得為空。
4. 若 action 來自 decisions 檔，使用者明確指定 `remove` 時可以刪，但 apply report 必須標明 `user_override_protected`。

## 7. Rule type 規格

### 7.1 regex_text

用途：偵測長串單一假名、長串笑聲、孤立英數等。

```yaml
- id: pure_repeated_kana_long
  severity: safe
  match:
    type: regex_text
    regex:
      - "^[あぁー〜…\\s]{6,}$"
      - "^[んー〜…\\s]{4,}$"
      - "^[うー〜…\\s]{4,}$"
      - "^(はぁっ?){3,}$"
  action:
    type: remove
    report: true
```

比對欄位預設使用 `compact_text`。若需使用原文，可加入：

```yaml
field: raw_text
```

### 7.2 single_cue

用途：依 cue duration、字數、詞表判斷。

```yaml
- id: low_info_vocal_short_duration
  severity: likely_noise
  match:
    type: single_cue
    max_duration_ms: 800
    text:
      in_list: low_info_jp_vocal
  action:
    type: remove
```

可支援條件：

```text
min_duration_ms
max_duration_ms
min_chars
max_chars
text.in_list
text.not_in_list
text.regex
exclude_protected
```

### 7.3 adjacent_duplicate

用途：相鄰 cue 完全重複。

```yaml
- id: adjacent_duplicate_short
  severity: safe
  match:
    type: adjacent_duplicate
    max_chars: 12
    max_gap_ms: 1500
    normalized_text_equal: true
  action:
    type: keep_first
```

### 7.4 adjacent_similarity

用途：相鄰 cue 高度相似。

```yaml
- id: adjacent_similarity_short
  severity: review
  match:
    type: adjacent_similarity
    max_chars: 16
    similarity_gte: 0.90
    max_gap_ms: 1200
  action:
    type: report
```

P0 similarity 可用 `difflib.SequenceMatcher`。

### 7.5 density_window

用途：短時間內低資訊字幕過多。

```yaml
- id: dense_low_info_vocal_window
  severity: dense_low_info
  match:
    type: density_window
    window_ms: 8000
    min_count: 3
    text:
      in_list: low_info_jp_vocal
      max_chars: 8
  action:
    type: keep_first_n
    count: 1
```

演算法：

1. 依 cue start_ms 排序。
2. 對每個 cue 建立 `[start_ms, start_ms + window_ms]` 視窗。
3. 找出視窗內符合條件的 cue。
4. 若數量 >= min_count，建立 group。
5. group 內依時間排序，保留前 N 筆，其餘標記 remove。
6. 重疊 group 要去重，避免同一 cue 產生多個互斥 decision。

### 7.6 repeated_phrase

用途：單一 cue 內同一片語重複過多。

```yaml
- id: repeated_phrase_in_single_cue
  severity: likely_noise
  match:
    type: repeated_phrase
    min_repeats: 4
    min_phrase_chars: 2
    max_phrase_chars: 12
    exclude_protected: true
  action:
    type: compress
    max_repeats: 1
```

範例：

```text
気持ちいい気持ちいい気持ちいい
```

壓縮為：

```text
気持ちいい
```

對長串單一字元，例如：

```text
ああああああああああ
```

若同時命中 `pure_repeated_kana_long`，應由 remove 規則優先處理。

### 7.7 text_in_list

用途：常見 hallucination 詞表。

```yaml
- id: known_likely_hallucination
  severity: likely_noise
  match:
    type: text_in_list
    list: likely_hallucination_jp
    case_insensitive: true
    max_chars: 20
  action:
    type: remove
```

### 7.8 protected_text

用途：產生 protected report。

```yaml
- id: protected_semantic_short_phrase
  severity: protected
  match:
    type: protected_text
  action:
    type: keep
    report: true
```

## 8. 內建 Profile

### 8.1 jp-adult-soft

用途：日文 ASR SRT 中，非語義短音、長串假名、呼吸聲、笑聲與密集低資訊 cue 清理。

建議內建：

```yaml
version: 1

profile: jp-adult-soft
description: Clean low-information Japanese ASR subtitles from dense non-semantic vocalizations.

defaults:
  mode: clean
  level: moderate
  preserve_original: true
  output_suffix: ".cleaned"
  report: true

text_normalization:
  trim: true
  collapse_spaces: true
  normalize_fullwidth: true
  strip_outer_punctuation: true
  normalize_long_vowels: true
  normalize_repeated_marks: true

levels:
  conservative:
    apply_severity:
      - safe
  moderate:
    apply_severity:
      - safe
      - likely_noise
  aggressive:
    apply_severity:
      - safe
      - likely_noise
      - dense_low_info

protected:
  text_regex:
    - "^(痛い|いたい)$"
    - "^(やめて|やめないで|やだ|嫌だ)$"
    - "^(待って|ちょっと待って)$"
    - "^(大丈夫|大丈夫です)$"
    - "^(ダメ|だめ|無理|むり)$"
    - "^(苦しい|苦しくない)$"
    - "^(気持ちいい|気持ちいいです)$"
    - "^(お願いします|ごめんなさい|すいません)$"
    - "^(入った|入らない|行く|いく)$"

lists:
  low_info_jp_vocal:
    - "あ"
    - "あっ"
    - "あぁ"
    - "あー"
    - "ああ"
    - "ん"
    - "んっ"
    - "んー"
    - "んん"
    - "う"
    - "うっ"
    - "うう"
    - "はぁ"
    - "はぁっ"
    - "ふぅ"
    - "おー"
  likely_hallucination_jp:
    - "おやすみなさい"
    - "バイバイ"
    - "byh"
    - "ok"
    - "ゴーゴー"
    - "ゴーゴーゴーゴー"

rules:
  - id: pure_repeated_kana_long
    severity: safe
    description: 長串單一假名或延長音，通常是非語義聲音
    match:
      type: regex_text
      regex:
        - "^[あぁー〜…\\s]{6,}$"
        - "^[んー〜…\\s]{4,}$"
        - "^[うー〜…\\s]{4,}$"
        - "^(はぁっ?){3,}$"
    action:
      type: remove
      report: true
      zh_explanation: "長串非語義聲音，字幕價值低，容易遮擋畫面"

  - id: repeated_laughter_or_noise
    severity: safe
    description: 長串笑聲或明顯噪音字元
    match:
      type: regex_text
      regex:
        - "^(笑){5,}$"
        - "^(母){4,}$"
        - "^(父){4,}$"
    action:
      type: remove
      report: true
      zh_explanation: "疑似 ASR 幻覺或噪音字幕"

  - id: low_info_vocal_short_duration
    severity: likely_noise
    description: 很短的低資訊發聲
    match:
      type: single_cue
      max_duration_ms: 800
      text:
        in_list: low_info_jp_vocal
    action:
      type: remove
      report: true
      zh_explanation: "短促低資訊發聲"

  - id: dense_low_info_vocal_window
    severity: dense_low_info
    description: 短時間內低資訊發聲過密
    match:
      type: density_window
      window_ms: 8000
      min_count: 3
      text:
        in_list: low_info_jp_vocal
        max_chars: 8
    action:
      type: keep_first_n
      count: 1
      report: true
      zh_explanation: "短時間內同類低資訊字幕過多，只保留少量代表性字幕"

  - id: adjacent_duplicate_short
    severity: safe
    description: 相鄰短字幕完全重複
    match:
      type: adjacent_duplicate
      max_chars: 12
      max_gap_ms: 1500
      normalized_text_equal: true
    action:
      type: keep_first
      report: true
      zh_explanation: "相鄰短字幕重複，保留第一筆"

  - id: repeated_phrase_in_single_cue
    severity: likely_noise
    description: 同一句在單一 cue 中重複太多次
    match:
      type: repeated_phrase
      min_repeats: 4
      min_phrase_chars: 2
      max_phrase_chars: 12
      exclude_protected: true
    action:
      type: compress
      max_repeats: 1
      report: true
      zh_explanation: "單一字幕內重複過多，壓縮成一次"

  - id: known_likely_hallucination
    severity: likely_noise
    description: 常見 Whisper 幻覺詞
    match:
      type: text_in_list
      list: likely_hallucination_jp
      case_insensitive: true
      max_chars: 20
    action:
      type: remove
      report: true
      zh_explanation: "常見 ASR 幻覺詞，通常不是實際對話"

  - id: suspicious_numeric_or_ascii
    severity: likely_noise
    description: 日文字幕中出現孤立數字或 ASCII 片段
    match:
      type: regex_text
      regex:
        - "^[0-9]{5,}$"
        - "^[A-Za-z0-9.]{2,8}$"
    action:
      type: remove
      report: true
      zh_explanation: "孤立數字或英數片段，疑似 ASR 誤判"

  - id: ultra_short_cue
    severity: review
    description: 時間極短的 cue，可能需要合併或刪除
    match:
      type: single_cue
      max_duration_ms: 250
    action:
      type: report
      report: true
      zh_explanation: "時間太短，可能是切分異常；第一版不自動刪"

  - id: protected_semantic_short_phrase
    severity: protected
    description: 有語意短句，保留
    match:
      type: protected_text
    action:
      type: keep
      report: true
      zh_explanation: "可能有語意，不自動刪除"
```

### 8.2 en-adult-soft

用途：英文 ASR SRT 中的低資訊 filler、短促聲音與重複音清理。

保護詞必須比日文更保守，因為英文短句常有語意。

建議：

```yaml
version: 1
profile: en-adult-soft

text_normalization:
  trim: true
  collapse_spaces: true
  lowercase: true
  strip_outer_punctuation: true

protected:
  text_regex:
    - "^(no|stop|wait|don't|dont|please|hurt|okay|are you okay)$"
    - "^(i can't|i cant|don't stop|dont stop)$"
    - "^(it hurts|are you ok|are you okay)$"

lists:
  low_info_en_vocal:
    - "ah"
    - "ahh"
    - "oh"
    - "ohh"
    - "uh"
    - "um"
    - "mm"
    - "mmm"
    - "hmm"
    - "yeah"
    - "yes"
    - "oh yeah"

rules:
  - id: repeated_english_vocal_long
    severity: safe
    match:
      type: regex_text
      regex:
        - "^(a+h+|o+h+|m+m+|u+h+)$"
        - "^(ha){4,}$"
    action:
      type: remove
      report: true
      zh_explanation: "英文低資訊長音或笑聲"

  - id: dense_low_info_english_short_cues
    severity: dense_low_info
    match:
      type: density_window
      window_ms: 5000
      min_count: 4
      text:
        in_list: low_info_en_vocal
        max_chars: 8
    action:
      type: keep_first_n
      count: 2
      report: true
      zh_explanation: "短時間內英文低資訊 filler 過多"

  - id: adjacent_duplicate_short_en
    severity: safe
    match:
      type: adjacent_duplicate
      max_chars: 16
      max_gap_ms: 1500
      normalized_text_equal: true
    action:
      type: keep_first
      report: true
      zh_explanation: "相鄰英文短字幕重複"
```

### 8.3 en-translation-soft

用途：翻譯後英文 SRT 的格式與重複檢查。

此 profile 應比 `en-adult-soft` 更保守，重點是：

1. cue 數量是否一致。
2. timecode 是否未被改動。
3. 相鄰翻譯是否重複。
4. 是否出現模型多餘說明。
5. 是否出現空 cue。

P0 可以只做 SRT 本身清理；translation consistency 可以留到 `translate-srt`。

建議規則：

```yaml
version: 1
profile: en-translation-soft

protected:
  text_regex:
    - ".*"

rules:
  - id: adjacent_duplicate_translation
    severity: review
    match:
      type: adjacent_duplicate
      max_chars: 80
      max_gap_ms: 2000
      normalized_text_equal: true
    action:
      type: report
      report: true
      zh_explanation: "翻譯後相鄰字幕完全相同，可能是模型重複輸出"

  - id: model_meta_output
    severity: safe
    match:
      type: regex_text
      field: raw_text
      regex:
        - "(?i)^translation:"
        - "(?i)^here is"
        - "(?i)^note:"
        - "(?i)<think>"
    action:
      type: remove
      report: true
      zh_explanation: "翻譯模型輸出的多餘說明文字"
```

## 9. Report 規格

### 9.1 Summary

`clean-report.txt` 開頭必須有摘要。

```text
srt-clean report
source=input.srt
profile=jp-adult-soft
mode=clean
level=moderate

summary:
  total_cues=345
  output_cues=278
  removed_cues=61
  compressed_cues=6
  protected_cues=14
  review_cues=9
  estimated_removed_ratio=17.68%

rule_summary:
  pure_repeated_kana_long removed=38
  known_likely_hallucination removed=7
  repeated_phrase_in_single_cue compressed=6
  protected_semantic_short_phrase kept=14
  ultra_short_cue review=9
```

### 9.2 Detail

每筆 detail 建議格式：

```text
[REMOVE]
id=000123
cue=54
time=00:25:21,413 --> 00:25:50,050
rule=pure_repeated_kana_long
severity=safe
text=ああああああああ...
reason_zh=長串非語義聲音，字幕價值低，容易遮擋畫面
```

Compress 範例：

```text
[COMPRESS]
id=000188
cue=286
time=02:31:13,789 --> 02:31:27,859
rule=repeated_phrase_in_single_cue
severity=likely_noise
before=気持ちいい気持ちいい気持ちいい
 after=気持ちいい
reason_zh=單一字幕內重複過多，壓縮成一次
```

Protected 範例：

```text
[KEEP-PROTECTED]
id=000201
cue=103
time=00:54:33,342 --> 00:54:38,944
rule=protected_semantic_short_phrase
severity=protected
text=痛い
reason_zh=可能有語意，不自動刪除
```

## 10. Decisions 檔規格

Report 模式應產生 decisions YAML。

```yaml
version: 1
source: input.srt
source_sha256: "..."
profile: jp-adult-soft
created_at: "2026-06-23T00:00:00+08:00"

decisions:
  - id: "000123"
    cue: 54
    start: "00:25:21,413"
    end: "00:25:50,050"
    text_sha256: "..."
    rule: pure_repeated_kana_long
    severity: safe
    suggested_action: remove
    action: remove
    reason_zh: "長串非語義聲音，字幕價值低，容易遮擋畫面"

  - id: "000201"
    cue: 103
    start: "00:54:33,342"
    end: "00:54:38,944"
    text_sha256: "..."
    rule: protected_semantic_short_phrase
    severity: protected
    suggested_action: keep
    action: keep
    reason_zh: "可能有語意，不自動刪除"
```

使用者可手動改：

```yaml
action: keep
```

或：

```yaml
action: remove
```

Apply 模式驗證：

1. `source_sha256` 與目前 input 不一致時，預設報錯。
2. 可加 `--allow-stale-decisions` 強制套用，但必須比對 cue index、start、end、text hash。
3. text hash 不一致的 decision 不套用，列為 conflict。
4. protected cue 若被使用者改成 remove，允許執行，但 report 標記 `user_override_protected`。

## 11. 規則優先順序

同一 cue 可能命中多個 rule。必須有固定優先順序。

建議順序：

1. parse / validation error
2. protected_text
3. remove rules with severity safe
4. remove rules with severity likely_noise
5. compress rules
6. density_window rules
7. adjacent_duplicate / adjacent_similarity
8. review-only rules

但實際套用時要注意：

1. protected 不代表完全不處理；只禁止自動 remove。
2. remove 優先於 compress。
3. 若 cue 已 remove，不再套用 compress。
4. 若 compress 後文字變成空字串，轉為 remove。
5. density window 不應刪除 protected cue。
6. decisions 檔明確指定時，以 decisions 為準。

## 12. SRT Parser 要求

### 12.1 Timecode

支援：

```text
HH:MM:SS,mmm --> HH:MM:SS,mmm
```

P0 不要求支援 `.` 作為毫秒分隔，但可接受：

```text
HH:MM:SS.mmm --> HH:MM:SS.mmm
```

### 12.2 Parser 容錯

應處理：

1. UTF-8 BOM。
2. Windows CRLF。
3. cue index 不連續。
4. cue text 多行。
5. 檔尾多餘空白。

遇到嚴重格式錯誤：

1. 顯示錯誤行號。
2. exit code 非 0。
3. 不產生 cleaned SRT。

### 12.3 Validation

檢查：

1. `end_ms > start_ms`。
2. cue time 不應倒退；倒退列為 warning。
3. 相鄰 cue overlap 列為 warning，不自動修正。
4. 空 text cue 列為 removable candidate。

## 13. 實作架構

建議 Python package：

```text
srt-clean/
├── pyproject.toml
├── README.md
├── bin/
│   └── srt-clean
├── docs/
│   └── SDD-srt-clean.md
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
    ├── test_normalize.py
    ├── test_rules_jp.py
    ├── test_rules_en.py
    ├── test_decisions.py
    └── fixtures/
```

### 13.1 models.py

放 dataclass：

```python
@dataclass
class Cue:
    index: int
    start_ms: int
    end_ms: int
    text: str
    raw_text_lines: list[str]

@dataclass
class RuleMatch:
    decision_id: str
    cue_indexes: list[int]
    rule_id: str
    severity: str
    suggested_action: str
    reason_zh: str
    before: str | None = None
    after: str | None = None

@dataclass
class Decision:
    decision_id: str
    cue_indexes: list[int]
    action: str
    rule_id: str
    severity: str
```

### 13.2 parser.py

負責 parse SRT。

### 13.3 writer.py

負責輸出 SRT，重編 index。

### 13.4 normalize.py

負責文字正規化。

P0 normalizer：

1. `strip()`。
2. collapse whitespace。
3. `unicodedata.normalize("NFKC", text)` optional。
4. 去除外層標點。
5. 將 `〜`、`ー`、`…` 視為延長音。
6. 英文 profile lowercase。

### 13.5 profile.py

讀取 YAML，驗證 schema。

缺少必要欄位要報錯。

### 13.6 rules.py

實作 rule engine。

### 13.7 actions.py

套用 remove / keep_first / keep_first_n / compress。

### 13.8 decisions.py

讀寫 decisions YAML，做 hash 驗證。

### 13.9 report.py

輸出 report。

## 14. 測試規格

### 14.1 Parser tests

1. 基本 SRT parse。
2. 多行字幕 parse。
3. CRLF parse。
4. BOM parse。
5. index 不連續仍可 parse。
6. timecode 格式錯誤會報錯。

### 14.2 Japanese rules tests

測試：

```text
ああああああああ
```

應 remove。

```text
はぁっはぁっはぁっはぁっ
```

應 remove。

```text
痛い
```

應 keep protected。

```text
気持ちいい気持ちいい気持ちいい気持ちいい
```

應 compress 成：

```text
気持ちいい
```

```text
byH.
```

應 remove。

```text
笑笑笑笑笑笑笑
```

應 remove。

### 14.3 English rules tests

```text
ahhhhh
```

應 remove。

```text
no
```

應 keep protected。

```text
stop
```

應 keep protected。

```text
oh yeah
oh yeah
oh yeah
```

密集時才處理，不應單獨無條件刪。

### 14.4 Density window tests

建立 5 到 8 秒內多個 low-info cue，驗證 keep_first_n。

### 14.5 Decisions tests

1. report 產生 decisions。
2. 修改 action 後 apply。
3. source hash 不符時報錯。
4. stale decisions with allow flag。
5. protected 被 user override 時 report 標記。

## 15. Exit codes

```text
0  成功
1  一般執行錯誤
2  CLI 參數錯誤
3  SRT parse error
4  profile schema error
5  decisions conflict
```

## 16. P0 實作範圍

第一輪建議完成：

1. `pyproject.toml`。
2. `srt-clean` CLI。
3. SRT parser / writer。
4. YAML profile loader。
5. 內建 `jp-adult-soft.yml`。
6. 內建 `en-adult-soft.yml`。
7. 內建 `en-translation-soft.yml` 的基本 report rules。
8. rule types：
   - `regex_text`
   - `single_cue`
   - `adjacent_duplicate`
   - `density_window`
   - `repeated_phrase`
   - `text_in_list`
   - `protected_text`
9. actions：
   - `remove`
   - `keep`
   - `keep_first`
   - `keep_first_n`
   - `compress`
   - `report`
10. report output。
11. decisions output。
12. apply mode。
13. pytest tests。

P0 不必完成：

1. 音訊分析。
2. LLM 輔助判斷。
3. 自動翻譯。
4. 影片處理。
5. GUI review。
6. merge_to_previous。
7. in-place 覆蓋。

## 17. 設計風險與限制

1. 規則過度積極會誤刪真實語意短句。
2. 日文短句可能在不同情境下有不同語意，因此 protected 清單必須保守。
3. 英文短詞如 `no`、`stop`、`wait`、`please` 不可放入低資訊清單。
4. SRT 只有文字與時間軸，無法真正判斷音訊是否有人聲。
5. ASR 幻覺詞會因模型、語言、影片類型而變化，必須允許 profile 持續調整。
6. clean 模式應預設只處理 safe / likely_noise，不應處理 review。
7. aggressive 模式要明確標示可能誤刪。

## 18. 與其他工具的關係

建議 pipeline：

```text
音訊 / 影片
  -> transcribe-audio / WhisperX
  -> 原始 SRT
  -> srt-clean
  -> cleaned SRT
  -> translate-srt
  -> translated SRT
```

`srt-clean` 不依賴 `transcribe-audio`，但可由 `transcribe-audio` 在未來以 optional post-processing 呼叫。

## 19. 使用範例

### 19.1 日文字幕清理

```bash
srt-clean --profile jp-adult-soft --level moderate sample.srt
```

### 19.2 先產生報告

```bash
srt-clean --mode report --profile jp-adult-soft sample.srt
vi sample.clean-decisions.yml
srt-clean --mode apply --decisions sample.clean-decisions.yml sample.srt
```

### 19.3 英文 ASR 字幕清理

```bash
srt-clean --profile en-adult-soft --level conservative sample.en.srt
```

### 19.4 翻譯後英文字幕檢查

```bash
srt-clean --profile en-translation-soft --mode report sample.translated.en.srt
```

## 20. 後續 Roadmap

1. `merge_to_previous` action。
2. HTML report。
3. side-by-side review file。
4. directory batch mode。
5. JSON report。
6. profile schema JSON Schema。
7. confidence score。
8. WhisperX JSON 輔助清理。
9. 與 `translate-srt` 共用 SRT parser。
10. 與 `transcribe-audio` 整合為 optional post step。
