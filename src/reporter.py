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

    async def post_analysis_comment(
        self, issue_number: int, result: AnalysisResult, is_pull_request: bool = True
    ) -> str:
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

    async def post_help_comment(
        self, issue_number: int, is_pull_request: bool = True
    ) -> str:
        """Post help information as a comment on issue or PR."""
        body = """## 🛡️ STRIDE GPT Help

### Available Commands
- `@stride-gpt analyze` - Run security analysis on changed files
- `@stride-gpt help` - Show this help message
- `@stride-gpt status` - Check your usage limits

### Free Tier Limits
- **20 analyses per month** per GitHub account
- **3 threats maximum** per analysis
- **Public repositories only**
- **Basic severity ratings** (Low/Medium/High)

### Want More?
Upgrade to a paid plan for:
- ✨ High-volume analysis plans
- 📊 DREAD risk scoring
- 🔒 Private repository support
- 🛠️ Detailed mitigation steps
- 🧠 State-of-the-art LLM access

[View Pricing →](https://stridegpt.ai/pricing)"""

        # Use appropriate method based on whether it's a PR or issue
        if is_pull_request:
            return self.github.create_comment(issue_number, body)
        else:
            return self.github.create_issue_comment(issue_number, body)

    async def post_status_comment(
        self, issue_number: int, usage: Dict[str, Any], is_pull_request: bool = True
    ) -> str:
        """Post usage status as a comment on issue or PR."""
        analyses_used = usage.get("analyses_used", 0)
        analyses_limit = usage.get("analyses_limit", 20)
        remaining = analyses_limit - analyses_used

        # Get trend emoji
        trend_emoji = self._get_trend_emoji(usage.get("usage_trend", "stable"))

        body = f"""## 📊 STRIDE GPT Usage Status

### Current Month
- **Analyses Used**: {analyses_used} of {analyses_limit}
- **Remaining**: {remaining}
- **Plan**: {usage.get("plan", "Free").title()}

### Billing Period  
- **Period**: {self._format_date(usage.get("period_start"))} to {self._format_date(usage.get("period_end"))}
- **Days Remaining**: {self._calculate_days_remaining(usage.get("period_end"))}

{self._get_usage_analytics_section(usage)}

{self._get_feature_access_section(usage)}

{self._get_account_info_section(usage)}

{self._get_upgrade_prompt() if usage.get("plan", "free").lower() == "free" else ""}"""

        # Use appropriate method based on whether it's a PR or issue
        if is_pull_request:
            return self.github.create_comment(issue_number, body)
        else:
            return self.github.create_issue_comment(issue_number, body)

    async def post_error_comment(
        self, issue_number: int, error_message: str, is_pull_request: bool = True
    ) -> str:
        """Post error message as a comment on issue or PR."""
        body = f"""## ❌ STRIDE GPT Error

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
            "critical": "🚨",
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢",
            "info": "ℹ️",
        }
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

        # Get current plan info
        try:
            if self.stride:
                current_usage = await self.stride.get_usage()
                plan_name = current_usage.get("plan", "free").title()
            else:
                plan_name = "Free"
        except Exception:
            plan_name = "Free"

        # Sort threats by severity (Critical first, Info last)
        sorted_threats = sorted(
            result.threats,
            key=lambda t: severity_order.get(t.get("severity", "medium").lower(), 2),
        )

        # Count threats by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for threat in sorted_threats:
            severity = threat.get("severity", "medium").lower()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Build comment
        lines = [
            f"## 🛡️ STRIDE GPT Threat Model Analysis ({plan_name} Tier)",
            "",
            "### Summary",
            f"- **Threats Found**: {result.threat_count} {'(free tier shows 3 max)' if result.is_limited else ''}",
            "- **Analysis Scope**: Changed files only",
            f"- **Severity Levels**: {severity_counts['critical']} Critical, {severity_counts['high']} High, {severity_counts['medium']} Medium, {severity_counts['low']} Low",
            "",
            "### Identified Threats",
            "",
        ]

        # Add each threat (already sorted by severity)
        for threat in sorted_threats:
            severity = threat.get("severity", "medium").lower()
            emoji = severity_emoji.get(severity, "🟡")

            # Only show file info if it's actually available and useful
            file_info_parts = []
            if threat.get("file") and threat.get("file") != "Unknown":
                file_line = threat.get("line", "")
                if file_line and file_line != "?":
                    file_info_parts.append(
                        f"**File**: `{threat.get('file')}:{file_line}`"
                    )
                else:
                    file_info_parts.append(f"**File**: `{threat.get('file')}`")

            lines.extend(
                [
                    f"#### {emoji} {severity.upper()}: {threat.get('title', 'Unknown Threat')}",
                    f"**Category**: {threat.get('category', 'Unknown')}",
                ]
                + file_info_parts
                + [
                    f"**Description**: {threat.get('description', 'No description provided')}",
                    "",
                ]
            )

        # Add limitation notice if provided by the API
        if result.limitation_notice:
            lines.extend(
                [
                    "---",
                    "",
                    f"⚠️ **{result.limitation_notice}**",
                    "",
                    "[Upgrade Now →](https://stridegpt.ai/pricing)",
                    "",
                ]
            )
        elif result.is_limited:
            # Fallback to previous behavior if no limitation notice is provided
            lines.extend(
                [
                    "---",
                    "",
                    "⚠️ **Free Tier Limit Reached**: Only 3 threats shown per analysis",
                    "",
                    "💡 **Upgrade to see all threats**: Get comprehensive analysis with enhanced threat modeling, DREAD scoring, and state-of-the-art LLMs for deeper insights.",
                    "",
                    "[Upgrade Now →](https://stridegpt.ai/pricing)",
                    "",
                ]
            )

        # Add upgrade prompt and usage footer
        lines.extend(["---", "", self._get_upgrade_prompt(), ""])

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

        # Generate appropriate messaging based on plan
        upgrade_section = self._get_no_threats_upgrade_section(plan_name.lower())
        
        return f"""## 🛡️ STRIDE GPT Threat Model Analysis ({plan_name} Tier)

