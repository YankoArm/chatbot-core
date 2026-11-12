from chatbot.connectors.whatsapp.parser import WhatsAppPayloadParser


def test_guided_menu_button_routes_by_id():
    message = {
        "from": "customer",
        "id": "wamid.button",
        "type": "interactive",
        "interactive": {
            "type": "button_reply",
            "button_reply": {
                "id": "ff_menu_booking_es",
                "title": "Texto visible del boton",
            },
        },
    }
    value = {
        "metadata": {"phone_number_id": "business-number"},
        "messages": [message],
    }
    payload = {"entry": [{"changes": [{"value": value}]}]}
    parser = WhatsAppPayloadParser()

    result = parser.parse(payload)

    assert result is not None
    assert result.text == "quiero reservar"
    assert result.user_id == "customer"
    assert result.phone_number_id == "business-number"
    assert result.message_id == "wamid.button"

    message["interactive"]["button_reply"]["id"] = "unknown"
    assert parser.parse(payload) is None


def test_interactive_reply_uses_the_incoming_business_number():
    from unittest.mock import Mock

    from chatbot.connectors.whatsapp.message_handler import (
        WhatsAppButtonReply,
        WhatsAppMessageHandler,
    )
    from chatbot.connectors.whatsapp.tenant_graph_sender import (
        TenantWhatsAppGraphSender,
    )

    graph = Mock()
    provider = Mock()
    provider.get_client.return_value = graph
    reply = WhatsAppButtonReply(
        text="Hola",
        buttons=(("ff_menu_prices_es", "Ver precios"),),
        fallback_text="Hola. Escribe precios.",
    )
    orchestrator = Mock()
    orchestrator.handle.return_value = reply
    handler = WhatsAppMessageHandler(
        parser=WhatsAppPayloadParser(),
        orchestrator=orchestrator,
        sender=TenantWhatsAppGraphSender(graph_client_provider=provider),
    )
    value = {
        "metadata": {"phone_number_id": "business-number"},
        "messages": [
            {"from": "customer", "id": "wamid.hello", "text": {"body": "hola"}},
        ],
    }
    payload = {"entry": [{"changes": [{"value": value}]}]}

    handler.handle(payload)
    handler.handle(payload)

    provider.get_client.assert_called_once_with("business-number")
    graph.send_reply_buttons.assert_called_once_with(
        to="customer",
        text=reply.text,
        buttons=reply.buttons,
    )
    graph.send_text_message.assert_not_called()


def test_tarot_activation_sends_buttons_and_handles_booking_without_calendar():
    from dataclasses import replace
    from unittest.mock import Mock

    from chatbot.clients.registry import build_client_definition
    from chatbot.connectors.whatsapp.bootstrap import (
        build_tenant_whatsapp_message_handler,
    )
    from run_flowforge import build_tenant_application

    original = build_client_definition("tarot_alvin")
    definition = replace(
        original,
        settings={
            **original.settings,
            "knowledge": {
                **original.settings.get("knowledge", {}),
                "greetings": {
                    "menu": {
                        "enabled": True,
                        "items": {
                            "services": True,
                            "booking": True,
                            "faq": True,
                            "human_transfer": True,
                        },
                    },
                },
            },
        },
    )
    application = build_tenant_application(
        definition=definition,
        calendar_service=None,
        booking_repository=None,
    )
    router = Mock()
    router.resolve_client_id.return_value = definition.id
    registry = Mock()
    registry.get_application.return_value = application
    provider = Mock()
    graph = provider.get_client.return_value
    handler = build_tenant_whatsapp_message_handler(
        tenant_router=router,
        application_registry=registry,
        graph_client_provider=provider,
    )

    def receive(message_id, **content):
        value = {
            "metadata": {"phone_number_id": "business-number"},
            "messages": [
                {"from": "customer", "id": message_id, **content},
            ],
        }
        handler.handle({"entry": [{"changes": [{"value": value}]}]})

    receive("wamid.hello", type="text", text={"body": "hola"})
    graph.send_text_message.assert_called_once()
    assert "TAROT" in graph.send_text_message.call_args.kwargs["text"].upper()
    graph.send_reply_buttons.assert_not_called()

    receive("wamid.activate", type="text", text={"body": "TAROT"})
    graph.send_reply_buttons.assert_called_once()
    sent = graph.send_reply_buttons.call_args.kwargs
    assert sent["to"] == "customer"
    assert tuple(button_id for button_id, _ in sent["buttons"]) == (
        "ff_menu_prices_es",
        "ff_menu_booking_es",
        "ff_menu_human_es",
    )
    assert "puedes escribir tu pregunta" in sent["text"]
    assert "Opciones r\u00e1pidas:" not in sent["text"]

    receive(
        "wamid.booking-button",
        type="interactive",
        interactive={
            "type": "button_reply",
            "button_reply": {
                "id": "ff_menu_booking_es",
                "title": "Reservar cita",
            },
        },
    )
    button_text = graph.send_text_message.call_args.kwargs["text"]
    assert "no est\u00e1 disponible" in button_text
    assert "hablar con una persona" in button_text

    receive(
        "wamid.booking-text",
        type="text",
        text={"body": "quiero reservar"},
    )
    assert graph.send_text_message.call_args.kwargs["text"] == button_text
    graph.send_reply_buttons.assert_called_once()
