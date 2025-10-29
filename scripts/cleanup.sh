#!/bin/bash
# Cleanup script - destroys all CDK stacks

set -e

echo "=========================================="
echo "  CDK Stack Cleanup"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will delete all resources!"
echo ""
read -p "Are you sure you want to proceed? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Cleanup cancelled"
    exit 0
fi

# Get bucket name and empty it first
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingStorageStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketNameOutput`].OutputValue' \
  --output text 2>/dev/null || true)

if [ ! -z "$BUCKET_NAME" ]; then
    echo "Emptying S3 bucket: $BUCKET_NAME"
    aws s3 rm s3://$BUCKET_NAME --recursive || true
fi

# Destroy stacks in reverse dependency order
echo ""
echo "Destroying CDK stacks..."

cdk destroy S3SizeTrackingDriverStack --force || true
cdk destroy S3SizeTrackingPlottingStack --force || true
cdk destroy S3SizeTrackingSizeTrackingStack --force || true
cdk destroy S3SizeTrackingStorageStack --force || true

echo ""
echo "✅ Cleanup complete!"