### ✅ No Security Threats Detected

Great job! No obvious security threats were found in the changed files.

### Analysis Details
- **Files Analyzed**: Changed files in this PR
- **Analysis Type**: {"Basic" if plan_name.lower() == "free" else "Enhanced"} STRIDE methodology
- **Severity Levels**: {"Low/Medium/High" if plan_name.lower() in ["free", "starter"] else "Low/Medium/High/Critical with DREAD scoring"}

{upgrade_section}

{usage_footer}"""

    def _format_limit_reached_comment(self) -> str:
        """Format comment when usage limit is reached."""
        return """## 🛑 Monthly Analysis Limit Reached

You've used all 20 free analyses for this month. Your limit will reset at the beginning of next month.

### Continue Analyzing Today

Upgrade to a paid plan for:
- ✅ **High-volume analysis plans**
- ✅ **DREAD risk scoring**
- ✅ **State-of-the-art LLM access**
- ✅ **Detailed mitigation steps**
- ✅ **Private repository support**
- ✅ **Priority support**

### Pricing Plans
- **Starter** ($29/month): 500 analyses, all Pro features
- **Pro** ($99/month): 2,500 analyses, API access
- **Enterprise**: Custom pricing - [Contact us](https://stridegpt.ai/contact) for volume discounts

[Upgrade Now →](https://stridegpt.ai/pricing)"""

    def _get_upgrade_prompt(self) -> str:
        """Get upgrade prompt for free tier users."""
        return """### 📈 Want More Detailed Threat Modeling?
Upgrade to a paid plan for:
- ✨ DREAD risk scoring
- 🛠️ Detailed mitigation steps
- 🔒 Private repository support
- 🧠 State-of-the-art LLM access
- 📊 Risk prioritization

[Get Started →](https://stridegpt.ai/pricing)"""

    def _get_no_threats_upgrade_section(self, plan: str) -> str:
        """Get appropriate upgrade section for no threats found, based on plan."""
        if plan == "free":
            return """### 💡 Want Deeper Threat Modeling?

While no obvious threats were found, paid plans offer:
- 🔍 **Deep code analysis** with AI-powered pattern recognition
- 📊 **DREAD scoring** for risk prioritization  
- 🛠️ **Detailed remediation** guidance
- 🔒 **Private repository** support
- 🧠 **State-of-the-art LLMs** for deeper analysis

[Upgrade to Starter →](https://stridegpt.ai/pricing)"""
        elif plan == "starter":
            return """### 💡 Enhanced Analysis Available

Consider upgrading to Pro for:
- 🧠 **State-of-the-art LLMs** for deeper analysis
- 🛠️ **Detailed remediation** guidance  
- 📊 **Advanced risk analysis**
- 🔍 **Enhanced pattern recognition**

[Upgrade to Pro →](https://stridegpt.ai/pricing)"""
        elif plan == "pro":
            return """### ✨ Pro Analysis Complete

You're using our most advanced threat modeling capabilities:
- ✅ **State-of-the-art LLMs** enabled
- ✅ **DREAD scoring** available
- ✅ **Comprehensive analysis** complete
- ✅ **Advanced pattern recognition** applied

Need custom features? [Contact Enterprise Sales →](https://stridegpt.ai/contact)"""
        elif plan == "enterprise":
            return """### 🏢 Enterprise Analysis Complete

You're using our highest-tier threat modeling:
- ✅ **Custom analysis rules** applied
- ✅ **Enterprise-grade LLMs** enabled
- ✅ **Advanced threat modeling** complete
- ✅ **Dedicated support** available

[Contact your account manager](https://stridegpt.ai/contact) for additional customizations."""
        else:
            # Fallback for unknown plans
            return """### 📊 Analysis Complete

Your current plan provides comprehensive threat modeling. No obvious security threats were found."""

    async def _get_usage_footer(self, usage_info: Dict[str, Any]) -> str:
        """Get usage footer for comments with real-time data."""
        try:
            # Fetch real-time usage data if stride client is available
            if self.stride:
                current_usage = await self.stride.get_usage()
                analyses_used = current_usage.get("analyses_used", 0)
                analyses_limit = current_usage.get("analyses_limit", 20)
                plan = current_usage.get("plan", "free").title()
            else:
                # Fallback to metadata from analysis result
                analyses_used = usage_info.get("analyses_used", 0)
                analyses_limit = usage_info.get("analyses_limit", 20)
                plan = usage_info.get("plan", "free").title()

            return f"\n*You've used {analyses_used} of {analyses_limit} {plan.lower()} analyses this month*"
        except Exception:
            # Fallback to original behavior on error
            analyses_used = usage_info.get("analyses_used", 0)
            analyses_limit = usage_info.get("analyses_limit", 20)
            return f"\n*You've used {analyses_used} of {analyses_limit} free analyses this month*"

    def _format_date(self, date_str: str) -> str:
        """Format date for user-friendly display."""
        if date_str and date_str != "N/A":
            try:
                # Handle various date formats
                if isinstance(date_str, str):
                    # Remove Z and replace with +00:00 for UTC
                    if date_str.endswith("Z"):
                        date_str = date_str.replace("Z", "+00:00")
                    elif not date_str.endswith("+00:00") and not date_str.endswith(
                        "UTC"
                    ):
                        date_str = date_str + "+00:00"

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
                    if period_end.endswith("Z"):
                        period_end = period_end.replace("Z", "+00:00")
                    elif not period_end.endswith("+00:00") and not period_end.endswith(
                        "UTC"
                    ):
                        period_end = period_end + "+00:00"

                    end_date = datetime.fromisoformat(period_end)
                else:
                    end_date = period_end  # Already a datetime object

                now = (
                    datetime.now(end_date.tzinfo) if end_date.tzinfo else datetime.now()
                )
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

    def _get_trend_emoji(self, trend: str) -> str:
        """Get emoji for usage trend."""
        trend_map = {"up": "⬆️", "down": "⬇️", "stable": "➡️"}
        return trend_map.get(trend, "➡️")

    def _get_usage_analytics_section(self, usage: Dict[str, Any]) -> str:
        """Generate usage analytics section."""
        daily_avg = usage.get("daily_average")
        projected = usage.get("projected_usage")
        trend = usage.get("usage_trend", "stable")
        trend_emoji = self._get_trend_emoji(trend)

        if daily_avg is not None and projected is not None:
            return f"""### 📈 Usage Analytics
- **Daily Average**: {daily_avg} analyses/day
- **Projected Month**: {projected} analyses {trend_emoji}
- **Usage Trend**: {trend.title()}"""
        return ""

    def _get_feature_access_section(self, usage: Dict[str, Any]) -> str:
        """Generate feature access summary."""
        plan = usage.get("plan", "free").lower()

        # Create feature list
        feature_lines = []

        # Always available features
        feature_lines.append("✅ Basic threat modeling")
        feature_lines.append("✅ STRIDE methodology")

        # Plan-specific features
        if plan == "free":
            feature_lines.append("✅ Simple severity ratings")
            feature_lines.append("🔒 DREAD scoring (Starter+ feature)")
            feature_lines.append("🔒 State-of-the-art LLMs (Pro+ feature)")
            feature_lines.append("🔒 Detailed mitigations (Pro+ feature)")
            feature_lines.append("🔒 Private repositories (Starter+ feature)")
        elif plan == "starter":
            feature_lines.append("✅ DREAD risk scoring")
            feature_lines.append("✅ Advanced severity analysis")
            feature_lines.append("✅ Private repositories")
            feature_lines.append("🔒 State-of-the-art LLMs (Pro+ feature)")
            feature_lines.append("🔒 Detailed mitigations (Pro+ feature)")
        elif plan == "pro":
            feature_lines.append("✅ DREAD risk scoring")
            feature_lines.append("✅ State-of-the-art LLM access")
            feature_lines.append("✅ Detailed mitigation steps")
            feature_lines.append("✅ Private repositories")
            feature_lines.append("🔒 Custom rules (Enterprise feature)")
        elif plan == "enterprise":
            feature_lines.append("✅ All Pro features included")
            feature_lines.append("✅ Custom volume pricing")
            feature_lines.append("✅ Dedicated support")
            feature_lines.append("📞 Contact us for custom requirements")

        features_text = "\n".join([f"- {line}" for line in feature_lines])

        return f"""### 🔓 Feature Access
{features_text}"""

    def _get_account_info_section(self, usage: Dict[str, Any]) -> str:
        """Generate account information section."""
        api_key_created = usage.get("api_key_created")
        last_usage = usage.get("last_usage")

        lines = []

        if api_key_created:
            created_date = self._format_date(api_key_created)
            lines.append(f"- **API Key Created**: {created_date}")

        if last_usage:
            last_used_date = self._format_date(last_usage)
            lines.append(f"- **Last Activity**: {last_used_date}")

        if lines:
            account_text = "\n".join(lines)
            return f"""### 👤 Account Details
{account_text}"""

        return """### 👤 Account Details
- **Account**: Active"""
