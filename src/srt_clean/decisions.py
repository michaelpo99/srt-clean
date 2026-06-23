from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .models import Cue, DecisionsConflictError, LoadedDecision, PipelineResult, ResolvedDecision
from .writer import format_timestamp


def compute_source_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compute_text_sha256(cue: Cue) -> str:
    text_for_hash = "\n".join(cue.raw_text_lines)
    return hashlib.sha256(text_for_hash.encode("utf-8")).hexdigest()


def build_decisions_document(
    *,
    input_path: Path,
    profile_name: str,
    decisions: list[ResolvedDecision],
) -> dict[str, Any]:
    return {
        "version": 1,
        "source": input_path.name,
        "source_sha256": compute_source_sha256(input_path),
        "profile": profile_name,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "decisions": [
            {
                "id": decision.decision_id,
                "cue": decision.cue_index,
                "start": decision.start,
                "end": decision.end,
                "text_sha256": decision.text_sha256,
                "rule": decision.rule_id,
                "severity": decision.severity,
                "suggested_action": decision.suggested_action,
                "action": decision.action,
                "reason_zh": decision.reason_zh,
                "text": decision.text,
                "before": decision.before,
                "after": decision.after,
            }
            for decision in decisions
        ],
    }


def write_decisions_file(path: str | Path, document: dict[str, Any]) -> None:
    Path(path).write_text(
        yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _ensure_mapping(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DecisionsConflictError(f"{label} must be a mapping")
    return value


def _ensure_str(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise DecisionsConflictError(f"{label} must be a non-empty string")
    return value


def _ensure_optional_str(value: Any, *, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise DecisionsConflictError(f"{label} must be a string")
    return value


def _ensure_int(value: Any, *, label: str) -> int:
    if not isinstance(value, int):
        raise DecisionsConflictError(f"{label} must be an integer")
    return value


def load_decisions_file(path: str | Path) -> dict[str, Any]:
    document_path = Path(path)
    if not document_path.exists():
        raise DecisionsConflictError(f"decisions file not found: {document_path}")
    try:
        data = yaml.safe_load(document_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise DecisionsConflictError(f"invalid decisions YAML: {exc}") from exc

    root = _ensure_mapping(data, label="decisions document")
    for required in ("version", "source", "source_sha256", "decisions"):
        if required not in root:
            raise DecisionsConflictError(f"decisions document missing required field: {required}")
    if root["version"] != 1:
        raise DecisionsConflictError(f"unsupported decisions version: {root['version']}")
    _ensure_str(root["source"], label="source")
    _ensure_str(root["source_sha256"], label="source_sha256")
    if "profile" in root and root["profile"] is not None:
        _ensure_str(root["profile"], label="profile")
    if not isinstance(root["decisions"], list):
        raise DecisionsConflictError("decisions must be a list")
    return root


def parse_loaded_decisions(document: dict[str, Any]) -> list[LoadedDecision]:
    loaded: list[LoadedDecision] = []
    seen_cues: set[int] = set()
    for index, item in enumerate(document["decisions"], start=1):
        row = _ensure_mapping(item, label=f"decision {index}")
        for required in (
            "id",
            "cue",
            "start",
            "end",
            "text_sha256",
            "rule",
            "severity",
            "suggested_action",
            "action",
            "reason_zh",
        ):
            if required not in row:
                raise DecisionsConflictError(f"decision {index} missing required field: {required}")

        action = _ensure_str(row["action"], label=f"decision {index}.action")
        if action not in {"remove", "keep", "compress", "report"}:
            raise DecisionsConflictError(f"decision {index}.action is invalid: {action}")
        after = _ensure_optional_str(row.get("after"), label=f"decision {index}.after")
        if action == "compress" and not after:
            raise DecisionsConflictError(f"decision {index}.after is required for compress")
        cue_index = _ensure_int(row["cue"], label=f"decision {index}.cue")
        if cue_index in seen_cues:
            raise DecisionsConflictError(f"duplicate decision for cue: {cue_index}")
        seen_cues.add(cue_index)
        loaded.append(
            LoadedDecision(
                decision_id=_ensure_str(row["id"], label=f"decision {index}.id"),
                cue_index=cue_index,
                start=_ensure_str(row["start"], label=f"decision {index}.start"),
                end=_ensure_str(row["end"], label=f"decision {index}.end"),
                text_sha256=_ensure_str(
                    row["text_sha256"], label=f"decision {index}.text_sha256"
                ),
                rule_id=_ensure_str(row["rule"], label=f"decision {index}.rule"),
                severity=_ensure_str(row["severity"], label=f"decision {index}.severity"),
                suggested_action=_ensure_str(
                    row["suggested_action"], label=f"decision {index}.suggested_action"
                ),
                action=action,
                reason_zh=_ensure_str(row["reason_zh"], label=f"decision {index}.reason_zh"),
                text=_ensure_optional_str(row.get("text"), label=f"decision {index}.text"),
                before=_ensure_optional_str(row.get("before"), label=f"decision {index}.before"),
                after=after,
            )
        )
    return loaded


def validate_source_hash(input_path: str | Path, document: dict[str, Any]) -> None:
    actual = compute_source_sha256(input_path)
    if actual != document["source_sha256"]:
        raise DecisionsConflictError("source_sha256 mismatch for decisions file")


def apply_loaded_decisions(
    *,
    cues: list[Cue],
    decisions: list[LoadedDecision],
) -> PipelineResult:
    cue_map = {cue.index: cue for cue in cues}
    result_cues: list[Cue] = []
    resolved: list[ResolvedDecision] = []
    decisions_by_cue = {decision.cue_index: decision for decision in decisions}

    for decision in decisions:
        cue = cue_map.get(decision.cue_index)
        if cue is None:
            raise DecisionsConflictError(f"decision cue not found: {decision.cue_index}")
        if format_timestamp(cue.start_ms) != decision.start or format_timestamp(cue.end_ms) != decision.end:
            raise DecisionsConflictError(f"cue identity mismatch for decision {decision.decision_id}")
        if compute_text_sha256(cue) != decision.text_sha256:
            raise DecisionsConflictError(f"text_sha256 mismatch for decision {decision.decision_id}")

    for cue in cues:
        decision = decisions_by_cue.get(cue.index)
        if decision is None:
            result_cues.append(cue)
            continue

        output_cue = cue
        metadata: dict[str, Any] = {}
        if decision.action == "remove":
            if decision.severity == "protected" and decision.suggested_action == "keep":
                metadata["user_override_protected"] = True
            output_cue = None
        elif decision.action == "compress":
            compressed_text = (decision.after or "").strip()
            if not compressed_text:
                raise DecisionsConflictError(
                    f"compress decision produced empty text for decision {decision.decision_id}"
                )
            output_cue = Cue(
                index=cue.index,
                start_ms=cue.start_ms,
                end_ms=cue.end_ms,
                text=compressed_text,
                raw_text_lines=[compressed_text],
                raw_block=cue.raw_block,
            )

        if output_cue is not None:
            result_cues.append(output_cue)

        resolved.append(
            ResolvedDecision(
                decision_id=decision.decision_id,
                cue_index=decision.cue_index,
                start=decision.start,
                end=decision.end,
                text_sha256=decision.text_sha256,
                rule_id=decision.rule_id,
                severity=decision.severity,
                suggested_action=decision.suggested_action,
                action=decision.action,
                reason_zh=decision.reason_zh,
                text=cue.text,
                before=decision.before or cue.text,
                after=decision.after,
                metadata=metadata,
            )
        )

    return PipelineResult(cleaned_cues=result_cues, decisions=resolved)
