#!/usr/bin/env python3

# This program is the main entry point for the traffic service.
# It runs random traffic against the frontend service.

import random
import sys
import threading
from time import sleep

import requests

from model import fruit

def run_get_hello():
    r = requests.get('http://localhost:5000/hello')

def run_get_fruit():
    fruit_name = random.choice(fruit.get_possible_fruits())
    r = requests.get(f'http://localhost:5000/fruit?name={fruit_name}')
    print(r.text)

def run_post_fruit():
    fruit_name = random.choice(fruit.get_possible_fruits())
    quantity = random.randint(1, 10)
    r = requests.post('http://localhost:5000/fruit', json={"fruit": fruit_name, "quantity": quantity})
    print(r.text)

class TrafficWorker(threading.Thread):
    def __init__(self, worker_id):
        super().__init__()
        self.stopped = False
        self.name = worker_id

    def run(self):
        while not self.stopped:
            # Simulate a request to the frontend service, choosing between GET /hello, GET /fruit, POST /fruit
            request_type = random.choice(["GET /hello", "GET /fruit", "POST /fruit"])
            if request_type == "GET /hello":
                run_get_hello()
            elif request_type == "GET /fruit":
                run_get_fruit()
            elif request_type == "POST /fruit":
                run_post_fruit()
            
            sleep(random.randint(1, 5)*.1)

    def stop(self):
        self.stopped = True

    def __str__(self) -> str:
        return f"TrafficWorker {self.name}"

class TrafficEngine:
    def main(self, num_threads=10):
        workers = []
        for i in range(num_threads):
            worker = TrafficWorker(i)
            workers.append(worker)

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
        return "TrafficEngine"


if __name__ == "__main__":
    num_threads = 10
    try:
        if len(sys.argv) > 1:
            num_threads = int(sys.argv[1])
    except ValueError:
        print("Invalid number of threads, defaulting to 10")

    app = TrafficEngine()
    app.main(num_threads)
