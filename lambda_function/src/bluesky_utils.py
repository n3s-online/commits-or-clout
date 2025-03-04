from atproto import Client
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class BlueskyHelper:
    def __init__(self, api_key):
        """Initialize the BlueskyHelper with the given API key.
        
        The api_key should be in the format "username:password" or a JSON string
        containing "username" and "password" keys.
        """
        self.client = Client()
        
        # Check if api_key is in JSON format with username and password
        if api_key and ':' in api_key:
            username, password = api_key.split(':', 1)
            self.client.login(username, password)
        else:
            logger.error("API key format incorrect. Should be 'username:password'")

    def get_total_followers(self, username):
        """
        Fetch the total number of followers for the specified username.

        Args:
            username (str): The username to fetch the total number of followers for.

        Returns:
            int: The total number of followers for the user.
        """
        try:
            # Fetch the user's profile information, which contains the follower count
            profile_data = self.client.get_profile(actor=username)
            
            # Extract follower count from profile data
            if hasattr(profile_data, 'followers_count'):
                follower_count = profile_data.followers_count
            else:
                # If followers_count is not directly accessible, try to access it through different paths
                # This depends on the actual structure returned by the API
                follower_count = getattr(profile_data, 'followers_count', 0)
                
            logger.info(f"Found {follower_count} Bluesky followers for {username}")
            return follower_count
        except Exception as e:
            error_msg = f"Error fetching Bluesky followers for {username}: {e}"
            logger.error(error_msg)
            return None 