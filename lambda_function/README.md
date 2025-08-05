# Lambda Function

This directory contains the AWS Lambda function code.

## Structure

- `src/lambda_handler.py`: The main Lambda function handler
- `src/generate_historical_data.py`: Script to generate historical data
- `src/utils.py`: Utility functions for HTML rendering
- `src/bluesky_utils.py`: Functions for interacting with the Bluesky API
- `src/youtube_utils.py`: Functions for fetching YouTube subscriber counts
- `requirements.txt`: Python dependencies for the Lambda function

## Features

- Fetches GitHub commits from all branches across all repositories
- Counts unique commits to avoid duplicates when the same commit appears in multiple branches
- Tracks historical data for commits and social media followers
- Generates a ratio of commits to social media followers

## Development

### Python Environment Setup

1. Create a virtual environment for the Lambda function:
   ```
   python -m venv lambda-venv
   ```

2. Activate the virtual environment:
   - On Windows: `lambda-venv\Scripts\activate`
   - On macOS/Linux: `source lambda-venv/bin/activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. When adding new dependencies:
   ```
   pip install package-name
   pip freeze > requirements.txt
   ```

### GitHub Token Setup

To fetch GitHub commits and repository data, you'll need to set up a GitHub Personal Access Token:

1. **Create a GitHub Personal Access Token:**
   - Go to [GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)](https://github.com/settings/tokens)
   - Click "Generate new token (classic)"
   - Give it a descriptive name (e.g., "Commits or Clout Lambda")
   - Select the following scopes:
     - `repo` (Full control of private repositories) - for accessing repository data
     - `read:org` (Read org and team membership) - if accessing organization repositories
   - Click "Generate token"
   - **Important:** Copy the token immediately as you won't be able to see it again

2. **Set up the token for local development:**
   ```bash
   export GITHUB_TOKEN="your_personal_access_token_here"
   ```
   
   Or add it to your shell profile file (`.bashrc`, `.zshrc`, etc.):
   ```bash
   echo 'export GITHUB_TOKEN="your_personal_access_token_here"' >> ~/.zshrc
   source ~/.zshrc
   ```

3. **For Lambda deployment:**
   - The token should be configured as an environment variable in your Lambda function
   - This is typically handled through the CDK deployment configuration
   - Never commit the actual token value to your repository

### GitHub Organization Support

The application now supports fetching repositories from both your personal GitHub account and a GitHub organization. This allows you to track commits across all repositories you have access to.

**Configuration:**
- Set the `GITHUB_ORGANIZATION` environment variable to your organization name
- The GitHub token must have appropriate permissions to access organization repositories
- Required token scopes:
  - `repo` - for accessing repository data
  - `read:org` - for accessing organization repositories

**How it works:**
- The application fetches repositories from both your personal account (`/user/repos`) and the specified organization (`/orgs/{org}/repos`)
- All commits are filtered by your GitHub username using the `author` parameter
- This ensures only your commits are counted, even from organization repositories

**Example:**
```bash
export GITHUB_ORGANIZATION="your-org-name"
```

**AWS Parameter Store:**
For production deployment, add the organization name to AWS Systems Manager Parameter Store:
```bash
aws ssm put-parameter --name "/commits-or-clout/github-organization" --type "String" --value "your-org-name"
```

### Lambda Development

1. Add your Lambda function logic in `src/lambda_handler.py`
2. Add any required dependencies to `requirements.txt`

## Deployment

This Lambda function is deployed using the CDK application in the `cdk_deployment` directory.