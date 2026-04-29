"""
Aurelius Health Clinic — Security Module
Implements security controls for healthcare IoT data:
  Data validation and sanitisation
  Role-based access control (RBAC)
  Data encryption for patient records (UK GDPR Article 9)
  Audit logging (NHS Data Security and Protection Toolkit)
  Input validation against injection attacks (OWASP IoT Top 10)
  Data anonymisation for research/analytics
"""

import hashlib
import hmac
import secrets
import json
import re
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SECURITY


class SecurityManager:
    """Manages authentication, encryption, and access control."""

    def __init__(self, db=None):
        self.db = db
        self._secret_key = secrets.token_hex(SECURITY["encryption_key_length"])
        self._active_tokens = {}
        self._failed_attempts = {}
        self.sensitive_fields = SECURITY["sensitive_fields"]
        self.allowed_roles = SECURITY["allowed_roles"]

    # 1. DATA VALIDATION (OWASP IoT #3 — Insecure Data Transfer)
   
    def validate_patient_data(self, data):
        """
        Validate incoming patient data against expected ranges.
        Prevents injection of malicious or corrupted sensor readings.
        Addresses OWASP IoT Top 10 #3: Insecure Ecosystem Interfaces.
        """
        errors = []

        # Check required fields exist
        required = ["patient_id", "heart_rate", "spo2", "blood_pressure", "glucose", "body_temp"]
        for field in required:
            if field not in data:
                errors.append("Missing required field: {}".format(field))

        if errors:
            return False, errors

        # Validate patient_id format (alphanumeric + hyphens only)
        pid = str(data.get("patient_id", ""))
        if not re.match(r'^[A-Za-z0-9\-]{1,20}$', pid):
            errors.append("Invalid patient_id format: {}".format(pid))

        # Validate numeric ranges (reject physiologically impossible values)
        validations = {
            "heart_rate":     (20, 250, "Heart rate"),
            "spo2":           (50, 100, "SpO2"),
            "blood_pressure": (40, 300, "Blood pressure"),
            "glucose":        (20, 500, "Glucose"),
            "body_temp":      (30.0, 45.0, "Body temperature"),
        }

        for field, (min_val, max_val, label) in validations.items():
            value = data.get(field)
            if value is not None:
                try:
                    val = float(value)
                    if val < min_val or val > max_val:
                        errors.append("{} out of valid range ({}-{}): {}".format(
                            label, min_val, max_val, val))
                except (ValueError, TypeError):
                    errors.append("{} is not a valid number: {}".format(label, value))

        return len(errors) == 0, errors

    def validate_environment_data(self, data):
        """
        Validate incoming environment data against expected ranges.
        Prevents spoofed or corrupted sensor data from entering the system.
        """
        errors = []

        required = ["room_id", "room_temp", "humidity", "co2"]
        for field in required:
            if field not in data:
                errors.append("Missing required field: {}".format(field))

        if errors:
            return False, errors

        # Validate room_id format
        rid = str(data.get("room_id", ""))
        if not re.match(r'^[A-Za-z0-9\-]{1,20}$', rid):
            errors.append("Invalid room_id format: {}".format(rid))

        validations = {
            "room_temp":      (0, 50, "Room temperature"),
            "humidity":       (0, 100, "Humidity"),
            "co2":            (100, 10000, "CO2"),
            "pm25":           (0, 1000, "PM2.5"),
            "noise":          (0, 150, "Noise"),
            "med_fridge_temp": (-10, 30, "Fridge temperature"),
        }

        for field, (min_val, max_val, label) in validations.items():
            value = data.get(field)
            if value is not None:
                try:
                    val = float(value)
                    if val < min_val or val > max_val:
                        errors.append("{} out of valid range ({}-{}): {}".format(
                            label, min_val, max_val, val))
                except (ValueError, TypeError):
                    errors.append("{} is not a valid number: {}".format(label, value))

        return len(errors) == 0, errors

    # 2. ROLE-BASED ACCESS CONTROL (OWASP IoT #5 — Privacy)

    def generate_token(self, user_role):
        """
        Generate a session token for authenticated users.
        Implements role-based access per NHS DSPT Standard 4.
        """
        if user_role not in self.allowed_roles:
            return None, "Invalid role: {}".format(user_role)

        token = secrets.token_hex(32)
        expiry = datetime.now() + timedelta(minutes=SECURITY["token_expiry_minutes"])

        self._active_tokens[token] = {
            "role": user_role,
            "created": datetime.now().isoformat(),
            "expires": expiry.isoformat(),
        }

        # Log access
        if self.db:
            self.db.log_access(user_role, "token_generated", "auth", success=True)

        return token, None

    def verify_token(self, token):
        """Verify a session token is valid and not expired."""
        if token not in self._active_tokens:
            return False, "Invalid token"

        token_data = self._active_tokens[token]
        expiry = datetime.fromisoformat(token_data["expires"])

        if datetime.now() > expiry:
            del self._active_tokens[token]
            return False, "Token expired"

        return True, token_data["role"]

    def check_permission(self, token, resource):
        """
        Check if a token holder has permission to access a resource.
        Implements principle of least privilege (NHS DSPT Standard 5).

        Access matrix:
          clinician: patient data (read/write), environment (read), alerts (read/write)
          nurse:     patient data (read), environment (read), alerts (read)
          admin:     all data (read/write), system config
          readonly:  environment data (read only)
        """
        valid, role = self.verify_token(token)
        if not valid:
            return False, role  # role contains error message

        permissions = {
            "clinician": ["patient_read", "patient_write", "environment_read", "alerts_read", "alerts_write"],
            "nurse":     ["patient_read", "environment_read", "alerts_read"],
            "admin":     ["patient_read", "patient_write", "environment_read", "environment_write",
                          "alerts_read", "alerts_write", "system_config", "audit_read"],
            "readonly":  ["environment_read"],
        }

        role_permissions = permissions.get(role, [])
        has_access = resource in role_permissions

        # Log access attempt
        if self.db:
            self.db.log_access(role, "access_check", resource, success=has_access)

        return has_access, role

    # 3. DATA ENCRYPTION (UK GDPR Article 9 — Health Data)

    def hash_patient_id(self, patient_id):
        """
        Create a pseudonymised hash of patient ID for analytics.
        UK GDPR Article 9 requires special protection for health data.
        Pseudonymisation allows analysis without exposing identity.
        """
        return hashlib.sha256(
            (patient_id + self._secret_key).encode()
        ).hexdigest()[:16]

    def anonymise_data(self, data):
        """
        Remove or hash personally identifiable information from data.
        Used when exporting data for research or HUIL reporting.
        Implements data minimisation principle (UK GDPR Article 5).
        """
        anonymised = dict(data)

        # Replace patient_id with pseudonymised hash
        if "patient_id" in anonymised:
            anonymised["patient_id"] = self.hash_patient_id(anonymised["patient_id"])

        # Remove any fields that could identify individuals
        fields_to_remove = ["name", "nhs_number", "address", "date_of_birth"]
        for field in fields_to_remove:
            anonymised.pop(field, None)

        return anonymised

    def create_integrity_hash(self, data):
        """
        Create HMAC hash to verify data has not been tampered with.
        Protects against OWASP IoT #4: Lack of Secure Update Mechanism.
        """
        data_string = json.dumps(data, sort_keys=True)
        return hmac.new(
            self._secret_key.encode(),
            data_string.encode(),
            hashlib.sha256
        ).hexdigest()

    def verify_integrity(self, data, expected_hash):
        """Verify data integrity using HMAC."""
        actual_hash = self.create_integrity_hash(data)
        return hmac.compare_digest(actual_hash, expected_hash)

    # 4. AUDIT LOGGING (NHS DSPT Standard 7)

    def log_security_event(self, event_type, details, severity="INFO"):
        """
        Log security-relevant events for NHS DSPT compliance.
        Standard 7 requires audit trails for all access to patient data.
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "details": details,
        }
        print("[SECURITY] [{}] {}: {}".format(severity, event_type, details))

        if self.db:
            self.db.log_access(
                user_role="system",
                action=event_type,
                resource=details,
                success=(severity != "CRITICAL")
            )

        return event

    # 5. BRUTE FORCE PROTECTION

    def record_failed_attempt(self, identifier):
        """Track failed authentication attempts."""
        if identifier not in self._failed_attempts:
            self._failed_attempts[identifier] = {"count": 0, "first": datetime.now()}

        self._failed_attempts[identifier]["count"] += 1
        self._failed_attempts[identifier]["last"] = datetime.now()

        count = self._failed_attempts[identifier]["count"]
        if count >= SECURITY["max_failed_attempts"]:
            self.log_security_event(
                "ACCOUNT_LOCKOUT",
                "Identifier {} locked after {} failed attempts".format(identifier, count),
                severity="WARNING"
            )
            return True  # Account locked
        return False  # Not yet locked

    def is_locked(self, identifier):
        """Check if an identifier is locked due to too many failed attempts."""
        if identifier not in self._failed_attempts:
            return False
        return self._failed_attempts[identifier]["count"] >= SECURITY["max_failed_attempts"]

    def reset_attempts(self, identifier):
        """Reset failed attempt counter after successful auth."""
        self._failed_attempts.pop(identifier, None)
