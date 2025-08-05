#!/bin/bash

# Quick deployment status checker
# This script checks the status of the Commits or Clout deployment

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Checking Commits or Clout Deployment Status${NC}"
echo "================================================"
echo ""

# Check if we're in the right directory
if [ ! -d "cdk_deployment" ]; then
    echo -e "${RED}❌ Error: cdk_deployment directory not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Run the status check
cd cdk_deployment
./deploy.sh status

# Get additional information
echo ""
echo -e "${BLUE}📊 Additional Information:${NC}"
echo "================================"

# Get CloudFront distribution info
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
    --stack-name CommitsOrCloutStack \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
    --output text 2>/dev/null || echo "Not available")

DOMAIN_NAME=$(aws cloudformation describe-stacks \
    --stack-name CommitsOrCloutStack \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDomainName`].OutputValue' \
    --output text 2>/dev/null || echo "Not available")

if [ "$DOMAIN_NAME" != "Not available" ]; then
    echo -e "${GREEN}✅ CloudFront Domain:${NC} $DOMAIN_NAME"
    echo -e "${GREEN}✅ Distribution ID:${NC} $DISTRIBUTION_ID"
    echo -e "${GREEN}✅ Custom Domain:${NC} commits.willness.dev"
    echo ""
    echo "🌐 Your application should be available at:"
    echo "   https://$DOMAIN_NAME"
    echo "   https://commits.willness.dev (once DNS is configured)"
else
    echo -e "${YELLOW}⚠️  Deployment information not available${NC}"
fi

echo ""
echo -e "${BLUE}📝 Quick Commands:${NC}"
echo "====================="
echo "Deploy:     cd cdk_deployment && ./deploy.sh"
echo "Status:     cd cdk_deployment && ./deploy.sh status"
echo "Help:       cd cdk_deployment && ./deploy.sh help" 