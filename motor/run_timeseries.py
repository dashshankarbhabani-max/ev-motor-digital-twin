from motor.motor_state import MotorState
from motor.motor_physics import update_motor_physics
from motor.motor_thermal import update_motor_thermal
from motor.motor_health import update_motor_health
from motor.motor_faults import update_faults
from motor.motor_rul import update_rul

def simulate_motor(steps=100, dt=0.1):
    state = MotorState(
        voltage_v=400,
        current_a=100,
        speed_rpm=6000,
        torque_nm=200,
        flux_estimate=0.8,
        coolant_flow_rate=1.0,
        vibration_accel=0.5,
        vibration_vel=1.0,
        insulation_resistance_mohm=900,
        current_harmonics=2.0
    )

    history = []

    for t in range(steps):
        state.current_a = 100 + 5 * (t % 10)
        state.speed_rpm = 6000 + 20 * t
        state.torque_nm = 200 + 2 * (t % 15)
        state.vibration_accel = 0.5 + 0.01 * t
        state.vibration_vel = 1.0 + 0.02 * t
        state.current_harmonics = 2.0 + 0.01 * t

        phys = update_motor_physics(state, dt)
        state = update_motor_thermal(state, phys["total_loss_w"], dt)
        state = update_motor_health(state)
        state = update_faults(state)
        state = update_rul(state)

        history.append({
            "step": t,
            "voltage_v": state.voltage_v,
            "current_a": state.current_a,
            "speed_rpm": state.speed_rpm,
            "torque_nm": state.torque_nm,
            "power_kw": state.power_kw,
            "efficiency": state.efficiency,
            "stator_temp_c": state.stator_temp_c,
            "rotor_temp_c": state.rotor_temp_c,
            "magnet_temp_c": state.magnet_temp_c,
            "bearing_temp_c": state.bearing_temp_c,
            "coolant_in_temp_c": state.coolant_in_temp_c,
            "coolant_out_temp_c": state.coolant_out_temp_c,
            "vibration_accel": state.vibration_accel,
            "vibration_vel": state.vibration_vel,
            "stator_health": state.stator_health,
            "rotor_health": state.rotor_health,
            "magnet_health": state.magnet_health,
            "bearing_health": state.bearing_health,
            "cooling_health": state.cooling_health,
            "overall_health": state.overall_health,
            "failure_probability": state.failure_probability,
            "rul_hours": state.rul_hours,
            "fault_code": state.fault_code
        })

    return history

if __name__ == "__main__":
    hist = simulate_motor(steps=20, dt=0.1)
    print(hist[-1])