from app.utils.message_queue import InMemoryProducerConsumer, MessageQueueTypes, TaskMessages


async def on_generate_structured_data():
    print("Generating structured data")
    pass


async def generate_structured_data_consumer():
    task_queue = InMemoryProducerConsumer(queue_name=MessageQueueTypes.TASK_QUEUE, connection_string="")
    await task_queue.connect()
    await task_queue.consume_messages(on_generate_structured_data)
