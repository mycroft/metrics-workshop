import json
from pika import ConnectionParameters, BlockingConnection
from prometheus_client import Counter, Histogram
from utils.latency import simulate_latency

MQ_CONSUME_COUNTER = Counter("mq_consume_total", "Total number of messages consumed", ["queue"])
MQ_CONSUME_LATENCY = Histogram("mq_consume_latency", "Time spent processing consume", ["queue"])
MQ_ACK_LATENCY = Histogram("mq_ack_latency", "Time spent processing basic_ack", ["queue"])

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
        MQ_CONSUME_COUNTER.labels('task_queue').inc()
        simulate_latency()

        with MQ_CONSUME_LATENCY.labels('task_queue').time():
            method, _props, body = next(
                self.channel.consume(
                    queue="task_queue", auto_ack=False, inactivity_timeout=1
                )
            )

        if method:
            message = json.loads(body)
            with MQ_ACK_LATENCY.labels('task_queue').time():
                self.channel.basic_ack(method.delivery_tag)
            return message

        return None

    def close(self):
        self.connection.close()
