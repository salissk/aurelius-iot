"""
Aurelius Health Clinic — Main Entry Point
IoT System for Remote Patient Monitoring and Clinical Environment Monitoring.

Usage:
  Simulate 24h of data:   python main.py --simulate
  Live MQTT receiver:     python main.py --live
  Run tests:              python -m pytest tests/ -v

CPS6008 Internet of Things — St Mary's University
"""

import sys
import os

from config import SIMULATION, DB_PATH
from storage.database import Database
from sensors.sensor_simulator import SensorSimulator
from processing.edge_processor import EdgeProcessor
from security.auth import SecurityManager


def run_simulation(hours=24, interval=60):
    """Run the IoT simulation generating realistic data for both domains."""

    print("\n" + "=" * 55)
    print("  AURELIUS HEALTH CLINIC — IoT System")
    print("  Domain 1: Remote Patient Monitoring")
    print("  Domain 2: Clinical Environment Monitoring")
    print("=" * 55)

    # Initialise modules
    db = Database()
    db.clear_database()  # Fresh start
    processor = EdgeProcessor(db)
    security = SecurityManager(db)
    simulator = SensorSimulator()

    print("\n  Simulating {} hours of data (interval: {}s)...".format(hours, interval))
    print("  Patients: {}".format(len(SIMULATION["patients"])))
    print("  Rooms: {}".format(len(SIMULATION["rooms"])))
    print("-" * 55)

    reading_count = 0
    validated_count = 0
    rejected_count = 0

    for step, sim_hour, patient_readings, env_readings in simulator.run(hours, interval):
        reading_count += 1

        # Process patient data with security validation
        for reading in patient_readings:
            valid, errors = security.validate_patient_data(reading)
            if valid:
                db.save_patient_reading(reading)
                processor.process_patient(reading)
                validated_count += 1
            else:
                security.log_security_event("DATA_REJECTED",
                    "Patient data failed validation: {}".format(errors),
                    severity="WARNING")
                rejected_count += 1

        # Process environment data with security validation
        for reading in env_readings:
            valid, errors = security.validate_environment_data(reading)
            if valid:
                db.save_environment_reading(reading)
                processor.process_environment(reading)
                validated_count += 1
            else:
                security.log_security_event("DATA_REJECTED",
                    "Environment data failed validation: {}".format(errors),
                    severity="WARNING")
                rejected_count += 1

        # Progress update
        if reading_count % 100 == 0:
            hour_display = int(sim_hour)
            print("  [Hour {:02d}:00] Cycles: {} | Alerts: {}".format(
                hour_display, reading_count, processor.alert_count))

    # Final summary
    print("\n" + "=" * 55)
    print("  SIMULATION COMPLETE")
    print("  Total cycles:        {}".format(reading_count))
    print("  Validated readings:  {}".format(validated_count))
    print("  Rejected readings:   {}".format(rejected_count))
    print("  Alerts generated:    {}".format(processor.alert_count))
    print("  Database:            {}".format(DB_PATH))
    print("=" * 55)


def run_live():
    """Run the MQTT receiver for live Wokwi data."""
    from communication.mqtt_handler import MQTTHandler

    db = Database()
    processor = EdgeProcessor(db)
    mqtt = MQTTHandler(db, processor)

    print("\n" + "=" * 55)
    print("  AURELIUS HEALTH CLINIC — Live MQTT Receiver")
    print("  Waiting for Wokwi ESP32 data...")
    print("=" * 55)

    mqtt.start()


if __name__ == "__main__":
    if "--simulate" in sys.argv:
        hours = 24
        interval = 60
        for arg in sys.argv:
            if arg.startswith("--hours="):
                hours = int(arg.split("=")[1])
            if arg.startswith("--interval="):
                interval = int(arg.split("=")[1])
        run_simulation(hours, interval)

    elif "--live" in sys.argv:
        run_live()

    else:
        print("Usage:")
        print("  python main.py --simulate          Run 24h simulation")
        print("  python main.py --simulate --hours=48  Custom duration")
        print("  python main.py --live               Listen for Wokwi MQTT data")
        print("  streamlit run dashboard/app.py      Launch dashboard")
        print("  python -m pytest tests/ -v          Run tests")
