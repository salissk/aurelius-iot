# Aurelius Health Clinic — IoT Monitoring System

## CPS6008 Internet of Things — Assessment 1
**St Mary's University, Twickenham, London**

---

## Overview

A simulated IoT system for **Aurelius Health Clinic**, a primary care facility operating within the Helix Park smart city. The system covers two operational domains using 16 IoT devices across 2 ESP32 microcontrollers:

- **Domain 1: Remote Patient Monitoring** — Continuous monitoring of patient vital signs (heart rate, SpO2, blood pressure, glucose, body temperature) with real-time alerting for clinical intervention.
- **Domain 2: Clinical Environment Monitoring** — Automated monitoring of consultation rooms, waiting areas, pharmacy, and laboratory conditions (temperature, humidity, CO2, PM2.5, noise, light, medication fridge temperature) to meet CQC environmental standards.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DEVICE LAYER (Wokwi)                 │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │  ESP32 #1         │    │  ESP32 #2                │   │
│  │  Patient Monitor  │    │  Environment Monitor     │   │
│  │  8 devices        │    │  8 devices               │   │
│  └────────┬─────────┘    └──────────┬───────────────┘   │
│           │   MQTT / Serial         │                   │
├───────────┼─────────────────────────┼───────────────────┤
│           │    PROCESSING LAYER     │                   │
│           ▼                         ▼                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Edge Processor (threshold detection, alerts)    │   │
│  │  Security Manager (validation, RBAC, encryption) │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                               │
├─────────────────────────┼───────────────────────────────┤
│                         │   APPLICATION LAYER           │
│                         ▼                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SQLite Database ──► Streamlit Dashboard          │   │
│  │  (patient_readings, environment_readings, alerts) │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- **Python 3.10+** — [python.org](https://python.org)
- **Wokwi account** — [wokwi.com](https://wokwi.com) (for circuit simulation)
- **MQTT broker** (optional) — only needed for live Wokwi data

### Python Dependencies

```
paho-mqtt
streamlit
pandas
plotly
numpy
matplotlib
```

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd aurelius-iot
   ```

2. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   python3 main.py
   ```
   This should print the usage instructions.

---

## Running the System

### Step 1: Generate Simulated Data

```bash
python3 main.py --simulate
```

This generates 24 hours of realistic sensor data for 3 patients and 4 clinic rooms, stored in `data/aurelius_iot.db`. The simulation includes:
- Circadian rhythm variation in patient vitals
- Occupancy-driven environment changes
- 5% anomaly injection for testing alert thresholds
- Security validation on every reading

**Custom duration:**
```bash
python3 main.py --simulate --hours=48
python3 main.py --simulate --hours=12 --interval=30
```

### Step 2: Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser. The dashboard has 4 tabs:
- **Patients** — vital signs with threshold lines, patient comparison
- **Environment** — room conditions, medication fridge compliance
- **Alerts** — severity breakdown, timeline, filterable alert log
- **Analytics** — statistical summaries, anomaly scatter, hourly patterns

### Step 3: Wokwi Circuit Simulation

Two separate Wokwi projects demonstrate the hardware layer:

**Domain 1 — Patient Monitoring:**
1. Open Wokwi and create a new ESP32 MicroPython project
2. Import `wokwi/patient.py` as `main.py` and the corresponding `diagram.json`
3. Click Play — adjust potentiometers to simulate changing vital signs
4. Observe threshold alerts, LED, and buzzer responses

**Domain 2 — Environment Monitoring:**
1. Open a second Wokwi project
2. Import `wokwi/room.py` as `main.py` and the corresponding `diagram.json`
3. Click Play — adjust knobs to simulate changing room conditions
4. Observe status LEDs (green/yellow/red) and ventilation servo response

### Step 4: Run Unit Tests

```bash
python3 -m unittest tests.test_sensors -v
```

Runs 18 tests covering data validation, access control, anonymisation, integrity checking, brute force protection, and sensor simulation ranges.

### Optional: Live MQTT Mode

To receive live data from running Wokwi projects:
```bash
python3 main.py --live
```
Requires Wokwi ESP32 projects configured to publish via MQTT to `broker.emqx.io`.

---

## Project Structure

```
aurelius-iot/
├── main.py                          # Entry point — simulation or live mode
├── config.py                        # Thresholds, MQTT, security settings
│
├── communication/                   # MQTT communication layer
│   ├── __init__.py
│   └── mqtt_handler.py              # MQTT client for Wokwi data
│
├── dashboard/                       # Streamlit web dashboard
│   └── app.py                       # 4-tab monitoring interface
│
├── processing/                      # Data processing layer
│   ├── __init__.py
│   └── edge_processor.py            # Threshold checking and alert generation
│
├── security/                        # Security and compliance layer
│   ├── __init__.py
│   └── auth.py                      # Validation, RBAC, encryption, audit
│
├── sensors/                         # Sensor simulation layer
│   ├── __init__.py
│   └── sensor_simulator.py          # Realistic patient and environment data
│
├── storage/                         # Data persistence layer
│   ├── __init__.py
│   └── database.py                  # SQLite database handler
│
├── tests/                           # Unit tests
│   ├── __init__.py
│   └── test_sensors.py              # 18 tests for validation and security
│
├── wokwi/                           # Wokwi ESP32 circuit projects
│   ├── patient.py                   # Domain 1 — ESP32 #1 MicroPython
│   ├── room.py                      # Domain 2 — ESP32 #2 MicroPython
│   └── diagram.json                 # Circuit diagrams
│
├── data/                            # Generated data (not committed)
│   └── aurelius_iot.db              # SQLite database
│
├── output/                          # Charts and analysis output
│   └── charts/
│
├── requirements.txt                 # Python dependencies
└── .gitignore
```

---

## Devices (16 Total)

### Domain 1 — Remote Patient Monitoring (ESP32 #1)

| Device | Component | GPIO | Purpose |
|--------|-----------|------|---------|
| Body Temperature | DHT22 | 4 | Patient body temperature |
| Heart Rate | Potentiometer | 35 | Simulated BPM (40–150) |
| Blood Oxygen (SpO2) | Potentiometer | 33 | Simulated SpO2 (85–100%) |
| Blood Pressure | Potentiometer | 32 | Simulated systolic (70–190 mmHg) |
| Glucose | Potentiometer | 34 | Simulated glucose (50–220 mg/dL) |
| Activity Sensor | PIR (HC-SR501) | 27 | Patient movement detection |
| Critical Alert | Red LED | 26 | Visual alert for critical readings |
| Emergency Alarm | Buzzer | 25 | Audible alarm for emergencies |

### Domain 2 — Clinical Environment Monitoring (ESP32 #2)

| Device | Component | GPIO | Purpose |
|--------|-----------|------|---------|
| Room Climate | DHT22 | 15 | Room temperature and humidity |
| Air Quality (CO2) | Potentiometer | 33 | Simulated CO2 (300–2500 ppm) |
| Noise Level | Potentiometer | 32 | Simulated noise (25–95 dB) |
| Particulates (PM2.5) | Potentiometer | VP/36 | Simulated PM2.5 (0–150 µg/m³) |
| Room Light | Photoresistor (LDR) | 34 | Light level monitoring |
| Medication Fridge | NTC Thermistor | VN/39 | Fridge temperature (safe: 2–8°C) |
| Ventilation Flap | Servo Motor (SG90) | 23 | Automated ventilation control |
| Environment Status | 3× LEDs (G/Y/R) | 19/18/17 | Green=normal, Yellow=warning, Red=critical |

---

## Security Features

The security module (`security/auth.py`) implements controls aligned with:
- **OWASP IoT Top 10** — input validation, data integrity verification
- **NHS Data Security and Protection Toolkit** — audit logging, access control
- **UK GDPR Article 9** — health data anonymisation, data minimisation

| Feature | Description |
|---------|-------------|
| Data Validation | Rejects readings outside physiologically valid ranges |
| Role-Based Access Control | 4 roles: clinician, nurse, admin, readonly |
| Patient ID Anonymisation | SHA-256 pseudonymisation for analytics |
| Data Integrity | HMAC verification to detect tampered data |
| Brute Force Protection | Account lockout after 5 failed attempts |
| Audit Logging | All access events logged for NHS DSPT compliance |

---

## Key Technologies

| Component | Technology |
|-----------|------------|
| Microcontroller | ESP32 (MicroPython) |
| Circuit Simulation | Wokwi |
| Communication Protocol | MQTT |
| Backend Language | Python 3 |
| Database | SQLite |
| Dashboard | Streamlit + Plotly |
| Security | hashlib, hmac, secrets (Python stdlib) |
| Testing | unittest (18 tests) |

---

## Regulatory Compliance

This system is designed with awareness of:
- **UK GDPR** — Data minimisation, pseudonymisation, consent for health data
- **NHS Data Security and Protection Toolkit** — 10 data security standards
- **Care Quality Commission (CQC)** — Clinical environment standards
- **Helix Park Smart Operations Charter** — HUIL data feed requirements

---

## Author

CPS6008 Internet of Things — Assessment 1
St Mary's University, Twickenham, London
