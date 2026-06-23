#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Cue:
    index: str
    timecode: str
    text: str


def parse_srt(text: str) -> list[Cue]:
    blocks = re.split(r"\n\s*\n", text.strip())
    cues: list[Cue] = []
    for block in blocks:
        lines = [line.rstrip("\n") for line in block.splitlines()]
        if len(lines) < 3:
            continue
        cues.append(Cue(index=lines[0], timecode=lines[1], text="\n".join(lines[2:])))
    return cues


def build_prompt(batch: list[Cue]) -> str:
    lines = [
        "/no_think",
        "Translate the following Japanese SRT cue texts into Traditional Chinese.",
        "Rules:",
        "- Output only the translated cue texts.",
        "- Keep the same cue ids in the same order.",
        "- Format each item exactly as <id>TAB<translation>.",
        "- Preserve line breaks inside a cue by writing \\n literally.",
        "- Do not add notes, quotes, markdown, or explanations.",
        "- If a cue contains numbers, filler, or nonsense, keep them naturally in Chinese context.",
        "",
    ]
    for idx, cue in enumerate(batch, start=1):
        text = cue.text.replace("\n", "\\n")
        lines.append(f"{idx}\t{text}")
    return "\n".join(lines)


def run_ollama(model: str, prompt: str) -> str:
    result = subprocess.run(
        ["ollama", "run", model, prompt],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def parse_output(raw: str, expected_count: int) -> list[str]:
    raw = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", raw)
    mapping: dict[int, str] = {}
    current_id: int | None = None
    parts: list[str] = []

    def flush() -> None:
        nonlocal current_id, parts
        if current_id is None:
            return
        mapping[current_id] = "".join(parts).strip().replace("\\n", "\n")
        current_id = None
        parts = []

    for raw_line in raw.splitlines():
        line = raw_line.strip()
        match = re.match(r"^(\d+)\t(.*)$", line)
        if match:
            flush()
            current_id = int(match.group(1))
            parts = [match.group(2)]
            continue
        if current_id is not None and line:
            parts.append(line)
    flush()
    if len(mapping) != expected_count:
        raise ValueError(
            f"Expected {expected_count} translated rows, got {len(mapping)}.\nRaw output:\n{raw}"
        )
    return [mapping[i] for i in range(1, expected_count + 1)]


def translate_batches(cues: list[Cue], model: str, batch_size: int) -> list[Cue]:
    translated: list[Cue] = []
    for start in range(0, len(cues), batch_size):
        batch = cues[start : start + batch_size]
        prompt = build_prompt(batch)
        raw = run_ollama(model, prompt)
        texts = parse_output(raw, len(batch))
        for cue, text in zip(batch, texts, strict=True):
            translated.append(Cue(index=cue.index, timecode=cue.timecode, text=text))
        print(
            f"Translated {start + 1}-{start + len(batch)} / {len(cues)} cues",
            file=sys.stderr,
        )
    return translated


def write_srt(path: Path, cues: list[Cue]) -> None:
    blocks = [f"{cue.index}\n{cue.timecode}\n{cue.text}" for cue in cues]
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", default="gemma2:9b")
    parser.add_argument("--batch-size", type=int, default=12)
    args = parser.parse_args()

    cues = parse_srt(args.input.read_text(encoding="utf-8"))
    translated = translate_batches(cues, args.model, args.batch_size)
    write_srt(args.output, translated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
