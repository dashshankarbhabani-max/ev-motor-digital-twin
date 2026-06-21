import os
import sys
import time
from pathlib import Path

import requests
import streamlit as st

# Streamlit adds the script directory to sys.path. Add the project root so the
# package imports also work when Render launches motor/dashboard.py directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from motor.motor_faults import update_faults
from motor.motor_health import update_motor_health
from motor.motor_physics import update_motor_physics
from motor.motor_rul import update_rul
from motor.motor_state import MotorState
from motor.motor_thermal import update_motor_thermal


API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "https://ev-motor-digital-twin-api.onrender.com",
).rstrip("/")
API_KEY = os.getenv("APP_API_KEY", "")


st.set_page_config(
    page_title="EV Motor Digital Twin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --navy: #0b132b;
        --blue: #2563eb;
        --cyan: #06b6d4;
        --green: #10b981;
        --amber: #f59e0b;
        --red: #ef4444;
        --surface: #ffffff;
        --muted: #64748b;
    }
    .stApp { background: #f4f7fb; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b132b 0%, #14213d 100%);
    }
    [data-testid="stSidebar"] * { color: #f8fafc; }
    [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div {
        color: #38bdf8;
    }
    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05);
    }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stMetricValue"] { color: var(--navy); }
    .hero {
        background: linear-gradient(120deg, #0b132b 0%, #1d4ed8 70%, #0891b2 100%);
        border-radius: 20px;
        padding: 28px 32px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 16px 40px rgba(29, 78, 216, 0.20);
    }
    .hero h1 { margin: 0; font-size: 2.15rem; color: white; }
    .hero p { margin: 8px 0 0; color: #dbeafe; font-size: 1rem; }
    .status-pill {
        display: inline-block;
        margin-top: 14px;
        padding: 6px 12px;
        border-radius: 999px;
        background: rgba(16, 185, 129, 0.18);
        border: 1px solid rgba(110, 231, 183, 0.45);
        color: #d1fae5;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .section-title {
        color: var(--navy);
        font-size: 1.35rem;
        font-weight: 750;
        margin: 18px 0 10px;
    }
    .prediction-card {
        background: linear-gradient(135deg, #eff6ff 0%, #ecfeff 100%);
        border: 1px solid #bfdbfe;
        border-radius: 16px;
        padding: 20px 22px;
        margin-top: 8px;
    }
    .prediction-label { color: #475569; font-size: 0.8rem; text-transform: uppercase; }
    .prediction-value { color: #0f172a; font-size: 1.35rem; font-weight: 750; }
    .small-note { color: #64748b; font-size: 0.82rem; }
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def new_motor_state():
    return MotorState(
        voltage_v=400,
        current_a=0,
        speed_rpm=0,
        vehicle_speed_kmph=0,
        battery_soc=100,
        torque_nm=0,
        flux_estimate=0.8,
        coolant_flow_rate=1.0,
        vibration_accel=0.5,
        vibration_vel=1.0,
        rul_hours=20000,
    )


@st.cache_data(ttl=30, show_spinner=False)
def api_is_healthy():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        return response.ok
    except requests.RequestException:
        return False


def prediction_payload(state):
    return {
        "voltage_v": state.voltage_v,
        "current_a": state.current_a,
        "speed_rpm": state.speed_rpm,
        "torque_nm": state.torque_nm,
        "flux_estimate": state.flux_estimate,
        "vehicle_speed_kmph": state.vehicle_speed_kmph,
        "battery_soc": state.battery_soc,
        "coolant_flow_rate": state.coolant_flow_rate,
        "vibration_accel": state.vibration_accel,
        "vibration_vel": state.vibration_vel,
        "current_harmonics": state.current_harmonics,
        "insulation_resistance_mohm": state.insulation_resistance_mohm,
        "partial_discharge": state.partial_discharge,
        "rul_hours": state.rul_hours,
    }


def request_prediction(state):
    if not API_KEY:
        raise RuntimeError("APP_API_KEY is not configured for the dashboard service.")

    # Wake Render's free API service before loading the model. A sleeping or
    # restarting instance can briefly return 502/503/504 during a cold start.
    requests.get(f"{API_BASE_URL}/health", timeout=120)

    transient_statuses = {502, 503, 504}
    last_response = None
    for attempt in range(4):
        last_response = requests.post(
            f"{API_BASE_URL}/predict",
            headers={"X-API-Key": API_KEY},
            json=prediction_payload(state),
            timeout=120,
        )
        if last_response.status_code not in transient_statuses:
            last_response.raise_for_status()
            return last_response.json()["ml_prediction"]
        if attempt < 3:
            time.sleep(3 * (attempt + 1))

    raise RuntimeError(
        "The prediction service is still starting. Please retry in one minute "
        f"(Render returned HTTP {last_response.status_code})."
    )


if "state" not in st.session_state:
    st.session_state.state = new_motor_state()
if "running" not in st.session_state:
    st.session_state.running = False
if "ai_output" not in st.session_state:
    st.session_state.ai_output = None

state = st.session_state.state
cloud_online = api_is_healthy()

st.markdown(
    f"""
    <div class="hero">
        <h1>⚡ EV Motor Digital Twin</h1>
        <p>Real-time simulation and machine-learning predictive maintenance</p>
        <span class="status-pill">{'● CLOUD API ONLINE' if cloud_online else '● CLOUD API WAKING UP'}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## 🚗 Vehicle Controls")
    st.caption("Drive the virtual EV motor and monitor its condition.")
    accelerator = st.slider("Accelerator (%)", 0, 100, 0)
    brake = st.slider("Brake (%)", 0, 100, 0)

    start_col, stop_col = st.columns(2)
    start = start_col.button("▶ Start", use_container_width=True)
    stop = stop_col.button("■ Stop", use_container_width=True)
    reset = st.button("↻ Reset Simulation", use_container_width=True)
    predict = st.button(
        "◎ Predict ML Health",
        type="primary",
        use_container_width=True,
    )

    st.divider()
    st.markdown("### System")
    st.write("🟢 Motor running" if st.session_state.running else "⚪ Motor stopped")
    st.write("🟢 Prediction API" if cloud_online else "🟠 API starting")
    st.caption(f"Endpoint: {API_BASE_URL}")

if start:
    st.session_state.running = True

if stop:
    st.session_state.running = False
    state.speed_rpm = 0
    state.vehicle_speed_kmph = 0
    state.filtered_torque = 0
    state.torque_nm = 0
    state.current_a = 0

if reset:
    st.session_state.state = new_motor_state()
    st.session_state.running = False
    st.session_state.ai_output = None
    st.rerun()

if st.session_state.running:
    target_torque = accelerator * 2.0
    state.torque_nm += (target_torque - state.torque_nm) * 0.08
    state.current_a = abs(state.torque_nm) * 1.4

    if brake > 0:
        state.torque_nm = -80 * (brake / 100)
        if state.vehicle_speed_kmph < 5:
            state.torque_nm = 0

    state = update_motor_physics(state, dt_s=0.1)
    state = update_motor_thermal(state, state.total_loss_w, dt_s=0.1)
    state = update_motor_health(state)
    state = update_faults(state)
    state = update_rul(state, dt_hours=0.1 / 3600)
    st.session_state.state = state

if predict:
    try:
        with st.spinner("Running your trained model on Render..."):
            st.session_state.ai_output = request_prediction(state)
        st.toast("Prediction completed", icon="✅")
    except (requests.RequestException, RuntimeError, KeyError) as error:
        st.session_state.ai_output = {"error": str(error)}

st.markdown('<div class="section-title">🔋 Live Motor Metrics</div>', unsafe_allow_html=True)
row_one = st.columns(4)
row_one[0].metric("Voltage", f"{state.voltage_v:.1f} V")
row_one[1].metric("Current", f"{state.current_a:.1f} A")
row_one[2].metric("Motor Speed", f"{state.speed_rpm:,.0f} RPM")
row_one[3].metric("Torque", f"{state.torque_nm:.1f} Nm")

row_two = st.columns(4)
row_two[0].metric("Vehicle Speed", f"{state.vehicle_speed_kmph:.1f} km/h")
row_two[1].metric("Battery SOC", f"{state.battery_soc:.1f}%")
row_two[2].metric("Power", f"{state.power_kw:.2f} kW")
row_two[3].metric("Efficiency", f"{state.efficiency * 100:.1f}%")

st.markdown('<div class="section-title">🌡️ Thermal Condition</div>', unsafe_allow_html=True)
thermal = st.columns(4)
thermal[0].metric("Stator", f"{state.stator_temp_c:.1f} °C")
thermal[1].metric("Rotor", f"{state.rotor_temp_c:.1f} °C")
thermal[2].metric("Magnet", f"{state.magnet_temp_c:.1f} °C")
thermal[3].metric("Bearing", f"{state.bearing_temp_c:.1f} °C")

st.markdown('<div class="section-title">❤️ Health & Maintenance</div>', unsafe_allow_html=True)
health = st.columns(3)
health[0].metric("Overall Health", f"{state.overall_health:.2f}%")
health[1].metric("Failure Probability", f"{state.failure_probability:.2f}%")
health[2].metric("Remaining Useful Life", f"{state.rul_hours:,.0f} h")

if state.overall_health >= 80:
    st.success("Healthy motor: all monitored systems are operating normally.")
elif state.overall_health >= 50:
    st.warning("Motor degradation detected: schedule an inspection.")
else:
    st.error("Critical condition: stop the motor and inspect immediately.")

st.markdown('<div class="section-title">◎ ML Predictive Maintenance</div>', unsafe_allow_html=True)
prediction = st.session_state.ai_output
if not prediction:
    st.info("Press 'Predict ML Health' to analyze the current motor state with your deployed model.")
elif "error" in prediction:
    st.error(f"Prediction failed: {prediction['error']}")
else:
    confidence = prediction.get("confidence")
    confidence_text = "N/A" if confidence is None else f"{confidence * 100:.1f}%"
    st.markdown(
        f"""
        <div class="prediction-card">
            <div class="prediction-label">Predicted motor condition</div>
            <div class="prediction-value">{prediction.get('fault_code', 'UNKNOWN')}</div>
            <p class="small-note">Model confidence: {confidence_text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    prediction_metrics = st.columns(3)
    prediction_metrics[0].metric(
        "Predicted Health",
        f"{prediction.get('health_score', 0):.2f}%",
    )
    prediction_metrics[1].metric(
        "Predicted Failure Risk",
        f"{prediction.get('failure_probability', 0):.2f}%",
    )
    prediction_metrics[2].metric(
        "Predicted RUL",
        f"{prediction.get('rul_hours', 0):,.0f} h",
    )
    anomalies = prediction.get("anomalies", [])
    if anomalies:
        st.warning("Detected anomalies: " + ", ".join(anomalies))
    else:
        st.success("No anomalies detected by the trained model.")

st.caption("EV Motor Digital Twin · Physics + Thermal + Health + Random Forest ML")

if st.session_state.running:
    time.sleep(0.12)
    st.rerun()
