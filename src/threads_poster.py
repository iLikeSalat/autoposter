"""
Threads (Meta) Poster
Handles posting threads with images to Meta's Threads platform.
Uses Threads API as documented at: https://developers.facebook.com/docs/threads/posts/
"""
import requests
from typing import List, Optional
import os
import time


class ThreadsPoster:
    def __init__(self, access_token: str, user_id: str, image_host_url: Optional[str] = None):
        """Initialize Threads API client.
        
        Args:
            access_token: Threads API access token
            user_id: Threads user ID
            image_host_url: Optional base URL for hosting images publicly.
                          If provided, local images will be uploaded there first.
                          Example: "https://your-domain.com/images/"
        """
        self.access_token = access_token
        self.user_id = user_id
        self.base_url = "https://graph.threads.net/v1.0"
        self.image_host_url = image_host_url
    
    def _get_image_url(self, image_path: str) -> Optional[str]:
        """Get a publicly accessible URL for an image.
        
        Threads API requires images to be hosted on a public server.
        If image_host_url is set, upload the image there.
        Otherwise, return None (will post text-only).
        """
        if not self.image_host_url:
            print("⚠ No image hosting URL configured. Images must be publicly accessible.")
            print("   Set image_host_url in ThreadsPoster or host images yourself.")
            return None
        
        # If image_path is already a URL, return it
        if image_path.startswith('http://') or image_path.startswith('https://'):
            return image_path
        
        # TODO: Implement image upload to hosting service
        # For now, if image_host_url is set, assume the image is already there
        # You'll need to implement actual upload logic based on your hosting service
        filename = os.path.basename(image_path)
        return f"{self.image_host_url.rstrip('/')}/{filename}"
    
    def _create_text_container(self, text: str) -> Optional[str]:
        """Create a simple text container using the official method.
        
        Args:
            text: Text content (max 500 characters)
            
        Returns:
            Container ID if successful, None otherwise
        """
        url = f"{self.base_url}/{self.user_id}/threads"
        
        # Ensure text is within 500 character limit
        if len(text) > 500:
            print(f"⚠ Text is {len(text)} characters, truncating to 500")
            text = text[:497] + "..."
        
        # API requires media_type for text posts
        # Note: is_restricted_content must be string "false", not boolean False
        data = {
            'text': text,
            'access_token': self.access_token,
            'is_restricted_content': 'false',  # String, not boolean
            'media_type': 'TEXT'  # Required by API
        }
        
        try:
            print(f"Creating text container...")
            print(f"URL: {url}")
            print(f"Data: text={text[:50]}..., access_token=..., is_restricted_content=false")
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 500:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    print(f"❌ 500 error: {error_msg}")
                    print("   This usually means:")
                    print("   1. Your app doesn't have Threads Content Publishing permissions approved")
                    print("   2. Check: https://developers.facebook.com/apps → Your App → Threads → Content Publishing")
                    print("   3. Must show 'Approved' status")
                except:
                    print(f"❌ 500 error: {response.text[:200]}")
                return None
            
            response.raise_for_status()
            result = response.json()
            
            if 'id' in result:
                print(f"✓ Container created: {result['id']}")
                return result['id']
            else:
                print(f"❌ Unexpected response: {result}")
                return None
                
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_code = error_data.get('error', {}).get('code')
                    error_message = error_data.get('error', {}).get('message', 'Unknown error')
                    print(f"   Error code: {error_code}")
                    print(f"   Error message: {error_message}")
                    
                    if error_code == 190:
                        print("   → Invalid access token - regenerate with: py get_threads_token.py")
                except:
                    print(f"   Response: {e.response.text[:200]}")
            return None
        except Exception as e:
            print(f"❌ Error creating container: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _publish_container(self, container_id: str) -> Optional[str]:
        """Publish a Threads container using the official method.
        
        Args:
            container_id: The container ID from _create_text_container
            
        Returns:
            Published post ID if successful, None otherwise
        """
        # Wait for container to be ready (API docs recommend ~30 seconds on average)
        # Using 5 seconds as minimum for testing
        time.sleep(5)
        
        url = f"{self.base_url}/{self.user_id}/threads_publish"
        
        # Official format
        data = {
            'creation_id': container_id,
            'access_token': self.access_token
        }
        
        try:
            print(f"Publishing container {container_id}...")
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 500:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    print(f"❌ 500 error: {error_msg}")
                except:
                    print(f"❌ 500 error: {response.text[:200]}")
                return None
            
            response.raise_for_status()
            result = response.json()
            
            if 'id' in result:
                print(f"✓ Published: {result['id']}")
                return result['id']
            else:
                print(f"❌ Unexpected response: {result}")
                return None
                
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error publishing: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {e.response.text[:200]}")
            return None
        except Exception as e:
            print(f"❌ Error publishing: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _post_text(self, text: str) -> Optional[str]:
        """Post a simple text post using Threads API.
        
        Args:
            text: Text content to post (max 500 characters)
            
        Returns:
            Published post ID if successful, None otherwise
        """
        # Create text container (no media_type for TEXT posts)
        container_id = self._create_text_container(text)
        if not container_id:
            return None
        
        # Publish the container
        post_id = self._publish_container(container_id)
        return post_id
    
    def _create_image_container(self, text: str, image_url: str) -> Optional[str]:
        """Create an image container for Threads API.
        
        Args:
            text: Caption text (max 500 characters)
            image_url: Publicly accessible image URL
            
        Returns:
            Container ID if successful, None otherwise
        """
        url = f"{self.base_url}/{self.user_id}/threads"
        
        # Ensure text is within 500 character limit
        if len(text) > 500:
            print(f"⚠ Text is {len(text)} characters, truncating to 500")
            text = text[:497] + "..."
        
        data = {
            'text': text,
            'access_token': self.access_token,
            'is_restricted_content': 'false',
            'media_type': 'IMAGE',
            'image_url': image_url
        }
        
        try:
            print(f"Creating image container...")
            print(f"Image URL: {image_url[:50]}...")
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 500:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    print(f"❌ 500 error: {error_msg}")
                except:
                    print(f"❌ 500 error: {response.text[:200]}")
                return None
            
            response.raise_for_status()
            result = response.json()
            
            if 'id' in result:
                print(f"✓ Image container created: {result['id']}")
                return result['id']
            else:
                print(f"❌ Unexpected response: {result}")
                return None
                
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_code = error_data.get('error', {}).get('code')
                    error_message = error_data.get('error', {}).get('message', 'Unknown error')
                    print(f"   Error code: {error_code}")
                    print(f"   Error message: {error_message}")
                except:
                    print(f"   Response: {e.response.text[:200]}")
            return None
        except Exception as e:
            print(f"❌ Error creating image container: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _post_image(self, text: str, image_url: str) -> Optional[str]:
        """Post an image with caption using Threads API.
        
        Args:
            text: Caption text
            image_url: Publicly accessible image URL
            
        Returns:
            Published post ID if successful, None otherwise
        """
        container_id = self._create_image_container(text, image_url)
        if not container_id:
            return None
        
        post_id = self._publish_container(container_id)
        return post_id
    
    def post_thread(self, posts: List[str], image_path: Optional[str] = None) -> bool:
        """Post a text or image post.
        
        Args:
            posts: List of text posts to publish
            image_path: If provided and is a URL, post as image. If None, post as text.
            
        Returns:
            True if successful, False otherwise
        """
        if not posts:
            print("❌ No posts to publish")
            return False
        
        try:
            first_post = posts[0]
            
            # Check if image_path is provided and is a URL (uploaded image)
            if image_path and (image_path.startswith('http://') or image_path.startswith('https://')):
                print(f"📸 Posting image post...")
                post_id = self._post_image(first_post, image_path)
            else:
                print(f"📝 Posting text-only post...")
                post_id = self._post_text(first_post)
            
            if not post_id:
                print("❌ Failed to post")
                return False
            
            print(f"✅ Posted successfully! Post ID: {post_id}")
            
            if len(posts) > 1:
                print(f"⚠ Note: Only posted first post. {len(posts) - 1} remaining posts skipped.")
            
            return True
            
        except Exception as e:
            print(f"❌ Error posting: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_credentials(self) -> bool:
        """Verify Threads API credentials.
        
        Note: Verification endpoint may sometimes fail with 500 errors.
        If verification fails but token is valid, this will return False.
        The real test is attempting to post.
        """
        try:
            # Try Threads API endpoint first
            url = f"{self.base_url}/{self.user_id}"
            params = {
                'access_token': self.access_token,
                'fields': 'username'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'username' in result:
                print(f"Authenticated as: @{result['username']}")
                return True
            return False
            
        except requests.exceptions.HTTPError as e:
            # If it's a 500 error, the API might be having issues but token could still be valid
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 500:
                    print("⚠ Verification endpoint returned 500 error (API issue)")
                    print("   Token may still be valid - will test with actual post")
                    return True  # Assume valid, let actual posting be the real test
                try:
                    error_data = e.response.json()
                    if error_data.get('error', {}).get('code') == 190:
                        # Invalid token error
                        print(f"❌ Invalid token: {error_data.get('error', {}).get('message', 'Unknown error')}")
                        return False
                except:
                    pass
            print(f"⚠ Verification failed: {e}")
            return True  # Assume valid, let actual posting be the real test
        except Exception as e:
            print(f"⚠ Verification error: {e}")
            return True  # Assume valid, let actual posting be the real test
    
    def post_reply(self, parent_id: str, text: str) -> Optional[str]:
        """Create and publish a text reply to a given thread or reply.
        
        Uses POST /{user-id}/threads with media_type=TEXT, reply_to_id, auto_publish_text=true.
        
        Args:
            parent_id: Thread ID or reply ID to reply to
            text: Reply text (max 500 characters)
            
        Returns:
            Created reply ID if successful, None otherwise
        """
        url = f"{self.base_url}/{self.user_id}/threads"
        
        # Ensure text is within 500 character limit
        if len(text) > 500:
            print(f"⚠ Reply text is {len(text)} characters, truncating to 500")
            text = text[:497] + "..."
        
        data = {
            'text': text,
            'access_token': self.access_token,
            'is_restricted_content': 'false',
            'media_type': 'TEXT',
            'reply_to_id': parent_id,
            'auto_publish_text': 'true'  # Auto-publish so we don't need to call threads_publish
        }
        
        try:
            print(f"Creating reply to {parent_id}...")
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 500:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    print(f"❌ 500 error: {error_msg}")
                except:
                    print(f"❌ 500 error: {response.text[:200]}")
                return None
            
            response.raise_for_status()
            result = response.json()
            
            if 'id' in result:
                reply_id = result['id']
                print(f"✓ Reply created and published: {reply_id}")
                return reply_id
            else:
                print(f"❌ Unexpected response: {result}")
                return None
                
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error posting reply: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_code = error_data.get('error', {}).get('code')
                    error_message = error_data.get('error', {}).get('message', 'Unknown error')
                    print(f"   Error code: {error_code}")
                    print(f"   Error message: {error_message}")
                    
                    if error_code == 190:
                        print("   → Invalid access token - regenerate with: py get_threads_token.py")
                except:
                    print(f"   Response: {e.response.text[:200]}")
            return None
        except Exception as e:
            print(f"❌ Error posting reply: {e}")
            import traceback
            traceback.print_exc()
            return None

