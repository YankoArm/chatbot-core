import pytest

from chatbot.api.admin_preview import (
    _is_booking_preview_request,
)


@pytest.mark.parametrize("message", [
    "Tengo un problema con una reserva",
    "Quiero consultar un problema con una reserva",
    "Necesito ayuda con mi cita",
    "Cuanto cuesta una reserva?",
    "Tengo que reservar para llamar?",
])
def test_preview_does_not_block_booking_related_questions(message):
    assert not _is_booking_preview_request(message)


@pytest.mark.parametrize("message", [
    "Quiero reservar una cita",
    "Me gustaria reservar",
    "Quiero pedir una cita",
    "I want to book",
    "Book an appointment",
])
def test_preview_blocks_explicit_booking_requests(message):
    assert _is_booking_preview_request(message)
