from motor.motor_state import MotorState

def update_rul(state: MotorState, degradation_rate_per_hour: float = 0.5):
    health_factor = max(state.overall_health, 1.0)
    severity_factor = max(1.0, state.failure_probability / 20.0)
    state.rul_hours = health_factor / (degradation_rate_per_hour * severity_factor)
    return state

if __name__ == "__main__":
    s = MotorState(overall_health=85.0, failure_probability=30.0)
    s = update_rul(s)
    print(s)