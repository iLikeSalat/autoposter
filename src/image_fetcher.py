"""
Local Folder Image Fetcher
Fetches images from a local folder dynamically.
"""
import os
import random
from typing import List, Dict, Optional
from pathlib import Path


class ImageFetcher:
    def __init__(self, image_folder: str = "images", 
                 file_extensions: List[str] = None):
        self.image_folder = Path(image_folder)
        self.file_extensions = file_extensions or [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        
        # Ensure the folder exists
        if not self.image_folder.exists():
            self.image_folder.mkdir(parents=True, exist_ok=True)
            print(f"Created image folder: {self.image_folder}")
    
    def _is_image_file(self, filepath: Path) -> bool:
        """Check if file is an image based on extension."""
        return filepath.suffix.lower() in [ext.lower() for ext in self.file_extensions]
    
    def _find_images_recursive(self, folder: Path, images: List[Dict] = None) -> List[Dict]:
        """Recursively find all image files in the folder."""
        if images is None:
            images = []
        
        if not folder.exists() or not folder.is_dir():
            return images
        
        try:
            for item in folder.iterdir():
                if item.is_file() and self._is_image_file(item):
                    # Get file size
                    size = item.stat().st_size
                    images.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.image_folder)),
                        "full_path": str(item),
                        "size": size
                    })
                elif item.is_dir():
                    # Recursively search subdirectories
                    self._find_images_recursive(item, images)
        except PermissionError as e:
            print(f"Permission denied accessing {folder}: {e}")
        
        return images
    
    def get_all_images(self) -> List[Dict]:
        """Get all images from the folder."""
        print(f"Scanning images from {self.image_folder}...")
        images = self._find_images_recursive(self.image_folder)
        print(f"Found {len(images)} images")
        return images
    
    def get_random_image(self, exclude_used: List[str] = None) -> Optional[Dict]:
        """Get a random image that hasn't been used recently."""
        images = self.get_all_images()
        
        if not images:
            return None
        
        # Filter out recently used images
        if exclude_used:
            images = [img for img in images if img["path"] not in exclude_used]
        
        if not images:
            # If all images have been used, reset and use any image
            images = self.get_all_images()
        
        # Return random image
        if images:
            selected = random.choice(images)
            return selected
        
        return None
    
    def get_image_path(self, image_info: Dict) -> str:
        """Get the full path to an image."""
        return image_info["full_path"]


