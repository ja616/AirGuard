import redis
import json
import os
import asyncio
from typing import Callable, Awaitable

class RedisPubSub:
    """Simple Redis PubSub wrapper for the Investigation pipeline events."""
    
    def __init__(self):
        # Default to local redis or use docker host
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_url = f"redis://{redis_host}:{redis_port}/0"
        
        # Async Redis client for subscribers (WebSockets)
        # We import aioredis/redis.asyncio dynamically to not break sync threads
        import redis.asyncio as aioredis
        self.async_client = aioredis.from_url(self.redis_url)
        
        # Sync Redis client for publishers (Background Threads)
        self.sync_client = redis.Redis.from_url(self.redis_url)

    def publish(self, channel: str, message: dict):
        """Publish a JSON message synchronously (safe for background threads)."""
        self.sync_client.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str, callback: Callable[[dict], Awaitable[None]]):
        """Subscribe to a channel asynchronously and yield to a callback (safe for FastAPI routes)."""
        pubsub = self.async_client.pubsub()
        await pubsub.subscribe(channel)
        
        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    data = json.loads(message['data'])
                    await callback(data)
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

# Global singleton
redis_pubsub = RedisPubSub()
