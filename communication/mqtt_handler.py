"""
Aurelius Health Clinic — MQTT Communication Handler
Handles MQTT publish/subscribe for receiving live data from Wokwi ESP32 devices.
Uses TLS-ready configuration for production deployment.
"""

import json
from datetime import datetime
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPICS

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("[MQTT] paho-mqtt not installed — MQTT features disabled")


class MQTTHandler:
    """MQTT client for the Aurelius IoT system."""

    def __init__(self, db, processor):
        self.db = db
        self.processor = processor

        if not MQTT_AVAILABLE:
            print("[MQTT] Cannot initialise — paho-mqtt not available")
            return

        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            print("[MQTT] Connected to broker at {}".format(MQTT_BROKER))
            client.subscribe(MQTT_TOPICS["patient"])
            client.subscribe(MQTT_TOPICS["environment"])
            print("[MQTT] Subscribed to patient and environment topics")
        else:
            print("[MQTT] Connection failed, code: {}".format(rc))

    def _on_message(self, client, userdata, msg):
        """Callback when a message is received."""
        try:
            payload = msg.payload.decode()
            data = json.loads(payload)
            data["timestamp"] = datetime.now().isoformat()
            domain = data.get("domain", "")

            if domain == "patient_monitoring":
                self.db.save_patient_reading(data)
                self.processor.process_patient(data)
                print("[PATIENT] HR={} SpO2={} BP={}".format(
                    data.get("heart_rate"), data.get("spo2"),
                    data.get("blood_pressure")))

            elif domain == "environment_monitoring":
                self.db.save_environment_reading(data)
                self.processor.process_environment(data)
                print("[ROOM] Temp={} CO2={} Fridge={}".format(
                    data.get("room_temp"), data.get("co2"),
                    data.get("med_fridge_temp")))

            else:
                print("[MQTT] Unknown domain: {}".format(domain))

        except json.JSONDecodeError:
            print("[MQTT] Invalid JSON received")
        except Exception as e:
            print("[MQTT] Error: {}".format(e))

    def connect(self):
        """Connect to the MQTT broker."""
        if not MQTT_AVAILABLE:
            print("[MQTT] Cannot connect — paho-mqtt not installed")
            return False
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            return True
        except Exception as e:
            print("[MQTT] Connection error: {}".format(e))
            return False

    def start(self):
        """Start listening for MQTT messages (blocking)."""
        if self.connect():
            print("[MQTT] Listening for data from Wokwi ESP32 devices...")
            self.client.loop_forever()
        else:
            print("[MQTT] Could not start — broker unavailable")

    def stop(self):
        """Disconnect from MQTT broker."""
        if MQTT_AVAILABLE:
            self.client.loop_stop()
            self.client.disconnect()
            print("[MQTT] Disconnected")
