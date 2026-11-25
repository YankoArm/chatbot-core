from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.web_chat import build_web_chat_router


@pytest.mark.parametrize(
    "metadata,visible",
    [
        ({"lead_capture_step": "name"}, False),
        ({"lead_capture_step": "phone"}, False),
        ({"lead_capture_step": "reason"}, False),
        ({"lead_captured": True}, True),
        ({"lead_capture_cancelled": True}, True),
        ({"lead_capture_follow_up": True}, True),
    ],
)
def test_contact_flow_controls_reply_buttons(metadata, visible):
    widget_id = "contact_widget_123456"
    definition = SimpleNamespace(
        id="demo",
        metadata={"admin_status": "active"},
        settings={
            "web_chat": {"enabled": True, "widget_id": widget_id},
            "knowledge": {
                "greetings": {
                    "menu": {
                        "enabled": True,
                        "items": {"services": True},
                    },
                },
            },
        },
    )
    result = SimpleNamespace(
        text="Test response",
        metadata={"capability": "lead_capture", **metadata},
    )
    application = SimpleNamespace(chat=lambda **kwargs: result)

    app = FastAPI()
    app.include_router(build_web_chat_router(
        resolve_widget=lambda value: definition,
        build_application=lambda tenant: application,
    ))

    with TestClient(app) as client:
        started = client.post(
            f"/webchat/api/{widget_id}/session", json={}
        )
        response = client.post(
            f"/webchat/api/{widget_id}/message",
            json={
                "session_token": started.json()["session_token"],
                "message": "Test",
            },
        )

    assert response.status_code == 200
    assert response.json()["response"] == "Test response"
    buttons = response.json()["buttons"]
    if visible:
        assert [button["id"] for button in buttons] == ["services"]
    else:
        assert buttons == []
