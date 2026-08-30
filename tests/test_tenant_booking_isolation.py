from chatbot.booking import (
    Booking,
    SQLiteBookingRepository,
)


def test_booking_repository_isolates_same_phone_between_clients(
) -> None:
    repository = SQLiteBookingRepository(
        database_path=":memory:",
    )

    repository.save(
        Booking(
            client_id="salon_norte",
            name="Yanko",
            phone="+34600123123",
            date="10/09/2026",
            time="10:00",
        )
    )
    repository.save(
        Booking(
            client_id="salon_sur",
            name="Yanko",
            phone="+34600123123",
            date="10/09/2026",
            time="11:00",
        )
    )

    norte_bookings = (
        repository.find_by_client_and_phone(
            client_id="salon_norte",
            phone="+34600123123",
        )
    )
    sur_bookings = (
        repository.find_by_client_and_phone(
            client_id="salon_sur",
            phone="+34600123123",
        )
    )

    assert len(norte_bookings) == 1
    assert norte_bookings[0].time == "10:00"

    assert len(sur_bookings) == 1
    assert sur_bookings[0].time == "11:00"

    repository.close()