"""
Driver Stack - Lambda Function for Testing
Creates the Lambda function that orchestrates test operations.
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_s3 as s3,
)
from constructs import Construct


class DriverStack(Stack):
    """
    Creates driver Lambda function:
    - Performs S3 operations (create/update/delete)
    - Calls plotting API
    - Used for testing the entire system
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        bucket: s3.IBucket,
        api_url: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Lambda function
        self.lambda_function = lambda_.Function(
            self,
            "DriverFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("lambda_code/driver"),
            timeout=Duration.minutes(2),
            memory_size=256,
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                # API URL will be set after deployment
                "PLOTTING_API_URL": "PLACEHOLDER",  # Update after deployment
            },
            description="Driver function for testing S3 size tracking system",
        )

        # Grant permissions
        bucket.grant_read_write(self.lambda_function)
        bucket.grant_delete(self.lambda_function)

