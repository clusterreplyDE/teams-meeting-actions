"""Parse WebVTT transcripts and consolidate consecutive speaker turns."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

import webvtt


@dataclass
class Turn:
    """A single consolidated speaker turn."""

    speaker: str
    text: str


def parse_vtt(vtt_content: str) -> list[Turn]:
    """Parse a WebVTT string into consolidated speaker turns.

    Consecutive captions from the same speaker are merged into one turn.
    Speaker names are extracted from the ``<v name>`` tag that Teams uses.
    """
    buffer = io.StringIO(vtt_content)
    captions = webvtt.read_buffer(buffer)

    raw_turns: list[tuple[str, str]] = []
    for caption in captions:
        speaker, text = _extract_speaker(caption.raw_text)
        raw_turns.append((speaker, text))

    return _consolidate(raw_turns)


# Teams WebVTT uses  <v Speaker Name>text</v>  or just plain text
_SPEAKER_RE = re.compile(r"<v\s+([^>]+)>(.+?)(?:</v>)?$", re.DOTALL)


def _extract_speaker(raw_text: str) -> tuple[str, str]:
    """Return (speaker, text) from a caption line."""
    match = _SPEAKER_RE.search(raw_text.strip())
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return "Unknown", raw_text.strip()


def _consolidate(turns: list[tuple[str, str]]) -> list[Turn]:
    """Merge consecutive entries from the same speaker."""
    if not turns:
        return []

    consolidated: list[Turn] = []
    current_speaker, current_text = turns[0]

    for speaker, text in turns[1:]:
        if speaker == current_speaker:
            current_text += " " + text
        else:
            consolidated.append(Turn(speaker=current_speaker, text=current_text))
            current_speaker = speaker
            current_text = text

    consolidated.append(Turn(speaker=current_speaker, text=current_text))
    return consolidated


def turns_to_text(turns: list[Turn]) -> str:
    """Format consolidated turns as a readable transcript string."""
    lines = [f"{t.speaker}: {t.text}" for t in turns]
    return "\n\n".join(lines)
