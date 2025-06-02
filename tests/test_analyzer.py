"""
Tests for action analyzer functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.analyzer import ActionAnalyzer, AnalysisResult
from src.stride_client import PaymentRequiredError, ForbiddenError


class TestActionAnalyzer:
    """Test the ActionAnalyzer class."""

    @pytest.fixture
    def analyzer(self, mock_github_client, mock_stride_client):
        """Create analyzer with mocked dependencies."""
        return ActionAnalyzer(mock_github_client, mock_stride_client)

    @pytest.mark.asyncio
    async def test_analyze_pr_success(
        self, analyzer, mock_github_client, mock_stride_client
    ):
        """Test successful PR analysis."""
        result = await analyzer.analyze_pr(42)

        assert isinstance(result, AnalysisResult)
        assert result.threat_count == 1
        assert len(result.threats) == 1
        assert result.analysis_id == "ana_test123"
        assert result.is_limited is False

        # Verify GitHub client was called to get PR files
        mock_github_client.get_pr_files.assert_called_once_with(42)

        # Verify STRIDE client was called with correct parameters
        mock_stride_client.analyze.assert_called_once()
        call_args = mock_stride_client.analyze.call_args[0][0]
        assert "repository" in call_args
        assert "github_token" in call_args
        assert "pr_number" in call_args
        assert call_args["pr_number"] == 42

    @pytest.mark.asyncio
    async def test_analyze_pr_private_repo(self, analyzer, mock_github_client):
        """Test PR analysis on private repository."""
        # Configure GitHub client to return private repo
        mock_github_client.is_public_repo.return_value = False

        with pytest.raises(ForbiddenError, match="Private repositories require"):
            await analyzer.analyze_pr(42)

    @pytest.mark.asyncio
    async def test_analyze_pr_no_files(
        self, analyzer, mock_github_client, mock_stride_client
    ):
        """Test PR analysis when no files are found."""
        # Configure GitHub client to return no files
        mock_github_client.get_pr_files.return_value = []

        result = await analyzer.analyze_pr(42)

        assert result.threat_count == 0
        assert len(result.threats) == 0
        assert result.analysis_id == ""

        # Should not call STRIDE API if no files
        mock_stride_client.analyze.assert_not_called()

    @pytest.mark.asyncio
    async def test_analyze_pr_payment_required(
        self, analyzer, mock_github_client, mock_stride_client
    ):
        """Test PR analysis when payment is required."""
        # Configure STRIDE client to raise payment error
        mock_stride_client.analyze.side_effect = PaymentRequiredError("Limit reached")

        result = await analyzer.analyze_pr(42)

        assert result.threat_count == 0
        assert result.is_limited is True
        assert (
            result.upgrade_message
            == "Monthly analysis limit reached. Upgrade to continue analyzing."
        )
        assert result.usage_info["limit_reached"] is True

    @pytest.mark.asyncio
    async def test_analyze_feature_description_success(
        self, analyzer, mock_github_client, mock_stride_client
    ):
        """Test successful feature description analysis."""
        result = await analyzer.analyze_feature_description(42)

        assert isinstance(result, AnalysisResult)
        assert result.threat_count == 1
        assert result.analysis_id == "ana_test123"

        # Verify GitHub client was called to get issue description
        mock_github_client.get_issue_description.assert_called_once_with(42)

        # Verify STRIDE client was called with feature analysis parameters
        mock_stride_client.analyze.assert_called_once()
        call_args = mock_stride_client.analyze.call_args[0][0]
        assert call_args["analysis_type"] == "feature_description"
        assert "feature_description" in call_args["options"]
        assert call_args["options"]["issue_number"] == 42

    @pytest.mark.asyncio
    async def test_analyze_feature_description_empty(
        self, analyzer, mock_github_client, mock_stride_client
    ):
        """Test feature description analysis with empty description."""
        # Configure GitHub client to return empty description
        mock_github_client.get_issue_description.return_value = "   "  # Whitespace only

        result = await analyzer.analyze_feature_description(42)

        assert result.threat_count == 0
        assert len(result.threats) == 0

        # Should not call STRIDE API if description is empty
        mock_stride_client.analyze.assert_not_called()

    @pytest.mark.asyncio
    async def test_analyze_repository_success(
        self, analyzer, mock_github_client, mock_stride_client
    ):
        """Test successful repository analysis."""
        result = await analyzer.analyze_repository()

        assert isinstance(result, AnalysisResult)
        assert result.threat_count == 1
        assert result.analysis_id == "ana_test123"

        # Verify STRIDE client was called with repository analysis parameters
        mock_stride_client.analyze.assert_called_once()
        call_args = mock_stride_client.analyze.call_args[0][0]
        assert call_args["analysis_type"] == "full_repository"
        assert "repository" in call_args
        assert "github_token" in call_args

    @pytest.mark.asyncio
    async def test_repository_url_formatting(
        self, analyzer, mock_github_client, mock_stride_client
    ):
        """Test that repository URLs are properly formatted."""
        # Configure GitHub client with just repo name (not full URL)
        mock_github_client.repo_name = "test/repo"

        await analyzer.analyze_pr(42)

        call_args = mock_stride_client.analyze.call_args[0][0]
        assert call_args["repository"] == "https://github.com/test/repo"

    @pytest.mark.asyncio
    async def test_repository_url_already_formatted(
        self, analyzer, mock_github_client, mock_stride_client
    ):
        """Test that full URLs are passed through unchanged."""
        # Configure GitHub client with full URL
        mock_github_client.repo_name = "https://github.com/test/repo"

        await analyzer.analyze_pr(42)

        call_args = mock_stride_client.analyze.call_args[0][0]
        assert call_args["repository"] == "https://github.com/test/repo"

    @pytest.mark.asyncio
    async def test_analyze_result_processing(
        self, analyzer, mock_github_client, mock_stride_client
    ):
        """Test that analysis results are properly processed."""
        # Configure STRIDE client with truncated results
        mock_stride_client.analyze.return_value = {
            "analysis_id": "ana_test123",
            "status": "completed",
            "threats": [{"id": "t1"}, {"id": "t2"}],
            "summary": {"total": 5},  # More threats than returned
            "truncated": True,
            "upgrade_message": "Upgrade for more threats",
        }

        result = await analyzer.analyze_pr(42)

        assert result.threat_count == 5  # Uses summary total, not threats length
        assert result.is_limited is True
        assert result.upgrade_message == "Upgrade for more threats"

    @pytest.mark.asyncio
    async def test_multiple_analyze_calls_isolation(
        self, analyzer, mock_github_client, mock_stride_client
    ):
        """Test that multiple analysis calls don't interfere with each other."""
        # First call
        result1 = await analyzer.analyze_pr(42)

        # Second call with different PR
        result2 = await analyzer.analyze_pr(43)

        # Both should succeed independently
        assert result1.analysis_id == "ana_test123"
        assert result2.analysis_id == "ana_test123"

        # STRIDE client should have been called twice
        assert mock_stride_client.analyze.call_count == 2

        # Verify different PR numbers were passed
        call_args_1 = mock_stride_client.analyze.call_args_list[0][0][0]
        call_args_2 = mock_stride_client.analyze.call_args_list[1][0][0]
        assert call_args_1["pr_number"] == 42
        assert call_args_2["pr_number"] == 43


