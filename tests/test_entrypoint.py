"""
Tests for GitHub Action entrypoint functionality.
"""

import pytest
import os
import json
import sys
from unittest.mock import patch, Mock, AsyncMock
from io import StringIO

import entrypoint
from src.analyzer import AnalysisResult


class TestMainFunction:
    """Test the main entry point function."""
    
    @pytest.mark.asyncio
    async def test_main_comment_trigger_analyze(self, mock_env_vars, mock_github_context):
        """Test main function with comment trigger for analysis."""
        mock_github_context["event"]["comment"]["body"] = "@stride-gpt analyze"
        
        with patch.dict(os.environ, {
            **mock_env_vars,
            "GITHUB_CONTEXT": json.dumps(mock_github_context)
        }), \
        patch('entrypoint.GitHubClient') as mock_gh_client, \
        patch('entrypoint.StrideClient') as mock_stride_client, \
        patch('entrypoint.ActionAnalyzer') as mock_analyzer, \
        patch('entrypoint.CommentReporter') as mock_reporter:
            
            # Configure mocks
            mock_analysis_result = AnalysisResult(
                threat_count=2,
                threats=[],
                analysis_id="ana_test123",
                usage_info={}
            )
            mock_analyzer.return_value.analyze_feature_description.return_value = mock_analysis_result
            mock_reporter.return_value.post_analysis_comment.return_value = "https://github.com/test/repo/issues/42#comment-123"
            
            # Run main function
            await entrypoint.main()
            
            # Verify analyzer was called for feature description (issue, not PR)
            mock_analyzer.return_value.analyze_feature_description.assert_called_once_with(42)
            
            # Verify comment was posted
            mock_reporter.return_value.post_analysis_comment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_comment_trigger_pr_analyze(self, mock_env_vars, mock_github_context):
        """Test main function with comment trigger on PR."""
        # Configure as PR comment
        mock_github_context["event"]["issue"]["pull_request"] = {"url": "https://api.github.com/repos/test/repo/pulls/42"}
        mock_github_context["event"]["comment"]["body"] = "@stride-gpt analyze"
        
        with patch.dict(os.environ, {
            **mock_env_vars,
            "GITHUB_CONTEXT": json.dumps(mock_github_context)
        }), \
        patch('entrypoint.GitHubClient') as mock_gh_client, \
        patch('entrypoint.StrideClient') as mock_stride_client, \
        patch('entrypoint.ActionAnalyzer') as mock_analyzer, \
        patch('entrypoint.CommentReporter') as mock_reporter:
            
            # Configure mocks
            mock_analysis_result = AnalysisResult(
                threat_count=1,
                threats=[],
                analysis_id="ana_test123",
                usage_info={}
            )
            mock_analyzer.return_value.analyze_pr.return_value = mock_analysis_result
            mock_reporter.return_value.post_analysis_comment.return_value = "https://github.com/test/repo/pulls/42#comment-123"
            
            # Run main function
            await entrypoint.main()
            
            # Verify analyzer was called for PR analysis
            mock_analyzer.return_value.analyze_pr.assert_called_once_with(42)
    
    @pytest.mark.asyncio
    async def test_main_comment_trigger_help(self, mock_env_vars, mock_github_context):
        """Test main function with help command."""
        mock_github_context["event"]["comment"]["body"] = "@stride-gpt help"
        
        with patch.dict(os.environ, {
            **mock_env_vars,
            "GITHUB_CONTEXT": json.dumps(mock_github_context)
        }), \
        patch('entrypoint.GitHubClient') as mock_gh_client, \
        patch('entrypoint.StrideClient') as mock_stride_client, \
        patch('entrypoint.ActionAnalyzer') as mock_analyzer, \
        patch('entrypoint.CommentReporter') as mock_reporter:
            
            # Run main function
            await entrypoint.main()
            
            # Verify help comment was posted
            mock_reporter.return_value.post_help_comment.assert_called_once_with(42, False)
            
            # Verify no analysis was performed
            mock_analyzer.return_value.analyze_pr.assert_not_called()
            mock_analyzer.return_value.analyze_feature_description.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_main_comment_trigger_status(self, mock_env_vars, mock_github_context):
        """Test main function with status command."""
        mock_github_context["event"]["comment"]["body"] = "@stride-gpt status"
        
        with patch.dict(os.environ, {
            **mock_env_vars,
            "GITHUB_CONTEXT": json.dumps(mock_github_context)
        }), \
        patch('entrypoint.GitHubClient') as mock_gh_client, \
        patch('entrypoint.StrideClient') as mock_stride_client, \
        patch('entrypoint.ActionAnalyzer') as mock_analyzer, \
        patch('entrypoint.CommentReporter') as mock_reporter:
            
            # Configure mock usage response
            mock_usage = {"plan": "FREE", "analyses_used": 5, "analyses_limit": 50}
            mock_stride_client.return_value.get_usage.return_value = mock_usage
            
            # Run main function
            await entrypoint.main()
            
            # Verify status comment was posted
            mock_reporter.return_value.post_status_comment.assert_called_once_with(42, mock_usage, False)
    
    @pytest.mark.asyncio
    async def test_main_pr_trigger(self, mock_env_vars, mock_pr_context):
        """Test main function with PR trigger."""
        with patch.dict(os.environ, {
            **mock_env_vars,
            "TRIGGER_MODE": "pr",
            "GITHUB_CONTEXT": json.dumps(mock_pr_context)
        }), \
        patch('entrypoint.GitHubClient') as mock_gh_client, \
        patch('entrypoint.StrideClient') as mock_stride_client, \
        patch('entrypoint.ActionAnalyzer') as mock_analyzer, \
        patch('entrypoint.CommentReporter') as mock_reporter:
            
            # Configure mocks
            mock_analysis_result = AnalysisResult(
                threat_count=3,
                threats=[],
                analysis_id="ana_test123",
                usage_info={}
            )
            mock_analyzer.return_value.analyze_pr.return_value = mock_analysis_result
            
            # Run main function
            await entrypoint.main()
            
            # Verify PR analysis was performed
            mock_analyzer.return_value.analyze_pr.assert_called_once_with(42)
    
    @pytest.mark.asyncio
    async def test_main_manual_trigger(self, mock_env_vars):
        """Test main function with manual trigger."""
        with patch.dict(os.environ, {
            **mock_env_vars,
            "TRIGGER_MODE": "manual"
        }), \
        patch('entrypoint.GitHubClient') as mock_gh_client, \
        patch('entrypoint.StrideClient') as mock_stride_client, \
        patch('entrypoint.ActionAnalyzer') as mock_analyzer, \
        patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            
            # Configure mocks
            mock_analysis_result = AnalysisResult(
                threat_count=2,
                threats=[
                    {"category": "Tampering", "title": "SQL Injection", "severity": "HIGH", "description": "Test threat"}
                ],
                analysis_id="ana_test123",
                usage_info={}
            )
            mock_analyzer.return_value.analyze_repository.return_value = mock_analysis_result
            
            # Run main function
            await entrypoint.main()
            
            # Verify repository analysis was performed
            mock_analyzer.return_value.analyze_repository.assert_called_once()
            
            # Verify output was printed to stdout
            output = mock_stdout.getvalue()
            assert "STRIDE-GPT Security Analysis Results" in output
            assert "Threats found: 2" in output
    
    @pytest.mark.asyncio
    async def test_main_missing_api_key(self, mock_env_vars):
        """Test main function fails with missing API key."""
        with patch.dict(os.environ, {**mock_env_vars, "STRIDE_API_KEY": ""}), \
             patch('sys.exit') as mock_exit, \
             patch('builtins.print') as mock_print:
            
            await entrypoint.main()
            
            mock_exit.assert_called_once_with(1)
            mock_print.assert_called_with("::error::STRIDE_API_KEY is required. Get your free key at https://stridegpt.ai")
    
    @pytest.mark.asyncio
    async def test_main_missing_github_token(self, mock_env_vars):
        """Test main function fails with missing GitHub token."""
        with patch.dict(os.environ, {**mock_env_vars, "GITHUB_TOKEN": ""}), \
             patch('sys.exit') as mock_exit, \
             patch('builtins.print') as mock_print:
            
            await entrypoint.main()
            
            mock_exit.assert_called_once_with(1)
            mock_print.assert_called_with("::error::GITHUB_TOKEN is required")
    
    @pytest.mark.asyncio
    async def test_main_missing_repo_name(self, mock_env_vars):
        """Test main function fails with missing repository name."""
        with patch.dict(os.environ, {**mock_env_vars, "GITHUB_REPOSITORY": ""}), \
             patch('sys.exit') as mock_exit, \
             patch('builtins.print') as mock_print:
            
            await entrypoint.main()
            
            mock_exit.assert_called_once_with(1)
            mock_print.assert_called_with("::error::GITHUB_REPOSITORY not found in environment")
    
    @pytest.mark.asyncio
    async def test_main_exception_handling(self, mock_env_vars, mock_github_context):
        """Test main function handles exceptions gracefully."""
        with patch.dict(os.environ, {
            **mock_env_vars,
            "GITHUB_CONTEXT": json.dumps(mock_github_context)
        }), \
        patch('entrypoint.GitHubClient') as mock_gh_client, \
        patch('entrypoint.StrideClient') as mock_stride_client, \
        patch('entrypoint.ActionAnalyzer') as mock_analyzer, \
        patch('entrypoint.CommentReporter') as mock_reporter, \
        patch('sys.exit') as mock_exit, \
        patch('builtins.print') as mock_print:
            
            # Make analyzer raise an exception
            mock_analyzer.side_effect = Exception("Test error")
            
            await entrypoint.main()
            
            mock_exit.assert_called_once_with(1)
            mock_print.assert_called_with("::error::Action failed: Test error")
    
    @pytest.mark.asyncio
    async def test_output_file_writing(self, mock_env_vars, mock_pr_context):
        """Test that outputs are written to GITHUB_OUTPUT file."""
        with patch.dict(os.environ, {
            **mock_env_vars,
            "TRIGGER_MODE": "pr",
            "GITHUB_OUTPUT": "/tmp/test_output",
            "GITHUB_CONTEXT": json.dumps(mock_pr_context)
        }), \
        patch('entrypoint.GitHubClient') as mock_gh_client, \
        patch('entrypoint.StrideClient') as mock_stride_client, \
        patch('entrypoint.ActionAnalyzer') as mock_analyzer, \
        patch('entrypoint.CommentReporter') as mock_reporter, \
        patch('builtins.open', create=True) as mock_open:
            
            # Configure mocks
            mock_analysis_result = AnalysisResult(
                threat_count=5,
                threats=[],
                analysis_id="ana_test123",
                usage_info={}
            )
            mock_analyzer.return_value.analyze_pr.return_value = mock_analysis_result
            mock_reporter.return_value.post_analysis_comment.return_value = "https://github.com/test/repo/pulls/42#comment-123"
            
            # Mock file operations
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Run main function
            await entrypoint.main()
            
            # Verify file was opened and written to
            mock_open.assert_called_once_with("/tmp/test_output", 'a')
            mock_file.write.assert_any_call("threat-count=5\n")
            mock_file.write.assert_any_call("report-url=https://github.com/test/repo/pulls/42#comment-123\n")


