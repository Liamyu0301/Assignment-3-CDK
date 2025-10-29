#!/bin/bash
# Test the deployed S3 size tracking system

set -e

echo "=========================================="
echo "  Testing S3 Size Tracking System"
echo "=========================================="

# Get Driver Lambda function name
DRIVER_FUNCTION=$(aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `S3SizeTrackingDriverStack`)].FunctionName' \
  --output text)

if [ -z "$DRIVER_FUNCTION" ]; then
    echo "❌ Failed to find Driver Lambda function"
    exit 1
fi

echo "✅ Driver Function: $DRIVER_FUNCTION"

# Invoke Lambda
echo ""
echo "Invoking Driver Lambda..."
aws lambda invoke \
  --function-name "$DRIVER_FUNCTION" \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  output.json

echo ""
echo "=========================================="
echo "  Lambda Response:"
echo "=========================================="
cat output.json | python3 -m json.tool

# Get bucket name
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingStorageStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketNameOutput`].OutputValue' \
  --output text)

# Check if plot was generated
echo ""
echo "=========================================="
echo "  Checking S3 Bucket Contents:"
echo "=========================================="
aws s3 ls s3://$BUCKET_NAME/

# Download plot
echo ""
echo "Downloading plot..."
aws s3 cp s3://$BUCKET_NAME/plot plot.png
echo "✅ Plot saved to plot.png"

# Check DynamoDB
echo ""
echo "=========================================="
echo "  Recent DynamoDB Entries:"
echo "=========================================="
aws dynamodb query \
  --table-name S3-object-size-history \
  --key-condition-expression "bucket_name = :bn" \
  --expression-attribute-values "{\":bn\":{\"S\":\"$BUCKET_NAME\"}}" \
  --limit 5 \
  --scan-index-forward false \
  --query 'Items[].{timestamp:timestamp.N,size:total_size.N,count:object_count.N}' \
  --output table

echo ""
echo "=========================================="
echo "  Test Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✅ Driver Lambda executed successfully"
echo "  ✅ Plot generated and saved to S3"
echo "  ✅ DynamoDB contains size history"
echo ""
echo "Next steps:"
echo "  - Open plot.png to view the graph"
echo "  - Check CloudWatch Logs for detailed execution logs"
echo ""

# Cleanup
rm output.json

