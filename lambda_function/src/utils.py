import json
import logging
from datetime import datetime
from jinja2 import Template
import pytz

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_html_template():
    """
    Returns the HTML template for the Commits or Clout website
    """
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Commits or Clout</title>
    <!-- Favicon links -->
    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png">
    <link rel="manifest" href="/site.webmanifest">
    <!-- Add Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Plausible Analytics -->
    <script defer data-domain="commits.willness.dev" src="https://plausible.io/js/script.js"></script>
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

        /* Chart container styles */
        .chart-container {
            background-color: var(--card-bg);
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 40px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--border-color);
        }

        .chart-title {
            text-align: center;
            margin-bottom: 20px;
            font-size: 1.5rem;
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
            <p class="subtitle">Tracking my GitHub activity vs. X/Twitter following</p>
        </header>

        <div class="stats-container">
            <div class="stat-card github-card">
                <div class="stat-title">
                    <a href="https://github.com/{{ github_username }}" target="_blank" style="color: inherit; text-decoration: none; display: flex; align-items: center;">
                        <svg height="24" width="24" viewBox="0 0 16 16" fill="currentColor">
                            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                        </svg>
                        GitHub Commits
                    </a>
                </div>
                <a href="https://github.com/{{ github_username }}" target="_blank" style="text-decoration: none;">
                    <div class="stat-value">{{ github_commits }}</div>
                </a>
                <div class="stat-description">Total commits since January 1st</div>
            </div>

            <div class="stat-card twitter-card">
                <div class="stat-title">
                    <a href="https://twitter.com/{{ twitter_username }}" target="_blank" style="color: inherit; text-decoration: none; display: flex; align-items: center;">
                        <svg height="24" width="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"></path>
                        </svg>
                        X/Twitter Followers
                    </a>
                </div>
                <a href="https://twitter.com/{{ twitter_username }}" target="_blank" style="text-decoration: none;">
                    <div class="stat-value">{{ twitter_followers }}</div>
                </a>
                <div class="stat-description">Current follower count</div>
            </div>
        </div>

        <div class="comparison-card">
            <h2>Commits vs. Clout</h2>
            <div class="ratio">{{ ratio_text }}</div>
            <p>{{ ratio_text_subtitle }}</p>
        </div>

        <!-- Chart container -->
        <div class="chart-container">
            <h2 class="chart-title">Historical Data</h2>
            <canvas id="historyChart"></canvas>
        </div>

        <div class="footer">
            <p>Created with ❤️ by <a href="https://willness.dev" target="_blank">willness.dev</a></p>
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

    <!-- Chart.js initialization script -->
    <script>
        // Parse the historical data from the template
        const historicalData = {{ historical_data_json|safe }};
        
        // Extract dates and values for the chart
        const dates = historicalData.data.map(entry => entry.date);
        const commits = historicalData.data.map(entry => entry.github_commits);
        const followers = historicalData.data.map(entry => entry.twitter_followers);
        
        // Create the chart
        const ctx = document.getElementById('historyChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'GitHub Commits',
                        data: commits,
                        borderColor: '#238636',
                        backgroundColor: 'rgba(35, 134, 54, 0.1)',
                        borderWidth: 2,
                        tension: 0.1,
                        pointBackgroundColor: '#238636'
                    },
                    {
                        label: 'X/Twitter Followers',
                        data: followers,
                        borderColor: '#1d9bf0',
                        backgroundColor: 'rgba(29, 155, 240, 0.1)',
                        borderWidth: 2,
                        tension: 0.1,
                        pointBackgroundColor: '#1d9bf0'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#f0f6fc'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#8b949e'
                        },
                        grid: {
                            color: 'rgba(48, 54, 61, 0.5)'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#8b949e'
                        },
                        grid: {
                            color: 'rgba(48, 54, 61, 0.5)'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    </script>
</body>
</html>"""

def render_html_template(commit_count, follower_count, github_username, twitter_username, historical_data=None):
    """
    Render the HTML template with the provided data
    
    Args:
        commit_count (int): Number of GitHub commits
        follower_count (int): Number of Twitter followers
        github_username (str): GitHub username
        twitter_username (str): Twitter username
        historical_data (dict, optional): Historical data for the chart
        
    Returns:
        str: Rendered HTML content
    """
    # Calculate the ratio (rounded to 1 decimal place)
    ratio = round((commit_count / follower_count if follower_count > 0 else 1) * 10) / 10
    current_year = datetime.now().year
    ratio_text = f"I have {ratio}x as many commits in {current_year} as followers"

    # Generate the ratio text subtitle
    ratio_text_subtitle = "Focusing more on building than on social media presence!" if ratio > 1 else "I need to build more..."
    
    # Format the current date with time in PST timezone
    pacific_tz = pytz.timezone('America/Los_Angeles')
    current_datetime = datetime.now(pacific_tz)
    timezone_name = "PDT" if current_datetime.dst() else "PST"
    current_date = current_datetime.strftime("%B %d, %Y at %I:%M %p") + f" {timezone_name}"
    
    # If no historical data is provided, create a minimal structure
    if historical_data is None:
        historical_data = {"data": []}
    
    # Convert historical data to JSON for the template
    historical_data_json = json.dumps(historical_data)
    
    # Create a Jinja2 template from the HTML string
    template = Template(get_html_template())

    # Render the template with the data
    html_content = template.render(
        github_commits=commit_count,
        twitter_followers=follower_count,
        ratio_text=ratio_text,
        ratio_text_subtitle=ratio_text_subtitle,
        github_username=github_username,
        twitter_username=twitter_username,
        last_updated=current_date,
        historical_data_json=historical_data_json
    )
    
    return html_content 