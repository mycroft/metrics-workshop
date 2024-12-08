import json
import pika

from prometheus_client import Counter, Histogram
from utils.latency import simulate_latency

MQ_PUBLISH_COUNTER = Counter("mq_publish_total", "Total number of messages published", ["queue"])
MQ_PUBLISH_LATENCY = Histogram("mq_publish_latency", "Time spent processing basic_publish", ["queue"])

class MessageProducer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters("localhost")
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue="task_queue", durable=True)

    @MQ_PUBLISH_LATENCY.labels('task_queue').time()
    def send_message(self, message):
        MQ_PUBLISH_COUNTER.labels('task_queue').inc()
        simulate_latency()

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
