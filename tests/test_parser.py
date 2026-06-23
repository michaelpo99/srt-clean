from __future__ import annotations

from pathlib import Path

import pytest

from srt_clean.models import SRTParseError
from srt_clean.parser import parse_srt_file, parse_srt_text

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_basic_and_multiline_srt() -> None:
    cues = parse_srt_file(FIXTURES / "basic_multiline.input.srt")

    assert len(cues) == 2
    assert cues[0].index == 1
    assert cues[0].text == "Hello world"
    assert cues[0].raw_text_lines == ["Hello", "world"]
    assert cues[1].text == "痛い"


def test_parse_utf8_bom_and_crlf() -> None:
    text = "\ufeff1\r\n00:00:01,000 --> 00:00:02,000\r\nAh\r\n\r\n"

    cues = parse_srt_text(text)

    assert len(cues) == 1
    assert cues[0].text == "Ah"


def test_parse_non_contiguous_indexes() -> None:
    cues = parse_srt_file(FIXTURES / "non_contiguous.input.srt")

    assert [cue.index for cue in cues] == [5, 9]


def test_parse_invalid_timecode_reports_line_number() -> None:
    with pytest.raises(SRTParseError) as excinfo:
        parse_srt_file(FIXTURES / "malformed_timecode.input.srt")

    assert "line 2" in str(excinfo.value)
    assert "invalid timecode" in str(excinfo.value)


def test_parse_zero_duration_cue_is_rejected() -> None:
    text = "1\n00:00:01,000 --> 00:00:01,000\nzero\n"

    with pytest.raises(SRTParseError) as excinfo:
        parse_srt_text(text)

    assert "line 2" in str(excinfo.value)
    assert "later than start time" in str(excinfo.value)
