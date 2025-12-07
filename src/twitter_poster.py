"""
Twitter/X Thread Poster
Handles posting threads with images to Twitter/X.
"""
import tweepy
from typing import List, Optional
import os


class TwitterPoster:
    def __init__(self, api_key: str, api_secret: str, 
                 access_token: str, access_token_secret: str,
                 bearer_token: Optional[str] = None):
        """Initialize Twitter API client."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        
        # Initialize v2 API client
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )
        
        # Initialize v1.1 API for media upload
        self.auth = tweepy.OAuth1UserHandler(
            api_key, api_secret, access_token, access_token_secret
        )
        self.api_v1 = tweepy.API(self.auth, wait_on_rate_limit=True)
    
    def upload_image(self, image_path: str) -> Optional[str]:
        """Upload an image to Twitter and return media_id."""
        try:
            media = self.api_v1.media_upload(image_path)
            return media.media_id_string
        except Exception as e:
            print(f"Error uploading image: {e}")
            return None
    
    def post_thread(self, tweets: List[str], image_path: Optional[str] = None) -> bool:
        """Post a thread of tweets with optional image."""
        if not tweets:
            print("No tweets to post")
            return False
        
        try:
            # Upload image if provided
            media_id = None
            if image_path and os.path.exists(image_path):
                print(f"Uploading image: {image_path}")
                media_id = self.upload_image(image_path)
                if not media_id:
                    print("Failed to upload image, posting without it")
            
            # Post first tweet with image
            first_tweet = tweets[0]
            if media_id:
                response = self.client.create_tweet(text=first_tweet, media_ids=[media_id])
            else:
                response = self.client.create_tweet(text=first_tweet)
            
            if not response.data:
                print("Failed to post first tweet")
                return False
            
            previous_tweet_id = response.data['id']
            print(f"Posted tweet 1/{len(tweets)}: {previous_tweet_id}")
            
            # Post remaining tweets as replies
            for i, tweet in enumerate(tweets[1:], start=2):
                response = self.client.create_tweet(
                    text=tweet,
                    in_reply_to_tweet_id=previous_tweet_id
                )
                
                if not response.data:
                    print(f"Failed to post tweet {i}/{len(tweets)}")
                    return False
                
                previous_tweet_id = response.data['id']
                print(f"Posted tweet {i}/{len(tweets)}: {previous_tweet_id}")
            
            print("Thread posted successfully!")
            return True
            
        except tweepy.TweepyException as e:
            print(f"Twitter API error: {e}")
            return False
        except Exception as e:
            print(f"Error posting thread: {e}")
            return False
    
    def verify_credentials(self) -> bool:
        """Verify Twitter API credentials."""
        try:
            me = self.client.get_me()
            if me.data:
                print(f"Authenticated as: @{me.data.username}")
                return True
            return False
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False


