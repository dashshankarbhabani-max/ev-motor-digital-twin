from motor.motor_faults import update_faults
from motor.motor_health import update_motor_health
from motor.motor_state import MotorState


def test_moderate_heat_reduces_health_before_hard_fault():
    state = MotorState(
        stator_temp_c=95,
        rotor_temp_c=90,
        magnet_temp_c=100,
        bearing_temp_c=78,
        current_a=220,
        torque_nm=240,
        vibration_vel=1.2,
        coolant_flow_rate=1.0,
        coolant_in_temp_c=27,
        coolant_out_temp_c=33,
    )

    state = update_motor_health(state)

    assert state.overall_health < 97.5
    assert state.stator_health < 98
    assert state.bearing_health < 96


def test_moderate_stress_increases_failure_probability_without_fault_code():
    state = MotorState(
        stator_temp_c=95,
        rotor_temp_c=90,
        magnet_temp_c=100,
        bearing_temp_c=78,
        current_a=220,
        torque_nm=240,
        vibration_vel=1.2,
        coolant_flow_rate=1.0,
        coolant_in_temp_c=27,
        coolant_out_temp_c=33,
    )

    state = update_motor_health(state)
    state = update_faults(state)

    assert 0 < state.failure_probability < 50
    assert state.fault_code == "NONE"


def test_failure_probability_rises_with_temperature_and_vibration():
    mild = MotorState(stator_temp_c=90, bearing_temp_c=75, vibration_vel=1.0)
    severe = MotorState(stator_temp_c=125, bearing_temp_c=95, vibration_vel=3.5)

    mild = update_faults(update_motor_health(mild))
    severe = update_faults(update_motor_health(severe))

    assert severe.failure_probability > mild.failure_probability
    assert severe.failure_probability > 30
