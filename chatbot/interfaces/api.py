# chatbot/interfaces/api.py

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse

from chatbot.core.engine import ChatEngine
from chatbot.bots.flow_bot import FlowBot
from chatbot.core.bot_config import BotConfig
from chatbot.templates.registry import TEMPLATE_REGISTRY
from chatbot.config.settings import (
    ACTIVE_TEMPLATE,
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
)


class MessageRequest(BaseModel):
    user_id: str
    message: str


class MessageResponse(BaseModel):
    user_id: str
    response: str

class ResetRequest(BaseModel):
    user_id: str


def create_engine() -> ChatEngine:
    template = TEMPLATE_REGISTRY[ACTIVE_TEMPLATE]

    config = BotConfig.from_template(
        template,
        default_language=DEFAULT_LANGUAGE,
        supported_languages=SUPPORTED_LANGUAGES,
    )

    bot = FlowBot(config)
    return ChatEngine(bot)


app = FastAPI(title="Chatbot Core API")

engine = create_engine()


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "chatbot_core",
        "active_template": ACTIVE_TEMPLATE,
    }


@app.post("/message", response_model=MessageResponse)
def message_endpoint(request: MessageRequest):
    response = engine.process_message(
        user_id=request.user_id,
        message=request.message,
    )

    return MessageResponse(
        user_id=request.user_id,
        response=response,
    )

