from dataclasses import dataclass
from time import time
from typing import Dict, Optional
from urllib.parse import urlparse

import aiomysql
import phpserialize

from liminus import settings


@dataclass
class CampaignSettingsCache:
    expiration: float
    campaign_data: Optional[dict]


class CampaignSettingsProvider:
    db_dsn: str
    connection_pool: aiomysql.Pool
    campaign_settings_cache: Dict[int, CampaignSettingsCache]

    def __init__(self):
        self.db_dsn = settings.READONLY_DATABASE_DSN
        self.cache_time = settings.CAMPAIGN_SETTINGS_CACHE_EXPIRY_SECONDS
        self.campaign_settings_cache = {}

    async def get_campaign_settings(self, campaign_id: int) -> Optional[dict]:
        now = time()
        cached = self.campaign_settings_cache.get(campaign_id)
        if cached:
            if cached.expiration > now:
                return cached.campaign_data
            # cache has expired
            del self.campaign_settings_cache[campaign_id]

        fresh_campaign_data = await self._get_campaign_settings_from_db(campaign_id)
        self.campaign_settings_cache[campaign_id] = CampaignSettingsCache(
            expiration=(now + self.cache_time), campaign_data=fresh_campaign_data
        )
        return fresh_campaign_data

    async def _get_campaign_settings_from_db(self, campaign_id: int) -> Optional[dict]:
        pool = await self._get_conn_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql = 'SELECT settings FROM ResCampaigns WHERE ID=%s'
                cursor.execute(sql, (campaign_id,))
                record = cursor.fetchone()

                if record is None:
                    return None

                settings = record['settings']
                data = phpserialize.loads(settings.encode(encoding='utf-8', errors='strict'), decode_strings=True)
                return data

    async def _get_conn_pool(self):
        if not self.connection_pool:
            db_parts = urlparse(self.db_dsn)
            self.connection_pool = await aiomysql.create_pool(
                host=db_parts.hostname,
                port=db_parts.port,
                user=db_parts.username,
                password=db_parts.password,
                db=db_parts.path.strip('/'),
                charset='utf8mb4',
            )
        return self.connection_pool
