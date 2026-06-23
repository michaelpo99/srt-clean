from __future__ import annotations

import hashlib
from collections import defaultdict

from .models import CandidateAction, Cue, NormalizedCue, PipelineResult, Profile, ResolvedDecision, RuleMatch
from .writer import format_timestamp


def _text_sha256(cue: Cue) -> str:
    text_for_hash = "\n".join(cue.raw_text_lines)
    return hashlib.sha256(text_for_hash.encode("utf-8")).hexdigest()


def _expand_match(match: RuleMatch) -> list[CandidateAction]:
    if match.suggested_action == "remove":
        return [
            CandidateAction(
                cue_index=cue_index,
                rule_id=match.rule_id,
                match_type=match.match_type,
                severity=match.severity,
                action="remove",
                reason_zh=match.reason_zh,
                rule_order=match.rule_order,
                before=match.before,
                metadata=match.metadata.copy(),
            )
            for cue_index in match.cue_indexes
        ]

    if match.suggested_action == "keep_first":
        return [
            CandidateAction(
                cue_index=cue_index,
                rule_id=match.rule_id,
                match_type=match.match_type,
                severity=match.severity,
                action="remove",
                reason_zh=match.reason_zh,
                rule_order=match.rule_order,
                before=match.before,
                metadata=match.metadata.copy(),
            )
            for cue_index in match.cue_indexes[1:]
        ]

    if match.suggested_action == "keep_first_n":
        keep_count = int(match.metadata.get("keep_count", 1))
        return [
            CandidateAction(
                cue_index=cue_index,
                rule_id=match.rule_id,
                match_type=match.match_type,
                severity=match.severity,
                action="remove",
                reason_zh=match.reason_zh,
                rule_order=match.rule_order,
                before=match.before,
                metadata=match.metadata.copy(),
            )
            for cue_index in match.cue_indexes[keep_count:]
        ]

    if match.suggested_action == "compress":
        return [
            CandidateAction(
                cue_index=cue_index,
                rule_id=match.rule_id,
                match_type=match.match_type,
                severity=match.severity,
                action="compress",
                reason_zh=match.reason_zh,
                rule_order=match.rule_order,
                before=match.before,
                after=match.after,
                metadata=match.metadata.copy(),
            )
            for cue_index in match.cue_indexes
        ]

    return [
        CandidateAction(
            cue_index=cue_index,
            rule_id=match.rule_id,
            match_type=match.match_type,
            severity=match.severity,
            action="keep" if match.severity == "protected" else "report",
            reason_zh=match.reason_zh,
            rule_order=match.rule_order,
            before=match.before,
            metadata=match.metadata.copy(),
        )
        for cue_index in match.cue_indexes
    ]


def _candidate_priority(candidate: CandidateAction) -> tuple[int, int]:
    if candidate.severity == "protected":
        return (0, candidate.rule_order)
    if candidate.action == "remove":
        if candidate.match_type == "density_window":
            return (50, candidate.rule_order)
        if candidate.match_type == "adjacent_duplicate":
            return (30, candidate.rule_order)
        return ((10 if candidate.severity == "safe" else 40), candidate.rule_order)
    if candidate.action == "compress":
        return (45, candidate.rule_order)
    if candidate.action == "report":
        return (90, candidate.rule_order)
    return (80, candidate.rule_order)


def resolve_actions(
    *,
    cues: list[Cue],
    normalized_cues: list[NormalizedCue],
    profile: Profile,
    matches: list[RuleMatch],
    mode: str,
    level: str,
) -> PipelineResult:
    allowed_severities = set(profile.levels[level].apply_severity)
    candidates_by_cue: dict[int, list[CandidateAction]] = defaultdict(list)
    for match in matches:
        for candidate in _expand_match(match):
            candidates_by_cue[candidate.cue_index].append(candidate)

    cleaned_cues: list[Cue] = []
    decisions: list[ResolvedDecision] = []
    decision_counter = 1

    for cue, normalized_cue in zip(cues, normalized_cues):
        cue_candidates = sorted(candidates_by_cue.get(cue.index, []), key=_candidate_priority)
        protected = any(candidate.severity == "protected" for candidate in cue_candidates)
        auto_candidates = [candidate for candidate in cue_candidates if candidate.severity in allowed_severities]
        remove_candidates = [candidate for candidate in auto_candidates if candidate.action == "remove"]
        compress_candidates = [candidate for candidate in auto_candidates if candidate.action == "compress"]
        report_candidates = [candidate for candidate in cue_candidates if candidate.action in {"report", "keep"}]

        primary: CandidateAction | None = None
        if protected:
            remove_candidates = []
        if remove_candidates:
            primary = remove_candidates[0]
        elif compress_candidates:
            primary = compress_candidates[0]
        elif protected:
            primary = next(candidate for candidate in cue_candidates if candidate.severity == "protected")
        elif report_candidates:
            primary = report_candidates[0]

        output_cue = cue
        if primary is None:
            cleaned_cues.append(cue)
            continue

        secondary_rule_ids = sorted({candidate.rule_id for candidate in cue_candidates if candidate.rule_id != primary.rule_id})
        action = primary.action
        suggested_action = primary.action
        if primary.severity == "protected":
            action = "keep"
            suggested_action = "keep"
        elif mode == "report" and primary.action in {"remove", "compress"}:
            action = primary.action
        elif primary.action == "report":
            action = "report"

        if primary.action == "compress" and primary.after is not None:
            compressed_text = primary.after.strip()
            if compressed_text:
                output_cue = Cue(
                    index=cue.index,
                    start_ms=cue.start_ms,
                    end_ms=cue.end_ms,
                    text=compressed_text,
                    raw_text_lines=[compressed_text],
                    raw_block=cue.raw_block,
                )
            else:
                action = "remove"
                suggested_action = "remove"

        if mode == "clean":
            if action == "remove":
                output_cue = None
            elif action == "compress":
                cleaned_cues.append(output_cue)
            else:
                cleaned_cues.append(cue)
        else:
            cleaned_cues.append(output_cue if action == "compress" else cue)

        decisions.append(
            ResolvedDecision(
                decision_id=f"{decision_counter:06d}",
                cue_index=cue.index,
                start=format_timestamp(cue.start_ms),
                end=format_timestamp(cue.end_ms),
                text_sha256=_text_sha256(cue),
                rule_id=primary.rule_id,
                severity=primary.severity,
                suggested_action=suggested_action,
                action=action,
                reason_zh=primary.reason_zh,
                text=cue.text,
                before=primary.before or cue.text,
                after=primary.after,
                secondary_rule_ids=secondary_rule_ids,
                metadata=primary.metadata.copy(),
            )
        )
        decision_counter += 1

    if mode == "clean":
        cleaned_cues = [cue for cue in cleaned_cues if cue is not None]

    return PipelineResult(cleaned_cues=cleaned_cues, decisions=decisions)