@app.post("/reset")
def reset_session(request: ResetRequest):
    if request.user_id in engine.sessions:
        del engine.sessions[request.user_id]
        engine.session_store.save_all(engine.sessions)

    return {
        "status": "ok",
        "user_id": request.user_id,
        "message": "Session reset successfully",
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.get("/demo", response_class=HTMLResponse)
def demo_page():
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Chatbot Core Demo</title>
        <style>
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
                box-shadow: 0 20px 60px rgba(0,0,0,0.25);
                overflow: hidden;
            }}

            .header {{
                background: #111827;
                color: white;
                padding: 24px;
            }}

            .header h1 {{
                margin: 0 0 8px 0;
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

            .input-row {{
                display: flex;
                gap: 10px;
                padding: 18px;
                border-top: 1px solid #e5e7eb;
                background: white;
            }}

            input {{
                flex: 1;
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

            .reset-button {{
                background: #6b7280;
            }}

            .reset-button:hover {{
                background: #4b5563;
            }}

            .hint {{
                padding: 0 18px 18px 18px;
                font-size: 13px;
                color: #6b7280;
            }}
        </style>
    </head>

    <body>
        <div class="container">
            <div class="header">
                <h1>Chatbot Core Demo</h1>
                <p class="subtitle">Template activo: {ACTIVE_TEMPLATE}</p>
            </div>

            <div id="chat"></div>

            <div class="input-row">
                <input id="messageInput" type="text" placeholder="Escribe un mensaje..." autofocus />
                <button onclick="sendMessage()">Enviar</button>
                <button class="reset-button" onclick="resetChat()">Nueva conversación</button>
            </div>

            <div class="hint">
                Prueba: hola · 1 · 2 · 3 · menu
            </div>
        </div>

        <script>
            const userId = "demo_user";
            const chat = document.getElementById("chat");
            const input = document.getElementById("messageInput");

            function addMessage(text, cssClass) {{
                const div = document.createElement("div");
                div.className = "message " + cssClass;
                div.textContent = text;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }}

            addMessage("Bienvenido. Escribe 'hola' para comenzar.", "bot");

            async function sendMessage() {{
                const message = input.value.trim();

                if (!message) {{
                    return;
                }}

                addMessage(message, "user");
                input.value = "";

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

                const data = await response.json();
                addMessage(data.response, "bot");
            }}

            async function resetChat() {{
                await fetch("/reset", {{
                    method: "POST",
                    headers: {{
                        "Content-Type": "application/json"
                    }},
                    body: JSON.stringify({{
                        user_id: userId
                    }})
                }});

                chat.innerHTML = "";
                addMessage("Nueva conversación iniciada. Escribe 'hola' para comenzar.", "bot");
                input.focus();
            }}

            input.addEventListener("keydown", function(event) {{
                if (event.key === "Enter") {{
                    sendMessage();
                }}
            }});
        </script>
    </body>
    </html>
    """

@app.get("/widget", response_class=HTMLResponse)
def widget_page():
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Chatbot Core Demo</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: transparent;
                font-family: Arial, sans-serif;
            }}

            .container {{
                width: 420px;
                height: 620px;
                background: #ffffff;
                border-radius: 18px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.25);
                overflow: hidden;
            }}

            .header {{
                background: #111827;
                color: white;
                padding: 16px;
            }}

            .header h1 {{
                margin: 0 0 8px 0;
                font-size: 26px;
            }}

            .subtitle {{
                margin: 0;
                color: #d1d5db;
                font-size: 14px;
            }}

            #chat {{
                padding: 14px;
                height: 380px;
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

            .input-row {{
                display: flex;
                gap: 10px;
                padding: 18px;
                border-top: 1px solid #e5e7eb;
                background: white;
            }}

            input {{
                flex: 1;
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

            .reset-button {{
                background: #6b7280;
            }}

            .reset-button:hover {{
                background: #4b5563;
            }}

            .hint {{
                padding: 0 18px 18px 18px;
                font-size: 13px;
                color: #6b7280;
            }}
        </style>
    </head>

    <body>
        <div class="container">
            <div class="header">
                <h1>Chatbot Core Demo</h1>
                <p class="subtitle">Template activo: {ACTIVE_TEMPLATE}</p>
            </div>

            <div id="chat"></div>

            <div class="input-row">
                <input id="messageInput" type="text" placeholder="Escribe un mensaje..." autofocus />
                <button onclick="sendMessage()">Enviar</button>
                <button class="reset-button" onclick="resetChat()">Nuevo chat</button>
            </div>

            <div class="hint">
                Prueba: hola · 1 · 2 · 3 · menu
            </div>
        </div>

        <script>
            const userId = "demo_user";
            const chat = document.getElementById("chat");
            const input = document.getElementById("messageInput");

            function addMessage(text, cssClass) {{
                const div = document.createElement("div");
                div.className = "message " + cssClass;
                div.textContent = text;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }}

            addMessage("Bienvenido. Escribe 'hola' para comenzar.", "bot");

            async function sendMessage() {{
                const message = input.value.trim();

                if (!message) {{
                    return;
                }}

                addMessage(message, "user");
                input.value = "";

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

                const data = await response.json();
                addMessage(data.response, "bot");
            }}

            async function resetChat() {{
                await fetch("/reset", {{
                    method: "POST",
                    headers: {{
                        "Content-Type": "application/json"
                    }},
                    body: JSON.stringify({{
                        user_id: userId
                    }})
                }});

                chat.innerHTML = "";
                addMessage("Nueva conversación iniciada. Escribe 'hola' para comenzar.", "bot");
                input.focus();
            }}

            input.addEventListener("keydown", function(event) {{
                if (event.key === "Enter") {{
                    sendMessage();
                }}
            }});
        </script>
    </body>
    </html>
    """

@app.get("/test_embed", response_class=HTMLResponse)
def test_embed():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Demo Cliente</title>

        <style>
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

            iframe {
                border: none;
                width: 420px;
                height: 620px;
                margin-top: 20px;
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
                box-shadow: 0 4px 20px rgba(0,0,0,0.25);
            }

            #chatWidget {
                position: fixed;
                bottom: 100px;
                right: 20px;
                width: 420px;
                height: 560px;
                display: none;
                background: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 8px 30px rgba(0,0,0,0.3);
                padding: 0;
            }

            #chatWidget iframe {
                width: 420px;
                height: 560px;
                border: none;
                display: block;
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
                Debajo aparece el chatbot incrustado mediante iframe.
            </p>

            <button id="chatButton">
                💬 Chat
            </button>

            <div id="chatWidget">
                <iframe src="/widget"></iframe>
            </div>

        </div>

    <script>
        const button = document.getElementById("chatButton");
        const widget = document.getElementById("chatWidget");

        button.addEventListener("click", () => {
            if (widget.style.display === "block") {
                widget.style.display = "none";
            } else {
                widget.style.display = "block";
            }
        });
    </script>

    </body>
    </html>
    """