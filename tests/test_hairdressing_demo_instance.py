from chatbot.application.bootstrap import Bootstrap
from chatbot.business_templates import (
    create_hairdressing_template,
)
from chatbot.clients import (
    create_hairdressing_demo_definition,
)


def build_hairdressing_demo_application():
    template = create_hairdressing_template()
    definition = create_hairdressing_demo_definition()

    return Bootstrap().build_from_definition(
        template=template,
        definition=definition,
    )


def test_bootstrap_builds_hairdressing_demo():
    app = build_hairdressing_demo_application()

    assert app.instance.id == "hairdressing_demo"
    assert app.instance.name == "Salón Estilo"
    assert app.instance.template_id == "hairdressing"

    assert app.instance.default_language == "es"
    assert app.instance.supported_languages == [
        "es",
        "en",
    ]

    assert app.instance.capabilities == [
        "greeting",
        "faq",
        "booking",
        "help",
        "human_transfer",
    ]

    assert app.instance.channels == [
        "web",
        "whatsapp",
    ]

    assert app.instance.knowledge_path == (
        "knowledge/hairdressing_demo"
    )

    assert app.instance.settings["business_type"] == (
        "hairdressing"
    )

    assert (
        app.instance.settings["booking"]["enabled"]
        is True
    )

    assert (
        app.instance.settings["booking"]["timezone"]
        == "Europe/Madrid"
    )

    assert (
        app.instance.settings["branding"]["display_name"]
        == "Salón Estilo"
    )

    assert app.instance.metadata["category"] == (
        "beauty_and_personal_care"
    )

    assert app.instance.metadata["owner"] == (
        "Demo comercial de FlowForge"
    )


def test_hairdressing_demo_answers_services_and_prices():
    app = build_hairdressing_demo_application()
    session_id = "hairdressing-services-session"

    app.chat(
        session_id=session_id,
        message="Peluquería",
    )

    response = app.chat(
        session_id=session_id,
        message="¿Qué servicios y precios tenéis?",
    )

    assert response.text == (
        "Estos son nuestros servicios:\n\n"
        "✂️ Corte de mujer — 25 €\n"
        "✂️ Corte de hombre — 18 €\n"
        "🧒 Corte infantil — 15 €\n"
        "💇 Peinado — 25 €\n"
        "🎨 Tinte — desde 45 €\n"
        "✨ Mechas — desde 65 €\n"
        "🌿 Tratamiento capilar — 30 €\n\n"
        "Los precios son orientativos y pueden variar "
        "según el largo y las características del cabello."
    )

    assert response.metadata["capability"] == "faq"
    assert response.metadata["handled"] is True
    assert response.metadata["answer_found"] is True
    assert response.metadata["language"] == "es"


def test_hairdressing_demo_answers_specific_service_price():
    app = build_hairdressing_demo_application()
    session_id = "hairdressing-highlights-price-session"

    app.chat(
        session_id=session_id,
        message="Peluquería",
    )

    response = app.chat(
        session_id=session_id,
        message="¿Cuánto cuestan las mechas?",
    )

    assert response.text == (
        "Las mechas cuestan desde 65 € y suelen durar "
        "aproximadamente 2 horas. El precio final puede "
        "variar según el largo y las características "
        "del cabello."
    )

    assert response.metadata["capability"] == "faq"
    assert response.metadata["answer_found"] is True
    assert response.metadata["language"] == "es"

def test_hairdressing_demo_answers_commercial_questions_in_spanish():
    cases = {
        "¿Qué horario tenéis?": (
            "Abrimos de lunes a viernes de 09:30 a 13:30 "
            "y de 16:00 a 20:00. Los sábados abrimos de "
            "09:30 a 14:00 y los domingos permanecemos cerrados."
        ),
        "¿Dónde estáis?": (
            "Estamos en Calle de Velázquez, 80, 28001 Madrid. "
            "Puedes pedirnos indicaciones si necesitas ayuda "
            "para llegar."
        ),
        "¿Puedo pagar con tarjeta?": (
            "Puedes pagar con tarjeta, efectivo o Bizum "
            "al finalizar el servicio."
        ),
        "¿Cuál es la política de cancelación?": (
            "Puedes cambiar o cancelar tu cita sin coste "
            "avisando con al menos 24 horas de antelación. "
            "Si necesitas hacerlo, escríbenos directamente."
        ),
    }

    for index, (message, expected_answer) in enumerate(
        cases.items()
    ):
        app = build_hairdressing_demo_application()
        session_id = f"hairdressing-commercial-es-{index}"

        app.chat(
            session_id=session_id,
            message="Peluquería",
        )

        response = app.chat(
            session_id=session_id,
            message=message,
        )

        assert response.text == expected_answer
        assert response.metadata["capability"] == "faq"
        assert response.metadata["answer_found"] is True
        assert response.metadata["language"] == "es"


