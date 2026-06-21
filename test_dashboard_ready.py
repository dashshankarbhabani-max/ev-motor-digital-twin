import os

import pytest
from streamlit.testing.v1 import AppTest


def dashboard_app():
    return AppTest.from_file("motor/dashboard.py", default_timeout=120).run()


def test_dashboard_renders_complete_motor_interface():
    app = dashboard_app()
    assert not app.exception
    assert len(app.slider) == 2
    assert {button.label for button in app.button} >= {
        "▶ Start",
        "■ Stop",
        "↻ Reset Simulation",
        "◎ Predict ML Health",
    }
    assert len(app.metric) == 15
    assert any("Healthy motor" in message.value for message in app.success)


@pytest.mark.skipif(not os.getenv("APP_API_KEY"), reason="APP_API_KEY is required")
def test_dashboard_calls_deployed_prediction_api():
    app = dashboard_app()
    predict_button = next(
        button for button in app.button if button.label == "◎ Predict ML Health"
    )
    predict_button.click().run(timeout=120)
    assert not app.exception
    assert not app.error, [message.value for message in app.error]
    metric_labels = {metric.label for metric in app.metric}
    assert {
        "Predicted Health",
        "Predicted Failure Risk",
        "Predicted RUL",
    } <= metric_labels
