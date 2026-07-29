from fastapi.testclient import TestClient

from chatbot.interfaces.api import app


def test_root_endpoint_returns_application_information() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "flowforge"
    assert "instance" in data
    assert "capabilities" in data

def test_message_endpoint_returns_chat_response() -> None:
    client = TestClient(app)

    response = client.post(
        "/message",
        json={
            "user_id": "test-user",
            "message": "hola",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == "test-user"
    assert isinstance(data["response"], str)
    assert data["response"]

def test_reset_endpoint_resets_user_session() -> None:
    client = TestClient(app)

    response = client.post(
        "/reset",
        json={
            "user_id": "test-user",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "user_id": "test-user",
        "message": "Session reset successfully",
    }