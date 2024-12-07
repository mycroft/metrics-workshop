import json
from pika import ConnectionParameters, BlockingConnection

class MessageConsumer:
    def __init__(self):
        self.connection = BlockingConnection(ConnectionParameters("localhost"))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue="task_queue", durable=True)

    def callback(self, ch, method, _properties, body):
        print(f"Received {body}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def consume(self, callback=None):
        if callback is None:
            callback = self.callback
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue="task_queue", on_message_callback=callback
        )
        self.channel.start_consuming()

    def consume_one(self):
        method, _props, body = next(
            self.channel.consume(
                queue="task_queue", auto_ack=False, inactivity_timeout=1
            )
        )

        if method:
            message = json.loads(body)
            self.channel.basic_ack(method.delivery_tag)
            return message

        return None

    def close(self):
        self.connection.close()
