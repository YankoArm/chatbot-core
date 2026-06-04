# Chatbot Core

Framework modular para crear chatbots reutilizables basados en reglas, estados, templates y servicios desacoplados.

## Características actuales

- Motor central reutilizable
- Sistema de sesiones
- Persistencia básica en JSON
- Templates configurables
- Registro dinámico de acciones
- Menús generados desde configuración
- Interfaz CLI
- API con FastAPI
- Demo web en `/demo`
- Tests automáticos con pytest

## Templates disponibles

- `booking`
- `faq`
- `sales`

El template activo se configura en:

```python
chatbot/config/settings.py

ACTIVE_TEMPLATE = "sales"
DEFAULT_LANGUAGE = "es"
SUPPORTED_LANGUAGES = ["es", "en"]

Ejecutar en consola
python main.py
Ejecutar API
uvicorn chatbot.interfaces.api:app --reload

Después abrir:

http://127.0.0.1:8000/docs
Demo web
http://127.0.0.1:8000/demo
Ejecutar tests
pytest
Estado actual
12 tests passing
Roadmap
Mejorar demo web
Añadir SQLite como sistema de persistencia
Cargar templates desde JSON
Añadir interfaz webchat embebible
Preparar adaptador WhatsApp