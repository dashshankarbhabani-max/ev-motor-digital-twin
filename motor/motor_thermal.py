from motor.motor_params import MOTOR
from motor.motor_state import MotorState


THERMAL_PARTS = {
    "stator": {
        "temp_attr": "stator_temp_c",
        "loss_fraction": 0.56,
        "thermal_mass_j_per_c": 12000.0,
        "cooling_w_per_c": 72.0,
        "coupled_to": None,
    },
    "rotor": {
        "temp_attr": "rotor_temp_c",
        "loss_fraction": 0.18,
        "thermal_mass_j_per_c": 9500.0,
        "cooling_w_per_c": 34.0,
        "coupled_to": "stator_temp_c",
    },
    "magnet": {
        "temp_attr": "magnet_temp_c",
        "loss_fraction": 0.16,
        "thermal_mass_j_per_c": 7200.0,
        "cooling_w_per_c": 30.0,
        "coupled_to": "rotor_temp_c",
    },
    "bearing": {
        "temp_attr": "bearing_temp_c",
        "loss_fraction": 0.10,
        "thermal_mass_j_per_c": 4500.0,
        "cooling_w_per_c": 24.0,
        "coupled_to": None,
    },
}


def _clamp(value, low, high):
    return max(low, min(high, value))


def _coolant_target_temp(ambient, flow_rate):
    # More flow keeps the inlet close to ambient; low flow warms the loop.
    return ambient + 2.0 + max(0.0, 1.0 - flow_rate) * 8.0


def update_motor_thermal(state: MotorState, loss_w: float, dt_s: float = 0.1):
    """Update motor part temperatures with heat input and liquid cooling.

    The previous model subtracted a tiny fixed cooling value each tick. This
    model behaves more like an EV liquid-cooled drive unit: heat removal grows
    with part temperature, coolant flow, and the temperature difference to the
    coolant loop.
    """
    ambient = MOTOR["ambient_temp_c"]
    dt_s = _clamp(float(dt_s), 0.02, 1.0)
    loss_w = max(float(loss_w), 0.0)
    flow_rate = _clamp(float(state.coolant_flow_rate), 0.2, 3.0)
    coolant_in = _coolant_target_temp(ambient, flow_rate)

    total_heat_rejected_w = 0.0
    for part in THERMAL_PARTS.values():
        temp_attr = part["temp_attr"]
        current_temp = float(getattr(state, temp_attr))
        heat_in_w = loss_w * part["loss_fraction"]

        coupled_temp = (
            float(getattr(state, part["coupled_to"]))
            if part["coupled_to"]
            else current_temp
        )
        coupling_w = max(0.0, coupled_temp - current_temp) * 8.0
        cooling_w = (
            part["cooling_w_per_c"]
            * flow_rate
            * max(0.0, current_temp - coolant_in)
        )

        net_heat_w = heat_in_w + coupling_w - cooling_w
        temp_delta = net_heat_w / part["thermal_mass_j_per_c"] * dt_s
        next_temp = max(ambient, current_temp + temp_delta)
        setattr(state, temp_attr, next_temp)
        total_heat_rejected_w += cooling_w

    state.coolant_in_temp_c = coolant_in
    coolant_heat_gain = total_heat_rejected_w / max(2500.0 * flow_rate, 1.0)
    state.coolant_out_temp_c = max(
        state.coolant_in_temp_c,
        state.coolant_in_temp_c + coolant_heat_gain,
    )

    return state


if __name__ == "__main__":
    s = MotorState(coolant_flow_rate=3.0, stator_temp_c=130)
    for _ in range(10):
        s = update_motor_thermal(s, 1000, 1.0)
    print(s.stator_temp_c)
