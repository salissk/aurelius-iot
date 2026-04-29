# ============================================================
# patient.py — Aurelius Health Clinic
# Domain 1: Remote Patient Monitoring
# ESP32 #1 — Wokwi MicroPython
# ============================================================

import machine
import dht
import time
import json

# Give USB port time to connect
time.sleep(2)

print("\n" + "=" * 50)
print("  AURELIUS HEALTH CLINIC — IoT System")
print("  Domain 1: Remote Patient Monitoring")
print("  ESP32 #1 — Patient Vital Signs")
print("=" * 50)

# ============================================================
# PIN SETUP
# ============================================================

# Sensors
body_temp_sensor = dht.DHT22(machine.Pin(4))

heart_rate_adc   = machine.ADC(machine.Pin(35))
spo2_adc         = machine.ADC(machine.Pin(33))
bp_adc           = machine.ADC(machine.Pin(32))
glucose_adc      = machine.ADC(machine.Pin(34))

pir_sensor       = machine.Pin(27, machine.Pin.IN)

# Actuators
alert_led        = machine.Pin(26, machine.Pin.OUT)
buzzer           = machine.Pin(25, machine.Pin.OUT)

# Configure ADC — full 0-3.3V range, 12-bit resolution
for adc in [heart_rate_adc, spo2_adc, bp_adc, glucose_adc]:
    adc.atten(machine.ADC.ATTN_11DB)
    adc.width(machine.ADC.WIDTH_12BIT)

# Start with actuators OFF
alert_led.value(0)
buzzer.value(0)

# ============================================================
# THRESHOLDS
# ============================================================

