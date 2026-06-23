from __future__ import annotations

import hashlib
from pathlib import Path

from srt_clean.decisions import build_decisions_document, compute_source_sha256, compute_text_sha256
from srt_clean.models import Cue, ResolvedDecision


def test_source_sha256_uses_exact_input_bytes(tmp_path: Path) -> None:
    path = tmp_path / "sample.srt"
    raw_bytes = b"\xef\xbb\xbf1\r\n00:00:01,000 --> 00:00:02,000\r\nah\r\n"
    path.write_bytes(raw_bytes)

    assert compute_source_sha256(path) == hashlib.sha256(raw_bytes).hexdigest()


def test_text_sha256_uses_raw_text_lines_joined_with_newline() -> None:
    cue = Cue(
        index=1,
        start_ms=1000,
        end_ms=2000,
        text="Hello world",
        raw_text_lines=["Hello", "world"],
        raw_block="",
    )

    assert compute_text_sha256(cue) == hashlib.sha256(b"Hello\nworld").hexdigest()


def test_build_decisions_document_contains_expected_fields(tmp_path: Path) -> None:
    input_path = tmp_path / "input.srt"
    input_path.write_text("1\n00:00:01,000 --> 00:00:02,000\n痛い\n", encoding="utf-8")
    decisions = [
        ResolvedDecision(
            decision_id="000001",
            cue_index=1,
            start="00:00:01,000",
            end="00:00:02,000",
            text_sha256="abc",
            rule_id="protected_semantic_short_phrase",
            severity="protected",
            suggested_action="keep",
            action="keep",
            reason_zh="可能有語意，不自動刪除",
            text="痛い",
        )
    ]

    document = build_decisions_document(
        input_path=input_path,
        profile_name="jp-adult-soft",
        decisions=decisions,
    )

    assert document["version"] == 1
    assert document["source"] == "input.srt"
    assert document["profile"] == "jp-adult-soft"
    assert document["decisions"][0]["cue"] == 1
    assert document["decisions"][0]["action"] == "keep"
