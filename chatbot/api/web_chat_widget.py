from __future__ import annotations

import json
import re
from html import escape
from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response


EMBED_SCRIPT = r"""
(() => {
  "use strict";

  const script = document.currentScript;
  if (!script) return;

  const widgetId = script.getAttribute("data-flowforge-widget");

  if (!widgetId || !/^[A-Za-z0-9_-]{12,96}$/.test(widgetId)) {
    return;
  }

  const hostId = "flowforge-" + widgetId;
  if (document.getElementById(hostId)) return;

  const host = document.createElement("div");
  host.id = hostId;

  const shadow = host.attachShadow({mode: "open"});

  const style = document.createElement("style");
  style.textContent = `
    :host { all: initial; }
    .toggle {
      display: grid;
      place-items: center;
      position: fixed;
      right: 20px;
      bottom: 20px;
      width: 60px;
      height: 60px;
      border: 0;
      border-radius: 50%;
      background: #2563eb;
      color: white;
      font-size: 27px;
      cursor: pointer;
      box-shadow: 0 6px 24px #0003;
      z-index: 2147483647;
    }
    .panel {
      position: fixed;
      right: 20px;
      bottom: 92px;
      width: 370px;
      height: 540px;
      max-height: calc(100dvh - 115px);
      border-radius: 18px;
      background: white;
      overflow: hidden;
      box-shadow: 0 12px 42px #0004;
      z-index: 2147483647;
    }
    .panel[hidden] { display: none; }
    iframe {
      display: block;
      width: 100%;
      height: 100%;
      border: 0;
    }
    @media (max-width: 600px) {
      .panel {
        left: 10px;
        right: 10px;
        width: auto;
        bottom: 86px;
        height: calc(100dvh - 105px);
      }
    }
  `;

  const chatIcon = '<svg width="27" height="27" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5 8.5 8.5 0 0 1-4-.99L3 21l1.99-5.5A8.5 8.5 0 1 1 21 11.5Z"/></svg>';

  const button = document.createElement("button");
  button.className = "toggle";
  button.type = "button";
  button.innerHTML = chatIcon;
  button.setAttribute("aria-label", "Abrir asistente");
  button.setAttribute("aria-expanded", "false");

  const panel = document.createElement("div");
  panel.className = "panel";
  panel.hidden = true;

  const frame = document.createElement("iframe");
  frame.title = "Asistente virtual FlowForge";
  frame.loading = "lazy";

  frame.src = new URL(
    "widget/" + encodeURIComponent(widgetId),
    script.src
  ).href;

  panel.appendChild(frame);

  button.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
    const open = !panel.hidden;

    button.innerHTML = open ? "&times;" : chatIcon;
    button.setAttribute("aria-expanded", String(open));
    button.setAttribute(
      "aria-label",
      open ? "Cerrar asistente" : "Abrir asistente"
    );
  });

  shadow.append(style, panel, button);

  const mount = () => document.body.appendChild(host);

  if (document.body) {
    mount();
  } else {
    document.addEventListener("DOMContentLoaded", mount, {
      once: true
    });
  }
})();
"""


