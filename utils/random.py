import random

def get_random_time():
    """returns a random time between 100ms and 500ms"""
    return random.randint(1, 5) * 0.1

def get_random_quantity():
    """returns a random quantity between 1 and 10"""
    return random.randint(1, 10)