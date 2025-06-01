"""
GitHub Client for STRIDE-GPT Action
"""

from typing import List, Dict, Any, Optional
from github import Github, PullRequest, Repository, Issue


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, token: str, repo_name: str):
        self.token = token
        self.github = Github(token)
        self.repo = self.github.get_repo(repo_name)
        self.repo_name = repo_name

    def get_pr(self, pr_number: int) -> PullRequest.PullRequest:
        """Get a pull request by number."""
        return self.repo.get_pull(pr_number)

    def get_pr_files(self, pr_number: int) -> List[Dict[str, Any]]:
        """Get list of files changed in a PR."""
        pr = self.get_pr(pr_number)
        files = []

        for file in pr.get_files():
            # Only include files we can analyze
            if file.status == "removed":
                continue

            files.append(
                {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch,
                    "contents_url": file.contents_url,
                }
            )

        return files

    def get_file_content(self, path: str, ref: Optional[str] = None) -> str:
        """Get content of a file from the repository."""
        try:
            if ref:
                contents = self.repo.get_contents(path, ref=ref)
            else:
                contents = self.repo.get_contents(path)

            if contents.encoding == "base64":
                import base64

                return base64.b64decode(contents.content).decode("utf-8")
            else:
                return contents.decoded_content.decode("utf-8")
        except Exception:
            return ""

    def create_comment(self, pr_number: int, body: str) -> str:
        """Create a comment on a PR."""
        pr = self.get_pr(pr_number)
        comment = pr.create_issue_comment(body)
        return comment.html_url

    def check_rate_limit(self) -> Dict[str, Any]:
        """Check GitHub API rate limit."""
        rate_limit = self.github.get_rate_limit()
        return {
            "remaining": rate_limit.core.remaining,
            "limit": rate_limit.core.limit,
            "reset": rate_limit.core.reset,
        }

    def is_public_repo(self) -> bool:
        """Check if the repository is public."""
        return not self.repo.private

    def get_issue(self, issue_number: int) -> Issue.Issue:
        """Get an issue by number."""
        return self.repo.get_issue(issue_number)

    def get_issue_description(self, issue_number: int) -> str:
        """Get the description/body of an issue."""
        issue = self.get_issue(issue_number)
        return issue.body or ""

    def create_issue_comment(self, issue_number: int, body: str) -> str:
        """Create a comment on an issue."""
        issue = self.get_issue(issue_number)
        comment = issue.create_comment(body)
        return comment.html_url
