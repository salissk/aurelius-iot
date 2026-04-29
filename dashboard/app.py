"""
Aurelius Health Clinic — IoT Dashboard (Compact)
Displays both domains: Patient Monitoring + Environment Monitoring
Run: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import os

st.set_page_config(
    page_title="Aurelius Health Clinic",
    layout="wide",
    page_icon="🏥"
)

# Compact styling
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    h1 {font-size: 1.6rem !important; margin-bottom: 0 !important;}
    h2 {font-size: 1.2rem !important;}
    h3 {font-size: 1.05rem !important;}
    .stMetric {padding: 8px 0 !important;}
    .stMetric label {font-size: 0.75rem !important;}
    .stMetric [data-testid="stMetricValue"] {font-size: 1.3rem !important;}
    .stTabs [data-baseweb="tab-list"] {gap: 2px;}
    .stTabs [data-baseweb="tab"] {padding: 6px 16px;}
    div[data-testid="stVerticalBlock"] > div {padding: 0;}
</style>
""", unsafe_allow_html=True)

DB_PATH = "data/aurelius_iot.db"

@st.cache_data(ttl=5)
def load_patient_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM patient_readings ORDER BY timestamp", conn)
    conn.close()
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

@st.cache_data(ttl=5)
def load_environment_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM environment_readings ORDER BY timestamp", conn)
    conn.close()
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

@st.cache_data(ttl=5)
def load_alerts():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM alerts ORDER BY timestamp DESC", conn)
    conn.close()
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


st.title("🏥 Aurelius Health Clinic — IoT Dashboard")

patient_df = load_patient_data()
env_df = load_environment_data()
alert_df = load_alerts()

if patient_df.empty and env_df.empty:
    st.warning("No data. Run: `python3 src/data_receiver.py --simulate` then refresh.")
    st.stop()

critical = len(alert_df[alert_df["level"] == "CRITICAL"]) if not alert_df.empty else 0
warnings = len(alert_df[alert_df["level"] == "WARNING"]) if not alert_df.empty else 0
patients_count = patient_df["patient_id"].nunique() if not patient_df.empty else 0
rooms_count = env_df["room_id"].nunique() if not env_df.empty else 0

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Patients", patients_count)
m2.metric("Rooms", rooms_count)
m3.metric("Patient Readings", len(patient_df))
m4.metric("Env Readings", len(env_df))
m5.metric("Critical", critical)
m6.metric("Warnings", warnings)


tab1, tab2, tab3, tab4 = st.tabs(["👤 Patients", "🌡️ Environment", "🚨 Alerts", "📊 Analytics"])

