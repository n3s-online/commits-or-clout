# Commits or Clout

A web application that tracks and visualizes the relationship between GitHub commits and social media followers (Twitter/X, YouTube, Bluesky). The project is designed to run as a serverless application on AWS, updating metrics regularly and displaying them on a static website.

## Project Overview

This project tracks a developer's GitHub commit activity and social media following, calculating a "commits-to-followers ratio" that visualizes the balance between technical productivity and social media presence. The application updates metrics regularly and displays historical data through an interactive web interface.

## Project Structure

The project is organized into two main components:

### 1. Lambda Function (`/lambda_function`)

Contains the core application logic that runs on AWS Lambda:

- **`src/`**: Source code directory
  - `lambda_handler.py`: Main Lambda function that fetches GitHub commits, social media followers, and generates the HTML
  - `utils.py`: Utility functions for data processing and HTML rendering
  - `bluesky_utils.py`: Functions for interacting with the Bluesky API
  - `youtube_utils.py`: Functions for fetching YouTube subscriber counts
  - `locally_render.py`: Script for local development and testing
  - `generate_historical_data.py`: Script to generate historical data
  - `local_runner.py`: Local development runner

- **Configuration Files**:
  - `requirements.txt`: Python dependencies
  - `.env` and `.env.example`: Environment variables for local development
  - `Dockerfile`: Container definition for Lambda deployment

- **Assets**:
  - `index.html`: Template for the website
  - `historical_data.json`: Cached historical metrics
  - `favicons/`: Website favicon assets

### 2. CDK Deployment (`/cdk_deployment`)

Contains the AWS Cloud Development Kit (CDK) code for infrastructure deployment:

- `app.py`: Main CDK application defining all AWS resources
- `requirements.txt`: Python dependencies for the CDK application
- `deploy.sh`: Automated deployment script
- `DEPLOYMENT.md`: Detailed deployment documentation

## Deployment Scripts

### Quick Deployment

The easiest way to deploy is using the automated script:

```bash
cd cdk_deployment
./deploy.sh
```

### Check Deployment Status

From the project root:

```bash
./check-deployment.sh
```

Or from the cdk_deployment directory:

```bash
./deploy.sh status
```

### Deployment Commands

```bash
# Deploy the application
./deploy.sh

# Check deployment status
./deploy.sh status

# Show help
./deploy.sh help
```

## Core Functionality

1. **Data Collection**:
   - Fetches GitHub commit count since January 1st of the current year
   - Retrieves follower counts from Twitter/X
   - Gets subscriber counts from YouTube
   - Collects follower data from Bluesky

2. **Data Processing**:
   - Calculates the ratio of commits to followers
   - Updates historical data with new metrics
   - Stores data in S3 for persistence

3. **Visualization**:
   - Renders an HTML dashboard with current metrics
   - Displays historical trends through charts
   - Updates the website automatically

## Infrastructure

The application is deployed on AWS with the following components:

- **AWS Lambda**: Runs the core application logic on a schedule
- **Amazon S3**: Hosts the static website and stores historical data
- **Amazon CloudFront**: Provides CDN capabilities for the website
- **AWS Systems Manager Parameter Store**: Securely stores API keys and credentials
- **Amazon CloudWatch Events**: Schedules regular updates (every 30 minutes)
- **AWS IAM**: Manages permissions and security

## Development Workflow

1. **Local Development**:
   - Use the local runner scripts to test functionality
   - Configure environment variables in `.env` file
   - Generate test data with the historical data generator

2. **Deployment**:
   - Use the automated `deploy.sh` script for easy deployment
   - The Lambda function is packaged and deployed automatically
   - CloudFront distribution is set up for the website

## Getting Started

1. Set up Python virtual environments for both the Lambda function and CDK deployment
2. Configure required API keys and credentials in AWS Systems Manager
3. Deploy using the automated script: `cd cdk_deployment && ./deploy.sh`
4. The website will be available through the CloudFront distribution URL

## Security Considerations

- API keys and credentials are stored in AWS Systems Manager Parameter Store
- S3 bucket is configured with appropriate public access settings for website hosting
- IAM roles are set up with least privilege principles

## Maintenance

- The Lambda function runs automatically on a schedule
- Historical data is preserved and backed up
- Alerts are sent to Discord for any errors or issues

## Documentation

- `cdk_deployment/DEPLOYMENT.md`: Detailed deployment guide
- `cdk_deployment/README.md`: CDK-specific documentation
- `lambda_function/README.md`: Lambda function documentation 