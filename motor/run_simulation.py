from motor.motor_reset import create_fresh_state
from motor.motor_physics import update_motor_physics
from motor.motor_thermal import update_motor_thermal
from motor.motor_health import update_motor_health
from motor.motor_faults import update_motor_faults
from motor.motor_rul import update_motor_rul


# =========================
# VEHICLE CONSTANTS
# =========================
MAX_SPEED_KMPH = 110.0
WHEEL_RADIUS_M = 0.30

MAX_TORQUE = 250.0
ACCEL_TORQUE_STEP = 8.0


# =========================
# CONVERSIONS
# =========================
def rpm_to_kmph(rpm):
    return (rpm * 2 * 3.14159265 * WHEEL_RADIUS_M / 60.0) * 3.6


def kmph_to_rpm(kmph):
    return (kmph / 3.6) * 60.0 / (
        2 * 3.14159265 * WHEEL_RADIUS_M
    )


# =========================
# BRAKE
# =========================
def apply_brake(state, strength=0.15):
    state.speed_rpm *= (1.0 - strength)

    if state.speed_rpm < 5:
        state.speed_rpm = 0.0
        state.torque_nm = 0.0
        state.current_a = 0.0

    return state


# =========================
# SIMULATION
# =========================
def run_once():

    # ALWAYS START FROM ZERO
    state = create_fresh_state()

    state.speed_rpm = 0.0
    state.torque_nm = 0.0
    state.current_a = 0.0

    dt = 0.2

    print("\n🚗 EV SIMULATION START\n")

    for step in range(80):

        # =========================
        # DRIVE PROFILE
        # =========================

        # 0-20 steps: accelerate
        if step < 20:

            state.torque_nm += ACCEL_TORQUE_STEP
            state.torque_nm = min(
                state.torque_nm,
                MAX_TORQUE
            )

        # 20-45 steps: cruise
        elif step < 45:

            state.torque_nm = 180

        # 45-65 steps: brake
        elif step < 65:

            state = apply_brake(
                state,
                strength=0.12
            )

        # 65-79 steps: full stop
        else:

            state = apply_brake(
                state,
                strength=0.25
            )
            state.torque_nm = 0.0

        # =========================
        # PHYSICS
        # =========================
        state = update_motor_physics(
            state,
            dt
        )

        # =========================
        # SPEED LIMIT
        # =========================
        speed_kmph = rpm_to_kmph(
            state.speed_rpm
        )

        if speed_kmph > MAX_SPEED_KMPH:
            state.speed_rpm = kmph_to_rpm(
                MAX_SPEED_KMPH
            )
            speed_kmph = MAX_SPEED_KMPH

        # =========================
        # COMPLETE STOP
        # =========================
        if state.speed_rpm < 5:
            state.speed_rpm = 0.0

        # =========================
        # THERMAL
        # =========================
        state = update_motor_thermal(
            state,
            getattr(
                state,
                "total_loss_w",
                0
            ),
            dt
        )

        # =========================
        # HEALTH
        # =========================
        state = update_motor_health(
            state
        )

        # =========================
        # RUL
        # =========================
        state = update_motor_rul(
            state,
            dt_hours=dt / 3600
        )

        # =========================
        # FAULTS
        # =========================
        state = update_motor_faults(
            state
        )

        # =========================
        # PRINT
        # =========================
        print(
            f"Step {step:02d} | "
            f"RPM: {state.speed_rpm:7.1f} | "
            f"Speed: {speed_kmph:6.1f} km/h | "
            f"Torque: {state.torque_nm:6.1f} Nm | "
            f"Temp: {state.stator_temp_c:5.1f} °C | "
            f"RUL: {state.rul_hours:8.1f} h"
        )

    print("\n🚗 EV SIMULATION END\n")


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    run_once()