class TestParseCommand:
    """Test the command parsing function."""
    
    def test_parse_command_analyze(self):
        """Test parsing analyze command."""
        command = entrypoint.parse_command("@stride-gpt analyze")
        assert command == "analyze"
    
    def test_parse_command_help(self):
        """Test parsing help command.""" 
        command = entrypoint.parse_command("@stride-gpt help")
        assert command == "help"
    
    def test_parse_command_status(self):
        """Test parsing status command."""
        command = entrypoint.parse_command("@stride-gpt status")
        assert command == "status"
    
    def test_parse_command_default_analyze(self):
        """Test that just mentioning @stride-gpt defaults to analyze."""
        command = entrypoint.parse_command("Hey @stride-gpt can you check this?")
        assert command == "analyze"
    
    def test_parse_command_case_insensitive(self):
        """Test that command parsing is case insensitive."""
        command = entrypoint.parse_command("@STRIDE-GPT HELP")
        assert command == "help"
    
    def test_parse_command_with_extra_text(self):
        """Test parsing command with extra text."""
        command = entrypoint.parse_command("Please @stride-gpt analyze this PR for security issues")
        assert command == "analyze"
    
    def test_parse_command_no_mention(self):
        """Test parsing when @stride-gpt is not mentioned."""
        command = entrypoint.parse_command("This is just a regular comment")
        assert command is None
    
    def test_parse_command_unknown(self):
        """Test parsing unknown command."""
        command = entrypoint.parse_command("@stride-gpt unknown")
        assert command == "unknown"


