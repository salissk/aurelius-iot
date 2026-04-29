"""
Aurelius Health Clinic — Unit Tests
Tests for sensor validation, security controls, and edge processing.
Run: python -m pytest tests/test_sensors.py -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.auth import SecurityManager
from sensors.sensor_simulator import SensorSimulator
from storage.database import Database
from processing.edge_processor import EdgeProcessor


class TestDataValidation(unittest.TestCase):
    """Test security data validation."""

    def setUp(self):
        self.security = SecurityManager()

    def test_valid_patient_data(self):
        data = {"patient_id": "PAT-001", "heart_rate": 75, "spo2": 98,
                "blood_pressure": 120, "glucose": 100, "body_temp": 36.5}
        valid, errors = self.security.validate_patient_data(data)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_missing_fields(self):
        data = {"patient_id": "PAT-001"}
        valid, errors = self.security.validate_patient_data(data)
        self.assertFalse(valid)

    def test_out_of_range_heart_rate(self):
        data = {"patient_id": "PAT-001", "heart_rate": 999, "spo2": 98,
                "blood_pressure": 120, "glucose": 100, "body_temp": 36.5}
        valid, errors = self.security.validate_patient_data(data)
        self.assertFalse(valid)

    def test_invalid_patient_id_format(self):
        data = {"patient_id": "'; DROP TABLE--", "heart_rate": 75, "spo2": 98,
                "blood_pressure": 120, "glucose": 100, "body_temp": 36.5}
        valid, errors = self.security.validate_patient_data(data)
        self.assertFalse(valid)

    def test_valid_environment_data(self):
        data = {"room_id": "ROOM-001", "room_temp": 22.5, "humidity": 45, "co2": 450}
        valid, errors = self.security.validate_environment_data(data)
        self.assertTrue(valid)


class TestAccessControl(unittest.TestCase):
    """Test role-based access control."""

    def setUp(self):
        self.security = SecurityManager()

    def test_generate_valid_token(self):
        token, error = self.security.generate_token("clinician")
        self.assertIsNotNone(token)
        self.assertIsNone(error)

    def test_invalid_role(self):
        token, error = self.security.generate_token("hacker")
        self.assertIsNone(token)
        self.assertIsNotNone(error)

    def test_clinician_can_read_patients(self):
        token, _ = self.security.generate_token("clinician")
        has_access, role = self.security.check_permission(token, "patient_read")
        self.assertTrue(has_access)

    def test_readonly_cannot_write_patients(self):
        token, _ = self.security.generate_token("readonly")
        has_access, role = self.security.check_permission(token, "patient_write")
        self.assertFalse(has_access)

    def test_nurse_cannot_write_patients(self):
        token, _ = self.security.generate_token("nurse")
        has_access, role = self.security.check_permission(token, "patient_write")
        self.assertFalse(has_access)

    def test_admin_has_full_access(self):
        token, _ = self.security.generate_token("admin")
        has_access, _ = self.security.check_permission(token, "system_config")
        self.assertTrue(has_access)


class TestDataAnonymisation(unittest.TestCase):
    """Test UK GDPR data anonymisation."""

    def setUp(self):
        self.security = SecurityManager()

    def test_patient_id_hashed(self):
        data = {"patient_id": "PAT-001", "heart_rate": 75}
        anonymised = self.security.anonymise_data(data)
        self.assertNotEqual(anonymised["patient_id"], "PAT-001")
        self.assertEqual(len(anonymised["patient_id"]), 16)

    def test_integrity_hash(self):
        data = {"heart_rate": 75, "spo2": 98}
        hash1 = self.security.create_integrity_hash(data)
        self.assertTrue(self.security.verify_integrity(data, hash1))

    def test_tampered_data_fails_integrity(self):
        data = {"heart_rate": 75, "spo2": 98}
        hash1 = self.security.create_integrity_hash(data)
        data["heart_rate"] = 999  # Tamper
        self.assertFalse(self.security.verify_integrity(data, hash1))


class TestBruteForceProtection(unittest.TestCase):
    """Test brute force protection."""

    def setUp(self):
        self.security = SecurityManager()

    def test_lockout_after_max_attempts(self):
        for i in range(5):
            self.security.record_failed_attempt("attacker_ip")
        self.assertTrue(self.security.is_locked("attacker_ip"))

    def test_not_locked_below_threshold(self):
        for i in range(3):
            self.security.record_failed_attempt("user_ip")
        self.assertFalse(self.security.is_locked("user_ip"))


class TestSensorSimulator(unittest.TestCase):
    """Test sensor data generation."""

    def setUp(self):
        self.sim = SensorSimulator()

    def test_patient_reading_in_range(self):
        patient = {"id": "PAT-001", "hr_base": 72, "spo2_base": 97.5,
                    "bp_base": 118, "gl_base": 95, "temp_base": 36.5}
        reading = self.sim.generate_patient_reading(patient, sim_hour=12)
        self.assertGreaterEqual(reading["heart_rate"], 40)
        self.assertLessEqual(reading["heart_rate"], 180)
        self.assertGreaterEqual(reading["spo2"], 80)
        self.assertLessEqual(reading["spo2"], 100)

    def test_environment_reading_in_range(self):
        room = {"id": "ROOM-001", "type": "consultation", "temp_base": 21.5, "hum_base": 45}
        reading = self.sim.generate_environment_reading(room, sim_hour=12)
        self.assertGreaterEqual(reading["room_temp"], 15)
        self.assertLessEqual(reading["room_temp"], 35)
        self.assertGreaterEqual(reading["co2"], 350)


if __name__ == "__main__":
    unittest.main()
