#!/usr/bin/env python3
"""
Simple test script for STRIDE action API client
"""

import asyncio
import os
import sys

# Add src directory to path
sys.path.append("src")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print(
        "Warning: python-dotenv not installed. Using system environment variables only."
    )
    print("Install with: pip install python-dotenv")

from stride_client import StrideClient


async def test_client():
    """Test the STRIDE API client."""

    # Load API key from environment (supports .env file)
    api_key = os.environ.get("STRIDE_API_KEY")
    if not api_key:
        print("❌ STRIDE_API_KEY not found!")
        print("")
        print("Options:")
        print("1. Create a .env file with: STRIDE_API_KEY=your_key_here")
        print("2. Set environment variable: export STRIDE_API_KEY=your_key_here")
        print("3. Get a free key at: https://stridegpt-api-production.up.railway.app")
        return

    print(f"🔑 Using API key: {api_key[:12]}...{api_key[-4:]}")

    client = StrideClient(api_key)

    # Test health check
    print("Testing health check...")
    is_healthy = await client.check_health()
    print(f"API Health: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")

    if not is_healthy:
        print("API is not healthy, stopping test")
        return

    # Test usage endpoint
    print("\n📊 Testing usage endpoint...")
    try:
        usage = await client.get_usage()
        print(f"✅ Usage Response:")
        print(f"   Plan: {usage.get('plan', 'unknown')}")
        print(
            f"   Analyses Used: {usage.get('analyses_used', 0)}/{usage.get('analyses_limit', 'unlimited')}"
        )
        print(f"   Features: {', '.join(usage.get('features_available', []))}")
    except Exception as e:
        print(f"❌ Usage Error: {e}")

    # Test analysis endpoint
    print("\n🔍 Testing analysis endpoint...")
    try:
        analysis_request = {
            "repository": "https://github.com/octocat/Hello-World",
            "analysis_type": "changed_files",
            "github_token": None,  # Not required for public repos
            "options": {},
        }
        print(f"📤 Sending request: {analysis_request}")
        result = await client.analyze(analysis_request)
        print(f"✅ Analysis completed successfully!")
        print(f"   Analysis ID: {result.get('analysis_id', 'Unknown')}")
        print(f"   Status: {result.get('status', 'Unknown')}")
        print(f"   Threats found: {len(result.get('threats', []))}")

        # Show first threat if any
        threats = result.get("threats", [])
        if threats:
            first_threat = threats[0]
            print(f"   First threat: {first_threat.get('title', 'Unknown')}")
            print(f"   Category: {first_threat.get('category', 'Unknown')}")
            print(f"   Severity: {first_threat.get('severity', 'Unknown')}")

        # Show summary
        summary = result.get("summary", {})
        if summary:
            print(
                f"   Summary: {summary.get('total', 0)} total, {summary.get('high', 0)} high, {summary.get('medium', 0)} medium"
            )
    except Exception as e:
        print(f"❌ Analysis Error: {e}")
        # Try to get more details about the error
        if hasattr(e, "__cause__") and hasattr(e.__cause__, "response"):
            try:
                error_detail = e.__cause__.response.text
                print(f"   Error details: {error_detail}")
            except:
                pass


if __name__ == "__main__":
    asyncio.run(test_client())
