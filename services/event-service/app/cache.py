import json
import uuid

import redis

from app.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def _key(event_id: uuid.UUID) -> str:
    return f"seatmap:{event_id}"


def get_cached_seat_map(event_id: uuid.UUID) -> dict | None:
    raw = redis_client.get(_key(event_id))
    return json.loads(raw) if raw else None


def cache_seat_map(event_id: uuid.UUID, data: dict) -> None:
    redis_client.setex(_key(event_id), settings.CACHE_TTL_SECONDS, json.dumps(data, default=str))


def invalidate_seat_map(event_id: uuid.UUID) -> None:
    redis_client.delete(_key(event_id))
