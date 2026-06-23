from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .models import Cue, ResolvedDecision


def _rule_summary_label(decision: ResolvedDecision) -> str:
    if decision.action == "remove":
        return "removed"
    if decision.action == "compress":
        return "compressed"
    if decision.action == "keep":
        return "kept"
    if decision.severity == "protected":
        return "kept"
    return "review"


def build_report_text(
    *,
    source_path: Path,
    profile_name: str,
    mode: str,
    level: str,
    total_cues: int,
    cleaned_cues: list[Cue],
    decisions: list[ResolvedDecision],
) -> str:
    removed = sum(1 for decision in decisions if decision.action == "remove")
    compressed = sum(1 for decision in decisions if decision.action == "compress")
    protected = sum(1 for decision in decisions if decision.severity == "protected")
    review = sum(1 for decision in decisions if decision.action == "report")
    removed_ratio = (removed / total_cues * 100) if total_cues else 0.0

    rule_summary: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for decision in decisions:
        rule_summary[decision.rule_id][_rule_summary_label(decision)] += 1

    lines = [
        "srt-clean report",
        f"source={source_path.name}",
        f"profile={profile_name}",
        f"mode={mode}",
        f"level={level}",
        "",
        "summary:",
        f"  total_cues={total_cues}",
        f"  output_cues={len(cleaned_cues)}",
        f"  removed_cues={removed}",
        f"  compressed_cues={compressed}",
        f"  protected_cues={protected}",
        f"  review_cues={review}",
        f"  estimated_removed_ratio={removed_ratio:.2f}%",
        "",
        "rule_summary:",
    ]
    if rule_summary:
        for rule_id in sorted(rule_summary):
            parts = " ".join(
                f"{label}={count}" for label, count in sorted(rule_summary[rule_id].items())
            )
            lines.append(f"  {rule_id} {parts}")
    else:
        lines.append("  none")

    for decision in decisions:
        if decision.action == "remove":
            lines.extend(
                [
                    "",
                    "[REMOVE]",
                    f"id={decision.decision_id}",
                    f"cue={decision.cue_index}",
                    f"time={decision.start} --> {decision.end}",
                    f"rule={decision.rule_id}",
                    f"severity={decision.severity}",
                    f"text={decision.text}",
                    f"reason_zh={decision.reason_zh}",
                ]
            )
            if decision.metadata.get("user_override_protected"):
                lines.append("user_override_protected=true")
        elif decision.action == "compress":
            lines.extend(
                [
                    "",
                    "[COMPRESS]",
                    f"id={decision.decision_id}",
                    f"cue={decision.cue_index}",
                    f"time={decision.start} --> {decision.end}",
                    f"rule={decision.rule_id}",
                    f"severity={decision.severity}",
                    f"before={decision.before}",
                    f"after={decision.after}",
                    f"reason_zh={decision.reason_zh}",
                ]
            )
        elif decision.severity == "protected":
            lines.extend(
                [
                    "",
                    "[KEEP-PROTECTED]",
                    f"id={decision.decision_id}",
                    f"cue={decision.cue_index}",
                    f"time={decision.start} --> {decision.end}",
                    f"rule={decision.rule_id}",
                    f"severity={decision.severity}",
                    f"text={decision.text}",
                    f"reason_zh={decision.reason_zh}",
                ]
            )
        elif decision.action == "keep":
            lines.extend(
                [
                    "",
                    "[KEEP]",
                    f"id={decision.decision_id}",
                    f"cue={decision.cue_index}",
                    f"time={decision.start} --> {decision.end}",
                    f"rule={decision.rule_id}",
                    f"severity={decision.severity}",
                    f"text={decision.text}",
                    f"reason_zh={decision.reason_zh}",
                ]
            )
        else:
            lines.extend(
                [
                    "",
                    "[REVIEW]",
                    f"id={decision.decision_id}",
                    f"cue={decision.cue_index}",
                    f"time={decision.start} --> {decision.end}",
                    f"rule={decision.rule_id}",
                    f"severity={decision.severity}",
                    f"text={decision.text}",
                    f"reason_zh={decision.reason_zh}",
                ]
            )

    return "\n".join(lines) + "\n"
