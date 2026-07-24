from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from chatbot.application.application import FlowForgeApplication
from chatbot.application.bootstrap import Bootstrap
from chatbot.instances.instance import Instance


class MessageRequest(BaseModel):
    user_id: str
    message: str


class MessageResponse(BaseModel):
    user_id: str
    response: str


class ResetRequest(BaseModel):
    user_id: str


def create_application() -> FlowForgeApplication:
    """
    Build the FlowForge application used by the HTTP API.
    """

    instance = Instance(
        id="flowforge-api",
        name="FlowForge API",
        default_language="es",
        channels=[
            "api",
            "web",
        ],
        capabilities=[
            "greeting",
            "booking",
        ],
    )

    return Bootstrap().build_from_instance(instance)


app = FastAPI(
    title="FlowForge API",
    description="HTTP API and web demo for FlowForge.",
    version="1.0.0",
)

application = create_application()


@app.get("/")
def root() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "flowforge",
        "instance": application.instance.name,
        "capabilities": [
            capability.name
            for capability in application.capability_manager.all()
        ],
    }


@app.post(
    "/message",
    response_model=MessageResponse,
)
def message_endpoint(
    request: MessageRequest,
) -> MessageResponse:
    response = application.chat(
        session_id=request.user_id,
        message=request.message,
    )

    return MessageResponse(
        user_id=request.user_id,
        response=response.text,
    )


@app.post("/reset")
def reset_session(
    request: ResetRequest,
) -> dict[str, str]:
    application.reset_session(request.user_id)

    return {
        "status": "ok",
        "user_id": request.user_id,
        "message": "Session reset successfully",
    }


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "healthy",
        "service": "flowforge",
        "instance": application.instance.name,
        "active_sessions": application.conversation_store.count(),
    }