class TestAnalysisResult:
    """Test the AnalysisResult dataclass."""

    def test_analysis_result_creation(self):
        """Test creating an AnalysisResult."""
        threats = [{"id": "t1", "title": "Test threat"}]

        result = AnalysisResult(
            threat_count=1,
            threats=threats,
            analysis_id="ana_123",
            usage_info={"plan": "FREE"},
            is_limited=False,
            upgrade_message=None,
        )

        assert result.threat_count == 1
        assert result.threats == threats
        assert result.analysis_id == "ana_123"
        assert result.usage_info["plan"] == "FREE"
        assert result.is_limited is False
        assert result.upgrade_message is None

    def test_analysis_result_defaults(self):
        """Test AnalysisResult default values."""
        result = AnalysisResult(
            threat_count=0, threats=[], analysis_id="", usage_info={}
        )

        # Default values should be set
        assert result.is_limited is False
        assert result.upgrade_message is None

    def test_analysis_result_with_limitations(self):
        """Test AnalysisResult with limitations."""
        result = AnalysisResult(
            threat_count=0,
            threats=[],
            analysis_id="",
            usage_info={"limit_reached": True},
            is_limited=True,
            upgrade_message="Upgrade required",
        )

        assert result.is_limited is True
        assert result.upgrade_message == "Upgrade required"
        assert result.usage_info["limit_reached"] is True
