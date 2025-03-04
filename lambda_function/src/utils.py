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
        
        html {
            overflow-x: hidden; /* Prevent horizontal scrolling */
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }

        /* Animated gradient background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(
                    circle at 20% 30%, 
                    rgba(35, 134, 54, 0.03) 0%, 
                    transparent 50%
                ),
                radial-gradient(
                    circle at 80% 70%, 
                    rgba(29, 155, 240, 0.03) 0%, 
                    transparent 50%
                );
            z-index: -2;
            animation: gradientShift 15s ease infinite alternate;
        }

        @keyframes gradientShift {
            0% {
                background-position: 0% 0%;
            }
            100% {
                background-position: 100% 100%;
            }
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }

        header {
            text-align: center;
            margin-bottom: 40px;
            position: relative;
        }

        /* Particles around logo */
        .particles-container {
            position: absolute;
            top: -80px;
            right: -80px;
            width: 160px;
            height: 160px;
            z-index: -1;
            pointer-events: none;
        }

        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background-color: var(--accent-github);
            opacity: 0;
            animation: particle-animation 3s ease-in-out infinite;
        }

        .particle:nth-child(even) {
            background-color: var(--accent-twitter);
        }

        .particle:nth-child(1) { top: 20%; left: 30%; animation-delay: 0s; }
        .particle:nth-child(2) { top: 70%; left: 60%; animation-delay: 0.3s; }
        .particle:nth-child(3) { top: 40%; left: 80%; animation-delay: 0.6s; }
        .particle:nth-child(4) { top: 60%; left: 20%; animation-delay: 0.9s; }
        .particle:nth-child(5) { top: 30%; left: 50%; animation-delay: 1.2s; }
        .particle:nth-child(6) { top: 80%; left: 40%; animation-delay: 1.5s; }
        .particle:nth-child(7) { top: 50%; left: 70%; animation-delay: 1.8s; }
        .particle:nth-child(8) { top: 10%; left: 60%; animation-delay: 2.1s; }

        @keyframes particle-animation {
            0% {
                transform: scale(0) translate(0, 0);
                opacity: 0;
            }
            50% {
                opacity: 0.8;
                transform: scale(1) translate(10px, 10px);
            }
            100% {
                transform: scale(0) translate(20px, 20px);
                opacity: 0;
            }
        }

        /* Floating logo animation */
        .floating-logo {
            position: absolute;
            top: -60px;
            right: -60px;
            width: 120px;
            height: 120px;
            opacity: 0.7;
            animation: float 6s ease-in-out infinite;
            z-index: -1;
            pointer-events: none; /* Prevent interaction with the logo */
            transform-origin: center; /* Ensure rotation happens from center */
        }

        .floating-logo img {
            width: 100%;
            height: 100%;
            filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.2));
            animation: rotate 20s linear infinite;
        }

        @keyframes float {
            0% {
                transform: translateY(0px);
            }
            50% {
                transform: translateY(-15px);
            }
            100% {
                transform: translateY(0px);
            }
        }

        @keyframes rotate {
            0% {
                transform: rotate(0deg);
            }
            100% {
                transform: rotate(360deg);
            }
        }

        /* Glowing effect for the logo */
        .logo-glow {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(
                circle at center,
                rgba(35, 134, 54, 0.3) 0%,
                rgba(29, 155, 240, 0.3) 50%,
                transparent 70%
            );
            filter: blur(15px);
            opacity: 0.5;
            animation: pulse 4s ease-in-out infinite alternate;
        }

        @keyframes pulse {
            0% {
                opacity: 0.3;
                transform: scale(0.95);
            }
            100% {
                opacity: 0.6;
                transform: scale(1.05);
            }
        }

        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, var(--accent-github), var(--accent-twitter));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            position: relative;
            z-index: 1;
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
            
            /* Hide chart container on mobile screens */
            .chart-container {
                display: none;
            }
            
            /* Make social links display in a column on mobile */
            .social-links {
                flex-direction: column;
                align-items: center;
                gap: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <!-- Particles around logo -->
            <div class="particles-container">
                <div class="particle"></div>
                <div class="particle"></div>
                <div class="particle"></div>
                <div class="particle"></div>
                <div class="particle"></div>
                <div class="particle"></div>
                <div class="particle"></div>
                <div class="particle"></div>
            </div>
            
            <!-- Floating animated logo -->
            <div class="floating-logo">
                <div class="logo-glow"></div>
                <img src="/favicon.svg" alt="Commits or Clout Logo">
            </div>
            
            <h1>Commits or Clout</h1>
            <p class="subtitle">Tracking my GitHub activity vs. social media following</p>
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
                    <a href="https://willness.dev?tab=socials" target="_blank" style="color: inherit; text-decoration: none; display: flex; align-items: center;">
                        <svg height="24" width="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M17.9,17.39C17.64,16.59 16.89,16 16,16H15V13A1,1 0 0,0 14,12H8V10H10A1,1 0 0,0 11,9V7H13A2,2 0 0,0 15,5V4.59C17.93,5.77 20,8.64 20,12C20,14.19 19.2,15.8 17.9,17.39M11,19.93C7.05,19.44 4,16.08 4,12C4,11.38 4.08,10.78 4.21,10.21L9,15V16A2,2 0 0,0 11,18M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z" />
                        </svg>
                        Total Followers
                    </a>
                </div>
                <a href="https://willness.dev?tab=socials" target="_blank" style="text-decoration: none;">
                    <div class="stat-value">{{ total_followers }}</div>
                </a>
                <div class="stat-description">Combined social media followers</div>
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

        <!-- Social Media Breakdown -->
        <div class="stats-container">
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
                <div class="stat-description">Current X/Twitter follower count</div>
            </div>

            <div class="stat-card" style="border-top: 4px solid #FF0000;">
                <div class="stat-title">
                    <a href="https://www.youtube.com/channel/{{ youtube_channel_id }}" target="_blank" style="color: inherit; text-decoration: none; display: flex; align-items: center;">
                        <svg height="24" width="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M10,15L15.19,12L10,9V15M21.56,7.17C21.69,7.64 21.78,8.27 21.84,9.07C21.91,9.87 21.94,10.56 21.94,11.16L22,12C22,14.19 21.84,15.8 21.56,16.83C21.31,17.73 20.73,18.31 19.83,18.56C19.36,18.69 18.5,18.78 17.18,18.84C15.88,18.91 14.69,18.94 13.59,18.94L12,19C7.81,19 5.2,18.84 4.17,18.56C3.27,18.31 2.69,17.73 2.44,16.83C2.31,16.36 2.22,15.73 2.16,14.93C2.09,14.13 2.06,13.44 2.06,12.84L2,12C2,9.81 2.16,8.2 2.44,7.17C2.69,6.27 3.27,5.69 4.17,5.44C4.64,5.31 5.5,5.22 6.82,5.16C8.12,5.09 9.31,5.06 10.41,5.06L12,5C16.19,5 18.8,5.16 19.83,5.44C20.73,5.69 21.31,6.27 21.56,7.17Z" />
                        </svg>
                        YouTube Subscribers
                    </a>
                </div>
                <a href="https://www.youtube.com/channel/{{ youtube_channel_id }}" target="_blank" style="text-decoration: none;">
                    <div class="stat-value" style="color: #FF0000;">{{ youtube_subscribers }}</div>
                </a>
                <div class="stat-description">Current YouTube subscriber count</div>
            </div>
            
            <div class="stat-card" style="border-top: 4px solid #0085ff;">
                <div class="stat-title">
                    <a href="https://bsky.app/profile/{{ bluesky_username }}" target="_blank" style="color: inherit; text-decoration: none; display: flex; align-items: center;">
                        <svg height="24" width="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12.001 2C6.47598 2 2.00098 6.475 2.00098 12C2.00098 17.525 6.47598 22 12.001 22C17.526 22 22.001 17.525 22.001 12C22.001 6.475 17.526 2 12.001 2ZM12.001 4C16.421 4 20.001 7.58 20.001 12C20.001 16.42 16.421 20 12.001 20C7.58098 20 4.00098 16.42 4.00098 12C4.00098 7.58 7.58098 4 12.001 4ZM12.001 7C9.79098 7 8.00098 8.79 8.00098 11C8.00098 13.21 9.79098 15 12.001 15C14.211 15 16.001 13.21 16.001 11C16.001 8.79 14.211 7 12.001 7Z" />
                        </svg>
                        Bluesky Followers
                    </a>
                </div>
                <a href="https://bsky.app/profile/{{ bluesky_username }}" target="_blank" style="text-decoration: none;">
                    <div class="stat-value" style="color: #0085ff;">{{ bluesky_followers }}</div>
                </a>
                <div class="stat-description">Current Bluesky follower count</div>
            </div>
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
                {% if bluesky_username %}
                <a href="https://bsky.app/profile/{{ bluesky_username }}" target="_blank">
                    <svg height="16" width="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12.001 2C6.47598 2 2.00098 6.475 2.00098 12C2.00098 17.525 6.47598 22 12.001 22C17.526 22 22.001 17.525 22.001 12C22.001 6.475 17.526 2 12.001 2ZM12.001 4C16.421 4 20.001 7.58 20.001 12C20.001 16.42 16.421 20 12.001 20C7.58098 20 4.00098 16.42 4.00098 12C4.00098 7.58 7.58098 4 12.001 4ZM12.001 7C9.79098 7 8.00098 8.79 8.00098 11C8.00098 13.21 9.79098 15 12.001 15C14.211 15 16.001 13.21 16.001 11C16.001 8.79 14.211 7 12.001 7Z" />
                    </svg>
                    @{{ bluesky_username }}
                </a>
                {% endif %}
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
        const youtubeSubscribers = historicalData.data.map(entry => entry.youtube_subscribers || 0);
        const blueskyFollowers = historicalData.data.map(entry => entry.bluesky_followers || 0);
        const totalFollowers = historicalData.data.map(entry => entry.total_followers || entry.twitter_followers);
        
        // Function to determine point radius based on dataset size
        const getPointRadius = (dataLength) => {
            if (dataLength > 100) return 0;  // Hide points for large datasets
            if (dataLength > 60) return 1;   // Very small points for medium-large datasets
            return 2;                        // Default size for smaller datasets
        };
        
        // Set point radius based on dataset size
        const pointRadius = getPointRadius(dates.length);
        
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
                        pointBackgroundColor: '#238636',
                        pointRadius: pointRadius,
                        pointHoverRadius: 4
                    },
                    {
                        label: 'Total Followers',
                        data: totalFollowers,
                        borderColor: '#9c27b0',
                        backgroundColor: 'rgba(156, 39, 176, 0.1)',
                        borderWidth: 2,
                        tension: 0.1,
                        pointBackgroundColor: '#9c27b0',
                        pointRadius: pointRadius,
                        pointHoverRadius: 4
                    },
                    {
                        label: 'X/Twitter Followers',
                        data: followers,
                        borderColor: '#1d9bf0',
                        backgroundColor: 'rgba(29, 155, 240, 0.1)',
                        borderWidth: 2,
                        tension: 0.1,
                        pointBackgroundColor: '#1d9bf0',
                        pointRadius: pointRadius,
                        pointHoverRadius: 4
                    },
                    {
                        label: 'YouTube Subscribers',
                        data: youtubeSubscribers,
                        borderColor: '#FF0000',
                        backgroundColor: 'rgba(255, 0, 0, 0.1)',
                        borderWidth: 2,
                        tension: 0.1,
                        pointBackgroundColor: '#FF0000',
                        pointRadius: pointRadius,
                        pointHoverRadius: 4
                    },
                    {
                        label: 'Bluesky Followers',
                        data: blueskyFollowers,
                        borderColor: '#0085ff',
                        backgroundColor: 'rgba(0, 133, 255, 0.1)',
                        borderWidth: 2,
                        tension: 0.1,
                        pointBackgroundColor: '#0085ff',
                        pointRadius: pointRadius,
                        pointHoverRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                elements: {
                    point: {
                        radius: 2,
                        hoverRadius: 4,
                        hitRadius: 6
                    },
                    line: {
                        borderWidth: 2
                    }
                },
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
                    },
                    decimation: {
                        enabled: true,
                        algorithm: 'min-max'
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

def render_html_template(commit_count, follower_count, github_username, twitter_username, historical_data=None, youtube_channel_id=None, bluesky_username=None):
    """
    Render the HTML template with the provided data
    
    Args:
        commit_count (int): Number of GitHub commits
        follower_count (int): Number of Twitter followers
        github_username (str): GitHub username
        twitter_username (str): Twitter username
        historical_data (dict, optional): Historical data for the chart
        youtube_channel_id (str, optional): YouTube channel ID for linking to the channel
        bluesky_username (str, optional): Bluesky username for linking to the profile
        
    Returns:
        str: Rendered HTML content
    """
    # Get YouTube subscribers, Bluesky followers, and total followers from historical data
    youtube_subscribers = 0
    bluesky_followers = 0
    total_followers = follower_count
    
    if historical_data and "data" in historical_data and historical_data["data"]:
        latest_entry = historical_data["data"][-1]
        youtube_subscribers = latest_entry.get("youtube_subscribers", 0)
        bluesky_followers = latest_entry.get("bluesky_followers", 0)
        total_followers = latest_entry.get("total_followers", follower_count)
    
    # Calculate ratio based on total followers
    ratio = round((commit_count / total_followers if total_followers > 0 else 1) * 10) / 10
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
        youtube_subscribers=youtube_subscribers,
        bluesky_followers=bluesky_followers,
        total_followers=total_followers,
        ratio_text=ratio_text,
        ratio_text_subtitle=ratio_text_subtitle,
        github_username=github_username,
        twitter_username=twitter_username,
        youtube_channel_id=youtube_channel_id or "",
        bluesky_username=bluesky_username or "",
        last_updated=current_date,
        historical_data_json=historical_data_json
    )
    
    return html_content 