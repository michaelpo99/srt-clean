from __future__ import annotations

from pathlib import Path

from srt_clean.actions import resolve_actions
from srt_clean.normalize import normalize_cues
from srt_clean.parser import parse_srt_file
from srt_clean.profile import load_profile
from srt_clean.rules import evaluate_rules
from srt_clean.writer import write_srt_text

FIXTURES = Path(__file__).parent / "fixtures"


def test_japanese_repeated_kana_and_protected_and_repeated_phrase_rules() -> None:
    cues = parse_srt_file(FIXTURES / "jp_batch_bc.input.srt")
    profile = load_profile("jp-adult-soft")
    normalized = normalize_cues(cues, profile.text_normalization)

    matches = evaluate_rules(cues, normalized, profile)
    rule_ids = {match.rule_id for match in matches}

    assert "pure_repeated_kana_long" in rule_ids
    assert "protected_semantic_short_phrase" in rule_ids
    assert "repeated_phrase_in_single_cue" in rule_ids
    assert "known_likely_hallucination" in rule_ids


def test_adjacent_duplicate_short_generates_remove_candidate() -> None:
    cues = parse_srt_file(FIXTURES / "jp_adjacent_duplicate.input.srt")
    profile = load_profile("jp-adult-soft")
    normalized = normalize_cues(cues, profile.text_normalization)

    matches = evaluate_rules(cues, normalized, profile)

    duplicate = next(match for match in matches if match.rule_id == "adjacent_duplicate_short")
    assert duplicate.cue_indexes == [1, 2]


def test_actions_apply_moderate_cleaning_deterministically() -> None:
    cues = parse_srt_file(FIXTURES / "jp_batch_bc.input.srt")
    profile = load_profile("jp-adult-soft")
    normalized = normalize_cues(cues, profile.text_normalization)
    matches = evaluate_rules(cues, normalized, profile)

    result = resolve_actions(
        cues=cues,
        normalized_cues=normalized,
        profile=profile,
        matches=matches,
        mode="clean",
        level="moderate",
    )

    actual = write_srt_text(result.cleaned_cues)
    expected = (FIXTURES / "jp_batch_bc.expected.moderate.cleaned.srt").read_text(encoding="utf-8")
    assert actual == expected


def test_density_window_only_applies_in_aggressive() -> None:
    cues = parse_srt_file(FIXTURES / "jp_batch_bc.input.srt")
    profile = load_profile("jp-adult-soft")
    normalized = normalize_cues(cues, profile.text_normalization)
    matches = evaluate_rules(cues, normalized, profile)

    result = resolve_actions(
        cues=cues,
        normalized_cues=normalized,
        profile=profile,
        matches=matches,
        mode="clean",
        level="aggressive",
    )

    actual = write_srt_text(result.cleaned_cues)
    expected = (FIXTURES / "jp_batch_bc.expected.aggressive.cleaned.srt").read_text(encoding="utf-8")
    assert actual == expected