THRESHOLDS = {
    "heart_rate":     {"low": 60,   "high": 100,  "critical_high": 120},
    "spo2":           {"low": 94,   "critical_low": 90},
    "blood_pressure": {"low": 90,   "high": 140,  "critical_high": 160},
    "glucose":        {"low": 70,   "high": 140,  "critical_high": 180},
    "body_temp":      {"low": 36.0, "high": 37.5, "critical_high": 38.5},
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def map_value(adc_raw, out_min, out_max):
    """Map ADC reading (0-4095) to a real-world sensor range."""
    return out_min + (adc_raw / 4095) * (out_max - out_min)


def check_alerts(data):
    """Edge processing: evaluate patient vitals against thresholds."""
    alerts = []
    t = THRESHOLDS

    # Heart rate
    hr = data["heart_rate"]
    if hr > t["heart_rate"]["critical_high"]:
        alerts.append({"level": "CRITICAL", "metric": "heart_rate",
                        "msg": "Heart rate CRITICAL: {} BPM".format(hr)})
    elif hr > t["heart_rate"]["high"]:
        alerts.append({"level": "WARNING", "metric": "heart_rate",
                        "msg": "Heart rate elevated: {} BPM".format(hr)})
    elif hr < t["heart_rate"]["low"]:
        alerts.append({"level": "WARNING", "metric": "heart_rate",
                        "msg": "Heart rate low: {} BPM".format(hr)})

    # SpO2
    sp = data["spo2"]
    if sp < t["spo2"]["critical_low"]:
        alerts.append({"level": "CRITICAL", "metric": "spo2",
                        "msg": "SpO2 CRITICAL: {}%".format(sp)})
    elif sp < t["spo2"]["low"]:
        alerts.append({"level": "WARNING", "metric": "spo2",
                        "msg": "SpO2 low: {}%".format(sp)})

    # Blood pressure
    bp = data["blood_pressure"]
    if bp > t["blood_pressure"]["critical_high"]:
        alerts.append({"level": "CRITICAL", "metric": "blood_pressure",
                        "msg": "BP CRITICAL: {} mmHg".format(bp)})
    elif bp > t["blood_pressure"]["high"]:
        alerts.append({"level": "WARNING", "metric": "blood_pressure",
                        "msg": "BP elevated: {} mmHg".format(bp)})
    elif bp < t["blood_pressure"]["low"]:
        alerts.append({"level": "WARNING", "metric": "blood_pressure",
                        "msg": "BP low: {} mmHg".format(bp)})

    # Glucose
    gl = data["glucose"]
    if gl > t["glucose"]["critical_high"]:
        alerts.append({"level": "CRITICAL", "metric": "glucose",
                        "msg": "Glucose CRITICAL: {} mg/dL".format(gl)})
    elif gl > t["glucose"]["high"]:
        alerts.append({"level": "WARNING", "metric": "glucose",
                        "msg": "Glucose high: {} mg/dL".format(gl)})
    elif gl < t["glucose"]["low"]:
        alerts.append({"level": "WARNING", "metric": "glucose",
                        "msg": "Glucose low: {} mg/dL".format(gl)})

    # Body temperature
    bt = data["body_temp"]
    if bt > t["body_temp"]["critical_high"]:
        alerts.append({"level": "CRITICAL", "metric": "body_temp",
                        "msg": "FEVER detected: {}C".format(bt)})
    elif bt > t["body_temp"]["high"]:
        alerts.append({"level": "WARNING", "metric": "body_temp",
                        "msg": "Temp elevated: {}C".format(bt)})
    elif bt < t["body_temp"]["low"]:
        alerts.append({"level": "WARNING", "metric": "body_temp",
                        "msg": "Temp low: {}C".format(bt)})

    return alerts


def control_actuators(alerts):
    """Control LED and buzzer based on alert severity."""
    has_critical = False
    has_warning = False

    for a in alerts:
        if a["level"] == "CRITICAL":
            has_critical = True
        elif a["level"] == "WARNING":
            has_warning = True

    if has_critical:
        alert_led.value(1)
        buzzer.value(1)
    elif has_warning:
        alert_led.value(1)
        buzzer.value(0)
    else:
        alert_led.value(0)
        buzzer.value(0)


# ============================================================
# MAIN LOOP
# ============================================================

cycle = 0

while True:
    cycle += 1

    # --- Read sensors ---
    try:
        body_temp_sensor.measure()
        body_temp = body_temp_sensor.temperature()
    except Exception as e:
        body_temp = 36.5  # fallback if sensor read fails

    heart_rate     = round(map_value(heart_rate_adc.read(), 40, 150))
    spo2           = round(map_value(spo2_adc.read(), 85, 100), 1)
    blood_pressure = round(map_value(bp_adc.read(), 70, 190))
    glucose        = round(map_value(glucose_adc.read(), 50, 220))
    motion         = pir_sensor.value()

    # --- Build data payload ---
    data = {
        "domain": "patient_monitoring",
        "patient_id": "PAT-001",
        "heart_rate": heart_rate,
        "spo2": spo2,
        "blood_pressure": blood_pressure,
        "glucose": glucose,
        "body_temp": round(body_temp, 1),
        "motion": motion,
        "cycle": cycle,
    }

    # --- Edge processing: check thresholds ---
    alerts = check_alerts(data)

    # --- Control actuators ---
    control_actuators(alerts)

    # --- Print to serial monitor ---
    print("\n" + "-" * 50)
    print("[Cycle {}] PATIENT MONITORING".format(cycle))
    print("-" * 50)
    print("  Heart Rate:     {} BPM".format(heart_rate))
    print("  SpO2:           {}%".format(spo2))
    print("  Blood Pressure: {} mmHg".format(blood_pressure))
    print("  Glucose:        {} mg/dL".format(glucose))
    print("  Body Temp:      {}C".format(round(body_temp, 1)))
    print("  Activity:       {}".format("Moving" if motion else "Still"))

    # Print alerts
    if alerts:
        print("  --- ALERTS ---")
        for a in alerts:
            print("  [{}] {}".format(a["level"], a["msg"]))
    else:
        print("  Status: All vitals NORMAL")

    # Print actuator state
    led_state = "ON" if alert_led.value() else "OFF"
    buz_state = "ON" if buzzer.value() else "OFF"
    print("  LED: {} | Buzzer: {}".format(led_state, buz_state))

    # --- Output JSON (for Python backend to parse) ---
    print("JSON:" + json.dumps(data))

    time.sleep(3)
