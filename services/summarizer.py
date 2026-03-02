"""Summarize meeting transcripts via azure-ai-inference."""

from __future__ import annotations

import logging
import os

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

from prompts.system_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_client: ChatCompletionsClient | None = None


def _get_client() -> ChatCompletionsClient:
    """Return a singleton ChatCompletionsClient."""
    global _client
    if _client is None:
        endpoint = os.environ["MODEL_ENDPOINT"]
        api_key = os.environ["MODEL_API_KEY"]
        _client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
        )
    return _client


def summarize(transcript_text: str, meeting_title: str) -> str:
    """Send the transcript to the AI model and return a structured markdown summary."""
    client = _get_client()
    model_name = os.environ.get("MODEL_NAME", "Kimi-K2.5")

    user_content = (
        f"Meeting title: {meeting_title}\n\n"
        f"Transcript:\n{transcript_text}"
    )

    logger.info("Calling model %s for meeting: %s", model_name, meeting_title)

    response = client.complete(
        model=model_name,
        messages=[
            SystemMessage(content=SYSTEM_PROMPT),
            UserMessage(content=user_content),
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    summary = response.choices[0].message.content
    logger.info("Summary generated (%d chars)", len(summary))
    return summary
