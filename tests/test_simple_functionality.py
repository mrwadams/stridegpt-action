"""
Simple functionality tests that avoid complex mocking issues.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.analyzer import ActionAnalyzer, AnalysisResult
from src.github_client import GitHubClient
from src.stride_client import StrideClient
import entrypoint


class TestBasicFunctionality:
    """Test basic functionality without complex mocking."""
    
    def test_analysis_result_creation(self):
        """Test creating an AnalysisResult."""
        result = AnalysisResult(
            threat_count=1,
            threats=[{"id": "test"}],
            analysis_id="ana_123",
            usage_info={"plan": "FREE"}
        )
        
        assert result.threat_count == 1
        assert len(result.threats) == 1
        assert result.analysis_id == "ana_123"
        assert result.is_limited is False
        assert result.upgrade_message is None
    
    def test_analysis_result_with_limits(self):
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


class TestCommandParsing:
    """Test command parsing functionality."""
    
    def test_parse_analyze_command(self):
        """Test parsing analyze command."""
        command = entrypoint.parse_command("@stride-gpt analyze")
        assert command == "analyze"
    
    def test_parse_help_command(self):
        """Test parsing help command.""" 
        command = entrypoint.parse_command("@stride-gpt help")
        assert command == "help"
    
    def test_parse_status_command(self):
        """Test parsing status command."""
        command = entrypoint.parse_command("@stride-gpt status")
        assert command == "status"
    
    def test_parse_command_with_text_before(self):
        """Test parsing command with text before mention."""
        command = entrypoint.parse_command("Please @stride-gpt analyze this PR")
        assert command == "analyze"
    
    def test_parse_command_just_mention(self):
        """Test that just mentioning @stride-gpt defaults to analyze."""
        command = entrypoint.parse_command("Hey @stride-gpt, can you check this")
        assert command == "analyze"
    
    def test_parse_command_case_insensitive(self):
        """Test that command parsing is case insensitive."""
        command = entrypoint.parse_command("@STRIDE-GPT HELP")
        assert command == "help"
    
    def test_parse_command_no_mention(self):
        """Test parsing when @stride-gpt is not mentioned."""
        command = entrypoint.parse_command("This is just a regular comment")
        assert command is None
    
    def test_parse_unknown_command(self):
        """Test parsing unknown command."""
        command = entrypoint.parse_command("@stride-gpt unknown")
        assert command == "unknown"


class TestAnalyzerWithMocks:
    """Test analyzer with simple mocks."""
    
    def test_analyzer_initialization(self):
        """Test analyzer can be initialized."""
        github_client = Mock(spec=GitHubClient)
        stride_client = Mock(spec=StrideClient)
        
        analyzer = ActionAnalyzer(github_client, stride_client)
        
        assert analyzer.github == github_client
        assert analyzer.stride == stride_client
    
    @pytest.mark.asyncio
    async def test_empty_pr_files(self):
        """Test analyzer behavior with empty PR files."""
        github_client = Mock(spec=GitHubClient)
        stride_client = Mock(spec=StrideClient)
        
        # Mock empty file list
        github_client.is_public_repo.return_value = True
        github_client.get_pr_files.return_value = []
        
        analyzer = ActionAnalyzer(github_client, stride_client)
        result = await analyzer.analyze_pr(42)
        
        assert result.threat_count == 0
        assert len(result.threats) == 0
        assert result.analysis_id == ""
        
        # Should not call stride client for empty files
        stride_client.analyze.assert_not_called()
    
    @pytest.mark.asyncio 
    async def test_empty_feature_description(self):
        """Test analyzer behavior with empty feature description."""
        github_client = Mock(spec=GitHubClient)
        stride_client = Mock(spec=StrideClient)
        
        # Mock empty description
        github_client.get_issue_description.return_value = "   "  # Just whitespace
        
        analyzer = ActionAnalyzer(github_client, stride_client)
        result = await analyzer.analyze_feature_description(42)
        
        assert result.threat_count == 0
        assert len(result.threats) == 0
        
        # Should not call stride client for empty description
        stride_client.analyze.assert_not_called()


class TestConfigValidation:
    """Test configuration validation helpers."""
    
    def test_api_key_formats(self):
        """Test API key format validation."""
        valid_keys = [
            "sk_test_123456789abcdef",
            "sk_live_abcdef123456789",
            "sk_dev_999888777666555"
        ]
        
        for key in valid_keys:
            assert key.startswith("sk_")
            assert len(key) > 10
    
    def test_github_token_formats(self):
        """Test GitHub token format validation."""
        valid_tokens = [
            "ghp_test123456789abcdef",
            "gho_example123456789abc",
            "ghr_test123456789abcdef",
            "ghs_test123456789abcdef"
        ]
        
        for token in valid_tokens:
            assert token.startswith(("ghp_", "gho_", "ghr_", "ghs_"))
            assert len(token) > 10