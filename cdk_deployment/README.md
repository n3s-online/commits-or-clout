# CDK Deployment

This directory contains the AWS CDK application for deploying and scheduling the Lambda function.

## Structure

- `app.py`: The main CDK application
- `requirements.txt`: Python dependencies for the CDK application

## Setup

### Python Environment Setup

1. Create a separate virtual environment for the CDK application:
   ```
   python -m venv cdk-venv
   ```

2. Activate the virtual environment:
   - On Windows: `cdk-venv\Scripts\activate`
   - On macOS/Linux: `source cdk-venv/bin/activate`

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. When adding new CDK dependencies:
   ```
   pip install package-name
   pip freeze > requirements.txt
   ```

### AWS CDK Setup

1. Bootstrap your AWS environment (if not already done):
   ```
   cdk bootstrap
   ```

## Deployment

To deploy the Lambda function:

1. Make sure your AWS credentials are configured
2. Run:
   ```
   cdk deploy --app "python app.py"
   ```

This will:
- Package and deploy the Lambda function from the `lambda_function` directory
- Set up a CloudWatch Events rule to trigger the Lambda every 30 minutes 