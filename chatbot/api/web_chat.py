from __future__ import annotations

import re
import secrets
import time
from collections import deque
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field


SESSION_TTL = 1800
MAX_SESSIONS = 200
MAX_MESSAGES_PER_MINUTE = 20
MAX_NEW_SESSIONS_PER_MINUTE = 8


class WebChatMessage(BaseModel):
    session_token: str = Field(min_length=30, max_length=128)
    message: str = Field(min_length=1, max_length=1200)


@dataclass
class WebChatSession:
    widget_id: str
    client_id: str
    application: Any
    last_seen: float
    message_times: deque = field(default_factory=deque)



def _build_initial_menu_buttons(definition: Any) -> list[dict[str, str]]:
    settings = getattr(definition, "settings", {})
    if not isinstance(settings, dict):
        return []

    knowledge = settings.get("knowledge", {})
    if not isinstance(knowledge, dict):
        return []

    greetings = knowledge.get("greetings", {})
    if not isinstance(greetings, dict):
        return []

    menu = greetings.get("menu", {})
    if not isinstance(menu, dict) or menu.get("enabled") is not True:
        return []

    items = menu.get("items", {})
    if not isinstance(items, dict):
        return []

    choices = (
        ("services", "Servicios y precios", "Ver servicios y precios"),
        ("booking", "Reservar cita", "Quiero reservar una cita"),
        ("faq", "Preguntas frecuentes", "ayuda"),
        (
            "human_transfer",
            "Hablar con alguien",
            "Quiero hablar con una persona",
        ),
    )

    return [
        {"id": key, "label": label, "message": message}
        for key, label, message in choices
        if items.get(key) is True
    ]



def _build_reply_menu_buttons(
    definition: Any,
    result: Any,
) -> list[dict[str, str]]:
    metadata = getattr(result, "metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    if metadata.get("capability") == "lead_capture":
        finished = any(
            metadata.get(key) is True
            for key in (
                "lead_captured",
                "lead_capture_cancelled",
                "lead_capture_follow_up",
            )
        )
        if not finished:
            return []

    terminal_steps = {"complete", "completed", "cancelled", "canceled"}

    for key in ("booking_step", "booking_management_step"):
        if key not in metadata:
            continue
        step = metadata[key]
        if not isinstance(step, str):
            return []
        if step.casefold() not in terminal_steps:
            return []

    return _build_initial_menu_buttons(definition)



def _format_web_chat_reply_text(definition: Any, result: Any) -> str:
    from chatbot.capabilities.greeting import GreetingCapability
    from chatbot.language import Language

    metadata = getattr(result, "metadata", {})
    if not isinstance(metadata, dict):
        return result.text

    if (
        metadata.get("capability") != "greeting"
        and metadata.get("activation_succeeded") is not True
    ):
        return result.text

    if not _build_initial_menu_buttons(definition):
        return result.text

    greetings = definition.settings["knowledge"]["greetings"]
    language = (
        Language.EN
        if metadata.get("language") == "en"
        else Language.ES
    )
    suffix = GreetingCapability._append_guided_menu(
        response_text="",
        greetings=greetings,
        language=language,
    )

    if suffix and result.text.endswith(suffix):
        return result.text.removesuffix(suffix)

    return result.text


def build_web_chat_router(
    *,
    resolve_widget: Callable[[str], Any],
    build_application: Callable[[Any], Any],
) -> APIRouter:
    """
    Isolated web-chat API foundation.

    This router is not registered in production yet.
    Session state is currently process-local and must be
    replaced or shared before multi-worker deployment.
    """
    router = APIRouter(prefix="/webchat/api")
    sessions: dict[str, WebChatSession] = {}
    creation_times: dict[str, deque] = {}
    lock = RLock()

    def get_definition(widget_id: str) -> Any:
        if not re.fullmatch(
            r"[A-Za-z0-9_-]{12,96}", widget_id
        ):
            raise HTTPException(status_code=404)

        definition = resolve_widget(widget_id)

        if definition is None:
            raise HTTPException(status_code=404)

        settings = getattr(definition, "settings", {})
        metadata = getattr(definition, "metadata", {})

        web_settings = (
            settings.get("web_chat", {})
            if isinstance(settings, dict)
            else {}
        )

        if not isinstance(web_settings, dict):
            raise HTTPException(status_code=404)

        if (
            web_settings.get("enabled") is not True
            or web_settings.get("widget_id") != widget_id
        ):
            raise HTTPException(status_code=404)

        if not isinstance(metadata, dict):
            raise HTTPException(status_code=404)

        if metadata.get("admin_status", "active") != "active":
            raise HTTPException(status_code=404)

        return definition

    def cleanup(now: float) -> None:
        expired = [
            token
            for token, session in sessions.items()
            if now - session.last_seen > SESSION_TTL
        ]

        for token in expired:
            del sessions[token]

    @router.post("/{widget_id}/session", status_code=201)
    def start_session(
        widget_id: str,
        request: Request,
        response: Response,
    ) -> dict[str, object]:
        definition = get_definition(widget_id)
        now = time.monotonic()
        client_ip = (
            request.client.host
            if request.client is not None
            else "unknown"
        )

        with lock:
            cleanup(now)

            attempts = creation_times.setdefault(
                client_ip, deque()
            )

            while attempts and now - attempts[0] > 60:
                attempts.popleft()

            if len(attempts) >= MAX_NEW_SESSIONS_PER_MINUTE:
                raise HTTPException(
                    status_code=429,
                    detail="Too many sessions",
                )

            if len(sessions) >= MAX_SESSIONS:
                raise HTTPException(
                    status_code=503,
                    detail="Session capacity reached",
                )

            token = secrets.token_urlsafe(32)
            application = build_application(definition)

            sessions[token] = WebChatSession(
                widget_id=widget_id,
                client_id=definition.id,
                application=application,
                last_seen=now,
            )
            attempts.append(now)

        response.headers["Cache-Control"] = "no-store"

        return {
            "session_token": token,
            "expires_in_seconds": SESSION_TTL,
            "buttons": _build_initial_menu_buttons(definition),
        }

    @router.post("/{widget_id}/message")
    def send_message(
        widget_id: str,
        payload: WebChatMessage,
        response: Response,
    ) -> dict[str, object]:
        definition = get_definition(widget_id)
        now = time.monotonic()

        with lock:
            cleanup(now)
            session = sessions.get(payload.session_token)

            if (
                session is None
                or session.widget_id != widget_id
                or session.client_id != definition.id
            ):
                raise HTTPException(status_code=404)

            times = session.message_times

            while times and now - times[0] > 60:
                times.popleft()

            if len(times) >= MAX_MESSAGES_PER_MINUTE:
                raise HTTPException(
                    status_code=429,
                    detail="Too many messages",
                )

            message = payload.message.strip()

            if not message:
                raise HTTPException(
                    status_code=422,
                    detail="Empty message",
                )

            times.append(now)
            session.last_seen = now

            result = session.application.chat(
                session_id=(
                    f"web:{widget_id}:{payload.session_token}"
                ),
                message=message,
            )

        response.headers["Cache-Control"] = "no-store"

        reply = {
            "response": _format_web_chat_reply_text(definition, result),
        }
        if _build_initial_menu_buttons(definition):
            reply["buttons"] = _build_reply_menu_buttons(definition, result)
        return reply

    return router
