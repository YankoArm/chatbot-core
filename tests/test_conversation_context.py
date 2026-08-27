from chatbot.booking import (
    BookingManagementAction,
    BookingManagementState,
    BookingState,
)
from chatbot.conversation.context import ConversationContext


def test_conversation_context_starts_without_booking_management(
) -> None:
    context = ConversationContext(
        session_id="booking-management-empty",
    )

    assert context.booking_management is None


def test_conversation_context_preserves_booking_management_state(
) -> None:
    management = BookingManagementState(
        action=BookingManagementAction.CANCEL,
    )

    context = ConversationContext(
        session_id="booking-management-active",
        booking_management=management,
    )

    assert context.booking_management is management


def test_reset_booking_management_only_clears_management_state(
) -> None:
    booking = BookingState()
    management = BookingManagementState(
        action=BookingManagementAction.CANCEL,
    )

    context = ConversationContext(
        session_id="reset-booking-management",
        booking=booking,
        booking_management=management,
    )

    context.reset_booking_management()

    assert context.booking_management is None
    assert context.booking is booking


def test_context_reset_clears_booking_and_booking_management(
) -> None:
    context = ConversationContext(
        session_id="reset-complete-context",
        booking=BookingState(),
        booking_management=BookingManagementState(
            action=BookingManagementAction.CANCEL,
        ),
    )

    context.reset()

    assert context.booking is None
    assert context.booking_management is None