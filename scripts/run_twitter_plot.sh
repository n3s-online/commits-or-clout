#!/bin/bash

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

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_status "Twitter Followers Plotter Setup"
echo "=================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "plot-venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv plot-venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source plot-venv/bin/activate

# Install/update dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
print_success "Dependencies installed"

# Check if .env file exists
ENV_FILE="../lambda_function/.env"
if [ ! -f "$ENV_FILE" ]; then
    print_error ".env file not found at $ENV_FILE"
    print_error "Please make sure the .env file exists in the lambda_function directory"
    exit 1
fi

print_success "Environment file found"

# Run the plotting script
print_status "Running Twitter followers plotter..."
python3 plot_twitter_followers.py

print_success "Script completed!"
print_status "Check the generated PNG file for your Twitter followers plot"
