from __future__ import annotations

from srt_clean.actions import resolve_actions
from srt_clean.normalize import normalize_cues
from srt_clean.parser import parse_srt_text
from srt_clean.profile import load_profile
from srt_clean.rules import evaluate_rules


def test_en_translation_profile_allows_model_meta_output_remove() -> None:
    cues = parse_srt_text("1\n00:00:01,000 --> 00:00:02,000\nTranslation: hello\n")
    profile = load_profile("en-translation-soft")
    normalized = normalize_cues(cues, profile.text_normalization)
    matches = evaluate_rules(cues, normalized, profile)

    rule_ids = {match.rule_id for match in matches}
    assert "model_meta_output" in rule_ids
    assert "adjacent_duplicate_translation" not in rule_ids

    result = resolve_actions(
        cues=cues,
        normalized_cues=normalized,
        profile=profile,
        matches=matches,
        mode="clean",
        level="conservative",
    )

    assert result.cleaned_cues == []


def test_en_translation_profile_levels_do_not_apply_review() -> None:
    profile = load_profile("en-translation-soft")

    assert profile.levels["conservative"].apply_severity == ["safe"]
    assert profile.levels["moderate"].apply_severity == ["safe"]
    assert profile.levels["aggressive"].apply_severity == ["safe"]
