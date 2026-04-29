"""
Aurelius Health Clinic — Data Analysis & Visualisation
Generates publication-ready charts for the CPS6008 project report.

Usage: python3 analysis.py
Output: output/charts/ (PNG files for report)

Run main.py --simulate first to generate data.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_PATH, PATIENT_THRESHOLDS, ENVIRONMENT_THRESHOLDS

# SETUP

os.makedirs("output/charts", exist_ok=True)

if not os.path.exists(DB_PATH):
    print("ERROR: No database found. Run 'python3 main.py --simulate' first.")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
patient_df = pd.read_sql("SELECT * FROM patient_readings ORDER BY timestamp", conn)
env_df = pd.read_sql("SELECT * FROM environment_readings ORDER BY timestamp", conn)
alert_df = pd.read_sql("SELECT * FROM alerts ORDER BY timestamp", conn)
conn.close()

patient_df["timestamp"] = pd.to_datetime(patient_df["timestamp"])
env_df["timestamp"] = pd.to_datetime(env_df["timestamp"])
alert_df["timestamp"] = pd.to_datetime(alert_df["timestamp"])

print("=" * 55)
print("  AURELIUS HEALTH CLINIC — Report Chart Generator")
print("=" * 55)
print("  Patient readings:     {}".format(len(patient_df)))
print("  Environment readings: {}".format(len(env_df)))
print("  Alerts:               {}".format(len(alert_df)))
print("-" * 55)

plt.style.use("seaborn-v0_8-whitegrid")
COLORS = ["#2196F3", "#FF5722", "#4CAF50", "#9C27B0", "#FF9800", "#00BCD4"]


# CHART 1: Heart Rate — 24h All Patients

fig, ax = plt.subplots(figsize=(12, 5))
for i, pid in enumerate(sorted(patient_df["patient_id"].unique())):
    pdf = patient_df[patient_df["patient_id"] == pid]
    ax.plot(pdf["timestamp"], pdf["heart_rate"], label=pid,
            color=COLORS[i], alpha=0.7, linewidth=0.8)
ax.axhline(y=100, color="orange", linestyle="--", linewidth=1, label="Warning (100 BPM)")
ax.axhline(y=120, color="red", linestyle="--", linewidth=1, label="Critical (120 BPM)")
ax.axhline(y=60, color="blue", linestyle="--", linewidth=1, label="Low (60 BPM)")
ax.set_title("Heart Rate Monitoring — 24-Hour Period", fontsize=13, fontweight="bold")
ax.set_xlabel("Time")
ax.set_ylabel("Heart Rate (BPM)")
ax.legend(loc="upper right", fontsize=8)
ax.set_ylim(40, 160)
plt.tight_layout()
plt.savefig("output/charts/01_heart_rate_24h.png", dpi=200)
plt.close()
print("  [1/8] Heart rate chart saved")


# CHART 2: SpO2 with Anomaly Markers

fig, ax = plt.subplots(figsize=(12, 5))
for i, pid in enumerate(sorted(patient_df["patient_id"].unique())):
    pdf = patient_df[patient_df["patient_id"] == pid]
    ax.plot(pdf["timestamp"], pdf["spo2"], label=pid,
            color=COLORS[i], alpha=0.7, linewidth=0.8)
    anomalies = pdf[pdf["is_anomaly"] == 1]
    if not anomalies.empty:
        ax.scatter(anomalies["timestamp"], anomalies["spo2"],
                   color="red", marker="x", s=30, zorder=5)
ax.axhline(y=94, color="orange", linestyle="--", linewidth=1, label="Warning (94%)")
ax.axhline(y=90, color="red", linestyle="--", linewidth=1, label="Critical (90%)")
ax.set_title("Blood Oxygen (SpO2) — Anomaly Events Highlighted", fontsize=13, fontweight="bold")
ax.set_xlabel("Time")
ax.set_ylabel("SpO2 (%)")
ax.legend(loc="lower right", fontsize=8)
ax.set_ylim(82, 101)
plt.tight_layout()
plt.savefig("output/charts/02_spo2_anomalies.png", dpi=200)
plt.close()
print("  [2/8] SpO2 anomaly chart saved")


# CHART 3: Single Patient Deep Dive (PAT-002 hypertension)

pat2 = patient_df[patient_df["patient_id"] == "PAT-002"]
fig, axes = plt.subplots(2, 3, figsize=(14, 7))
fig.suptitle("Patient PAT-002 (Hypertension) — Full Vital Signs", fontsize=13, fontweight="bold")

axes[0, 0].plot(pat2["timestamp"], pat2["heart_rate"], color=COLORS[0], linewidth=0.8)
axes[0, 0].axhline(y=100, color="orange", linestyle="--", linewidth=0.8)
axes[0, 0].set_title("Heart Rate (BPM)", fontsize=10)
axes[0, 0].set_ylim(50, 150)

axes[0, 1].plot(pat2["timestamp"], pat2["spo2"], color=COLORS[1], linewidth=0.8)
axes[0, 1].axhline(y=94, color="orange", linestyle="--", linewidth=0.8)
axes[0, 1].set_title("SpO2 (%)", fontsize=10)
axes[0, 1].set_ylim(85, 101)

axes[0, 2].plot(pat2["timestamp"], pat2["blood_pressure"], color=COLORS[2], linewidth=0.8)
axes[0, 2].axhline(y=140, color="orange", linestyle="--", linewidth=0.8)
axes[0, 2].axhline(y=160, color="red", linestyle="--", linewidth=0.8)
axes[0, 2].set_title("Blood Pressure (mmHg)", fontsize=10)
axes[0, 2].set_ylim(80, 200)

axes[1, 0].plot(pat2["timestamp"], pat2["glucose"], color=COLORS[3], linewidth=0.8)
axes[1, 0].axhline(y=140, color="orange", linestyle="--", linewidth=0.8)
axes[1, 0].axhline(y=180, color="red", linestyle="--", linewidth=0.8)
axes[1, 0].set_title("Glucose (mg/dL)", fontsize=10)

axes[1, 1].plot(pat2["timestamp"], pat2["body_temp"], color=COLORS[4], linewidth=0.8)
axes[1, 1].axhline(y=37.5, color="orange", linestyle="--", linewidth=0.8)
axes[1, 1].set_title("Body Temperature (°C)", fontsize=10)
axes[1, 1].set_ylim(35.5, 38.5)

axes[1, 2].fill_between(pat2["timestamp"], pat2["motion"], color=COLORS[5], alpha=0.4)
axes[1, 2].set_title("Patient Activity", fontsize=10)
axes[1, 2].set_ylim(-0.1, 1.3)
axes[1, 2].set_yticks([0, 1])
axes[1, 2].set_yticklabels(["Still", "Moving"])

for ax in axes.flat:
    ax.tick_params(axis="x", rotation=30, labelsize=7)
plt.tight_layout()
plt.savefig("output/charts/03_patient_deep_dive.png", dpi=200)
plt.close()
print("  [3/8] Patient deep dive chart saved")


# CHART 4: Room CO2 and Temperature

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for i, rid in enumerate(sorted(env_df["room_id"].unique())):
    rdf = env_df[env_df["room_id"] == rid]
    axes[0].plot(rdf["timestamp"], rdf["co2"], label=rid, color=COLORS[i], alpha=0.7, linewidth=0.8)
    axes[1].plot(rdf["timestamp"], rdf["room_temp"], label=rid, color=COLORS[i], alpha=0.7, linewidth=0.8)

axes[0].axhline(y=1000, color="orange", linestyle="--", linewidth=1, label="Warning")
axes[0].axhline(y=1500, color="red", linestyle="--", linewidth=1, label="Danger")
axes[0].set_title("CO2 Levels Across Clinic Rooms", fontsize=12, fontweight="bold")
axes[0].set_ylabel("CO2 (ppm)")
axes[0].legend(fontsize=7)

axes[1].axhline(y=18, color="blue", linestyle="--", linewidth=1, label="Min (18°C)")
axes[1].axhline(y=26, color="red", linestyle="--", linewidth=1, label="Max (26°C)")
axes[1].set_title("Room Temperature Across Clinic", fontsize=12, fontweight="bold")
axes[1].set_ylabel("Temperature (°C)")
axes[1].legend(fontsize=7)

for ax in axes:
    ax.tick_params(axis="x", rotation=30, labelsize=8)
plt.tight_layout()
plt.savefig("output/charts/04_environment_co2_temp.png", dpi=200)
plt.close()
print("  [4/8] Environment CO2/temp chart saved")


# CHART 5: Medication Fridge Compliance

fig, ax = plt.subplots(figsize=(12, 5))
for i, rid in enumerate(sorted(env_df["room_id"].unique())):
    rdf = env_df[env_df["room_id"] == rid]
    ax.plot(rdf["timestamp"], rdf["med_fridge_temp"], label=rid, color=COLORS[i], alpha=0.7, linewidth=0.8)

ax.axhspan(2, 8, alpha=0.08, color="green")
ax.axhline(y=2, color="green", linestyle="--", linewidth=1)
ax.axhline(y=8, color="green", linestyle="--", linewidth=1)
ax.set_title("Medication Fridge Temperature — Compliance Monitoring", fontsize=13, fontweight="bold")
ax.set_xlabel("Time")
ax.set_ylabel("Temperature (°C)")
ax.legend(fontsize=8)

total = len(env_df)
breaches = len(env_df[(env_df["med_fridge_temp"] < 2) | (env_df["med_fridge_temp"] > 8)])
compliance_pct = round(((total - breaches) / total) * 100, 1)
ax.text(0.02, 0.95, "Compliance: {}% ({} breaches / {} readings)".format(compliance_pct, breaches, total),
        transform=ax.transAxes, fontsize=9, verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
plt.tight_layout()
plt.savefig("output/charts/05_med_fridge_compliance.png", dpi=200)
plt.close()
print("  [5/8] Medication fridge compliance chart saved")


# CHART 6: Alert Distribution

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

level_counts = alert_df["level"].value_counts()
colors_bar = ["#F44336" if x == "CRITICAL" else "#FF9800" for x in level_counts.index]
axes[0].bar(level_counts.index, level_counts.values, color=colors_bar)
axes[0].set_title("Alerts by Severity", fontsize=12, fontweight="bold")
axes[0].set_ylabel("Count")
for i, v in enumerate(level_counts.values):
    axes[0].text(i, v + 20, str(v), ha="center", fontsize=10, fontweight="bold")

metric_counts = alert_df["metric"].value_counts().head(10)
axes[1].barh(metric_counts.index, metric_counts.values, color="#2196F3")
axes[1].set_title("Top Alert-Generating Metrics", fontsize=12, fontweight="bold")
axes[1].set_xlabel("Count")
axes[1].invert_yaxis()
plt.tight_layout()
plt.savefig("output/charts/06_alert_distribution.png", dpi=200)
plt.close()
print("  [6/8] Alert distribution chart saved")


# CHART 7: Hourly Alert Pattern

alert_df["hour"] = alert_df["timestamp"].dt.hour
hourly = alert_df.groupby(["hour", "level"]).size().unstack(fill_value=0)

fig, ax = plt.subplots(figsize=(12, 5))
hourly.plot(kind="bar", stacked=True, ax=ax,
            color={"CRITICAL": "#F44336", "WARNING": "#FF9800"}, width=0.8)
ax.set_title("Alert Frequency by Hour of Day", fontsize=13, fontweight="bold")
ax.set_xlabel("Hour of Day")
ax.set_ylabel("Number of Alerts")
ax.legend(fontsize=9)
ax.set_xticklabels(["{:02d}:00".format(h) for h in range(24)], rotation=45, fontsize=8)

peak_hour = hourly.sum(axis=1).idxmax()
peak_count = hourly.sum(axis=1).max()
ax.annotate("Peak: {:02d}:00\n({} alerts)".format(peak_hour, int(peak_count)),
            xy=(peak_hour, peak_count), xytext=(peak_hour + 2, peak_count + 10),
            arrowprops=dict(arrowstyle="->", color="black"), fontsize=9, fontweight="bold")
plt.tight_layout()
plt.savefig("output/charts/07_hourly_alert_pattern.png", dpi=200)
plt.close()
print("  [7/8] Hourly alert pattern chart saved")


# CHART 8: Patient Comparison Box Plot

fig, axes = plt.subplots(1, 4, figsize=(14, 5))
fig.suptitle("Patient Vital Signs Distribution — Comparison by Condition", fontsize=13, fontweight="bold")

metrics = [
    ("heart_rate", "Heart Rate (BPM)", axes[0]),
    ("spo2", "SpO2 (%)", axes[1]),
    ("blood_pressure", "Blood Pressure (mmHg)", axes[2]),
    ("glucose", "Glucose (mg/dL)", axes[3]),
]

for metric, title, ax in metrics:
    data_by_patient = []
    labels = []
    for pid in sorted(patient_df["patient_id"].unique()):
        data_by_patient.append(patient_df[patient_df["patient_id"] == pid][metric].values)
        labels.append(pid)
    bp = ax.boxplot(data_by_patient, labels=labels, patch_artist=True)
    for patch, color in zip(bp["boxes"], COLORS[:3]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_title(title, fontsize=10)
    ax.tick_params(axis="x", rotation=30, labelsize=8)
plt.tight_layout()
plt.savefig("output/charts/08_patient_comparison_boxplot.png", dpi=200)
plt.close()
print("  [8/8] Patient comparison chart saved")


# STATISTICAL SUMMARY

print("\n" + "=" * 55)
print("  STATISTICAL SUMMARY FOR REPORT")
print("=" * 55)

print("\n--- Patient Vitals (all patients) ---")
for metric in ["heart_rate", "spo2", "blood_pressure", "glucose", "body_temp"]:
    mean = patient_df[metric].mean()
    std = patient_df[metric].std()
    min_v = patient_df[metric].min()
    max_v = patient_df[metric].max()
    print("  {:<18s} mean={:>7.1f}  std={:>6.1f}  min={:>7.1f}  max={:>7.1f}".format(
        metric, mean, std, min_v, max_v))

print("\n--- Per Patient ---")
for pid in sorted(patient_df["patient_id"].unique()):
    pdf = patient_df[patient_df["patient_id"] == pid]
    anomalies = len(pdf[pdf["is_anomaly"] == 1])
    print("  {} — HR avg={:.0f} | SpO2 avg={:.1f}% | BP avg={:.0f} | Anomalies={}".format(
        pid, pdf["heart_rate"].mean(), pdf["spo2"].mean(),
        pdf["blood_pressure"].mean(), anomalies))

print("\n--- Environment (all rooms) ---")
for metric in ["room_temp", "humidity", "co2", "pm25", "noise", "med_fridge_temp"]:
    mean = env_df[metric].mean()
    std = env_df[metric].std()
    min_v = env_df[metric].min()
    max_v = env_df[metric].max()
    print("  {:<18s} mean={:>7.1f}  std={:>6.1f}  min={:>7.1f}  max={:>7.1f}".format(
        metric, mean, std, min_v, max_v))

print("\n--- Medication Fridge Compliance ---")
total = len(env_df)
breaches = len(env_df[(env_df["med_fridge_temp"] < 2) | (env_df["med_fridge_temp"] > 8)])
print("  Total readings: {}".format(total))
print("  Breaches:       {} ({:.1f}%)".format(breaches, (breaches / total) * 100))
print("  Compliance:     {:.1f}%".format(((total - breaches) / total) * 100))

print("\n--- Alerts Summary ---")
print("  Total alerts:    {}".format(len(alert_df)))
print("  CRITICAL:        {}".format(len(alert_df[alert_df["level"] == "CRITICAL"])))
print("  WARNING:         {}".format(len(alert_df[alert_df["level"] == "WARNING"])))
print("\n  Top 5 alert metrics:")
for metric, count in alert_df["metric"].value_counts().head(5).items():
    print("    {:<18s} {}".format(metric, count))

print("\n  Charts saved to: output/charts/")
print("=" * 55)