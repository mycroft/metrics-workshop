#!/usr/bin/env python3

import random
from time import sleep
from flask import Flask, request, jsonify
from model import fruit
from utils.cache import get_cache, get_cache_key
from utils.db import create_db_engine, get_session
from utils.producer import MessageProducer

app = Flask(__name__)

@app.route('/hello', methods=['GET'])
def hello():
    # Adding random latency
    sleep(random.randint(1, 100)*.01)

    queue = MessageProducer()
    queue.send_message('hello')

    return "Hello, World!"


@app.route('/fruit', methods=['POST'])
def fruit_post():
    # Adding random latency
    sleep(random.randint(1, 100)*.01)

    data = request.get_json()
    if not data or 'fruit' not in data or 'quantity' not in data:
        return jsonify({"error": "No fruit or quantity provided"}), 400
    
    try:
        fruit_name = data['fruit'].lower()
        quantity = int(data['quantity'])
        queue = MessageProducer()
        queue.send_message({'fruit': fruit_name, 'quantity': quantity})

        if fruit_name not in fruit.get_possible_fruits():
            return jsonify({"error": "Invalid fruit"}), 400
        elif quantity < 1:
            return jsonify({"error": "Invalid quantity"}), 400
        else:
            return jsonify({"message": f"You sent {quantity} {fruit_name}!"})
    except ValueError:
        return jsonify({"error": "Invalid quantity"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/fruit', methods=['GET'])
def fruit_get():
    # adding random latency
    sleep(random.randint(1, 100)*.01)

    fruit_name = request.args.get('name')
    if not fruit_name:
        return jsonify({"error": "No fruit provided"}), 400
    
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
    
    session = get_session(create_db_engine())
    try:
        total_quantity = fruit.get_total_quantity(session, fruit_name)
        total_quantity = total_quantity if total_quantity is not None else 0

        # save the value in cache with a 10 seconds ttl
        cache.set(cache_key, total_quantity, ex=5)

        return jsonify({"fruit": fruit_name, "total_quantity": total_quantity})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

    return jsonify({"message": "You requested fruits!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
