def _clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def _warning(severity, title, message, corrective_action):
    return {
        "severity": severity,
        "title": title,
        "message": message,
        "corrective_action": corrective_action,
    }


def analyze_driver_inputs(state, accelerator_pct, brake_pct, dt_s):
    """Detect unsafe or inefficient pedal usage in the real-time simulation."""
    accelerator_pct = _clamp(float(accelerator_pct))
    brake_pct = _clamp(float(brake_pct))
    dt_s = max(float(dt_s), 0.05)

    previous_accelerator = getattr(state, "last_accelerator_pct", accelerator_pct)
    previous_brake = getattr(state, "last_brake_pct", brake_pct)
    accelerator_rate = (accelerator_pct - previous_accelerator) / dt_s
    brake_rate = (brake_pct - previous_brake) / dt_s

    warnings = []
    hot_motor = max(
        state.stator_temp_c,
        state.rotor_temp_c,
        state.magnet_temp_c,
        state.bearing_temp_c,
    ) >= 85

    if accelerator_pct > 10 and brake_pct > 10:
        warnings.append(
            _warning(
                "critical",
                "Accelerator and brake pressed together",
                "Both pedals are active, which wastes energy and creates unnecessary heat.",
                "Release one pedal. The guardian will ignore acceleration while braking in assistive/protective mode.",
            )
        )

    if accelerator_pct >= 85 and state.vehicle_speed_kmph < 15:
        warnings.append(
            _warning(
                "warning",
                "Harsh launch detected",
                "Very high accelerator demand from low speed can spike current and heat the stator.",
                "Accelerate progressively until the motor reaches a stable speed.",
            )
        )

    if accelerator_rate > 260:
        warnings.append(
            _warning(
                "warning",
                "Sudden accelerator change",
                "The accelerator was increased too quickly for smooth thermal operation.",
                "Apply accelerator gradually to avoid current spikes.",
            )
        )

    if brake_pct >= 85 and state.vehicle_speed_kmph > 35:
        warnings.append(
            _warning(
                "warning",
                "Hard braking at speed",
                "Heavy braking at high speed increases driveline stress and can reduce stability.",
                "Brake progressively unless this is an emergency stop.",
            )
        )

    if brake_rate > 300 and state.vehicle_speed_kmph > 20:
        warnings.append(
            _warning(
                "warning",
                "Sudden brake change",
                "The brake was applied very quickly while the vehicle was moving.",
                "Use a smoother brake ramp to reduce shock loading.",
            )
        )

    if accelerator_pct >= 70 and hot_motor:
        warnings.append(
            _warning(
                "critical",
                "Heavy acceleration while motor is hot",
                "High torque demand during elevated temperature can push the motor toward overheating.",
                "Reduce accelerator input until temperatures recover.",
            )
        )

    if brake_pct >= 70 and state.battery_soc >= 98:
        warnings.append(
            _warning(
                "warning",
                "Regenerative braking limited",
                "The battery is nearly full, so regenerative braking has less room to absorb energy.",
                "Use gentler braking and avoid repeated hard stops.",
            )
        )

    state.last_accelerator_pct = accelerator_pct
    state.last_brake_pct = brake_pct
    return warnings
