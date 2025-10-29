#!/bin/bash
# Deployment script for Assignment 3 CDK stacks

set -e  # Exit on error

echo "=========================================="
echo "  Assignment 3 CDK Deployment Script"
echo "=========================================="

# Check prerequisites
echo ""
echo "[1/6] Checking prerequisites..."

if ! command -v cdk &> /dev/null; then
    echo "❌ CDK CLI not found. Install with: npm install -g aws-cdk"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Install from: https://aws.amazon.com/cli/"
    exit 1
fi

if [ ! -f "../layer_build/layer.zip" ]; then
    echo "⚠️  Warning: matplotlib layer not found at ../layer_build/layer.zip"
    echo "   You may need to build it first"
fi

echo "✅ Prerequisites check passed"

# Bootstrap CDK (if needed)
echo ""
echo "[2/6] Checking CDK bootstrap..."
cdk bootstrap || echo "✅ CDK already bootstrapped"

# Install Python dependencies
echo ""
echo "[3/6] Installing Python dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Synthesize CloudFormation templates
echo ""
echo "[4/6] Synthesizing CloudFormation templates..."
cdk synth > /dev/null
echo "✅ Templates synthesized"

# Show what will be deployed
echo ""
echo "[5/6] Showing deployment plan..."
cdk diff || true

# Deploy stacks
echo ""
echo "[6/6] Deploying stacks..."
read -p "Do you want to proceed with deployment? (yes/no): " -r
echo

if [[ $REPLY =~ ^[Yy]es$ ]]; then
    echo "Deploying all stacks..."
    cdk deploy --all --require-approval never
    
    echo ""
    echo "=========================================="
    echo "  Deployment Complete!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Run scripts/update_driver_env.sh to update Driver Lambda API URL"
    echo "2. Test the system with scripts/test_system.sh"
    echo ""
    
    # Show outputs
    echo "Stack Outputs:"
    aws cloudformation describe-stacks \
      --stack-name S3SizeTrackingStorageStack \
      --query 'Stacks[0].Outputs' \
      --output table 2>/dev/null || true
    
    aws cloudformation describe-stacks \
      --stack-name S3SizeTrackingPlottingStack \
      --query 'Stacks[0].Outputs' \
      --output table 2>/dev/null || true
else
    echo "Deployment cancelled"
    exit 0
fi

