"""
Simple cache system for dashboard stats
"""

import json
import redis.asyncio as redis
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from app.core.config import settings

class DashboardCache:
    """Simple cache for dashboard statistics"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.cache_ttl = 300  # 5 minutes

    async def get_client(self) -> redis.Redis:
        """Get Redis client"""
        if not self.redis_client:
            self.redis_client = redis.from_url(settings.REDIS_URL)
        return self.redis_client

    async def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get cached dashboard stats"""
        try:
            client = await self.get_client()
            cached_data = await client.get("dashboard:stats")

            if cached_data:
                return json.loads(cached_data)

            return None
        except Exception:
            return None

    async def set_stats(self, stats: Dict[str, Any]) -> bool:
        """Cache dashboard stats"""
        try:
            client = await self.get_client()
            stats_with_timestamp = {
                **stats,
                "cached_at": datetime.utcnow().isoformat(),
                "cache_ttl": self.cache_ttl
            }

            await client.set(
                "dashboard:stats",
                json.dumps(stats_with_timestamp, default=str),
                ex=self.cache_ttl
            )

            return True
        except Exception:
            return False

    async def clear_cache(self) -> bool:
        """Clear dashboard cache"""
        try:
            client = await self.get_client()
            await client.delete("dashboard:stats")
            return True
        except Exception:
            return False

# Global cache instance
dashboard_cache = DashboardCache()
