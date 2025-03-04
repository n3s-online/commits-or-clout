import os
import json
import logging
import requests
import boto3
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from youtube_utils import get_youtube_subscriber_count
from bluesky_utils import BlueskyHelper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# GitHub API configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

# YouTube API configuration
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")

# Bluesky API configuration
BLUESKY_API_KEY = os.getenv("BLUESKY_API_KEY")
BLUESKY_USERNAME = os.getenv("BLUESKY_USERNAME")

# S3 configuration
S3_BUCKET = os.getenv("S3_BUCKET")
S3_HISTORY_KEY = os.getenv("S3_HISTORY_KEY", "historical_data.json")
S3_HISTORY_BACKUP_KEY = os.getenv("S3_HISTORY_BACKUP_KEY", "historical_data_backup.json")

# Constants
TWITTER_FOLLOWERS = 35  # Fixed number of Twitter followers
OUTPUT_FILE = "historical_data.json"

# Initialize S3 client
s3 = boto3.client('s3')

def get_user_repositories(username, token):
    """
    Fetch all repositories for a GitHub user.
    """
    url = f"https://api.github.com/user/repos"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    params = {
        "per_page": 100,
        "type": "all",
    }
    all_repos = []

    try:
        page = 1
        while True:
            params["page"] = page
            response = requests.get(url, headers=headers, params=params)
            logger.info(f"API Response Status: {response.status_code}")
            
            response.raise_for_status()
            repos = response.json()

            if not repos:  # No more repositories
                break

            all_repos.extend(repos)
            logger.info(f"Fetched page {page} with {len(repos)} repositories")

            # Check if there's a next page using Link header
            if "Link" in response.headers:
                if 'rel="next"' not in response.headers["Link"]:
                    break
            else:
                # If no Link header and we got less than per_page results, we're done
                if len(repos) < params["per_page"]:
                    break

            page += 1

        logger.info(f"Found {len(all_repos)} repositories for user {username}")
        return all_repos
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching repositories: {e}")
        return []

