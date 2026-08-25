import pytest

from chatbot.booking import BookingSlotUnavailableError, BookingState, BookingStep
from chatbot.capabilities.booking import BookingCapability
from chatbot.conversation.context import ConversationContext

from datetime import date, time, timedelta
from unittest.mock import Mock
from chatbot.availability import (
    BookingRules,
    BusinessHours,
)

class FakeBookingService:
    def __init__(self) -> None:
        self.received_state: BookingState | None = None
        self.received_creation_rules: BookingRules | None = None
        self.received_date_rules: BookingRules | None = None
        self.received_slot_rules: BookingRules | None = None
        self.raise_slot_unavailable = False
        self.available_slots = ()
        self.available_dates: tuple[date, ...] = ()

    def create_booking_from_state(
        self,
        state: BookingState,
        *,
        business_hours=None,
        rules=None,
        now=None,
    ) -> None:
        self.received_state = state
        self.received_creation_rules = rules

        if self.raise_slot_unavailable:
            raise BookingSlotUnavailableError()

        state.confirm(
            booking_id="booking-123",
        )

    def get_available_dates(
        self,
        *,
        start_date,
        days,
        business_hours=None,
        rules=None,
        now=None,
    ) -> tuple[date, ...]:
        self.received_date_rules = rules

        return self.available_dates

    def get_available_slots_for_date(
        self,
        target_date,
        *,
        business_hours=None,
        rules=None,
        now=None,
    ):
        self.received_slot_rules = rules

        return self.available_slots

def build_booking_capability(
    *,
    available_dates: tuple[date, ...] | None = None,
) -> BookingCapability:
    booking_service = FakeBookingService()

    booking_service.available_dates = (
        available_dates
        if available_dates is not None
        else (
            date.today() + timedelta(days=10),
            date.today() + timedelta(days=11),
            date.today() + timedelta(days=12),
        )
    )

    business_hours = BusinessHours.standard_week(
        start=time(9, 0),
        end=time(18, 0),
        timezone_name="Europe/Madrid",
    )

    booking_rules = BookingRules.hourly()

    return BookingCapability(
        booking_service=booking_service,
        business_hours=business_hours,
        booking_rules=booking_rules,
    ) 

def test_booking_capability_confirms_booking_through_service() -> None:
    booking_service = FakeBookingService()

    capability = BookingCapability(
        booking_service=booking_service,
    )

    context = ConversationContext(
        session_id="user_1",
    )

    booking_state = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
        time="16:30",
    )

    context.booking = booking_state

    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="sí",
    )

    assert booking_service.received_state is booking_state
    assert booking_state.confirmed is True
    assert booking_state.is_complete is True
    assert booking_state.booking_id == "booking-123"
    assert booking_state.next_step is BookingStep.COMPLETE

    assert context.booking is None
    assert context.active_capability is None

    assert response.metadata["handled"] is True
    assert response.metadata["booking_step"] == "complete"

    assert (
        "Tu reserva se ha realizado correctamente"
        in response.text
    )

    assert (
        "Si necesitas algo más, escríbeme directamente"
        in response.text
    )

def test_booking_capability_stores_name_and_requests_phone() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState()
    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="Yanko",
    )

    assert context.booking.name == "Yanko"
    assert context.booking.next_step is BookingStep.PHONE

    assert response.text == (
        "Encantado, Yanko. "
        "¿Cuál es tu número de teléfono? "
        "Puedes incluir el prefijo internacional, "
        "por ejemplo +34."
    )

def test_booking_capability_stores_phone_and_requests_date() -> None:
    available_dates = (
        date.today() + timedelta(days=10),
        date.today() + timedelta(days=11),
        date.today() + timedelta(days=12),
    )

    capability = build_booking_capability(
        available_dates=available_dates,
    )

    context = ConversationContext(
        session_id="user_1",
    )

    context.booking = BookingState(
        name="Yanko",
    )

    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="600123123",
    )

    assert context.booking.phone == "+34600123123"
    assert context.booking.next_step is BookingStep.DATE

    formatted_dates = ", ".join(
        available_date.strftime("%d/%m/%Y")
        for available_date in available_dates
    )

    assert response.text == (
        "Tengo disponibilidad para las próximas fechas: "
        f"{formatted_dates}. "
        "¿Qué día prefieres? "
        "Si necesitas una fecha posterior, dímelo."
    )

