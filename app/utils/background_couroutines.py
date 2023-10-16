# -------------------------------------------------------------------------------
# Engineering
# async_tasks.py
# -------------------------------------------------------------------------------
"""Run and manage async tasks with fastapi"""
# -------------------------------------------------------------------------------
# Copyright (C) 2022 Secure Ai Labs, Inc. All Rights Reserved.
# Private and Confidential. Internal Use Only.
#     This software contains proprietary information which shall not
#     be reproduced or transferred to other documents and shall not
#     be disclosed to others for any purpose without
#     prior written permission of Secure Ai Labs, Inc.
# -------------------------------------------------------------------------------

import asyncio
from typing import Any, Coroutine


class AsyncTaskManager:
    _instance = None
    _loop = asyncio.get_event_loop()
    _tasks = set()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AsyncTaskManager, cls).__new__(cls)
        return cls._instance

    async def _wrap_task(self, coro: Coroutine, callback=None):
        try:
            result = await coro
            if callback:
                callback(result)
        except Exception as e:
            print(f"An exception was caught in the async task: {str(e)}")
        finally:
            if self._tasks:
                await asyncio.wait(self._tasks)
            self._tasks.discard(coro)

    def create_task(self, coro: Coroutine, callback=None) -> None:
        if not asyncio.iscoroutine(coro):
            raise ValueError("Expected a coroutine for the execution")

        task = self._loop.create_task(self._wrap_task(coro, callback))
        self._tasks.add(task)

    async def wait_tasks(self) -> None:
        if self._tasks:
            await asyncio.wait(self._tasks)
