"""
Aurelius Health Clinic — Configuration
Central configuration for thresholds, MQTT, database, and simulation settings.
"""

# ============================================================
# DATABASE
# ============================================================

DB_PATH = "data/aurelius_iot.db"

# ============================================================
# MQTT BROKER
# ============================================================

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPICS = {
    "patient":    "aurelius/patient/#",
    "environment": "aurelius/environment/#",
}

# ============================================================
# CLINICAL THRESHOLDS
# Based on NHS clinical guidelines and CQC environmental standards
# ============================================================

PATIENT_THRESHOLDS = {
    "heart_rate": {
        "low": 60,
        "high": 100,
        "critical_high": 120,
        "unit": "BPM",
    },
    "spo2": {
        "low": 94,
        "critical_low": 90,
        "unit": "%",
    },
    "blood_pressure": {
        "low": 90,
        "high": 140,
        "critical_high": 160,
        "unit": "mmHg",
    },
    "glucose": {
        "low": 70,
        "high": 140,
        "critical_high": 180,
        "unit": "mg/dL",
    },
    "body_temp": {
        "low": 36.0,
        "high": 37.5,
        "critical_high": 38.5,
        "unit": "°C",
    },
}

ENVIRONMENT_THRESHOLDS = {
    "co2": {
        "warning": 1000,
        "danger": 1500,
        "unit": "ppm",
    },
    "room_temp": {
        "low": 18.0,
        "high": 26.0,
        "unit": "°C",
    },
    "humidity": {
        "low": 30.0,
        "high": 60.0,
        "unit": "%",
    },
    "med_fridge": {
        "low": 2.0,
        "high": 8.0,
        "unit": "°C",
    },
    "pm25": {
        "warning": 35,
        "danger": 75,
        "unit": "µg/m³",
    },
    "noise": {
        "warning": 65,
        "danger": 80,
        "unit": "dB",
    },
    "light": {
        "low": 300,
        "high": 750,
        "unit": "lux",
    },
}

# ============================================================
# SIMULATION SETTINGS
# ============================================================

SIMULATION = {
    "duration_hours": 24,
    "interval_seconds": 60,
    "anomaly_probability": 0.05,
    "patients": [
        {"id": "PAT-001", "condition": "healthy",      "hr_base": 72, "spo2_base": 97.5, "bp_base": 118, "gl_base": 95,  "temp_base": 36.5},
        {"id": "PAT-002", "condition": "hypertension",  "hr_base": 82, "spo2_base": 95.0, "bp_base": 145, "gl_base": 155, "temp_base": 36.7},
        {"id": "PAT-003", "condition": "respiratory",   "hr_base": 88, "spo2_base": 93.0, "bp_base": 125, "gl_base": 90,  "temp_base": 36.4},
    ],
    "rooms": [
        {"id": "ROOM-001", "type": "consultation", "temp_base": 21.5, "hum_base": 45},
        {"id": "ROOM-002", "type": "waiting",      "temp_base": 22.0, "hum_base": 48},
        {"id": "ROOM-003", "type": "pharmacy",     "temp_base": 20.5, "hum_base": 42},
        {"id": "ROOM-004", "type": "lab",           "temp_base": 21.0, "hum_base": 44},
    ],
}

# ============================================================
# SECURITY SETTINGS
# ============================================================

SECURITY = {
    "encryption_key_length": 32,        # AES-256
    "token_expiry_minutes": 30,
    "max_failed_attempts": 5,
    "data_retention_days": 90,           # UK GDPR compliance
    "allowed_roles": ["clinician", "nurse", "admin", "readonly"],
    "sensitive_fields": ["patient_id", "heart_rate", "spo2", "blood_pressure", "glucose", "body_temp"],
}