def get_daily_commits(username, token, start_date, end_date):
    """
    Fetch commits for each day between start_date and end_date.
    Returns a dictionary with dates as keys and commit counts as values.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    # Get all repositories
    repositories = get_user_repositories(username, token)
    
    # Initialize a dictionary to store daily commit counts
    daily_commits = {}
    current_date = start_date
    while current_date <= end_date:
        daily_commits[current_date.strftime("%Y-%m-%d")] = 0
        current_date += timedelta(days=1)
    
    # For each repository, get commits and count them by date
    for repo in repositories:
        repo_name = repo['name']
        logger.info(f"Processing repository: {repo_name}")
        
        url = f"https://api.github.com/repos/{username}/{repo_name}/commits"
        params = {
            "since": start_date.isoformat(),
            "until": (end_date + timedelta(days=1)).isoformat(),  # Include end_date
            "per_page": 100,
            "author": username
        }
        
        try:
            page = 1
            while True:
                params["page"] = page
                response = requests.get(url, headers=headers, params=params)
                
                # Skip if we get an error (like empty repository)
                if response.status_code != 200:
                    logger.warning(f"Skipping repo {repo_name}: {response.status_code}")
                    break
                
                commits = response.json()
                if not commits:
                    break
                
                # Process commits on this page
                for commit in commits:
                    # Extract the date from the commit
                    commit_date_str = commit['commit']['committer']['date']
                    commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
                    commit_date_key = commit_date.strftime("%Y-%m-%d")
                    
                    # Increment the count for this date if it's in our range
                    if commit_date_key in daily_commits:
                        daily_commits[commit_date_key] += 1
                
                # Check if we need to fetch more pages
                if len(commits) < params["per_page"]:
                    break
                
                page += 1
                
        except Exception as e:
            logger.error(f"Error processing repo {repo_name}: {e}")
    
    return daily_commits

def get_historical_data_from_s3():
    """
    Fetch historical data from S3 bucket
    """
    try:
        logger.info(f"Fetching historical data from S3: {S3_BUCKET}/{S3_HISTORY_KEY}")
        response = s3.get_object(Bucket=S3_BUCKET, Key=S3_HISTORY_KEY)
        historical_data = json.loads(response['Body'].read().decode('utf-8'))
        logger.info(f"Successfully retrieved historical data from S3")
        return historical_data
    except s3.exceptions.NoSuchKey:
        logger.info(f"No historical data found in S3, trying to restore from backup")
        logger.info(f"Fetching backup historical data from S3: {S3_BUCKET}/{S3_HISTORY_BACKUP_KEY}")
        try:
            # Try to restore from backup
            response = s3.get_object(Bucket=S3_BUCKET, Key=S3_HISTORY_BACKUP_KEY)
            historical_data = json.loads(response['Body'].read().decode('utf-8'))
            logger.info(f"Successfully restored historical data from backup")
            return historical_data
        except s3.exceptions.NoSuchKey:
            logger.info(f"No backup historical data found either, creating new dataset")
            raise Exception("No historical data found in S3")
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            raise e;
    except Exception as e:
        logger.error(f"Error retrieving historical data from S3: {e}")
        raise e;

def save_historical_data_to_s3(historical_data):
    """
    Save historical data to S3 bucket
    """
    try:
        # First, create a backup of the existing data
        try:
            # Check if the file exists before trying to copy it
            s3.head_object(Bucket=S3_BUCKET, Key=S3_HISTORY_KEY)
            
            # Copy the existing file to a backup
            s3.copy_object(
                Bucket=S3_BUCKET,
                CopySource={'Bucket': S3_BUCKET, 'Key': S3_HISTORY_KEY},
                Key=S3_HISTORY_BACKUP_KEY
            )
            logger.info(f"Created backup of historical data at s3://{S3_BUCKET}/{S3_HISTORY_BACKUP_KEY}")
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.info(f"No existing historical data file to backup")
            else:
                logger.warning(f"Error creating backup of historical data: {e}")
        
        # Now save the new data
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=S3_HISTORY_KEY,
            Body=json.dumps(historical_data, indent=2).encode('utf-8'),
            ContentType='application/json'
        )
        logger.info(f"Successfully saved historical data to S3")
        
        # Also save locally for reference
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(historical_data, indent=2, fp=f)
        logger.info(f"Historical data saved locally to {OUTPUT_FILE}")
        
        return True
    except Exception as e:
        logger.error(f"Error saving historical data to S3: {e}")
        return False

def generate_historical_data():
    """
    Generate historical data from January 1st to today with cumulative commit counts.
    Uses existing data from S3 as the source of truth and updates it.
    """
    # Use Pacific timezone for all date operations
    pacific_tz = pytz.timezone('America/Los_Angeles')
    current_year = datetime.now(pacific_tz).year
    
    # Start from January 1st in Pacific time
    start_date = pacific_tz.localize(datetime(current_year, 1, 1)).astimezone(pytz.UTC)
    
    # End at today (midnight) in Pacific time
    today_pacific = datetime.now(pacific_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today_pacific.astimezone(pytz.UTC)
    
    # Get daily commit counts
    daily_commits = get_daily_commits(GITHUB_USERNAME, GITHUB_TOKEN, start_date, end_date)
    
    # Get YouTube subscriber count (current value)
    current_youtube_subscribers = 0
    try:
        current_youtube_subscribers = get_youtube_subscriber_count(YOUTUBE_API_KEY, YOUTUBE_CHANNEL_ID) or 0
        logger.info(f"Current YouTube subscribers: {current_youtube_subscribers}")
    except Exception as e:
        logger.error(f"Error fetching YouTube subscribers: {e}")
        raise e
    
    # Get current Twitter followers (fixed value for this script)
    current_twitter_followers = TWITTER_FOLLOWERS
    
    # Get current Bluesky followers
    current_bluesky_followers = 0
    try:
        bluesky_helper = BlueskyHelper(BLUESKY_API_KEY)
        current_bluesky_followers = bluesky_helper.get_total_followers(BLUESKY_USERNAME) or 0
        logger.info(f"Current Bluesky followers: {current_bluesky_followers}")
    except Exception as e:
        logger.error(f"Error fetching Bluesky followers: {e}")
        raise e

    
    # Get existing historical data from S3
    historical_data = get_historical_data_from_s3()
    
    # Create a dictionary of existing entries by date for easy lookup
    existing_entries = {}
    for entry in historical_data.get("data", []):
        existing_entries[entry.get("date")] = entry
    
    # Calculate cumulative commits for each day
    updated_historical_data = {"data": []}
    cumulative_commits = 0
    
    # Sort dates to ensure chronological order
    sorted_dates = sorted(daily_commits.keys())
    
    for date_str in sorted_dates:
        cumulative_commits += daily_commits[date_str]
        
        # Get current time in Pacific timezone for last_updated
        current_pacific_time = datetime.now(pacific_tz)
        
        # Check if we have existing data for this date
        if date_str in existing_entries:
            existing_entry = existing_entries[date_str]
            
            # Use existing follower counts if available, otherwise use current values
            twitter_followers = existing_entry.get("twitter_followers", current_twitter_followers)
            youtube_subscribers = existing_entry.get("youtube_subscribers", current_youtube_subscribers)
            bluesky_followers = existing_entry.get("bluesky_followers", current_bluesky_followers)
            
            # Always update GitHub commits
            github_commits = cumulative_commits
        else:
            # No existing data, use current values
            twitter_followers = current_twitter_followers
            youtube_subscribers = current_youtube_subscribers
            bluesky_followers = current_bluesky_followers
            github_commits = cumulative_commits
        
        # Always recalculate total_followers and ratio
        total_followers = max(twitter_followers + youtube_subscribers + bluesky_followers, 1)  # Ensure we don't divide by zero
        ratio = round((github_commits / total_followers) * 10) / 10
        
        # Create or update entry for this date
        entry = {
            "date": date_str,
            "github_commits": github_commits,
            "twitter_followers": twitter_followers,
            "youtube_subscribers": youtube_subscribers,
            "bluesky_followers": bluesky_followers,
            "total_followers": total_followers,
            "ratio": ratio,
            "last_updated": current_pacific_time.isoformat()
        }
        
        updated_historical_data["data"].append(entry)
    
    # Save updated data to S3
    save_historical_data_to_s3(updated_historical_data)
    
    logger.info(f"Generated/updated {len(updated_historical_data['data'])} daily entries")
    logger.info(f"Data ranges from {sorted_dates[0]} to {sorted_dates[-1]}")
    
    return updated_historical_data

if __name__ == "__main__":
    if not GITHUB_TOKEN or not GITHUB_USERNAME:
        logger.error("GitHub token or username not found in environment variables")
        print("Please set GITHUB_TOKEN and GITHUB_USERNAME environment variables")
        print("You can create a .env file with these values")
        exit(1)
    
    if not S3_BUCKET:
        logger.error("S3_BUCKET not found in environment variables")
        print("Please set S3_BUCKET environment variable")
        print("You can create a .env file with this value")
        exit(1)
    
    logger.info(f"Generating historical data for GitHub user: {GITHUB_USERNAME}")
    generate_historical_data()
    logger.info("Done!") 