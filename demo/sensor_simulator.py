"""
Sensor Simulator - Generates realistic PLC data for testing
"""
import random
import math
import time

class TemperatureSensorSimulator:
    def __init__(self, setpoint=65.5, noise_amplitude=1.5, drift_speed=0.05):
        self.setpoint = setpoint
        self.noise_amplitude = noise_amplitude
        self.drift_speed = drift_speed
        self.start_time = time.time()
    
    def read(self):
        elapsed = time.time() - self.start_time
        drift = math.sin(elapsed * self.drift_speed) * 2.0
        noise = random.gauss(0, self.noise_amplitude * 0.3)
        cycle = math.sin(elapsed * 0.1) * 0.5
        value = self.setpoint + drift + noise + cycle
        return round(max(-50.0, min(150.0, value)), 2)

class SystemMetricsSimulator:
    def __init__(self):
        self.start_time = time.time()
    
    def get_metrics(self):
        return {
            'cpu': max(0, min(100, 12 + random.uniform(-3, 5))),
            'memory': max(0, min(100, 45 + random.uniform(-2, 2))),
            'net_up': max(0, 1.2 + random.uniform(-0.5, 0.8)),
            'net_down': max(0, 0.8 + random.uniform(-0.3, 0.5)),
            'uptime_seconds': int(time.time() - self.start_time),
        }