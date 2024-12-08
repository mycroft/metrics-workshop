#!/usr/bin/env python3

import json
import random
import threading
from time import sleep

from utils.cache import get_cache, get_cache_key
from utils.consumer import MessageConsumer
from utils.latency import simulate_latency
from utils.producer import MessageProducer
from utils.random import get_random_time, get_random_quantity

from utils.db import Database

from prometheus_client import start_http_server, Counter, Gauge, Histogram

WORKER_RUN_COUNTER = Counter("worker_total_run", "Total number of workers execution", ["worker_id"])
GENERATOR_RUN_COUNTER = Gauge("generator_total_run", "Total number of generators execution", ["generator_id"])
WORKER_BUSY_GAUGE = Gauge("worker_busy", "Number of workers busy")

DATABASE_INSERT_QUERIES_COUNTER = Counter("database_insert_queries", "Number of insert queries to the database")
DATABASE_INSERT_LATENCY_HISTOGRAM = Histogram("database_insert_latency", "Latency of insert queries to the database")
CACHE_DELETE_LATENCY_HISTOGRAM = Histogram("cache_delete_latency", "Latency of cache delete operations")
MQ_READ_LATENCY_HISTOGRAM = Histogram("mq_read_latency", "Latency of reading messages from the message queue")

JOBS_COUNTER = Counter("jobs_total", "Total number of jobs")

from model import model, fruit

class Worker(threading.Thread):
    """Worker class"""

    def __init__(self, worker_id):
        """Worker constructor"""
        super().__init__()
        print(f"Worker created {worker_id}")
        self.stopped = False
        self.name = worker_id

        self.consumer = MessageConsumer()
        self.producer = MessageProducer()

    def run(self):
        print("Worker running")

        db = Database()
        db.initialize(create_schema=False)

        while not self.stopped:
            WORKER_RUN_COUNTER.labels(self.name).inc()
            WORKER_BUSY_GAUGE.inc(1)
            try:
                with MQ_READ_LATENCY_HISTOGRAM.time():
                    message = self.consumer.consume_one()
                    if message is None:
                        sleep(1)
                        continue

                JOBS_COUNTER.inc()

                print(f"Worker working {self.name} with message {message}")

                if message == "hello":
                    sleep(get_random_time())
                else:
                    # Message is likely a json with fruit & quantity
                    # if not, we consider it as a string and use a random quantity
                    fruit_name = 'unknown'
                    quantity = get_random_quantity()

                    simulate_latency()

                    if isinstance(message, dict):
                        fruit_name = message.get('fruit', 'unknown')
                        quantity = message.get('quantity', get_random_quantity())

                    with DATABASE_INSERT_LATENCY_HISTOGRAM.time():
                        with db.session() as session:
                            session.add(fruit.Fruit(name=fruit_name, quantity=quantity))
                            session.commit()

                    # Drop cache
                    with CACHE_DELETE_LATENCY_HISTOGRAM.time():
                        cache = get_cache()
                        cache_key = get_cache_key(fruit_name)
                        cache.delete(cache_key)

            except TimeoutError:
                pass
            except Exception as e:
                print(str(e))
            finally:
                WORKER_BUSY_GAUGE.dec()

        db.dispose()

        self.consumer.close()

    def stop(self):
        print(f"Worker stopped {self.name}")
        self.stopped = True

    def __str__(self) -> str:
        return "Worker"
    
class Generator(threading.Thread):
    def __init__(self, worker_id):
        super().__init__()
        print(f"Generator created {worker_id}")
        self.stopped = False
        self.name = worker_id

        self.consumer = MessageConsumer()
        self.producer = MessageProducer()

    def run(self):
        print("Generator running")
        while not self.stopped:
            GENERATOR_RUN_COUNTER.labels(self.name).inc()
            try:
                message = {'fruit': 'oranges', 'quantity': random.randint(1, 10)}
                self.producer.send_message(message)

                sleep(get_random_time())
            except Exception as e:
                print(e)

            GENERATOR_RUN_COUNTER.labels(self.name).dec()

    def stop(self):
        print(f"Generator stopped {self.name}")
        self.stopped = True

    def __str__(self) -> str:
        return "Generator"

class Engine:
    def main(self):
        print("Worker started")

        workers = []

        for i in range(0, 20):
            worker = Worker(i)
            workers.append(worker)

        for i in range(0, 1):
            generator = Generator(i)
            workers.append(generator)

        for worker in workers:
            worker.start()

        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            print("Stopping workers")
            for worker in workers:
                worker.stop()

        for worker in workers:
            worker.join()

    def __str__(self) -> str:
        return "Engine"

def start():
    # Create the database, if required.
    db = Database()
    db.initialize(create_schema=True)

    app = Engine()
    start_http_server(5001)
    app.main()


if __name__ == "__main__":
    start()
