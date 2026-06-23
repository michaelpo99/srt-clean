from __future__ import annotations

from pathlib import Path

from srt_clean.actions import resolve_actions
from srt_clean.normalize import normalize_cues
from srt_clean.parser import parse_srt_file
from srt_clean.profile import load_profile
from srt_clean.rules import evaluate_rules

FIXTURES = Path(__file__).parent / "fixtures"


def test_english_repeated_vocal_and_protected_rules() -> None:
    cues = parse_srt_file(FIXTURES / "en_rules.input.srt")
    profile = load_profile("en-adult-soft")
    normalized = normalize_cues(cues, profile.text_normalization)

    matches = evaluate_rules(cues, normalized, profile)
    rule_ids = {match.rule_id for match in matches}

    assert "repeated_english_vocal_long" in rule_ids
    assert "protected_semantic_short_phrase_en" in rule_ids


def test_english_density_window_keeps_only_first_n_in_aggressive() -> None:
    cues = parse_srt_file(FIXTURES / "en_rules.input.srt")
    profile = load_profile("en-adult-soft")
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

    texts = [cue.text for cue in result.cleaned_cues]
    assert "ahhhhh" not in texts
    assert "no" in texts
    assert "stop" in texts
    assert "yeah" in texts
    assert "yes" in texts
    assert "oh yeah" not in texts
    assert "hmm" not in texts
