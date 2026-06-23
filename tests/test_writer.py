from __future__ import annotations

from pathlib import Path

from srt_clean.parser import parse_srt_file
from srt_clean.writer import write_srt_text

FIXTURES = Path(__file__).parent / "fixtures"


def test_writer_renumbers_cues_from_one() -> None:
    cues = parse_srt_file(FIXTURES / "non_contiguous.input.srt")

    output = write_srt_text(cues)

    assert output.startswith("1\n00:00:05,000 --> 00:00:06,000\nfirst")
    assert "\n\n2\n00:00:06,500 --> 00:00:08,000\nsecond\n" in output


def test_writer_preserves_timecodes_and_multiline_text() -> None:
    cues = parse_srt_file(FIXTURES / "basic_multiline.input.srt")

    output = write_srt_text(cues)

    assert "00:00:01,000 --> 00:00:02,500" in output
    assert "Hello\nworld" in output
