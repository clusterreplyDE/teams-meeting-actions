"""Tests for the Azure Function HTTP trigger."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import azure.functions as func

from function_app import summarize_transcript

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _make_request(body: dict | str | None = None) -> func.HttpRequest:
    """Create a mock HttpRequest."""
    if isinstance(body, dict):
        body_bytes = json.dumps(body).encode()
    elif isinstance(body, str):
        body_bytes = body.encode()
    else:
        body_bytes = b""

    return func.HttpRequest(
        method="POST",
        url="/api/summarize",
        body=body_bytes,
        headers={"Content-Type": "application/json"},
    )


class TestSummarizeTranscript:
    def test_rejects_invalid_json(self):
        req = _make_request("not json")
        resp = summarize_transcript(req)
        assert resp.status_code == 400
        assert "Invalid JSON" in resp.get_body().decode()

    def test_rejects_missing_fields(self):
        req = _make_request({"transcript": "WEBVTT\n\n"})
        resp = summarize_transcript(req)
        assert resp.status_code == 422
        assert "Validation failed" in resp.get_body().decode()

    def test_rejects_empty_transcript_field(self):
        req = _make_request({"transcript": "", "meeting_title": "Test"})
        resp = summarize_transcript(req)
        assert resp.status_code == 422

    @patch("function_app.write_summary")
    @patch("function_app.summarize")
    def test_successful_flow(self, mock_summarize, mock_write):
        vtt = (FIXTURES_DIR / "sample_transcript.vtt").read_text(encoding="utf-8")
        mock_summarize.return_value = "# Summary\n\nContent"
        mock_write.return_value = "https://github.com/owner/repo/blob/main/notes.md"

        req = _make_request({
            "transcript": vtt,
            "meeting_title": "Sprint Review",
            "meeting_date": "2024-01-15",
        })
        resp = summarize_transcript(req)

        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert body["status"] == "success"
        assert "github.com" in body["file_url"]
        assert "Alice Johnson" in body["speakers"]

    @patch("function_app.write_summary")
    @patch("function_app.summarize")
    def test_deduplicates_speakers(self, mock_summarize, mock_write):
        vtt = (FIXTURES_DIR / "sample_transcript.vtt").read_text(encoding="utf-8")
        mock_summarize.return_value = "# Summary"
        mock_write.return_value = "https://github.com/example"

        req = _make_request({
            "transcript": vtt,
            "meeting_title": "Test",
        })
        resp = summarize_transcript(req)

        body = json.loads(resp.get_body())
        # Speakers should be unique
        assert len(body["speakers"]) == len(set(body["speakers"]))

    @patch("function_app.summarize", side_effect=Exception("API error"))
    def test_handles_summarization_error(self, mock_summarize):
        vtt = (FIXTURES_DIR / "sample_transcript.vtt").read_text(encoding="utf-8")
        req = _make_request({
            "transcript": vtt,
            "meeting_title": "Test",
        })
        resp = summarize_transcript(req)
        assert resp.status_code == 502
        assert "Summarization failed" in resp.get_body().decode()

    @patch("function_app.summarize", return_value="# Summary")
    @patch("function_app.write_summary", side_effect=Exception("GitHub error"))
    def test_handles_github_error(self, mock_write, mock_summarize):
        vtt = (FIXTURES_DIR / "sample_transcript.vtt").read_text(encoding="utf-8")
        req = _make_request({
            "transcript": vtt,
            "meeting_title": "Test",
        })
        resp = summarize_transcript(req)
        assert resp.status_code == 502
        assert "GitHub write failed" in resp.get_body().decode()
