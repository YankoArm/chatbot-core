from chatbot.application.bootstrap import Bootstrap
from chatbot.business_templates import (
    create_hairdressing_template,
)
from chatbot.capabilities.greeting import (
    GreetingCapability,
)
from chatbot.clients import (
    create_hairdressing_demo_definition,
)
from chatbot.conversation import ConversationContext


def test_greeting_does_not_capture_price_request():
    capability = GreetingCapability()
    context = ConversationContext(
        session_id="greeting-priority-session",
    )

    assert capability.can_handle(
        context,
        "Hola, ¿me puedes decir los precios?",
    ) is False


def test_price_request_with_greeting_uses_faq():
    app = Bootstrap().build_from_definition(
        template=create_hairdressing_template(),
        definition=create_hairdressing_demo_definition(),
    )

    session_id = "hairdressing-greeting-price-session"

    app.chat(
        session_id=session_id,
        message="Peluquería",
    )

    response = app.chat(
        session_id=session_id,
        message="Hola, ¿me puedes decir los precios?",
    )

    assert response.metadata["capability"] == "faq"
    assert response.metadata["answer_found"] is True
    assert "Corte de mujer — 25 €" in response.text