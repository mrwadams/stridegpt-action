"""
Action Analyzer - Coordinates analysis between GitHub and STRIDE API
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .github_client import GitHubClient
from .stride_client import StrideClient, PaymentRequiredError, ForbiddenError


@dataclass
class AnalysisResult:
    """Result from STRIDE analysis."""

    threat_count: int
    threats: List[Dict[str, Any]]
    analysis_id: str
    usage_info: Dict[str, Any]
    is_limited: bool = False
    upgrade_message: Optional[str] = None
    limitation_notice: Optional[str] = None


class ActionAnalyzer:
    """Coordinates analysis between GitHub and STRIDE API."""

    def __init__(self, github_client: GitHubClient, stride_client: StrideClient):
        self.github = github_client
        self.stride = stride_client

    async def analyze_pr(self, pr_number: int) -> AnalysisResult:
        """Analyze a pull request for security threats."""

        # Check if repo is public (free tier only supports public repos)
        if not self.github.is_public_repo():
            raise ForbiddenError(
                "Private repositories require a paid STRIDE-GPT plan. "
                "Visit https://stridegpt.ai/pricing to upgrade."
            )

        # Get PR information
        files = self.github.get_pr_files(pr_number)

        if not files:
            return AnalysisResult(
                threat_count=0,
                threats=[],
                analysis_id="",
                usage_info={},
                is_limited=False,
                limitation_notice=None,
            )

        # Prepare analysis request matching API model
        # Convert repo name to full GitHub URL if needed
        repository_url = self.github.repo_name
        if not repository_url.startswith("https://"):
            repository_url = f"https://github.com/{repository_url}"

        analysis_request = {
            "repository": repository_url,
            "github_token": self.github.token,  # Pass token for API access
            "pr_number": pr_number,
        }

        try:
            # Submit to STRIDE API
            result = await self.stride.analyze(analysis_request)

            # Process results using new API response format
            threats = result.get("threats", [])
            summary = result.get("summary", {})

            # Check if results were truncated by the API
            is_limited = result.get("truncated", False)
            upgrade_message = result.get("upgrade_message")
            limitation_notice = result.get("limitation_notice")

            return AnalysisResult(
                threat_count=summary.get("total", len(threats)),
                threats=threats,
                analysis_id=result.get("analysis_id", ""),
                usage_info=result.get("metadata", {}),
                is_limited=is_limited,
                upgrade_message=upgrade_message,
                limitation_notice=limitation_notice,
            )

        except PaymentRequiredError:
            # Return a special result indicating limit reached
            return AnalysisResult(
                threat_count=0,
                threats=[],
                analysis_id="",
                usage_info={"limit_reached": True},
                is_limited=True,
                upgrade_message="Monthly analysis limit reached. Upgrade to continue analyzing.",
                limitation_notice=None,
            )

    async def analyze_feature_description(self, issue_number: int) -> AnalysisResult:
        """Analyze a proposed feature description for security threats."""

        # Check if repo is public (free tier only supports public repos)
        if not self.github.is_public_repo():
            raise ForbiddenError(
                "Private repositories require a paid STRIDE-GPT plan. "
                "Visit https://stridegpt.ai/pricing to upgrade."
            )

        # Get issue description
        feature_description = self.github.get_issue_description(issue_number)

        if not feature_description.strip():
            return AnalysisResult(
                threat_count=0,
                threats=[],
                analysis_id="",
                usage_info={},
                is_limited=False,
                limitation_notice=None,
            )

        # Prepare analysis request for feature description
        repository_url = self.github.repo_name
        if not repository_url.startswith("https://"):
            repository_url = f"https://github.com/{repository_url}"

        analysis_request = {
            "repository": repository_url,
            "github_token": self.github.token,
            "analysis_type": "feature_description",
            "options": {
                "feature_description": feature_description,
                "issue_number": issue_number,
            },
        }

        try:
            # Send to STRIDE API for conceptual threat modeling
            result = await self.stride.analyze(analysis_request)

            # Process results using new API response format
            threats = result.get("threats", [])
            summary = result.get("summary", {})

            # Check if results were truncated by the API
            is_limited = result.get("truncated", False)
            upgrade_message = result.get("upgrade_message")
            limitation_notice = result.get("limitation_notice")

            return AnalysisResult(
                threat_count=summary.get("total", len(threats)),
                threats=threats,
                analysis_id=result.get("analysis_id", ""),
                usage_info=result.get("metadata", {}),
                is_limited=is_limited,
                upgrade_message=upgrade_message,
                limitation_notice=limitation_notice,
            )

        except PaymentRequiredError:
            # Return a special result indicating limit reached
            return AnalysisResult(
                threat_count=0,
                threats=[],
                analysis_id="",
                usage_info={"limit_reached": True},
                is_limited=True,
                upgrade_message="Monthly analysis limit reached. Upgrade to continue analyzing.",
                limitation_notice=None,
            )

    async def analyze_repository(self) -> AnalysisResult:
        """Analyze the entire repository for security threats."""

        # Check if repo is public (free tier only supports public repos)
        if not self.github.is_public_repo():
            raise ForbiddenError(
                "Private repositories require a paid STRIDE-GPT plan. "
                "Visit https://stridegpt.ai/pricing to upgrade."
            )

        # Prepare analysis request for full repository
        repository_url = self.github.repo_name
        if not repository_url.startswith("https://"):
            repository_url = f"https://github.com/{repository_url}"

        analysis_request = {
            "repository": repository_url,
            "github_token": self.github.token,  # Pass token for API access
            "analysis_type": "full_repository",
        }

        try:
            # Submit to STRIDE API
            result = await self.stride.analyze(analysis_request)

            # Process results using new API response format
            threats = result.get("threats", [])
            summary = result.get("summary", {})

            # Check if results were truncated by the API
            is_limited = result.get("truncated", False)
            upgrade_message = result.get("upgrade_message")
            limitation_notice = result.get("limitation_notice")

            return AnalysisResult(
                threat_count=summary.get("total", len(threats)),
                threats=threats,
                analysis_id=result.get("analysis_id", ""),
                usage_info=result.get("metadata", {}),
                is_limited=is_limited,
                upgrade_message=upgrade_message,
                limitation_notice=limitation_notice,
            )

        except PaymentRequiredError:
            # Return a special result indicating limit reached
            return AnalysisResult(
                threat_count=0,
                threats=[],
                analysis_id="",
                usage_info={"limit_reached": True},
                is_limited=True,
                upgrade_message="Monthly analysis limit reached. Upgrade to continue analyzing.",
                limitation_notice=None,
            )