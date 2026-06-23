from __future__ import annotations

from srt_clean.models import Cue, TextNormalizationConfig
from srt_clean.normalize import normalize_cue


def make_cue(text: str) -> Cue:
    return Cue(
        index=1,
        start_ms=1_000,
        end_ms=2_000,
        text=text,
        raw_text_lines=[text],
        raw_block="",
    )


def test_trim_and_collapse_spaces() -> None:
    cue = make_cue("  hello   world  ")

    normalized = normalize_cue(cue, TextNormalizationConfig())

    assert normalized.normalized_text == "hello world"


def test_nfkc_normalization_when_enabled() -> None:
    cue = make_cue("ＡＢＣ １２３")

    normalized = normalize_cue(cue, TextNormalizationConfig(normalize_fullwidth=True))

    assert normalized.normalized_text == "ABC 123"


def test_english_lowercase_when_enabled() -> None:
    cue = make_cue("DON'T STOP")

    normalized = normalize_cue(cue, TextNormalizationConfig(lowercase=True, normalize_fullwidth=False))

    assert normalized.normalized_text == "don't stop"


def test_outer_punctuation_stripping() -> None:
    cue = make_cue("「痛い!」")

    normalized = normalize_cue(cue, TextNormalizationConfig())

    assert normalized.normalized_text == "痛い"


def test_compact_text_removes_comparison_only_punctuation() -> None:
    cue = make_cue(" Ah...  ah〜〜 ")

    normalized = normalize_cue(
        cue,
        TextNormalizationConfig(lowercase=True, normalize_long_vowels=True, normalize_repeated_marks=True),
    )

    assert normalized.compact_text == "ahahー"


def test_normalization_does_not_mutate_output_subtitle_text() -> None:
    cue = make_cue("  ＡＢＣ...  ")

    _ = normalize_cue(cue, TextNormalizationConfig(lowercase=True))

    assert cue.text == "  ＡＢＣ...  "