class TestGitHubContextLoading:
    """Test GitHub context loading functionality."""
    
    def test_context_loading_from_environment(self):
        """Test loading context from environment variables."""
        mock_event_data = {"test": "data"}
        
        with patch.dict(os.environ, {
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REPOSITORY": "test/repo",
            "GITHUB_EVENT_PATH": "/tmp/event.json"
        }), \
        patch('os.path.exists', return_value=True), \
        patch('builtins.open') as mock_open, \
        patch('json.load', return_value=mock_event_data):
            
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Simulate the context loading logic
            if "GITHUB_CONTEXT" not in os.environ:
                context = {
                    "event_name": os.environ.get("GITHUB_EVENT_NAME", ""),
                    "repository": os.environ.get("GITHUB_REPOSITORY", ""),
                    "event": {}
                }
                
                event_path = os.environ.get("GITHUB_EVENT_PATH")
                if event_path and os.path.exists(event_path):
                    with open(event_path, 'r') as f:
                        context["event"] = json.load(f)
                
                os.environ["GITHUB_CONTEXT"] = json.dumps(context)
            
            # Verify context was properly constructed
            loaded_context = json.loads(os.environ["GITHUB_CONTEXT"])
            assert loaded_context["event_name"] == "pull_request"
            assert loaded_context["repository"] == "test/repo"
            assert loaded_context["event"] == mock_event_data