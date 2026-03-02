"""Tests for the summarizer service."""

from unittest.mock import MagicMock, patch

from services.summarizer import summarize


class TestSummarize:
    @patch("services.summarizer._get_client")
    def test_returns_summary_content(self, mock_get_client):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "# Test Summary\n\nSome content"
        mock_client.complete.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = summarize("Alice: Hello\n\nBob: Hi", "Test Meeting")

        assert result == "# Test Summary\n\nSome content"

    @patch("services.summarizer._get_client")
    def test_passes_correct_messages(self, mock_get_client):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "summary"
        mock_client.complete.return_value = mock_response
        mock_get_client.return_value = mock_client

        summarize("transcript text", "Weekly Standup")

        call_kwargs = mock_client.complete.call_args
        messages = call_kwargs.kwargs["messages"]
        assert len(messages) == 2
        assert "Weekly Standup" in messages[1].content
        assert "transcript text" in messages[1].content

    @patch("services.summarizer._get_client")
    @patch.dict("os.environ", {"MODEL_NAME": "test-model"})
    def test_uses_model_from_env(self, mock_get_client):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "summary"
        mock_client.complete.return_value = mock_response
        mock_get_client.return_value = mock_client

        summarize("text", "title")

        call_kwargs = mock_client.complete.call_args
        assert call_kwargs.kwargs["model"] == "test-model"