def test_booking_capability_stores_date_and_requests_time() -> None:
    capability = BookingCapability()
    context = ConversationContext(
        session_id="user_1"
    )

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
    )

    context.set_active_capability(
        "booking"
    )

    response = capability.handle(
        context=context,
        message="25/07/2099",
    )

    assert context.booking.date == "25/07/2099"
    assert context.booking.next_step is BookingStep.TIME
    assert response.text == "¿A qué hora quieres la cita?"

def test_booking_capability_moves_to_confirmation_after_time() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="17:00",
    )

    assert context.booking.time == "17:00"
    assert context.booking.has_required_data is True
    assert context.booking.is_complete is False
    assert context.booking.next_step is BookingStep.CONFIRMATION

    assert "Estos son los datos de tu reserva" in response.text
    assert "Yanko" in response.text
    assert "600123123" in response.text
    assert "28/07/2026" in response.text
    assert "17:00" in response.text


def test_booking_capability_does_not_advance_with_invalid_phone() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="abc",
    )

    assert context.booking.phone is None
    assert context.booking.next_step is BookingStep.PHONE

    assert response.text == (
        "El teléfono no parece válido. "
        "Comprueba el número y su prefijo internacional."
    )

def test_booking_capability_does_not_advance_with_invalid_name() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState()

    response = capability.handle(
        context=context,
        message="1",
    )

    assert context.booking.name is None
    assert context.booking.next_step is BookingStep.NAME

    assert response.text == (
        "Ese nombre no parece válido. "
        "¿Puedes escribirlo de nuevo?"
    )


def test_booking_capability_does_not_advance_with_invalid_date() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
    )

    response = capability.handle(
        context=context,
        message="ahora",
    )

    assert context.booking.date is None
    assert context.booking.next_step is BookingStep.DATE

    assert response.text == (
        "La fecha no parece válida. "
        "Escríbela con el formato DD/MM/YYYY "
        "o pregúntame qué días hay disponibles."
    )


def test_booking_capability_does_not_advance_with_invalid_time() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
        date="25/07/2026",
    )

    response = capability.handle(
        context=context,
        message="ahora",
    )

    assert context.booking.time is None
    assert context.booking.next_step is BookingStep.TIME

    assert response.text == (
        "La hora no parece válida. "
        "Escríbela con el formato HH:MM."
    )


def test_booking_capability_returns_available_dates_without_advancing() -> None:
    capability = build_booking_capability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="¿Qué días hay disponibles?",
    )

    assert context.booking.date is None
    assert context.booking.next_step is BookingStep.DATE

    assert "Tengo disponibilidad" in response.text
    assert "¿Qué día prefieres?" in response.text


@pytest.mark.parametrize(
    "message",
    [
        "que dias hay",
        "¿Qué días hay?",
        "QUE DIAS HAY DISPONIBLES?",
        "que dias tienes?",
        "¿qué fechas tienes?",
        "hay huecos?",
    ],
)
def test_booking_capability_recognizes_availability_questions(
    message: str,
) -> None:
    capability = build_booking_capability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message=message,
    )

    assert context.booking.date is None
    assert context.booking.next_step is BookingStep.DATE
    assert "Tengo disponibilidad" in response.text


def test_booking_capability_confirms_booking() -> None:
    capability = BookingCapability()

    context = ConversationContext(
        session_id="user_1",
    )

    booking_state = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
        time="17:00",
    )

    context.booking = booking_state

    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="sí",
    )

    assert booking_state.confirmed is True
    assert booking_state.is_complete is True
    assert booking_state.next_step is BookingStep.COMPLETE

    assert context.booking is None
    assert context.active_capability is None

    assert (
        "Tu reserva se ha realizado correctamente"
        in response.text
    )

    assert (
        "Si necesitas algo más, escríbeme directamente"
        in response.text
    )

def test_booking_capability_cancels_booking() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
        time="17:00",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="no",
    )

    assert context.booking is None
    assert "cancelada" in response.text.lower()
    assert response.metadata["booking_step"] == "cancelled"


