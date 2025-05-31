#!/usr/bin/env python3
"""
STRIDE-GPT GitHub Action Entry Point
"""

import os
import sys
import json
import asyncio
from typing import Optional

from src.github_client import GitHubClient
from src.stride_client import StrideClient
from src.analyzer import ActionAnalyzer
from src.reporter import CommentReporter


async def main():
    """Main entry point for the GitHub Action."""
    
    # Get environment variables
    api_key = os.environ.get("STRIDE_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    trigger_mode = os.environ.get("TRIGGER_MODE", "comment")
    
    # Validate required inputs
    if not api_key:
        print("::error::STRIDE_API_KEY is required. Get your free key at https://stridegpt.ai")
        sys.exit(1)
    
    if not github_token:
        print("::error::GITHUB_TOKEN is required")
        sys.exit(1)
    
    # Get GitHub context
    github_context = json.loads(os.environ.get("GITHUB_CONTEXT", "{}"))
    repo_name = os.environ.get("GITHUB_REPOSITORY")
    
    if not repo_name:
        print("::error::GITHUB_REPOSITORY not found in environment")
        sys.exit(1)
    
    try:
        # Initialize clients
        github_client = GitHubClient(github_token, repo_name)
        stride_client = StrideClient(api_key)
        analyzer = ActionAnalyzer(github_client, stride_client)
        reporter = CommentReporter(github_client)
        
        # Handle different trigger modes
        if trigger_mode == "comment":
            # Handle comment trigger
            if github_context.get("event_name") != "issue_comment":
                print("::error::Comment trigger requires issue_comment event")
                sys.exit(1)
            
            comment_body = github_context.get("event", {}).get("comment", {}).get("body", "")
            pr_number = github_context.get("event", {}).get("issue", {}).get("number")
            
            if not pr_number:
                print("::error::Could not determine PR number")
                sys.exit(1)
            
            # Check if comment mentions @stride-gpt
            if "@stride-gpt" not in comment_body:
                print("Comment does not mention @stride-gpt, skipping")
                sys.exit(0)
            
            # Parse command
            command = parse_command(comment_body)
            
            if command == "help":
                await reporter.post_help_comment(pr_number)
            elif command == "status":
                usage = await stride_client.get_usage()
                await reporter.post_status_comment(pr_number, usage)
            elif command == "analyze":
                # Run analysis
                print(f"::notice::Starting security analysis for PR #{pr_number}")
                result = await analyzer.analyze_pr(pr_number)
                
                # Post results
                comment_url = await reporter.post_analysis_comment(pr_number, result)
                
                # Set outputs
                with open(os.environ.get('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
                    f.write(f"threat-count={result.threat_count}\n")
                    f.write(f"report-url={comment_url}\n")
            else:
                await reporter.post_error_comment(
                    pr_number, 
                    f"Unknown command: {command}. Use '@stride-gpt help' for available commands."
                )
        
        elif trigger_mode == "pr":
            # Handle PR trigger
            pr_number = github_context.get("event", {}).get("pull_request", {}).get("number")
            
            if not pr_number:
                print("::error::Could not determine PR number from context")
                sys.exit(1)
            
            # Run analysis
            print(f"::notice::Starting automatic security analysis for PR #{pr_number}")
            result = await analyzer.analyze_pr(pr_number)
            
            # Post results
            comment_url = await reporter.post_analysis_comment(pr_number, result)
            
            # Set outputs
            with open(os.environ.get('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
                f.write(f"threat-count={result.threat_count}\n")
                f.write(f"report-url={comment_url}\n")
        
        elif trigger_mode == "manual":
            # Handle manual trigger - analyze the entire repository
            print(f"::notice::Starting manual security analysis for repository {repo_name}")
            result = await analyzer.analyze_repository()
            
            # For manual triggers, we'll output to the logs instead of PR comments
            print("::group::STRIDE-GPT Security Analysis Results")
            print(f"Repository: {repo_name}")
            print(f"Threats found: {result.threat_count}")
            if hasattr(result, 'threats') and result.threats:
                for i, threat in enumerate(result.threats, 1):
                    print(f"\n--- Threat {i} ---")
                    print(f"Category: {threat.category}")
                    print(f"Title: {threat.title}")
                    print(f"Severity: {threat.severity}")
                    print(f"Description: {threat.description}")
            print("::endgroup::")
            
            # Set outputs
            with open(os.environ.get('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
                f.write(f"threat-count={result.threat_count}\n")
        
        else:
            print(f"::error::Unknown trigger mode: {trigger_mode}")
            sys.exit(1)
        
        print("::notice::Analysis completed successfully")
        
    except Exception as e:
        print(f"::error::Action failed: {str(e)}")
        sys.exit(1)


def parse_command(comment_body: str) -> Optional[str]:
    """Parse command from comment body."""
    # Simple command parsing - look for @stride-gpt followed by command
    import re
    
    match = re.search(r'@stride-gpt\s+(\w+)', comment_body.lower())
    if match:
        return match.group(1)
    
    # Default to analyze if just @stride-gpt is mentioned
    if "@stride-gpt" in comment_body:
        return "analyze"
    
    return None


if __name__ == "__main__":
    # Load GitHub context from environment
    if "GITHUB_CONTEXT" not in os.environ:
        # Try to load from GitHub Actions environment variables
        context = {
            "event_name": os.environ.get("GITHUB_EVENT_NAME", ""),
            "repository": os.environ.get("GITHUB_REPOSITORY", ""),
            "event": {}
        }
        
        # Try to load event data from event path
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        if event_path and os.path.exists(event_path):
            with open(event_path, 'r') as f:
                context["event"] = json.load(f)
        
        os.environ["GITHUB_CONTEXT"] = json.dumps(context)
    
    # Run the action
    asyncio.run(main())