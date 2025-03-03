import os
import json
import logging
import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# GitHub API configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

# Constants
TWITTER_FOLLOWERS = 35  # Fixed number of Twitter followers
OUTPUT_FILE = "historical_data.json"

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

def generate_historical_data():
    """
    Generate historical data from January 1st to today with cumulative commit counts.
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
    
    # Calculate cumulative commits for each day
    historical_data = {"data": []}
    cumulative_commits = 0
    
    # Sort dates to ensure chronological order
    sorted_dates = sorted(daily_commits.keys())
    
    for date_str in sorted_dates:
        cumulative_commits += daily_commits[date_str]
        
        # Get current time in Pacific timezone for last_updated
        current_pacific_time = datetime.now(pacific_tz)
        
        # Create entry for this date
        entry = {
            "date": date_str,
            "github_commits": cumulative_commits,
            "twitter_followers": TWITTER_FOLLOWERS,
            "ratio": round((cumulative_commits / TWITTER_FOLLOWERS) * 10) / 10,
            "last_updated": current_pacific_time.isoformat()
        }
        
        historical_data["data"].append(entry)
    
    # Save to file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(historical_data, indent=2, fp=f)
    
    logger.info(f"Historical data saved to {OUTPUT_FILE}")
    logger.info(f"Generated {len(historical_data['data'])} daily entries")
    logger.info(f"Data ranges from {sorted_dates[0]} to {sorted_dates[-1]}")
    
    return historical_data

if __name__ == "__main__":
    if not GITHUB_TOKEN or not GITHUB_USERNAME:
        logger.error("GitHub token or username not found in environment variables")
        print("Please set GITHUB_TOKEN and GITHUB_USERNAME environment variables")
        print("You can create a .env file with these values")
        exit(1)
    
    logger.info(f"Generating historical data for GitHub user: {GITHUB_USERNAME}")
    generate_historical_data()
    logger.info("Done!") 