def test_booking_capability_keeps_confirmation_step_for_unknown_answer() -> None:
    capability = BookingCapability()
    context = ConversationContext(session_id="user_1")

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
        time="17:00",
    )

    context.set_active_capability("booking")

    response = capability.handle(
        context=context,
        message="quizás",
    )

    assert context.booking.confirmed is False
    assert context.booking.next_step is BookingStep.CONFIRMATION
    assert "sí" in response.text.lower()
    assert "no" in response.text.lower()

def test_booking_capability_requests_new_time_when_slot_becomes_unavailable() -> None:
    booking_service = FakeBookingService()
    booking_service.raise_slot_unavailable = True

    booking_service.available_slots = (
        type(
            "Slot",
            (),
            {
                "start": type(
                    "Start",
                    (),
                    {
                        "strftime": lambda self, fmt: "15:30",
                    },
                )(),
            },
        )(),
        type(
            "Slot",
            (),
            {
                "start": type(
                    "Start",
                    (),
                    {
                        "strftime": lambda self, fmt: "17:00",
                    },
                )(),
            },
        )(),
    )

    business_hours = BusinessHours.standard_week(
        start=time(9, 0),
        end=time(18, 0),
        timezone_name="Europe/Madrid",
    )

    booking_rules = BookingRules.hourly(
        slot_interval_minutes=30,
    )

    capability = BookingCapability(
        booking_service=booking_service,
        business_hours=business_hours,
        booking_rules=booking_rules,
    )

    context = ConversationContext(
        session_id="user_1",
    )

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
        time="16:30",
    )

    context.booking.available_times = (
        "15:30",
        "17:00",
    )

    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="sí",
    )

    assert booking_service.received_state is context.booking

    assert context.booking.confirmed is False
    assert context.booking.booking_id is None

    assert context.booking.time is None
    assert context.booking.date == "28/07/2026"

    assert context.booking.next_step is BookingStep.TIME

    assert "15:30" in response.text
    assert "17:00" in response.text

def test_booking_capability_requests_new_date_when_no_times_remain() -> None:
    booking_service = FakeBookingService()
    booking_service.raise_slot_unavailable = True

    booking_service.available_slots = ()
    business_hours = BusinessHours.standard_week(
        start=time(9, 0),
        end=time(18, 0),
        timezone_name="Europe/Madrid",
    )

    booking_rules = BookingRules.hourly(
        slot_interval_minutes=30,
    )

    capability = BookingCapability(
        booking_service=booking_service,
        business_hours=business_hours,
        booking_rules=booking_rules,
    )

    context = ConversationContext(
        session_id="user_1",
    )

    context.booking = BookingState(
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
        time="16:30",
    )

    context.booking.available_times = (
        "15:30",
        "17:00",
    )

    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="sí",
    )

    assert booking_service.received_state is context.booking

    assert context.booking.confirmed is False
    assert context.booking.booking_id is None

    assert context.booking.time is None
    assert context.booking.date is None

    assert context.booking.available_times == ()

    assert context.booking.next_step is BookingStep.DATE

    assert "No quedan horas disponibles" in response.text

def test_booking_capability_reports_no_available_dates_after_phone() -> None:
    booking_service = Mock()
    booking_service.get_available_dates.return_value = ()

    business_hours = BusinessHours.standard_week(
        start=time(9, 0),
        end=time(18, 0),
        timezone_name="Europe/Madrid",
    )

    booking_rules = BookingRules.hourly()

    capability = BookingCapability(
        booking_service=booking_service,
        business_hours=business_hours,
        booking_rules=booking_rules,
    )

    context = ConversationContext(
        session_id="user_1",
    )
    context.booking = BookingState(
        name="Yanko",
    )
    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="600123123",
    )

    assert context.booking.phone == "+34600123123"
    assert context.booking.next_step is BookingStep.DATE
    assert response.text == (
        "Ahora mismo no tengo fechas disponibles. "
        "Inténtalo de nuevo más adelante."
    )

