#!/usr/bin/env python3
"""
Local runner for the Lambda function.
This script allows you to test the Lambda handler locally by:
1. Loading environment variables from a .env file
2. Creating mock event and context objects
3. Calling the Lambda handler function
4. Displaying the results
"""

import os
import json
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging BEFORE importing the lambda_handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Find and load the .env file BEFORE importing the lambda_handler
current_dir = Path(__file__).parent
project_root = current_dir.parent
env_path = project_root / '.env'

print(f"Looking for .env file at: {env_path}")
if env_path.exists():
    print(f".env file found!")
    # Load environment variables from .env file
    load_dotenv(dotenv_path=env_path, override=True)
    
    # Manually load environment variables to ensure they're set
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                    except ValueError:
                        # Skip lines that don't have a key=value format
                        continue
    except Exception as e:
        print(f"Error manually loading .env file: {e}")
else:
    print(f"ERROR: .env file not found at {env_path}")
    print("Current directory structure:")
    for item in project_root.iterdir():
        print(f"  {item}")
    sys.exit(1)

# Now import the lambda_handler after environment variables are set
from lambda_handler import handler

class MockContext:
    """Mock Lambda context object"""
    def __init__(self):
        self.function_name = "local-lambda-runner"
        self.function_version = "$LATEST"
        self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:local-lambda-runner"
        self.memory_limit_in_mb = 128
        self.aws_request_id = "local-request-id"
        self.log_group_name = "/aws/lambda/local-lambda-runner"
        self.log_stream_name = "2023/01/01/[$LATEST]abcdef123456"
        self.identity = None
        self.client_context = None
        self.remaining_time_in_millis = 300000  # 5 minutes

    def get_remaining_time_in_millis(self):
        return self.remaining_time_in_millis

def main():
    """Main function to run the Lambda handler locally"""
    # Check for required environment variables
    required_vars = ["GITHUB_TOKEN", "GITHUB_USERNAME", "TWITTER_BEARER_TOKEN", 
                     "TWITTER_USERNAME", "S3_BUCKET"]
    
    print("\nEnvironment variables:")
    for var in required_vars:
        value = os.environ.get(var)
        # Print first few characters if exists, otherwise "Not set"
        if value:
            # Mask sensitive values
            if var in ["GITHUB_TOKEN", "TWITTER_BEARER_TOKEN", "AWS_SECRET_ACCESS_KEY"]:
                display_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"  {var}: {display_value}")
        else:
            print(f"  {var}: Not set")
    
    # Create a mock event (empty for simplicity, but you can customize this)
    event = {}
    
    # Create a mock context
    context = MockContext()
    
    print("\nRunning Lambda handler locally...")
    print("-" * 50)
    
    # Call the Lambda handler
    try:
        result = handler(event, context)
        
        # Pretty print the result
        print("\nLambda execution result:")
        print("-" * 50)
        print(f"Status Code: {result['statusCode']}")
        
        # Parse and pretty print the body
        body = json.loads(result['body'])
        print("Body:")
        print(json.dumps(body, indent=2))
        
        if result['statusCode'] == 200:
            print("\n✅ Lambda executed successfully!")
        else:
            print("\n❌ Lambda execution failed!")
    except Exception as e:
        print(f"\n❌ Error executing Lambda: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 