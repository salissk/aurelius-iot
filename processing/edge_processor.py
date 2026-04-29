"""
Aurelius Health Clinic — Edge Processor
Performs threshold-based alert detection on patient and environment data.
Mirrors the edge processing logic running on the ESP32 devices in Wokwi.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PATIENT_THRESHOLDS, ENVIRONMENT_THRESHOLDS


class EdgeProcessor:
    """Processes sensor data against clinical thresholds and generates alerts."""

    def __init__(self, db):
        self.db = db
        self.alert_count = 0

    def process_patient(self, data):
        """Check patient vitals against NHS clinical thresholds."""
        t = PATIENT_THRESHOLDS
        pid = data.get("patient_id", "PAT-001")

        # Heart rate
        hr = data.get("heart_rate", 75)
        if hr > t["heart_rate"]["critical_high"]:
            self._alert("CRITICAL", pid, "heart_rate", hr,
                        "Heart rate CRITICAL: {} BPM".format(hr))
        elif hr > t["heart_rate"]["high"] or hr < t["heart_rate"]["low"]:
            self._alert("WARNING", pid, "heart_rate", hr,
                        "Heart rate abnormal: {} BPM".format(hr))

        # Blood oxygen (SpO2)
        sp = data.get("spo2", 98)
        if sp < t["spo2"]["critical_low"]:
            self._alert("CRITICAL", pid, "spo2", sp,
                        "SpO2 CRITICAL: {}%".format(sp))
        elif sp < t["spo2"]["low"]:
            self._alert("WARNING", pid, "spo2", sp,
                        "SpO2 low: {}%".format(sp))

        # Blood pressure (systolic)
        bp = data.get("blood_pressure", 120)
        if bp > t["blood_pressure"]["critical_high"]:
            self._alert("CRITICAL", pid, "blood_pressure", bp,
                        "BP CRITICAL: {} mmHg".format(bp))
        elif bp > t["blood_pressure"]["high"]:
            self._alert("WARNING", pid, "blood_pressure", bp,
                        "BP elevated: {} mmHg".format(bp))

        # Glucose
        gl = data.get("glucose", 100)
        if gl > t["glucose"]["critical_high"]:
            self._alert("CRITICAL", pid, "glucose", gl,
                        "Glucose CRITICAL: {} mg/dL".format(gl))
        elif gl > t["glucose"]["high"]:
            self._alert("WARNING", pid, "glucose", gl,
                        "Glucose high: {} mg/dL".format(gl))

        # Body temperature
        bt = data.get("body_temp", 36.5)
        if bt > t["body_temp"]["critical_high"]:
            self._alert("CRITICAL", pid, "body_temp", bt,
                        "FEVER: {}°C".format(bt))
        elif bt > t["body_temp"]["high"]:
            self._alert("WARNING", pid, "body_temp", bt,
                        "Temp elevated: {}°C".format(bt))

    def process_environment(self, data):
        """Check environment readings against CQC clinical standards."""
        t = ENVIRONMENT_THRESHOLDS
        rid = data.get("room_id", "ROOM-001")

        # CO2
        co2 = data.get("co2", 400)
        if co2 > t["co2"]["danger"]:
            self._alert("CRITICAL", rid, "co2", co2,
                        "CO2 DANGEROUS: {} ppm".format(co2))
        elif co2 > t["co2"]["warning"]:
            self._alert("WARNING", rid, "co2", co2,
                        "CO2 elevated: {} ppm".format(co2))

        # Room temperature
        rt = data.get("room_temp", 22)
        if rt > t["room_temp"]["high"] or rt < t["room_temp"]["low"]:
            self._alert("WARNING", rid, "room_temp", rt,
                        "Room temp out of range: {}°C".format(rt))

        # Medication fridge — patient safety critical
        fr = data.get("med_fridge_temp", 5)
        if fr > t["med_fridge"]["high"] or fr < t["med_fridge"]["low"]:
            self._alert("CRITICAL", rid, "med_fridge", fr,
                        "Fridge temp: {}°C — meds at risk!".format(fr))

        # Humidity
        hm = data.get("humidity", 45)
        if hm > t["humidity"]["high"] or hm < t["humidity"]["low"]:
            self._alert("WARNING", rid, "humidity", hm,
                        "Humidity out of range: {}%".format(hm))

        # PM2.5 particulates
        pm = data.get("pm25", 10)
        if pm > t["pm25"]["danger"]:
            self._alert("CRITICAL", rid, "pm25", pm,
                        "PM2.5 dangerous: {} µg/m³".format(pm))
        elif pm > t["pm25"]["warning"]:
            self._alert("WARNING", rid, "pm25", pm,
                        "PM2.5 elevated: {} µg/m³".format(pm))

        # Noise
        ns = data.get("noise", 40)
        if ns > t["noise"]["danger"]:
            self._alert("CRITICAL", rid, "noise", ns,
                        "Noise excessive: {} dB".format(ns))
        elif ns > t["noise"]["warning"]:
            self._alert("WARNING", rid, "noise", ns,
                        "Noise elevated: {} dB".format(ns))

    def _alert(self, level, source_id, metric, value, message):
        """Save alert to database."""
        self.db.save_alert(level, source_id, metric, value, message)
        self.alert_count += 1
