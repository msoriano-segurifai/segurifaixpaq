#!/bin/bash
# =============================================================================
# SegurifAI x PAQ - Production Deployment Script
# =============================================================================
# Usage: ./scripts/deploy.sh [environment]
# Environments: staging, production

set -e

ENVIRONMENT=${1:-production}
APP_NAME="segurifai"
REGION="us-east-1"

echo "=========================================="
echo "SegurifAI x PAQ - Deployment Script"
echo "Environment: $ENVIRONMENT"
echo "=========================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    echo "Install with: pip install awscli"
    exit 1
fi

# Check if EB CLI is installed
if ! command -v eb &> /dev/null; then
    echo "Error: EB CLI is not installed"
    echo "Install with: pip install awsebcli"
    exit 1
fi

# Pre-deployment checks
echo ""
echo "Running pre-deployment checks..."

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Using environment variables."
fi

# Run Django checks
echo "Running Django system checks..."
python manage.py check --deploy

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations check
echo "Checking for pending migrations..."
python manage.py showmigrations --plan | grep -q '\[ \]' && {
    echo "Warning: There are unapplied migrations"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

# Deploy based on method
echo ""
echo "Deploying to AWS Elastic Beanstalk..."

# Initialize EB if not already done
if [ ! -d ".elasticbeanstalk" ]; then
    echo "Initializing Elastic Beanstalk..."
    eb init $APP_NAME --platform python-3.11 --region $REGION
fi

# Deploy
if [ "$ENVIRONMENT" == "production" ]; then
    eb deploy $APP_NAME-prod --staged
else
    eb deploy $APP_NAME-staging --staged
fi

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify the deployment: eb status"
echo "2. Check logs: eb logs"
echo "3. Open the app: eb open"
