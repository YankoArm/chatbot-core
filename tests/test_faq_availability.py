import pytest

from chatbot.capabilities.faq.availability import build_availability_answer
from chatbot.language import Language


@pytest.mark.parametrize(
    "language,message,expected",
    [
        (Language.ES, "que horarios tienen?", "a consultar"),
        (Language.EN, "opening hours", "on request"),
    ],
)
def test_service_24_7_keeps_human_availability_separate(
    language, message, expected
):
    answer = build_availability_answer(
        availability={
            "service_24_7": True,
            "human_attention": {"mode": "on_request"},
        },
        message=message,
        language=language,
    )
    assert answer is not None
    assert "24" in answer
    assert expected in answer


def test_custom_human_hours_are_shown():
    answer = build_availability_answer(
        availability={
            "service_24_7": True,
            "human_attention": {
                "mode": "custom",
                "hours_text": "L-V 09:00-18:00",
            },
        },
        message="horario",
        language=Language.ES,
    )
    assert "L-V 09:00-18:00" in answer
    assert "reservas" in answer


def test_missing_availability_preserves_existing_faq():
    assert build_availability_answer(
        availability=None,
        message="horario",
        language=Language.ES,
    ) is None


def test_price_question_is_not_replaced_by_hours():
    assert build_availability_answer(
        availability={"service_24_7": True},
        message="Ver servicios y precios",
        language=Language.ES,
    ) is None
