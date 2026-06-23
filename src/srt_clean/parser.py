from __future__ import annotations

import re
from pathlib import Path

from .models import Cue, SRTParseError

TIMECODE_RE = re.compile(
    r"^(?P<start_h>\d{2}):(?P<start_m>\d{2}):(?P<start_s>\d{2}),(?P<start_ms>\d{3})"
    r" --> "
    r"(?P<end_h>\d{2}):(?P<end_m>\d{2}):(?P<end_s>\d{2}),(?P<end_ms>\d{3})$"
)


def parse_timestamp(value: str, *, line_number: int | None = None) -> int:
    match = TIMECODE_RE.match(value)
    if not match:
        raise SRTParseError("invalid timecode", line_number=line_number)
    parts = {key: int(number) for key, number in match.groupdict().items()}
    start_ms = (
        ((parts["start_h"] * 60 + parts["start_m"]) * 60 + parts["start_s"]) * 1000
        + parts["start_ms"]
    )
    end_ms = (
        ((parts["end_h"] * 60 + parts["end_m"]) * 60 + parts["end_s"]) * 1000 + parts["end_ms"]
    )
    if end_ms < start_ms:
        raise SRTParseError("end time is earlier than start time", line_number=line_number)
    return start_ms, end_ms


def parse_srt_text(text: str) -> list[Cue]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if normalized.startswith("\ufeff"):
        normalized = normalized.removeprefix("\ufeff")
    lines = normalized.split("\n")
    cues: list[Cue] = []
    i = 0

    while i < len(lines):
        if lines[i].strip() == "":
            i += 1
            continue

        index_line_number = i + 1
        index_line = lines[i].strip()
        if not index_line.isdigit():
            raise SRTParseError("expected cue index", line_number=index_line_number)

        i += 1
        if i >= len(lines):
            raise SRTParseError("missing timecode line", line_number=index_line_number + 1)

        timecode_line_number = i + 1
        timecode_line = lines[i].strip()
        start_ms, end_ms = parse_timestamp(timecode_line, line_number=timecode_line_number)
        i += 1

        text_lines: list[str] = []
        while i < len(lines) and lines[i].strip() != "":
            text_lines.append(lines[i])
            i += 1

        raw_block_lines = [index_line, timecode_line, *text_lines]
        cue = Cue(
            index=int(index_line),
            start_ms=start_ms,
            end_ms=end_ms,
            text=" ".join(text_lines),
            raw_text_lines=text_lines.copy(),
            raw_block="\n".join(raw_block_lines),
        )
        cues.append(cue)

    return cues


def parse_srt_file(path: str | Path) -> list[Cue]:
    return parse_srt_text(Path(path).read_text(encoding="utf-8-sig"))
