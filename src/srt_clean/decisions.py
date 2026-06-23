from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .models import Cue, ResolvedDecision


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
            }
            for decision in decisions
        ],
    }


def write_decisions_file(path: str | Path, document: dict[str, Any]) -> None:
    Path(path).write_text(
        yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
