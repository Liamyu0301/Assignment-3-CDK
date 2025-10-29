"""
Size Tracking Stack - Lambda Function with S3 Event Trigger
Creates the Lambda function that monitors S3 bucket size changes.
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class SizeTrackingStack(Stack):
    """
    Creates size-tracking Lambda function:
    - Triggered by S3 events (create/update/delete)
    - Calculates total bucket size
    - Records to DynamoDB
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        bucket: s3.IBucket,
        table: dynamodb.ITable,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Lambda function
        self.lambda_function = lambda_.Function(
            self,
            "SizeTrackingFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("lambda_code/size_tracking"),
            timeout=Duration.minutes(1),
            memory_size=256,
            environment={
                "TABLE_NAME": table.table_name,
            },
            description="Tracks S3 bucket size changes and records to DynamoDB",
        )

        # Grant permissions
        bucket.grant_read(self.lambda_function)
        table.grant_write_data(self.lambda_function)

