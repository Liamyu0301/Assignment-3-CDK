#!/usr/bin/env python3
"""
Assignment 3 - S3 Bucket Size Tracking System using AWS CDK
Author: Yumeng Li

This CDK app creates all resources for the S3 bucket size tracking system:
- StorageStack: S3 bucket and DynamoDB table
- SizeTrackingStack: Lambda function triggered by S3 events
- PlottingStack: Lambda function with API Gateway and matplotlib layer
- DriverStack: Lambda function for testing (optional)
"""

import aws_cdk as cdk
from stacks.storage_stack import StorageStack
from stacks.size_tracking_stack import SizeTrackingStack
from stacks.plotting_stack import PlottingStack
from stacks.driver_stack import DriverStack


app = cdk.App()

# Stack 1: Create storage resources (S3 + DynamoDB)
storage_stack = StorageStack(
    app,
    "S3SizeTrackingStorageStack",
    description="Storage resources: S3 bucket and DynamoDB table for size tracking"
)

# Stack 2: Create size-tracking lambda with S3 event trigger
size_tracking_stack = SizeTrackingStack(
    app,
    "S3SizeTrackingSizeTrackingStack",
    bucket=storage_stack.bucket,
    table=storage_stack.table,
    description="Size-tracking Lambda function triggered by S3 events"
)
size_tracking_stack.add_dependency(storage_stack)

# Stack 3: Create plotting lambda with API Gateway
plotting_stack = PlottingStack(
    app,
    "S3SizeTrackingPlottingStack",
    bucket=storage_stack.bucket,
    table=storage_stack.table,
    description="Plotting Lambda function with REST API Gateway"
)
plotting_stack.add_dependency(storage_stack)

# Stack 4: Create driver lambda for testing
driver_stack = DriverStack(
    app,
    "S3SizeTrackingDriverStack",
    bucket=storage_stack.bucket,
    api_url_parameter=plotting_stack.api_url_parameter,
    description="Driver Lambda function for testing the system"
)
driver_stack.add_dependency(storage_stack)
driver_stack.add_dependency(plotting_stack)

# Output important information
cdk.CfnOutput(
    storage_stack,
    "BucketNameOutput",
    value=storage_stack.bucket.bucket_name,
    description="S3 Bucket name for testing",
    export_name="S3SizeTrackingBucketName"
)

cdk.CfnOutput(
    storage_stack,
    "TableNameOutput",
    value=storage_stack.table.table_name,
    description="DynamoDB table name",
    export_name="S3SizeTrackingTableName"
)

cdk.CfnOutput(
    plotting_stack,
    "ApiUrlOutput",
    value=plotting_stack.api_url_parameter.value_as_string,
    description="Plotting API URL",
    export_name="S3SizeTrackingApiUrl"
)

app.synth()

