from __future__ import annotations

from pathlib import Path

import pytest

from srt_clean.models import ProfileError
from srt_clean.profile import list_builtin_profiles, load_profile, validate_profile_data

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_list_builtin_profiles() -> None:
    assert list_builtin_profiles() == [
        "en-adult-soft",
        "en-translation-soft",
        "jp-adult-soft",
    ]


def test_load_each_builtin_profile() -> None:
    names = list_builtin_profiles()

    profiles = [load_profile(name) for name in names]

    assert [profile.profile for profile in profiles] == names


def test_missing_profile_fails_clearly() -> None:
    with pytest.raises(ProfileError) as excinfo:
        load_profile("missing-profile")

    assert "profile not found" in str(excinfo.value)


def test_invalid_yaml_fails() -> None:
    path = REPO_ROOT / "tests/fixtures/invalid_profile.yml"
    path.write_text("profile: [\n", encoding="utf-8")
    try:
        with pytest.raises(ProfileError) as excinfo:
            load_profile(str(path))
    finally:
        path.unlink()

    assert "invalid YAML" in str(excinfo.value)


def test_unknown_rule_type_exits_code_4() -> None:
    data = {
        "version": 1,
        "profile": "invalid",
        "rules": [
            {
                "id": "bad",
                "severity": "safe",
                "match": {"type": "not_real"},
                "action": {"type": "remove"},
            }
        ],
    }

    with pytest.raises(ProfileError) as excinfo:
        validate_profile_data(data, source_path=REPO_ROOT / "invalid.yml")

    assert excinfo.value.exit_code == 4
    assert "unknown match.type" in str(excinfo.value)


def test_unknown_action_exits_code_4() -> None:
    data = {
        "version": 1,
        "profile": "invalid",
        "rules": [
            {
                "id": "bad",
                "severity": "safe",
                "match": {"type": "protected_text"},
                "action": {"type": "explode"},
            }
        ],
    }

    with pytest.raises(ProfileError) as excinfo:
        validate_profile_data(data, source_path=REPO_ROOT / "invalid.yml")

    assert excinfo.value.exit_code == 4
    assert "unknown action.type" in str(excinfo.value)


def test_regex_compile_error_exits_code_4() -> None:
    data = {
        "version": 1,
        "profile": "invalid",
        "rules": [
            {
                "id": "bad",
                "severity": "safe",
                "match": {"type": "regex_text", "regex": ["("]},
                "action": {"type": "remove"},
            }
        ],
    }

    with pytest.raises(ProfileError) as excinfo:
        validate_profile_data(data, source_path=REPO_ROOT / "invalid.yml")

    assert excinfo.value.exit_code == 4
    assert "regex compile error" in str(excinfo.value)


def test_missing_list_reference_exits_code_4() -> None:
    data = {
        "version": 1,
        "profile": "invalid",
        "lists": {},
        "rules": [
            {
                "id": "bad",
                "severity": "safe",
                "match": {"type": "text_in_list", "list": "missing"},
                "action": {"type": "remove"},
            }
        ],
    }

    with pytest.raises(ProfileError) as excinfo:
        validate_profile_data(data, source_path=REPO_ROOT / "invalid.yml")

    assert excinfo.value.exit_code == 4
    assert "references missing list" in str(excinfo.value)


def test_remove_action_rejects_count_field() -> None:
    data = {
        "version": 1,
        "profile": "invalid",
        "rules": [
            {
                "id": "bad",
                "severity": "safe",
                "match": {"type": "protected_text"},
                "action": {"type": "remove", "count": 1},
            }
        ],
    }

    with pytest.raises(ProfileError) as excinfo:
        validate_profile_data(data, source_path=REPO_ROOT / "invalid.yml")

    assert excinfo.value.exit_code == 4
    assert "unknown fields: count" in str(excinfo.value)


def test_report_action_rejects_max_repeats_field() -> None:
    data = {
        "version": 1,
        "profile": "invalid",
        "rules": [
            {
                "id": "bad",
                "severity": "review",
                "match": {"type": "protected_text"},
                "action": {"type": "report", "max_repeats": 1},
            }
        ],
    }

    with pytest.raises(ProfileError) as excinfo:
        validate_profile_data(data, source_path=REPO_ROOT / "invalid.yml")

    assert excinfo.value.exit_code == 4
    assert "unknown fields: max_repeats" in str(excinfo.value)
