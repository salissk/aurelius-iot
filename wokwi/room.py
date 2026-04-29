# ============================================================
# room.py — Aurelius Health Clinic
# Domain 2: Clinical Environment Monitoring
# ESP32 #2 — Room Sensors & Actuators
# ============================================================

import machine
import dht
import time
import json

# Give USB port time to connect
time.sleep(2)

print("\n" + "=" * 50)
print("  AURELIUS HEALTH CLINIC — IoT System")
print("  Domain 2: Clinical Environment Monitoring")
print("  ESP32 #2 — Room Conditions")
print("=" * 50)

# ============================================================
# PIN SETUP (matching Wokwi wiring)
# ============================================================

# Sensors
room_climate     = dht.DHT22(machine.Pin(15))       # Room temp & humidity

particulate_adc  = machine.ADC(machine.Pin(36))      # VP  — PM2.5
fridge_adc       = machine.ADC(machine.Pin(39))      # VN  — Medication fridge NTC
light_adc        = machine.ADC(machine.Pin(34))      # LDR — Room light
noise_adc        = machine.ADC(machine.Pin(32))      # Noise level pot
co2_adc          = machine.ADC(machine.Pin(33))      # Air CO2 knob

# Actuators
servo_pwm        = machine.PWM(machine.Pin(23), freq=50)  # Ventilation flap
led_green        = machine.Pin(19, machine.Pin.OUT)
led_yellow       = machine.Pin(18, machine.Pin.OUT)
led_red          = machine.Pin(17, machine.Pin.OUT)        # CHANGED from 5 to 17

# Configure ADC — full 0-3.3V range, 12-bit resolution
for adc in [co2_adc, fridge_adc, light_adc, noise_adc, particulate_adc]:
    adc.atten(machine.ADC.ATTN_11DB)
    adc.width(machine.ADC.WIDTH_12BIT)

# Start with green status
led_green.value(1)
led_yellow.value(0)
led_red.value(0)

# ============================================================
# THRESHOLDS
# ============================================================

