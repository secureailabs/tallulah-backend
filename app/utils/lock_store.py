import abc
import threading
import time
from typing import Dict

from app.utils.redis_client import redis_client


class LockStore(abc.ABC):
    def __init__(self, expiry=None):
        self.expiry = expiry

    @abc.abstractmethod
    def acquire(self, name, expiry=None):
        pass

    @abc.abstractmethod
    def release(self, name):
        pass

    @abc.abstractmethod
    def is_locked(self, name):
        pass


class LocalLockStore(LockStore):
    def __new__(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = super(LocalLockStore, cls).__new__(cls)
            cls._locks: Dict[str, threading.Lock] = {}
            cls._timers: Dict[str, threading.Timer] = {}
            cls._store_lock = threading.Lock()
        return cls._instance

    def acquire(self, name: str, expiry: int):
        with self._store_lock:
            if name not in self._locks:
                self._locks[name] = threading.Lock()

            lock_acquired = self._locks[name].acquire(blocking=False)
            if lock_acquired:
                # Start a timer to release the lock after expiry seconds
                timer = threading.Timer(expiry, self.release, args=(name,))
                timer.start()
                self._timers[name] = timer
            return lock_acquired

    def release(self, name):
        with self._store_lock:
            if name in self._locks and self._locks[name].locked():
                self._locks[name].release()
                if name in self._timers:
                    self._timers[name].cancel()
                    del self._timers[name]

    def is_locked(self, name):
        with self._store_lock:
            return name in self._locks and self._locks[name].locked()


class RedisLockStore(LockStore):
    def __new__(cls) -> "RedisLockStore":
        if not hasattr(cls, "_instance"):
            cls._instance = super(RedisLockStore, cls).__new__(cls)
            cls.redis_client = redis_client
        return cls._instance

    async def acquire(self, name, expiry=None):
        if not expiry:
            expiry = self.expiry

        # Try to acquire the lock
        lock_acquired = await self.redis_client.set(name, "LOCKED", ex=expiry, nx=True)

        # return True if lock is acquired else False
        return lock_acquired

    async def release(self, name):
        await self.redis_client.delete(name)

    async def is_locked(self, name):
        return await self.redis_client.exists(name)
