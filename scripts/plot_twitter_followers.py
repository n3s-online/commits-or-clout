#!/usr/bin/env python3
"""
Local script to fetch historical data from S3 and plot Twitter followers over time.
This script is for local analysis only and should not be deployed.
"""

import os
import sys
import json
import boto3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env file"""
    # Look for .env file in lambda_function directory
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lambda_function', '.env')
    
    if not os.path.exists(env_path):
        logger.error(f"Environment file not found at {env_path}")
        sys.exit(1)
    
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
    
    # Check required environment variables
    required_vars = ["S3_BUCKET", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    return {
        'bucket': os.environ.get('S3_BUCKET'),
        'history_key': os.environ.get('S3_HISTORY_KEY', 'historical_data.json'),
        'backup_key': os.environ.get('S3_HISTORY_BACKUP_KEY', 'historical_data_backup.json')
    }

def fetch_historical_data_from_s3(config):
    """Fetch historical data from S3"""
    try:
        # Initialize S3 client with credentials from environment
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        logger.info(f"Fetching historical data from S3: {config['bucket']}/{config['history_key']}")
        
        try:
            # Try to get the main historical data file
            response = s3.get_object(Bucket=config['bucket'], Key=config['history_key'])
            historical_data = json.loads(response['Body'].read().decode('utf-8'))
            logger.info("Successfully retrieved historical data from S3")
            return historical_data
            
        except s3.exceptions.NoSuchKey:
            logger.info("Main historical data not found, trying backup...")
            
            # Try to get the backup file
            response = s3.get_object(Bucket=config['bucket'], Key=config['backup_key'])
            historical_data = json.loads(response['Body'].read().decode('utf-8'))
            logger.info("Successfully retrieved historical data from backup")
            return historical_data
            
    except Exception as e:
        logger.error(f"Error fetching historical data from S3: {e}")
        sys.exit(1)

def filter_current_year_data(historical_data):
    """Filter data to only include current year"""
    current_year = datetime.now().year
    filtered_data = []
    
    for entry in historical_data.get('data', []):
        entry_date = datetime.strptime(entry['date'], '%Y-%m-%d')
        if entry_date.year == current_year:
            filtered_data.append(entry)
    
    logger.info(f"Filtered to {len(filtered_data)} entries for year {current_year}")
    return filtered_data

def create_twitter_followers_plot(data):
    """Create and display a plot of Twitter followers over time"""
    if not data:
        logger.error("No data available for plotting")
        return
    
    # Extract dates and Twitter follower counts
    dates = []
    twitter_followers = []
    
    for entry in data:
        dates.append(datetime.strptime(entry['date'], '%Y-%m-%d').date())
        twitter_followers.append(entry.get('twitter_followers', 0))
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    plt.plot(dates, twitter_followers, marker='o', linewidth=2, markersize=4, color='#1d9bf0')
    
    # Customize the plot
    plt.title(f'Twitter Followers Over Time - {datetime.now().year}', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Twitter Followers', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Format x-axis to show dates nicely
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.xticks(rotation=45)
    
    # Add some statistics to the plot
    min_followers = min(twitter_followers)
    max_followers = max(twitter_followers)
    current_followers = twitter_followers[-1] if twitter_followers else 0
    
    # Add text box with statistics
    stats_text = f'Current: {current_followers}\nMin: {min_followers}\nMax: {max_followers}\nGrowth: +{current_followers - twitter_followers[0] if twitter_followers else 0}'
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the plot
    output_file = os.path.join(os.path.dirname(__file__), f'twitter_followers_{datetime.now().year}.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    logger.info(f"Plot saved to: {output_file}")
    
    # Display the plot
    plt.show()
    
    return output_file

def main():
    """Main function"""
    print("🐦 Twitter Followers Plotter")
    print("=" * 40)
    
    # Load environment variables
    config = load_environment()
    
    # Fetch historical data from S3
    print("📥 Fetching historical data from S3...")
    historical_data = fetch_historical_data_from_s3(config)
    
    # Filter to current year only
    print(f"📅 Filtering data for {datetime.now().year}...")
    current_year_data = filter_current_year_data(historical_data)
    
    if not current_year_data:
        print(f"❌ No data found for {datetime.now().year}")
        sys.exit(1)
    
    # Create and display the plot
    print("📊 Creating Twitter followers plot...")
    output_file = create_twitter_followers_plot(current_year_data)
    
    print(f"✅ Plot created successfully!")
    print(f"📁 Saved to: {output_file}")
    print(f"📈 Showing {len(current_year_data)} data points for {datetime.now().year}")

if __name__ == "__main__":
    main()
