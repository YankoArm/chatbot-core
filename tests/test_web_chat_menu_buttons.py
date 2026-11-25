from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.web_chat import build_web_chat_router


WIDGET_ID = "demo_widget_123456"


def make_client(items, enabled=True):
    definition = SimpleNamespace(
        id="demo",
        metadata={"admin_status": "active"},
        settings={
            "web_chat": {
                "enabled": True,
                "widget_id": WIDGET_ID,
            },
            "knowledge": {
                "greetings": {
                    "menu": {
                        "enabled": enabled,
                        "items": items,
                    },
                },
            },
        },
    )

    app = FastAPI()
    app.include_router(build_web_chat_router(
        resolve_widget=lambda widget_id: (
            definition if widget_id == WIDGET_ID else None
        ),
        build_application=lambda tenant: SimpleNamespace(),
    ))
    return TestClient(app)


@pytest.mark.parametrize(
    "item",
    ["services", "booking", "faq", "human_transfer"],
)
def test_session_exposes_only_selected_menu_button(item):
    items = {
        key: key == item
        for key in ("services", "booking", "faq", "human_transfer")
    }

    with make_client(items) as client:
        response = client.post(
            f"/webchat/api/{WIDGET_ID}/session",
            json={},
        )

    assert response.status_code == 201
    buttons = response.json().get("buttons")
    assert isinstance(buttons, list)
    assert len(buttons) == 1
    assert buttons[0]["id"] == item
    assert buttons[0]["label"].strip()
    assert buttons[0]["message"].strip()


def test_disabled_menu_exposes_no_buttons():
    with make_client({"services": True}, enabled=False) as client:
        response = client.post(
            f"/webchat/api/{WIDGET_ID}/session",
            json={},
        )

    assert response.status_code == 201
    assert response.json().get("buttons") == []
