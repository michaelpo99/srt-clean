from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .models import ACTION_TYPES, MATCH_TYPES, Profile, ProfileError, ProfileLevel, SEVERITIES, TextNormalizationConfig

TOP_LEVEL_KEYS = {
    "version",
    "profile",
    "description",
    "defaults",
    "text_normalization",
    "levels",
    "protected",
    "lists",
    "rules",
}
DEFAULT_KEYS = {"mode", "level", "preserve_original", "output_suffix", "report"}
NORMALIZATION_KEYS = {
    "trim",
    "collapse_spaces",
    "normalize_fullwidth",
    "strip_outer_punctuation",
    "normalize_long_vowels",
    "normalize_repeated_marks",
    "lowercase",
}
LEVEL_NAMES = {"conservative", "moderate", "aggressive"}
LEVEL_KEYS = {"apply_severity"}
PROTECTED_KEYS = {"text_regex"}
RULE_KEYS = {"id", "severity", "description", "match", "action"}
ACTION_KEYS = {"type", "report", "count", "max_repeats", "zh_explanation"}


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def built_in_profiles_dir() -> Path:
    return project_root() / "profiles"


def list_builtin_profiles() -> list[str]:
    return sorted(path.stem for path in built_in_profiles_dir().glob("*.yml"))


def resolve_profile_path(name_or_path: str) -> Path:
    candidate = Path(name_or_path)
    if candidate.exists():
        return candidate.resolve()

    built_in = built_in_profiles_dir() / f"{name_or_path}.yml"
    if built_in.exists():
        return built_in.resolve()

    available = ", ".join(list_builtin_profiles())
    raise ProfileError(
        f"profile not found: {name_or_path}. Use --list-profiles or choose one of: {available}"
    )


