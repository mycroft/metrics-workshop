#!/usr/bin/env python3

from flask import Flask, request, jsonify
from utils.producer import MessageProducer

app = Flask(__name__)

@app.route('/hello', methods=['GET'])
def hello():
    queue = MessageProducer()
    queue.send_message('hello')

    return "Hello, World!"

@app.route('/fruit', methods=['POST'])
def fruit():
    data = request.get_json()
    if not data or 'fruit' not in data:
        return jsonify({"error": "No fruit provided"}), 400
    
    fruit = data['fruit'].lower()
    queue = MessageProducer()
    queue.send_message(fruit)
    if fruit == 'apples':
        return jsonify({"message": "You sent apples!"})
    elif fruit == 'oranges':
        return jsonify({"message": "You sent oranges!"})
    else:
        return jsonify({"error": "Invalid fruit"}), 400

if __name__ == '__main__':
    app.run(debug=True)