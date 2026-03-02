"""Pydantic models for incoming HTTP requests."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    """Request body for the summarize endpoint."""

    transcript: str = Field(
        ...,
        min_length=1,
        description="WebVTT transcript content from Teams meeting.",
    )
    meeting_title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Title of the meeting.",
    )
    meeting_date: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Meeting date in YYYY-MM-DD format. Defaults to today (UTC).",
    )
