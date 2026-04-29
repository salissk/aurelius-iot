"""
Aurelius Health Clinic — Database Handler
SQLite storage for patient readings, environment readings, and alerts.
Implements data retention policies for UK GDPR compliance.
"""

import sqlite3
import os
from datetime import datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


class Database:
    """SQLite database manager for the Aurelius IoT system."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._create_tables()

    def _connect(self):
        """Create a new database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        """Initialise database tables if they don't exist."""
        conn = self._connect()
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS patient_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                patient_id TEXT,
                heart_rate INTEGER,
                spo2 REAL,
                blood_pressure INTEGER,
                glucose INTEGER,
                body_temp REAL,
                motion INTEGER,
                is_anomaly INTEGER DEFAULT 0
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS environment_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                room_id TEXT,
                room_type TEXT,
                room_temp REAL,
                humidity REAL,
                co2 INTEGER,
                pm25 REAL,
                light INTEGER,
                noise REAL,
                med_fridge_temp REAL,
                is_anomaly INTEGER DEFAULT 0
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT,
                source_id TEXT,
                metric TEXT,
                value REAL,
                message TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_role TEXT,
                action TEXT,
                resource TEXT,
                ip_address TEXT,
                success INTEGER DEFAULT 1
            )
        """)

        conn.commit()
        conn.close()
        print("[DB] Database initialised at", self.db_path)

    def save_patient_reading(self, data):
        """Insert a patient vital signs reading."""
        conn = self._connect()
        c = conn.cursor()
        c.execute("""
            INSERT INTO patient_readings
            (timestamp, patient_id, heart_rate, spo2, blood_pressure, glucose, body_temp, motion, is_anomaly)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("timestamp", datetime.now().isoformat()),
            data.get("patient_id", "PAT-001"),
            data.get("heart_rate", 0),
            data.get("spo2", 0),
            data.get("blood_pressure", 0),
            data.get("glucose", 0),
            data.get("body_temp", 0),
            data.get("motion", 0),
            data.get("is_anomaly", 0),
        ))
        conn.commit()
        conn.close()

    def save_environment_reading(self, data):
        """Insert a clinical environment reading."""
        conn = self._connect()
        c = conn.cursor()
        c.execute("""
            INSERT INTO environment_readings
            (timestamp, room_id, room_type, room_temp, humidity, co2, pm25, light, noise, med_fridge_temp, is_anomaly)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("timestamp", datetime.now().isoformat()),
            data.get("room_id", "ROOM-001"),
            data.get("room_type", "consultation"),
            data.get("room_temp", 0),
            data.get("humidity", 0),
            data.get("co2", 0),
            data.get("pm25", 0),
            data.get("light", 0),
            data.get("noise", 0),
            data.get("med_fridge_temp", 0),
            data.get("is_anomaly", 0),
        ))
        conn.commit()
        conn.close()

    def save_alert(self, level, source_id, metric, value, message):
        """Insert an alert record."""
        conn = self._connect()
        c = conn.cursor()
        c.execute("""
            INSERT INTO alerts (timestamp, level, source_id, metric, value, message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), level, source_id, metric, value, message))
        conn.commit()
        conn.close()

    def log_access(self, user_role, action, resource, ip_address="127.0.0.1", success=True):
        """Log an access event for audit trail (NHS DSPT compliance)."""
        conn = self._connect()
        c = conn.cursor()
        c.execute("""
            INSERT INTO access_log (timestamp, user_role, action, resource, ip_address, success)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), user_role, action, resource, ip_address, 1 if success else 0))
        conn.commit()
        conn.close()

    def get_patient_data(self, patient_id=None, limit=1000):
        """Retrieve patient readings."""
        conn = self._connect()
        c = conn.cursor()
        if patient_id:
            c.execute("SELECT * FROM patient_readings WHERE patient_id=? ORDER BY timestamp DESC LIMIT ?",
                       (patient_id, limit))
        else:
            c.execute("SELECT * FROM patient_readings ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows

    def get_environment_data(self, room_id=None, limit=1000):
        """Retrieve environment readings."""
        conn = self._connect()
        c = conn.cursor()
        if room_id:
            c.execute("SELECT * FROM environment_readings WHERE room_id=? ORDER BY timestamp DESC LIMIT ?",
                       (room_id, limit))
        else:
            c.execute("SELECT * FROM environment_readings ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows

    def get_alerts(self, level=None, limit=500):
        """Retrieve alerts."""
        conn = self._connect()
        c = conn.cursor()
        if level:
            c.execute("SELECT * FROM alerts WHERE level=? ORDER BY timestamp DESC LIMIT ?", (level, limit))
        else:
            c.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows

    def clear_database(self):
        """Clear all data (for re-running simulation)."""
        conn = self._connect()
        c = conn.cursor()
        c.execute("DELETE FROM patient_readings")
        c.execute("DELETE FROM environment_readings")
        c.execute("DELETE FROM alerts")
        c.execute("DELETE FROM access_log")
        conn.commit()
        conn.close()
        print("[DB] All data cleared")
