"""
Plotting Stack - Lambda Function with API Gateway and Layer
Creates the Lambda function that generates matplotlib plots.
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigateway,
)
from constructs import Construct


class PlottingStack(Stack):
    """
    Creates plotting Lambda function:
    - Generates matplotlib plots from DynamoDB data
    - Exposed via REST API Gateway
    - Uses Lambda layer for matplotlib dependencies
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

        # Create Lambda layer for matplotlib
        # Note: You need to build this layer separately
        # See ../layer_build/ from Assignment 2
        matplotlib_layer = lambda_.LayerVersion(
            self,
            "MatplotlibLayer",
            code=lambda_.Code.from_asset("../layer_build/layer.zip"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9],
            description="Matplotlib and dependencies for plotting",
        )

        # Create Lambda function
        self.lambda_function = lambda_.Function(
            self,
            "PlottingFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("lambda_code/plotting"),
            timeout=Duration.minutes(1),
            memory_size=512,  # matplotlib needs more memory
            layers=[matplotlib_layer],
            environment={
                "TABLE_NAME": table.table_name,
                "BUCKET_NAME": bucket.bucket_name,
                "WINDOW_SECONDS": "10",
            },
            description="Generates matplotlib plots of bucket size history",
        )

        # Grant permissions
        table.grant_read_data(self.lambda_function)
        bucket.grant_put(self.lambda_function)

        # Create REST API
        api = apigateway.RestApi(
            self,
            "PlottingApi",
            rest_api_name="S3 Size Tracking Plotting API",
            description="API for generating bucket size plots",
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                throttling_rate_limit=10,
                throttling_burst_limit=20,
            ),
        )

        # Create /plot resource
        plot_resource = api.root.add_resource("plot")

        # Add GET method with Lambda proxy integration
        plot_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(
                self.lambda_function,
                proxy=True,
            ),
        )

        # Store API URL for cross-stack reference
        self.api_url = f"{api.url}plot"

