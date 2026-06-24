FAULT_GUIDANCE = {
    "M001_STATOR_OVERHEAT": {
        "part": "Stator winding",
        "issue": "Stator temperature is above the safe operating limit.",
        "action": "Stop the motor and allow it to cool before restarting.",
        "fix": "Check coolant flow, reduce load, inspect stator windings, and verify the temperature sensor.",
    },
    "STATOR_FAULT": {
        "part": "Stator winding",
        "issue": "The model detected a possible stator fault.",
        "action": "Reduce load and schedule a stator inspection.",
        "fix": "Inspect winding insulation, phase balance, connectors, and cooling around the stator.",
    },
    "M004_INSULATION_BREAKDOWN": {
        "part": "Insulation system",
        "issue": "Insulation resistance is too low, which can become an electrical safety risk.",
        "action": "Stop the motor and isolate power before further operation.",
        "fix": "Perform insulation resistance testing, inspect cables and windings for moisture or damage, and repair before restart.",
    },
    "M005_CURRENT_IMBALANCE": {
        "part": "Inverter and phase current",
        "issue": "Current harmonics or phase imbalance are above the healthy range.",
        "action": "Reduce load and stop the motor if imbalance continues.",
        "fix": "Check inverter output, phase connectors, current sensors, and motor phase resistance.",
    },
    "M201_PARTIAL_DEMAGNETIZATION": {
        "part": "Rotor magnets",
        "issue": "Magnet temperature is high enough to risk partial demagnetization.",
        "action": "Stop high-load operation and let the rotor cool.",
        "fix": "Improve cooling, check rotor temperature trend, and inspect magnets if torque remains low.",
    },
    "M301_BEARING_FAULT": {
        "part": "Bearing assembly",
        "issue": "Bearing temperature or vibration indicates bearing damage risk.",
        "action": "Stop the motor and inspect the bearing before continuing.",
        "fix": "Check lubrication, alignment, mounting looseness, and replace the bearing if heat or vibration remains high.",
    },
    "M401_COOLING_FAILURE": {
        "part": "Cooling system",
        "issue": "Coolant flow is below the required level.",
        "action": "Stop the motor or keep it at very low load until cooling is restored.",
        "fix": "Check coolant level, pump, filter, radiator, air pockets, and leaks in the cooling loop.",
    },
}


def _value(features, key, default=0.0):
    try:
        return float(features.get(key, default))
    except (TypeError, ValueError):
        return default


def _add(recommendations, seen, severity, part, issue, action, fix):
    key = (severity, part, issue)
    if key in seen:
        return
    seen.add(key)
    recommendations.append(
        {
            "severity": severity,
            "part": part,
            "issue": issue,
            "action": action,
            "fix": fix,
        }
    )


def _fault_code(features, explicit_fault_code):
    if explicit_fault_code:
        return str(explicit_fault_code)
    for key in ("fault_code", "detected_fault_code", "safety_fault_code"):
        code = str(features.get(key, "NONE"))
        if code and code != "NONE":
            return code
    return "NONE"


