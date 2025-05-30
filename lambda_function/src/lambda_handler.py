import json
import logging
import requests
import os
import boto3
# import tweepy  # Remove tweepy import
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader, Template
import pytz
from utils import get_html_template, render_html_template, calculate_weekly_activity  # Import the utility functions
from youtube_utils import get_youtube_subscriber_count  # Import the YouTube utility function
from bluesky_utils import BlueskyHelper  # Import the Bluesky utility class
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# SSM client for retrieving parameters
ssm_client = boto3.client('ssm')
# S3 client for file operations
s3 = boto3.client('s3')

def get_parameter(param_name, with_decryption=True):
    """
    Get a parameter from SSM Parameter Store
    """
    try:
        response = ssm_client.get_parameter(
            Name=param_name,
            WithDecryption=with_decryption
        )
        return response['Parameter']['Value']
    except Exception as e:
        logger.error(f"Error retrieving parameter {param_name}: {e}")
        return None

# Environment variables for parameter names
GITHUB_TOKEN_PARAM_NAME = os.environ.get("GITHUB_TOKEN_PARAM_NAME")
GITHUB_USERNAME_PARAM_NAME = os.environ.get("GITHUB_USERNAME_PARAM_NAME")
TWITTER_BEARER_TOKEN_PARAM_NAME = os.environ.get("TWITTER_BEARER_TOKEN_PARAM_NAME")
TWITTER_USERNAME_PARAM_NAME = os.environ.get("TWITTER_USERNAME_PARAM_NAME")
DISCORD_WEBHOOK_URL_PARAM_NAME = os.environ.get("DISCORD_WEBHOOK_URL_PARAM_NAME")
YOUTUBE_API_KEY_PARAM_NAME = os.environ.get("YOUTUBE_API_KEY_PARAM_NAME")
YOUTUBE_CHANNEL_ID_PARAM_NAME = os.environ.get("YOUTUBE_CHANNEL_ID_PARAM_NAME")
BLUESKY_API_KEY_PARAM_NAME = os.environ.get("BLUESKY_API_KEY_PARAM_NAME")
BLUESKY_USERNAME_PARAM_NAME = os.environ.get("BLUESKY_USERNAME_PARAM_NAME")
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_KEY = os.environ.get("S3_KEY", "index.html")
S3_KEY_BACKUP = os.environ.get("S3_KEY_BACKUP", "index_backup.html")
S3_HISTORY_KEY = os.environ.get("S3_HISTORY_KEY", "historical_data.json")
S3_HISTORY_BACKUP_KEY = os.environ.get("S3_HISTORY_BACKUP_KEY", "historical_data_backup.json")
SSM_PARAM_NAME = os.environ.get('SSM_PARAM_NAME', '/commits-or-clout/historical-data')

# Default values from environment variables
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "")
TWITTER_USERNAME = os.environ.get("TWITTER_USERNAME", "")
YOUTUBE_CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID", "")

# Retrieve actual values from Parameter Store
GITHUB_TOKEN = get_parameter(GITHUB_TOKEN_PARAM_NAME) or os.environ.get("GITHUB_TOKEN", "")
GITHUB_USERNAME = get_parameter(GITHUB_USERNAME_PARAM_NAME, False) or GITHUB_USERNAME
TWITTER_USERNAME = get_parameter(TWITTER_USERNAME_PARAM_NAME, False) or TWITTER_USERNAME
TWITTER_BEARER_TOKEN = get_parameter(TWITTER_BEARER_TOKEN_PARAM_NAME) or os.environ.get("TWITTER_BEARER_TOKEN", "")
DISCORD_WEBHOOK_URL = get_parameter(DISCORD_WEBHOOK_URL_PARAM_NAME, False) or os.environ.get("DISCORD_WEBHOOK_URL", "")
YOUTUBE_API_KEY = get_parameter(YOUTUBE_API_KEY_PARAM_NAME) or os.environ.get("YOUTUBE_API_KEY", "")
YOUTUBE_CHANNEL_ID = get_parameter(YOUTUBE_CHANNEL_ID_PARAM_NAME, False) or YOUTUBE_CHANNEL_ID
BLUESKY_API_KEY = get_parameter(BLUESKY_API_KEY_PARAM_NAME) or os.environ.get("BLUESKY_API_KEY", "")
BLUESKY_USERNAME = get_parameter(BLUESKY_USERNAME_PARAM_NAME) or os.environ.get("BLUESKY_USERNAME", "")

