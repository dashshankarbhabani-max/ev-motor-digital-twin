import streamlit as st
import time

from motor.motor_state import MotorState
from motor.motor_physics import update_motor_physics
from motor.motor_thermal import update_motor_thermal
from motor.motor_health import update_motor_health
from motor.motor_faults import update_faults
from motor.motor_rul import update_rul
from motor.motor_ai import predict_motor_health
from motor.feature_extractor import extract_features

if "running" not in st.session_state:
    st.session_state.running = False

# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="EV Motor Digital Twin",
    layout="wide"
)

st.title("⚡ EV Motor Digital Twin Dashboard")


# =====================================
# SESSION STATE
# =====================================
if "state" not in st.session_state:
    st.session_state.state = MotorState(
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
        rul_hours=20000
    )

if "running" not in st.session_state:
    st.session_state.running = False

if "ai_output" not in st.session_state:
    st.session_state.ai_output = None

state = st.session_state.state


# =====================================
# SIDEBAR CONTROLS
# =====================================
st.sidebar.header("🚗 Vehicle Controls")

accelerator = st.sidebar.slider(
    "Accelerator (%)",
    0,
    100,
    0
)

brake = st.sidebar.slider(
    "Brake (%)",
    0,
    100,
    0
)

start = st.sidebar.button("▶ Start")
stop = st.sidebar.button("⏹ Stop")
reset = st.sidebar.button("🔄 Reset")
predict = st.sidebar.button("🤖 Predict AI Health")


# =====================================
# START / STOP
# =====================================
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
    st.session_state.state = MotorState(
        voltage_v=400,
        current_a=0,
        speed_rpm=0,
        torque_nm=0,
        vehicle_speed_kmph=0,
        battery_soc=100,
        flux_estimate=0.8,
        coolant_flow_rate=1.0,
        vibration_accel=0.5,
        vibration_vel=1.0,
        rul_hours=20000
    )

    st.session_state.running = False
    st.session_state.ai_output = None
    st.rerun()


# =====================================
# MANUAL AI PREDICTION
# =====================================
if predict:
    try:
        features = extract_features(state)
        st.session_state.ai_output = (
            predict_motor_health(features)
        )
    except Exception as e:
        st.session_state.ai_output = {
            "error": str(e)
        }


# =====================================
# SIMULATION
# =====================================
if st.session_state.running:

    # ---------------------------
    # ACCELERATOR
    # ---------------------------
    target_torque = accelerator * 2.0

    state.torque_nm += (
        target_torque
        - state.torque_nm
    ) * 0.08

    state.current_a = (
        abs(state.torque_nm) * 1.4
    )

    # ---------------------------
    # REGENERATIVE BRAKING
    # ---------------------------
    if brake > 0:

        brake_factor = brake / 100

        state.torque_nm = (
            -80 * brake_factor
        )

        if state.vehicle_speed_kmph < 5:
            state.torque_nm = 0

    # ---------------------------
    # PHYSICS
    # ---------------------------
    state = update_motor_physics(
        state,
        dt_s=0.1
    )

    # ---------------------------
    # THERMAL
    # ---------------------------
    state = update_motor_thermal(
        state,
        getattr(state, "total_loss_w", 0),
        0.1
    )

    # ---------------------------
    # HEALTH
    # ---------------------------
    state = update_motor_health(
        state
    )

    # ---------------------------
    # FAULTS
    # ---------------------------
    state = update_faults(
        state
    )

    # ---------------------------
    # RUL
    # ---------------------------
    state = update_rul(
        state,
        dt_hours=0.1 / 3600
    )

    st.session_state.state = state


# =====================================
# CORE METRICS
# =====================================
st.subheader("🔋 Core Metrics")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Voltage (V)",
    round(state.voltage_v, 1)
)

c1.metric(
    "Current (A)",
    round(state.current_a, 1)
)

c1.metric(
    "Battery SOC (%)",
    round(state.battery_soc, 1)
)

c2.metric(
    "Speed (RPM)",
    round(state.speed_rpm, 0)
)

c2.metric(
    "Torque (Nm)",
    round(state.torque_nm, 1)
)

c2.metric(
    "Vehicle Speed (km/h)",
    round(state.vehicle_speed_kmph, 1)
)

c3.metric(
    "Power (kW)",
    round(state.power_kw, 2)
)

c3.metric(
    "Efficiency",
    round(state.efficiency, 3)
)


# =====================================
# TEMPERATURES
# =====================================
st.divider()
st.subheader("🌡 Temperatures")

t1, t2, t3 = st.columns(3)

t1.metric(
    "Stator Temp (°C)",
    round(state.stator_temp_c, 1)
)

t2.metric(
    "Rotor Temp (°C)",
    round(state.rotor_temp_c, 1)
)

t3.metric(
    "Bearing Temp (°C)",
    round(state.bearing_temp_c, 1)
)


# =====================================
# HEALTH
# =====================================
st.divider()
st.subheader("❤️ Health")

h1, h2, h3 = st.columns(3)

h1.metric(
    "Overall Health (%)",
    round(state.overall_health, 2)
)

h2.metric(
    "Failure Probability (%)",
    round(state.failure_probability, 2)
)

h3.metric(
    "RUL (hours)",
    round(state.rul_hours, 1)
)

if state.overall_health >= 80:
    st.success("🟢 Healthy Motor")
elif state.overall_health >= 50:
    st.warning("🟡 Degrading")
else:
    st.error("🔴 Critical Condition")


# =====================================
# AI PREDICTION
# =====================================
st.divider()
st.subheader("🤖 AI Prediction")

if st.session_state.ai_output:
    st.json(
        st.session_state.ai_output
    )
else:
    st.info(
        "Press 'Predict AI Health' to run AI."
    )


# =====================================
# AUTO REFRESH
# =====================================
if st.session_state.running:
    time.sleep(0.05)
    st.rerun()