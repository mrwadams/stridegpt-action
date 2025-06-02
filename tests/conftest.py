"""
Test configuration and fixtures for STRIDE-GPT GitHub Action tests.
"""

import pytest
import os
import json
import asyncio
from unittest.mock import AsyncMock, Mock, patch


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_github_context():
    """Mock GitHub context for testing."""
    return {
        "event_name": "issue_comment",
        "repository": "test/repo",
        "event": {
            "comment": {"body": "@stride-gpt analyze", "id": 123456},
            "issue": {"number": 42, "pull_request": None},
        },
    }


@pytest.fixture
def mock_pr_context():
    """Mock GitHub context for PR events."""
    return {
        "event_name": "pull_request",
        "repository": "test/repo",
        "event": {
            "pull_request": {
                "number": 42,
                "head": {"sha": "abc123"},
                "base": {"sha": "def456"},
            }
        },
    }


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    env_vars = {
        "STRIDE_API_KEY": "sk_test_123456789abcdef",
        "GITHUB_TOKEN": "ghp_test123456789abcdef",
        "GITHUB_REPOSITORY": "test/repo",
        "TRIGGER_MODE": "comment",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_stride_client():
    """Mock STRIDE API client."""
    client = Mock()

    # Mock successful analysis response
    client.analyze = AsyncMock(
        return_value={
            "analysis_id": "ana_test123",
            "status": "completed",
            "threats": [
                {
                    "id": "threat_1",
                    "category": "Tampering",
                    "title": "SQL Injection Vulnerability",
                    "description": "Potential SQL injection in user input handling",
                    "severity": "HIGH",
                    "affected_files": ["src/database.py"],
                    "scenario": "Attacker injects malicious SQL",
                    "potential_impact": "Data breach or corruption",
                    "mitigations": ["Use parameterized queries"],
                }
            ],
            "summary": {"total": 1, "critical": 0, "high": 1, "medium": 0, "low": 0},
            "metadata": {"plan": "FREE", "model_used": "gpt-3.5-turbo"},
        }
    )

    # Mock usage response
    client.get_usage = AsyncMock(
        return_value={
            "plan": "FREE",
            "analyses_used": 5,
            "analyses_limit": 50,
            "features_available": ["basic_analysis"],
        }
    )

    # Mock health check
    client.check_health = AsyncMock(return_value=True)

    return client


@pytest.fixture
def mock_github_client():
    """Mock GitHub client."""
    client = Mock()

    # Mock repository info
    client.repo_name = "test/repo"
    client.token = "ghp_test123"
    client.is_public_repo.return_value = True

    # Mock PR files
    client.get_pr_files.return_value = [
        {
            "filename": "src/app.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
            "patch": "@@ -1,5 +1,10 @@\n+new code\n-old code",
        }
    ]

    # Mock issue description
    client.get_issue_description.return_value = (
        "Add user authentication with OAuth support"
    )

    # Mock comment posting
    client.create_comment.return_value = (
        "https://github.com/test/repo/issues/42#issuecomment-123456"
    )

    return client


@pytest.fixture
def mock_analysis_result():
    """Mock analysis result."""
    from src.analyzer import AnalysisResult

    return AnalysisResult(
        threat_count=2,
        threats=[
            {
                "id": "threat_1",
                "category": "Tampering",
                "title": "SQL Injection",
                "description": "Potential SQL injection vulnerability",
                "severity": "HIGH",
            },
            {
                "id": "threat_2",
                "category": "Information Disclosure",
                "title": "Sensitive Data Exposure",
                "description": "API keys exposed in logs",
                "severity": "MEDIUM",
            },
        ],
        analysis_id="ana_test123",
        usage_info={"plan": "FREE"},
        is_limited=False,
        upgrade_message=None,
    )


@pytest.fixture
def mock_limited_analysis_result():
    """Mock analysis result with limitations."""
    from src.analyzer import AnalysisResult

    return AnalysisResult(
        threat_count=0,
        threats=[],
        analysis_id="",
        usage_info={"limit_reached": True},
        is_limited=True,
        upgrade_message="Monthly analysis limit reached. Upgrade to continue analyzing.",
    )


@pytest.fixture
def sample_feature_description():
    """Sample feature description for testing."""
    return """
    ## Add User Authentication
    
    We need to implement user authentication using OAuth 2.0. This should include:
    
    - Login/logout functionality
    - Session management
    - Protected routes
    - User profile management
    
    Security considerations:
    - Secure token storage
    - CSRF protection
    - Rate limiting on auth endpoints
    """


@pytest.fixture
def sample_analysis_request():
    """Sample analysis request for testing."""
    return {
        "repository": "https://github.com/test/repo",
        "analysis_type": "changed_files",
        "github_token": "ghp_test123",
        "pr_number": 42,
        "options": {},
    }


@pytest.fixture
def sample_feature_analysis_request():
    """Sample feature analysis request for testing."""
    return {
        "repository": "https://github.com/test/repo",
        "analysis_type": "feature_description",
        "github_token": "ghp_test123",
        "options": {
            "feature_description": "Add user authentication with OAuth",
            "issue_number": 42,
        },
    }


@pytest.fixture
def mock_github_api_responses():
    """Mock responses for GitHub API calls."""
    return {
        "issue": {
            "number": 42,
            "title": "Add user authentication",
            "body": "We need OAuth 2.0 authentication",
            "state": "open",
        },
        "pr": {
            "number": 42,
            "title": "Add authentication system",
            "body": "This PR adds OAuth 2.0 authentication",
            "state": "open",
            "head": {"sha": "abc123"},
            "base": {"sha": "def456"},
        },
        "files": [
            {
                "filename": "src/auth.py",
                "status": "added",
                "additions": 50,
                "deletions": 0,
            }
        ],
    }


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for API calls."""
    with patch("httpx.AsyncClient") as mock_client:
        # Configure mock responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        mock_client.return_value.__aexit__ = AsyncMock()

        yield mock_client
