"""
Comment Reporter - Formats and posts analysis results to GitHub
"""

from typing import Dict, Any
from datetime import datetime
from .github_client import GitHubClient
from .analyzer import AnalysisResult
from .stride_client import StrideClient


class CommentReporter:
    """Formats and posts analysis results as GitHub comments."""
    
    def __init__(self, github_client: GitHubClient, stride_client: StrideClient = None):
        self.github = github_client
        self.stride = stride_client
    
    async def post_analysis_comment(self, issue_number: int, result: AnalysisResult, is_pull_request: bool = True) -> str:
        """Post analysis results as a comment on issue or PR."""
        
        # Check if limit was reached
        if result.usage_info.get("limit_reached"):
            body = self._format_limit_reached_comment()
        elif result.threat_count == 0:
            body = await self._format_no_threats_comment(result)
        else:
            body = await self._format_threats_comment(result)
        
        # Use appropriate method based on whether it's a PR or issue
        if is_pull_request:
            return self.github.create_comment(issue_number, body)
        else:
            return self.github.create_issue_comment(issue_number, body)
    
    async def post_help_comment(self, issue_number: int, is_pull_request: bool = True) -> str:
        """Post help information as a comment on issue or PR."""
        body = """## 🛡️ STRIDE-GPT Help

### Available Commands
- `@stride-gpt analyze` - Run security analysis on changed files
- `@stride-gpt help` - Show this help message
- `@stride-gpt status` - Check your usage limits

### Free Tier Limits
- **50 analyses per month** per GitHub account
- **5 threats maximum** per analysis
- **Public repositories only**
- **Basic severity ratings** (Low/Medium/High)

### Want More?
Upgrade to STRIDE-GPT Pro for:
- ✨ Unlimited analyses
- 🌳 Attack tree visualization
- 📊 DREAD risk scoring
- 🔒 Private repository support
- 🛠️ Detailed mitigation steps
- 📋 Compliance mapping

[View Pricing →](https://stridegpt.ai/pricing)"""
        
        # Use appropriate method based on whether it's a PR or issue
        if is_pull_request:
            return self.github.create_comment(issue_number, body)
        else:
            return self.github.create_issue_comment(issue_number, body)
    
    async def post_status_comment(self, issue_number: int, usage: Dict[str, Any], is_pull_request: bool = True) -> str:
        """Post usage status as a comment on issue or PR."""
        analyses_used = usage.get("analyses_used", 0)
        analyses_limit = usage.get("analyses_limit", 50)
        remaining = analyses_limit - analyses_used
        
        body = f"""## 📊 STRIDE-GPT Usage Status

### Current Month
- **Analyses Used**: {analyses_used} of {analyses_limit}
- **Remaining**: {remaining}
- **Plan**: {usage.get("plan", "Free").title()}

### Account Details  
- **User**: {usage.get("account", "N/A")}
- **Period**: {self._format_date(usage.get("period_start"))} to {self._format_date(usage.get("period_end"))}
- **Days Remaining**: {self._calculate_days_remaining(usage.get("period_end"))}

{self._get_upgrade_prompt() if usage.get("plan", "free").lower() == "free" else ""}"""
        
        # Use appropriate method based on whether it's a PR or issue
        if is_pull_request:
            return self.github.create_comment(issue_number, body)
        else:
            return self.github.create_issue_comment(issue_number, body)
    
    async def post_error_comment(self, issue_number: int, error_message: str, is_pull_request: bool = True) -> str:
        """Post error message as a comment on issue or PR."""
        body = f"""## ❌ STRIDE-GPT Error

{error_message}

### Need Help?
- Use `@stride-gpt help` to see available commands
- Visit [documentation](https://stridegpt.ai/docs)
- Contact [support](https://stridegpt.ai/support)"""
        
        # Use appropriate method based on whether it's a PR or issue
        if is_pull_request:
            return self.github.create_comment(issue_number, body)
        else:
            return self.github.create_issue_comment(issue_number, body)
    
    async def _format_threats_comment(self, result: AnalysisResult) -> str:
        """Format threats into a comment."""
        severity_emoji = {
            "high": "🔴",
            "medium": "🟡", 
            "low": "🟢"
        }
        
        # Get current plan info
        try:
            if self.stride:
                current_usage = await self.stride.get_usage()
                plan_name = current_usage.get("plan", "free").title()
            else:
                plan_name = "Free"
        except Exception:
            plan_name = "Free"
        
        # Count threats by severity
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for threat in result.threats:
            severity = threat.get("severity", "medium").lower()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Build comment
        lines = [
            f"## 🛡️ STRIDE Security Analysis ({plan_name} Tier)",
            "",
            "### Summary",
            f"- **Threats Found**: {result.threat_count} {'of 5 max' if result.is_limited else ''}",
            "- **Analysis Scope**: Changed files only",
            f"- **Severity Levels**: {severity_counts['high']} High, {severity_counts['medium']} Medium, {severity_counts['low']} Low",
            "",
            "### Identified Threats",
            ""
        ]
        
        # Add each threat
        for threat in result.threats:
            severity = threat.get("severity", "medium").lower()
            emoji = severity_emoji.get(severity, "🟡")
            
            lines.extend([
                f"#### {emoji} {severity.upper()}: {threat.get('title', 'Unknown Threat')}",
                f"**Category**: {threat.get('category', 'Unknown')}",
                f"**File**: `{threat.get('file', 'Unknown')}:{threat.get('line', '?')}`",
                f"**Description**: {threat.get('description', 'No description provided')}",
                ""
            ])
        
        # Add upgrade message if limited
        if result.is_limited and result.upgrade_message:
            lines.extend([
                "---",
                "",
                f"⚠️ **{result.upgrade_message}**",
                ""
            ])
        
        # Add upgrade prompt and usage footer
        lines.extend([
            "---",
            "",
            self._get_upgrade_prompt(),
            ""
        ])
        
        # Add real-time usage footer
        usage_footer = await self._get_usage_footer(result.usage_info)
        lines.append(usage_footer)
        
        return "\n".join(lines)
    
    async def _format_no_threats_comment(self, result: AnalysisResult) -> str:
        """Format comment when no threats are found."""
        # Get current plan info
        try:
            if self.stride:
                current_usage = await self.stride.get_usage()
                plan_name = current_usage.get("plan", "free").title()
            else:
                plan_name = "Free"
        except Exception:
            plan_name = "Free"
            
        # Get real-time usage footer
        usage_footer = await self._get_usage_footer(result.usage_info)
        
        return f"""## 🛡️ STRIDE Security Analysis ({plan_name} Tier)

### ✅ No Security Threats Detected

Great job! No obvious security threats were found in the changed files.

### Analysis Details
- **Files Analyzed**: Changed files in this PR
- **Analysis Type**: Basic STRIDE methodology
- **Severity Levels**: Low/Medium/High

### 💡 Want Deeper Analysis?

While no obvious threats were found, STRIDE-GPT Pro offers:
- 🔍 **Deep code analysis** with AI-powered pattern recognition
- 🌳 **Attack tree generation** to visualize potential attack paths
- 📊 **DREAD scoring** for risk prioritization
- 🛠️ **Detailed remediation** guidance
- 🔒 **Private repository** support

[Upgrade to Pro →](https://stridegpt.ai/pricing)

{usage_footer}"""
    
    def _format_limit_reached_comment(self) -> str:
        """Format comment when usage limit is reached."""
        return """## 🛑 Monthly Analysis Limit Reached

You've used all 50 free analyses for this month. Your limit will reset at the beginning of next month.

### Continue Analyzing Today

Upgrade to a paid plan for:
- ✅ **Unlimited analyses**
- ✅ **Advanced threat detection**
- ✅ **DREAD risk scoring**
- ✅ **Attack tree diagrams**
- ✅ **Private repository support**
- ✅ **Priority support**

### Pricing Plans
- **Starter** ($29/month): 500 analyses, all Pro features
- **Pro** ($99/month): 2,500 analyses, API access
- **Enterprise** ($299/month): Unlimited analyses, SLA support

[Upgrade Now →](https://stridegpt.ai/pricing)"""
    
    def _get_upgrade_prompt(self) -> str:
        """Get upgrade prompt for free tier users."""
        return """### 📈 Want More Detailed Analysis?
Upgrade to STRIDE-GPT Pro for:
- ✨ DREAD risk scoring
- 🌳 Attack tree visualization
- 🛠️ Detailed mitigation steps
- 🔒 Private repository support
- 📊 Compliance mapping

[Get Started →](https://stridegpt.ai/pricing)"""
    
    async def _get_usage_footer(self, usage_info: Dict[str, Any]) -> str:
        """Get usage footer for comments with real-time data."""
        try:
            # Fetch real-time usage data if stride client is available
            if self.stride:
                current_usage = await self.stride.get_usage()
                analyses_used = current_usage.get("analyses_used", 0)
                analyses_limit = current_usage.get("analyses_limit", 50)
                plan = current_usage.get("plan", "free").title()
            else:
                # Fallback to metadata from analysis result
                analyses_used = usage_info.get("analyses_used", 0)
                analyses_limit = usage_info.get("analyses_limit", 50)
                plan = usage_info.get("plan", "free").title()
            
            return f"\n*You've used {analyses_used} of {analyses_limit} {plan.lower()} analyses this month*"
        except Exception:
            # Fallback to original behavior on error
            analyses_used = usage_info.get("analyses_used", 0)
            analyses_limit = usage_info.get("analyses_limit", 50)
            return f"\n*You've used {analyses_used} of {analyses_limit} free analyses this month*"
    
    def _format_date(self, date_str: str) -> str:
        """Format date for user-friendly display."""
        if date_str and date_str != "N/A":
            try:
                # Handle various date formats
                if isinstance(date_str, str):
                    # Remove Z and replace with +00:00 for UTC
                    if date_str.endswith('Z'):
                        date_str = date_str.replace('Z', '+00:00')
                    elif not date_str.endswith('+00:00') and not date_str.endswith('UTC'):
                        date_str = date_str + '+00:00'
                    
                    date_obj = datetime.fromisoformat(date_str)
                else:
                    date_obj = date_str  # Already a datetime object
                
                return date_obj.strftime("%b %d, %Y")
            except (ValueError, AttributeError):
                return date_str  # Return as-is if parsing fails
        return "N/A"
    
    def _calculate_days_remaining(self, period_end: str) -> str:
        """Calculate days remaining in the current period."""
        if period_end and period_end != "N/A":
            try:
                # Handle various date formats
                if isinstance(period_end, str):
                    if period_end.endswith('Z'):
                        period_end = period_end.replace('Z', '+00:00')
                    elif not period_end.endswith('+00:00') and not period_end.endswith('UTC'):
                        period_end = period_end + '+00:00'
                    
                    end_date = datetime.fromisoformat(period_end)
                else:
                    end_date = period_end  # Already a datetime object
                
                now = datetime.now(end_date.tzinfo) if end_date.tzinfo else datetime.now()
                days_left = (end_date - now).days
                
                if days_left > 0:
                    return f"{days_left} days"
                elif days_left == 0:
                    return "Last day"
                else:
                    return "Period ended"
            except (ValueError, AttributeError):
                return "Unknown"
        return "N/A"