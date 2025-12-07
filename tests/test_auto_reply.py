"""
Test script for auto-reply system.
Allows manual testing of reply fetching, generation, and posting.
"""
import os
import yaml
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.threads_reply_manager import ThreadsReplyManager
from src.llm_reply_generator import LLMReplyGenerator
from src.threads_poster import ThreadsPoster
import requests

def main():
    """Test auto-reply system."""
    load_dotenv()
    
    # Load config
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        print("❌ config.yaml not found")
        return
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Get credentials
    access_token = os.getenv('THREADS_ACCESS_TOKEN')
    user_id = os.getenv('THREADS_USER_ID')
    
    if not access_token or not user_id:
        print("❌ THREADS_ACCESS_TOKEN and THREADS_USER_ID must be set in .env")
        return
    
    # Get own username
    own_username = None
    try:
        url = f"https://graph.threads.net/v1.0/{user_id}"
        params = {'access_token': access_token, 'fields': 'username'}
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            result = response.json()
            own_username = result.get('username')
            print(f"✓ Authenticated as: @{own_username}")
    except Exception as e:
        print(f"⚠ Could not fetch username: {e}")
    
    # Initialize components
    print("\n" + "="*60)
    print("Initializing Auto-Reply Test System")
    print("="*60)
    
    reply_manager = ThreadsReplyManager(
        access_token=access_token,
        user_id=user_id,
        own_username=own_username
    )
    
    llm_config = config.get('llm', {})
    api_key = os.getenv('OPENAI_API_KEY') or llm_config.get('api_key')
    if not api_key:
        print("❌ OPENAI_API_KEY must be set in .env")
        return
    
    reply_generator = LLMReplyGenerator(
        api_key=api_key,
        model=llm_config.get('model', 'gpt-4o'),
        temperature=llm_config.get('temperature', 0.7)
    )
    
    threads_poster = ThreadsPoster(
        access_token=access_token,
        user_id=user_id
    )
    
    print("✓ All components initialized\n")
    
    # Check if we can reply
    print("="*60)
    print("Checking Rate Limits")
    print("="*60)
    if not reply_manager.can_reply_now():
        print("❌ Cannot reply now (rate limit reached or too soon)")
        print(f"   Daily replies: {reply_manager._get_today_reply_count()}/{reply_manager.MAX_REPLIES_PER_DAY}")
        return
    else:
        print(f"✓ Can reply now")
        print(f"   Daily replies: {reply_manager._get_today_reply_count()}/{reply_manager.MAX_REPLIES_PER_DAY}")
    
    # Get unreplied comments
    print("\n" + "="*60)
    print("Fetching Unreplied Comments")
    print("="*60)
    
    unreplied = reply_manager.get_unreplied_comments_recent_threads(limit_threads=10)
    
    if not unreplied:
        print("❌ No unreplied comments found")
        print("\nTo test:")
        print("1. Post a thread using: py main.py --test-text")
        print("2. Manually comment on that thread from another account")
        print("3. Run this script again: py test_auto_reply.py")
        return
    
    print(f"✓ Found {len(unreplied)} unreplied comment(s)\n")
    
    # Show first comment
    context = unreplied[0]
    print("="*60)
    print("First Unreplied Comment")
    print("="*60)
    print(f"Thread ID: {context.thread_id}")
    print(f"Reply ID: {context.reply_id}")
    print(f"Author: @{context.author_username}")
    print(f"Comment: {context.reply_text}")
    print()
    
    # Get original post text
    print("Fetching original post text...")
    try:
        url = f"https://graph.threads.net/v1.0/{context.thread_id}"
        params = {'access_token': access_token, 'fields': 'text'}
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            result = response.json()
            original_post_text = result.get('text', '')
            print(f"Original post: {original_post_text[:100]}...")
        else:
            original_post_text = "Check out my latest post!"
            print("⚠ Could not fetch original post, using placeholder")
    except Exception as e:
        original_post_text = "Check out my latest post!"
        print(f"⚠ Error fetching original post: {e}")
    
    # Generate reply
    print("\n" + "="*60)
    print("Generating Reply")
    print("="*60)
    
    reply_text = reply_generator.generate_reply(
        original_post_text=original_post_text,
        user_reply_text=context.reply_text,
        author_username=context.author_username
    )
    
    if not reply_text:
        print("❌ Failed to generate reply or reply was filtered")
        return
    
    print(f"Generated reply: {reply_text}")
    print(f"Length: {len(reply_text)} characters")
    
    # Ask for confirmation
    print("\n" + "="*60)
    print("Post Reply?")
    print("="*60)
    response = input("Post this reply? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("❌ Reply not posted (cancelled by user)")
        return
    
    # Post reply
    print("\n" + "="*60)
    print("Posting Reply")
    print("="*60)
    
    # Always reply directly to the comment (not the thread)
    # context.reply_id is the ID of the comment we want to reply to
    print(f"Replying to comment: {context.reply_id}")
    
    reply_id = threads_poster.post_reply(
        parent_id=context.reply_id,  # Always use the comment ID, not thread ID
        text=reply_text
    )
    
    if reply_id:
        # Mark as replied
        reply_manager.mark_replied(
            reply_id=context.reply_id,
            thread_id=context.thread_id,
            author_id=context.author_id
        )
        print(f"\n✅ Reply posted successfully!")
        print(f"   Reply ID: {reply_id}")
        print(f"   Thread ID: {context.thread_id}")
        print(f"   Comment ID: {context.reply_id}")
    else:
        print("\n❌ Failed to post reply")
    
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