THRESHOLDS = {
    "co2":        {"warning": 1000, "danger": 1500},
    "room_temp":  {"low": 18.0, "high": 26.0},
    "humidity":   {"low": 30.0, "high": 60.0},
    "med_fridge": {"low": 2.0,  "high": 8.0},
    "pm25":       {"warning": 35, "danger": 75},
    "noise":      {"warning": 65, "danger": 80},
    "light":      {"low": 300,  "high": 750},
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def map_value(adc_raw, out_min, out_max):
    """Map ADC reading (0-4095) to a real-world sensor range."""
    return out_min + (adc_raw / 4095) * (out_max - out_min)


def set_servo_angle(angle):
    """Set servo to angle 0-180 degrees."""
    duty = int(26 + (angle / 180) * 101)
    servo_pwm.duty(duty)


def set_status_leds(level):
    """Set status LEDs: 0=green (normal), 1=yellow (warning), 2=red (critical)."""
    led_green.value(1 if level == 0 else 0)
    led_yellow.value(1 if level == 1 else 0)
    led_red.value(1 if level == 2 else 0)


def check_alerts(data):
    """Edge processing: evaluate environment readings against thresholds."""
    alerts = []
    t = THRESHOLDS

    # CO2
    co2 = data["co2"]
    if co2 > t["co2"]["danger"]:
        alerts.append({"level": "CRITICAL", "metric": "co2",
                        "msg": "CO2 DANGEROUS: {} ppm".format(co2)})
    elif co2 > t["co2"]["warning"]:
        alerts.append({"level": "WARNING", "metric": "co2",
                        "msg": "CO2 elevated: {} ppm".format(co2)})

    # Room temperature
    rt = data["room_temp"]
    if rt > t["room_temp"]["high"]:
        alerts.append({"level": "WARNING", "metric": "room_temp",
                        "msg": "Room too warm: {}C".format(rt)})
    elif rt < t["room_temp"]["low"]:
        alerts.append({"level": "WARNING", "metric": "room_temp",
                        "msg": "Room too cold: {}C".format(rt)})

    # Humidity
    hm = data["humidity"]
    if hm > t["humidity"]["high"]:
        alerts.append({"level": "WARNING", "metric": "humidity",
                        "msg": "Humidity high: {}%".format(hm)})
    elif hm < t["humidity"]["low"]:
        alerts.append({"level": "WARNING", "metric": "humidity",
                        "msg": "Humidity low: {}%".format(hm)})

    # Medication fridge — CRITICAL (patient safety)
    fr = data["med_fridge_temp"]
    if fr > t["med_fridge"]["high"]:
        alerts.append({"level": "CRITICAL", "metric": "med_fridge",
                        "msg": "Fridge TOO WARM: {}C — meds at risk!".format(fr)})
    elif fr < t["med_fridge"]["low"]:
        alerts.append({"level": "CRITICAL", "metric": "med_fridge",
                        "msg": "Fridge TOO COLD: {}C — meds at risk!".format(fr)})

    # PM2.5
    pm = data["pm25"]
    if pm > t["pm25"]["danger"]:
        alerts.append({"level": "CRITICAL", "metric": "pm25",
                        "msg": "PM2.5 DANGEROUS: {} ug/m3".format(pm)})
    elif pm > t["pm25"]["warning"]:
        alerts.append({"level": "WARNING", "metric": "pm25",
                        "msg": "PM2.5 elevated: {} ug/m3".format(pm)})

    # Noise
    ns = data["noise"]
    if ns > t["noise"]["danger"]:
        alerts.append({"level": "CRITICAL", "metric": "noise",
                        "msg": "Noise EXCESSIVE: {} dB".format(ns)})
    elif ns > t["noise"]["warning"]:
        alerts.append({"level": "WARNING", "metric": "noise",
                        "msg": "Noise elevated: {} dB".format(ns)})

    # Light
    lt = data["light"]
    if lt > t["light"]["high"]:
        alerts.append({"level": "WARNING", "metric": "light",
                        "msg": "Light too bright: {} lux".format(lt)})
    elif lt < t["light"]["low"] and lt > 0:
        alerts.append({"level": "WARNING", "metric": "light",
                        "msg": "Light too dim: {} lux".format(lt)})

    return alerts


def control_actuators(alerts, co2_level):
    """Control servo (ventilation) and status LEDs based on alerts."""
    has_critical = False
    has_warning = False

    for a in alerts:
        if a["level"] == "CRITICAL":
            has_critical = True
        elif a["level"] == "WARNING":
            has_warning = True

    # Status LEDs
    if has_critical:
        set_status_leds(2)  # RED
    elif has_warning:
        set_status_leds(1)  # YELLOW
    else:
        set_status_leds(0)  # GREEN

    # Ventilation servo — based on CO2 level
    if co2_level > 1500:
        set_servo_angle(180)
        vent_status = "FULLY OPEN (180)"
    elif co2_level > 1000:
        set_servo_angle(90)
        vent_status = "HALF OPEN (90)"
    elif co2_level > 800:
        set_servo_angle(45)
        vent_status = "QUARTER OPEN (45)"
    else:
        set_servo_angle(0)
        vent_status = "CLOSED (0)"

    return vent_status


# ============================================================
# MAIN LOOP
# ============================================================

cycle = 0

while True:
    cycle += 1

    # --- Read sensors ---
    try:
        room_climate.measure()
        room_temp = room_climate.temperature()
        humidity  = room_climate.humidity()
    except Exception as e:
        room_temp = 22.0
        humidity  = 45.0

    co2             = round(map_value(co2_adc.read(), 300, 2500))
    med_fridge_temp = round(map_value(fridge_adc.read(), -2, 15), 1)
    light           = round(map_value(light_adc.read(), 0, 1000))
    noise           = round(map_value(noise_adc.read(), 25, 95), 1)
    pm25            = round(map_value(particulate_adc.read(), 0, 150), 1)

    # --- Build data payload ---
    data = {
        "domain": "environment_monitoring",
        "room_id": "ROOM-001",
        "room_type": "consultation",
        "room_temp": round(room_temp, 1),
        "humidity": round(humidity, 1),
        "co2": co2,
        "pm25": pm25,
        "light": light,
        "noise": noise,
        "med_fridge_temp": med_fridge_temp,
        "cycle": cycle,
    }

    # --- Edge processing: check thresholds ---
    alerts = check_alerts(data)

    # --- Control actuators ---
    vent_status = control_actuators(alerts, co2)

    # --- Print to serial monitor ---
    print("\n" + "-" * 50)
    print("[Cycle {}] ENVIRONMENT MONITORING".format(cycle))
    print("-" * 50)
    print("  Room Temp:      {}C".format(round(room_temp, 1)))
    print("  Humidity:       {}%".format(round(humidity, 1)))
    print("  CO2 Level:      {} ppm".format(co2))
    print("  PM2.5:          {} ug/m3".format(pm25))
    print("  Light Level:    {} lux".format(light))
    print("  Noise Level:    {} dB".format(noise))
    print("  Med Fridge:     {}C".format(med_fridge_temp))
    print("  Ventilation:    {}".format(vent_status))

    # Print alerts
    if alerts:
        print("  --- ALERTS ---")
        for a in alerts:
            print("  [{}] {}".format(a["level"], a["msg"]))
    else:
        print("  Status: Environment NORMAL")

    # LED state
    g = "ON" if led_green.value() else "OFF"
    y = "ON" if led_yellow.value() else "OFF"
    r = "ON" if led_red.value() else "OFF"
    print("  LEDs: Green={} Yellow={} Red={}".format(g, y, r))

    # --- Output JSON (for Python backend to parse) ---
    print("JSON:" + json.dumps(data))

    time.sleep(3)
