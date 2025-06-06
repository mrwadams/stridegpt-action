"""
STRIDE-GPT API Client
"""

import os
from typing import Dict, Any, List, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class StrideClient:
    """Client for interacting with STRIDE-GPT API."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url or os.environ.get(
            "STRIDE_API_URL", "https://stridegpt-api-production.up.railway.app"
        )
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "STRIDE-GPT-Action/1.0",
        }

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def analyze(self, analysis_request: Dict[str, Any]) -> Dict[str, Any]:
        """Submit analysis request to STRIDE-GPT API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/analyze",
                    json=analysis_request,
                    headers=self.headers,
                    timeout=180.0,
                )
        except httpx.TimeoutException:
            raise StrideAPIError(
                "Analysis request timed out. Large repositories may take longer to analyze. "
                "Consider using a smaller repository or contact support if this persists."
            )

        if response.status_code == 402:
            # Check if this is a private repo plan restriction
            try:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("detail", "")
            except:
                error_message = ""

            if "private" in error_message.lower():
                raise PaymentRequiredError(
                    "Private repositories require a paid STRIDE-GPT plan. "
                    "Visit https://stridegpt.ai/pricing to upgrade."
                )
            else:
                raise PaymentRequiredError(
                    "Monthly limit reached. Please upgrade your plan."
                )
        elif response.status_code == 403:
            try:
                error_data = response.json() if response.content else {}
                error_message = error_data.get(
                    "detail", "Invalid API key or insufficient permissions."
                )
            except:
                error_message = "Invalid API key or insufficient permissions."
            raise ForbiddenError(error_message)
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded. Please try again later.")

        response.raise_for_status()
        return response.json()

    async def get_usage(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/usage", headers=self.headers, timeout=10.0
            )

            response.raise_for_status()
            return response.json()

    async def check_health(self) -> bool:
        """Check if the API is healthy."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=5.0)
                return response.status_code == 200
        except Exception:
            return False


class StrideAPIError(Exception):
    """Base exception for STRIDE API errors."""

    pass


class PaymentRequiredError(StrideAPIError):
    """Raised when usage limit is exceeded."""

    pass


class ForbiddenError(StrideAPIError):
    """Raised when API key is invalid or lacks permissions."""

    pass


class RateLimitError(StrideAPIError):
    """Raised when rate limit is exceeded."""

    pass
