"""
Simple tests for STRIDE client functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx

from src.stride_client import (
    StrideClient,
    StrideAPIError,
    PaymentRequiredError,
    ForbiddenError,
    RateLimitError,
)


class TestStrideClientBasics:
    """Test basic STRIDE client functionality."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = StrideClient("sk_test_123", "https://api.test.com")
        assert client.api_key == "sk_test_123"
        assert client.base_url == "https://api.test.com"
        assert client.headers["Authorization"] == "Bearer sk_test_123"
        assert client.headers["User-Agent"] == "STRIDE-GPT-Action/1.0"

    def test_client_default_url(self):
        """Test client with default URL."""
        with patch.dict("os.environ", {"STRIDE_API_URL": "https://custom.api.com"}):
            client = StrideClient("sk_test_123")
            assert client.base_url == "https://custom.api.com"

    @pytest.mark.asyncio
    async def test_analyze_success(self):
        """Test successful analysis request."""
        client = StrideClient("sk_test_123", "https://api.test.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "analysis_id": "ana_test123",
            "status": "completed",
            "threats": [],
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await client.analyze({"repository": "test/repo"})

            assert result["analysis_id"] == "ana_test123"
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_usage_success(self):
        """Test successful usage retrieval."""
        client = StrideClient("sk_test_123", "https://api.test.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "plan": "FREE",
            "analyses_used": 5,
            "analyses_limit": 50,
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await client.get_usage()

            assert result["plan"] == "FREE"
            assert result["analyses_used"] == 5

    @pytest.mark.asyncio
    async def test_check_health_success(self):
        """Test successful health check."""
        client = StrideClient("sk_test_123", "https://api.test.com")

        mock_response = Mock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await client.check_health()

            assert result is True

    @pytest.mark.asyncio
    async def test_check_health_failure(self):
        """Test health check failure."""
        client = StrideClient("sk_test_123", "https://api.test.com")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.side_effect = Exception("Connection failed")

            result = await client.check_health()

            assert result is False


class TestStrideAPIErrors:
    """Test STRIDE API error classes."""

    def test_base_error(self):
        """Test base StrideAPIError."""
        error = StrideAPIError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_payment_required_error(self):
        """Test PaymentRequiredError."""
        error = PaymentRequiredError("Limit reached")
        assert str(error) == "Limit reached"
        assert isinstance(error, StrideAPIError)

    def test_forbidden_error(self):
        """Test ForbiddenError."""
        error = ForbiddenError("Invalid key")
        assert str(error) == "Invalid key"
        assert isinstance(error, StrideAPIError)

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("Too many requests")
        assert str(error) == "Too many requests"
        assert isinstance(error, StrideAPIError)


class TestErrorHandling:
    """Test error handling in client."""

    def test_error_classes_exist(self):
        """Test that error classes can be instantiated."""
        # Just test that the error classes exist and work
        payment_error = PaymentRequiredError("Payment required")
        forbidden_error = ForbiddenError("Forbidden")
        rate_limit_error = RateLimitError("Rate limited")

        assert str(payment_error) == "Payment required"
        assert str(forbidden_error) == "Forbidden"
        assert str(rate_limit_error) == "Rate limited"

        # Test inheritance
        assert isinstance(payment_error, StrideAPIError)
        assert isinstance(forbidden_error, StrideAPIError)
        assert isinstance(rate_limit_error, StrideAPIError)
