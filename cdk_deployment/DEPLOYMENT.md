# Deployment Guide

This guide explains how to deploy the Commits or Clout application using the automated deployment script.

## Prerequisites

Before deploying, ensure you have the following installed:

1. **AWS CLI** - Configured with appropriate credentials
2. **CDK CLI** - Install with `npm install -g aws-cdk`
3. **Python 3.9+** - For running the CDK application
4. **Docker** - For building the Lambda container image

## Quick Deployment

The easiest way to deploy is using the automated script:

```bash
cd cdk_deployment
./deploy.sh
```

This script will:
- ✅ Check AWS credentials
- ✅ Verify CDK installation
- ✅ Set up Python virtual environment
- ✅ Install dependencies
- ✅ Bootstrap CDK (if needed)
- ✅ Deploy the application
- ✅ Show deployment information

## Manual Deployment

If you prefer to deploy manually or need to troubleshoot:

### 1. Set up the environment

```bash
cd cdk_deployment

# Create virtual environment
python3 -m venv cdk-venv

# Activate virtual environment
source cdk-venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Bootstrap CDK (first time only)

```bash
# Get your AWS account ID
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

# Bootstrap CDK
cdk bootstrap aws://$ACCOUNT/us-east-1
```

### 3. Deploy the application

```bash
# Synthesize to check for errors
cdk synth --app "python app.py"

# Deploy
cdk deploy --app "python app.py" --require-approval never
```

## Deployment Script Commands

The `deploy.sh` script supports several commands:

```bash
# Deploy the application (default)
./deploy.sh

# Check deployment status
./deploy.sh status

# Show help
./deploy.sh help
```

## What Gets Deployed

The deployment creates the following AWS resources:

### Core Infrastructure
- **S3 Bucket** - Hosts the static website
- **CloudFront Distribution** - CDN with HTTPS
- **SSL Certificate** - For `commits.willness.dev`
- **Lambda Function** - Runs every 30 minutes to update metrics

### Supporting Resources
- **IAM Roles** - Permissions for Lambda and deployment
- **CloudWatch Events** - Schedules Lambda execution
- **Systems Manager Parameters** - Store API keys securely

## Configuration

### Required Parameters

The application requires several AWS Systems Manager parameters to be configured:

```bash
# GitHub Configuration
aws ssm put-parameter --name "/commits-or-clout/github-token" --type "SecureString" --value "your-github-token"
aws ssm put-parameter --name "/commits-or-clout/github-username" --type "String" --value "your-github-username"
aws ssm put-parameter --name "/commits-or-clout/github-organization" --type "String" --value "your-org-name"
aws ssm put-parameter --name "/commits-or-clout/github-token-org" --type "SecureString" --value "your-org-token"

# Twitter Configuration
aws ssm put-parameter --name "/commits-or-clout/twitter-bearer-token" --type "SecureString" --value "your-twitter-token"
aws ssm put-parameter --name "/commits-or-clout/twitter-username" --type "String" --value "your-twitter-username"

# YouTube Configuration
aws ssm put-parameter --name "/commits-or-clout/youtube-api-key" --type "SecureString" --value "your-youtube-api-key"
aws ssm put-parameter --name "/commits-or-clout/youtube-channel-id" --type "String" --value "your-channel-id"

# Bluesky Configuration
aws ssm put-parameter --name "/commits-or-clout/bluesky-api-key" --type "SecureString" --value "your-bluesky-token"
aws ssm put-parameter --name "/commits-or-clout/bluesky-username" --type "String" --value "your-bluesky-username"

# Discord Configuration
aws ssm put-parameter --name "/commits-or-clout/discord-webhook-url" --type "SecureString" --value "your-discord-webhook"
```

### DNS Configuration

After deployment, configure your DNS provider to point `commits.willness.dev` to the CloudFront distribution.

## Monitoring

### Check Deployment Status

```bash
./deploy.sh status
```

### View CloudFormation Stack

```bash
aws cloudformation describe-stacks --stack-name CommitsOrCloutStack --region us-east-1
```

### View Lambda Logs

```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/CommitsOrCloutUpdater" --region us-east-1
```

### Test Lambda Function

```bash
aws lambda invoke --function-name CommitsOrCloutUpdater --region us-east-1 response.json
```

## Troubleshooting

### Common Issues

1. **CDK Bootstrap Required**
   ```
   Error: This stack uses assets, so the toolkit stack must be deployed to the environment
   ```
   Solution: Run `cdk bootstrap` first

2. **AWS Credentials Not Configured**
   ```
   Error: Unable to locate credentials
   ```
   Solution: Run `aws configure` to set up credentials

3. **Docker Not Running**
   ```
   Error: Cannot connect to the Docker daemon
   ```
   Solution: Start Docker Desktop

4. **SSL Certificate Validation**
   - Check your email for the certificate validation link
   - Click the link to validate the certificate

### Rollback

To rollback to a previous deployment:

```bash
cdk rollback --app "python app.py"
```

### Destroy Stack

To completely remove the deployment:

```bash
cdk destroy --app "python app.py"
```

## Security Notes

- API keys are stored securely in AWS Systems Manager Parameter Store
- The S3 bucket is configured for public read access (required for website hosting)
- IAM roles follow the principle of least privilege
- All communication uses HTTPS

## Cost Optimization

The deployment uses serverless resources to minimize costs:
- Lambda function only runs when needed (every 30 minutes)
- S3 storage costs are minimal for a static website
- CloudFront provides cost-effective CDN

Estimated monthly cost: $1-5 USD (depending on usage) 