#!/bin/bash
# Update Driver Lambda environment variables with API URL

set -e

echo "=========================================="
echo "  Updating Driver Lambda Environment"
echo "=========================================="

# Get API URL from CloudFormation output
API_URL=$(aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingPlottingStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrlOutput`].OutputValue' \
  --output text)

if [ -z "$API_URL" ]; then
    echo "❌ Failed to get API URL from CloudFormation"
    exit 1
fi

echo "✅ API URL: $API_URL"

# Get Bucket Name
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingStorageStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketNameOutput`].OutputValue' \
  --output text)

if [ -z "$BUCKET_NAME" ]; then
    echo "❌ Failed to get Bucket Name from CloudFormation"
    exit 1
fi

echo "✅ Bucket Name: $BUCKET_NAME"

# Get Driver Lambda function name
DRIVER_FUNCTION=$(aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `S3SizeTrackingDriverStack`)].FunctionName' \
  --output text)

if [ -z "$DRIVER_FUNCTION" ]; then
    echo "❌ Failed to find Driver Lambda function"
    exit 1
fi

echo "✅ Driver Function: $DRIVER_FUNCTION"

# Update environment variables
echo ""
echo "Updating environment variables..."
aws lambda update-function-configuration \
  --function-name "$DRIVER_FUNCTION" \
  --environment "Variables={BUCKET_NAME=$BUCKET_NAME,PLOTTING_API_URL=$API_URL}" \
  > /dev/null

echo ""
echo "✅ Environment variables updated successfully!"
echo ""
echo "Driver Lambda is now configured with:"
echo "  BUCKET_NAME: $BUCKET_NAME"
echo "  PLOTTING_API_URL: $API_URL"