# --- TAB 1: Patient Monitoring ---
with tab1:
    if not patient_df.empty:
        col_select, col_metric = st.columns([1, 1])
        with col_select:
            selected_patient = st.selectbox("Patient", sorted(patient_df["patient_id"].unique()), label_visibility="collapsed")
        with col_metric:
            compare_metric = st.selectbox("Compare", ["heart_rate", "spo2", "blood_pressure", "glucose", "body_temp"], label_visibility="collapsed")

        pdf = patient_df[patient_df["patient_id"] == selected_patient]
        latest = pdf.iloc[-1]

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("HR", "{} BPM".format(int(latest["heart_rate"])))
        c2.metric("SpO2", "{}%".format(latest["spo2"]))
        c3.metric("BP", "{} mmHg".format(int(latest["blood_pressure"])))
        c4.metric("Glucose", "{} mg/dL".format(int(latest["glucose"])))
        c5.metric("Temp", "{}°C".format(latest["body_temp"]))

        chart_left, chart_right = st.columns(2)

        with chart_left:
            fig_hr = px.line(pdf, x="timestamp", y="heart_rate",
                             title="Heart Rate — {}".format(selected_patient))
            fig_hr.add_hline(y=100, line_dash="dash", line_color="orange")
            fig_hr.add_hline(y=120, line_dash="dash", line_color="red")
            fig_hr.add_hline(y=60, line_dash="dash", line_color="blue")
            fig_hr.update_layout(height=280, margin=dict(t=30, b=20, l=40, r=10),
                                 showlegend=False, xaxis_title="", yaxis_title="BPM")
            st.plotly_chart(fig_hr, use_container_width=True)

        with chart_right:
            fig_compare = px.line(patient_df, x="timestamp", y=compare_metric,
                                  color="patient_id",
                                  title="{} — All Patients".format(compare_metric.replace("_", " ").title()))
            fig_compare.update_layout(height=280, margin=dict(t=30, b=20, l=40, r=10),
                                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fig_compare, use_container_width=True)

        fig_vitals = make_subplots(rows=1, cols=4,
                                    subplot_titles=["SpO2 (%)", "BP (mmHg)", "Glucose (mg/dL)", "Temp (°C)"])
        fig_vitals.add_trace(go.Scatter(x=pdf["timestamp"], y=pdf["spo2"],
                                         line=dict(color="#2196F3", width=1)), row=1, col=1)
        fig_vitals.add_trace(go.Scatter(x=pdf["timestamp"], y=pdf["blood_pressure"],
                                         line=dict(color="#FF5722", width=1)), row=1, col=2)
        fig_vitals.add_trace(go.Scatter(x=pdf["timestamp"], y=pdf["glucose"],
                                         line=dict(color="#9C27B0", width=1)), row=1, col=3)
        fig_vitals.add_trace(go.Scatter(x=pdf["timestamp"], y=pdf["body_temp"],
                                         line=dict(color="#4CAF50", width=1)), row=1, col=4)
        fig_vitals.update_layout(height=220, margin=dict(t=30, b=20, l=40, r=10),
                                  showlegend=False)
        st.plotly_chart(fig_vitals, use_container_width=True)

# --- TAB 2: Environment Monitoring ---
with tab2:
    if not env_df.empty:
        selected_room = st.selectbox("Room", sorted(env_df["room_id"].unique()), label_visibility="collapsed")
        rdf = env_df[env_df["room_id"] == selected_room]
        latest_env = rdf.iloc[-1]

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Temp", "{}°C".format(latest_env["room_temp"]))
        c2.metric("Humidity", "{}%".format(latest_env["humidity"]))
        c3.metric("CO2", "{} ppm".format(int(latest_env["co2"])))
        c4.metric("PM2.5", "{}".format(latest_env["pm25"]))
        c5.metric("Noise", "{} dB".format(latest_env["noise"]))
        c6.metric("Fridge", "{}°C".format(latest_env["med_fridge_temp"]))

        fig_env = make_subplots(rows=2, cols=3,
                                 subplot_titles=["Room Temp (°C)", "Humidity (%)", "CO2 (ppm)",
                                                  "PM2.5 (µg/m³)", "Noise (dB)", "Med Fridge (°C)"])
        fig_env.add_trace(go.Scatter(x=rdf["timestamp"], y=rdf["room_temp"],
                                      line=dict(color="#FF5722", width=1)), row=1, col=1)
        fig_env.add_trace(go.Scatter(x=rdf["timestamp"], y=rdf["humidity"],
                                      line=dict(color="#2196F3", width=1)), row=1, col=2)
        fig_env.add_trace(go.Scatter(x=rdf["timestamp"], y=rdf["co2"],
                                      line=dict(color="#FF9800", width=1)), row=1, col=3)
        fig_env.add_trace(go.Scatter(x=rdf["timestamp"], y=rdf["pm25"],
                                      line=dict(color="#9C27B0", width=1)), row=2, col=1)
        fig_env.add_trace(go.Scatter(x=rdf["timestamp"], y=rdf["noise"],
                                      line=dict(color="#607D8B", width=1)), row=2, col=2)
        fig_env.add_trace(go.Scatter(x=rdf["timestamp"], y=rdf["med_fridge_temp"],
                                      line=dict(color="#00BCD4", width=1)), row=2, col=3)
        fig_env.update_layout(height=380, margin=dict(t=30, b=20, l=40, r=10),
                               showlegend=False)
        st.plotly_chart(fig_env, use_container_width=True)

        col_fridge, col_rooms = st.columns(2)
        with col_fridge:
            fig_f = px.line(env_df, x="timestamp", y="med_fridge_temp",
                            color="room_id", title="Fridge Compliance (2-8°C)")
            fig_f.add_hrect(y0=2, y1=8, fillcolor="green", opacity=0.08)
            fig_f.add_hline(y=2, line_dash="dash", line_color="green")
            fig_f.add_hline(y=8, line_dash="dash", line_color="green")
            fig_f.update_layout(height=260, margin=dict(t=30, b=20, l=40, r=10),
                                 legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fig_f, use_container_width=True)
        with col_rooms:
            fig_co2 = px.box(env_df, x="room_id", y="co2", color="room_id",
                              title="CO2 by Room")
            fig_co2.update_layout(height=260, margin=dict(t=30, b=20, l=40, r=10),
                                   showlegend=False)
            st.plotly_chart(fig_co2, use_container_width=True)

