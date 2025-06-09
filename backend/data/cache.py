import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import json
import yaml
import os
from dataclasses import dataclass
import time
from datetime import datetime, timedelta
import redis
from redis import Redis
import pickle
import hashlib
import threading
import logging
import functools
import inspect
import weakref
import gc
import psutil
import mmap
import tempfile
import shutil
from pathlib import Path

@dataclass
class CacheConfig:
    """Configuration for the cache system."""
    cache_dir: str
    redis_url: str
    max_size: int
    ttl: int
    cleanup_interval: int
    compression: bool
    encryption: bool
    enable_redis: bool
    enable_disk: bool
    enable_memory: bool

class DataCache:
    def __init__(self, config_path: str = 'config/cache_config.yaml'):
        """Initialize the cache system."""
        self.config_path = config_path
        self.config = self._load_config()
        self.cache = {}
        self.memory_cache = {}
        self.disk_cache = {}
        self.redis_cache = None
        self.cleanup_thread = None
        self.is_cleaning = False
        
        # Create cache directory
        os.makedirs(self.config.cache_dir, exist_ok=True)
        
        # Initialize cache backends
        self._init_cache_backends()
        
        # Start cleanup thread
        self.start_cleanup()

    def _load_config(self) -> CacheConfig:
        """Load cache configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return CacheConfig(**config_dict)
        except Exception as e:
            print(f"Error loading cache configuration: {str(e)}")
            raise

    def _init_cache_backends(self) -> None:
        """Initialize cache backends."""
        try:
            # Initialize Redis cache
            if self.config.enable_redis:
                self.redis_cache = Redis.from_url(self.config.redis_url)
            
            # Initialize disk cache
            if self.config.enable_disk:
                self.disk_cache = {}
            
            # Initialize memory cache
            if self.config.enable_memory:
                self.memory_cache = {}
            
        except Exception as e:
            print(f"Error initializing cache backends: {str(e)}")
            raise

    def start_cleanup(self) -> None:
        """Start cache cleanup thread."""
        try:
            if not self.is_cleaning:
                self.is_cleaning = True
                self.cleanup_thread = threading.Thread(target=self._cleanup_cache)
                self.cleanup_thread.daemon = True
                self.cleanup_thread.start()
            
        except Exception as e:
            print(f"Error starting cleanup thread: {str(e)}")
            raise

    def stop_cleanup(self) -> None:
        """Stop cache cleanup thread."""
        try:
            self.is_cleaning = False
            if self.cleanup_thread:
                self.cleanup_thread.join()
            
        except Exception as e:
            print(f"Error stopping cleanup thread: {str(e)}")
            raise

    def _cleanup_cache(self) -> None:
        """Clean up expired cache entries."""
        try:
            while self.is_cleaning:
                # Clean memory cache
                if self.config.enable_memory:
                    self._cleanup_memory_cache()
                
                # Clean disk cache
                if self.config.enable_disk:
                    self._cleanup_disk_cache()
                
                # Clean Redis cache
                if self.config.enable_redis:
                    self._cleanup_redis_cache()
                
                # Sleep for cleanup interval
                time.sleep(self.config.cleanup_interval)
            
        except Exception as e:
            print(f"Error cleaning up cache: {str(e)}")
            raise

    def _cleanup_memory_cache(self) -> None:
        """Clean up memory cache."""
        try:
            current_time = time.time()
            
            # Remove expired entries
            expired_keys = [
                key for key, (value, timestamp) in self.memory_cache.items()
                if current_time - timestamp > self.config.ttl
            ]
            
            for key in expired_keys:
                del self.memory_cache[key]
            
            # Check memory usage
            if psutil.Process().memory_info().rss > self.config.max_size:
                # Remove oldest entries
                sorted_entries = sorted(
                    self.memory_cache.items(),
                    key=lambda x: x[1][1]
                )
                
                while psutil.Process().memory_info().rss > self.config.max_size:
                    if not sorted_entries:
                        break
                    key, _ = sorted_entries.pop(0)
                    del self.memory_cache[key]
            
        except Exception as e:
            print(f"Error cleaning up memory cache: {str(e)}")
            raise

    def _cleanup_disk_cache(self) -> None:
        """Clean up disk cache."""
        try:
            current_time = time.time()
            
            # Remove expired files
            for filename in os.listdir(self.config.cache_dir):
                filepath = os.path.join(self.config.cache_dir, filename)
                
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    
                    if current_time - file_time > self.config.ttl:
                        os.remove(filepath)
            
            # Check disk usage
            total_size = sum(
                os.path.getsize(os.path.join(self.config.cache_dir, f))
                for f in os.listdir(self.config.cache_dir)
            )
            
            if total_size > self.config.max_size:
                # Remove oldest files
                files = [
                    (f, os.path.getmtime(os.path.join(self.config.cache_dir, f)))
                    for f in os.listdir(self.config.cache_dir)
                ]
                
                files.sort(key=lambda x: x[1])
                
                while total_size > self.config.max_size:
                    if not files:
                        break
                    filename, _ = files.pop(0)
                    filepath = os.path.join(self.config.cache_dir, filename)
                    total_size -= os.path.getsize(filepath)
                    os.remove(filepath)
            
        except Exception as e:
            print(f"Error cleaning up disk cache: {str(e)}")
            raise

    def _cleanup_redis_cache(self) -> None:
        """Clean up Redis cache."""
        try:
            if not self.config.enable_redis:
                return
            
            # Redis automatically handles TTL
            pass
            
        except Exception as e:
            print(f"Error cleaning up Redis cache: {str(e)}")
            raise

    def get(self, key: str) -> Any:
        """Get a value from the cache."""
        try:
            # Try memory cache
            if self.config.enable_memory and key in self.memory_cache:
                value, timestamp = self.memory_cache[key]
                if time.time() - timestamp <= self.config.ttl:
                    return value
            
            # Try disk cache
            if self.config.enable_disk:
                filepath = os.path.join(self.config.cache_dir, f"{key}.cache")
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        value = pickle.load(f)
                    return value
            
            # Try Redis cache
            if self.config.enable_redis:
                value = self.redis_cache.get(key)
                if value:
                    return pickle.loads(value)
            
            return None
            
        except Exception as e:
            print(f"Error getting from cache: {str(e)}")
            raise

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache."""
        try:
            # Set in memory cache
            if self.config.enable_memory:
                self.memory_cache[key] = (value, time.time())
            
            # Set in disk cache
            if self.config.enable_disk:
                filepath = os.path.join(self.config.cache_dir, f"{key}.cache")
                with open(filepath, 'wb') as f:
                    pickle.dump(value, f)
            
            # Set in Redis cache
            if self.config.enable_redis:
                self.redis_cache.setex(
                    key,
                    self.config.ttl,
                    pickle.dumps(value)
                )
            
        except Exception as e:
            print(f"Error setting in cache: {str(e)}")
            raise

    def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        try:
            # Delete from memory cache
            if self.config.enable_memory and key in self.memory_cache:
                del self.memory_cache[key]
            
            # Delete from disk cache
            if self.config.enable_disk:
                filepath = os.path.join(self.config.cache_dir, f"{key}.cache")
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            # Delete from Redis cache
            if self.config.enable_redis:
                self.redis_cache.delete(key)
            
        except Exception as e:
            print(f"Error deleting from cache: {str(e)}")
            raise

    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            # Clear memory cache
            if self.config.enable_memory:
                self.memory_cache.clear()
            
            # Clear disk cache
            if self.config.enable_disk:
                for filename in os.listdir(self.config.cache_dir):
                    filepath = os.path.join(self.config.cache_dir, filename)
                    if os.path.isfile(filepath):
                        os.remove(filepath)
            
            # Clear Redis cache
            if self.config.enable_redis:
                self.redis_cache.flushdb()
            
        except Exception as e:
            print(f"Error clearing cache: {str(e)}")
            raise

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        try:
            stats = {
                'memory_cache_size': len(self.memory_cache) if self.config.enable_memory else 0,
                'disk_cache_size': sum(
                    os.path.getsize(os.path.join(self.config.cache_dir, f))
                    for f in os.listdir(self.config.cache_dir)
                ) if self.config.enable_disk else 0,
                'redis_cache_size': self.redis_cache.dbsize() if self.config.enable_redis else 0
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting cache stats: {str(e)}")
            raise

    def cache_decorator(self, ttl: Optional[int] = None):
        """Decorator for caching function results."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                key_parts = [
                    func.__name__,
                    str(args),
                    str(sorted(kwargs.items()))
                ]
                key = hashlib.md5(''.join(key_parts).encode()).hexdigest()
                
                # Try to get from cache
                cached_value = self.get(key)
                if cached_value is not None:
                    return cached_value
                
                # Call function
                result = func(*args, **kwargs)
                
                # Cache result
                self.set(key, result)
                
                return result
            
            return wrapper
        
        return decorator

# Example usage
if __name__ == "__main__":
    # Create cache instance
    cache = DataCache()
    
    # Example cached function
    @cache.cache_decorator()
    def expensive_operation(x: int) -> int:
        time.sleep(1)  # Simulate expensive operation
        return x * x
    
    # Test caching
    result1 = expensive_operation(5)  # First call - slow
    result2 = expensive_operation(5)  # Second call - fast (cached)
    
    print(f"Result: {result1}")
    print(f"Cache stats: {cache.get_cache_stats()}")
    
    # Clear cache
    cache.clear() 