def test_booking_capability_rejects_unavailable_date() -> None:
    from datetime import datetime, timedelta

    capability = BookingCapability()

    context = ConversationContext(
        session_id="user_1",
    )

    first_available_date = (
        datetime.now().date()
        + timedelta(days=10)
    )

    second_available_date = (
        datetime.now().date()
        + timedelta(days=11)
    )

    unavailable_date = (
        datetime.now().date()
        + timedelta(days=12)
    )

    context.booking = BookingState(
        name="Yanko",
        phone="+34600123123",
        available_dates=(
            first_available_date.strftime(
                "%d/%m/%Y",
            ),
            second_available_date.strftime(
                "%d/%m/%Y",
            ),
        ),
    )

    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message=unavailable_date.strftime(
            "%d/%m/%Y",
        ),
    )

    assert context.booking.date is None

    assert (
        "Lo siento, esa fecha no está disponible"
        in response.text
    )

def test_booking_capability_can_handle_initial_availability_question() -> None:
    capability = build_booking_capability()
    context = ConversationContext(
        session_id="initial-availability-intent",
    )

    assert capability.can_handle(
        context,
        "¿Qué fechas tenéis disponibles?",
    ) is True


def test_booking_capability_answers_initial_availability_question() -> None:
    available_dates = (
        date.today() + timedelta(days=10),
        date.today() + timedelta(days=11),
    )

    capability = build_booking_capability(
        available_dates=available_dates,
    )

    context = ConversationContext(
        session_id="initial-availability-response",
    )

    response = capability.handle(
        context=context,
        message="¿Qué fechas tenéis disponibles?",
    )

    first_date = available_dates[0].strftime(
        "%d/%m/%Y",
    )
    second_date = available_dates[1].strftime(
        "%d/%m/%Y",
    )

    assert context.booking is None
    assert first_date in response.text
    assert second_date in response.text
    assert "¿Qué día prefieres?" in response.text

    assert response.metadata == {
        "capability": "booking",
        "handled": True,
        "booking_step": "inactive",
        "language": "es",
    }

def test_initial_availability_shows_only_next_five_dates() -> None:
    available_dates = tuple(
        date.today() + timedelta(days=day_offset)
        for day_offset in range(10, 17)
    )

    capability = build_booking_capability(
        available_dates=available_dates,
    )

    context = ConversationContext(
        session_id="limited-initial-availability",
    )

    response = capability.handle(
        context=context,
        message="¿Qué fechas tenéis disponibles?",
    )

    for available_date in available_dates[:5]:
        assert (
            available_date.strftime("%d/%m/%Y")
            in response.text
        )

    assert (
        available_dates[5].strftime("%d/%m/%Y")
        not in response.text
    )

    assert "fecha posterior" in response.text

def test_booking_capability_requests_service_when_catalog_exists() -> None:
    from chatbot.booking.services import BookableService

    highlights = BookableService(
        id="highlights",
        name_es="Mechas",
        name_en="Highlights",
        duration_minutes=120,
        price_type="from",
        price_cents=6500,
        currency="EUR",
    )

    capability = BookingCapability(
        services=(
            highlights,
        ),
    )

    context = ConversationContext(
        session_id="service-selection-start",
    )

    response = capability.handle(
        context=context,
        message="Quiero reservar",
    )

    assert context.booking is not None
    assert context.booking.requires_service_selection is True
    assert context.booking.next_step is BookingStep.SERVICE
    assert "¿Qué servicio quieres reservar?" in response.text
    assert "Mechas" in response.text
    assert "desde 65 €" in response.text


def test_booking_capability_selects_service_from_initial_message() -> None:
    from chatbot.booking.services import BookableService

    highlights = BookableService(
        id="highlights",
        name_es="Mechas",
        name_en="Highlights",
        duration_minutes=120,
        price_type="from",
        price_cents=6500,
        currency="EUR",
    )

    capability = BookingCapability(
        services=(
            highlights,
        ),
    )

    context = ConversationContext(
        session_id="service-selection-from-message",
    )

    response = capability.handle(
        context=context,
        message="Quiero reservar unas mechas",
    )

    assert context.booking is not None
    assert context.booking.service_id == "highlights"
    assert context.booking.service_name == "Mechas"
    assert context.booking.service_duration_minutes == 120
    assert context.booking.service_price_cents == 6500
    assert context.booking.service_price_type == "from"
    assert context.booking.service_currency == "EUR"
    assert context.booking.next_step is BookingStep.NAME

    assert response.text == (
        "Perfecto. Has elegido Mechas. "
        "¿Cómo te llamas?"
    )

