import asyncio
import random
from typing import Coroutine, Dict


class DaemonManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DaemonManager, cls).__new__(cls)
            cls.tasks: Dict[str, asyncio.Task] = {}
        return cls._instance

    def add_task(self, name, coro: Coroutine):
        if not asyncio.iscoroutine(coro):
            raise ValueError("Expected a coroutine for the execution")

        if name in self.tasks:
            raise ValueError(f"Daemon task with name '{name}' already exists.")
        # Start the task
        self.tasks[name] = asyncio.create_task(self._run_task(name, coro))

    async def _run_task(self, name: str, coro: Coroutine):
        while True:
            try:
                print(f"Starting daemon task '{name}'.")
                await coro
            except Exception as e:
                print(f"Task '{name}' failed with exception: {e}. Restarting...")
                await asyncio.sleep(1)

    def cancel_task(self, name):
        if name in self.tasks:
            self.tasks[name].cancel()
            del self.tasks[name]
            print(f"Task '{name}' has been cancelled.")
        else:
            raise ValueError(f"Task with name '{name}' does not exist.")

    def cancel_all_tasks(self):
        for name, task in self.tasks.items():
            task.cancel()
            print(f"Task '{name}' has been cancelled.")
        self.tasks.clear()


# Example daemon tasks
async def my_task():
    while True:
        print("my_task is running.")
        await asyncio.sleep(1)
        if random.random() < 0.2:
            raise Exception("Random failure in my_task.")


async def another_task():
    while True:
        print("another_task is running.")
        await asyncio.sleep(1.5)
        if random.random() < 0.1:
            raise Exception("Random failure in another_task.")


async def main():
    manager = DaemonManager()
    manager.add_task("my_task", my_task())
    manager.add_task("another_task", another_task())

    try:
        # Keep the main program running
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        manager.cancel_all_tasks()


if __name__ == "__main__":
    asyncio.run(main())
