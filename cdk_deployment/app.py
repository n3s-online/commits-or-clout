#!/usr/bin/env python3
import os
import subprocess
import shutil
import tempfile
from aws_cdk import (
    App,
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_s3 as s3,
    aws_ssm as ssm,
    aws_iam as iam,
)
from constructs import Construct

class CommitsOrCloutStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create an S3 bucket for storing the HTML file
        website_bucket = s3.Bucket(
            self,
            "CommitsOrCloutWebsite",
            removal_policy=RemovalPolicy.DESTROY,  # For development; use RETAIN for production
            auto_delete_objects=True,  # For development; remove for production
            website_index_document="index.html",
            public_read_access=True,  # Allow public access to read the website
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            )
        )

        # Define parameter names
        github_token_param_name = "/commits-or-clout/github-token"
        github_username_param_name = "/commits-or-clout/github-username"
        twitter_bearer_token_param_name = "/commits-or-clout/twitter-bearer-token"
        twitter_username_param_name = "/commits-or-clout/twitter-username"

        # Create a temporary directory for Lambda code with dependencies
        temp_dir = tempfile.mkdtemp()
        try:
            # Copy Lambda source code to temp directory
            lambda_src_dir = os.path.abspath("../lambda_function/src")
            for item in os.listdir(lambda_src_dir):
                src_item = os.path.join(lambda_src_dir, item)
                dst_item = os.path.join(temp_dir, item)
                if os.path.isdir(src_item):
                    shutil.copytree(src_item, dst_item)
                else:
                    shutil.copy2(src_item, dst_item)
            
            # Install dependencies to the temp directory
            requirements_file = os.path.abspath("../lambda_function/requirements.txt")
            subprocess.check_call([
                "pip", "install", 
                "-r", requirements_file,
                "--target", temp_dir,
                "--no-user"
            ])
            
            # Define the Lambda function with dependencies included
            lambda_function = _lambda.Function(
                self, 
                "CommitsOrCloutUpdater",
                runtime=_lambda.Runtime.PYTHON_3_9,
                code=_lambda.Code.from_asset(temp_dir),
                handler="lambda_handler.handler",
                timeout=Duration.seconds(120),
                memory_size=128,
                description="Lambda function that updates the CommitsOrClout website",
                environment={
                    "S3_BUCKET": website_bucket.bucket_name,
                    "S3_KEY": "index.html",
                    "GITHUB_TOKEN_PARAM_NAME": github_token_param_name,
                    "GITHUB_USERNAME_PARAM_NAME": github_username_param_name,
                    "TWITTER_BEARER_TOKEN_PARAM_NAME": twitter_bearer_token_param_name,
                    "TWITTER_USERNAME_PARAM_NAME": twitter_username_param_name,
                },
            )
        finally:
            # Clean up the temporary directory when done
            # Comment this out if you want to inspect the contents for debugging
            shutil.rmtree(temp_dir)
        
        # Grant the Lambda function permission to read the SSM parameters
        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter", "ssm:GetParameters"],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter{github_token_param_name}",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter{github_username_param_name}",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter{twitter_bearer_token_param_name}",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter{twitter_username_param_name}",
                ]
            )
        )
        
        # Grant the Lambda function permission to write to the S3 bucket
        website_bucket.grant_write(lambda_function)
        
        # Create a CloudWatch Event Rule to schedule the Lambda
        rule = events.Rule(
            self,
            "CommitsOrCloutUpdateSchedule",
            schedule=events.Schedule.rate(Duration.minutes(30)),
            description="Schedule for updating the CommitsOrClout website every 30 minutes",
        )
        
        # Add the Lambda function as a target for the rule
        rule.add_target(targets.LambdaFunction(lambda_function))


app = App()
CommitsOrCloutStack(app, "CommitsOrCloutStack")
app.synth() 