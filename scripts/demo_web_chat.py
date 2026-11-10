from __future__ import annotations

import re
from contextlib import asynccontextmanager
from html import escape
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from chatbot.api.web_chat_mount import mount_web_chat
from chatbot.clients.registry import build_instance_from_definition
from chatbot.instances.sqlite_repository import (
    SQLiteInstanceDefinitionRepository,
)
from run_flowforge import build_tenant_application


DEFAULT_DATABASE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "flowforge_admin.sqlite3"
)


def create_demo_app(
    *,
    database_path: str | Path = DEFAULT_DATABASE,
    client_id: str = "easy_app_code",
) -> FastAPI:
    """Build a local demo from an existing stored client."""
    database = Path(database_path).resolve()

    if not database.is_file():
        raise FileNotFoundError(
            f"No existe la base de datos de la demo: {database}"
        )

    repository = SQLiteInstanceDefinitionRepository(
        database_path=database,
    )

    try:
        definition = repository.get(client_id)

        if definition is None:
            raise ValueError(
                f"No existe la empresa '{client_id}' en SQLite."
            )

        web = definition.settings.get("web_chat") or {}

        if not isinstance(web, dict):
            raise ValueError("La configuracion Chat Web no es valida.")

        widget_id = web.get("widget_id")

        if (
            not isinstance(widget_id, str)
            or re.fullmatch(r"[A-Za-z0-9_-]{12,96}", widget_id) is None
        ):
            raise ValueError(
                f"Configura el widget Chat Web de '{client_id}' "
                "desde el panel antes de iniciar la demo."
            )

        if web.get("enabled") is not True:
            raise ValueError(
                f"Activa el widget Chat Web de '{client_id}' en el panel."
            )

        if definition.metadata.get("admin_status") != "active":
            raise ValueError(
                f"Activa la empresa '{client_id}' en el panel."
            )

        if "web" not in build_instance_from_definition(definition).channels:
            raise ValueError(
                f"La empresa '{client_id}' no tiene el canal Web."
            )

        class DemoRepository:
            def list_all(self):
                # Reload settings while keeping this demo scoped to one client.
                current = repository.get(client_id)
                if current is None:
                    return ()

                current_web = current.settings.get("web_chat")
                current_widget_id = (
                    current_web.get("widget_id")
                    if isinstance(current_web, dict)
                    else None
                )

                if not isinstance(current_widget_id, str):
                    return ()

                # Preserve the shared resolver's duplicate-ID rejection.
                return tuple(
                    item
                    for item in repository.list_all()
                    if (
                        isinstance(item.settings.get("web_chat"), dict)
                        and item.settings["web_chat"].get("widget_id")
                        == current_widget_id
                    )
                )

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            try:
                yield
            finally:
                repository.close()

        app = FastAPI(
            title="FlowForge Local Web Demo",
            lifespan=lifespan,
        )

        mount_web_chat(
            app,
            repository=DemoRepository(),
            application_factory=lambda tenant: build_tenant_application(
                definition=tenant,
                calendar_service=None,
                booking_repository=None,
                lead_repository=None,
            ),
            enabled=True,
        )

        @app.get("/", response_class=HTMLResponse)
        def demo_page():
            current = repository.get(client_id)
            if current is None:
                return HTMLResponse(
                    "Empresa no disponible",
                    status_code=404,
                    headers={"Cache-Control": "no-store"},
                )

            current_web = current.settings.get("web_chat")
            current_widget = (
                current_web.get("widget_id", "")
                if isinstance(current_web, dict)
                else ""
            )
            name = escape(current.name)
            widget = escape(str(current_widget), quote=True)

            return HTMLResponse(
                f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{name} - Demo Chat Web</title>
  <style>
    body {{
      font-family: system-ui, sans-serif;
      background: #f1f5f9;
      color: #0f172a;
      padding: 45px 20px;
    }}
    main {{ max-width: 800px; margin: auto; }}
    section {{
      background: white;
      padding: 30px;
      border-radius: 16px;
    }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>{name}</h1>
      <p>Prueba local del asistente con su configuraci&#243;n guardada.</p>
      <p>Pulsa el bot&#243;n de chat para comenzar.</p>
      <p>Esta demo no agenda citas ni guarda solicitudes de contacto.</p>
    </section>
  </main>
  <script src="/webchat/embed.js"
    data-flowforge-widget="{widget}" defer></script>
</body>
</html>""",
                headers={"Cache-Control": "no-store"},
            )

        return app
    except Exception:
        repository.close()
        raise
