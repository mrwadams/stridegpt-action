# STRIDE GPT Threat Modeling Action

AI-powered threat modeling for your GitHub repositories using the STRIDE methodology.

## Features

- **STRIDE threat detection** using AI-powered analysis
- **Severity ratings** (Critical/High/Medium/Low/Info)
- **Markdown formatted reports** in comments
- **Support for public repositories**
- **Analysis of changed files in PRs**
- **Threat modeling of proposed features in issues**
- **Multiple trigger modes** (manual, PR, comment)

## Status

✅ **Operational** - Ready for use  
✅ **GitHub Actions** - Published at `mrwadams/stridegpt-action@main`

## Quick Start

### 1. Get Your API Key

Contact the development team for an API key.

### 2. Add the API Key to Your Repository

Add your API key as a repository secret:
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `STRIDE_API_KEY`
4. Value: Your provided API key

### 3. Create a Workflow

Create `.github/workflows/threat-analysis.yml`:

```yaml
name: STRIDE GPT Threat Modeling

on:
  workflow_dispatch:  # Manual trigger
  pull_request:       # Auto-trigger on PRs
    types: [opened, synchronize]

jobs:
  threat-analysis:
    runs-on: ubuntu-latest
    name: STRIDE GPT Threat Modeling
    
    steps:
    - name: Run STRIDE GPT Analysis
      uses: mrwadams/stridegpt-action@main
      with:
        stride-api-key: ${{ secrets.STRIDE_API_KEY }}
        github-token: ${{ secrets.GITHUB_TOKEN }}
        trigger-mode: manual  # Use 'manual' for workflow_dispatch, 'pr' for pull_request
```

### 4. Run Analysis

- **Manual:** Go to Actions tab → "STRIDE GPT Threat Modeling" → "Run workflow"
- **Automatic:** Create or update a pull request
- **Comment:** Use `@stride-gpt analyze` in PR or issue comments

## Analysis Types

The action automatically detects the context and performs different types of analysis:

### 🔍 **Code Analysis** (PR Comments)
When you comment `@stride-gpt analyze` on a **pull request**, the action:
- Analyzes the changed code files in the PR
- Identifies security vulnerabilities in the code
- Reports threats with specific file locations and line numbers

### 💡 **Feature Threat Modeling** (Issue Comments)  
When you comment `@stride-gpt analyze` on an **issue**, the action:
- Analyzes the feature description in the issue body
- Identifies potential security threats in the proposed feature
- Provides conceptual threat modeling before code is written

**Perfect for:** Getting security feedback on proposed features, architecture changes, or new functionality during the planning phase.

## Usage Examples

### Comment-Triggered Threat Modeling

Run threat modeling when someone comments `@stride-gpt analyze`:

```yaml
name: STRIDE GPT Threat Model Analysis on Comment

on:
  issue_comment:
    types: [created]

jobs:
  stride-threat-modeling:
    if: github.event.issue.pull_request && contains(github.event.comment.body, '@stride-gpt')
    runs-on: ubuntu-latest
    steps:
      - name: Run STRIDE GPT Threat Modeling
        uses: mrwadams/stridegpt-action@main
        with:
          stride-api-key: ${{ secrets.STRIDE_API_KEY }}
          trigger-mode: comment
```

### Automatic PR Threat Modeling

Automatically run threat modeling on all new pull requests:

```yaml
name: Automatic STRIDE GPT Threat Model Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  threat-modeling:
    runs-on: ubuntu-latest
    steps:
      - name: Run STRIDE GPT Threat Modeling
        uses: mrwadams/stridegpt-action@main
        with:
          stride-api-key: ${{ secrets.STRIDE_API_KEY }}
          trigger-mode: pr
```

### Manual Repository Threat Modeling

Run full repository threat modeling manually:

```yaml
name: Manual STRIDE GPT Threat Model Scan

on:
  workflow_dispatch:

jobs:
  threat-modeling:
    runs-on: ubuntu-latest
    steps:
      - name: Run STRIDE GPT Threat Modeling
        uses: mrwadams/stridegpt-action@main
        with:
          stride-api-key: ${{ secrets.STRIDE_API_KEY }}
          trigger-mode: manual
```

## Available Commands

- `@stride-gpt analyze` - Run threat modeling (context-aware):
  - **In PR comments:** Models threats in changed code files  
  - **In issue comments:** Models threats for proposed features

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `stride-api-key` | Your STRIDE GPT API key | Yes | - |
| `github-token` | GitHub token for API access | Yes | `${{ github.token }}` |
| `trigger-mode` | How the action is triggered (`comment`, `pr`, or `manual`) | No | `comment` |

## Outputs

| Output | Description |
|--------|-------------|
| `threat-count` | Number of threats identified |
| `report-url` | URL to the analysis comment |

## Example Analysis Output

```markdown
## 🛡️ STRIDE GPT Threat Model Analysis

### Summary
- **Threats Found**: 3
- **Analysis Scope**: Changed files
- **Severity Levels**: 0 Critical, 1 High, 2 Medium, 0 Low

### Identified Threats

#### 🔴 HIGH: Potential SQL Injection
**Category**: Tampering
**File**: `src/database.py:45`
**Description**: User input appears to be directly concatenated into SQL query

#### 🟡 MEDIUM: Missing Authentication Check
**Category**: Spoofing
**File**: `src/api/endpoints.py:23`
**Description**: API endpoint lacks authentication middleware
```

## Limitations

- Public repositories only
- PR analysis limited to changed files
- Issue analysis requires feature description in issue body

## Support

- 🐛 [Report Issues](https://github.com/mrwadams/stridegpt-action/issues)

## License

This action is provided under the MIT License. See [LICENSE](LICENSE) for details.

---

Made with ❤️ by the STRIDE GPT team.