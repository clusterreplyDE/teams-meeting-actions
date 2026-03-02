"""Tests for the WebVTT transcript parser."""

from pathlib import Path

from services.transcript_parser import Turn, parse_vtt, turns_to_text

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


class TestParseVtt:
    def test_parses_sample_transcript(self):
        vtt = _load_fixture("sample_transcript.vtt")
        turns = parse_vtt(vtt)
        assert len(turns) > 0
        assert all(isinstance(t, Turn) for t in turns)

    def test_consolidates_consecutive_speakers(self):
        vtt = _load_fixture("sample_transcript.vtt")
        turns = parse_vtt(vtt)
        # Alice speaks lines 1-2 consecutively → should be merged
        assert turns[0].speaker == "Alice Johnson"
        assert "sprint review" in turns[0].text
        assert "three main topics" in turns[0].text

    def test_bob_consecutive_lines_merged(self):
        vtt = _load_fixture("sample_transcript.vtt")
        turns = parse_vtt(vtt)
        # Bob speaks lines 3-4 consecutively
        assert turns[1].speaker == "Bob Smith"
        assert "authentication endpoints" in turns[1].text
        assert "reporting endpoints" in turns[1].text

    def test_extracts_all_speakers(self):
        vtt = _load_fixture("sample_transcript.vtt")
        turns = parse_vtt(vtt)
        speakers = {t.speaker for t in turns}
        assert speakers == {"Alice Johnson", "Bob Smith", "Carol Davis"}

    def test_handles_minimal_vtt(self):
        vtt = "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\n<v Speaker>Hello</v>\n"
        turns = parse_vtt(vtt)
        assert len(turns) == 1
        assert turns[0].speaker == "Speaker"
        assert turns[0].text == "Hello"

    def test_handles_plain_text_without_speaker_tag(self):
        vtt = "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nPlain text line\n"
        turns = parse_vtt(vtt)
        assert len(turns) == 1
        assert turns[0].speaker == "Unknown"
        assert turns[0].text == "Plain text line"

    def test_empty_transcript_returns_empty(self):
        vtt = "WEBVTT\n\n"
        turns = parse_vtt(vtt)
        assert turns == []


class TestTurnsToText:
    def test_formats_turns(self):
        turns = [
            Turn(speaker="Alice", text="Hello"),
            Turn(speaker="Bob", text="Hi there"),
        ]
        result = turns_to_text(turns)
        assert result == "Alice: Hello\n\nBob: Hi there"

    def test_empty_turns(self):
        assert turns_to_text([]) == ""