WIDGET_HTML = r"""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__BUSINESS_TITLE__ | FlowForge</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: system-ui, Arial, sans-serif;
    background: #f8fafc;
    color: #0f172a;
    height: 100dvh;
  }
  .shell {
    display: flex;
    flex-direction: column;
    height: 100dvh;
  }
  header {
    background: #1d4ed8;
    color: #fff;
    padding: 16px;
  }
  header strong { display: block; font-size: 16px; }
  header small { opacity: .88; }
  #messages {
    flex: 1;
    overflow-y: auto;
    padding: 15px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .message {
    padding: 11px 13px;
    border-radius: 14px;
    max-width: 88%;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    font-size: 14px;
    line-height: 1.5;
  }
  .bot { background: #e2e8f0; align-self: flex-start; }
  .user {
    background: #2563eb;
    color: white;
    align-self: flex-end;
  }
  .error {
    background: #fee2e2;
    color: #991b1b;
    align-self: flex-start;
  }
  form {
    display: flex;
    gap: 8px;
    padding: 12px;
    background: white;
    border-top: 1px solid #e2e8f0;
  }
  input {
    flex: 1;
    min-width: 0;
    padding: 11px;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    font: inherit;
    font-size: 14px;
  }
  button {
    border: 0;
    border-radius: 10px;
    padding: 10px 13px;
    cursor: pointer;
    background: #2563eb;
    color: white;
    font-weight: 600;
  }
  button:disabled { opacity: .5; cursor: wait; }
  .reset {
    background: transparent;
    color: #fff;
    padding: 5px;
    font-size: 12px;
    text-decoration: underline;
  }
  .foot {
    font-size: 11px;
    color: #64748b;
    text-align: center;
    padding-bottom: 7px;
    background: white;
  }
</style>
</head>
<body>
<div class="shell">
  <header>
    <strong>__BUSINESS_TITLE__</strong>
    <small>Asistente virtual</small>
    <button class="reset" type="button" id="reset">
      Nueva conversaci&#243;n
    </button>
  </header>

  <main id="messages" role="log" aria-live="polite"></main>

  <form id="chat-form">
    <input id="message" maxlength="1200"
           placeholder="Escribe tu mensaje..."
           aria-label="Tu mensaje" autocomplete="off">
    <button id="send" type="submit">Enviar</button>
  </form>
  <div class="foot">Asistente autom&#225;tico &#183; FlowForge</div>
</div>

<script>
"use strict";

const widgetId = __WIDGET_ID_JSON__;
const api = "/webchat/api/" + encodeURIComponent(widgetId);

const messages = document.getElementById("messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const send = document.getElementById("send");

let sessionToken = null;
let busy = false;

function addMessage(content, kind) {
  const element = document.createElement("div");
  element.className = "message " + kind;
  element.textContent = content;
  messages.appendChild(element);
  messages.scrollTop = messages.scrollHeight;
}

function setBusy(value) {
  busy = value;
  send.disabled = value;
  input.disabled = value;
}

async function request(path, body) {
  const response = await fetch(api + path, {
    method: "POST",
    credentials: "omit",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    if (response.status === 404) sessionToken = null;
    throw new Error("HTTP " + response.status);
  }

  return response.json();
}

form.addEventListener("submit", async event => {
  event.preventDefault();

  const message = input.value.trim();
  if (!message || busy) return;

  addMessage(message, "user");
  input.value = "";
  setBusy(true);

  try {
    if (!sessionToken) {
      const started = await request("/session", {});
      sessionToken = started.session_token;
    }

    const answer = await request("/message", {
      session_token: sessionToken,
      message: message
    });

    addMessage(answer.response, "bot");
  } catch (error) {
    addMessage(
      "No se pudo enviar el mensaje. Int?ntalo de nuevo.",
      "error"
    );
  } finally {
    setBusy(false);
    input.focus();
  }
});

document.getElementById("reset").addEventListener("click", () => {
  if (busy) return;
  sessionToken = null;
  messages.replaceChildren();
  addMessage("Nueva conversaci\u00F3n. \u00BFEn qu\u00E9 puedo ayudarte?", "bot");
  input.focus();
});

addMessage("\u00A1Hola! \u00BFEn qu\u00E9 puedo ayudarte?", "bot");
</script>
</body>
</html>
"""


def build_web_chat_widget_router(
    *,
    resolve_widget: Callable[[str], Any],
) -> APIRouter:
    router = APIRouter(prefix="/webchat")

    @router.get("/embed.js")
    def embed_script() -> Response:
        return Response(
            content=EMBED_SCRIPT,
            media_type="application/javascript",
            headers={
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "no-store",
            },
        )

    @router.get("/widget/{widget_id}")
    def widget_page(widget_id: str) -> HTMLResponse:
        if re.fullmatch(
            r"[A-Za-z0-9_-]{12,96}", widget_id
        ) is None:
            raise HTTPException(status_code=404)

        definition = resolve_widget(widget_id)

        if definition is None:
            raise HTTPException(status_code=404)

        settings = getattr(definition, "settings", {})
        metadata = getattr(definition, "metadata", {})

        web = (
            settings.get("web_chat", {})
            if isinstance(settings, dict)
            else {}
        )

        if (
            not isinstance(web, dict)
            or web.get("enabled") is not True
            or web.get("widget_id") != widget_id
            or not isinstance(metadata, dict)
            or metadata.get("admin_status", "active") != "active"
        ):
            raise HTTPException(status_code=404)

        title = escape(str(definition.name), quote=True)

        content = WIDGET_HTML.replace(
            "__BUSINESS_TITLE__", title
        ).replace(
            "__WIDGET_ID_JSON__", json.dumps(widget_id)
        )

        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
            },
        )

    return router
