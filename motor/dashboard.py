import os
import sys
import time
from html import escape
from pathlib import Path

import requests
import streamlit as st

# Streamlit adds the script directory to sys.path. Add the project root so the
# package imports also work when Render launches motor/dashboard.py directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from motor.feature_extractor import extract_features
from motor.agent_policy import AGENTIC_AI_ON, AGENTIC_AI_OPTIONS, AGENTIC_DECISION_RULES
from motor.genai_supervisor import guardian_mode_help, run_guardian_cycle
from motor.maintenance_recommendations import build_recommendations
from motor.motor_ai import predict_motor_health
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
    .recommendation-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 6px solid #10b981;
        border-radius: 14px;
        padding: 14px 16px;
        margin: 10px 0;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05);
    }
    .recommendation-critical { border-left-color: #ef4444; }
    .recommendation-warning { border-left-color: #f59e0b; }
    .recommendation-normal { border-left-color: #10b981; }
    .recommendation-severity {
        color: #475569;
        font-size: 0.75rem;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .recommendation-part {
        color: #0f172a;
        font-size: 1.05rem;
        font-weight: 750;
        margin-top: 3px;
    }
    .recommendation-text { color: #334155; margin-top: 7px; }
    .recommendation-fix { color: #0f172a; margin-top: 7px; font-weight: 600; }
    .guardian-card {
        background: linear-gradient(135deg, #eef2ff 0%, #ecfeff 100%);
        border: 1px solid #c7d2fe;
        border-radius: 16px;
        padding: 16px 18px;
        margin: 10px 0;
    }
    .guardian-action {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 10px 12px;
        margin: 8px 0;
    }
    .guardian-critical { border-left: 5px solid #ef4444; }
    .guardian-warning { border-left: 5px solid #f59e0b; }
    .guardian-normal { border-left: 5px solid #10b981; }
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
        "stator_temp_c": state.stator_temp_c,
        "rotor_temp_c": state.rotor_temp_c,
        "magnet_temp_c": state.magnet_temp_c,
        "bearing_temp_c": state.bearing_temp_c,
        "coolant_in_temp_c": state.coolant_in_temp_c,
        "coolant_out_temp_c": state.coolant_out_temp_c,
        "rul_hours": state.rul_hours,
    }


def local_prediction(state, reason):
    features = extract_features(state)
    features["detected_fault_code"] = state.fault_code
    result = predict_motor_health(features)
    result["deployment_mode"] = "local_fallback"
    result["fallback_reason"] = reason
    return result


def request_prediction(state):
    if not API_KEY:
        raise RuntimeError("APP_API_KEY is not configured for the dashboard service.")

    # Wake Render's free API service before loading the model. A sleeping or
    # restarting instance can briefly return 502/503/504 during a cold start.
    transient_statuses = {502, 503, 504}
    try:
        requests.get(f"{API_BASE_URL}/health", timeout=120)
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
                result = last_response.json()["ml_prediction"]
                result["deployment_mode"] = "cloud_api"
                return result
            if attempt < 3:
                time.sleep(3 * (attempt + 1))

        return local_prediction(
            state,
            f"Render returned HTTP {last_response.status_code} after retries.",
        )
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code in {401, 403}:
            raise
        return local_prediction(state, str(error))
    except requests.RequestException as error:
        return local_prediction(state, str(error))


def live_recommendations(state):
    features = extract_features(state)
    features["fault_code"] = state.fault_code
    return build_recommendations(features, fault_code=state.fault_code)


def render_recommendations(recommendations):
    for recommendation in recommendations:
        severity = recommendation.get("severity", "normal")
        st.markdown(
            f"""
            <div class="recommendation-card recommendation-{escape(severity)}">
                <div class="recommendation-severity">{escape(severity)}</div>
                <div class="recommendation-part">{escape(recommendation.get('part', 'Motor system'))}</div>
                <div class="recommendation-text"><b>Action:</b> {escape(recommendation.get('action', 'Continue monitoring.'))}</div>
                <div class="recommendation-text"><b>Reason:</b> {escape(recommendation.get('issue', 'No issue detected.'))}</div>
                <div class="recommendation-fix">Fix: {escape(recommendation.get('fix', 'No repair is required right now.'))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_driver_warnings(warnings):
    if not warnings:
        st.success("Driving inputs look smooth and safe.")
        return

    for warning in warnings:
        severity = warning.get("severity", "warning")
        st.markdown(
            f"""
            <div class="guardian-action guardian-{escape(severity)}">
                <b>{escape(warning.get('title', 'Driving warning'))}</b><br>
                {escape(warning.get('message', 'Input behavior needs attention.'))}<br>
                <span class="small-note">Do this: {escape(warning.get('corrective_action', 'Drive smoothly.'))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_guardian_actions(actions):
    applied = [action for action in actions if action.get("allowed", True)]
    advisory = [action for action in actions if not action.get("allowed", True)]

    if not applied and not advisory:
        st.success("Guardian is observing. No control action is needed right now.")
        return

    for action in applied + advisory:
        severity = action.get("severity", "normal")
        status = "Applied" if action.get("allowed", True) else "Advisory only"
        value = action.get("value")
        value_text = "" if value is None else f" Value: {value}"
        st.markdown(
            f"""
            <div class="guardian-action guardian-{escape(severity)}">
                <b>{escape(status)} - {escape(action.get('type', 'guardian_action'))}</b><br>
                {escape(action.get('reason', 'Guardian action.'))}<br>
                <span class="small-note">{escape(value_text)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


if "state" not in st.session_state:
    st.session_state.state = new_motor_state()
if "running" not in st.session_state:
    st.session_state.running = False
if "ai_output" not in st.session_state:
    st.session_state.ai_output = None
if "last_update_time" not in st.session_state:
    st.session_state.last_update_time = time.monotonic()

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
    agentic_ai = st.selectbox(
        "Agentic AI",
        AGENTIC_AI_OPTIONS,
        index=AGENTIC_AI_OPTIONS.index(getattr(state, "guardian_mode", AGENTIC_AI_ON)),
        help="Turn autonomous motor protection ON or OFF.",
    )
    st.caption(guardian_mode_help(agentic_ai))

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
    st.write(f"Agentic AI: {agentic_ai}")
    st.write("🟢 Motor running" if st.session_state.running else "⚪ Motor stopped")
    st.write("🟢 Prediction API" if cloud_online else "🟠 API starting")
    st.caption(f"Endpoint: {API_BASE_URL}")

if start:
    st.session_state.running = True
    st.session_state.last_update_time = time.monotonic()

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
    st.session_state.last_update_time = time.monotonic()
    st.rerun()

if st.session_state.running:
    now = time.monotonic()
    dt_s = max(0.10, min(now - st.session_state.last_update_time, 1.0))
    st.session_state.last_update_time = now

    guardian_result = run_guardian_cycle(
        state,
        accelerator,
        brake,
        agentic_ai,
        dt_s,
    )
    controls = guardian_result["controls"]

    target_torque = controls["target_torque_nm"]
    state.torque_nm += (target_torque - state.torque_nm) * min(0.28, dt_s / 1.2)

    if state.effective_brake_pct > 0 and state.vehicle_speed_kmph < 5:
        state.torque_nm = 0

    state = update_motor_physics(state, dt_s=dt_s)
    state = update_motor_thermal(state, state.total_loss_w, dt_s=dt_s)
    state = update_motor_health(state)
    state = update_faults(state)
    state = update_rul(state, dt_hours=dt_s / 3600)
    st.session_state.state = state
else:
    state.guardian_mode = agentic_ai

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

if state.failure_probability >= 50:
    st.error(
        f"Critical fault risk ({state.fault_code}): stop the motor and inspect immediately."
    )
elif state.failure_probability > 0 or state.overall_health < 80:
    st.warning("Motor degradation detected: schedule an inspection.")
else:
    st.success("Healthy motor: all monitored systems are operating normally.")

st.markdown('<div class="section-title">Agentic EV Motor Guardian</div>', unsafe_allow_html=True)
guardian_metrics = st.columns(4)
guardian_metrics[0].metric("Effective Accelerator", f"{state.effective_accelerator_pct:.0f}%")
guardian_metrics[1].metric("Effective Brake", f"{state.effective_brake_pct:.0f}%")
guardian_metrics[2].metric("Torque Limit", f"{state.torque_limit_pct:.0f}%")
guardian_metrics[3].metric("Speed Limit", f"{state.speed_limit_kmph:.0f} km/h")
cooling_metrics = st.columns(3)
cooling_metrics[0].metric("Cooling Flow", f"{state.coolant_flow_rate:.2f}x")
cooling_metrics[1].metric("Cooling Boost", "ON" if state.cooling_boost_active else "OFF")
cooling_metrics[2].metric("Limp Mode", "ON" if state.limp_mode_active else "OFF")
st.markdown(
    f"""
    <div class="guardian-card">
        <b>{escape(state.guardian_mode)}</b><br>
        {escape(state.guardian_explanation)}
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">Driving Behavior Warnings</div>', unsafe_allow_html=True)
render_driver_warnings(state.driver_warnings)

st.markdown('<div class="section-title">Guardian Actions</div>', unsafe_allow_html=True)
render_guardian_actions(state.guardian_actions)

st.markdown('<div class="section-title">Agentic AI Decision Rules</div>', unsafe_allow_html=True)
st.table(AGENTIC_DECISION_RULES)

st.markdown('<div class="section-title">Recommended Action</div>', unsafe_allow_html=True)
render_recommendations(live_recommendations(state))

st.markdown('<div class="section-title">◎ ML Predictive Maintenance</div>', unsafe_allow_html=True)
prediction = st.session_state.ai_output
if not prediction:
    st.info("Press 'Predict ML Health' to analyze the current motor state with your deployed model.")
elif "error" in prediction:
    st.error(f"Prediction failed: {prediction['error']}")
else:
    confidence = prediction.get("confidence")
    confidence_text = "N/A" if confidence is None else f"{confidence * 100:.1f}%"
    diagnosis_source = prediction.get("diagnosis_source", "random_forest")
    if diagnosis_source == "safety_rules":
        model_confidence = prediction.get("model_confidence")
        model_confidence_text = (
            "N/A" if model_confidence is None else f"{model_confidence * 100:.1f}%"
        )
        diagnosis_detail = (
            "Safety-rule override · Random Forest: "
            f"{prediction.get('model_fault_code', 'UNKNOWN')} ({model_confidence_text})"
        )
    else:
        diagnosis_detail = f"Random Forest confidence: {confidence_text}"
    st.markdown(
        f"""
        <div class="prediction-card">
            <div class="prediction-label">Predicted motor condition</div>
            <div class="prediction-value">{prediction.get('fault_code', 'UNKNOWN')}</div>
            <p class="small-note">{diagnosis_detail}</p>
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
    if prediction.get("deployment_mode") == "local_fallback":
        st.warning(
            "Cloud API was temporarily unavailable. This result was computed "
            "with the same trained model on the dashboard server."
        )
    if anomalies:
        st.warning("Detected anomalies: " + ", ".join(anomalies))
    else:
        st.success("No anomalies detected by the trained model.")
    prediction_recommendations = prediction.get("recommendations", [])
    if prediction_recommendations:
        st.markdown(
            '<div class="section-title">ML Recommended Action</div>',
            unsafe_allow_html=True,
        )
        render_recommendations(prediction_recommendations)

st.caption("EV Motor Digital Twin · Physics + Thermal + Health + Random Forest ML + Agentic Guardian")

if st.session_state.running:
    time.sleep(0.45)
    st.rerun()
