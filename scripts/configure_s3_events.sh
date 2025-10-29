#!/bin/bash
# Configure S3 event notifications for size-tracking lambda

set -e

echo "Configuring S3 event notifications..."

# Get bucket name
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingStorageStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketNameOutput`].OutputValue' \
  --output text)

# Get Lambda function ARN
LAMBDA_ARN=$(aws lambda list-functions \
  --query 'Functions[?contains(FunctionName, `SizeTrackingFunction`)].FunctionArn' \
  --output text)

echo "Bucket: $BUCKET"
echo "Lambda ARN: $LAMBDA_ARN"

# Add Lambda permission for S3 to invoke it
aws lambda add-permission \
  --function-name "$LAMBDA_ARN" \
  --statement-id s3-invoke-permission \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn "arn:aws:s3:::$BUCKET" \
  || echo "Permission already exists"

# Configure S3 event notification
cat > /tmp/s3-notification.json << EOF
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "$LAMBDA_ARN",
      "Events": ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
    }
  ]
}
EOF

aws s3api put-bucket-notification-configuration \
  --bucket "$BUCKET" \
  --notification-configuration file:///tmp/s3-notification.json

echo "✅ S3 event notifications configured successfully!"


