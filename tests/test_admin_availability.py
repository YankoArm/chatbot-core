import pytest

from chatbot.api.admin_availability import (
    availability_form_values,
    build_availability_settings,
)


def test_default_does_not_claim_24_7():
    settings = build_availability_settings({})
    assert settings["service_24_7"] is False
    assert settings["human_attention"]["mode"] == "on_request"


def test_service_24_7_does_not_enable_human_24_7_or_booking():
    settings = build_availability_settings({"service_24_7": "on"})
    assert settings["service_24_7"] is True
    assert settings["human_attention"]["mode"] == "on_request"
    assert "booking" not in settings


def test_human_24_7_can_be_selected_independently():
    settings = build_availability_settings({
        "human_attention_mode": "24_7",
    })
    assert settings["service_24_7"] is False
    assert settings["human_attention"]["mode"] == "24_7"


def test_custom_human_hours_survive_form_reload():
    settings = build_availability_settings({
        "service_24_7": "on",
        "human_attention_mode": "custom",
        "human_attention_hours": "L-V 09:00-18:00",
    })
    values = availability_form_values({"availability": settings})
    assert values["service_24_7"] == "on"
    assert values["human_attention_mode"] == "custom"
    assert values["human_attention_hours"] == "L-V 09:00-18:00"


@pytest.mark.parametrize(
    "values",
    [
        {"human_attention_mode": "custom"},
        {"human_attention_mode": "invalid"},
        {"service_24_7": "invalid"},
    ],
)
def test_invalid_availability_is_rejected(values):
    with pytest.raises(ValueError):
        build_availability_settings(values)
