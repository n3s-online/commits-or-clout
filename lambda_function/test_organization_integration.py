#!/usr/bin/env python3
"""
Test script to verify GitHub organization integration works correctly.
This script tests the new organization repository fetching functionality.
"""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Import our functions
from lambda_handler import (
    get_user_repositories, 
    get_organization_repositories, 
    get_all_repositories
)

def test_organization_integration():
    """Test the organization integration functionality."""
    
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
    
    print(f"✅ Testing with username: {github_username}")
    
    if github_organization:
        print(f"✅ Testing with organization: {github_organization}")
    else:
        print("⚠️  No GITHUB_ORGANIZATION set - will only test user repositories")
    
    try:
        # Test user repositories
        print("\n🔍 Testing user repository fetching...")
        user_repos = get_user_repositories(github_username, github_token)
        print(f"✅ Found {len(user_repos)} user repositories")
        
        if user_repos:
            print("   Sample user repositories:")
            for repo in user_repos[:3]:  # Show first 3
                print(f"   - {repo['name']} (owner: {repo['owner']['login']})")
        
        # Test organization repositories (if configured)
        org_repos = []
        if github_organization:
            print(f"\n🔍 Testing organization repository fetching...")
            org_repos = get_organization_repositories(github_organization, github_token)
            print(f"✅ Found {len(org_repos)} organization repositories")
            
            if org_repos:
                print("   Sample organization repositories:")
                for repo in org_repos[:3]:  # Show first 3
                    print(f"   - {repo['name']} (owner: {repo['owner']['login']})")
        
        # Test combined repository fetching
        print(f"\n🔍 Testing combined repository fetching...")
        all_repos = get_all_repositories(github_username, github_token, github_organization)
        expected_total = len(user_repos) + len(org_repos)
        
        print(f"✅ Combined function returned {len(all_repos)} repositories")
        print(f"   Expected: {expected_total} (user: {len(user_repos)} + org: {len(org_repos)})")
        
        if len(all_repos) == expected_total:
            print("✅ Repository counts match!")
        else:
            print("⚠️  Repository counts don't match - there might be duplicates or missing repos")
        
        # Verify no duplicates
        repo_names = [repo['full_name'] for repo in all_repos]
        unique_names = set(repo_names)
        
        if len(repo_names) == len(unique_names):
            print("✅ No duplicate repositories found")
        else:
            duplicates = len(repo_names) - len(unique_names)
            print(f"⚠️  Found {duplicates} duplicate repositories")
        
        print(f"\n🎉 Test completed successfully!")
        print(f"   Total repositories accessible: {len(all_repos)}")
        print(f"   User repositories: {len(user_repos)}")
        print(f"   Organization repositories: {len(org_repos)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting GitHub Organization Integration Test")
    print("=" * 50)
    
    success = test_organization_integration()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Tests failed!")
        sys.exit(1)
