from motor.motor_state import MotorState
from motor.motor_physics import update_motor_physics

state = MotorState(voltage_v=400, current_a=100, speed_rpm=6000, torque_nm=200, flux_estimate=0.8)
result = update_motor_physics(state)

print(state)
print(result)