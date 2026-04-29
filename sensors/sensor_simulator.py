"""
Aurelius Health Clinic — Sensor Simulator
Generates realistic patient vital signs and clinical environment data.
Includes circadian rhythm, activity patterns, anomaly injection, and
condition-specific baselines for different patient profiles.
"""

import random
import math
from datetime import datetime, timedelta
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SIMULATION


class SensorSimulator:
    """Generates simulated IoT sensor data for both domains."""

    def __init__(self):
        self.patients = SIMULATION["patients"]
        self.rooms = SIMULATION["rooms"]
        self.anomaly_prob = SIMULATION["anomaly_probability"]

    def generate_patient_reading(self, patient, sim_hour, anomaly=False):
        """Generate a single patient's vital signs with realistic variation."""
        # Circadian rhythm (body functions vary throughout the day)
        circadian = math.sin((sim_hour - 6) * math.pi / 12) * 0.5

        # Activity simulation (more active during daytime)
        active_prob = 0.6 if 8 <= sim_hour <= 20 else 0.1
        activity_bump = random.uniform(5, 15) if random.random() < active_prob else 0
        anomaly_bump = random.uniform(10, 25) if anomaly else 0

        hr = round(patient["hr_base"] + random.gauss(0, 3) + circadian * 5
                    + activity_bump + anomaly_bump * 0.5)
        hr = max(40, min(180, hr))

        spo2 = round(patient["spo2_base"] + random.gauss(0, 0.5)
                      - (anomaly_bump * 0.3 if anomaly else 0), 1)
        spo2 = max(80, min(100, spo2))

        bp = round(patient["bp_base"] + random.gauss(0, 5) + circadian * 3
                    + activity_bump * 0.8 + anomaly_bump * 0.7)
        bp = max(70, min(200, bp))

        # Glucose spikes after meals (7-9am, 12-2pm)
        meal_bump = 15 if (7 <= sim_hour <= 9 or 12 <= sim_hour <= 14) else 0
        gl = round(patient["gl_base"] + random.gauss(0, 5) + meal_bump
                    + anomaly_bump * 0.5)
        gl = max(50, min(250, gl))

        temp = round(patient["temp_base"] + random.gauss(0, 0.15) + circadian * 0.2
                      + (anomaly_bump * 0.08 if anomaly else 0), 1)
        temp = max(35.0, min(41.0, temp))

        motion = 1 if random.random() < active_prob else 0

        return {
            "patient_id": patient["id"],
            "heart_rate": hr,
            "spo2": spo2,
            "blood_pressure": bp,
            "glucose": gl,
            "body_temp": temp,
            "motion": motion,
            "is_anomaly": 1 if anomaly else 0,
        }

    def generate_environment_reading(self, room, sim_hour, anomaly=False):
        """Generate clinical environment readings with occupancy-based variation."""
        # Occupancy pattern (busier during clinic hours)
        if 9 <= sim_hour <= 17 and room["type"] == "waiting":
            occupancy = random.randint(2, 8)
        elif 8 <= sim_hour <= 18:
            occupancy = random.randint(0, 3)
        else:
            occupancy = 0

        # External temperature influence
        ext_temp = math.sin((sim_hour - 4) * math.pi / 12) * 2

        rt = round(room["temp_base"] + ext_temp + occupancy * 0.3
                    + random.gauss(0, 0.5) + (5 if anomaly else 0), 1)
        rt = max(15, min(35, rt))

        hum = round(room["hum_base"] + occupancy * 1.5 + random.gauss(0, 2)
                     + (15 if anomaly else 0), 1)
        hum = max(20, min(80, hum))

        co2 = round(400 + occupancy * 80 + random.gauss(0, 30)
                     + (500 if anomaly else 0))
        co2 = max(350, min(3000, co2))

        pm25 = round(8 + occupancy * 2 + random.gauss(0, 3)
                      + (40 if anomaly else 0), 1)
        pm25 = max(0, min(200, pm25))

        if 8 <= sim_hour <= 18 and occupancy > 0:
            light = round(random.uniform(400, 700))
        else:
            light = round(random.uniform(10, 50))

        noise = round(35 + occupancy * 4 + random.gauss(0, 3)
                       + (20 if anomaly else 0), 1)
        noise = max(25, min(95, noise))

        # Medication fridge (should stay 2-8°C)
        fridge = round(5.0 + random.gauss(0, 0.5) + (4 if anomaly else 0), 1)
        fridge = max(0, min(15, fridge))

        return {
            "room_id": room["id"],
            "room_type": room["type"],
            "room_temp": rt,
            "humidity": hum,
            "co2": co2,
            "pm25": pm25,
            "light": light,
            "noise": noise,
            "med_fridge_temp": fridge,
            "is_anomaly": 1 if anomaly else 0,
        }

    def run(self, duration_hours=24, interval_seconds=60):
        """Generator that yields readings over the simulation period."""
        total_steps = int((duration_hours * 3600) / interval_seconds)

        for step in range(total_steps):
            sim_hour = (step * interval_seconds / 3600) % 24
            timestamp = datetime.now().isoformat()
            anomaly = random.random() < self.anomaly_prob

            # Generate patient readings
            patient_readings = []
            for p in self.patients:
                reading = self.generate_patient_reading(p, sim_hour, anomaly)
                reading["timestamp"] = timestamp
                patient_readings.append(reading)

            # Generate environment readings
            env_readings = []
            for r in self.rooms:
                reading = self.generate_environment_reading(r, sim_hour, anomaly)
                reading["timestamp"] = timestamp
                env_readings.append(reading)

            yield step, sim_hour, patient_readings, env_readings
