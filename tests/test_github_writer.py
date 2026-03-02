"""Tests for the GitHub writer service."""

from unittest.mock import MagicMock, patch

import pytest
from github import GithubException

from services.github_writer import _sanitize_filename, write_summary


class TestSanitizeFilename:
    def test_basic_title(self):
        assert _sanitize_filename("Sprint Review") == "sprint-review"

    def test_special_characters(self):
        assert _sanitize_filename("Q2 Planning (Draft)") == "q2-planning-draft"

    def test_excessive_whitespace(self):
        assert _sanitize_filename("  Too   Many   Spaces  ") == "too-many-spaces"

    def test_empty_string(self):
        assert _sanitize_filename("") == "untitled"

    def test_only_special_chars(self):
        assert _sanitize_filename("!!!") == "untitled"

    def test_long_title_truncated(self):
        long_title = "A" * 200
        assert len(_sanitize_filename(long_title)) <= 80


class TestWriteSummary:
    @patch("services.github_writer._get_github")
    @patch.dict(
        "os.environ",
        {"GITHUB_TOKEN": "fake", "GITHUB_REPO": "owner/repo", "GITHUB_BRANCH": "main"},
    )
    def test_creates_new_file(self, mock_get_github):
        mock_gh = MagicMock()
        mock_repo = MagicMock()
        mock_get_github.return_value = mock_gh
        mock_gh.get_repo.return_value = mock_repo

        # Simulate 404 (file doesn't exist)
        mock_repo.get_contents.side_effect = GithubException(404, {}, {})
        mock_result_content = MagicMock()
        mock_result_content.html_url = "https://github.com/owner/repo/blob/main/meeting-notes/2024-01-15/test.md"
        mock_repo.create_file.return_value = {"content": mock_result_content}

        url = write_summary("# Summary", "Test Meeting", "2024-01-15")

        assert "github.com" in url
        mock_repo.create_file.assert_called_once()

    @patch("services.github_writer._get_github")
    @patch.dict(
        "os.environ",
        {"GITHUB_TOKEN": "fake", "GITHUB_REPO": "owner/repo", "GITHUB_BRANCH": "main"},
    )
    def test_updates_existing_file(self, mock_get_github):
        mock_gh = MagicMock()
        mock_repo = MagicMock()
        mock_get_github.return_value = mock_gh
        mock_gh.get_repo.return_value = mock_repo

        # Simulate existing file
        mock_existing = MagicMock()
        mock_existing.sha = "abc123"
        mock_repo.get_contents.return_value = mock_existing
        mock_result_content = MagicMock()
        mock_result_content.html_url = "https://github.com/owner/repo/blob/main/meeting-notes/2024-01-15/test.md"
        mock_repo.update_file.return_value = {"content": mock_result_content}

        url = write_summary("# Updated Summary", "Test Meeting", "2024-01-15")

        assert "github.com" in url
        mock_repo.update_file.assert_called_once()

    @patch("services.github_writer._get_github")
    @patch.dict(
        "os.environ",
        {"GITHUB_TOKEN": "fake", "GITHUB_REPO": "owner/repo", "GITHUB_BRANCH": "main"},
    )
    def test_raises_on_non_404_error(self, mock_get_github):
        mock_gh = MagicMock()
        mock_repo = MagicMock()
        mock_get_github.return_value = mock_gh
        mock_gh.get_repo.return_value = mock_repo

        mock_repo.get_contents.side_effect = GithubException(500, {}, {})

        with pytest.raises(GithubException):
            write_summary("# Summary", "Test", "2024-01-15")
