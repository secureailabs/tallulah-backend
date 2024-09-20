import abc
import threading
import time
from typing import Dict

# import redis


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


# class RedisLockStore(LockStore):
#     def __init__(self, redis_client, expiry=None):
#         super().__init__(expiry)
#         self.redis_client = redis_client
#         self._locks = {}

#     def acquire(self, name, expiry=None):
#         if name not in self._locks:
#             actual_expiry = expiry if expiry is not None else self.expiry
#             self._locks[name] = self.redis_client.lock(name, timeout=actual_expiry)
#         return self._locks[name].acquire(blocking=False)

#     def release(self, name):
#         if name in self._locks:
#             self._locks[name].release()
#             del self._locks[name]

#     def is_locked(self, name):
#         # Redis locks don't provide a direct way to check if a lock is held,
#         # but we can attempt to acquire it without blocking.
#         if name not in self._locks:
#             self._locks[name] = self.redis_client.lock(name, timeout=self.expiry)
#         lock_acquired = self._locks[name].acquire(blocking=False)
#         if lock_acquired:
#             # We acquired the lock, so it was not held. Release it immediately.
#             self._locks[name].release()
#             return False
#         else:
#             # Lock is held by someone else.
#             return True


if __name__ == "__main__":
    # Test LocalLockStore
    print("Testing LocalLockStore")
    local_lock_store = LocalLockStore()

    lock_name = "my_local_lock"
    if local_lock_store.acquire(lock_name, expiry=5):
        print(f"Acquired local lock '{lock_name}'")
        time.sleep(2)
        print(f"Within local lock '{lock_name}'")
        local_lock_store.release(lock_name)
        print(f"Released local lock '{lock_name}'")
    else:
        print(f"Failed to acquire local lock '{lock_name}'")

    # Test RedisLockStore (Requires a running Redis server)
    # print("\nTesting RedisLockStore")
    # redis_client = redis.Redis(host="localhost", port=6379, db=0)
    # redis_lock_store = RedisLockStore(redis_client, expiry=5)

    # lock_name = "my_redis_lock"
    # if redis_lock_store.acquire(lock_name):
    #     print(f"Acquired Redis lock '{lock_name}'")
    #     time.sleep(2)
    #     print(f"Within Redis lock '{lock_name}'")
    #     redis_lock_store.release(lock_name)
    #     print(f"Released Redis lock '{lock_name}'")
    # else:
    #     print(f"Failed to acquire Redis lock '{lock_name}'")
