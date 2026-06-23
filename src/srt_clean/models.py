from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


EXIT_OK = 0
EXIT_GENERAL_ERROR = 1
EXIT_CLI_ERROR = 2
EXIT_PARSE_ERROR = 3
EXIT_PROFILE_ERROR = 4
EXIT_DECISIONS_ERROR = 5

SEVERITIES = {"safe", "likely_noise", "dense_low_info", "review", "protected"}
MATCH_TYPES = {
    "regex_text",
    "single_cue",
    "text_in_list",
    "protected_text",
    "adjacent_duplicate",
    "density_window",
    "repeated_phrase",
}
ACTION_TYPES = {"remove", "keep", "keep_first", "keep_first_n", "compress", "report"}


class SRTCleanError(Exception):
    """Base exception for user-facing errors."""


class CLIError(SRTCleanError):
    exit_code = EXIT_CLI_ERROR


class SRTParseError(SRTCleanError):
    exit_code = EXIT_PARSE_ERROR

    def __init__(self, message: str, *, line_number: int | None = None) -> None:
        detail = message if line_number is None else f"line {line_number}: {message}"
        super().__init__(detail)
        self.line_number = line_number


class ProfileError(SRTCleanError):
    exit_code = EXIT_PROFILE_ERROR


class DecisionsConflictError(SRTCleanError):
    exit_code = EXIT_DECISIONS_ERROR


@dataclass(slots=True)
class Cue:
    index: int
    start_ms: int
    end_ms: int
    text: str
    raw_text_lines: list[str]
    raw_block: str

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


@dataclass(slots=True)
class TextNormalizationConfig:
    trim: bool = True
    collapse_spaces: bool = True
    normalize_fullwidth: bool = True
    strip_outer_punctuation: bool = True
    normalize_long_vowels: bool = False
    normalize_repeated_marks: bool = False
    lowercase: bool = False


@dataclass(slots=True)
class NormalizedCue:
    cue: Cue
    normalized_text: str
    compact_text: str
    char_count: int
    duration_ms: int


@dataclass(slots=True)
class ProfileLevel:
    apply_severity: list[str]


@dataclass(slots=True)
class Profile:
    version: int
    profile: str
    description: str | None
    defaults: dict[str, Any]
    text_normalization: TextNormalizationConfig
    levels: dict[str, ProfileLevel]
    protected: dict[str, Any]
    lists: dict[str, list[str]]
    rules: list[dict[str, Any]]
    source_path: Path


@dataclass(slots=True)
class CheckResult:
    input_path: Path
    profile: Profile
    cue_count: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RuleMatch:
    cue_indexes: list[int]
    rule_id: str
    match_type: str
    severity: str
    suggested_action: str
    reason_zh: str
    rule_order: int
    before: str | None = None
    after: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CandidateAction:
    cue_index: int
    rule_id: str
    match_type: str
    severity: str
    action: str
    reason_zh: str
    rule_order: int
    before: str | None = None
    after: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ResolvedDecision:
    decision_id: str
    cue_index: int
    start: str
    end: str
    text_sha256: str
    rule_id: str
    severity: str
    suggested_action: str
    action: str
    reason_zh: str
    text: str | None = None
    before: str | None = None
    after: str | None = None
    secondary_rule_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PipelineResult:
    cleaned_cues: list[Cue]
    decisions: list[ResolvedDecision]


@dataclass(slots=True)
class LoadedDecision:
    decision_id: str
    cue_index: int
    start: str
    end: str
    text_sha256: str
    rule_id: str
    severity: str
    suggested_action: str
    action: str
    reason_zh: str
    text: str | None = None
    before: str | None = None
    after: str | None = None
