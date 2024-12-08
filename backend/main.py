#!/usr/bin/env python3

import json
import random
import threading
from time import sleep

from utils.cache import get_cache, get_cache_key
from utils.consumer import MessageConsumer
from utils.producer import MessageProducer
from utils.random import get_random_time, get_random_quantity
from utils.db import create_schema, create_db_engine, get_session

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

        db = create_db_engine()

        while not self.stopped:
            try:
                message = self.consumer.consume_one()
                if message is None:
                    continue

                print(f"Worker working {self.name} with message {message}")

                if message == "hello":
                    sleep(get_random_time())
                else:
                    # Message is likely a json with fruit & quantity
                    # if not, we consider it as a string and use a random quantity
                    fruit_name = 'unknown'
                    quantity = get_random_quantity()

                    if isinstance(message, dict):
                        fruit_name = message.get('fruit', 'unknown')
                        quantity = message.get('quantity', get_random_quantity())

                    # Save message to database
                    session = get_session(db)
                    session.add(fruit.Fruit(name=fruit_name, quantity=quantity))
                    session.commit()
                    session.close()

                    # Drop cache
                    cache = get_cache()
                    cache_key = get_cache_key(fruit_name)
                    cache.delete(cache_key)

            except TimeoutError:
                pass
            except Exception as e:
                print(str(e))

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
            try:
                message = {'fruit': 'oranges', 'quantity': random.randint(1, 10)}
                self.producer.send_message(message)
            except Exception as e:
                print(e)

    def stop(self):
        print(f"Generator stopped {self.name}")
        self.stopped = True

    def __str__(self) -> str:
        return "Generator"

class Engine:
    def main(self):
        # Create schema, if not already done
        db_engine = create_db_engine()
        create_schema(model.get_base(), db_engine)
        db_engine.dispose()

        print("Worker started")

        workers = []

        for i in range(0, 20):
            worker = Worker(i)
            workers.append(worker)

        for i in range(0, 5):
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
    app = Engine()
    app.main()


if __name__ == "__main__":
    start()
