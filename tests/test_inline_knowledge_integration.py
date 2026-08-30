from chatbot.application import Bootstrap
from chatbot.instances import Instance


def test_application_answers_with_inline_instance_faq(
    tmp_path,
) -> None:
    instance = Instance(
        id="salon_nuevo",
        name="Salón Nuevo",
        default_language="es",
        supported_languages=[
            "es",
        ],
        capabilities=[
            "faq",
        ],
        settings={
            "knowledge": {
                "company": {
                    "name": "Salón Nuevo",
                    "phone": "+34600123123",
                },
                "faq": {
                    "location": {
                        "keywords": [
                            "donde estais",
                            "direccion",
                            "ubicacion",
                        ],
                        "answers": {
                            "es": (
                                "Estamos en Calle Mayor, 10, Madrid."
                            ),
                        },
                    },
                },
            },
        },
    )

    bootstrap = Bootstrap(
        knowledge_root=tmp_path,
    )
    application = bootstrap.build_from_instance(
        instance
    )

    response = application.chat(
        session_id="inline-faq-integration",
        message="¿Dónde estáis?",
    )

    assert response.text == (
        "Estamos en Calle Mayor, 10, Madrid."
    )
    assert response.metadata[
        "capability"
    ] == "faq"
    assert response.metadata[
        "answer_found"
    ] is True

    context = application.conversation_store.get(
        "inline-faq-integration"
    )

    assert context is not None
    assert context.knowledge_service.get(
        "company",
        "phone",
    ) == "+34600123123"