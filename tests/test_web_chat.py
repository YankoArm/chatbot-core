from dataclasses import dataclass
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.web_chat import build_web_chat_router


WIDGET_A = "wf_easyappcode_123456"
WIDGET_B = "wf_otherclient_123456"


@dataclass
class Definition:
    id: str
    widget_id: str
    enabled: bool = True
    status: str = "active"

    @property
    def settings(self):
        return {
            "web_chat": {
                "enabled": self.enabled,
                "widget_id": self.widget_id,
            }
        }

    @property
    def metadata(self):
        return {"admin_status": self.status}


class FakeApplication:
    def chat(self, *, session_id, message):
        return SimpleNamespace(
            text=f"{session_id}: {message}"
        )


def make_client(definitions):
    app = FastAPI()

    def resolve(widget_id):
        return definitions.get(widget_id)

    app.include_router(
        build_web_chat_router(
            resolve_widget=resolve,
            build_application=lambda definition: (
                FakeApplication()
            ),
        )
    )

    return TestClient(app)


def test_webchat_creates_session_and_answers():
    client = make_client({
        WIDGET_A: Definition("easy_app_code", WIDGET_A)
    })

    started = client.post(
        f"/webchat/api/{WIDGET_A}/session"
    )
    assert started.status_code == 201

    token = started.json()["session_token"]

    answered = client.post(
        f"/webchat/api/{WIDGET_A}/message",
        json={
            "session_token": token,
            "message": "Hola",
        },
    )

    assert answered.status_code == 200
    assert answered.json()["response"].endswith(": Hola")


def test_webchat_rejects_cross_tenant_session():
    client = make_client({
        WIDGET_A: Definition("easy_app_code", WIDGET_A),
        WIDGET_B: Definition("other_client", WIDGET_B),
    })

    started = client.post(
        f"/webchat/api/{WIDGET_A}/session"
    )
    token = started.json()["session_token"]

    response = client.post(
        f"/webchat/api/{WIDGET_B}/message",
        json={
            "session_token": token,
            "message": "Hola",
        },
    )

    assert response.status_code == 404


def test_webchat_rejects_disabled_widget():
    client = make_client({
        WIDGET_A: Definition(
            "easy_app_code", WIDGET_A, enabled=False
        )
    })

    response = client.post(
        f"/webchat/api/{WIDGET_A}/session"
    )

    assert response.status_code == 404


def test_webchat_rejects_inactive_client():
    client = make_client({
        WIDGET_A: Definition(
            "easy_app_code",
            WIDGET_A,
            status="draft",
        )
    })

    response = client.post(
        f"/webchat/api/{WIDGET_A}/session"
    )

    assert response.status_code == 404


def test_webchat_limits_message_length():
    client = make_client({
        WIDGET_A: Definition("easy_app_code", WIDGET_A)
    })

    token = client.post(
        f"/webchat/api/{WIDGET_A}/session"
    ).json()["session_token"]

    response = client.post(
        f"/webchat/api/{WIDGET_A}/message",
        json={
            "session_token": token,
            "message": "a" * 1201,
        },
    )

    assert response.status_code == 422


def test_webchat_rejects_unknown_session():
    client = make_client({
        WIDGET_A: Definition("easy_app_code", WIDGET_A)
    })

    response = client.post(
        f"/webchat/api/{WIDGET_A}/message",
        json={
            "session_token": "x" * 40,
            "message": "Hola",
        },
    )

    assert response.status_code == 404


def test_webchat_limits_session_creation():
    client = make_client({
        WIDGET_A: Definition("easy_app_code", WIDGET_A)
    })

    for _ in range(8):
        response = client.post(
            f"/webchat/api/{WIDGET_A}/session"
        )
        assert response.status_code == 201

    blocked = client.post(
        f"/webchat/api/{WIDGET_A}/session"
    )

    assert blocked.status_code == 429