def test_booking_summary_includes_selected_service() -> None:
    capability = BookingCapability()

    context = ConversationContext(
        session_id="service-summary",
    )

    context.booking = BookingState(
        requires_service_selection=True,
        service_id="highlights",
        service_name="Mechas",
        service_duration_minutes=120,
        service_price_cents=6500,
        service_price_type="from",
        service_currency="EUR",
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
    )

    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="17:00",
    )

    assert context.booking.next_step is BookingStep.CONFIRMATION
    assert "Servicio: Mechas" in response.text
    assert "Nombre: Yanko" in response.text
    assert "Fecha: 28/07/2026" in response.text
    assert "Hora: 17:00" in response.text


def test_confirmed_booking_includes_selected_service() -> None:
    capability = BookingCapability()

    context = ConversationContext(
        session_id="confirmed-service-summary",
    )

    context.booking = BookingState(
        requires_service_selection=True,
        service_id="highlights",
        service_name="Mechas",
        service_duration_minutes=120,
        service_price_cents=6500,
        service_price_type="from",
        service_currency="EUR",
        name="Yanko",
        phone="600123123",
        date="28/07/2026",
        time="17:00",
    )

    context.set_active_capability(
        "booking",
    )

    response = capability.handle(
        context=context,
        message="sí",
    )

    assert context.booking is None
    assert "Tu reserva se ha realizado correctamente" in response.text
    assert "Servicio: Mechas" in response.text
    assert "Nombre: Yanko" in response.text
    assert "Fecha: 28/07/2026" in response.text
    assert "Hora: 17:00" in response.text


def test_service_duration_is_used_when_requesting_available_dates() -> None:
    booking_service = FakeBookingService()
    booking_service.available_dates = (
        date.today() + timedelta(days=10),
    )

    business_hours = BusinessHours.standard_week(
        start=time(9, 0),
        end=time(18, 0),
        timezone_name="Europe/Madrid",
    )
    booking_rules = BookingRules.hourly()

    capability = BookingCapability(
        booking_service=booking_service,
        business_hours=business_hours,
        booking_rules=booking_rules,
    )

    context = ConversationContext(
        session_id="highlights-available-dates",
    )
    context.booking = BookingState(
        requires_service_selection=True,
        service_id="highlights",
        service_name="Mechas",
        service_duration_minutes=120,
        service_price_cents=6500,
        service_price_type="from",
        service_currency="EUR",
        name="Yanko",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="600123123",
    )

    assert booking_service.received_date_rules is not None
    assert (
        booking_service.received_date_rules.appointment_duration
        == timedelta(minutes=120)
    )
    assert (
        booking_rules.appointment_duration
        == timedelta(minutes=60)
    )


def test_service_duration_is_used_when_confirming_booking() -> None:
    booking_service = FakeBookingService()

    business_hours = BusinessHours.standard_week(
        start=time(9, 0),
        end=time(18, 0),
        timezone_name="Europe/Madrid",
    )
    booking_rules = BookingRules.hourly()

    capability = BookingCapability(
        booking_service=booking_service,
        business_hours=business_hours,
        booking_rules=booking_rules,
    )

    context = ConversationContext(
        session_id="highlights-confirmation-duration",
    )
    context.booking = BookingState(
        requires_service_selection=True,
        service_id="highlights",
        service_name="Mechas",
        service_duration_minutes=120,
        service_price_cents=6500,
        service_price_type="from",
        service_currency="EUR",
        name="Yanko",
        phone="+34600123123",
        date="28/07/2026",
        time="17:00",
    )
    context.set_active_capability(
        "booking",
    )

    capability.handle(
        context=context,
        message="sí",
    )

    assert booking_service.received_creation_rules is not None
    assert (
        booking_service.received_creation_rules.appointment_duration
        == timedelta(minutes=120)
    )
    assert (
        booking_rules.appointment_duration
        == timedelta(minutes=60)
    )
