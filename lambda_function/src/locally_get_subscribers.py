#!/usr/bin/env python3
import os
import sys
import logging
from dotenv import load_dotenv
from youtube_utils import get_youtube_subscriber_count

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Load environment variables from .env file and print YouTube subscriber count
    """
    # Load environment variables from .env file
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if not os.path.exists(env_path):
        logger.error(f"Environment file not found at {env_path}")
        sys.exit(1)
    
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
    
    # Get YouTube API key and channel ID from environment variables
    youtube_api_key = os.environ.get('YOUTUBE_API_KEY')
    youtube_channel_id = os.environ.get('YOUTUBE_CHANNEL_ID')
    
    if not youtube_api_key:
        logger.error("YOUTUBE_API_KEY not found in environment variables")
        sys.exit(1)
    
    if not youtube_channel_id:
        logger.error("YOUTUBE_CHANNEL_ID not found in environment variables")
        sys.exit(1)
    
    logger.info(f"Using YouTube channel ID: {youtube_channel_id}")
    
    # Get subscriber count
    try:
        subscriber_count = get_youtube_subscriber_count(youtube_api_key, youtube_channel_id)
        
        if subscriber_count is not None:
            print(f"\n✅ Successfully retrieved YouTube subscriber count:")
            print(f"Channel: {youtube_channel_id}")
            print(f"Subscribers: {subscriber_count:,}")
        else:
            print(f"\n❌ Failed to retrieve YouTube subscriber count for channel: {youtube_channel_id}")
            print("Check the logs for more details.")
    except Exception as e:
        logger.error(f"Error getting YouTube subscriber count: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 