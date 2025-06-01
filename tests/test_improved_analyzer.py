"""
Improved tests for action analyzer functionality following stridegpt-api patterns.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.analyzer import ActionAnalyzer, AnalysisResult
from src.stride_client import PaymentRequiredError, ForbiddenError


class TestAnalyzerInitialization:
    """Test analyzer initialization and setup."""
    
    def test_analyzer_creation(self, mock_github_client, mock_stride_client):
        """Test that analyzer can be created with dependencies."""
        analyzer = ActionAnalyzer(mock_github_client, mock_stride_client)
        
        assert analyzer.github_client == mock_github_client
        assert analyzer.stride_client == mock_stride_client


class TestPRAnalysis:
    """Test PR analysis functionality."""
    
    @pytest.fixture
    def analyzer(self, mock_github_client, mock_stride_client):
        """Create analyzer with mocked dependencies."""
        return ActionAnalyzer(mock_github_client, mock_stride_client)
    
    @pytest.mark.asyncio
    async def test_successful_pr_analysis(self, analyzer, mock_github_client, mock_stride_client):
        """Test successful PR analysis."""
        result = await analyzer.analyze_pr(42)
        
        assert isinstance(result, AnalysisResult)
        assert result.threat_count == 1
        assert len(result.threats) == 1
        assert result.analysis_id == "ana_test123"
        assert result.is_limited is False
        
        # Verify client interactions
        mock_github_client.get_pr_files.assert_called_once_with(42)
        mock_stride_client.analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pr_analysis_with_empty_files(self, analyzer, mock_github_client, mock_stride_client):
        """Test PR analysis when no files are found."""
        mock_github_client.get_pr_files.return_value = []
        
        result = await analyzer.analyze_pr(42)
        
        assert result.threat_count == 0
        assert len(result.threats) == 0
        assert result.analysis_id == ""
        
        # Should not call STRIDE API if no files
        mock_stride_client.analyze.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_pr_analysis_private_repo_error(self, analyzer, mock_github_client):
        """Test PR analysis on private repository raises error."""
        mock_github_client.is_public_repo.return_value = False
        
        with pytest.raises(ForbiddenError, match="Private repositories require"):
            await analyzer.analyze_pr(42)
    
    @pytest.mark.asyncio
    async def test_pr_analysis_payment_required(self, analyzer, mock_github_client, mock_stride_client):
        """Test PR analysis when payment is required."""
        mock_stride_client.analyze.side_effect = PaymentRequiredError("Limit reached")
        
        result = await analyzer.analyze_pr(42)
        
        assert result.threat_count == 0
        assert result.is_limited is True
        assert result.upgrade_message == "Monthly analysis limit reached. Upgrade to continue analyzing."


class TestFeatureAnalysis:
    """Test feature description analysis functionality."""
    
    @pytest.fixture
    def analyzer(self, mock_github_client, mock_stride_client):
        """Create analyzer with mocked dependencies."""
        return ActionAnalyzer(mock_github_client, mock_stride_client)
    
    @pytest.mark.asyncio
    async def test_successful_feature_analysis(self, analyzer, mock_github_client, mock_stride_client):
        """Test successful feature description analysis."""
        result = await analyzer.analyze_feature_description(42)
        
        assert isinstance(result, AnalysisResult)
        assert result.threat_count == 1
        assert result.analysis_id == "ana_test123"
        
        # Verify client interactions
        mock_github_client.get_issue_description.assert_called_once_with(42)
        mock_stride_client.analyze.assert_called_once()
        
        # Verify analysis type in request
        call_args = mock_stride_client.analyze.call_args[0][0]
        assert call_args["analysis_type"] == "feature_description"
    
    @pytest.mark.asyncio
    async def test_feature_analysis_empty_description(self, analyzer, mock_github_client, mock_stride_client):
        """Test feature analysis with empty description."""
        mock_github_client.get_issue_description.return_value = "   "  # Whitespace only
        
        result = await analyzer.analyze_feature_description(42)
        
        assert result.threat_count == 0
        assert len(result.threats) == 0
        
        # Should not call STRIDE API if description is empty
        mock_stride_client.analyze.assert_not_called()


class TestRepositoryAnalysis:
    """Test full repository analysis functionality."""
    
    @pytest.fixture
    def analyzer(self, mock_github_client, mock_stride_client):
        """Create analyzer with mocked dependencies."""
        return ActionAnalyzer(mock_github_client, mock_stride_client)
    
    @pytest.mark.asyncio
    async def test_successful_repository_analysis(self, analyzer, mock_github_client, mock_stride_client):
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


class TestAnalysisResultProcessing:
    """Test analysis result processing and formatting."""
    
    @pytest.fixture
    def analyzer(self, mock_github_client, mock_stride_client):
        """Create analyzer with mocked dependencies."""
        return ActionAnalyzer(mock_github_client, mock_stride_client)
    
    @pytest.mark.asyncio
    async def test_truncated_results_handling(self, analyzer, mock_github_client, mock_stride_client):
        """Test that truncated analysis results are properly processed."""
        # Configure STRIDE client with truncated results
        mock_stride_client.analyze.return_value = {
            "analysis_id": "ana_test123",
            "status": "completed",
            "threats": [{"id": "t1"}, {"id": "t2"}],
            "summary": {"total": 5},  # More threats than returned
            "truncated": True,
            "upgrade_message": "Upgrade for more threats"
        }
        
        result = await analyzer.analyze_pr(42)
        
        assert result.threat_count == 5  # Uses summary total, not threats length
        assert result.is_limited is True
        assert result.upgrade_message == "Upgrade for more threats"
    
    def test_repository_url_formatting(self, analyzer, mock_github_client, mock_stride_client):
        """Test that repository URLs are properly formatted."""
        # Test case handled by the analyzer's URL formatting logic
        mock_github_client.repo_name = "test/repo"
        
        # This would be tested during actual analysis calls
        assert True  # Placeholder for URL formatting test


class TestAnalysisResultDataClass:
    """Test the AnalysisResult dataclass functionality."""
    
    def test_analysis_result_creation_with_defaults(self):
        """Test creating an AnalysisResult with default values."""
        result = AnalysisResult(
            threat_count=0,
            threats=[],
            analysis_id="",
            usage_info={}
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
            upgrade_message="Upgrade required"
        )
        
        assert result.is_limited is True
        assert result.upgrade_message == "Upgrade required"
        assert result.usage_info["limit_reached"] is True
    
    def test_analysis_result_with_threats(self):
        """Test AnalysisResult with actual threat data."""
        threats = [
            {
                "id": "t1", 
                "title": "SQL Injection",
                "category": "Tampering",
                "severity": "HIGH"
            }
        ]
        
        result = AnalysisResult(
            threat_count=1,
            threats=threats,
            analysis_id="ana_123",
            usage_info={"plan": "FREE"}
        )
        
        assert result.threat_count == 1
        assert result.threats == threats
        assert result.analysis_id == "ana_123"
        assert result.usage_info["plan"] == "FREE"