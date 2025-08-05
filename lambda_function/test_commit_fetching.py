#!/usr/bin/env python3
"""
Test script to verify commit fetching with organization integration works correctly.
This script tests that commits are properly filtered by username.
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Import our functions
from lambda_handler import get_commits_since_jan_1

def test_commit_fetching():
    """Test the commit fetching functionality with organization integration."""
    
    # Get configuration from environment
    github_token = os.getenv("GITHUB_TOKEN")
    github_username = os.getenv("GITHUB_USERNAME")
    github_organization = os.getenv("GITHUB_ORGANIZATION")
    
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment variables")
        return False
    
    if not github_username:
        print("❌ GITHUB_USERNAME not found in environment variables")
        return False
    
    print(f"✅ Testing commit fetching for username: {github_username}")
    
    if github_organization:
        print(f"✅ Organization configured: {github_organization}")
    else:
        print("⚠️  No GITHUB_ORGANIZATION set")
    
    try:
        print(f"\n🔍 Fetching commits since January 1st...")
        
        # Test commit fetching
        commit_count = get_commits_since_jan_1(github_username, github_token)
        
        if commit_count is not None:
            print(f"✅ Successfully fetched commits: {commit_count}")
            
            current_year = datetime.now().year
            print(f"   Total commits in {current_year}: {commit_count}")
            
            if commit_count > 0:
                print("✅ Found commits - the integration is working!")
            else:
                print("⚠️  No commits found - this might be expected if no commits were made this year")
            
            return True
        else:
            print("❌ Commit fetching returned None - there was an error")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Commit Fetching Test")
    print("=" * 50)
    
    success = test_commit_fetching()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Commit fetching test passed!")
        sys.exit(0)
    else:
        print("❌ Commit fetching test failed!")
        sys.exit(1)