# Maximum Discord message length
MAX_DISCORD_MESSAGE_LENGTH = 2000

def send_discord_alert(message):
    """
    Send an alert message to Discord webhook
    """
    if not DISCORD_WEBHOOK_URL:
        logger.warning("Discord webhook URL not configured, skipping alert")
        return False

    # Truncate message if it exceeds maximum length
    if len(message) > MAX_DISCORD_MESSAGE_LENGTH:
        message = message[:MAX_DISCORD_MESSAGE_LENGTH - 3] + "..."

    payload = {
        "content": message
    }

    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        logger.info(f"Discord alert sent successfully: {message}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Discord alert: {e}")
        return False

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
    }  # Correct parameters
    all_repos = []

    try:
        page = 1
        while True:
            params["page"] = page
            response = requests.get(url, headers=headers, params=params)

            # Log the response status and headers for debugging
            logger.info(f"API Response Status: {response.status_code}")
            logger.info(f"API Response Headers: {response.headers}")

            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            repos = response.json()

            if not repos:  # No more repositories
                logger.info(f"No more repositories found on page {page}")
                break

            all_repos.extend(repos)
            logger.info(f"Fetched page {page} with {len(repos)} repositories")

            # Check if there's a next page using Link header
            if "Link" in response.headers:
                if 'rel="next"' not in response.headers["Link"]:
                    logger.info("No more pages according to Link header")
                    break
            else:
                # If no Link header and we got less than per_page results, we're done
                if len(repos) < params["per_page"]:
                    logger.info(
                        "Got fewer results than per_page limit, assuming last page"
                    )
                    break  # This is the problem.  Remove this break.

            page += 1

        logger.info(f"Found {len(all_repos)} repositories for user {username}")
        return all_repos
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching repositories: {e}")
        logger.error(
            f"Response content: {e.response.content if hasattr(e, 'response') else 'No response'}"
        )
        return []