def test_hairdressing_demo_answers_commercial_questions_in_english():
    cases = {
        "What are your opening hours?": (
            "We are open Monday to Friday from 09:30 to 13:30 "
            "and from 16:00 to 20:00. On Saturdays we are open "
            "from 09:30 to 14:00, and we are closed on Sundays."
        ),
        "What is your address?": (
            "We are located at Calle de Velázquez, 80, "
            "28001 Madrid. Ask us for directions if you need "
            "help getting here."
        ),
        "What payment methods do you accept?": (
            "You can pay by card, cash or Bizum after "
            "your service."
        ),
        "What is your cancellation policy?": (
            "You can reschedule or cancel your appointment "
            "free of charge with at least 24 hours' notice. "
            "If you need to do so, message us directly."
        ),
    }

    for index, (message, expected_answer) in enumerate(
        cases.items()
    ):
        app = build_hairdressing_demo_application()
        session_id = f"hairdressing-commercial-en-{index}"

        app.chat(
            session_id=session_id,
            message="Peluquería",
        )

        response = app.chat(
            session_id=session_id,
            message=message,
        )

        assert response.text == expected_answer
        assert response.metadata["capability"] == "faq"
        assert response.metadata["answer_found"] is True
        assert response.metadata["language"] == "en"

def test_hairdressing_demo_answers_hair_coloring_details():
    app = build_hairdressing_demo_application()
    session_id = "hairdressing-coloring-details"

    app.chat(
        session_id=session_id,
        message="Peluquería",
    )

    response = app.chat(
        session_id=session_id,
        message="Cuéntame sobre el tinte",
    )

    assert response.text == (
        "El tinte cuesta desde 45 € y suele durar "
        "aproximadamente 90 minutos. El precio final puede "
        "variar según el largo y las características del cabello."
    )
    assert response.metadata["capability"] == "faq"
    assert response.metadata["answer_found"] is True


def test_hairdressing_demo_preserves_service_context_in_follow_up():
    app = build_hairdressing_demo_application()
    session_id = "hairdressing-service-follow-up"

    app.chat(
        session_id=session_id,
        message="Peluquería",
    )

    first_response = app.chat(
        session_id=session_id,
        message="Cuéntame sobre el tinte",
    )

    follow_up_response = app.chat(
        session_id=session_id,
        message="¿Y cuánto cuesta?",
    )

    assert "El tinte cuesta desde 45 €" in first_response.text
    assert follow_up_response.text == first_response.text
    assert follow_up_response.metadata["capability"] == "faq"
    assert follow_up_response.metadata["answer_found"] is True

def test_hairdressing_demo_answers_all_specific_service_questions():
    cases = {
        "¿Cuánto cuesta el corte de mujer?": (
            "El corte de mujer cuesta 25 € y dura "
            "aproximadamente 45 minutos."
        ),
        "¿Cuánto cuesta el corte de hombre?": (
            "El corte de hombre cuesta 18 € y dura "
            "aproximadamente 30 minutos."
        ),
        "¿Cuánto cuesta el corte infantil?": (
            "El corte infantil cuesta 15 € y dura "
            "aproximadamente 30 minutos."
        ),
        "¿Cuánto cuesta el peinado?": (
            "El peinado cuesta 25 € y dura "
            "aproximadamente 45 minutos."
        ),
        "¿Cuánto cuesta el tratamiento capilar?": (
            "El tratamiento capilar cuesta 30 € y dura "
            "aproximadamente 45 minutos."
        ),
    }

    for index, (message, expected_answer) in enumerate(
        cases.items()
    ):
        app = build_hairdressing_demo_application()
        session_id = f"hairdressing-service-details-{index}"

        app.chat(
            session_id=session_id,
            message="Peluquería",
        )

        response = app.chat(
            session_id=session_id,
            message=message,
        )

        assert response.text == expected_answer
        assert response.metadata["capability"] == "faq"
        assert response.metadata["answer_found"] is True

def test_hairdressing_demo_activation_shows_commercial_menu():
    app = build_hairdressing_demo_application()

    response = app.chat(
        session_id="hairdressing-commercial-menu",
        message="Peluquería",
    )

    assert response.text == (
        "Demostración de peluquería activada correctamente.\n\n"
        "Puedo ayudarte con:\n"
        "• Reservar una cita\n"
        "• Consultar servicios y precios\n"
        "• Ver horarios y ubicación\n"
        "• Hablar con una persona\n\n"
        "Escríbeme directamente qué necesitas."
    )

def test_hairdressing_demo_allows_human_transfer_during_booking():
    app = build_hairdressing_demo_application()
    session_id = "hairdressing-transfer-during-booking"

    app.chat(
        session_id=session_id,
        message="Peluquería",
    )

    booking_response = app.chat(
        session_id=session_id,
        message="Quiero reservar",
    )

    assert "¿Cómo te llamas?" in booking_response.text

    transfer_response = app.chat(
        session_id=session_id,
        message="Quiero hablar con una persona",
    )

    assert transfer_response.text == (
        "De acuerdo. Voy a solicitar que una persona "
        "continúe la conversación contigo."
    )
    assert transfer_response.metadata["capability"] == (
        "human_transfer"
    )
    assert (
        transfer_response.metadata["human_transfer_requested"]
        is True
    )
    assert (
        transfer_response.metadata["transfer_registered"]
        is True
    )

def test_hairdressing_demo_preserves_booking_after_help():
    app = build_hairdressing_demo_application()
    session_id = "hairdressing-help-during-booking"

    app.chat(
        session_id=session_id,
        message="Peluquería",
    )

    app.chat(
        session_id=session_id,
        message="Quiero reservar",
    )

    help_response = app.chat(
        session_id=session_id,
        message="Ayuda",
    )

    assert "Estás realizando una reserva" in help_response.text
    assert help_response.metadata["capability"] == "help"

    continued_response = app.chat(
        session_id=session_id,
        message="Yanko",
    )

    assert "¿Cuál es tu número de teléfono?" in continued_response.text
    assert continued_response.metadata["capability"] == "booking"