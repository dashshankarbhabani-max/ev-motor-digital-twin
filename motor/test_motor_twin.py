from motor.motor_state import MotorState
from motor.motor_dynamics import update_motor_state
from motor.motor_sensors import simulate_sensors

def main():
    state = MotorState(
        voltage_v=400.0,
        current_a=0.0,
        speed_rpm=1000.0,
        coolant_flow_rate=1.0,
        coolant_pressure=2.5,
        stator_temp_c=40.0,
        rotor_temp_c=38.0,
        magnet_temp_c=36.0,
        bearing_temp_c=35.0,
        bearing_health=90.0
    )

    print("INITIAL STATE")
    print(state)
    print("-" * 80)

    for step in range(1, 6):
        state = update_motor_state(state, load_fraction=0.6, dt=1.0)
        sensors = simulate_sensors(state)

        print(f"STEP {step}")
        print("STATE:")
        print(state)
        print("SENSORS:")
        print(sensors)
        print("-" * 80)

if __name__ == "__main__":
    main()