import json
import logging
import requests
import os
import boto3
# import tweepy  # Remove tweepy import
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader, Template

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

        # Calculate the ratio (rounded to 1 decimal place)
        ratio = round((commit_count / follower_count if follower_count > 0 else 1) * 10) / 10
        current_year = datetime.now().year
        ratio_text = f"I have {ratio}x as many commits in {current_year} as followers"

        # Generate the ratio text subtitle
        ratio_text_subtitle = "Focusing more on building than on social media presence!" if ratio > 1 else "I need to build more..."
        
        # Format the current date
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # HTML template
        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Commits or Clout</title>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --accent-github: #238636;
            --accent-twitter: #1d9bf0;
            --border-color: #30363d;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }

        header {
            text-align: center;
            margin-bottom: 40px;
        }

        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, var(--accent-github), var(--accent-twitter));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            color: var(--text-secondary);
            font-size: 1.2rem;
        }

        .stats-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 40px;
        }

        .stat-card {
            flex: 1;
            min-width: 250px;
            background-color: var(--card-bg);
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--border-color);
            transition: transform 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .github-card {
            border-top: 4px solid var(--accent-github);
        }

        .twitter-card {
            border-top: 4px solid var(--accent-twitter);
        }

        .stat-title {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            font-size: 1.2rem;
            color: var(--text-secondary);
        }

        .stat-title svg {
            margin-right: 10px;
        }

        .stat-value {
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .github-card .stat-value {
            color: var(--accent-github);
        }

        .twitter-card .stat-value {
            color: var(--accent-twitter);
        }

        .stat-description {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .comparison-card {
            background-color: var(--card-bg);
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 40px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--border-color);
            text-align: center;
        }

        .ratio {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 20px 0;
            background: linear-gradient(90deg, var(--accent-github), var(--accent-twitter));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .footer {
            text-align: center;
            margin-top: 40px;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .footer a {
            color: var(--text-primary);
            text-decoration: none;
        }

        .footer a:hover {
            text-decoration: underline;
        }
        
        .social-links {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 10px;
        }
        
        .social-links a {
            display: flex;
            align-items: center;
        }
        
        .social-links svg {
            margin-right: 5px;
        }

        .last-updated {
            margin-top: 10px;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        @media (max-width: 600px) {
            .stats-container {
                flex-direction: column;
            }
            
            h1 {
                font-size: 2rem;
            }
            
            .stat-value {
                font-size: 2.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Commits or Clout</h1>
            <p class="subtitle">Tracking my GitHub activity vs. Twitter following</p>
        </header>

        <div class="stats-container">
            <div class="stat-card github-card">
                <div class="stat-title">
                    <svg height="24" width="24" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                    </svg>
                    GitHub Commits
                </div>
                <div class="stat-value">{{ github_commits }}</div>
                <div class="stat-description">Total commits since January 1st</div>
            </div>

            <div class="stat-card twitter-card">
                <div class="stat-title">
                    <svg height="24" width="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"></path>
                    </svg>
                    Twitter Followers
                </div>
                <div class="stat-value">{{ twitter_followers }}</div>
                <div class="stat-description">Current follower count</div>
            </div>
        </div>

        <div class="comparison-card">
            <h2>Commits vs. Clout</h2>
            <div class="ratio">{{ ratio_text }}</div>
            <p>{{ ratio_text_subtitle }}</p>
        </div>

        <div class="footer">
            <p>Created with ❤️ by</p>
            <div class="social-links">
                <a href="https://github.com/{{ github_username }}" target="_blank">
                    <svg height="16" width="16" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                    </svg>
                    @{{ github_username }}
                </a>
                <a href="https://twitter.com/{{ twitter_username }}" target="_blank">
                    <svg height="16" width="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"></path>
                    </svg>
                    @{{ twitter_username }}
                </a>
            </div>
            <p class="last-updated">Last updated: <span id="last-updated">{{ last_updated }}</span></p>
        </div>
    </div>
</body>
</html>"""

        # Create a Jinja2 template from the HTML string
        template = Template(html_template)

        # Render the template with the data
        html_content = template.render(
            github_commits=commit_count,
            twitter_followers=follower_count,
            ratio_text=ratio_text,
            ratio_text_subtitle=ratio_text_subtitle,
            github_username=GITHUB_USERNAME,
            twitter_username=TWITTER_USERNAME,
            last_updated=current_date
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
                'twitter_followers': follower_count,
                'ratio': ratio
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