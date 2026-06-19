from motor.motor_state import MotorState
from motor.motor_physics import update_motor_physics

def run_motor_twin(
    voltage_v,
    current_a,
    speed_rpm,
    torque_nm,
    flux_estimate
):
    state = MotorState(
        voltage_v=voltage_v,
        current_a=current_a,
        speed_rpm=speed_rpm,
        torque_nm=torque_nm,
        flux_estimate=flux_estimate
    )

    result = update_motor_physics(state)

    return {
        "motor_state": state.__dict__,
        "physics_result": result
    }