# --- TAB 3: Alerts ---
with tab3:
    if not alert_df.empty:
        col_pie, col_bar = st.columns(2)
        with col_pie:
            fig_pie = px.pie(alert_df, names="level", title="By Severity",
                              color="level",
                              color_discrete_map={"CRITICAL": "#F44336", "WARNING": "#FF9800"})
            fig_pie.update_layout(height=260, margin=dict(t=30, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_bar:
            fig_bar = px.histogram(alert_df, x="metric", color="level",
                                    title="By Metric",
                                    color_discrete_map={"CRITICAL": "#F44336", "WARNING": "#FF9800"})
            fig_bar.update_layout(height=260, margin=dict(t=30, b=20, l=40, r=10))
            st.plotly_chart(fig_bar, use_container_width=True)

        fig_tl = px.scatter(alert_df, x="timestamp", y="metric", color="level",
                             title="Alert Timeline",
                             color_discrete_map={"CRITICAL": "#F44336", "WARNING": "#FF9800"},
                             hover_data=["message", "source_id", "value"])
        fig_tl.update_layout(height=250, margin=dict(t=30, b=20, l=40, r=10))
        st.plotly_chart(fig_tl, use_container_width=True)

        level_filter = st.multiselect("Filter", ["CRITICAL", "WARNING"],
                                       default=["CRITICAL", "WARNING"], label_visibility="collapsed")
        filtered = alert_df[alert_df["level"].isin(level_filter)]
        st.dataframe(filtered.head(50), use_container_width=True, height=250)

# --- TAB 4: Analytics ---
with tab4:
    if not patient_df.empty and not env_df.empty:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("**Patient Vitals Summary**")
            stats = patient_df[["heart_rate", "spo2", "blood_pressure", "glucose", "body_temp"]].describe()
            st.dataframe(stats.round(2), use_container_width=True, height=200)
        with col_s2:
            st.markdown("**Environment Summary**")
            env_stats = env_df[["room_temp", "humidity", "co2", "pm25", "noise", "med_fridge_temp"]].describe()
            st.dataframe(env_stats.round(2), use_container_width=True, height=200)

        col_anom, col_hourly = st.columns(2)
        with col_anom:
            anomalies = patient_df[patient_df["is_anomaly"] == 1]
            if not anomalies.empty:
                fig_anom = px.scatter(anomalies, x="timestamp", y="heart_rate",
                                      color="patient_id", size="blood_pressure",
                                      title="Anomaly Events ({})".format(len(anomalies)))
                fig_anom.update_layout(height=280, margin=dict(t=30, b=20, l=40, r=10),
                                        legend=dict(orientation="h", yanchor="bottom", y=1.02))
                st.plotly_chart(fig_anom, use_container_width=True)
        with col_hourly:
            if not alert_df.empty:
                adf = alert_df.copy()
                adf["hour"] = adf["timestamp"].dt.hour
                hourly = adf.groupby(["hour", "level"]).size().reset_index(name="count")
                fig_h = px.bar(hourly, x="hour", y="count", color="level",
                                title="Alerts by Hour",
                                color_discrete_map={"CRITICAL": "#F44336", "WARNING": "#FF9800"})
                fig_h.update_layout(height=280, margin=dict(t=30, b=20, l=40, r=10))
                st.plotly_chart(fig_h, use_container_width=True)

st.caption("Aurelius Health Clinic IoT — CPS6008 | St Mary's University | 2 Domains | 16 Devices | 2 ESP32s")