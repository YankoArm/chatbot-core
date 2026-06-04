# chatbot/bots/rule_bot.py

from chatbot.bots.base_bot import BaseBot
from chatbot.core.session import Session
from chatbot.core import states
from chatbot.services.language_detector import LanguageDetector
from chatbot.config.messages import MESSAGES
from chatbot.config.knowledge import BUSINESS_INFO


class RuleBot(BaseBot):

    def handle_message(self, message: str, session: Session) -> str:
        language = LanguageDetector.detect(message)
        text = message.strip().lower()

        if text in {"menu", "menú", "start", "inicio"}:
            session.current_state = states.MAIN_MENU
            return self._main_menu(language)

        if session.current_state is None:
            session.current_state = states.MAIN_MENU
            return self._welcome(language)

        if session.current_state == states.MAIN_MENU:
            return self._handle_main_menu(text, language, session)

        if session.current_state == states.BOOKING_SESSION_SELECTION:
            return self._handle_booking_session_selection(text, language, session)

        if session.current_state == states.BOOKING_DATE_SELECTION:
            return self._handle_booking_date_selection(text, language, session)

        if session.current_state == states.BOOKING_CONFIRMATION:
            return self._handle_booking_confirmation(text, language, session)

        session.current_state = states.MAIN_MENU
        return self._main_menu(language)

    def _welcome(self, language: str) -> str:
        return (
            MESSAGES["welcome"][language]
            + "\n\n"
            + MESSAGES["main_menu"][language]
        )

    def _main_menu(self, language: str) -> str:
        return MESSAGES["main_menu"][language]

    def _handle_main_menu(self, text: str, language: str, session: Session) -> str:
        if text == "1":
            return self._sessions_info(language)

        if text == "2":
            return BUSINESS_INFO["prices"][language]

        if text == "3":
            return self._available_dates(language)

        if text == "4":
            session.current_state = states.BOOKING_SESSION_SELECTION
            return self._booking_session_menu(language)

        if text == "5":
            session.current_state = states.HUMAN_SUPPORT
            return self._human_support(language)

        return MESSAGES["invalid_option"][language] + "\n\n" + self._main_menu(language)

    def _sessions_info(self, language: str) -> str:
        sessions = BUSINESS_INFO["sessions"][language]
        sessions_text = "\n".join(f"{index + 1}. {item}" for index, item in enumerate(sessions))

        return (
            MESSAGES["choose_session_type"][language]
            + "\n\n"
            + sessions_text
            + "\n\n"
            + MESSAGES["back_to_menu"][language]
        )

    def _available_dates(self, language: str) -> str:
        dates = BUSINESS_INFO["available_dates"][language]
        dates_text = "\n".join(f"{index + 1}. {item}" for index, item in enumerate(dates))

        return (
            MESSAGES["choose_date"][language]
            + "\n\n"
            + dates_text
            + "\n\n"
            + MESSAGES["back_to_menu"][language]
        )

    def _booking_session_menu(self, language: str) -> str:
        sessions = BUSINESS_INFO["sessions"][language]
        sessions_text = "\n".join(f"{index + 1}. {item}" for index, item in enumerate(sessions))

        return (
            MESSAGES["choose_session_type"][language]
            + "\n\n"
            + sessions_text
        )

    def _handle_booking_session_selection(self, text: str, language: str, session: Session) -> str:
        sessions = BUSINESS_INFO["sessions"][language]

        if not text.isdigit():
            return MESSAGES["invalid_option"][language]

        selected_index = int(text) - 1

        if selected_index < 0 or selected_index >= len(sessions):
            return MESSAGES["invalid_option"][language]

        session.selected_session = sessions[selected_index]
        session.current_state = states.BOOKING_DATE_SELECTION

        return self._available_dates_for_booking(language)

    def _available_dates_for_booking(self, language: str) -> str:
        dates = BUSINESS_INFO["available_dates"][language]
        dates_text = "\n".join(f"{index + 1}. {item}" for index, item in enumerate(dates))

        return (
            MESSAGES["choose_date"][language]
            + "\n\n"
            + dates_text
        )

    def _handle_booking_date_selection(self, text: str, language: str, session: Session) -> str:
        dates = BUSINESS_INFO["available_dates"][language]

        if not text.isdigit():
            return MESSAGES["invalid_option"][language]

        selected_index = int(text) - 1

        if selected_index < 0 or selected_index >= len(dates):
            return MESSAGES["invalid_option"][language]

        session.selected_date = dates[selected_index]
        session.current_state = states.BOOKING_CONFIRMATION

        selected_session = session.selected_session
        selected_date = session.selected_date

        if language == "en":
            return (
                "Please confirm your booking:\n\n"
                f"Session: {selected_session}\n"
                f"Date: {selected_date}\n\n"
                "Reply OK to confirm or MENU to cancel."
            )

        return (
            "Por favor, confirma tu reserva:\n\n"
            f"Sesión: {selected_session}\n"
            f"Fecha: {selected_date}\n\n"
            "Responde OK para confirmar o MENÚ para cancelar."
        )

    def _handle_booking_confirmation(self, text: str, language: str, session: Session) -> str:
        if text == "ok":
            session.current_state = states.MAIN_MENU
            return MESSAGES["booking_confirmed"][language]

        return MESSAGES["booking_cancelled"][language] + "\n\n" + self._main_menu(language)

    def _human_support(self, language: str) -> str:
        if language == "en":
            return "A person from the team will contact you as soon as possible."

        return "Una persona del equipo contactará contigo lo antes posible."