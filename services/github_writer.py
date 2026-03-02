"""Write markdown summary files to GitHub."""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone

from github import Github, GithubException

logger = logging.getLogger(__name__)


def _get_github() -> Github:
    return Github(os.environ["GITHUB_TOKEN"])


def _sanitize_filename(title: str) -> str:
    """Convert a meeting title to a safe filename slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")
    return slug[:80] or "untitled"


def write_summary(
    summary_markdown: str,
    meeting_title: str,
    meeting_date: str | None = None,
) -> str:
    """Write (or update) a markdown file in the target GitHub repo.

    Returns the HTML URL of the created/updated file.
    """
    gh = _get_github()
    repo_name = os.environ["GITHUB_REPO"]
    branch = os.environ.get("GITHUB_BRANCH", "main")
    repo = gh.get_repo(repo_name)

    if meeting_date is None:
        meeting_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    filename = _sanitize_filename(meeting_title)
    path = f"meeting-notes/{meeting_date}/{filename}.md"

    try:
        existing = repo.get_contents(path, ref=branch)
        result = repo.update_file(
            path=path,
            message=f"Update meeting notes: {meeting_title}",
            content=summary_markdown,
            sha=existing.sha,
            branch=branch,
        )
        logger.info("Updated existing file: %s", path)
    except GithubException as exc:
        if exc.status == 404:
            result = repo.create_file(
                path=path,
                message=f"Add meeting notes: {meeting_title}",
                content=summary_markdown,
                branch=branch,
            )
            logger.info("Created new file: %s", path)
        else:
            raise

    return result["content"].html_url
