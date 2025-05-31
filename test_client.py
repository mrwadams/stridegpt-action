#!/usr/bin/env python3
"""
Simple test script for STRIDE action API client
"""

import asyncio
import os
import sys
sys.path.append('src')

from stride_client import StrideClient

async def test_client():
    """Test the STRIDE API client."""
    
    # You'll need to set this environment variable
    api_key = os.environ.get("STRIDE_API_KEY")
    if not api_key:
        print("Please set STRIDE_API_KEY environment variable")
        print("Get a free key at: https://stridegpt.ai")
        return
    
    client = StrideClient(api_key)
    
    # Test health check
    print("Testing health check...")
    is_healthy = await client.check_health()
    print(f"API Health: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
    
    if not is_healthy:
        print("API is not healthy, stopping test")
        return
    
    # Test usage endpoint
    print("\nTesting usage endpoint...")
    try:
        usage = await client.get_usage()
        print(f"Usage Response: {usage}")
    except Exception as e:
        print(f"Usage Error: {e}")
    
    # Test analysis endpoint (you'll need a valid repo)
    print("\nTesting analysis endpoint...")
    try:
        analysis_request = {
            "repository": "https://github.com/octocat/Hello-World",
            "analysis_type": "changed_files",
            "options": {}
        }
        result = await client.analyze(analysis_request)
        print(f"Analysis Response: {result}")
    except Exception as e:
        print(f"Analysis Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_client())