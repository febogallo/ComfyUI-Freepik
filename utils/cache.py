"""
Caching system for Freepik API results
Avoid redundant API calls for identical parameters
"""

import os
import json
import hashlib
from PIL import Image
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import shutil


class FreepikCache:
    """Intelligent caching for API results"""
    
    def __init__(self, cache_dir: str = None, max_age_days: int = 30):
        """
        Initialize cache
        
        Args:
            cache_dir: Directory for cache storage
            max_age_days: Maximum age for cached items
        """
        if cache_dir is None:
            # Default to ComfyUI output directory
            cache_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "cache"
            )
        
        self.cache_dir = cache_dir
        self.max_age = timedelta(days=max_age_days)
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Create subdirectories for organization
        for subdir in ['images', 'metadata', 'temp']:
            os.makedirs(os.path.join(self.cache_dir, subdir), exist_ok=True)
    
    def _get_cache_key(self, params: Dict[str, Any]) -> str:
        """
        Generate unique cache key from parameters
        
        Args:
            params: Parameter dictionary
            
        Returns:
            MD5 hash string
        """
        # Sort keys for consistency
        param_str = json.dumps(params, sort_keys=True, default=str)
        
        # Generate hash
        cache_key = hashlib.md5(param_str.encode()).hexdigest()
        
        return cache_key
    
    def _get_image_path(self, cache_key: str) -> str:
        """Get path for cached image"""
        return os.path.join(self.cache_dir, 'images', f"{cache_key}.png")
    
    def _get_metadata_path(self, cache_key: str) -> str:
        """Get path for cached metadata"""
        return os.path.join(self.cache_dir, 'metadata', f"{cache_key}.json")
    
    def has_cached(self, params: Dict[str, Any]) -> bool:
        """
        Check if result is cached
        
        Args:
            params: Parameter dictionary
            
        Returns:
            True if valid cache exists
        """
        cache_key = self._get_cache_key(params)
        image_path = self._get_image_path(cache_key)
        metadata_path = self._get_metadata_path(cache_key)
        
        # Check if files exist
        if not (os.path.exists(image_path) and os.path.exists(metadata_path)):
            return False
        
        # Check age
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            cached_time = datetime.fromisoformat(metadata['timestamp'])
            age = datetime.now() - cached_time
            
            if age > self.max_age:
                print(f"⚠️ Cache expired (age: {age.days} days)")
                return False
            
            return True
            
        except Exception as e:
            print(f"⚠️ Cache validation error: {str(e)}")
            return False
    
    def get_cached(self, params: Dict[str, Any]) -> Optional[Image.Image]:
        """
        Retrieve cached result
        
        Args:
            params: Parameter dictionary
            
        Returns:
            PIL Image if cached, None otherwise
        """
        if not self.has_cached(params):
            return None
        
        cache_key = self._get_cache_key(params)
        image_path = self._get_image_path(cache_key)
        
        try:
            image = Image.open(image_path)
            print(f"✓ Cache hit: {cache_key[:8]}")
            return image
        except Exception as e:
            print(f"❌ Cache read error: {str(e)}")
            return None
    
    def save_to_cache(
        self,
        params: Dict[str, Any],
        image: Image.Image,
        extra_metadata: Optional[Dict] = None
    ):
        """
        Save result to cache
        
        Args:
            params: Parameter dictionary
            image: PIL Image to cache
            extra_metadata: Optional additional metadata
        """
        cache_key = self._get_cache_key(params)
        image_path = self._get_image_path(cache_key)
        metadata_path = self._get_metadata_path(cache_key)
        
        try:
            # Save image
            image.save(image_path, 'PNG', optimize=True)
            
            # Save metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'params': params,
                'image_size': image.size,
                'cache_key': cache_key
            }
            
            if extra_metadata:
                metadata.update(extra_metadata)
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✓ Cached: {cache_key[:8]}")
            
        except Exception as e:
            print(f"❌ Cache write error: {str(e)}")
    
    def clear_cache(self, older_than_days: Optional[int] = None):
        """
        Clear cache entries
        
        Args:
            older_than_days: Only clear entries older than this many days
                           If None, clear all cache
        """
        if older_than_days is None:
            # Clear everything
            shutil.rmtree(self.cache_dir)
            self._ensure_cache_dir()
            print("✓ Cache cleared completely")
            return
        
        # Clear old entries
        cutoff = datetime.now() - timedelta(days=older_than_days)
        cleared = 0
        
        metadata_dir = os.path.join(self.cache_dir, 'metadata')
        
        for metadata_file in os.listdir(metadata_dir):
            metadata_path = os.path.join(metadata_dir, metadata_file)
            
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                cached_time = datetime.fromisoformat(metadata['timestamp'])
                
                if cached_time < cutoff:
                    cache_key = metadata['cache_key']
                    
                    # Remove image and metadata
                    os.remove(self._get_image_path(cache_key))
                    os.remove(metadata_path)
                    
                    cleared += 1
                    
            except Exception as e:
                print(f"⚠️ Error clearing {metadata_file}: {str(e)}")
        
        print(f"✓ Cleared {cleared} cache entries older than {older_than_days} days")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        images_dir = os.path.join(self.cache_dir, 'images')
        metadata_dir = os.path.join(self.cache_dir, 'metadata')
        
        # Count files
        num_images = len(os.listdir(images_dir))
        num_metadata = len(os.listdir(metadata_dir))
        
        # Calculate total size
        total_size = 0
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                filepath = os.path.join(root, file)
                total_size += os.path.getsize(filepath)
        
        # Convert to MB
        total_size_mb = total_size / (1024 * 1024)
        
        return {
            'num_entries': num_images,
            'total_size_mb': round(total_size_mb, 2),
            'cache_dir': self.cache_dir,
            'max_age_days': self.max_age.days
        }
    
    def print_stats(self):
        """Print cache statistics"""
        stats = self.get_cache_stats()
        print("\n" + "="*50)
        print("📊 Cache Statistics")
        print("="*50)
        print(f"Entries:     {stats['num_entries']}")
        print(f"Total Size:  {stats['total_size_mb']} MB")
        print(f"Location:    {stats['cache_dir']}")
        print(f"Max Age:     {stats['max_age_days']} days")
        print("="*50 + "\n")


# Global cache instance
_global_cache = None


def get_cache(cache_dir: Optional[str] = None) -> FreepikCache:
    """Get global cache instance"""
    global _global_cache
    
    if _global_cache is None:
        _global_cache = FreepikCache(cache_dir)
    
    return _global_cache
