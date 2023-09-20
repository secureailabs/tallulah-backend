import abc
from typing import Callable

from aio_pika import DeliveryMode, Message, connect
from aio_pika.abc import AbstractIncomingMessage


class MessageQueueType(abc.ABC):
    @abc.abstractmethod
    def connect(self):
        raise NotImplementedError

    @abc.abstractmethod
    def push_message(self, message):
        raise NotImplementedError

    @abc.abstractmethod
    def consume_messages(self, on_message: Callable):
        raise NotImplementedError

    @abc.abstractmethod
    def disconnect(self):
        raise NotImplementedError


class RabbitMQProducerConumer(MessageQueueType):
    def __init__(self, url="amqp://guest:guest@localhost/", queue_name="hello"):
        self.url = url
        self.queue_name = queue_name

    async def connect(self):
        self.connection = await connect(self.url)
        self.channel = await self.connection.channel()
        self.queue = await self.channel.declare_queue(self.queue_name)

    async def push_message(self, message: str):
        await self.channel.default_exchange.publish(
            Message(message.encode()),
            routing_key=self.queue.name,
        )

    async def consume_messages(self):
        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    print(message.body)

    async def disconnect(self):
        await self.connection.close()


class RabbitMQWorkQueue(MessageQueueType):
    def __init__(self, url="amqp://guest:guest@localhost/", queue_name="task_queue"):
        self.url = url
        self.queue_name = queue_name
        self.is_initialized = False

    async def connect(self):
        self.connection = await connect(self.url)
        self.channel = await self.connection.channel()
        self.queue = await self.channel.declare_queue(self.queue_name, durable=True)
        self.is_initialized = True

    async def push_message(self, message: str):
        if not self.is_initialized:
            raise Exception("Not initialized")

        await self.channel.default_exchange.publish(
            Message(message.encode(), delivery_mode=DeliveryMode.PERSISTENT),
            routing_key=self.queue.name,
        )

    async def consume_messages(self, on_message: Callable):
        if not self.is_initialized:
            raise Exception("Not initialized")

        await self.channel.set_qos(prefetch_count=1)

        await self.queue.consume(on_message)

        print(" [*] Waiting for messages. To exit press CTRL+C")
        await asyncio.Future()

    async def disconnect(self):
        if not self.is_initialized:
            raise Exception("Not initialized")

        await self.connection.close()


class MessageQueueClient:
    def __init__(self, client: MessageQueueType) -> None:
        self.client = client

    async def connect(self):
        await self.client.connect()

    async def push_message(self, message: str):
        await self.client.push_message(message)

    async def consume_messages(self, on_message: Callable):
        await self.client.consume_messages(on_message)

    async def disconnect(self):
        await self.client.disconnect()


async def on_message(message: AbstractIncomingMessage) -> None:
    async with message.process(ignore_processed=True):
        await asyncio.sleep(message.body.count(b"."))
        print(f"     Message body is: {message.body!r}")


async def main():
    # mq = RabbitMQProducerConumer()
    # await mq.connect()
    # await mq.push_message("Hello World!")
    # await mq.consume_messages()
    # await mq.disconnect()

    mq = MessageQueueClient(RabbitMQWorkQueue())
    await mq.connect()
    await mq.push_message("Hello World! Work Queue 1")
    await mq.push_message("Hello World! Work Queue 2")
    await mq.consume_messages(on_message)
    await mq.disconnect()


import asyncio

if __name__ == "__main__":
    asyncio.run(main())
