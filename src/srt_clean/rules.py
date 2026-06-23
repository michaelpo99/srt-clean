from __future__ import annotations

import re

from .models import Cue, NormalizedCue, Profile, RuleMatch


def _protected_patterns(profile: Profile) -> list[re.Pattern[str]]:
    return [re.compile(pattern) for pattern in profile.protected.get("text_regex", [])]


def _is_protected_text(text: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _text_condition_matches(
    match_config: dict[str, object],
    normalized_cue: NormalizedCue,
    profile: Profile,
) -> bool:
    text_config = match_config.get("text")
    if not isinstance(text_config, dict):
        return True
    text = normalized_cue.normalized_text
    if "in_list" in text_config and text not in profile.lists[text_config["in_list"]]:
        return False
    if "not_in_list" in text_config and text in profile.lists[text_config["not_in_list"]]:
        return False
    if "regex" in text_config and not any(re.search(pattern, text) for pattern in text_config["regex"]):
        return False
    if "max_chars" in text_config and len(text) > text_config["max_chars"]:
        return False
    return True


def _detect_repeated_phrase(
    cue: Cue,
    normalized_cue: NormalizedCue,
    match_config: dict[str, object],
) -> str | None:
    min_repeats = match_config["min_repeats"]
    min_phrase_chars = match_config["min_phrase_chars"]
    max_phrase_chars = match_config["max_phrase_chars"]
    text = cue.text.strip()
    compact = normalized_cue.compact_text

    for phrase_length in range(min_phrase_chars, min(max_phrase_chars, len(text)) + 1):
        if len(text) % phrase_length != 0:
            continue
        repeats = len(text) // phrase_length
        phrase = text[:phrase_length]
        if repeats >= min_repeats and phrase * repeats == text:
            return phrase

    tokens = [token for token in re.split(r"[\s,，、。.!?！？;:・]+", text) if token]
    if len(tokens) >= min_repeats and len(set(tokens)) == 1:
        token = tokens[0]
        if min_phrase_chars <= len(token) <= max_phrase_chars:
            return token

    for phrase_length in range(min_phrase_chars, min(max_phrase_chars, len(compact)) + 1):
        if len(compact) % phrase_length != 0:
            continue
        repeats = len(compact) // phrase_length
        phrase = compact[:phrase_length]
        if repeats >= min_repeats and phrase * repeats == compact:
            return text[: len(text) // repeats]

    return None


def evaluate_rules(cues: list[Cue], normalized_cues: list[NormalizedCue], profile: Profile) -> list[RuleMatch]:
    matches: list[RuleMatch] = []
    protected_patterns = _protected_patterns(profile)
    normalized_by_index = {cue.cue.index: cue for cue in normalized_cues}

    for rule_order, rule in enumerate(profile.rules):
        match_config = rule["match"]
        action_config = rule["action"]
        match_type = match_config["type"]
        action_type = action_config["type"]
        reason_zh = action_config.get("zh_explanation", "")
        severity = rule["severity"]
        rule_id = rule["id"]

        if match_type == "protected_text":
            for normalized_cue in normalized_cues:
                if _is_protected_text(normalized_cue.normalized_text, protected_patterns):
                    matches.append(
                        RuleMatch(
                            cue_indexes=[normalized_cue.cue.index],
                            rule_id=rule_id,
                            match_type=match_type,
                            severity=severity,
                            suggested_action="keep",
                            reason_zh=reason_zh,
                            rule_order=rule_order,
                            before=normalized_cue.cue.text,
                        )
                    )
            continue

        if match_type == "regex_text":
            field = match_config.get("field", "compact_text")
            regexes = [re.compile(pattern) for pattern in match_config["regex"]]
            for normalized_cue in normalized_cues:
                field_value = {
                    "raw_text": "\n".join(normalized_cue.cue.raw_text_lines),
                    "text": normalized_cue.cue.text,
                    "normalized_text": normalized_cue.normalized_text,
                    "compact_text": normalized_cue.compact_text,
                }[field]
                if any(regex.search(field_value) for regex in regexes):
                    matches.append(
                        RuleMatch(
                            cue_indexes=[normalized_cue.cue.index],
                            rule_id=rule_id,
                            match_type=match_type,
                            severity=severity,
                            suggested_action=action_type,
                            reason_zh=reason_zh,
                            rule_order=rule_order,
                            before=normalized_cue.cue.text,
                        )
                    )
            continue

        if match_type == "single_cue":
            for normalized_cue in normalized_cues:
                if "min_duration_ms" in match_config and normalized_cue.duration_ms < match_config["min_duration_ms"]:
                    continue
                if "max_duration_ms" in match_config and normalized_cue.duration_ms > match_config["max_duration_ms"]:
                    continue
                if "min_chars" in match_config and normalized_cue.char_count < match_config["min_chars"]:
                    continue
                if "max_chars" in match_config and normalized_cue.char_count > match_config["max_chars"]:
                    continue
                if match_config.get("exclude_protected") and _is_protected_text(
                    normalized_cue.normalized_text, protected_patterns
                ):
                    continue
                if not _text_condition_matches(match_config, normalized_cue, profile):
                    continue
                matches.append(
                    RuleMatch(
                        cue_indexes=[normalized_cue.cue.index],
                        rule_id=rule_id,
                        match_type=match_type,
                        severity=severity,
                        suggested_action=action_type,
                        reason_zh=reason_zh,
                        rule_order=rule_order,
                        before=normalized_cue.cue.text,
                    )
                )
            continue

        if match_type == "text_in_list":
            values = profile.lists[match_config["list"]]
            for normalized_cue in normalized_cues:
                text = normalized_cue.normalized_text
                if match_config.get("case_insensitive"):
                    matched = text.lower() in {value.lower() for value in values}
                else:
                    matched = text in values
                if not matched:
                    continue
                if "min_chars" in match_config and normalized_cue.char_count < match_config["min_chars"]:
                    continue
                if "max_chars" in match_config and normalized_cue.char_count > match_config["max_chars"]:
                    continue
                matches.append(
                    RuleMatch(
                        cue_indexes=[normalized_cue.cue.index],
                        rule_id=rule_id,
                        match_type=match_type,
                        severity=severity,
                        suggested_action=action_type,
                        reason_zh=reason_zh,
                        rule_order=rule_order,
                        before=normalized_cue.cue.text,
                    )
                )
            continue

        if match_type == "adjacent_duplicate":
            for left, right in zip(normalized_cues, normalized_cues[1:]):
                if right.cue.start_ms - left.cue.end_ms > match_config["max_gap_ms"]:
                    continue
                if right.char_count > match_config["max_chars"]:
                    continue
                if match_config.get("normalized_text_equal") and left.normalized_text != right.normalized_text:
                    continue
                matches.append(
                    RuleMatch(
                        cue_indexes=[left.cue.index, right.cue.index],
                        rule_id=rule_id,
                        match_type=match_type,
                        severity=severity,
                        suggested_action=action_type,
                        reason_zh=reason_zh,
                        rule_order=rule_order,
                        before=right.cue.text,
                        metadata={"keep_count": 1},
                    )
                )
            continue

        if match_type == "density_window":
            seen_groups: set[tuple[int, ...]] = set()
            for base_cue in normalized_cues:
                group: list[int] = []
                window_end = base_cue.cue.start_ms + match_config["window_ms"]
                for candidate in normalized_cues:
                    if candidate.cue.start_ms < base_cue.cue.start_ms or candidate.cue.start_ms > window_end:
                        continue
                    if not _text_condition_matches(match_config, candidate, profile):
                        continue
                    group.append(candidate.cue.index)
                if len(group) >= match_config["min_count"]:
                    group_key = tuple(group)
                    if group_key in seen_groups:
                        continue
                    seen_groups.add(group_key)
                    matches.append(
                        RuleMatch(
                            cue_indexes=group,
                            rule_id=rule_id,
                            match_type=match_type,
                            severity=severity,
                            suggested_action=action_type,
                            reason_zh=reason_zh,
                            rule_order=rule_order,
                            metadata={
                                "keep_count": action_config["count"],
                                "group_start_ms": normalized_by_index[group[0]].cue.start_ms,
                                "group_end_ms": normalized_by_index[group[-1]].cue.end_ms,
                                "group_size": len(group),
                            },
                        )
                    )
            continue

        if match_type == "repeated_phrase":
            for normalized_cue in normalized_cues:
                if match_config.get("exclude_protected") and _is_protected_text(
                    normalized_cue.normalized_text, protected_patterns
                ):
                    continue
                after = _detect_repeated_phrase(normalized_cue.cue, normalized_cue, match_config)
                if after is None or after == normalized_cue.cue.text:
                    continue
                matches.append(
                    RuleMatch(
                        cue_indexes=[normalized_cue.cue.index],
                        rule_id=rule_id,
                        match_type=match_type,
                        severity=severity,
                        suggested_action=action_type,
                        reason_zh=reason_zh,
                        rule_order=rule_order,
                        before=normalized_cue.cue.text,
                        after=after,
                    )
                )

    return matches
