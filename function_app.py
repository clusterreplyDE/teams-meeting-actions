"""Azure Function HTTP trigger for Teams transcript summarization."""

from __future__ import annotations

import json
import logging

import azure.functions as func
from pydantic import ValidationError

from models.request_models import SummarizeRequest
from services.github_writer import write_summary
from services.summarizer import summarize
from services.transcript_parser import parse_vtt, turns_to_text

app = func.FunctionApp()

logger = logging.getLogger(__name__)


@app.function_name(name="SummarizeTranscript")
@app.route(route="summarize", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def summarize_transcript(req: func.HttpRequest) -> func.HttpResponse:
    """Receive a Teams transcript, summarize it, and write to GitHub."""
    logger.info("SummarizeTranscript triggered")

    # Parse and validate request body
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        request = SummarizeRequest(**body)
    except ValidationError as exc:
        return func.HttpResponse(
            json.dumps({"error": "Validation failed", "details": exc.errors()}),
            status_code=422,
            mimetype="application/json",
        )

    # Parse WebVTT transcript
    try:
        turns = parse_vtt(request.transcript)
        transcript_text = turns_to_text(turns)
    except Exception as exc:
        logger.exception("Failed to parse transcript")
        return func.HttpResponse(
            json.dumps({"error": f"Transcript parsing failed: {exc}"}),
            status_code=400,
            mimetype="application/json",
        )

    if not turns:
        return func.HttpResponse(
            json.dumps({"error": "Transcript contains no content"}),
            status_code=400,
            mimetype="application/json",
        )

    # Summarize via Kimi-K2.5
    try:
        summary = summarize(transcript_text, request.meeting_title)
    except Exception as exc:
        logger.exception("Summarization failed")
        return func.HttpResponse(
            json.dumps({"error": f"Summarization failed: {exc}"}),
            status_code=502,
            mimetype="application/json",
        )

    # Write to GitHub
    try:
        file_url = write_summary(
            summary_markdown=summary,
            meeting_title=request.meeting_title,
            meeting_date=request.meeting_date,
        )
    except Exception as exc:
        logger.exception("GitHub write failed")
        return func.HttpResponse(
            json.dumps({"error": f"GitHub write failed: {exc}"}),
            status_code=502,
            mimetype="application/json",
        )

    result = {
        "status": "success",
        "file_url": file_url,
        "meeting_title": request.meeting_title,
        "speakers": [t.speaker for t in turns],
    }
    # Deduplicate speakers list while preserving order
    seen = set()
    unique_speakers = []
    for s in result["speakers"]:
        if s not in seen:
            seen.add(s)
            unique_speakers.append(s)
    result["speakers"] = unique_speakers

    logger.info("Summary written to: %s", file_url)

    return func.HttpResponse(
        json.dumps(result),
        status_code=200,
        mimetype="application/json",
    )
