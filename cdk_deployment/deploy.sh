#!/bin/bash

# Commits or Clout Deployment Script
# This script automates the deployment of the Commits or Clout application to AWS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check AWS credentials
check_aws_credentials() {
    print_status "Checking AWS credentials..."
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        print_error "AWS credentials not configured or invalid"
        print_status "Please run 'aws configure' or set up your credentials"
        exit 1
    fi
    print_success "AWS credentials verified"
}

# Function to check if CDK is installed
check_cdk() {
    print_status "Checking CDK installation..."
    if ! command_exists cdk; then
        print_error "CDK CLI not found"
        print_status "Please install CDK CLI: npm install -g aws-cdk"
        exit 1
    fi
    print_success "CDK CLI found"
}

# Function to setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."
    
    # Check if we're in the right directory
    if [ ! -f "app.py" ]; then
        print_error "app.py not found. Please run this script from the cdk_deployment directory"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "cdk-venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv cdk-venv
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source cdk-venv/bin/activate
    
    # Install dependencies
    print_status "Installing dependencies..."
    pip install -r requirements.txt
    
    print_success "Python environment setup complete"
}

# Function to bootstrap CDK (if needed)
bootstrap_cdk() {
    print_status "Checking CDK bootstrap status..."
    
    # Get AWS account and region
    ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    REGION="us-east-1"
    
    # Check if bootstrap is needed
    if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $REGION >/dev/null 2>&1; then
        print_status "Bootstrapping CDK environment..."
        cdk bootstrap aws://$ACCOUNT/$REGION
        print_success "CDK bootstrap complete"
    else
        print_success "CDK already bootstrapped"
    fi
}

# Function to deploy the application
deploy_application() {
    print_status "Deploying Commits or Clout application..."
    
    # Synthesize first to check for errors
    print_status "Synthesizing CDK app..."
    cdk synth --app "python app.py"
    
    # Deploy the application
    print_status "Deploying to AWS..."
    cdk deploy --app "python app.py" --require-approval never
    
    print_success "Deployment completed successfully!"
}

# Function to show deployment info
show_deployment_info() {
    print_status "Getting deployment information..."
    
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
    
    echo ""
    echo "🎉 Deployment Summary:"
    echo "======================"
    echo "CloudFront Distribution ID: $DISTRIBUTION_ID"
    echo "CloudFront Domain: $DOMAIN_NAME"
    echo "Custom Domain: commits.willness.dev"
    echo ""
    echo "Your application should be available at:"
    echo "  https://$DOMAIN_NAME"
    echo "  https://commits.willness.dev (once DNS is configured)"
    echo ""
    echo "The Lambda function will run every 30 minutes to update metrics."
    echo ""
}

# Function to check deployment status
check_deployment_status() {
    print_status "Checking deployment status..."
    
    if aws cloudformation describe-stacks --stack-name CommitsOrCloutStack --region us-east-1 >/dev/null 2>&1; then
        STATUS=$(aws cloudformation describe-stacks \
            --stack-name CommitsOrCloutStack \
            --region us-east-1 \
            --query 'Stacks[0].StackStatus' \
            --output text)
        
        if [ "$STATUS" = "CREATE_COMPLETE" ] || [ "$STATUS" = "UPDATE_COMPLETE" ]; then
            print_success "Stack is deployed and healthy (Status: $STATUS)"
            return 0
        else
            print_warning "Stack exists but status is: $STATUS"
            return 1
        fi
    else
        print_error "Stack not found"
        return 1
    fi
}

# Main deployment function
main() {
    echo "🚀 Commits or Clout Deployment Script"
    echo "====================================="
    echo ""
    
    # Check prerequisites
    check_aws_credentials
    check_cdk
    
    # Setup environment
    setup_python_env
    
    # Bootstrap if needed
    bootstrap_cdk
    
    # Deploy the application
    deploy_application
    
    # Show deployment information
    show_deployment_info
    
    echo ""
    print_success "Deployment script completed successfully!"
}

# Handle script arguments
case "${1:-}" in
    "status")
        check_deployment_status
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no args)  Deploy the application"
        echo "  status     Check deployment status"
        echo "  help       Show this help message"
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac 