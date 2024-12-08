#!/usr/bin/env python3

import random
from time import sleep
from flask import Flask, request, jsonify
from model import fruit
from utils.cache import get_cache, get_cache_key
from utils.db import Database
from utils.latency import simulate_latency
from utils.producer import MessageProducer

from prometheus_client import make_wsgi_app, Counter, Gauge, Histogram
from werkzeug.middleware.dispatcher import DispatcherMiddleware

HELLO_COUNTER = Counter('hello_total', 'Total number of hello requests')
ALL_FRUITS_GAUGE = Gauge('all_fruits', 'Total number of recent fruits in the database')
RECENT_FRUITS_GAUGE = Gauge('recent_fruits', 'Total number of recent fruits in the database', ['fruit'])
REQUEST_COUNTER = Counter('http_requests_total', 'Total number of HTTP requests', ['method', 'endpoint'])
ERRORS_COUNTER = Counter('errors_total', 'Total number of errors', ['method', 'endpoint', 'error'])
HTTP_LATENCY_HISTOGRAM = Histogram('http_latency', 'Histogram of HTTP latencies', ['method', 'endpoint'])
QUANTITY_COUNTER = Counter('quantity_total', 'Total number of quantity', ['fruit'])

app = Flask(__name__)
# Add prometheus wsgi middleware to route /metrics requests
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

@app.route('/hello', methods=['GET'])
@HTTP_LATENCY_HISTOGRAM.labels('GET', 'hello').time()
def hello():
    # Adding random latency
    simulate_latency()

    HELLO_COUNTER.inc(1)
    REQUEST_COUNTER.labels('GET', 'hello').inc(1)

    queue = MessageProducer()
    queue.send_message('hello')

    return "Hello, World!"


@app.route('/fruit', methods=['POST'])
@HTTP_LATENCY_HISTOGRAM.labels('POST', '/fruit').time()
def fruit_post():
    # Adding random latency
    simulate_latency()

    REQUEST_COUNTER.labels('POST', '/fruit').inc(1)

    data = request.get_json()
    if not data or 'fruit' not in data or 'quantity' not in data:
        ERRORS_COUNTER.labels('POST', '/fruit', 'MissingValueError').inc(1)
        return jsonify({"error": "No fruit or quantity provided"}), 400

    QUANTITY_COUNTER.labels(data['fruit']).inc(data['quantity'])

    try:
        fruit_name = data['fruit'].lower()
        quantity = int(data['quantity'])

        queue = MessageProducer()
        queue.send_message({'fruit': fruit_name, 'quantity': quantity})

        if fruit_name not in fruit.get_possible_fruits():
            ERRORS_COUNTER.labels('POST', '/fruit', 'FruitValueError').inc(1)
            return jsonify({"error": "Invalid fruit"}), 400
        elif quantity < 1:
            ERRORS_COUNTER.labels('POST', '/fruit', 'QuantityValueError').inc(1)
            return jsonify({"error": "Invalid quantity"}), 400
        else:
            return jsonify({"message": f"You sent {quantity} {fruit_name}!"})
    except ValueError:
        ERRORS_COUNTER.labels('POST', '/fruit', 'ValueError').inc(1)
        return jsonify({"error": "Invalid quantity"}), 400
    except Exception as e:
        ERRORS_COUNTER.labels('POST', '/fruit', 'OtherError').inc(1)
        return jsonify({"error": str(e)}), 500


@app.route('/fruit', methods=['GET'])
@HTTP_LATENCY_HISTOGRAM.labels('GET', '/fruit').time()
def fruit_get():
    fruit_name = request.args.get('name', 'all')
    
    # adding random latency
    simulate_latency()

    REQUEST_COUNTER.labels('GET', '/fruit').inc(1)

    # check if cache has the value
    cache = get_cache()
    cache_key = get_cache_key(fruit_name)

    try:
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            app.logger.info(f"Cache hit for key {cache_key}")
            return jsonify({"fruit": fruit_name, "total_quantity": int(cached_value)})
        else:
            app.logger.info(f"Cache miss for key {cache_key}")
    except Exception as e:
        app.logger.error(f"Error accessing cache: {str(e)}")
        ERRORS_COUNTER.labels('GET', '/fruit', 'CacheError').inc(1)

    db = Database()
    db.initialize(create_schema=False)

    try:
        with db.session() as session:
            if fruit_name == 'all':
                total_quantity = fruit.get_all_fruits(session)
                ALL_FRUITS_GAUGE.set(total_quantity)
            else:
                total_quantity = fruit.get_recent_quantity(session, fruit_name)
                RECENT_FRUITS_GAUGE.labels(fruit_name).set(total_quantity)

        total_quantity = total_quantity if total_quantity is not None else 0

        # save the value in cache with a 10 seconds ttl
        cache.set(cache_key, total_quantity, ex=5)

        return jsonify({"fruit": fruit_name, "total_quantity": total_quantity})
    except Exception as e:
        ERRORS_COUNTER.labels('GET', '/fruit', 'OtherError').inc(1)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