def get_commits_since_jan_1(username, token):
    """
    Fetch the number of commits made to all GitHub repositories since January 1st across all branches.
    Returns None if there's an error.
    """
    current_year = datetime.now().year
    since = datetime(current_year, 1, 1, tzinfo=timezone.utc).isoformat()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Use a set to track unique commit SHAs to avoid counting duplicates
    unique_commits = set()

    try:
        # First get all repositories
        repositories = get_user_repositories(username, token)

        for repo in repositories:
            repo_name = repo['name']
            repo_owner = repo['owner']['login']

            # First get all branches for this repository
            branches_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches"
            branches_params = {"per_page": 100}
            branches = []

            try:
                # Fetch all branches
                branches_page = 1
                while True:
                    branches_params["page"] = branches_page
                    branches_response = requests.get(branches_url, headers=headers, params=branches_params)
                    branches_response.raise_for_status()
                    page_branches = branches_response.json()

                    if not page_branches:
                        break

                    branches.extend(page_branches)
                    logger.info(f"Fetched page {branches_page} with {len(page_branches)} branches for repo {repo_name}")

                    # Check if we need to fetch more pages
                    if len(page_branches) < branches_params["per_page"]:
                        break

                    # Check if there's a next page using Link header
                    if "Link" in branches_response.headers:
                        if 'rel="next"' not in branches_response.headers["Link"]:
                            break

                    branches_page += 1

                logger.info(f"Found {len(branches)} branches in repo {repo_name}")

                # If no branches were found, try the default branch
                if not branches:
                    logger.info(f"No branches found for {repo_name}, trying default branch")
                    branches = [{"name": repo.get("default_branch", "main")}]

                # Now get commits for each branch
                for branch in branches:
                    branch_name = branch["name"]
                    commits_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
                    commits_params = {
                        "since": since,
                        "per_page": 100,
                        "author": username,
                        "sha": branch_name
                    }

                    try:
                        commits_page = 1
                        while True:
                            commits_params["page"] = commits_page
                            commits_response = requests.get(commits_url, headers=headers, params=commits_params)
                            commits_response.raise_for_status()
                            commits = commits_response.json()

                            if not commits:
                                break

                            # Add unique commit SHAs to our set
                            for commit in commits:
                                unique_commits.add(commit["sha"])

                            logger.info(f"Found {len(commits)} commits in branch {branch_name} of repo {repo_name} (page {commits_page})")

                            # Check if we need to fetch more pages
                            if len(commits) < commits_params["per_page"]:
                                break

                            # Check if there's a next page using Link header
                            if "Link" in commits_response.headers:
                                if 'rel="next"' not in commits_response.headers["Link"]:
                                    break

                            commits_page += 1

                    except requests.exceptions.RequestException as e:
                        logger.warning(f"Error fetching commits for branch {branch_name} in repo {repo_name}: {e}")
                        # Continue with other branches instead of failing completely
                        continue

                logger.info(f"Found {len(unique_commits)} unique commits in repo {repo_name} since Jan 1")

            except requests.exceptions.RequestException as e:
                error_msg = f"Error fetching branches for repo {repo_name}: {e}"
                logger.error(error_msg)
                # Send error to Discord but continue with other repositories
                send_discord_alert(f"⚠️ {error_msg}")
                continue

        total_commits = len(unique_commits)
        logger.info(f"Found total of {total_commits} unique commits across all repositories and branches since Jan 1")
        return total_commits
    except Exception as e:
        error_msg = f"Error in get_commits_since_jan_1: {e}"
        logger.error(error_msg)
        send_discord_alert(f"⚠️ Error fetching commits: {error_msg}")
        return None

def get_follower_count(username, bearer_token):
    """
    Fetch the follower count for a Twitter user using Twitter API v2 directly.
    Returns None if there's an error.
    """
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    params = {
        "user.fields": "public_metrics"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        user_data = response.json()

        if "data" in user_data and "public_metrics" in user_data["data"]:
            followers_count = user_data["data"]["public_metrics"]["followers_count"]
            logger.info(f"Found {followers_count} Twitter followers")
            return followers_count
        else:
            error_msg = f"Unexpected response format: {user_data}"
            logger.error(error_msg)
            send_discord_alert(f"⚠️ Error fetching X followers: {error_msg}")
            return None
    except Exception as e:
        error_msg = f"Error fetching X follower count: {e}"
        logger.error(error_msg)
        send_discord_alert(f"⚠️ {error_msg}")
        return None

def get_historical_data():
    """
    Fetch historical data from S3 bucket
    """
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=S3_HISTORY_KEY)
        historical_data = json.loads(response['Body'].read().decode('utf-8'))
        logger.info(f"Successfully retrieved historical data from S3")
        return historical_data
    except s3.exceptions.NoSuchKey:
        logger.info(f"No historical data found, trying to restore from backup")
        try:
            # Try to restore from backup
            response = s3.get_object(Bucket=S3_BUCKET, Key=S3_HISTORY_BACKUP_KEY)
            historical_data = json.loads(response['Body'].read().decode('utf-8'))
            logger.info(f"Successfully restored historical data from backup")

            # Save the restored data to the main file
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=S3_HISTORY_KEY,
                Body=json.dumps(historical_data, indent=2).encode('utf-8'),
                ContentType='application/json'
            )
            logger.info(f"Restored backup data to main historical data file")

            return historical_data
        except s3.exceptions.NoSuchKey:
            logger.info(f"No backup historical data found either, creating new dataset")
            return {"data": []}
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            return {"data": []}
    except Exception as e:
        logger.error(f"Error retrieving historical data: {e}")
        send_discord_alert(f"⚠️ Error retrieving historical data: {e}")
        return {"data": []}

