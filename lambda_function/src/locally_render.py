#!/usr/bin/env python3
"""
Script to locally render the Commits or Clout HTML page with fake data
"""
import os
import sys
import json
from datetime import datetime, timedelta
from utils import render_html_template

def generate_fake_historical_data(days=28):
    """
    Generate fake historical data for the past 4 weeks
    
    Args:
        days (int): Number of days of historical data to generate
        
    Returns:
        dict: Dictionary containing fake historical data
    """
    data = []
    today = datetime.now().date()
    
    # Start with base values
    base_commits = 200
    base_followers = 80
    
    # Generate data for each day with some variation
    for i in range(days, 0, -1):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        # Add some random-like variation to the data
        day_commits = base_commits + (i * 2) + ((i % 7) * 5)  # Increasing trend with weekly pattern
        day_followers = base_followers + (i // 2)  # Slower increasing trend
        
        # Calculate ratio
        ratio = round((day_commits / day_followers if day_followers > 0 else 1) * 10) / 10
        
        # Create entry
        entry = {
            "date": date_str,
            "github_commits": day_commits,
            "twitter_followers": day_followers,
            "ratio": ratio,
            "last_updated": f"{date_str}T12:00:00-08:00"
        }
        data.append(entry)
    
    return {"data": data}

def main():
    """
    Generate a local HTML file with fake data
    """
    # Fake data for local rendering
    commit_count = 250
    follower_count = 100
    github_username = "your_github_username"
    twitter_username = "your_twitter_username"
    
    # Generate fake historical data (4 weeks)
    historical_data = generate_fake_historical_data(300)
    
    # Print summary of the historical data
    print(f"Generated {len(historical_data['data'])} days of fake historical data")
    print(f"First day: {historical_data['data'][0]['date']}, "
          f"Commits: {historical_data['data'][0]['github_commits']}, "
          f"Followers: {historical_data['data'][0]['twitter_followers']}")
    print(f"Last day: {historical_data['data'][-1]['date']}, "
          f"Commits: {historical_data['data'][-1]['github_commits']}, "
          f"Followers: {historical_data['data'][-1]['twitter_followers']}")
    
    # Render the HTML template with historical data
    html_content = render_html_template(
        commit_count=commit_count,
        follower_count=follower_count,
        github_username=github_username,
        twitter_username=twitter_username,
        historical_data=historical_data
    )
    
    # Write to index.html file
    output_file = "index.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Also save the historical data to a JSON file for reference
    with open("historical_data.json", "w", encoding="utf-8") as f:
        json.dump(historical_data, f, indent=2)
    
    print(f"HTML file generated at: {os.path.abspath(output_file)}")
    print(f"Historical data saved to: {os.path.abspath('historical_data.json')}")
    print("Open the HTML file in your browser to preview the page with the chart.")

if __name__ == "__main__":
    main() 