from __future__ import annotations

from pathlib import Path

from .models import Cue


def format_timestamp(total_ms: int) -> str:
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def cue_text_lines(cue: Cue) -> list[str]:
    original_joined = " ".join(cue.raw_text_lines)
    if cue.raw_text_lines and cue.text == original_joined:
        return cue.raw_text_lines
    if "\n" in cue.text:
        return cue.text.splitlines()
    return [cue.text]


def write_srt_text(cues: list[Cue]) -> str:
    blocks: list[str] = []
    for new_index, cue in enumerate(cues, start=1):
        timecode = f"{format_timestamp(cue.start_ms)} --> {format_timestamp(cue.end_ms)}"
        block_lines = [str(new_index), timecode, *cue_text_lines(cue)]
        blocks.append("\n".join(block_lines))
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def write_srt_file(path: str | Path, cues: list[Cue]) -> None:
    Path(path).write_text(write_srt_text(cues), encoding="utf-8")
