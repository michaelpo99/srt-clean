from __future__ import annotations

from pathlib import Path

import yaml

from srt_clean.actions import resolve_actions
from srt_clean.normalize import normalize_cues
from srt_clean.parser import parse_srt_file, parse_srt_text
from srt_clean.profile import load_profile, validate_profile_data
from srt_clean.report import build_report_text
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


def test_protected_cue_blocks_automatic_remove_and_report_marks_blocked(tmp_path: Path) -> None:
    profile_data = yaml.safe_load(
        """
version: 1
profile: synthetic-protected-block
defaults:
  mode: clean
  level: moderate
text_normalization:
  trim: true
  collapse_spaces: true
levels:
  conservative:
    apply_severity: [safe]
  moderate:
    apply_severity: [safe]
  aggressive:
    apply_severity: [safe]
protected:
  text_regex:
    - "^(痛い)$"
lists:
  protected_low_info:
    - "痛い"
rules:
  - id: remove_protected_phrase
    severity: safe
    match:
      type: text_in_list
      list: protected_low_info
    action:
      type: remove
      report: true
      zh_explanation: "synthetic remove"
  - id: protected_semantic_short_phrase
    severity: protected
    match:
      type: protected_text
    action:
      type: keep
      report: true
      zh_explanation: "synthetic protected"
"""
    )
    profile = validate_profile_data(profile_data, source_path=tmp_path / "synthetic.yml")
    cues = parse_srt_text("1\n00:00:01,000 --> 00:00:02,000\n痛い\n")
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

    assert [cue.text for cue in result.cleaned_cues] == ["痛い"]
    assert result.decisions[0].metadata["blocked_by_protected"] is True

    report_path = tmp_path / "input.srt"
    report_path.write_text("1\n00:00:01,000 --> 00:00:02,000\n痛い\n", encoding="utf-8")
    report_text = build_report_text(
        source_path=report_path,
        profile_name=profile.profile,
        mode="clean",
        level="moderate",
        total_cues=1,
        cleaned_cues=result.cleaned_cues,
        decisions=result.decisions,
        warnings=[],
    )
    assert "blocked_by_protected=true" in report_text
