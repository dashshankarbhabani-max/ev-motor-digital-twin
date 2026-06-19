from motor.motor_state import MotorState
from motor.motor_physics import update_motor_physics
from motor.motor_thermal import update_motor_thermal
from motor.motor_health import update_motor_health
from motor.motor_faults import update_faults
from motor.motor_rul import update_rul

def run_once():
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

    phys = update_motor_physics(state, 0.1)
    state = update_motor_thermal(state, phys["total_loss_w"], 0.1)
    state = update_motor_health(state)
    state = update_faults(state)
    state = update_rul(state)

    print(state)
    print(phys)

if __name__ == "__main__":
    run_once()