from abc import ABC, abstractmethod
from collections import deque
from enum import Enum
from typing import Callable

from aio_pika import DeliveryMode, Message, connect
from aio_pika.abc import AbstractIncomingMessage


class MessageQueueTypes(Enum):
    FORM_DATA_METADATA_GENERATION = "FORM_DATA_METADATA_GENERATION"
    EMAIL_QUEUE = "email_queue"


class TaskMessages(Enum):
    GENERATE_STRUCTURED_DATA = "GENERATE_STRUCTURED_DATA"


class AbstractMessageQueue(ABC):
    @abstractmethod
    def connect(self):
        raise NotImplementedError

    @abstractmethod
    def push_message(self, message):
        raise NotImplementedError

    @abstractmethod
    def consume_messages(self, on_message: Callable):
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        raise NotImplementedError


# This is a simple in-memory producer-consumer class when we don't want to use RabbitMQ
# Since the class is derived from AbstractMessageQueue, we can use this class in place of RabbitMQ
# And later on, we can replace this class with Rabbit MQ without changing the code
class InMemoryProducerConsumer(AbstractMessageQueue):
    _queues = {}

    # Make a singleton class for all the unique queues
    def __new__(cls, queue_name: MessageQueueTypes, connection_string: str):
        if queue_name not in cls._queues:
            cls._queues[queue_name] = super(InMemoryProducerConsumer, cls).__new__(cls)
        return cls._queues[queue_name]

    def __init__(self, queue_name: MessageQueueTypes, connection_string: str):
        self.queue_name = queue_name

    async def connect(self):
        if not hasattr(self, "queue"):
            self.queue = deque()

    async def push_message(self, message: str):
        self.queue.append(message)

    async def consume_messages(self, on_message: Callable):
        # This will be an infinite loop will wake up every 10 seconds to check for new messages
        while True:
            print("Checking for messages in ", self.queue_name)
            if self.queue:
                message = self.queue.popleft()
                await on_message(message)
            await asyncio.sleep(10)

    async def disconnect(self):
        pass


class RabbitMQProducerConumer(AbstractMessageQueue):
    _queues = {}

    # Make a singleton class for all the unique queues
    def __new__(cls, queue_name: MessageQueueTypes, connection_string: str):
        if queue_name not in cls._queues:
            cls._queues[queue_name] = super(RabbitMQProducerConumer, cls).__new__(cls)
        return cls._queues[queue_name]

    def __init__(self, queue_name: MessageQueueTypes, connection_string: str):
        if not hasattr(self, "queue_name"):
            self.queue_name = queue_name
            self.is_connected = False

        if not hasattr(self, "url"):
            self.url = connection_string
        elif self.url != connection_string:
            raise ValueError("Cannot change the url of the queue")

    async def connect(self):
        if not self.is_connected:
            self.connection = await connect(self.url, loop=asyncio.get_event_loop())
            self.channel = await self.connection.channel()
            self.queue = await self.channel.declare_queue(self.queue_name.value, durable=True)
            self.is_connected = True

    async def push_message(self, message: str):
        if not self.is_connected:
            raise Exception("Not connected")
        await self.channel.default_exchange.publish(
            Message(message.encode(), delivery_mode=DeliveryMode.PERSISTENT),
            routing_key=self.queue.name,
        )

    async def consume_messages(self, on_message: Callable):
        if not self.is_connected:
            raise Exception("Not connected")

        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                await on_message(message)

    async def disconnect(self):
        if not self.is_connected:
            raise Exception("Not connected")
        await self.connection.close()


class RabbitMQWorkQueue(AbstractMessageQueue):
    _queues = {}

    # Make a singleton class for all the unique queues
    def __new__(cls, queue_name: MessageQueueTypes, connection_string: str):
        if queue_name not in cls._queues:
            cls._queues[queue_name] = super(RabbitMQWorkQueue, cls).__new__(cls)
        return cls._queues[queue_name]

    def __init__(self, queue_name: MessageQueueTypes, connection_string: str):
        if not hasattr(self, "queue_name"):
            self.queue_name = queue_name
            self.is_connected = False

        if not hasattr(self, "url"):
            self.url = connection_string
        elif self.url != connection_string:
            raise ValueError("Cannot change the connection url of the queue")

    async def connect(self):
        if not self.is_connected:
            self.connection = await connect(self.url, loop=asyncio.get_running_loop())
            self.channel = await self.connection.channel()
            self.queue = await self.channel.declare_queue(self.queue_name.value, durable=True)
            self.is_connected = True

    async def push_message(self, message: str):
        if not self.is_connected:
            raise Exception("Not connected")

        await self.channel.default_exchange.publish(
            Message(message.encode(), delivery_mode=DeliveryMode.PERSISTENT),
            routing_key=self.queue.name,
        )

    async def consume_messages(self, on_message: Callable):
        if not self.is_connected:
            raise Exception("Not connected")

        await self.channel.set_qos(prefetch_count=1)

        await self.queue.consume(on_message)

        print(" [*] Waiting for messages. To exit press CTRL+C")
        await asyncio.Future()

    async def disconnect(self):
        if not self.is_connected:
            raise Exception("Not connected")

        await self.connection.close()


async def main():
    # mq = RabbitMQProducerConumer()
    # await mq.connect()
    # await mq.push_message("Hello World!")
    # await mq.consume_messages()
    # await mq.disconnect()
    async def on_message(message: AbstractIncomingMessage) -> None:
        async with message.process(ignore_processed=True):
            await asyncio.sleep(message.body.count(b"."))
            print(f"     Message body is: {message.body!r}")

    mq = RabbitMQWorkQueue(MessageQueueTypes.FORM_DATA_METADATA_GENERATION, "amqp://guest:guest@localhost/")
    await mq.connect()
    await mq.push_message("Hello World! Work Queue 1")
    await mq.push_message("Hello World! Work Queue 2")
    await mq.consume_messages(on_message)
    await mq.disconnect()


import asyncio

if __name__ == "__main__":
    asyncio.run(main())
