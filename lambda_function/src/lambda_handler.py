import json
import logging
import requests
import os
import boto3
# import tweepy  # Remove tweepy import
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "your_github_username")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")
TWITTER_USERNAME = os.environ.get("TWITTER_USERNAME", "your_twitter_username")
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_KEY = os.environ.get("S3_KEY", "index.html")  # The path to your index.html in the S3 bucket

def get_user_repositories(username, token):
    """
    Fetch all repositories for a GitHub user.
    """
    url = f"https://api.github.com/users/{username}/repos"
    headers = {"Authorization": f"token {token}"}
    params = {"per_page": 100}  # Maximum 100 repos per page
    all_repos = []
    
    try:
        # Handle pagination
        while url:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            repos = response.json()
            all_repos.extend(repos)
            
            # Check if there are more pages
            if 'next' in response.links:
                url = response.links['next']['url']
                params = {}  # Parameters are included in the next URL
            else:
                url = None
                
        logger.info(f"Found {len(all_repos)} repositories for user {username}")
        return all_repos
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching repositories: {e}")
        return []

def get_commits_since_jan_1(username, token):
    """
    Fetch the number of commits made to all GitHub repositories since January 1st.
    """
    since = datetime(2025, 1, 1, tzinfo=timezone.utc).isoformat()
    headers = {"Authorization": f"token {token}"}
    params = {"since": since}
    total_commits = 0
    
    try:
        # First get all repositories
        repositories = get_user_repositories(username, token)
        
        for repo in repositories:
            repo_name = repo['name']
            url = f"https://api.github.com/repos/{username}/{repo_name}/commits"
            
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                commits = response.json()
                
                # Add commits from this repo to total
                repo_commits = len(commits)
                total_commits += repo_commits
                logger.info(f"Found {repo_commits} commits in repo {repo_name} since Jan 1")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching commits for repo {repo_name}: {e}")
                # Continue with other repos even if one fails
                continue
        
        logger.info(f"Found total of {total_commits} commits across all repositories since Jan 1")
        return total_commits
    except Exception as e:
        logger.error(f"Error in get_commits_since_jan_1: {e}")
        return 0

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
            logger.error(f"Unexpected response format: {user_data}")
            return 0
    except Exception as e:
        logger.error(f"Error fetching follower count: {e}")
        return 0

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
            return {
                'statusCode': 500,
                'body': json.dumps({'error': error_msg})
            }
        
        # Get GitHub commits and Twitter followers
        commit_count = get_commits_since_jan_1(GITHUB_USERNAME, GITHUB_TOKEN)
        follower_count = get_follower_count(TWITTER_USERNAME, TWITTER_BEARER_TOKEN)

        # Load Jinja2 template
        env = Environment(loader=FileSystemLoader('/tmp'))
        
        # First, check if the template exists in /tmp, if not, create it
        template_path = '/tmp/index.html.j2'
        if not os.path.exists(template_path):
            # You might want to download the template from S3 or include it in the deployment package
            # For now, we'll create a simple template
            with open(template_path, 'w') as f:
                f.write("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>GitHub and Twitter Stats</title>
                </head>
                <body>
                    <h1>My Stats</h1>
                    <p>GitHub Commits across all repositories since Jan 1: {{ github_commits }}</p>
                    <p>Twitter Followers: {{ twitter_followers }}</p>
                    <p>Last updated: {{ last_updated }}</p>
                </body>
                </html>
                """)
        
        template = env.get_template('index.html.j2')

        # Render the template with the data
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_content = template.render(
            github_commits=commit_count, 
            twitter_followers=follower_count,
            last_updated=current_time
        )

        # Upload to S3
        s3 = boto3.client('s3')
        try:
            s3.put_object(
                Bucket=S3_BUCKET, 
                Key=S3_KEY, 
                Body=html_content.encode('utf-8'), 
                ContentType='text/html'
            )
            logger.info(f"Successfully uploaded to s3://{S3_BUCKET}/{S3_KEY}")
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f"Error uploading to S3: {str(e)}"})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'HTML updated and uploaded successfully!',
                'github_commits': commit_count,
                'twitter_followers': follower_count
            })
        }
    except Exception as e:
        logger.error("Error in Lambda execution: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        } 