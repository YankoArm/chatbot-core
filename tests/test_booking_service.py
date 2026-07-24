from chatbot.booking.models import Booking
from chatbot.booking.repository import BookingRepository
from chatbot.booking.service import BookingService


class FakeBookingRepository(BookingRepository):

    def __init__(self):
        self.saved_booking = None

    def save(self, booking: Booking) -> None:
        self.saved_booking = booking


def test_booking_service_saves_booking():
    repository = FakeBookingRepository()

    service = BookingService(repository)

    booking = Booking(
        name="Yanko",
        phone="600123123",
        date="25/07/2026",
        time="16:30",
    )

    service.create_booking(booking)

    assert repository.saved_booking == booking