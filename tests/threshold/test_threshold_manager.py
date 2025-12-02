import pytest

from src.manager.threshold_manager import ThresholdManager, ThresholdValidationError


def test_validate_profile_ok():
    mgr = ThresholdManager()
    payload = {
        "systolic_min": 90,
        "systolic_max": 140,
        "diastolic_min": 60,
        "diastolic_max": 90,
        "heart_rate_min": 50,
        "heart_rate_max": 100,
    }
    mgr.validate_profile(payload)


@pytest.mark.parametrize("payload", [
    {"systolic_min": 20, "systolic_max": 140, "diastolic_min": 60, "diastolic_max": 90},
    {"systolic_min": 100, "systolic_max": 140, "diastolic_min": 110, "diastolic_max": 120},
])
def test_validate_profile_invalid(payload):
    mgr = ThresholdManager()
    with pytest.raises(ThresholdValidationError):
        mgr.validate_profile(payload)
