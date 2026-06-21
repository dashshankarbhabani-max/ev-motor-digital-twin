from motor.motor_rul import update_rul
from motor.motor_state import MotorState


def test_high_failure_risk_immediately_limits_rul():
    state = MotorState(
        overall_health=80,
        failure_probability=80,
        rul_hours=20000,
    )

    state = update_rul(state, dt_hours=0.1 / 3600)

    assert 3000 < state.rul_hours < 3500


def test_healthy_motor_retains_high_rul():
    state = MotorState(
        overall_health=100,
        failure_probability=0,
        rul_hours=20000,
    )

    state = update_rul(state, dt_hours=0.1 / 3600)

    assert state.rul_hours > 19999
