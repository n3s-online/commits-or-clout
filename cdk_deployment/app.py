#!/usr/bin/env python3
import os
from aws_cdk import (
    App,
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_certificatemanager as acm,
    aws_s3_deployment as s3deploy,
    aws_ssm as ssm,
    aws_iam as iam,
    aws_ecr_assets as ecr_assets,
    Duration,
    RemovalPolicy,
    CfnOutput,
    Environment
)
from constructs import Construct

class CommitsOrCloutStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create an S3 bucket for storing the HTML file
        website_bucket = s3.Bucket(
            self,
            "CommitsOrCloutWebsite",
            removal_policy=RemovalPolicy.DESTROY,  # Keep as DESTROY to avoid deployment issues
            auto_delete_objects=True,  # Keep as True to avoid permission errors
            website_index_document="index.html",
            public_read_access=True,  # Allow public access to read the website
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            )
        )

        # Add a lifecycle rule to preserve important files
        website_bucket.add_lifecycle_rule(
            id="PreserveImportantFiles",
            prefix="",  # Apply to all objects
            noncurrent_version_expiration=Duration.days(1),  # Clean up old versions
            abort_incomplete_multipart_upload_after=Duration.days(1),
            expiration=None,  # Don't expire current versions
            transitions=[],
            noncurrent_version_transitions=[],
            expiration_date=None,
            expired_object_delete_marker=False
        )

        # Upload favicon files directly to S3 during deployment
        favicon_files = [
            {"source": "../lambda_function/favicons/favicon.ico", "target": "favicon.ico", "content_type": "image/x-icon"},
            {"source": "../lambda_function/favicons/favicon.svg", "target": "favicon.svg", "content_type": "image/svg+xml"},
            {"source": "../lambda_function/favicons/apple-touch-icon.png", "target": "apple-touch-icon.png", "content_type": "image/png"},
            {"source": "../lambda_function/favicons/favicon-96x96.png", "target": "favicon-96x96.png", "content_type": "image/png"},
            {"source": "../lambda_function/favicons/web-app-manifest-192x192.png", "target": "web-app-manifest-192x192.png", "content_type": "image/png"},
            {"source": "../lambda_function/favicons/web-app-manifest-512x512.png", "target": "web-app-manifest-512x512.png", "content_type": "image/png"},
            {"source": "../lambda_function/favicons/site.webmanifest", "target": "site.webmanifest", "content_type": "application/json"}
        ]
        
        # Deploy all favicon files at once
        s3deploy.BucketDeployment(
            self,
            "DeployFavicons",
            sources=[s3deploy.Source.asset("../lambda_function/favicons")],
            destination_bucket=website_bucket,
            destination_key_prefix="",
            retain_on_delete=True,  # Changed from False to True to retain files on delete
            prune=False  # Added to prevent pruning of files not in the source
        )

        # Request a certificate for commits.willness.dev
        # Note: You'll need to validate this certificate manually with Porkbun
        certificate = acm.Certificate(
            self, "CommitsCertificate",
            domain_name="commits.willness.dev",
            validation=acm.CertificateValidation.from_email()  # Email validation is simpler with external DNS
        )

        # Create a CloudFront distribution
        distribution = cloudfront.Distribution(
            self, "CommitsDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(website_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            domain_names=["commits.willness.dev"],
            certificate=certificate,
            default_root_object="index.html",
        )

        # Output the CloudFront domain name and distribution ID
        CfnOutput(self, "CloudFrontDomainName", 
                  value=distribution.distribution_domain_name,
                  description="The domain name of the CloudFront distribution")
        
        CfnOutput(self, "CloudFrontDistributionId", 
                  value=distribution.distribution_id,
                  description="The ID of the CloudFront distribution")

        # Define parameter names
        # cli command to create these parameters: aws ssm put-parameter --name "" --type "SecureString" --value ""
        github_token_param_name = "/commits-or-clout/github-token"
        github_username_param_name = "/commits-or-clout/github-username"
        github_organization_param_name = "/commits-or-clout/github-organization"
        github_token_org_param_name = "/commits-or-clout/github-token-org"
        twitter_bearer_token_param_name = "/commits-or-clout/twitter-bearer-token"
        twitter_username_param_name = "/commits-or-clout/twitter-username"
        discord_webhook_url_param_name = "/commits-or-clout/discord-webhook-url"
        youtube_api_key_param_name = "/commits-or-clout/youtube-api-key"
        youtube_channel_id_param_name = "/commits-or-clout/youtube-channel-id"
        bluesky_api_key_param_name = "/commits-or-clout/bluesky-api-key"
        bluesky_username_param_name = "/commits-or-clout/bluesky-username"

        # Define the Lambda function using Docker container
        lambda_function = _lambda.DockerImageFunction(
            self, 
            "CommitsOrCloutUpdater",
            code=_lambda.DockerImageCode.from_image_asset(
                "../lambda_function",  # Path to the directory containing Dockerfile
                # No need to specify cmd as we're using ENTRYPOINT in Dockerfile
                platform=ecr_assets.Platform.LINUX_AMD64,  # Specify Linux AMD64 platform
                build_args={
                    "DOCKER_BUILDKIT": "1"  # Enable BuildKit for better cross-platform support
                }
            ),
            timeout=Duration.seconds(300),
            memory_size=1024,  # Increased to 1GB for better performance
            description="Lambda function that updates the CommitsOrClout website",
            environment={
                "S3_BUCKET": website_bucket.bucket_name,
                "S3_KEY": "index.html",
                "S3_HISTORY_KEY": "historical_data.json",
                "GITHUB_TOKEN_PARAM_NAME": github_token_param_name,
                "GITHUB_USERNAME_PARAM_NAME": github_username_param_name,
                "GITHUB_ORGANIZATION_PARAM_NAME": github_organization_param_name,
                "GITHUB_TOKEN_ORG_PARAM_NAME": github_token_org_param_name,
                "TWITTER_BEARER_TOKEN_PARAM_NAME": twitter_bearer_token_param_name,
                "TWITTER_USERNAME_PARAM_NAME": twitter_username_param_name,
                "DISCORD_WEBHOOK_URL_PARAM_NAME": discord_webhook_url_param_name,
                "YOUTUBE_API_KEY_PARAM_NAME": youtube_api_key_param_name,
                "YOUTUBE_CHANNEL_ID_PARAM_NAME": youtube_channel_id_param_name,
                "BLUESKY_API_KEY_PARAM_NAME": bluesky_api_key_param_name,
                "BLUESKY_USERNAME_PARAM_NAME": bluesky_username_param_name,
                "PYTHONUNBUFFERED": "1"  # Ensure Python output is unbuffered for better logging
            },
            architecture=_lambda.Architecture.X86_64  # Ensure Lambda runs on x86_64
        )
        
        # Grant the Lambda function permission to read the SSM parameters
        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter", "ssm:GetParameters"],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{github_token_param_name.lstrip('/')}",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{github_username_param_name.lstrip('/')}",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{github_organization_param_name.lstrip('/')}",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{github_token_org_param_name.lstrip('/')}",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{twitter_bearer_token_param_name.lstrip('/')}",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{twitter_username_param_name.lstrip('/')}",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{discord_webhook_url_param_name.lstrip('/')}",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{youtube_api_key_param_name.lstrip('/')}",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{youtube_channel_id_param_name.lstrip('/')}",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{bluesky_api_key_param_name.lstrip('/')}",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{bluesky_username_param_name.lstrip('/')}",
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

# Deploy everything to us-east-1
CommitsOrCloutStack(app, "CommitsOrCloutStack", 
                   env=Environment(account=os.environ.get("CDK_DEFAULT_ACCOUNT"), 
                                   region="us-east-1"))

app.synth() 