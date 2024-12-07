import json
import pika

class MessageProducer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters("localhost")
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue="task_queue", durable=True)

    def send_message(self, message):
        self.channel.basic_publish(
            exchange="",
            routing_key="task_queue",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ),
        )

    def close(self):
        self.connection.close()
