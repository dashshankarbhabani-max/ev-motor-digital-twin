import math
from motor.motor_params import MOTOR
from motor.motor_state import MotorState


# ==========================
# VEHICLE PARAMETERS
# ==========================
GEAR_RATIO = 9.0
WHEEL_RADIUS = 0.30          # m
VEHICLE_MASS = 1700          # kg
DRIVELINE_EFF = 0.95
MAX_SPEED_KMPH = 105
BATTERY_CAPACITY_KWH = 60


# ==========================
# HELPERS
# ==========================
def mechanical_power_kw(torque_nm, speed_rpm):
    omega = 2 * math.pi * speed_rpm / 60
    return torque_nm * omega / 1000


def back_emf_v(speed_rpm, ke=0.12):
    omega = 2 * math.pi * speed_rpm / 60
    return ke * omega


def copper_loss_w(current_a, resistance_ohm):
    return 3 * current_a**2 * resistance_ohm


def iron_loss_w(flux, freq_hz):
    return 0.5 * flux**2 * freq_hz


def mechanical_loss_w(speed_rpm, friction_coeff):
    omega = 2 * math.pi * speed_rpm / 60
    return friction_coeff * omega**2


def efficiency(pin_kw, pout_kw):
    if pin_kw <= 0:
        return 0.0
    return max(0.0, min(1.0, pout_kw / pin_kw))


# ==========================
# RPM -> VEHICLE SPEED
# ==========================
def rpm_to_kmph(rpm):
    wheel_rpm = rpm / GEAR_RATIO

    vehicle_speed_ms = (
        wheel_rpm
        * 2
        * math.pi
        * WHEEL_RADIUS
        / 60
    )

    return vehicle_speed_ms * 3.6


# ==========================
# VEHICLE SPEED -> RPM
# ==========================
def kmph_to_rpm(kmph):
    speed_ms = kmph / 3.6

    wheel_rpm = (
        speed_ms
        * 60
        / (2 * math.pi * WHEEL_RADIUS)
    )

    return wheel_rpm * GEAR_RATIO


# ==========================
# ROAD LOAD
# ==========================
def road_load_force(speed_kmph):

    speed_ms = speed_kmph / 3.6

    rolling = 180

    aero = 0.35 * speed_ms**2

    return rolling + aero


# ==========================
# MAIN PHYSICS
# ==========================
def update_motor_physics(
    state: MotorState,
    dt_s: float = 0.1
):

    # ----------------------
    # Initialize variables
    # ----------------------
    if not hasattr(state, "vehicle_speed_kmph"):
        state.vehicle_speed_kmph = 0.0

    if not hasattr(state, "battery_soc"):
        state.battery_soc = 100.0

    if not hasattr(state, "filtered_torque"):
        state.filtered_torque = 0.0

    if not hasattr(state, "initialized"):
        state.initialized = True

    if state.speed_rpm < 0:
        state.speed_rpm = 0

    # ----------------------
    # Smooth torque response
    # ----------------------
    target = state.torque_nm

    torque_rate = 0.08

    state.filtered_torque += (
        target
        - state.filtered_torque
    ) * torque_rate

    # ----------------------
    # Vehicle dynamics
    # ----------------------
    speed_ms = (
        state.vehicle_speed_kmph / 3.6
    )

    drive_force = (
    state.filtered_torque
    * GEAR_RATIO
    * DRIVELINE_EFF
    * 0.55
    / WHEEL_RADIUS
    )
    

    load_force = road_load_force(
        state.vehicle_speed_kmph
    )

    net_force = (
        drive_force
        - load_force
    )

    acceleration = (
        net_force
        / VEHICLE_MASS
    )

    speed_ms += (
        acceleration
        * dt_s
    )

    if speed_ms < 0:
        speed_ms = 0

    state.vehicle_speed_kmph = (
        speed_ms * 3.6
    )

    # ----------------------
    # Top speed limiter
    # ----------------------
    if state.vehicle_speed_kmph >= MAX_SPEED_KMPH:
        state.vehicle_speed_kmph = MAX_SPEED_KMPH

    # stop further acceleration
    if state.filtered_torque > 0:
        state.filtered_torque = 0

    # ----------------------
    # Convert speed to RPM
    # ----------------------
    state.speed_rpm = kmph_to_rpm(
        state.vehicle_speed_kmph
    )
    if state.vehicle_speed_kmph >= 105:
        state.vehicle_speed_kmph = 105
        state.speed_rpm = kmph_to_rpm(105)

    # ----------------------
    # Battery SOC
    # ----------------------
    state.power_kw = (
        mechanical_power_kw(
            state.filtered_torque,
            state.speed_rpm
        )
    )

    energy_used = (
        state.power_kw
        * dt_s
        / 3600
    )

    soc_drop = (
        energy_used
        / BATTERY_CAPACITY_KWH
        * 100
    )

    state.battery_soc -= soc_drop

    state.battery_soc = max(
        0,
        min(
            state.battery_soc,
            100
        )
    )

    # ----------------------
    # Regenerative braking
    # ----------------------
    if (
        state.torque_nm < 0
        and state.vehicle_speed_kmph > 5
    ):
        regen_kw = (
            abs(state.torque_nm)
            * speed_ms
            / 10
        )

        state.battery_soc += (
            regen_kw
            * dt_s
            / 3600
            / BATTERY_CAPACITY_KWH
            * 100
        )

        state.battery_soc = min(
            100,
            state.battery_soc
        )

    # ----------------------
    # Electrical losses
    # ----------------------
    state.back_emf_v = (
        back_emf_v(
            state.speed_rpm
        )
    )

    state.copper_loss_w = (
        copper_loss_w(
            state.current_a,
            MOTOR[
                "stator_resistance_ohm"
            ]
        )
    )

    state.iron_loss_w = (
        iron_loss_w(
            state.flux_estimate,
            max(
                state.speed_rpm / 60,
                1
            )
        )
    )

    state.mechanical_loss_w = (
        mechanical_loss_w(
            state.speed_rpm,
            MOTOR[
                "friction_coeff_nm_per_radps"
            ]
        )
    )

    state.total_loss_w = (
        state.copper_loss_w
        + state.iron_loss_w
        + state.mechanical_loss_w
    )

    pin_kw = (
        state.power_kw
        + state.total_loss_w / 1000
    )

    state.efficiency = (
        efficiency(
            pin_kw,
            state.power_kw
        )
    )

    return state