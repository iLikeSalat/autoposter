"""
AutoPoster - Main application class.
Handles scheduling, posting, and auto-reply functionality.
"""
import os
import schedule
import time
import json
import random
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from functools import partial

from .config import Config
from .logger import setup_logger
from .image_fetcher import ImageFetcher
from .image_uploader import ImageUploader
from .llm_content_generator import LLMContentGenerator
from .threads_poster import ThreadsPoster
from .twitter_poster import TwitterPoster
from .threads_reply_manager import ThreadsReplyManager
from .llm_reply_generator import LLMReplyGenerator


class AutoPoster:
    """Main AutoPoster application class."""
    
    def __init__(self, config: Config, logger=None):
        """Initialize AutoPoster with configuration.
        
        Args:
            config: Config instance
            logger: Optional logger instance. If None, creates a new one.
        """
        self.config = config
        self.logger = logger or setup_logger()
        
        # Initialize components
        self._init_image_components()
        self._init_llm_components()
        self._init_platforms()
        self._init_tracking()
    
    def _init_image_components(self):
        """Initialize image fetching and uploading components."""
        images_config = self.config.get('images', {})
        
        self.image_fetcher = ImageFetcher(
            image_folder=images_config.get('folder', 'images'),
            file_extensions=images_config.get('file_extensions', ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
        )
        
        upload_service = images_config.get('upload_service', 'imgbb')
        self.image_uploader = ImageUploader(service=upload_service)
    
    def _init_llm_components(self):
        """Initialize LLM content generation components."""
        llm_config = self.config.get('llm', {})
        api_key = self.config.get_env_or_config('OPENAI_API_KEY', 'llm.api_key')
        
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env or llm.api_key in config.yaml")
        
        prompts_file = llm_config.get('prompts_file', 'prompts.txt')
        stories_file = llm_config.get('stories_file', 'stories.txt')
        
        self.content_generator = LLMContentGenerator(
            api_key=api_key,
            model=llm_config.get('model', 'gpt-4o'),
            max_tokens=llm_config.get('max_tokens', 500),
            temperature=llm_config.get('temperature', 0.7),
            prompts_file=prompts_file,
            stories_file=stories_file
        )
    
    def _init_platforms(self):
        """Initialize platform posters and reply systems."""
        platforms_config = self.config.get('platforms', {})
        self.enable_threads = (
            os.getenv('ENABLE_THREADS', '').lower() == 'true' or 
            platforms_config.get('threads', False)
        )
        self.enable_twitter = (
            os.getenv('ENABLE_TWITTER', '').lower() == 'true' or 
            platforms_config.get('twitter', False)
        )
        
        self.threads_poster = None
        self.twitter_poster = None
        self.reply_manager = None
        self.reply_generator = None
        self.enable_auto_replies = False
        
        if self.enable_threads:
            self._init_threads()
        
        if self.enable_twitter:
            self._init_twitter()
    
    def _init_threads(self):
        """Initialize Threads platform."""
        access_token = self.config.get_env_or_config('THREADS_ACCESS_TOKEN', 'threads.access_token')
        user_id = self.config.get_env_or_config('THREADS_USER_ID', 'threads.user_id')
        
        if not access_token or not user_id:
            self.logger.warning("Threads enabled but credentials not provided")
            self.enable_threads = False
            return
        
        image_host_url = self.config.get_env_or_config('THREADS_IMAGE_HOST_URL', 'threads.image_host_url')
        self.threads_poster = ThreadsPoster(
            access_token=access_token,
            user_id=user_id,
            image_host_url=image_host_url
        )
        
        # Initialize auto-reply system if enabled
        threads_config = self.config.get('threads', {})
        self.enable_auto_replies = (
            os.getenv('ENABLE_AUTO_REPLIES', '').lower() == 'true' or 
            threads_config.get('enable_auto_replies', False)
        )
        
        if self.enable_auto_replies:
            self._init_auto_replies(access_token, user_id)
    
    def _init_auto_replies(self, access_token: str, user_id: str):
        """Initialize auto-reply system."""
        # Get own username
        own_username = None
        try:
            if self.threads_poster.verify_credentials():
                url = f"{self.threads_poster.base_url}/{user_id}"
                params = {'access_token': access_token, 'fields': 'username'}
                response = requests.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    own_username = result.get('username')
        except Exception as e:
            self.logger.warning(f"Could not fetch username: {e}")
        
        self.reply_manager = ThreadsReplyManager(
            access_token=access_token,
            user_id=user_id,
            own_username=own_username
        )
        
        llm_config = self.config.get('llm', {})
        api_key = self.config.get_env_or_config('OPENAI_API_KEY', 'llm.api_key')
        
        self.reply_generator = LLMReplyGenerator(
            api_key=api_key,
            model=llm_config.get('model', 'gpt-4o'),
            temperature=llm_config.get('temperature', 0.7)
        )
        
        self.logger.info("✓ Auto-reply system initialized")
    
    def _init_twitter(self):
        """Initialize Twitter/X platform."""
        twitter_config = self.config.get('twitter', {})
        self.twitter_poster = TwitterPoster(
            api_key=self.config.get_env_or_config('TWITTER_API_KEY', 'twitter.api_key', ''),
            api_secret=self.config.get_env_or_config('TWITTER_API_SECRET', 'twitter.api_secret', ''),
            access_token=self.config.get_env_or_config('TWITTER_ACCESS_TOKEN', 'twitter.access_token', ''),
            access_token_secret=self.config.get_env_or_config('TWITTER_ACCESS_TOKEN_SECRET', 'twitter.access_token_secret', ''),
            bearer_token=self.config.get_env_or_config('TWITTER_BEARER_TOKEN', 'twitter.bearer_token')
        )
    
    def _init_tracking(self):
        """Initialize tracking for used images and stats."""
        self.used_images_file = Path("used_images.json")
        self.used_images = self._load_used_images()
        
        self.post_stats = {
            'text_posts_today': 0,
            'image_posts_today': 0,
            'last_reset_date': datetime.now().date()
        }
    
    def _load_used_images(self) -> list:
        """Load list of previously used images."""
        if self.used_images_file.exists():
            try:
                with open(self.used_images_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Error loading used images: {e}")
                return []
        return []
    
    def _save_used_image(self, image_path: str):
        """Save image path to used images list."""
        self.used_images.append(image_path)
        if len(self.used_images) > 100:
            self.used_images = self.used_images[-100:]
        
        try:
            with open(self.used_images_file, 'w') as f:
                json.dump(self.used_images, f)
        except Exception as e:
            self.logger.error(f"Error saving used images: {e}")
    
    def _reset_daily_stats(self):
        """Reset daily posting stats if it's a new day."""
        today = datetime.now().date()
        if today != self.post_stats['last_reset_date']:
            self.post_stats['text_posts_today'] = 0
            self.post_stats['image_posts_today'] = 0
            self.post_stats['last_reset_date'] = today
    
    def post_thread(self, post_type: str = 'auto') -> bool:
        """Main function to generate and post content.
        
        Args:
            post_type: 'text', 'image', or 'auto' (auto decides based on daily limits)
            
        Returns:
            True if successful, False otherwise
        """
        self._reset_daily_stats()
        
        try:
            if post_type == 'text':
                return self._post_text_only()
            elif post_type == 'image':
                return self._post_with_image()
            elif post_type == 'auto':
                # Auto mode: decide based on daily limits
                schedule_config = self.config.get('schedule', {})
                text_posts_per_day = schedule_config.get('text_posts_per_day', 10)
                image_posts_per_day = schedule_config.get('image_posts_per_day', 5)
                
                if self.post_stats['text_posts_today'] < text_posts_per_day:
                    return self._post_text_only()
                elif self.post_stats['image_posts_today'] < image_posts_per_day:
                    return self._post_with_image()
                else:
                    self.logger.info("Daily post limits reached")
                    return False
            else:
                self.logger.error(f"Invalid post_type: {post_type}")
                return False
        except Exception as e:
            self.logger.exception(f"Error in post_thread: {e}")
            return False
    
    def _post_text_only(self) -> bool:
        """Post a text-only post."""
        self.logger.info("Generating text post...")
        post_text = self.content_generator.generate_single_post()
        
        if not post_text:
            self.logger.error("Failed to generate content")
            return False
        
        self.logger.info(f"Generated post: {post_text[:100]}...")
        
        all_success = True
        
        if self.enable_threads and self.threads_poster:
            self.logger.info("Posting to Threads...")
            success = self.threads_poster.post_thread(posts=[post_text], image_path=None)
            if not success:
                all_success = False
        
        if self.enable_twitter and self.twitter_poster:
            self.logger.info("Posting to Twitter/X...")
            success = self.twitter_poster.post_thread(tweets=[post_text], image_path=None)
            if not success:
                all_success = False
        
        if all_success:
            self.logger.info("✓ Text post published successfully!")
            self.post_stats['text_posts_today'] += 1
        else:
            self.logger.error("✗ Failed to post to one or more platforms")
        
        return all_success
    
    def _post_with_image(self) -> bool:
        """Post with an image."""
        self.logger.info("Selecting image...")
        image_info = self.image_fetcher.get_random_image(exclude_used=self.used_images)
        
        if not image_info:
            self.logger.warning("No images available. Falling back to text post.")
            return self._post_text_only()
        
        image_path = image_info["full_path"]
        self.logger.info(f"Selected image: {os.path.basename(image_path)}")
        
        # Upload image
        self.logger.info("Uploading image to hosting service...")
        image_url = self.image_uploader.upload(image_path)
        
        if not image_url:
            self.logger.warning("Image upload failed. Falling back to text post.")
            return self._post_text_only()
        
        # Generate caption
        self.logger.info("Generating image caption...")
        caption = self.content_generator.generate_image_caption(image_path)
        
        if not caption:
            self.logger.warning("Failed to generate caption. Using simple caption.")
            caption = "What do you think?"
        
        # Add engagement question if not present
        engagement_questions = [
            "Be honest, would you actually notice me?",
            "Do I look too young or just right?",
            "Would someone like you even say hi?",
            "Is this a red flag or green flag for you?",
            "Should I post more like this or no?",
            "Honest question... do I look older here?",
            "Would you approach me or keep scrolling?",
            "Do I look innocent or dangerous?",
            "What would you do if you saw me like this?",
            "Be real, is this giving what I think it is?",
            "Would someone mature even notice this?",
            "Do I look too young for you or just right?",
            "Honest thoughts?",
            "Would you actually text me back?",
            "Is this too much or just right?"
        ]
        
        if not any(q.lower() in caption.lower() for q in engagement_questions):
            caption += f" {random.choice(engagement_questions)}"
        
        self.logger.info(f"Generated caption: {caption[:100]}...")
        
        # Post to enabled platforms
        all_success = True
        
        if self.enable_threads and self.threads_poster:
            self.logger.info("Posting to Threads...")
            success = self.threads_poster.post_thread(posts=[caption], image_path=image_url)
            if not success:
                all_success = False
            else:
                self._save_used_image(image_info["path"])
        
        if self.enable_twitter and self.twitter_poster:
            self.logger.info("Posting to Twitter/X...")
            success = self.twitter_poster.post_thread(tweets=[caption], image_path=image_path)
            if not success:
                all_success = False
        
        if all_success:
            self.logger.info("✓ Image post published successfully!")
            self.post_stats['image_posts_today'] += 1
        else:
            self.logger.error("✗ Failed to post to one or more platforms")
        
        return all_success
    
    def _get_thread_text(self, thread_id: str) -> Optional[str]:
        """Fetch the text content of a thread."""
        if not self.threads_poster:
            return None
        
        try:
            url = f"{self.threads_poster.base_url}/{thread_id}"
            params = {
                'access_token': self.threads_poster.access_token,
                'fields': 'text'
            }
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result.get('text', '')
        except Exception as e:
            self.logger.warning(f"Error fetching thread text: {e}")
        
        return None
    
    def _process_replies(self):
        """Process and reply to comments on recent threads."""
        if not self.enable_auto_replies or not self.reply_manager or not self.reply_generator:
            return
        
        self.logger.info("Checking for replies to process...")
        
        if not self.reply_manager.can_reply_now():
            return
        
        unreplied = self.reply_manager.get_unreplied_comments_recent_threads(limit_threads=10)
        
        if not unreplied:
            self.logger.info("No unreplied comments found")
            return
        
        self.logger.info(f"Found {len(unreplied)} unreplied comment(s)")
        
        context = unreplied[0]
        self.logger.info(f"Processing reply from @{context.author_username}: {context.reply_text[:50]}...")
        
        original_post_text = self._get_thread_text(context.thread_id)
        if not original_post_text:
            original_post_text = "Check out my latest post!"
        
        reply_text = self.reply_generator.generate_reply(
            original_post_text=original_post_text,
            user_reply_text=context.reply_text,
            author_username=context.author_username
        )
        
        if not reply_text:
            self.logger.warning("Failed to generate reply or reply was filtered")
            return
        
        self.logger.info(f"Generated reply: {reply_text}")
        
        reply_id = self.threads_poster.post_reply(
            parent_id=context.reply_id,
            text=reply_text
        )
        
        if reply_id:
            self.reply_manager.mark_replied(
                reply_id=context.reply_id,
                thread_id=context.thread_id,
                author_id=context.author_id
            )
            self.logger.info(f"✓ Reply posted successfully! Reply ID: {reply_id}")
        else:
            self.logger.error("Failed to post reply")
    
    def setup_schedule(self):
        """Setup the posting schedule with weighted randomness."""
        schedule_config = self.config.get('schedule', {})
        text_posts_per_day = schedule_config.get('text_posts_per_day', 10)
        image_posts_per_day = schedule_config.get('image_posts_per_day', 5)
        random_times = schedule_config.get('random_times', True)
        use_weighted_random = schedule_config.get('weighted_random', True)
        
        if not random_times:
            # Single post at specific time
            post_time = schedule_config.get('post_time', '09:00')
            schedule.every().day.at(post_time).do(self.post_thread)
            self.logger.info(f"Scheduled daily post at {post_time}")
            return
        
        # Generate random times for text and image posts
        all_times = []
        
        for _ in range(text_posts_per_day):
            time_str = self._generate_weighted_time(use_weighted_random)
            all_times.append(('text', time_str))
        
        for _ in range(image_posts_per_day):
            time_str = self._generate_weighted_time(use_weighted_random)
            all_times.append(('image', time_str))
        
        # Sort by time
        all_times.sort(key=lambda x: x[1])
        
        # Schedule each post
        for post_type, time_str in all_times:
            schedule.every().day.at(time_str).do(partial(self.post_thread, post_type=post_type))
            self.logger.info(f"Scheduled {post_type} post at {time_str}")
    
    def _generate_weighted_time(self, weighted: bool = True) -> str:
        """Generate a random time with weighted distribution."""
        if not weighted:
            hour = random.randint(8, 22)
            minute = random.randint(0, 59)
            return f"{hour:02d}:{minute:02d}"
        
        # Weighted hours (avoid 2-7 AM, favor active hours)
        hour_weights = []
        for h in range(24):
            if 2 <= h < 7:
                weight = 0
            elif 9 <= h <= 11 or 12 <= h <= 14 or 17 <= h <= 21:
                weight = 3
            else:
                weight = 1
            hour_weights.append(weight)
        
        # Select hour based on weights
        hour = random.choices(range(24), weights=hour_weights)[0]
        minute = random.randint(0, 59)
        
        return f"{hour:02d}:{minute:02d}"
    
    def run(self):
        """Run the auto-poster continuously."""
        self.setup_schedule()
        
        # Post immediately on startup
        self.logger.info("Posting initial thread...")
        self.post_thread()
        
        self.logger.info("Auto-poster is running. Press Ctrl+C to stop.")
        self.logger.info("Waiting for scheduled posts...")
        
        # Run scheduler and reply loop
        last_reply_check = datetime.now()
        reply_check_interval = timedelta(minutes=15)
        
        while True:
            schedule.run_pending()
            
            # Check for replies if auto-replies are enabled
            if self.enable_auto_replies and self.reply_manager and self.reply_generator:
                if datetime.now() - last_reply_check >= reply_check_interval:
                    self._process_replies()
                    last_reply_check = datetime.now()
            
            time.sleep(60)  # Check every minute

