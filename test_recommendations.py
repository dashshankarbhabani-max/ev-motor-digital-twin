from motor.maintenance_recommendations import build_recommendations


def test_healthy_motor_recommends_monitoring():
    recommendations = build_recommendations(
        {
            "overall_health": 100,
            "failure_probability": 0,
            "stator_health": 100,
            "rotor_health": 100,
            "magnet_health": 100,
            "bearing_health": 100,
            "cooling_health": 100,
            "shaft_health": 100,
        }
    )

    assert recommendations == [
        {
            "severity": "normal",
            "part": "Motor system",
            "issue": "No harmful condition detected.",
            "action": "Continue operation and keep monitoring live metrics.",
            "fix": "No repair is required right now.",
        }
    ]


def test_bearing_fault_recommends_stop_and_repair():
    recommendations = build_recommendations(
        {
            "fault_code": "M301_BEARING_FAULT",
            "bearing_temp_c": 105,
            "vibration_vel": 5.0,
            "bearing_health": 55,
            "overall_health": 75,
            "failure_probability": 80,
        }
    )

    assert recommendations[0]["severity"] == "critical"
    assert recommendations[0]["part"] == "Bearing assembly"
    assert "Stop" in recommendations[0]["action"]
    assert any("bearing" in item["fix"].lower() for item in recommendations)
