import redis.asyncio as redis

from app.utils.secrets import secret_store

# redis_client = redis.StrictRedis(host="redis", port=6379, password=secret_store.REDIS_PASSWORD, decode_responses=True)
redis_client = redis.StrictRedis(host="redis", port=6379, decode_responses=True)
