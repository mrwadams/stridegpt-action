"""
Tests for STRIDE API client.
"""

import pytest
import httpx
from unittest.mock import patch, Mock, AsyncMock
from tenacity import RetryError

from src.stride_client import (
    StrideClient, 
    StrideAPIError, 
    PaymentRequiredError, 
    ForbiddenError, 
    RateLimitError
)


class TestStrideClientInitialization:
    """Test STRIDE client initialization."""
    
    def test_client_initialization_with_custom_url(self):
        """Test client initialization with custom URL."""
        client = StrideClient("sk_test_123", "https://custom.api.com")
        assert client.base_url == "https://custom.api.com"
        assert client.api_key == "sk_test_123"
        assert client.headers["Authorization"] == "Bearer sk_test_123"
        assert client.headers["User-Agent"] == "STRIDE-GPT-Action/1.0"
    
    def test_client_initialization_with_default_url(self):
        """Test client initialization with default URL from environment."""
        with patch.dict('os.environ', {'STRIDE_API_URL': 'https://custom.api.com'}):
            client = StrideClient("sk_test_123")
            assert client.base_url == "https://custom.api.com"


class TestStrideClientAnalysis:
    """Test STRIDE API client analysis functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return StrideClient("sk_test_123", "https://api.test.com")
    
    @pytest.mark.asyncio
    async def test_analyze_success(self, client, mock_httpx_client):
        """Test successful analysis request."""
        # Configure mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "analysis_id": "ana_test123",
            "status": "completed",
            "threats": []
        }
        mock_response.raise_for_status.return_value = None
        
        mock_httpx_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        analysis_request = {
            "repository": "https://github.com/test/repo",
            "analysis_type": "changed_files"
        }
        
        result = await client.analyze(analysis_request)
        
        assert result["analysis_id"] == "ana_test123"
        assert result["status"] == "completed"
        
        # Verify correct API call
        mock_httpx_client.return_value.__aenter__.return_value.post.assert_called_once_with(
            "https://api.test.com/api/v1/analyze",
            json=analysis_request,
            headers={
                "Authorization": "Bearer sk_test_123",
                "Content-Type": "application/json",
                "User-Agent": "STRIDE-GPT-Action/1.0"
            },
            timeout=60.0
        )
    
    @pytest.mark.asyncio
    async def test_analyze_payment_required(self, client, mock_httpx_client):
        """Test analysis with payment required error."""
        mock_response = Mock()
        mock_response.status_code = 402
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Payment Required", request=Mock(), response=mock_response
        )
        
        mock_httpx_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        analysis_request = {"repository": "https://github.com/test/repo"}
        
        with pytest.raises(PaymentRequiredError, match="Monthly limit reached"):
            await client.analyze(analysis_request)
    
    @pytest.mark.asyncio 
    async def test_analyze_forbidden(self, client, mock_httpx_client):
        """Test analysis with forbidden error."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=Mock(), response=mock_response
        )
        
        mock_httpx_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        analysis_request = {"repository": "https://github.com/test/repo"}
        
        with pytest.raises(ForbiddenError, match="Invalid API key"):
            await client.analyze(analysis_request)
    
    @pytest.mark.asyncio
    async def test_analyze_rate_limit(self, client, mock_httpx_client):
        """Test analysis with rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Too Many Requests", request=Mock(), response=mock_response
        )
        
        mock_httpx_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        analysis_request = {"repository": "https://github.com/test/repo"}
        
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            await client.analyze(analysis_request)
    
    @pytest.mark.asyncio
    async def test_analyze_retry_on_failure(self, client):
        """Test that client retries on transient failures."""
        with patch('httpx.AsyncClient') as mock_client:
            # First two attempts fail, third succeeds
            mock_responses = [
                Exception("Connection failed"),
                Exception("Timeout"),
                Mock(status_code=200, json=lambda: {"status": "success"})
            ]
            
            mock_post = Mock()
            mock_post.side_effect = mock_responses
            mock_client.return_value.__aenter__.return_value.post = mock_post
            mock_client.return_value.__aenter__.return_value.__aexit__ = AsyncMock()
            
            # Mock the last successful response
            mock_responses[2].raise_for_status.return_value = None
            
            analysis_request = {"repository": "https://github.com/test/repo"}
            result = await client.analyze(analysis_request)
            
            assert result["status"] == "success"
            # Should have been called 3 times (2 failures + 1 success)
            assert mock_post.call_count == 3
    
    


class TestStrideClientUsage:
    """Test STRIDE client usage and health check functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return StrideClient("sk_test_123", "https://api.test.com")
    
    @pytest.mark.asyncio
    async def test_get_usage_success(self, client, mock_httpx_client):
        """Test successful usage stats retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "plan": "FREE",
            "analyses_used": 10,
            "analyses_limit": 50
        }
        mock_response.raise_for_status.return_value = None
        
        mock_httpx_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await client.get_usage()
        
        assert result["plan"] == "FREE"
        assert result["analyses_used"] == 10
        
        # Verify correct API call
        mock_httpx_client.return_value.__aenter__.return_value.get.assert_called_once_with(
            "https://api.test.com/api/v1/usage",
            headers={
                "Authorization": "Bearer sk_test_123",
                "Content-Type": "application/json", 
                "User-Agent": "STRIDE-GPT-Action/1.0"
            },
            timeout=10.0
        )
    
    @pytest.mark.asyncio
    async def test_check_health_success(self, client, mock_httpx_client):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_httpx_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await client.check_health()
        
        assert result is True
        
        # Verify correct API call
        mock_httpx_client.return_value.__aenter__.return_value.get.assert_called_once_with(
            "https://api.test.com/health",
            timeout=5.0
        )
    
    @pytest.mark.asyncio
    async def test_check_health_failure(self, client, mock_httpx_client):
        """Test health check failure."""
        mock_httpx_client.return_value.__aenter__.return_value.get.side_effect = Exception("Connection failed")
        
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