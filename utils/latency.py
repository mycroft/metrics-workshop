import math
import time

def simulate_latency():
    current_time = time.time()
    latency = (math.cos(current_time) + 1) * 0.5
    time.sleep(latency)
