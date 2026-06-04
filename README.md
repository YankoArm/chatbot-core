# Chatbot Core

Modular chatbot framework built with Python and FastAPI.

Chatbot Core is a reusable framework designed to build conversational assistants using configurable templates, state-based flows and decoupled services. The project focuses on maintainability, extensibility and rapid adaptation to different business scenarios.

---

## Features

### Core Architecture

* Modular architecture
* State-based conversation flows
* Session management
* Template-driven configuration
* Service-oriented design
* Dynamic action registry

### Persistence

* JSON session persistence
* Automatic session recovery
* Session reset support

### Interfaces

* CLI interface
* FastAPI REST API
* Web demo
* Embeddable chatbot widget
* Floating widget integration demo

### Testing

* Automated tests with pytest
* Service testing
* Configuration testing
* Flow testing
* Persistence testing

---

## Available Templates

### Booking

Reservation-oriented chatbot.

Examples:

* Appointments
* Consultations
* Services
* Scheduling

### FAQ

Frequently asked questions chatbot.

Examples:

* Customer support
* Information services
* Product information

### Sales

Lead generation and sales chatbot.

Examples:

* Product inquiries
* Service sales
* Customer acquisition

---

## Project Structure

```text
chatbot_core/
│
├── chatbot/
│   ├── bots/
│   ├── config/
│   ├── core/
│   ├── interfaces/
│   ├── services/
│   ├── storage/
│   └── templates/
│
├── docs/
├── tests/
├── README.md
└── main.py
```

---

## Configuration

The active chatbot template can be configured in:

```python
chatbot/config/settings.py
```

Example:

```python
ACTIVE_TEMPLATE = "sales"

DEFAULT_LANGUAGE = "es"

SUPPORTED_LANGUAGES = [
    "es",
    "en"
]
```

---

## Run CLI

```bash
python main.py
```

---

## Run API

```bash
uvicorn chatbot.interfaces.api:app --reload
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Demo Pages

Main demo:

```text
http://127.0.0.1:8000/demo
```

Embeddable widget:

```text
http://127.0.0.1:8000/widget
```

Widget integration example:

```text
http://127.0.0.1:8000/test_embed
```

---

## Run Tests

```bash
pytest
```

Current status:

```text
12 tests passing
```

---

## Technologies

* Python 3
* FastAPI
* Pytest
* HTML
* CSS
* JavaScript

---

## Roadmap

### v0.9

* Jinja2 templates
* Improved frontend structure
* Enhanced widget customization
* Public deployment

### v1.0

* SQLite support
* JSON template loading
* WhatsApp adapter
* Telegram adapter
* Admin panel

---

## License

MIT License (planned)

---

## Author

Yanko Armijo

Cybersecurity | Python Developer | Tool Builder