def update_historical_data(historical_data, commit_count, follower_count, ratio, youtube_subscribers, bluesky_followers):
    """
    Update historical data with current day's information.
    If any data point is None, use the most recent value from historical data.
    """
    # Get current date in PST timezone (without time)
    pacific_tz = pytz.timezone('America/Los_Angeles')
    current_datetime = datetime.now(pacific_tz)
    current_date = current_datetime.strftime("%Y-%m-%d")

    # Get the most recent entry to use as fallback for missing data
    most_recent_entry = None
    if historical_data["data"]:
        most_recent_entry = historical_data["data"][-1]

    # Use most recent values for any None data points
    if most_recent_entry:
        if commit_count is None:
            commit_count = most_recent_entry.get("github_commits", 0)
            logger.info(f"Using most recent GitHub commits value: {commit_count}")

        if follower_count is None:
            follower_count = most_recent_entry.get("twitter_followers", 1)
            logger.info(f"Using most recent Twitter followers value: {follower_count}")

        if youtube_subscribers is None:
            youtube_subscribers = most_recent_entry.get("youtube_subscribers", 0)
            logger.info(f"Using most recent YouTube subscribers value: {youtube_subscribers}")

        if bluesky_followers is None:
            bluesky_followers = most_recent_entry.get("bluesky_followers", 0)
            logger.info(f"Using most recent Bluesky followers value: {bluesky_followers}")

    # Calculate total followers (Twitter + YouTube + Bluesky)
    total_followers = (follower_count or 0) + (youtube_subscribers or 0) + (bluesky_followers or 0)
    logger.info(f"Calculated total followers: {total_followers}")

    # Always recalculate ratio after ensuring commit_count and total_followers are not None
    ratio = round((commit_count / total_followers if total_followers > 0 else 1) * 10) / 10
    logger.info(f"Calculated ratio: {ratio}")

    # Check if we already have an entry for today
    today_entry = None
    for entry in historical_data["data"]:
        if entry.get("date") == current_date:
            today_entry = entry
            break

    # Update existing entry or create a new one
    if today_entry:
        logger.info(f"Updating existing entry for {current_date}")
        today_entry["github_commits"] = commit_count
        today_entry["twitter_followers"] = follower_count
        today_entry["youtube_subscribers"] = youtube_subscribers
        today_entry["bluesky_followers"] = bluesky_followers
        today_entry["total_followers"] = total_followers
        today_entry["ratio"] = ratio
        today_entry["last_updated"] = current_datetime.isoformat()
    else:
        logger.info(f"Creating new entry for {current_date}")
        historical_data["data"].append({
            "date": current_date,
            "github_commits": commit_count,
            "twitter_followers": follower_count,
            "youtube_subscribers": youtube_subscribers,
            "bluesky_followers": bluesky_followers,
            "total_followers": total_followers,
            "ratio": ratio,
            "last_updated": current_datetime.isoformat()
        })

    return historical_data

def save_historical_data(historical_data):
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
        return True
    except Exception as e:
        logger.error(f"Error saving historical data: {e}")
        send_discord_alert(f"❌ Error saving historical data: {e}")
        return False

