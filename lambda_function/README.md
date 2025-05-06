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

### Lambda Development

1. Add your Lambda function logic in `src/lambda_handler.py`
2. Add any required dependencies to `requirements.txt`

## Deployment

This Lambda function is deployed using the CDK application in the `cdk_deployment` directory.