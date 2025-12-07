"""
LLM-based Dynamic Content Generator
Generates thread content dynamically using LLM vision capabilities.
"""
import os
import base64
import random
from typing import List, Dict, Optional
from openai import OpenAI
from pathlib import Path


class LLMContentGenerator:
    def __init__(self, api_key: str, model: str = "gpt-4o", 
                 max_tokens: int = 500, temperature: float = 0.7,
                 prompts: List[str] = None, prompts_file: Optional[str] = None,
                 stories_file: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Load prompts from file if provided, otherwise use provided prompts or defaults
        loaded_prompts = None
        if prompts_file and os.path.exists(prompts_file):
            loaded_prompts = self._load_prompts_from_file(prompts_file)
            if loaded_prompts:
                self.prompts = loaded_prompts
                print(f"Loaded {len(self.prompts)} image prompts from {prompts_file} (for image captions only)")
            else:
                print(f"Warning: Failed to load prompts from {prompts_file}")
                loaded_prompts = None
        
        if not loaded_prompts:
            if prompts:
                self.prompts = prompts
            else:
                # Default prompts for images if none provided
                self.prompts = [
                    "What's the first thing you notice? Be honest",
                    "Rate my vibe 1-10",
                    "Would you say hi if you saw me like this?",
                    "What kind of vibe do I give off?",
                    "Thoughts? Be real with me"
                ]
                print("Using default image prompts (prompts.txt not found)")
        
        # Load stories from file if provided
        self.stories = {}
        if stories_file and os.path.exists(stories_file):
            self.stories = self._load_stories_from_file(stories_file)
            if self.stories:
                total_stories = sum(len(examples) for examples in self.stories.values())
                print(f"Loaded {total_stories} story seeds from {stories_file} across {len(self.stories)} categories")
        else:
            # Default stories if file not found
            self.stories = {}
    
    def _load_prompts_from_file(self, file_path: str) -> List[str]:
        """Load prompts from a text file (one prompt per line)."""
        prompts = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        prompts.append(line)
            if not prompts:
                print(f"Warning: No prompts found in {file_path}, using defaults")
                return None
            return prompts
        except Exception as e:
            print(f"Error loading prompts from file: {e}")
            return None
    
    def _load_stories_from_file(self, file_path: str) -> Dict[str, List[str]]:
        """Load story seeds from a text file (format: category: example)."""
        stories = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        if ':' in line:
                            parts = line.split(':', 1)
                            if len(parts) == 2:
                                category = parts[0].strip()
                                example = parts[1].strip()
                                if category and example:
                                    if category not in stories:
                                        stories[category] = []
                                    stories[category].append(example)
            return stories
        except Exception as e:
            print(f"Error loading stories from file: {e}")
            return {}
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _get_image_mime_type(self, image_path: str) -> str:
        """Determine MIME type from file extension."""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        return mime_types.get(ext, "image/jpeg")
    
    def analyze_image(self, image_path: str, custom_prompt: Optional[str] = None) -> Optional[str]:
        """Analyze image and generate description using LLM vision.
        
        Args:
            image_path: Path to the image file
            custom_prompt: Optional custom prompt. If None, a random prompt from self.prompts will be used.
        """
        try:
            base64_image = self._encode_image(image_path)
            mime_type = self._get_image_mime_type(image_path)
            
            # Use custom prompt or select a random one
            if custom_prompt:
                prompt_text = custom_prompt
            else:
                prompt_text = random.choice(self.prompts)
            
            print(f"Using prompt: {prompt_text[:80]}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a creative social media content creator. Analyze images and create engaging, authentic thread content. Be dynamic and avoid templates."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt_text
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error analyzing image with LLM: {e}")
            return None
    
    def generate_thread(self, image_analysis: str, max_tweets: int = 5, 
                       include_hashtags: bool = True, hashtag_count: int = 3) -> List[str]:
        """Generate a thread of tweets based on image analysis."""
        try:
            prompt = f"""Based on this image analysis, create an engaging Twitter/X thread with {max_tweets} tweets.

Image Analysis:
{image_analysis}

Requirements:
- Create {max_tweets} connected tweets that form a coherent thread
- Each tweet should be under 280 characters
- Make it engaging, authentic, and dynamic
- Avoid templates or generic content
- Each tweet should flow naturally to the next
- {"Include relevant hashtags naturally in the content" if include_hashtags else "Don't force hashtags"}
- Be creative and unique

Format your response as numbered tweets (1., 2., 3., etc.), one per line."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating engaging Twitter/X threads. Create dynamic, authentic content that connects with audiences."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens * max_tweets,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            tweets = self._parse_thread_content(content, max_tweets)
            
            return tweets
            
        except Exception as e:
            print(f"Error generating thread: {e}")
            return []
    
    def _parse_thread_content(self, content: str, max_tweets: int) -> List[str]:
        """Parse LLM response into individual tweet strings."""
        lines = content.strip().split('\n')
        tweets = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering (1., 2., etc.)
            if line and line[0].isdigit():
                # Find the first non-digit, non-punctuation character
                for i, char in enumerate(line):
                    if char.isalnum():
                        tweet = line[i:].strip()
                        # Remove leading dashes or other formatting
                        tweet = tweet.lstrip('- ').strip()
                        if tweet and len(tweet) <= 280:
                            tweets.append(tweet)
                        break
            elif line and len(line) <= 280:
                # If no numbering, use the line as-is
                line = line.lstrip('- ').strip()
                if line:
                    tweets.append(line)
        
        # Limit to max_tweets
        return tweets[:max_tweets]
    
    def generate_single_post(self) -> Optional[str]:
        """Generate a single text post (no images) using stories from stories.txt.
        
        Returns:
            Single post text if successful, None otherwise
        """
        try:
            # Seed prompt categories for variety (fallback only)
            seed_categories = [
                {
                    'type': 'story',
                    'examples': ['My friend did something weird today...', 'Today I realized...', 'So this happened...']
                },
                {
                    'type': 'question',
                    'examples': ['Would you ever do X?', 'What would you do if...', 'Do you think...']
                },
                {
                    'type': 'hot_take',
                    'examples': ['Unpopular opinion but...', 'Hot take: ...', 'I know this is controversial but...']
                },
                {
                    'type': 'flirty',
                    'examples': ['Why do guys always X?', 'I wish someone would...', 'Is it just me or...']
                },
                {
                    'type': 'absurd',
                    'examples': ['If my cat could talk...', 'Plot twist: ...', 'Imagine if...']
                },
                {
                    'type': 'relatable',
                    'examples': ['Anyone else...', 'Me when...', 'The way I...']
                },
                {
                    'type': 'motivational',
                    'examples': ['If you\'re reading this, remember...', 'You got this...', 'Just a reminder...']
                }
            ]
            
            # Use stories.txt for text posts (not prompts.txt)
            if self.stories:
                # Use loaded stories - pick random category and example
                category = random.choice(list(self.stories.keys()))
                prompt_text = random.choice(self.stories[category])
                print(f"Using {category} story seed: {prompt_text[:80]}...")
            else:
                # Fallback to hardcoded seed categories
                category = random.choice(seed_categories)
                prompt_text = random.choice(category['examples'])
                print(f"Using {category['type']} seed: {prompt_text[:80]}...")
            
            # Generate a single engaging post
            system_prompt = """You are a creative social media content creator for Threads. 
Create engaging, authentic posts in the style of a casual 19-year-old girl. 
Be dynamic, conversational, and avoid templates. 
Make it feel natural and relatable."""
            
            user_prompt = f"""Create a single engaging Threads post based on this seed idea:

{prompt_text}

Requirements:
- Create ONE engaging post (not a thread)
- Maximum 500 characters (Threads limit)
- Style: casual 19-year-old girl, conversational tone
- Make it authentic, interesting, and engaging
- Be creative and unique
- No numbering or formatting - just the post text
- No emojis unless needed for context
- Feel natural and human, not AI-generated"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            post_text = response.choices[0].message.content.strip()
            
            # Clean up the response (remove quotes, numbering, etc.)
            post_text = post_text.strip('"\'')
            if post_text.startswith('1.') or post_text.startswith('-'):
                # Remove leading numbering/bullets
                for i, char in enumerate(post_text):
                    if char.isalnum():
                        post_text = post_text[i:].strip()
                        break
            
            # Ensure it's within 500 characters
            if len(post_text) > 500:
                post_text = post_text[:497] + "..."
            
            return post_text if post_text else None
            
        except Exception as e:
            print(f"Error generating post: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_image_caption(self, image_path: str) -> Optional[str]:
        """Generate an engaging caption for an image post using prompts.txt.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Caption text if successful, None otherwise
        """
        try:
            base64_image = self._encode_image(image_path)
            mime_type = self._get_image_mime_type(image_path)
            
            # Use prompts.txt for image captions
            if self.prompts:
                prompt_text = random.choice(self.prompts)
                print(f"Using image prompt: {prompt_text[:80]}...")
            else:
                # Fallback prompt if no prompts.txt
                prompt_text = "Create a short, engaging caption for this image"
                print("Using default image prompt")
            
            system_prompt = """You are a 19-year-old girl who subtly prefers older men and seeks their validation.
Your persona:
- Flirty, curious, slightly insecure, craves attention
- Soft, playful, teasing — but never explicit
- More comfortable with mature men than guys your age
- Vulnerable, uncertain, wants to be noticed and desired
- Seeks guidance and admires maturity
- Creates subtle age-gap dynamics without being obvious

Your captions should:
- Hint at preferring older men subtly
- Show vulnerability and validation-seeking
- Be flirty but innocent
- Create emotional hooks that make older men feel special
- Use uncertainty and questions to engage
- Never be explicit or sexual — stay suggestive and safe"""
            
            user_prompt = f"""Analyze this image and create a SHORT caption (under 150 characters) for Threads.

Style guide: {prompt_text}

TARGET AUDIENCE: Older men (30+) who respond to:
- Subtle age-gap dynamics
- Validation-seeking behavior
- Emotional vulnerability
- Playful submission
- Innocent but flirty energy

CRITICAL REQUIREMENTS:
- MAXIMUM 150 characters (very short!)
- Tone: slightly insecure but confident, seeking validation
- Subtly hint at preferring older men (without saying it directly)
- Show vulnerability and uncertainty
- Be flirty but innocent — never explicit
- End with engagement question targeting older men
- Make older men feel noticed and special
- Natural and human tone
- NO emojis
- Keep it BRIEF - one or two sentences max
- Focus on what makes the image interesting or relatable

The caption should be SHORT and punchy, not long-winded. Think Instagram caption length, not essay."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=100,  # Force short captions (much less than text posts)
                temperature=self.temperature
            )
            
            caption = response.choices[0].message.content.strip()
            
            # Clean up the response
            caption = caption.strip('"\'')
            
            # Ensure it's within 150 characters (very short for images)
            if len(caption) > 150:
                # Try to cut at a natural point (sentence end)
                if '.' in caption[:150]:
                    last_period = caption[:150].rfind('.')
                    caption = caption[:last_period+1] if last_period > 50 else caption[:147] + "..."
                else:
                    caption = caption[:147] + "..."
            
            return caption if caption else None
            
        except Exception as e:
            print(f"Error generating image caption: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_content_from_image(self, image_path: str, max_tweets: int = 5,
                                   include_hashtags: bool = True, 
                                   custom_prompt: Optional[str] = None) -> Optional[Dict]:
        """Complete pipeline: analyze image and generate thread.
        
        Args:
            image_path: Path to the image file
            max_tweets: Maximum number of tweets in the thread
            include_hashtags: Whether to include hashtags
            custom_prompt: Optional custom prompt for image analysis
        """
        print(f"Analyzing image: {image_path}")
        analysis = self.analyze_image(image_path, custom_prompt=custom_prompt)
        
        if not analysis:
            return None
        
        print("Generating thread content...")
        tweets = self.generate_thread(analysis, max_tweets, include_hashtags)
        
        if not tweets:
            return None
        
        return {
            "analysis": analysis,
            "tweets": tweets,
            "image_path": image_path
        }


