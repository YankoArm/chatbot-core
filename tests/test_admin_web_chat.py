from dataclasses import replace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.api.admin import build_admin_router
from chatbot.clients.registry import build_client_definition
from chatbot.instances.sqlite_repository import SQLiteInstanceDefinitionRepository


@pytest.fixture
def environment(tmp_path):
    repo = SQLiteInstanceDefinitionRepository(tmp_path / "web_admin.sqlite3")
    app = FastAPI()
    app.include_router(build_admin_router(repo))
    try:
        yield TestClient(app), repo
    finally:
        repo.close()


def make_bot(repo, channel="web", status="active"):
    original = build_client_definition("tarot_alvin")
    bot = replace(
        original,
        id="eac_web_test",
        name="Easy App Code Test",
        whatsapp_phone_number_id=None,
        channels=[channel] if channel != "both" else ["whatsapp", "web"],
        metadata={
            **original.metadata,
            "channel_mode": channel,
            "admin_status": status,
        },
    )
    repo.save(bot)
    return bot


def url():
    return "/admin/clients/eac_web_test/web-chat"


def test_panel_accessible_and_linked(environment):
    client, repo = environment
    make_bot(repo)
    page = client.get(url())
    assert page.status_code == 200
    assert 'name="allowed_origins"' in page.text
    assert "Easy App Code Test" in page.text
    detail = client.get("/admin/clients/eac_web_test")
    assert detail.status_code == 200
    assert url() in detail.text


@pytest.mark.parametrize("channel", ["web", "both"])
def test_enables_web_and_generates_code(environment, channel):
    client, repo = environment
    make_bot(repo, channel=channel)
    response = client.post(
        url(),
        data={
            "enabled": "on",
            "allowed_origins": (
                "https://easyappcode.com\n"
                "https://www.easyappcode.com"
            ),
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    saved = repo.get("eac_web_test")
    web = saved.settings["web_chat"]
    assert web["enabled"] is True
    assert len(web["allowed_origins"]) == 2
    assert web["widget_id"].startswith("wf_")
    assert web["widget_id"] in client.get(url()).text
    assert "data-flowforge-widget" in client.get(url()).text

    second = client.post(
        url(),
        data={"enabled": "on", "allowed_origins": "https://easyappcode.com"},
        follow_redirects=False,
    )
    assert second.status_code == 303
    assert repo.get("eac_web_test").settings["web_chat"]["widget_id"] == web["widget_id"]


def test_can_disable_without_losing_id(environment):
    client, repo = environment
    make_bot(repo)
    client.post(url(), data={"enabled": "on", "allowed_origins": "https://easyappcode.com"})
    before = repo.get("eac_web_test").settings["web_chat"]["widget_id"]
    client.post(url(), data={"allowed_origins": "https://easyappcode.com"})
    after = repo.get("eac_web_test").settings["web_chat"]
    assert after["enabled"] is False
    assert after["widget_id"] == before


@pytest.mark.parametrize("origin", [
    "http://easyappcode.com",
    "https://example.com/private",
    "javascript:alert(1)",
    "https://user:pass@example.com",
])
def test_rejects_invalid_origin_without_writing(environment, origin):
    client, repo = environment
    make_bot(repo)
    resp = client.post(url(), data={"enabled": "on", "allowed_origins": origin})
    assert resp.status_code == 422
    assert "web_chat" not in repo.get("eac_web_test").settings


def test_rejects_empty_origins(environment):
    client, repo = environment
    make_bot(repo)
    resp = client.post(url(), data={"enabled": "on", "allowed_origins": ""})
    assert resp.status_code == 422


def test_whatsapp_only_cannot_enable_web(environment):
    client, repo = environment
    make_bot(repo, channel="whatsapp")
    resp = client.post(
        url(), data={"enabled": "on", "allowed_origins": "https://easyappcode.com"}
    )
    assert resp.status_code == 422
    assert "web_chat" not in repo.get("eac_web_test").settings


def test_localhost_allowed_for_development(environment):
    client, repo = environment
    make_bot(repo)
    resp = client.post(
        url(),
        data={"enabled": "on", "allowed_origins": "http://127.0.0.1:8010"},
        follow_redirects=False,
    )
    assert resp.status_code == 303


def test_unknown_client_rejected(environment):
    client, _ = environment
    assert client.get("/admin/clients/no_such_client/web-chat").status_code == 404
