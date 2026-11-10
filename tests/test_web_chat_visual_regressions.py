from fastapi.testclient import TestClient

from scripts.demo_web_chat import app


def test_demo_page_has_correct_text():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "demostraci&#243;n local" in response.text
    assert "demostraci?n" not in response.text


def test_embed_has_svg_chat_icon():
    client = TestClient(app)
    response = client.get("/webchat/embed.js")

    assert response.status_code == 200
    assert "const chatIcon =" in response.text
    assert "<svg" in response.text
    assert "button.innerHTML = chatIcon;" in response.text
