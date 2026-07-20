from chatbot.instances import Instance


def test_instance_stores_basic_configuration():
    instance = Instance(
        id="tarot_esmeralda",
        name="Tarot Esmeralda",
        capabilities=["booking", "faq"],
        connectors=["google_calendar"],
        channels=["whatsapp", "web_widget"],
    )

    assert instance.id == "tarot_esmeralda"
    assert instance.name == "Tarot Esmeralda"
    assert instance.default_language == "es"
    assert instance.capabilities == ["booking", "faq"]
    assert instance.connectors == ["google_calendar"]
    assert instance.channels == ["whatsapp", "web_widget"]


def test_instance_uses_safe_defaults():
    instance = Instance(
        id="demo",
        name="Demo",
    )

    assert instance.channels == []
    assert instance.capabilities == []
    assert instance.connectors == []
    assert instance.knowledge_path is None
    assert instance.settings == {}