"""
Storage Stack - S3 Bucket and DynamoDB Table
Creates the foundational storage resources for the S3 size tracking system.
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class StorageStack(Stack):
    """
    Creates storage resources:
    - S3 bucket for storing files and plots
    - DynamoDB table for storing size history with GSI
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket
        # No hardcoded name - CDK will generate unique name
        self.bucket = s3.Bucket(
            self,
            "TestBucket",
            # Enable versioning for data protection
            versioned=False,
            # Automatically delete objects when stack is destroyed (for dev/test)
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            # Enable event notifications
            event_bridge_enabled=False,  # We'll use S3 event notifications instead
            # Block public access
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        # Create DynamoDB table
        self.table = dynamodb.Table(
            self,
            "SizeHistoryTable",
            # Partition key: bucket_name (supports multiple buckets)
            partition_key=dynamodb.Attribute(
                name="bucket_name",
                type=dynamodb.AttributeType.STRING
            ),
            # Sort key: timestamp (enables time-based queries)
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            # On-demand billing mode
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            # Cleanup policy for dev/test
            removal_policy=RemovalPolicy.DESTROY,
            # Point-in-time recovery
            point_in_time_recovery=False,
        )

        # Add Global Secondary Index for time-based queries across all buckets
        self.table.add_global_secondary_index(
            index_name="timestamp-index",
            partition_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

