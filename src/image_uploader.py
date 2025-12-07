"""
Image Uploader for Threads API
Uploads images to Imgur (or other hosting services) to get publicly accessible URLs.
Threads API requires images to be publicly hosted.
"""
import os
import requests
from typing import Optional
from pathlib import Path


class ImageUploader:
    """Upload images to public hosting services for Threads API."""
    
    def __init__(self, service: str = "imgur", api_key: Optional[str] = None):
        """
        Initialize image uploader.
        
        Args:
            service: Hosting service ('imgur', 'imgbb', etc.)
            api_key: API key for the service (optional for some services)
        """
        self.service = service.lower()
        # Support both old IMGUR_CLIENT_ID and new IMGBB_API_KEY for backwards compatibility
        if self.service == 'imgbb':
            self.api_key = api_key or os.getenv('IMGBB_API_KEY') or os.getenv('IMGUR_CLIENT_ID')
        elif self.service == 'imgur':
            self.api_key = api_key or os.getenv('IMGUR_CLIENT_ID')
        else:
            self.api_key = api_key
        
        if self.service == 'imgbb' and not self.api_key:
            print("⚠ Warning: IMGBB_API_KEY not set. Image uploads will fail.")
            print("   Get your API key from: https://api.imgbb.com/")
            print("   Add IMGBB_API_KEY to your .env file")
        elif self.service == 'imgur' and not self.api_key:
            print("⚠ Warning: IMGUR_CLIENT_ID not set. Image uploads will fail.")
            print("   Get your client ID from: https://api.imgur.com/oauth2/addclient")
            print("   Add IMGUR_CLIENT_ID to your .env file")
    
    def upload(self, image_path: str) -> Optional[str]:
        """
        Upload an image and return the public URL.
        
        Args:
            image_path: Path to local image file
            
        Returns:
            Public URL of uploaded image, or None if upload failed
        """
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return None
        
        if self.service == 'imgur':
            return self._upload_to_imgur(image_path)
        elif self.service == 'imgbb':
            return self._upload_to_imgbb(image_path)
        else:
            print(f"❌ Unsupported service: {self.service}")
            return None
    
    def _upload_to_imgur(self, image_path: str) -> Optional[str]:
        """Upload image to Imgur."""
        if not self.api_key:
            print("❌ Imgur API key not configured")
            return None
        
        try:
            # Read image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Upload to Imgur
            headers = {
                'Authorization': f'Client-ID {self.api_key}'
            }
            
            files = {
                'image': image_data
            }
            
            response = requests.post(
                'https://api.imgur.com/3/image',
                headers=headers,
                files=files,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('success') and 'data' in result:
                image_url = result['data'].get('link')
                if image_url:
                    print(f"✓ Image uploaded to Imgur: {image_url}")
                    return image_url
                else:
                    print(f"❌ No URL in Imgur response: {result}")
                    return None
            else:
                error_msg = result.get('data', {}).get('error', 'Unknown error')
                print(f"❌ Imgur upload failed: {error_msg}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error uploading to Imgur: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Response: {e.response.text[:200]}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error uploading image: {e}")
            return None
    
    def _upload_to_imgbb(self, image_path: str) -> Optional[str]:
        """Upload image to ImgBB (alternative service)."""
        if not self.api_key:
            print("❌ ImgBB API key not configured")
            return None
        
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            response = requests.post(
                'https://api.imgbb.com/1/upload',
                data={
                    'key': self.api_key
                },
                files={
                    'image': image_data
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('success') and 'data' in result:
                # ImgBB returns URL in data.url (direct link) or data.image.url (image object)
                image_url = result['data'].get('url') or result['data'].get('image', {}).get('url')
                if image_url:
                    print(f"✓ Image uploaded to ImgBB: {image_url}")
                    return image_url
                else:
                    print(f"❌ No URL in ImgBB response: {result}")
                    return None
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                print(f"❌ ImgBB upload failed: {error_msg}")
                return None
                
        except Exception as e:
            print(f"❌ Error uploading to ImgBB: {e}")
            return None

