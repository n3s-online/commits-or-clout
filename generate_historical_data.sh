#!/bin/bash

# Historical Data Generation and S3 Upload Script
# This script generates historical data and uploads it to S3

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

# Check if we're in the right directory
if [ ! -f "lambda_function/src/generate_historical_data.py" ]; then
    print_error "This script must be run from the project root directory"
    print_error "Expected to find: lambda_function/src/generate_historical_data.py"
    exit 1
fi

# Check if .env file exists
if [ ! -f "lambda_function/.env" ]; then
    print_error "Environment file not found: lambda_function/.env"
    print_error "Please create the .env file with your configuration"
    exit 1
fi

print_status "Starting historical data generation process..."

# Change to lambda function directory
cd lambda_function

# Check if virtual environment exists
if [ ! -d "lambda-venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv lambda-venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source lambda-venv/bin/activate

# Install/update dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
print_success "Dependencies installed"

# Load environment variables
print_status "Loading environment variables..."
set -a  # Automatically export all variables
source .env
set +a  # Stop automatically exporting

# Check required environment variables
required_vars=("GITHUB_TOKEN" "GITHUB_USERNAME" "S3_BUCKET")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_error "Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        print_error "  - $var"
    done
    exit 1
fi

print_success "Environment variables loaded"
print_status "GitHub Username: $GITHUB_USERNAME"
print_status "S3 Bucket: $S3_BUCKET"

if [ -n "$GITHUB_ORGANIZATION" ]; then
    print_status "GitHub Organization: $GITHUB_ORGANIZATION"
fi

# Generate historical data
print_status "Generating historical data..."
python src/generate_historical_data.py

if [ $? -eq 0 ]; then
    print_success "Historical data generated successfully"
else
    print_error "Failed to generate historical data"
    exit 1
fi

# Check if historical data file was created
if [ ! -f "historical_data.json" ]; then
    print_error "Historical data file not found: historical_data.json"
    exit 1
fi

# Get file size for reporting
file_size=$(du -h historical_data.json | cut -f1)
print_status "Generated file size: $file_size"

# Upload to S3
print_status "Uploading historical data to S3..."

# Upload main file
aws s3 cp historical_data.json "s3://$S3_BUCKET/historical_data.json" --content-type "application/json"

if [ $? -eq 0 ]; then
    print_success "Historical data uploaded to S3: s3://$S3_BUCKET/historical_data.json"
else
    print_error "Failed to upload historical data to S3"
    exit 1
fi

# Create backup
backup_filename="historical_data_backup_$(date +%Y%m%d_%H%M%S).json"
aws s3 cp historical_data.json "s3://$S3_BUCKET/$backup_filename" --content-type "application/json"

if [ $? -eq 0 ]; then
    print_success "Backup created: s3://$S3_BUCKET/$backup_filename"
else
    print_warning "Failed to create backup file"
fi

# Also upload as the standard backup filename
aws s3 cp historical_data.json "s3://$S3_BUCKET/historical_data_backup.json" --content-type "application/json"

if [ $? -eq 0 ]; then
    print_success "Standard backup updated: s3://$S3_BUCKET/historical_data_backup.json"
else
    print_warning "Failed to update standard backup file"
fi

# Verify upload
print_status "Verifying S3 upload..."
aws s3 ls "s3://$S3_BUCKET/historical_data.json" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    print_success "Upload verified successfully"
else
    print_error "Upload verification failed"
    exit 1
fi

# Clean up
print_status "Cleaning up..."
deactivate

print_success "Historical data generation and upload completed successfully!"
print_status "Files uploaded:"
print_status "  - s3://$S3_BUCKET/historical_data.json"
print_status "  - s3://$S3_BUCKET/historical_data_backup.json"
print_status "  - s3://$S3_BUCKET/$backup_filename"

echo ""
print_status "You can now trigger your Lambda function to use the updated historical data."
