# chatbot/services/booking_flow_service.py

from chatbot.services.content_service import ContentService
from chatbot.services.response_service import ResponseService
from chatbot.config.messages import MESSAGES
from chatbot.core import states


class BookingFlowService:

    @staticmethod
    def handle_session_selection(option: str, session):
        sessions = ContentService.get_sessions(session.language)

        if not option.isdigit():
            return (
                MESSAGES["invalid_option"][session.language]
                + "\n\n"
                + ResponseService.ask_session_type(session)
            )

        index = int(option) - 1

        if index < 0 or index >= len(sessions):
            return (
                MESSAGES["invalid_option"][session.language]
                + "\n\n"
                + ResponseService.ask_session_type(session)
            )

        session.selected_session = sessions[index]
        session.current_state = states.BOOKING_DATE_SELECTION

        return ResponseService.show_dates_for_booking(session)
    
    @staticmethod
    def handle_date_selection(option: str, session):
        dates = ContentService.get_dates(session.language)

        if not option.isdigit():
            return (
                MESSAGES["invalid_option"][session.language]
                + "\n\n"
                + ResponseService.show_dates_for_booking(session)
            )

        index = int(option) - 1

        if index < 0 or index >= len(dates):
            return (
                MESSAGES["invalid_option"][session.language]
                + "\n\n"
                + ResponseService.show_dates_for_booking(session)
            )

        session.selected_date = dates[index]
        session.current_state = states.BOOKING_CONFIRMATION

        return BookingFlowService.ask_confirmation(session)
    
    @staticmethod
    def ask_confirmation(session):
        if session.language == "en":
            return (
                "Please review your booking details:\n"
                f"Session: {session.selected_session}\n"
                f"Date: {session.selected_date}\n\n"
                "Type 'yes' to confirm.\n"
                "Type 'menu' to go back to the main menu."
            )

        return (
            "Por favor, revisa los datos de tu reserva:\n"
            f"Sesión: {session.selected_session}\n"
            f"Fecha: {session.selected_date}\n\n"
            "Escribe 'si' para confirmar.\n"
            "Escribe 'menu' para volver al menú principal."
        )

    @staticmethod
    def handle_confirmation(message: str, session, config):
        text = message.lower().strip()

        if text in ["si", "sí", "yes"]:
            session.booking_confirmed = True
            session.current_state = states.MAIN_MENU

            confirmation_text = MESSAGES["booking_confirmed"][session.language]
            menu = ResponseService.main_menu(session, config)

            return f"{confirmation_text}\n\n{menu}"

        cancellation_text = MESSAGES["booking_cancelled"][session.language]
        return f"{cancellation_text}\n\n{BookingFlowService.ask_confirmation(session)}"