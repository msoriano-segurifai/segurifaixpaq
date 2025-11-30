#!/bin/bash
# =============================================================================
# SegurifAI x PAQ - AWS Infrastructure Setup Script
# =============================================================================
# This script creates the necessary AWS resources for production deployment
# Run this ONCE before first deployment

set -e

APP_NAME="segurifai"
REGION="us-east-1"
DB_INSTANCE_CLASS="db.t3.micro"
DB_NAME="segurifai_prod"
DB_USER="segurifai_admin"

echo "=========================================="
echo "SegurifAI x PAQ - AWS Setup"
echo "=========================================="

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    exit 1
fi

echo "Checking AWS credentials..."
aws sts get-caller-identity > /dev/null 2>&1 || {
    echo "Error: AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
}

echo ""
echo "Step 1: Creating S3 bucket for media files..."
BUCKET_NAME="${APP_NAME}-media-prod"
aws s3api create-bucket \
    --bucket $BUCKET_NAME \
    --region $REGION \
    --create-bucket-configuration LocationConstraint=$REGION 2>/dev/null || echo "Bucket already exists or name taken"

# Block public access
aws s3api put-public-access-block \
    --bucket $BUCKET_NAME \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "S3 bucket created: $BUCKET_NAME"

echo ""
echo "Step 2: Creating RDS PostgreSQL database..."
echo "Note: This will prompt for the database password"
read -sp "Enter database password (min 8 chars): " DB_PASSWORD
echo ""

# Create DB subnet group first (requires VPC setup)
echo "Note: RDS creation requires a VPC with subnets"
echo "For quick setup, use Elastic Beanstalk's managed database option instead"
echo ""
echo "To use EB managed database, run:"
echo "  eb create segurifai-prod --database --database.engine postgres --database.instance db.t3.micro"

echo ""
echo "Step 3: Setting up Elastic Beanstalk..."

# Install EB CLI if not present
if ! command -v eb &> /dev/null; then
    pip install awsebcli
fi

# Initialize EB
cd "$(dirname "$0")/.."
eb init $APP_NAME --platform python-3.11 --region $REGION

echo ""
echo "Step 4: Creating Elastic Beanstalk environment..."
echo "This will create an environment with a managed RDS database"

eb create ${APP_NAME}-prod \
    --database \
    --database.engine postgres \
    --database.instance $DB_INSTANCE_CLASS \
    --database.username $DB_USER \
    --database.password "$DB_PASSWORD" \
    --elb-type application \
    --instance_type t3.small

echo ""
echo "=========================================="
echo "AWS Setup Complete!"
echo "=========================================="
echo ""
echo "Resources created:"
echo "- S3 Bucket: $BUCKET_NAME"
echo "- Elastic Beanstalk Application: $APP_NAME"
echo "- Environment: ${APP_NAME}-prod (with RDS PostgreSQL)"
echo ""
echo "Next steps:"
echo "1. Configure environment variables in EB console or with:"
echo "   eb setenv SECRET_KEY=... PAQ_SSO_SECRET=... etc."
echo ""
echo "2. Deploy with: ./scripts/deploy.sh production"
echo ""
echo "3. Set up your domain in Cloudflare pointing to the EB URL"
