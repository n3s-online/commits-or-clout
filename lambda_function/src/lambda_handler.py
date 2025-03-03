import json
import logging
import requests
import os
import boto3
# import tweepy  # Remove tweepy import
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader, Template
import pytz
from utils import get_html_template, render_html_template  # Import the utility functions
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
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_KEY = os.environ.get("S3_KEY", "index.html")
S3_KEY_BACKUP = os.environ.get("S3_KEY_BACKUP", "index_backup.html")
S3_HISTORY_KEY = os.environ.get("S3_HISTORY_KEY", "historical_data.json")
S3_HISTORY_BACKUP_KEY = os.environ.get("S3_HISTORY_BACKUP_KEY", "historical_data_backup.json")
SSM_PARAM_NAME = os.environ.get('SSM_PARAM_NAME', '/commits-or-clout/historical-data')

# Retrieve actual values from Parameter Store
GITHUB_TOKEN = get_parameter(GITHUB_TOKEN_PARAM_NAME)
GITHUB_USERNAME = get_parameter(GITHUB_USERNAME_PARAM_NAME, False) or GITHUB_USERNAME
TWITTER_USERNAME = get_parameter(TWITTER_USERNAME_PARAM_NAME, False) or TWITTER_USERNAME
TWITTER_BEARER_TOKEN = get_parameter(TWITTER_BEARER_TOKEN_PARAM_NAME)
DISCORD_WEBHOOK_URL = get_parameter(DISCORD_WEBHOOK_URL_PARAM_NAME, False)

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
    Fetch the number of commits made to all GitHub repositories since January 1st.
    """
    current_year = datetime.now().year
    since = datetime(current_year, 1, 1, tzinfo=timezone.utc).isoformat()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    params = {"since": since, "per_page": 100}  # Increase page size and add pagination
    total_commits = 0
    
    try:
        # First get all repositories
        repositories = get_user_repositories(username, token)
        
        for repo in repositories:
            repo_name = repo['name']
            url = f"https://api.github.com/repos/{username}/{repo_name}/commits"
            repo_commits = 0
            
            try:
                page = 1
                while True:
                    params["page"] = page
                    response = requests.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    commits = response.json()
                    
                    # Add commits from this page to repo total
                    page_commits = len(commits)
                    repo_commits += page_commits
                    
                    # Check if we need to fetch more pages
                    if page_commits < params["per_page"]:
                        break  # No more pages
                    
                    # Check if there's a next page using Link header
                    if "Link" in response.headers:
                        if 'rel="next"' not in response.headers["Link"]:
                            break
                    
                    page += 1
                
                total_commits += repo_commits
                logger.info(f"Found {repo_commits} commits in repo {repo_name} since Jan 1")
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Error fetching commits for repo {repo_name}: {e}"
                logger.error(error_msg)
                # Send error to Discord and exit early
                send_discord_alert(f"❌ {error_msg}")
                raise Exception(error_msg)
        
        logger.info(f"Found total of {total_commits} commits across all repositories since Jan 1")
        return total_commits
    except Exception as e:
        error_msg = f"Error in get_commits_since_jan_1: {e}"
        logger.error(error_msg)
        # Send error to Discord and exit early
        send_discord_alert(f"❌ Error fetching commits: {error_msg}")
        raise Exception(error_msg)

def get_follower_count(username, bearer_token):
    """
    Fetch the follower count for a Twitter user using Twitter API v2 directly.
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
            send_discord_alert(f"❌ Error fetching X followers: {error_msg}")
            raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Error fetching X follower count: {e}"
        logger.error(error_msg)
        send_discord_alert(f"❌ {error_msg}")
        raise Exception(error_msg)

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

def update_historical_data(historical_data, commit_count, follower_count, ratio):
    """
    Update historical data with current day's information
    """
    # Get current date in PST timezone (without time)
    pacific_tz = pytz.timezone('America/Los_Angeles')
    current_datetime = datetime.now(pacific_tz)
    current_date = current_datetime.strftime("%Y-%m-%d")
    
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
        today_entry["ratio"] = ratio
        today_entry["last_updated"] = current_datetime.isoformat()
    else:
        logger.info(f"Creating new entry for {current_date}")
        historical_data["data"].append({
            "date": current_date,
            "github_commits": commit_count,
            "twitter_followers": follower_count,
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
        
        # Get GitHub commits and Twitter followers
        commit_count = get_commits_since_jan_1(GITHUB_USERNAME, GITHUB_TOKEN)
        follower_count = get_follower_count(TWITTER_USERNAME, TWITTER_BEARER_TOKEN)

        # Calculate the ratio (rounded to 1 decimal place)
        ratio = round((commit_count / follower_count if follower_count > 0 else 1) * 10) / 10
        
        # Get and update historical data
        historical_data = get_historical_data()
        updated_historical_data = update_historical_data(historical_data, commit_count, follower_count, ratio)
        save_historical_data(updated_historical_data)
        
        # Use the render_html_template function from utils.py with historical data
        html_content = render_html_template(
            commit_count, 
            follower_count, 
            GITHUB_USERNAME, 
            TWITTER_USERNAME,
            updated_historical_data  # Pass the historical data to the template
        )

        # Upload to S3
        try:
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
            logger.info(f"Successfully uploaded to s3://{S3_BUCKET}/{S3_KEY}")
        except Exception as e:
            error_msg = f"Error uploading to S3: {e}"
            logger.error(error_msg)
            send_discord_alert(f"❌ {error_msg}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': error_msg})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'HTML updated and uploaded successfully!',
                'github_commits': commit_count,
                'twitter_followers': follower_count,
                'ratio': ratio
            })
        }
    except Exception as e:
        error_msg = f"Error in Lambda execution: {str(e)}"
        logger.error(error_msg)
        send_discord_alert(f"❌ {error_msg}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        } 