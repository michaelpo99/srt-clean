from __future__ import annotations

import re
import unicodedata

from .models import Cue, NormalizedCue, TextNormalizationConfig

WHITESPACE_RE = re.compile(r"\s+")
OUTER_PUNCTUATION = set("!?！？。、，,.\"'`()[]{}<>「」『』【】")
COMPARISON_ONLY_PUNCTUATION = set("!?！？。、，,.\"'`()[]{}<>「」『』【】:;・")
LONG_VOWEL_MARKS = {"ー", "〜", "~", "…", "-"}


def _is_outer_punctuation(char: str) -> bool:
    if char in LONG_VOWEL_MARKS:
        return False
    if char in OUTER_PUNCTUATION:
        return True
    return unicodedata.category(char).startswith(("P", "S"))


def strip_outer_punctuation(text: str) -> str:
    start = 0
    end = len(text)
    while start < end and _is_outer_punctuation(text[start]):
        start += 1
    while end > start and _is_outer_punctuation(text[end - 1]):
        end -= 1
    return text[start:end]


def _build_compact_text(text: str, config: TextNormalizationConfig) -> str:
    compact_chars: list[str] = []
    for char in text:
        if char.isspace():
            continue
        normalized_char = char
        if config.normalize_long_vowels and char in LONG_VOWEL_MARKS:
            normalized_char = "ー"
        elif char in COMPARISON_ONLY_PUNCTUATION or unicodedata.category(char).startswith(("P", "S")):
            continue

        if config.normalize_repeated_marks and compact_chars and compact_chars[-1] == normalized_char:
            if normalized_char in LONG_VOWEL_MARKS or normalized_char == "ー":
                continue
        compact_chars.append(normalized_char)
    return "".join(compact_chars)


def normalize_cue(cue: Cue, config: TextNormalizationConfig) -> NormalizedCue:
    text = cue.text
    if config.trim:
        text = text.strip()
    if config.normalize_fullwidth:
        text = unicodedata.normalize("NFKC", text)
    if config.collapse_spaces:
        text = WHITESPACE_RE.sub(" ", text)
    if config.lowercase:
        text = text.lower()
    if config.strip_outer_punctuation:
        text = strip_outer_punctuation(text)

    compact_text = _build_compact_text(text, config)
    return NormalizedCue(
        cue=cue,
        normalized_text=text,
        compact_text=compact_text,
        char_count=len(text),
        duration_ms=cue.duration_ms,
    )


def normalize_cues(cues: list[Cue], config: TextNormalizationConfig) -> list[NormalizedCue]:
    return [normalize_cue(cue, config) for cue in cues]
