"""
Threads Reply Manager
Handles fetching replies, tracking replied comments, and enforcing rate limits.
"""
import os
import json
import time
import random
import requests
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ReplyContext:
    """Context for a reply that needs to be answered."""
    thread_id: str
    reply_id: str
    reply_text: str
    author_username: str
    author_id: Optional[str] = None
    parent_id: Optional[str] = None  # If replying to a reply, this is the parent reply ID


class ThreadsReplyManager:
    def __init__(self, access_token: str, user_id: str, own_username: Optional[str] = None):
        """Initialize Threads Reply Manager.
        
        Args:
            access_token: Threads API access token
            user_id: Threads user ID
            own_username: Your own username (to filter out self-replies)
        """
        self.access_token = access_token
        self.user_id = user_id
        self.own_username = own_username
        self.base_url = "https://graph.threads.net/v1.0"
        
        # Rate limits
        self.MAX_REPLIES_PER_DAY = 20
        self.MAX_REPLIES_PER_THREAD = 3
        self.MIN_REPLY_DELAY_SEC = 120  # 2 minutes
        self.MAX_REPLY_DELAY_SEC = 900  # 15 minutes
        
        # Data directory for tracking
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Tracking files
        self.replied_file = self.data_dir / "replied_comments.json"
        self.stats_file = self.data_dir / "reply_stats.json"
        
        # Load tracking data
        self.replied_ids = self._load_replied_ids()
        self.stats = self._load_stats()
        
        # Clean up old stats (older than 1 day)
        self._cleanup_old_stats()
    
    def _load_replied_ids(self) -> set:
        """Load set of replied comment IDs."""
        if not self.replied_file.exists():
            return set()
        
        try:
            with open(self.replied_file, 'r') as f:
                data = json.load(f)
                return set(data.get('replied_ids', []))
        except Exception as e:
            print(f"⚠ Error loading replied IDs: {e}")
            return set()
    
    def _save_replied_ids(self):
        """Save replied comment IDs to file."""
        try:
            data = {
                'replied_ids': list(self.replied_ids),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.replied_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠ Error saving replied IDs: {e}")
    
    def _load_stats(self) -> Dict:
        """Load reply statistics."""
        if not self.stats_file.exists():
            return {
                'daily_replies': {},
                'thread_replies': {},
                'user_replies': {},  # Track replies per user per thread
                'last_reply_time': None
            }
        
        try:
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠ Error loading stats: {e}")
            return {
                'daily_replies': {},
                'thread_replies': {},
                'user_replies': {},
                'last_reply_time': None
            }
    
    def _save_stats(self):
        """Save reply statistics to file."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"⚠ Error saving stats: {e}")
    
    def _cleanup_old_stats(self):
        """Remove stats older than 1 day."""
        today = datetime.now().date().isoformat()
        
        # Clean daily_replies
        if 'daily_replies' in self.stats:
            self.stats['daily_replies'] = {
                k: v for k, v in self.stats['daily_replies'].items()
                if k >= today
            }
        
        # Clean thread_replies (keep last 7 days)
        if 'thread_replies' in self.stats:
            cutoff_date = (datetime.now() - timedelta(days=7)).date().isoformat()
            self.stats['thread_replies'] = {
                k: v for k, v in self.stats['thread_replies'].items()
                if v.get('date', '') >= cutoff_date
            }
        
        self._save_stats()
    
    def _get_today_reply_count(self) -> int:
        """Get number of replies sent today."""
        today = datetime.now().date().isoformat()
        return self.stats.get('daily_replies', {}).get(today, 0)
    
    def _get_thread_reply_count(self, thread_id: str) -> int:
        """Get number of replies sent to a specific thread."""
        return self.stats.get('thread_replies', {}).get(thread_id, {}).get('count', 0)
    
    def _get_user_reply_count(self, thread_id: str, user_id: str) -> int:
        """Get number of replies sent to a specific user in a thread."""
        key = f"{thread_id}:{user_id}"
        return self.stats.get('user_replies', {}).get(key, 0)
    
    def _increment_daily_count(self):
        """Increment daily reply count."""
        today = datetime.now().date().isoformat()
        if 'daily_replies' not in self.stats:
            self.stats['daily_replies'] = {}
        self.stats['daily_replies'][today] = self.stats['daily_replies'].get(today, 0) + 1
        self._save_stats()
    
    def _increment_thread_count(self, thread_id: str):
        """Increment thread reply count."""
        if 'thread_replies' not in self.stats:
            self.stats['thread_replies'] = {}
        
        if thread_id not in self.stats['thread_replies']:
            self.stats['thread_replies'][thread_id] = {
                'count': 0,
                'date': datetime.now().date().isoformat()
            }
        
        self.stats['thread_replies'][thread_id]['count'] += 1
        self._save_stats()
    
    def _increment_user_count(self, thread_id: str, user_id: str):
        """Increment user reply count for a thread."""
        if 'user_replies' not in self.stats:
            self.stats['user_replies'] = {}
        
        key = f"{thread_id}:{user_id}"
        self.stats['user_replies'][key] = self.stats['user_replies'].get(key, 0) + 1
        self._save_stats()
    
    def _update_last_reply_time(self):
        """Update last reply timestamp."""
        self.stats['last_reply_time'] = datetime.now().isoformat()
        self._save_stats()
    
    def can_reply_now(self) -> bool:
        """Check if we can reply now (rate limits + time delay)."""
        # Check daily limit
        if self._get_today_reply_count() >= self.MAX_REPLIES_PER_DAY:
            print(f"⚠ Daily reply limit reached ({self.MAX_REPLIES_PER_DAY})")
            return False
        
        # Check time since last reply
        last_reply_time = self.stats.get('last_reply_time')
        if last_reply_time:
            try:
                last_time = datetime.fromisoformat(last_reply_time)
                elapsed = (datetime.now() - last_time).total_seconds()
                min_delay = self.MIN_REPLY_DELAY_SEC
                
                if elapsed < min_delay:
                    remaining = int(min_delay - elapsed)
                    print(f"⚠ Too soon to reply. Wait {remaining} seconds.")
                    return False
            except Exception as e:
                print(f"⚠ Error checking last reply time: {e}")
        
        return True
    
    def _is_low_value_reply(self, text: str) -> bool:
        """Check if reply is too short or low-value."""
        if not text or len(text.strip()) < 3:
            return True
        
        # Check if it's only emojis
        text_clean = text.strip()
        # Simple emoji check (if text is very short and has no letters/numbers)
        if len(text_clean) <= 5 and not any(c.isalnum() for c in text_clean):
            return True
        
        # Common low-value replies
        low_value_patterns = ['lol', '🔥', '❤️', '👍', '😍', '💯', 'yesss', 'yes', 'no', 'ok', 'okay']
        text_lower = text_clean.lower()
        if text_lower in low_value_patterns or text_lower.strip() in low_value_patterns:
            return True
        
        return False
    
    def _fetch_replies(self, thread_id: str, limit: int = 25) -> List[Dict]:
        """Fetch replies for a thread.
        
        Args:
            thread_id: Thread ID to fetch replies for
            limit: Maximum number of replies to fetch
            
        Returns:
            List of reply dictionaries
        """
        url = f"{self.base_url}/{thread_id}/replies"
        params = {
            'access_token': self.access_token,
            'limit': limit,
            'fields': 'id,text,from,parent_id'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'data' in result:
                return result['data']
            return []
            
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_code = error_data.get('error', {}).get('code')
                    if error_code == 190:
                        print("❌ Invalid access token")
                    else:
                        print(f"❌ Error fetching replies: {error_data.get('error', {}).get('message', 'Unknown error')}")
                except:
                    print(f"❌ Error fetching replies: {e.response.text[:200]}")
            else:
                print(f"❌ Error fetching replies: {e}")
            return []
        except Exception as e:
            print(f"❌ Error fetching replies: {e}")
            return []
    
    def _get_own_threads(self, limit: int = 10) -> List[str]:
        """Get list of recent own thread IDs.
        
        Args:
            limit: Maximum number of threads to fetch
            
        Returns:
            List of thread IDs
        """
        url = f"{self.base_url}/{self.user_id}/threads"
        params = {
            'access_token': self.access_token,
            'limit': limit,
            'fields': 'id'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'data' in result:
                return [thread['id'] for thread in result['data']]
            return []
            
        except Exception as e:
            print(f"⚠ Error fetching own threads: {e}")
            return []
    
    def get_unreplied_comments_recent_threads(self, limit_threads: int = 10) -> List[ReplyContext]:
        """Get unreplied comments from recent threads.
        
        Args:
            limit_threads: Maximum number of threads to check
            
        Returns:
            List of ReplyContext objects for unreplied comments
        """
        if not self.can_reply_now():
            return []
        
        # Get recent own threads
        thread_ids = self._get_own_threads(limit=limit_threads)
        
        if not thread_ids:
            print("⚠ No recent threads found")
            return []
        
        unreplied = []
        
        for thread_id in thread_ids:
            # Check thread reply limit
            if self._get_thread_reply_count(thread_id) >= self.MAX_REPLIES_PER_THREAD:
                continue
            
            # Fetch replies
            replies = self._fetch_replies(thread_id, limit=25)
            
            for reply in replies:
                reply_id = reply.get('id')
                reply_text = reply.get('text', '')
                from_user = reply.get('from', {})
                author_username = from_user.get('username', '')
                author_id = from_user.get('id', '')
                parent_id = reply.get('parent_id')
                
                # Skip if already replied
                if reply_id in self.replied_ids:
                    continue
                
                # Skip if from self
                if author_username == self.own_username or author_id == self.user_id:
                    continue
                
                # Skip low-value replies
                if self._is_low_value_reply(reply_text):
                    continue
                
                # Check user reply limit for this thread
                if author_id and self._get_user_reply_count(thread_id, author_id) >= 3:
                    continue
                
                # Create reply context
                context = ReplyContext(
                    thread_id=thread_id,
                    reply_id=reply_id,
                    reply_text=reply_text,
                    author_username=author_username,
                    author_id=author_id,
                    parent_id=parent_id
                )
                
                unreplied.append(context)
                
                # Limit results to avoid processing too many at once
                if len(unreplied) >= 10:
                    break
            
            if len(unreplied) >= 10:
                break
        
        return unreplied
    
    def mark_replied(self, reply_id: str, thread_id: str, author_id: Optional[str] = None):
        """Mark a reply as replied to.
        
        Args:
            reply_id: Reply ID that was answered
            thread_id: Thread ID
            author_id: Optional author ID for tracking
        """
        self.replied_ids.add(reply_id)
        self._save_replied_ids()
        
        self._increment_daily_count()
        self._increment_thread_count(thread_id)
        
        if author_id:
            self._increment_user_count(thread_id, author_id)
        
        self._update_last_reply_time()
        
        print(f"✓ Marked reply {reply_id} as replied")
    
    def get_next_reply_delay(self) -> int:
        """Get random delay for next reply (in seconds)."""
        return random.randint(self.MIN_REPLY_DELAY_SEC, self.MAX_REPLY_DELAY_SEC)

