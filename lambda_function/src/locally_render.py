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
    base_youtube_subscribers = 12  
    base_bluesky_followers = 10
    # Generate data for each day with some variation
    for i in range(days, 0, -1):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        # Add some random-like variation to the data
        day_commits = base_commits + ((days - i) * 2) + (((days - i) % 7) * 5)  # Increasing trend with weekly pattern
        day_followers = base_followers + ((days-i) // 2)  # Slower increasing trend
        day_youtube_subscribers = base_youtube_subscribers + ((days - i))  # Steady growth for YouTube
        day_bluesky_followers = base_bluesky_followers + ((days - i)*2)  # Steady growth for Bluesky
        
        # Calculate total followers
        total_followers = day_followers + day_youtube_subscribers + day_bluesky_followers
        
        # Calculate ratio based on total followers
        ratio = round((day_commits / total_followers if total_followers > 0 else 1) * 10) / 10
        
        # Create entry
        entry = {
            "date": date_str,
            "github_commits": day_commits,
            "twitter_followers": day_followers,
            "youtube_subscribers": day_youtube_subscribers,
            "bluesky_followers": day_bluesky_followers,
            "total_followers": total_followers,
            "ratio": ratio,
            "last_updated": f"{date_str}T12:00:00-08:00"
        }
        data.append(entry)
    
    return {"data": data}

def main():
    """
    Generate a local HTML file with fake data
    """
    # Generate fake historical data (4 weeks)
    historical_data = generate_fake_historical_data(300)
    
    # Use the latest values from historical data
    latest_entry = historical_data["data"][-1]
    commit_count = latest_entry["github_commits"]
    follower_count = latest_entry["twitter_followers"]
    youtube_subscribers = latest_entry["youtube_subscribers"]
    bluesky_followers = latest_entry["bluesky_followers"]
    total_followers = latest_entry["total_followers"]   

    # Set usernames and channel ID
    github_username = "n3s-online"
    twitter_username = "N3sOnline"
    youtube_channel_id = "UCX6OQ3DkcsbYNE6H8uQQuVA"  # MrBeast's YouTube channel ID
    bluesky_username= "n3sonline.bsky.social"
    
    # Print summary of the historical data
    print(f"Generated {len(historical_data['data'])} days of fake historical data")
    print(f"First day: {historical_data['data'][0]['date']}, "
          f"Commits: {historical_data['data'][0]['github_commits']}, "
          f"Twitter Followers: {historical_data['data'][0]['twitter_followers']}, "
          f"YouTube Subscribers: {historical_data['data'][0]['youtube_subscribers']}, "
          f"Bluesky Followers: {historical_data['data'][0]['bluesky_followers']}")
    print(f"Last day: {historical_data['data'][-1]['date']}, "
          f"Commits: {commit_count}, "
          f"Twitter Followers: {follower_count}, "
          f"YouTube Subscribers: {youtube_subscribers}, "
          f"Total Followers: {total_followers}, "
          f"Bluesky Followers: {bluesky_followers}")
    
    # Render the HTML template with historical data
    html_content = render_html_template(
        commit_count=commit_count,
        follower_count=follower_count,
        github_username=github_username,
        twitter_username=twitter_username,
        historical_data=historical_data,
        youtube_channel_id=youtube_channel_id,
        bluesky_username=bluesky_username
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