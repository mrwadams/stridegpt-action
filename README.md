# STRIDE-GPT Security Analysis Action

Free AI-powered security threat modeling for your GitHub repositories using the STRIDE methodology.

## Features

### 🎁 Free Tier Includes
- **50 analyses per month** per GitHub account
- **Basic STRIDE threat detection** (up to 5 threats per analysis)
- **Simple severity ratings** (Low/Medium/High)
- **Markdown formatted reports** in PR comments
- **Support for public repositories**
- **Analysis of changed files in PRs**

### 🚀 Premium Features (Upgrade Required)
- DREAD risk scoring
- Attack tree visualization  
- Detailed mitigation recommendations
- Private repository support
- Full repository analysis
- Compliance mapping
- Priority support

## 📋 Current Status

✅ **Fully Operational** - End-to-end system working perfectly  
✅ **API Integration** - Connected to Railway-hosted STRIDE-GPT API  
✅ **Authentication** - API key system working  
✅ **Threat Detection** - Successfully analyzing repositories and finding security threats  
✅ **Multiple Trigger Modes** - Manual, PR, and comment triggers all working  
✅ **GitHub Actions** - Published and ready for production use  
✅ **Test Results** - Successfully detected 5 security threats in test repository  

**Action URL:** `mrwadams/stridegpt-action@main`  
**API Endpoint:** `https://stridegpt-api-production.up.railway.app`

## Quick Start

### 1. Get Your Free API Key

**For Development/Testing:**
Contact the development team for a test API key.

**For Production:**
Visit [https://stridegpt-api-production.up.railway.app](https://stridegpt-api-production.up.railway.app) to register and get your free API key.

### 2. Add the API Key to Your Repository

Add your API key as a repository secret:
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `STRIDE_API_KEY`
4. Value: Your API key from stridegpt.ai

### 3. Create a Workflow

Create `.github/workflows/security-analysis.yml`:

```yaml
name: STRIDE-GPT Security Analysis

on:
  workflow_dispatch:  # Manual trigger
  pull_request:       # Auto-trigger on PRs
    types: [opened, synchronize]

jobs:
  security-analysis:
    runs-on: ubuntu-latest
    name: STRIDE Threat Modeling
    
    steps:
    - name: Run STRIDE-GPT Analysis
      uses: mrwadams/stridegpt-action@main
      with:
        stride-api-key: ${{ secrets.STRIDE_API_KEY }}
        github-token: ${{ secrets.GITHUB_TOKEN }}
        trigger-mode: manual  # Use 'manual' for workflow_dispatch, 'pr' for pull_request
```

### 4. Run Analysis

- **Manual:** Go to Actions tab → "STRIDE-GPT Security Analysis" → "Run workflow"
- **Automatic:** Create or update a pull request
- **Comment:** In PR comments, use `@stride-gpt analyze`

## Usage Examples

### Comment-Triggered Analysis

Analyze when someone comments `@stride-gpt analyze`:

```yaml
name: Security Analysis on Comment

on:
  issue_comment:
    types: [created]

jobs:
  stride-analysis:
    if: github.event.issue.pull_request && contains(github.event.comment.body, '@stride-gpt')
    runs-on: ubuntu-latest
    steps:
      - uses: mrwadams/stridegpt-action@main
        with:
          stride-api-key: ${{ secrets.STRIDE_API_KEY }}
          trigger-mode: comment
```

### Automatic PR Analysis

Automatically analyze all new pull requests:

```yaml
name: Automatic Security Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  security-check:
    runs-on: ubuntu-latest
    steps:
      - uses: mrwadams/stridegpt-action@main
        with:
          stride-api-key: ${{ secrets.STRIDE_API_KEY }}
          trigger-mode: pr
```

### Manual Repository Analysis

Run full repository analysis manually:

```yaml
name: Manual Security Scan

on:
  workflow_dispatch:
    inputs:
      pr-number:
        description: 'Pull Request number to analyze'
        required: true
        type: number

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: mrwadams/stride-gpt-action@v1
        with:
          stride-api-key: ${{ secrets.STRIDE_API_KEY }}
          trigger-mode: 'pr'
        env:
          PR_NUMBER: ${{ inputs.pr-number }}
```

## Available Commands

- `@stride-gpt analyze` - Run security analysis on changed files
- `@stride-gpt help` - Show available commands and limits
- `@stride-gpt status` - Check your current usage

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `stride-api-key` | Your STRIDE-GPT API key | Yes | - |
| `github-token` | GitHub token for API access | Yes | `${{ github.token }}` |
| `trigger-mode` | How the action is triggered (`comment` or `pr`) | No | `comment` |

## Outputs

| Output | Description |
|--------|-------------|
| `threat-count` | Number of security threats identified |
| `report-url` | URL to the analysis comment |

## Example Analysis Output

```markdown
## 🛡️ STRIDE Security Analysis (Free Tier)

### Summary
- **Threats Found**: 3 of 5 max
- **Analysis Scope**: Changed files only
- **Severity Levels**: 1 High, 2 Medium

### Identified Threats

#### 🔴 HIGH: Potential SQL Injection
**Category**: Tampering
**File**: `src/database.py:45`
**Description**: User input appears to be directly concatenated into SQL query

#### 🟡 MEDIUM: Missing Authentication Check
**Category**: Spoofing
**File**: `src/api/endpoints.py:23`
**Description**: API endpoint lacks authentication middleware

---

*You've used 3 of 50 free analyses this month*
```

## Limitations (Free Tier)

- 50 analyses per month per GitHub account
- Maximum 5 threats shown per analysis
- Public repositories only
- Basic severity ratings only
- No DREAD scoring
- No attack trees
- No detailed mitigations

## Upgrade to Pro

Get advanced features with STRIDE-GPT Pro:

- ✨ Unlimited analyses
- 🌳 Attack tree visualization
- 📊 DREAD risk scoring
- 🔒 Private repository support
- 🛠️ Detailed remediation guidance
- 📋 Compliance mapping
- 🚀 Priority support

[View Pricing →](https://stridegpt.ai/pricing)

## Support

- 📖 [Documentation](https://stridegpt.ai/docs)
- 💬 [Community Forum](https://community.stridegpt.ai)
- 📧 [Email Support](mailto:support@stridegpt.ai)
- 🐛 [Report Issues](https://github.com/mrwadams/stride-gpt-action/issues)

## License

This action is provided under the MIT License. See [LICENSE](LICENSE) for details.

---

Made with ❤️ by the STRIDE-GPT team. [Get your free API key →](https://stridegpt.ai)