def handler(event, context):
    """
    Main Lambda handler function.

    Args:
        event (dict): The event data passed to the Lambda function
        context (LambdaContext): The runtime information provided by AWS Lambda

    Returns:
        dict: Response object
    """
    import time
    start_time = time.time()
    logger.info("Lambda function invoked with event: %s", json.dumps(event))

    try:
        # Check if required environment variables are set
        if not all([GITHUB_TOKEN, S3_BUCKET, TWITTER_BEARER_TOKEN]):
            missing_vars = []
            if not GITHUB_TOKEN: missing_vars.append("GITHUB_TOKEN")
            if not S3_BUCKET: missing_vars.append("S3_BUCKET")
            if not TWITTER_BEARER_TOKEN: missing_vars.append("TWITTER_BEARER_TOKEN")

            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            send_discord_alert(f"❌ {error_msg}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': error_msg})
            }

        # Get historical data first to have fallback values available
        logger.info("Fetching historical data...")
        historical_data_start = time.time()
        historical_data = get_historical_data()
        logger.info(f"Historical data fetched in {time.time() - historical_data_start:.2f} seconds")

        # Get GitHub commits and Twitter followers
        logger.info("Fetching GitHub commits...")
        github_start = time.time()
        commit_count = get_commits_since_jan_1(GITHUB_USERNAME, GITHUB_TOKEN)
        logger.info(f"GitHub commits fetched in {time.time() - github_start:.2f} seconds: {commit_count}")

        logger.info("Fetching Twitter followers...")
        twitter_start = time.time()
        follower_count = get_follower_count(TWITTER_USERNAME, TWITTER_BEARER_TOKEN)
        logger.info(f"Twitter followers fetched in {time.time() - twitter_start:.2f} seconds: {follower_count}")

        # Get YouTube subscribers
        youtube_subscribers = None
        try:
            logger.info("Fetching YouTube subscribers...")
            youtube_start = time.time()
            youtube_subscribers = get_youtube_subscriber_count(YOUTUBE_API_KEY, YOUTUBE_CHANNEL_ID)
            logger.info(f"YouTube subscribers fetched in {time.time() - youtube_start:.2f} seconds: {youtube_subscribers}")
        except Exception as e:
            error_msg = f"Error fetching YouTube subscribers: {e}"
            logger.error(error_msg)
            send_discord_alert(f"⚠️ {error_msg}")
            youtube_subscribers = None

        # Get Bluesky followers
        bluesky_followers = None
        try:
            if BLUESKY_API_KEY and BLUESKY_USERNAME:
                logger.info(f"Fetching Bluesky followers for {BLUESKY_USERNAME}")
                bluesky_start = time.time()
                bluesky_helper = BlueskyHelper(BLUESKY_API_KEY)
                bluesky_followers = bluesky_helper.get_total_followers(BLUESKY_USERNAME)
                logger.info(f"Bluesky followers fetched in {time.time() - bluesky_start:.2f} seconds: {bluesky_followers}")
        except Exception as e:
            error_msg = f"Error fetching Bluesky followers: {e}"
            logger.error(error_msg)
            send_discord_alert(f"⚠️ {error_msg}")
            bluesky_followers = None

        # We'll calculate the ratio inside update_historical_data after ensuring values are not None
        # So pass None for ratio here
        logger.info("Updating historical data...")
        update_start = time.time()
        updated_historical_data = update_historical_data(
            historical_data,
            commit_count,
            follower_count,
            None,  # Pass None for ratio, it will be calculated in the function
            youtube_subscribers,
            bluesky_followers
        )
        logger.info(f"Historical data updated in {time.time() - update_start:.2f} seconds")

        logger.info("Saving historical data...")
        save_start = time.time()
        save_historical_data(updated_historical_data)
        logger.info(f"Historical data saved in {time.time() - save_start:.2f} seconds")

        # Get the most recent entry which now has all the updated values
        most_recent_entry = updated_historical_data["data"][-1]
        commit_count = most_recent_entry["github_commits"]
        follower_count = most_recent_entry["twitter_followers"]
        youtube_subscribers = most_recent_entry["youtube_subscribers"]
        bluesky_followers = most_recent_entry["bluesky_followers"]
        total_followers = most_recent_entry["total_followers"]
        ratio = most_recent_entry["ratio"]

        # Calculate today's changes by comparing with yesterday's data
        commits_today = 0
        followers_today = 0

        if len(updated_historical_data["data"]) > 1:
            yesterday_entry = updated_historical_data["data"][-2]
            commits_today = commit_count - yesterday_entry["github_commits"]
            followers_today = total_followers - yesterday_entry["total_followers"]
            logger.info(f"Daily changes: +{commits_today} commits, +{followers_today} followers")
        else:
            logger.info("No previous data available to calculate daily changes")

        # Calculate weekly activity
        logger.info("Calculating weekly activity...")
        weekly_activity = calculate_weekly_activity(updated_historical_data)
        commits_week = weekly_activity["commits_week"]
        followers_week = weekly_activity["followers_week"]
        logger.info(f"Weekly changes: +{commits_week} commits, +{followers_week} followers")

        # Use the render_html_template function from utils.py with historical data
        logger.info("Rendering HTML template...")
        render_start = time.time()
        html_content = render_html_template(
            commit_count,
            follower_count,
            GITHUB_USERNAME,
            TWITTER_USERNAME,
            updated_historical_data,  # Pass the historical data to the template
            YOUTUBE_CHANNEL_ID,  # Pass the YouTube channel ID
            BLUESKY_USERNAME,  # Pass the Bluesky username
            commits_today,  # Pass the commits made today
            followers_today,  # Pass the followers gained today
            commits_week,  # Pass the commits made this week
            followers_week  # Pass the followers gained this week
        )
        logger.info(f"HTML template rendered in {time.time() - render_start:.2f} seconds")

        # Upload to S3
        try:
            logger.info("Uploading to S3...")
            s3_start = time.time()

            # First, create a backup of the existing index.html
            try:
                # Check if the file exists before trying to copy it
                s3.head_object(Bucket=S3_BUCKET, Key=S3_KEY)

                # Copy the existing file to a backup
                s3.copy_object(
                    Bucket=S3_BUCKET,
                    CopySource={'Bucket': S3_BUCKET, 'Key': S3_KEY},
                    Key=S3_KEY_BACKUP
                )
                logger.info(f"Created backup of index.html at s3://{S3_BUCKET}/{S3_KEY_BACKUP}")
            except s3.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '404':
                    logger.info(f"No existing index.html file to backup")
                else:
                    logger.warning(f"Error creating backup of index.html: {e}")

            # Upload HTML file
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=S3_KEY,
                Body=html_content.encode('utf-8'),
                ContentType='text/html',
                CacheControl='max-age=1800'  # 30 minutes in seconds, matching the Lambda schedule
            )
            logger.info(f"S3 upload completed in {time.time() - s3_start:.2f} seconds")
            logger.info(f"Successfully uploaded to s3://{S3_BUCKET}/{S3_KEY}")
        except Exception as e:
            error_msg = f"Error uploading to S3: {e}"
            logger.error(error_msg)
            send_discord_alert(f"❌ {error_msg}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': error_msg})
            }

        total_execution_time = time.time() - start_time
        logger.info(f"Total Lambda execution time: {total_execution_time:.2f} seconds")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'HTML updated and uploaded successfully!',
                'github_commits': commit_count,
                'twitter_followers': follower_count,
                'youtube_subscribers': youtube_subscribers,
                'bluesky_followers': bluesky_followers,
                'total_followers': total_followers,
                'ratio': ratio,
                'commits_today': commits_today,
                'followers_today': followers_today,
                'commits_week': commits_week,
                'followers_week': followers_week,
                'execution_time_seconds': total_execution_time
            })
        }
    except Exception as e:
        error_msg = f"Error in Lambda execution: {str(e)}"
        logger.error(error_msg)
        send_discord_alert(f"❌ {error_msg}")

        total_execution_time = time.time() - start_time
        logger.error(f"Lambda failed after {total_execution_time:.2f} seconds")

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg,
                'execution_time_seconds': total_execution_time
            })
        }

# Add this at the end of the file to ensure the handler is properly exposed
if __name__ == "__main__":
    # For local testing
    handler({}, None)