def build_recommendations(features, fault_code=None):
    """Build operator recommendations from live health, fault, and ML signals."""
    recommendations = []
    seen = set()
    code = _fault_code(features, fault_code)

    if code != "NONE":
        guidance = FAULT_GUIDANCE.get(
            code,
            {
                "part": "Motor system",
                "issue": f"Fault condition detected: {code}.",
                "action": "Stop the motor and perform a full inspection.",
                "fix": "Review sensor values, inspect the affected subsystem, and restart only after readings return to normal.",
            },
        )
        severity = "critical" if code.startswith("M") else "warning"
        _add(recommendations, seen, severity, **guidance)

    threshold_checks = [
        (
            _value(features, "stator_temp_c") > 120,
            "critical",
            "Stator winding",
            "Stator temperature is very high.",
            "Stop the motor and cool the stator.",
            "Check coolant flow, load demand, stator windings, and temperature sensor calibration.",
        ),
        (
            _value(features, "rotor_temp_c") > 110,
            "warning",
            "Rotor",
            "Rotor temperature is approaching an unsafe range.",
            "Reduce load and monitor rotor temperature.",
            "Inspect rotor cooling path and avoid sustained high-torque operation.",
        ),
        (
            _value(features, "magnet_temp_c") > 130,
            "critical",
            "Rotor magnets",
            "Magnet temperature can damage magnetic strength.",
            "Stop high-load operation.",
            "Restore cooling and inspect for torque loss after the motor cools.",
        ),
        (
            _value(features, "bearing_temp_c") > 85,
            "critical",
            "Bearing assembly",
            "Bearing temperature is too high.",
            "Stop and inspect the bearing.",
            "Check lubrication, alignment, preload, and replace worn bearings.",
        ),
        (
            _value(features, "vibration_vel") > 3.5,
            "critical",
            "Bearing and shaft",
            "Vibration is above the normal operating band.",
            "Stop the motor if vibration continues or increases.",
            "Inspect bearing wear, rotor balance, shaft alignment, and mounting bolts.",
        ),
        (
            _value(features, "coolant_flow_rate", 1.0) < 0.7,
            "critical",
            "Cooling system",
            "Coolant flow is weak.",
            "Reduce load or stop until cooling flow is restored.",
            "Check pump operation, coolant level, clogged filter, radiator, and leaks.",
        ),
        (
            _value(features, "insulation_resistance_mohm", 1000.0) < 700,
            "critical",
            "Insulation system",
            "Insulation resistance is below the preferred safety margin.",
            "Do not run under heavy load.",
            "Dry and inspect windings/cables, then perform insulation resistance testing.",
        ),
        (
            _value(features, "current_harmonics") > 4,
            "warning",
            "Electrical drive",
            "Current harmonics are high.",
            "Reduce load and check inverter output quality.",
            "Inspect phase connectors, inverter switching health, and current sensors.",
        ),
    ]

    for should_add, severity, part, issue, action, fix in threshold_checks:
        if should_add:
            _add(recommendations, seen, severity, part, issue, action, fix)

    low_health_checks = [
        ("stator_health", "Stator winding"),
        ("rotor_health", "Rotor"),
        ("magnet_health", "Rotor magnets"),
        ("bearing_health", "Bearing assembly"),
        ("cooling_health", "Cooling system"),
        ("shaft_health", "Shaft and coupling"),
    ]
    for key, part in low_health_checks:
        health = _value(features, key, 100.0)
        if health < 60:
            _add(
                recommendations,
                seen,
                "critical",
                part,
                f"{part} health is critically low ({health:.1f}%).",
                "Stop the motor and inspect this subsystem.",
                "Repair the root cause and verify the health score improves before restart.",
            )
        elif health < 80:
            _add(
                recommendations,
                seen,
                "warning",
                part,
                f"{part} health is degrading ({health:.1f}%).",
                "Schedule maintenance soon.",
                "Review related temperature, vibration, and electrical readings.",
            )

    failure_probability = _value(features, "failure_probability")
    overall_health = _value(features, "overall_health", 100.0)
    if failure_probability >= 70:
        _add(
            recommendations,
            seen,
            "critical",
            "Motor system",
            f"Failure probability is high ({failure_probability:.1f}%).",
            "Stop the motor and inspect before continuing.",
            "Use the subsystem recommendations above to fix the highest-risk component first.",
        )
    elif failure_probability >= 35 or overall_health < 80:
        _add(
            recommendations,
            seen,
            "warning",
            "Motor system",
            "The motor is showing early degradation.",
            "Reduce load and plan maintenance.",
            "Trend the readings and inspect the weakest subsystem during the next service window.",
        )

    if not recommendations:
        recommendations.append(
            {
                "severity": "normal",
                "part": "Motor system",
                "issue": "No harmful condition detected.",
                "action": "Continue operation and keep monitoring live metrics.",
                "fix": "No repair is required right now.",
            }
        )

    severity_rank = {"critical": 0, "warning": 1, "normal": 2}
    return sorted(recommendations, key=lambda item: severity_rank[item["severity"]])
