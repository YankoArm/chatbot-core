from types import SimpleNamespace

import pytest

from chatbot.api.web_chat import _build_reply_menu_buttons
from chatbot.capabilities.booking.capability import BookingManagementStep


@pytest.mark.parametrize(
    "metadata,visible",
    [
        ({"booking_step": "name"}, False),
        ({"booking_step": "phone"}, False),
        ({"booking_step": "date"}, False),
        ({"booking_step": "time"}, False),
        ({"booking_step": "complete"}, True),
        ({"booking_step": "cancelled"}, True),
        (
            {"booking_management_step": BookingManagementStep.PHONE.value},
            False,
        ),
        (
            {"booking_management_step": BookingManagementStep.COMPLETE.value},
            True,
        ),
        ({"booking_step": None}, False),
    ],
)
def test_booking_steps_control_menu_visibility(metadata, visible):
    definition = SimpleNamespace(settings={
        "knowledge": {
            "greetings": {
                "menu": {
                    "enabled": True,
                    "items": {"services": True},
                },
            },
        },
    })
    result = SimpleNamespace(
        metadata={"capability": "booking", **metadata},
    )

    buttons = _build_reply_menu_buttons(definition, result)

    if visible:
        assert [button["id"] for button in buttons] == ["services"]
    else:
        assert buttons == []