@app.get("/demo", response_class=HTMLResponse)
def demo_page() -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FlowForge Demo</title>

        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #111827, #1f2937);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 24px;
            }}

            .container {{
                width: 100%;
                max-width: 760px;
                background: #ffffff;
                border-radius: 18px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
                overflow: hidden;
            }}

            .header {{
                background: #111827;
                color: white;
                padding: 24px;
            }}

            .header h1 {{
                margin: 0 0 8px;
                font-size: 26px;
            }}

            .subtitle {{
                margin: 0;
                color: #d1d5db;
                font-size: 14px;
            }}

            #chat {{
                padding: 20px;
                min-height: 360px;
                max-height: 440px;
                overflow-y: auto;
                background: #f9fafb;
                display: flex;
                flex-direction: column;
                gap: 12px;
                white-space: pre-wrap;
            }}

            .message {{
                max-width: 85%;
                padding: 12px 14px;
                border-radius: 14px;
                line-height: 1.4;
                font-size: 15px;
            }}

            .message.user {{
                align-self: flex-end;
                background: #2563eb;
                color: white;
                border-bottom-right-radius: 4px;
            }}

            .message.bot {{
                align-self: flex-start;
                background: #e5e7eb;
                color: #111827;
                border-bottom-left-radius: 4px;
            }}

            .message.error {{
                align-self: flex-start;
                background: #fee2e2;
                color: #991b1b;
                border-bottom-left-radius: 4px;
            }}

            .input-row {{
                display: flex;
                gap: 10px;
                padding: 18px;
                border-top: 1px solid #e5e7eb;
                background: white;
            }}

            input {{
                flex: 1;
                min-width: 0;
                padding: 13px 14px;
                font-size: 16px;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                outline: none;
            }}

            input:focus {{
                border-color: #2563eb;
            }}

            button {{
                padding: 13px 20px;
                font-size: 16px;
                border: none;
                border-radius: 10px;
                background: #111827;
                color: white;
                cursor: pointer;
            }}

            button:hover {{
                background: #374151;
            }}

            button:disabled {{
                opacity: 0.6;
                cursor: not-allowed;
            }}

            .reset-button {{
                background: #6b7280;
            }}

            .reset-button:hover {{
                background: #4b5563;
            }}

            .hint {{
                padding: 0 18px 18px;
                font-size: 13px;
                color: #6b7280;
            }}

            @media (max-width: 640px) {{
                body {{
                    padding: 0;
                }}

                .container {{
                    min-height: 100vh;
                    border-radius: 0;
                }}

                .input-row {{
                    flex-wrap: wrap;
                }}

                input {{
                    flex-basis: 100%;
                }}
            }}
        </style>
    </head>

    <body>
        <div class="container">
            <div class="header">
                <h1>FlowForge Demo</h1>
                <p class="subtitle">
                    Asistente: {application.instance.name}
                </p>
            </div>

            <div id="chat"></div>

            <div class="input-row">
                <input
                    id="messageInput"
                    type="text"
                    placeholder="Escribe un mensaje..."
                    autocomplete="off"
                    autofocus
                >
                <button id="sendButton" onclick="sendMessage()">
                    Enviar
                </button>
                <button
                    id="resetButton"
                    class="reset-button"
                    onclick="resetChat()"
                >
                    Nueva conversación
                </button>
            </div>

            <div class="hint">
                Prueba: hola · reservar · ¿qué días hay disponibles?
            </div>
        </div>

        <script>
            const userId = "demo_user";
            const chat = document.getElementById("chat");
            const input = document.getElementById("messageInput");
            const sendButton = document.getElementById("sendButton");
            const resetButton = document.getElementById("resetButton");

            function addMessage(text, cssClass) {{
                const div = document.createElement("div");
                div.className = "message " + cssClass;
                div.textContent = text;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }}

            function setBusy(isBusy) {{
                input.disabled = isBusy;
                sendButton.disabled = isBusy;
                resetButton.disabled = isBusy;
            }}

            addMessage(
                "Bienvenido. Escribe 'hola' para comenzar.",
                "bot"
            );

            async function sendMessage() {{
                const message = input.value.trim();

                if (!message) {{
                    return;
                }}

                addMessage(message, "user");
                input.value = "";
                setBusy(true);

                try {{
                    const response = await fetch("/message", {{
                        method: "POST",
                        headers: {{
                            "Content-Type": "application/json"
                        }},
                        body: JSON.stringify({{
                            user_id: userId,
                            message: message
                        }})
                    }});

                    if (!response.ok) {{
                        throw new Error(
                            `HTTP ${{response.status}}`
                        );
                    }}

                    const data = await response.json();
                    addMessage(data.response, "bot");
                }} catch (error) {{
                    console.error(error);
                    addMessage(
                        "No se pudo conectar con FlowForge.",
                        "error"
                    );
                }} finally {{
                    setBusy(false);
                    input.focus();
                }}
            }}

            async function resetChat() {{
                setBusy(true);

                try {{
                    const response = await fetch("/reset", {{
                        method: "POST",
                        headers: {{
                            "Content-Type": "application/json"
                        }},
                        body: JSON.stringify({{
                            user_id: userId
                        }})
                    }});

                    if (!response.ok) {{
                        throw new Error(
                            `HTTP ${{response.status}}`
                        );
                    }}

                    chat.innerHTML = "";
                    addMessage(
                        "Nueva conversación iniciada. "
                        + "Escribe 'hola' para comenzar.",
                        "bot"
                    );
                }} catch (error) {{
                    console.error(error);
                    addMessage(
                        "No se pudo reiniciar la conversación.",
                        "error"
                    );
                }} finally {{
                    setBusy(false);
                    input.focus();
                }}
            }}

            input.addEventListener(
                "keydown",
                function (event) {{
                    if (event.key === "Enter") {{
                        sendMessage();
                    }}
                }}
            );
        </script>
    </body>
    </html>
    """


@app.get("/widget", response_class=HTMLResponse)
def widget_page() -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FlowForge Widget</title>

        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                padding: 0;
                background: transparent;
                font-family: Arial, sans-serif;
            }}

            .container {{
                width: 100%;
                height: 100vh;
                min-height: 560px;
                background: #ffffff;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }}

            .header {{
                background: #111827;
                color: white;
                padding: 16px;
            }}

            .header h1 {{
                margin: 0 0 8px;
                font-size: 22px;
            }}

            .subtitle {{
                margin: 0;
                color: #d1d5db;
                font-size: 14px;
            }}

            #chat {{
                flex: 1;
                padding: 14px;
                overflow-y: auto;
                background: #f9fafb;
                display: flex;
                flex-direction: column;
                gap: 12px;
                white-space: pre-wrap;
            }}

            .message {{
                max-width: 85%;
                padding: 12px 14px;
                border-radius: 14px;
                line-height: 1.4;
                font-size: 15px;
            }}

            .message.user {{
                align-self: flex-end;
                background: #2563eb;
                color: white;
                border-bottom-right-radius: 4px;
            }}

            .message.bot {{
                align-self: flex-start;
                background: #e5e7eb;
                color: #111827;
                border-bottom-left-radius: 4px;
            }}

            .message.error {{
                align-self: flex-start;
                background: #fee2e2;
                color: #991b1b;
                border-bottom-left-radius: 4px;
            }}

            .input-row {{
                display: flex;
                gap: 8px;
                padding: 12px;
                border-top: 1px solid #e5e7eb;
                background: white;
            }}

            input {{
                flex: 1;
                min-width: 0;
                padding: 11px 12px;
                font-size: 15px;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                outline: none;
            }}

            input:focus {{
                border-color: #2563eb;
            }}

            button {{
                padding: 10px 12px;
                font-size: 14px;
                border: none;
                border-radius: 10px;
                background: #111827;
                color: white;
                cursor: pointer;
            }}

            button:hover {{
                background: #374151;
            }}

            button:disabled {{
                opacity: 0.6;
                cursor: not-allowed;
            }}

            .reset-button {{
                background: #6b7280;
            }}

            .reset-button:hover {{
                background: #4b5563;
            }}

            .hint {{
                padding: 0 12px 12px;
                font-size: 12px;
                color: #6b7280;
            }}
        </style>
    </head>

    <body>
        <div class="container">
            <div class="header">
                <h1>FlowForge</h1>
                <p class="subtitle">
                    Asistente: {application.instance.name}
                </p>
            </div>

            <div id="chat"></div>

            <div class="input-row">
                <input
                    id="messageInput"
                    type="text"
                    placeholder="Escribe un mensaje..."
                    autocomplete="off"
                    autofocus
                >
                <button id="sendButton" onclick="sendMessage()">
                    Enviar
                </button>
                <button
                    id="resetButton"
                    class="reset-button"
                    onclick="resetChat()"
                >
                    Nuevo
                </button>
            </div>

            <div class="hint">
                Prueba: hola · reservar
            </div>
        </div>

        <script>
            const userId = "demo_user";
            const chat = document.getElementById("chat");
            const input = document.getElementById("messageInput");
            const sendButton = document.getElementById("sendButton");
            const resetButton = document.getElementById("resetButton");

            function addMessage(text, cssClass) {{
                const div = document.createElement("div");
                div.className = "message " + cssClass;
                div.textContent = text;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }}

            function setBusy(isBusy) {{
                input.disabled = isBusy;
                sendButton.disabled = isBusy;
                resetButton.disabled = isBusy;
            }}

            addMessage(
                "Bienvenido. Escribe 'hola' para comenzar.",
                "bot"
            );

            async function sendMessage() {{
                const message = input.value.trim();

                if (!message) {{
                    return;
                }}

                addMessage(message, "user");
                input.value = "";
                setBusy(true);

                try {{
                    const response = await fetch("/message", {{
                        method: "POST",
                        headers: {{
                            "Content-Type": "application/json"
                        }},
                        body: JSON.stringify({{
                            user_id: userId,
                            message: message
                        }})
                    }});

                    if (!response.ok) {{
                        throw new Error(
                            `HTTP ${{response.status}}`
                        );
                    }}

                    const data = await response.json();
                    addMessage(data.response, "bot");
                }} catch (error) {{
                    console.error(error);
                    addMessage(
                        "No se pudo conectar con FlowForge.",
                        "error"
                    );
                }} finally {{
                    setBusy(false);
                    input.focus();
                }}
            }}

            async function resetChat() {{
                setBusy(true);

                try {{
                    const response = await fetch("/reset", {{
                        method: "POST",
                        headers: {{
                            "Content-Type": "application/json"
                        }},
                        body: JSON.stringify({{
                            user_id: userId
                        }})
                    }});

                    if (!response.ok) {{
                        throw new Error(
                            `HTTP ${{response.status}}`
                        );
                    }}

                    chat.innerHTML = "";
                    addMessage(
                        "Nueva conversación iniciada. "
                        + "Escribe 'hola' para comenzar.",
                        "bot"
                    );
                }} catch (error) {{
                    console.error(error);
                    addMessage(
                        "No se pudo reiniciar la conversación.",
                        "error"
                    );
                }} finally {{
                    setBusy(false);
                    input.focus();
                }}
            }}

            input.addEventListener(
                "keydown",
                function (event) {{
                    if (event.key === "Enter") {{
                        sendMessage();
                    }}
                }}
            );
        </script>
    </body>
    </html>
    """


