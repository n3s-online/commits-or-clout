#!/usr/bin/env python3
"""
Script to locally render the Commits or Clout HTML page with fake data
"""
import os
import sys
from utils import render_html_template

def main():
    """
    Generate a local HTML file with fake data
    """
    # Fake data for local rendering
    commit_count = 250
    follower_count = 100
    github_username = "your_github_username"
    twitter_username = "your_twitter_username"
    
    # Render the HTML template
    html_content = render_html_template(
        commit_count=commit_count,
        follower_count=follower_count,
        github_username=github_username,
        twitter_username=twitter_username
    )
    
    # Write to index.html file
    output_file = "index.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"HTML file generated at: {os.path.abspath(output_file)}")
    print("Open this file in your browser to preview the page.")

if __name__ == "__main__":
    main() 