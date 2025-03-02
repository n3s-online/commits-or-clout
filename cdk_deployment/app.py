#!/usr/bin/env python3
import os
from aws_cdk import (
    App,
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct

class LambdaDeploymentStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Define the Lambda function
        lambda_function = _lambda.Function(
            self, 
            "ScheduledLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("../lambda_function/src"),
            handler="lambda_handler.handler",
            timeout=Duration.seconds(30),
            memory_size=128,
            description="Lambda function deployed via CDK",
        )
        
        # Create a CloudWatch Event Rule to schedule the Lambda
        rule = events.Rule(
            self,
            "ScheduleRule",
            schedule=events.Schedule.rate(Duration.minutes(30)),
            description="Schedule for Lambda function execution every 30 minutes",
        )
        
        # Add the Lambda function as a target for the rule
        rule.add_target(targets.LambdaFunction(lambda_function))


app = App()
LambdaDeploymentStack(app, "LambdaDeploymentStack")
app.synth() 