@app.get("/test_embed", response_class=HTMLResponse)
def test_embed() -> str:
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Demo cliente FlowForge</title>

        <style>
            * {
                box-sizing: border-box;
            }

            body {
                font-family: Arial, sans-serif;
                margin: 40px;
                background: #f5f5f5;
            }

            .content {
                max-width: 900px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 12px;
            }

            #chatButton {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 70px;
                height: 70px;
                border: none;
                border-radius: 50%;
                background: #111827;
                color: white;
                cursor: pointer;
                font-size: 16px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            }

            #chatWidget {
                position: fixed;
                bottom: 100px;
                right: 20px;
                width: 420px;
                height: 620px;
                display: none;
                background: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
            }

            #chatWidget iframe {
                width: 100%;
                height: 100%;
                border: none;
                display: block;
            }

            @media (max-width: 500px) {
                body {
                    margin: 20px;
                }

                #chatWidget {
                    right: 10px;
                    bottom: 95px;
                    width: calc(100vw - 20px);
                    height: calc(100vh - 120px);
                }

                #chatButton {
                    right: 10px;
                    bottom: 10px;
                }
            }
        </style>
    </head>

    <body>
        <div class="content">
            <h1>Web de ejemplo</h1>

            <p>
                Esta página simula la web de un cliente.
            </p>

            <p>
                Pulsa el botón para abrir o cerrar el chatbot.
            </p>
        </div>

        <button
            id="chatButton"
            type="button"
            aria-controls="chatWidget"
            aria-expanded="false"
        >
            💬 Chat
        </button>

        <div id="chatWidget">
            <iframe
                src="/widget"
                title="Asistente FlowForge"
            ></iframe>
        </div>

        <script>
            const button = document.getElementById("chatButton");
            const widget = document.getElementById("chatWidget");

            button.addEventListener("click", () => {
                const isOpen = widget.style.display === "block";

                widget.style.display = isOpen
                    ? "none"
                    : "block";

                button.setAttribute(
                    "aria-expanded",
                    String(!isOpen)
                );
            });
        </script>
    </body>
    </html>
    """