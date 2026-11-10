from dataclasses import replace

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from chatbot.api.web_chat_mount import mount_web_chat
from chatbot.clients.registry import build_client_definition
from run_flowforge import build_tenant_application


WIDGET_ID = "wf_local_tarot_demo_2026"

original = build_client_definition("tarot_alvin")

definition = replace(
    original,
    settings={
        **original.settings,
        "web_chat": {
            "enabled": True,
            "widget_id": WIDGET_ID,
        },
    },
    metadata={
        **original.metadata,
        "admin_status": "active",
    },
)


class DemoRepository:
    def list_all(self):
        return (definition,)


app = FastAPI(title="FlowForge Local Web Demo")

mount_web_chat(
    app,
    repository=DemoRepository(),
    application_factory=lambda tenant: (
        build_tenant_application(
            definition=tenant,
            calendar_service=None,
            booking_repository=None,
            lead_repository=None,
        )
    ),
    enabled=True,
)


@app.get("/", response_class=HTMLResponse)
def demo_page():
    return """
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <meta name="viewport"
            content="width=device-width, initial-scale=1">
      <title>FlowForge - Demo Chat Web</title>
      <style>
        body {
          font-family: system-ui, sans-serif;
          background: #f1f5f9;
          color: #0f172a;
          padding: 45px 20px;
        }
        main {
          max-width: 800px;
          margin: auto;
        }
        section {
          background: white;
          padding: 30px;
          border-radius: 16px;
        }
      </style>
    </head>
    <body>
      <main>
        <section>
          <h1>FlowForge - Demostraci&#243;n Web</h1>
          <p>Esta es una p&#225;gina de demostraci&#243;n local.</p>
          <p>El asistente utiliza el motor real de Tarot Alvin.</p>
          <p>Pulsa el bot&#243;n de chat de la esquina inferior
             derecha para comenzar.</p>
        </section>
      </main>

      <script src="/webchat/embed.js"
        data-flowforge-widget="wf_local_tarot_demo_2026"
        defer></script>
    </body>
    </html>
    """
