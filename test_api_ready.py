from motor_service import run_motor_twin

result = run_motor_twin(
    voltage_v=400,
    current_a=100,
    speed_rpm=6000,
    torque_nm=200,
    flux_estimate=0.8
)

print(result)