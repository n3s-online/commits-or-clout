import requests
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_youtube_subscriber_count(api_key, channel_id):
    """
    Fetch the subscriber count for a YouTube channel using the YouTube Data API v3.
    
    Args:
        api_key (str): YouTube Data API key
        channel_id (str): YouTube channel ID
        
    Returns:
        int: The number of subscribers, or None if an error occurs
    """
    if not api_key or not channel_id:
        logger.warning("YouTube API key or channel ID not provided")
        return None
        
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "statistics",
        "id": channel_id,
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "items" in data and len(data["items"]) > 0:
            subscriber_count = int(data["items"][0]["statistics"]["subscriberCount"])
            logger.info(f"Found {subscriber_count} YouTube subscribers")
            return subscriber_count
        else:
            error_msg = f"No channel data found for channel ID: {channel_id}"
            logger.error(error_msg)
            return None
    except Exception as e:
        error_msg = f"Error fetching YouTube subscriber count: {e}"
        logger.error(error_msg)
        return None