def _ensure_mapping(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProfileError(f"{label} must be a mapping")
    return value


def _ensure_list_of_strings(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ProfileError(f"{label} must be a list of strings")
    return value


def _ensure_bool(value: Any, *, label: str) -> bool:
    if not isinstance(value, bool):
        raise ProfileError(f"{label} must be a boolean")
    return value


def _ensure_non_negative_int(value: Any, *, label: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise ProfileError(f"{label} must be a non-negative integer")
    return value


def _reject_unknown_fields(value: dict[str, Any], *, allowed: set[str], label: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        unknown_list = ", ".join(sorted(unknown))
        raise ProfileError(f"{label} has unknown fields: {unknown_list}")


def _validate_regex_list(value: Any, *, label: str) -> list[str]:
    regexes = _ensure_list_of_strings(value, label=label)
    for pattern in regexes:
        try:
            re.compile(pattern)
        except re.error as exc:
            raise ProfileError(f"{label} regex compile error: {exc}") from exc
    return regexes


def _validate_text_condition(
    value: Any, *, label: str, known_lists: dict[str, list[str]], allow_max_chars: bool = False
) -> dict[str, Any]:
    mapping = _ensure_mapping(value, label=label)
    allowed = {"in_list", "not_in_list", "regex"}
    if allow_max_chars:
        allowed.add("max_chars")
    _reject_unknown_fields(mapping, allowed=allowed, label=label)

    if "in_list" in mapping and mapping["in_list"] not in known_lists:
        raise ProfileError(f"{label}.in_list references missing list: {mapping['in_list']}")
    if "not_in_list" in mapping and mapping["not_in_list"] not in known_lists:
        raise ProfileError(f"{label}.not_in_list references missing list: {mapping['not_in_list']}")
    if "regex" in mapping:
        regex_value = mapping["regex"]
        if isinstance(regex_value, str):
            regex_value = [regex_value]
        _validate_regex_list(regex_value, label=f"{label}.regex")
        mapping["regex"] = regex_value
    if "max_chars" in mapping:
        _ensure_non_negative_int(mapping["max_chars"], label=f"{label}.max_chars")
    return mapping


def _validate_match(match_config: Any, *, rule_id: str, known_lists: dict[str, list[str]]) -> dict[str, Any]:
    mapping = _ensure_mapping(match_config, label=f"rule {rule_id} match")
    if "type" not in mapping:
        raise ProfileError(f"rule {rule_id} match.type is required")
    match_type = mapping["type"]
    if match_type not in MATCH_TYPES:
        raise ProfileError(f"rule {rule_id} uses unknown match.type: {match_type}")

    allowed_fields: dict[str, set[str]] = {
        "regex_text": {"type", "regex", "field"},
        "single_cue": {
            "type",
            "min_duration_ms",
            "max_duration_ms",
            "min_chars",
            "max_chars",
            "text",
            "exclude_protected",
        },
        "text_in_list": {"type", "list", "case_insensitive", "min_chars", "max_chars"},
        "protected_text": {"type"},
        "adjacent_duplicate": {"type", "max_chars", "max_gap_ms", "normalized_text_equal"},
        "density_window": {"type", "window_ms", "min_count", "text"},
        "repeated_phrase": {
            "type",
            "min_repeats",
            "min_phrase_chars",
            "max_phrase_chars",
            "exclude_protected",
        },
    }
    _reject_unknown_fields(mapping, allowed=allowed_fields[match_type], label=f"rule {rule_id} match")

    if match_type == "regex_text":
        if "regex" not in mapping:
            raise ProfileError(f"rule {rule_id} match.regex is required")
        _validate_regex_list(mapping["regex"], label=f"rule {rule_id} match.regex")
        if "field" in mapping and mapping["field"] not in {
            "raw_text",
            "text",
            "normalized_text",
            "compact_text",
        }:
            raise ProfileError(f"rule {rule_id} match.field is invalid: {mapping['field']}")
    elif match_type == "single_cue":
        if "text" in mapping:
            _validate_text_condition(mapping["text"], label=f"rule {rule_id} match.text", known_lists=known_lists)
        if "exclude_protected" in mapping:
            _ensure_bool(mapping["exclude_protected"], label=f"rule {rule_id} match.exclude_protected")
    elif match_type == "text_in_list":
        if "list" not in mapping:
            raise ProfileError(f"rule {rule_id} match.list is required")
        if mapping["list"] not in known_lists:
            raise ProfileError(f"rule {rule_id} match.list references missing list: {mapping['list']}")
        if "case_insensitive" in mapping:
            _ensure_bool(mapping["case_insensitive"], label=f"rule {rule_id} match.case_insensitive")
    elif match_type == "adjacent_duplicate":
        if "normalized_text_equal" in mapping:
            _ensure_bool(
                mapping["normalized_text_equal"],
                label=f"rule {rule_id} match.normalized_text_equal",
            )
    elif match_type == "density_window":
        for required_key in ("window_ms", "min_count", "text"):
            if required_key not in mapping:
                raise ProfileError(f"rule {rule_id} match.{required_key} is required")
        _ensure_non_negative_int(mapping["window_ms"], label=f"rule {rule_id} match.window_ms")
        _ensure_non_negative_int(mapping["min_count"], label=f"rule {rule_id} match.min_count")
        _validate_text_condition(
            mapping["text"],
            label=f"rule {rule_id} match.text",
            known_lists=known_lists,
            allow_max_chars=True,
        )
    elif match_type == "repeated_phrase":
        for required_key in ("min_repeats", "min_phrase_chars", "max_phrase_chars"):
            if required_key not in mapping:
                raise ProfileError(f"rule {rule_id} match.{required_key} is required")
            _ensure_non_negative_int(mapping[required_key], label=f"rule {rule_id} match.{required_key}")
        if "exclude_protected" in mapping:
            _ensure_bool(mapping["exclude_protected"], label=f"rule {rule_id} match.exclude_protected")

    for numeric_key in ("min_duration_ms", "max_duration_ms", "min_chars", "max_chars"):
        if numeric_key in mapping:
            _ensure_non_negative_int(mapping[numeric_key], label=f"rule {rule_id} match.{numeric_key}")
    return mapping


def _validate_action(action_config: Any, *, rule_id: str) -> dict[str, Any]:
    mapping = _ensure_mapping(action_config, label=f"rule {rule_id} action")
    _reject_unknown_fields(mapping, allowed=ACTION_KEYS, label=f"rule {rule_id} action")
    action_type = mapping.get("type")
    if action_type not in ACTION_TYPES:
        raise ProfileError(f"rule {rule_id} uses unknown action.type: {action_type}")

    allowed_by_type: dict[str, set[str]] = {
        "remove": {"type", "report", "zh_explanation"},
        "keep": {"type", "report", "zh_explanation"},
        "keep_first": {"type", "report", "zh_explanation"},
        "keep_first_n": {"type", "report", "zh_explanation", "count"},
        "compress": {"type", "report", "zh_explanation", "max_repeats"},
        "report": {"type", "report", "zh_explanation"},
    }
    _reject_unknown_fields(mapping, allowed=allowed_by_type[action_type], label=f"rule {rule_id} action")

    if "report" in mapping:
        _ensure_bool(mapping["report"], label=f"rule {rule_id} action.report")
    if action_type == "keep_first_n":
        if "count" not in mapping:
            raise ProfileError(f"rule {rule_id} action.count is required for keep_first_n")
        _ensure_non_negative_int(mapping["count"], label=f"rule {rule_id} action.count")
    if action_type == "compress" and "max_repeats" in mapping:
        _ensure_non_negative_int(mapping["max_repeats"], label=f"rule {rule_id} action.max_repeats")
    return mapping


def validate_profile_data(data: Any, *, source_path: Path) -> Profile:
    root = _ensure_mapping(data, label="profile")
    _reject_unknown_fields(root, allowed=TOP_LEVEL_KEYS, label="profile")

    for required in ("version", "profile", "rules"):
        if required not in root:
            raise ProfileError(f"profile missing required field: {required}")
    if root["version"] != 1:
        raise ProfileError(f"unsupported profile version: {root['version']}")

    defaults = _ensure_mapping(root.get("defaults", {}), label="defaults")
    _reject_unknown_fields(defaults, allowed=DEFAULT_KEYS, label="defaults")

    normalization_mapping = _ensure_mapping(
        root.get("text_normalization", {}), label="text_normalization"
    )
    _reject_unknown_fields(
        normalization_mapping, allowed=NORMALIZATION_KEYS, label="text_normalization"
    )
    normalization_kwargs = {}
    for key, value in normalization_mapping.items():
        normalization_kwargs[key] = _ensure_bool(value, label=f"text_normalization.{key}")
    normalization_config = TextNormalizationConfig(**normalization_kwargs)

    levels_mapping = _ensure_mapping(root.get("levels", {}), label="levels")
    levels: dict[str, ProfileLevel] = {}
    for level_name, level_value in levels_mapping.items():
        if level_name not in LEVEL_NAMES:
            raise ProfileError(f"unknown level: {level_name}")
        level_mapping = _ensure_mapping(level_value, label=f"levels.{level_name}")
        _reject_unknown_fields(level_mapping, allowed=LEVEL_KEYS, label=f"levels.{level_name}")
        if "apply_severity" not in level_mapping:
            raise ProfileError(f"levels.{level_name}.apply_severity is required")
        severities = _ensure_list_of_strings(
            level_mapping["apply_severity"], label=f"levels.{level_name}.apply_severity"
        )
        invalid = [severity for severity in severities if severity not in SEVERITIES]
        if invalid:
            raise ProfileError(f"levels.{level_name}.apply_severity has unknown severity: {invalid[0]}")
        levels[level_name] = ProfileLevel(apply_severity=severities)

    protected = _ensure_mapping(root.get("protected", {}), label="protected")
    _reject_unknown_fields(protected, allowed=PROTECTED_KEYS, label="protected")
    if "text_regex" in protected:
        _validate_regex_list(protected["text_regex"], label="protected.text_regex")

    known_lists: dict[str, list[str]] = {}
    lists_mapping = _ensure_mapping(root.get("lists", {}), label="lists")
    for list_name, list_values in lists_mapping.items():
        known_lists[list_name] = _ensure_list_of_strings(list_values, label=f"lists.{list_name}")

    rules_data = root["rules"]
    if not isinstance(rules_data, list):
        raise ProfileError("rules must be a list")
    seen_rule_ids: set[str] = set()
    validated_rules: list[dict[str, Any]] = []
    for index, rule_data in enumerate(rules_data, start=1):
        rule = _ensure_mapping(rule_data, label=f"rule {index}")
        _reject_unknown_fields(rule, allowed=RULE_KEYS, label=f"rule {index}")
        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or not rule_id:
            raise ProfileError(f"rule {index} missing id")
        if rule_id in seen_rule_ids:
            raise ProfileError(f"duplicate rule id: {rule_id}")
        seen_rule_ids.add(rule_id)
        severity = rule.get("severity")
        if severity not in SEVERITIES:
            raise ProfileError(f"rule {rule_id} uses unknown severity: {severity}")
        if "match" not in rule:
            raise ProfileError(f"rule {rule_id} missing match")
        if "action" not in rule:
            raise ProfileError(f"rule {rule_id} missing action")
        match = _validate_match(rule["match"], rule_id=rule_id, known_lists=known_lists)
        action = _validate_action(rule["action"], rule_id=rule_id)
        validated_rule = dict(rule)
        validated_rule["match"] = match
        validated_rule["action"] = action
        validated_rules.append(validated_rule)

    return Profile(
        version=1,
        profile=root["profile"],
        description=root.get("description"),
        defaults=defaults,
        text_normalization=normalization_config,
        levels=levels,
        protected=protected,
        lists=known_lists,
        rules=validated_rules,
        source_path=source_path,
    )


def load_profile(name_or_path: str) -> Profile:
    source_path = resolve_profile_path(name_or_path)
    try:
        raw_data = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ProfileError(f"invalid YAML in {source_path}: {exc}") from exc
    return validate_profile_data(raw_data, source_path=source_path)
