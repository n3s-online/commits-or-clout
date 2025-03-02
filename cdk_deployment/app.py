#!/usr/bin/env python3
import os
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

        # Retrieve parameters from SSM Parameter Store
        github_token = ssm.StringParameter.from_secure_string_parameter_attributes(
            self, "GitHubToken",
            parameter_name="/commits-or-clout/github-token",
            version=1
        )
        
        github_username = ssm.StringParameter.from_string_parameter_attributes(
            self, "GitHubUsername",
            parameter_name="/commits-or-clout/github-username",
            version=1
        )
        
        twitter_bearer_token = ssm.StringParameter.from_secure_string_parameter_attributes(
            self, "TwitterBearerToken",
            parameter_name="/commits-or-clout/twitter-bearer-token",
            version=1
        )
        
        twitter_username = ssm.StringParameter.from_string_parameter_attributes(
            self, "TwitterUsername",
            parameter_name="/commits-or-clout/twitter-username",
            version=1
        )

        # Define the Lambda function
        lambda_function = _lambda.Function(
            self, 
            "CommitsOrCloutUpdater",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("../lambda_function/src"),
            handler="lambda_handler.handler",
            timeout=Duration.seconds(120),
            memory_size=128,
            description="Lambda function that updates the CommitsOrClout website",
            environment={
                "S3_BUCKET": website_bucket.bucket_name,
                "S3_KEY": "index.html",
                "GITHUB_TOKEN": github_token.string_value,
                "GITHUB_USERNAME": github_username.string_value,
                "TWITTER_BEARER_TOKEN": twitter_bearer_token.string_value,
                "TWITTER_USERNAME": twitter_username.string_value,
            },
        )
        
        # Grant the Lambda function permission to read the SSM parameters
        github_token.grant_read(lambda_function)
        github_username.grant_read(lambda_function)
        twitter_bearer_token.grant_read(lambda_function)
        twitter_username.grant_read(lambda_function)
        
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