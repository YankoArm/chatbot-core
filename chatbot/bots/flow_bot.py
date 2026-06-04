# chatbot/bots/flow_bot.py

from chatbot.bots.base_bot import BaseBot
from chatbot.core.session import Session
from chatbot.services.language_detector import LanguageDetector
from chatbot.services.menu_service import MenuService
from chatbot.services.action_service import ActionService
from chatbot.services.response_service import ResponseService
from chatbot.config.messages import MESSAGES
from chatbot.core import states
from chatbot.services.booking_flow_service import BookingFlowService


class FlowBot(BaseBot):

    def __init__(self, config):
        self.config = config
        self.action_service = ActionService()

        self.action_service.register(
            "sessions",
            lambda session: ResponseService.show_sessions(session, self.config)
        )

        self.action_service.register(
            "prices",
            lambda session: ResponseService.show_prices(session, self.config)
        )

        self.action_service.register(
            "dates",
            lambda session: ResponseService.show_dates(
                session,
                self.config,
                include_menu=True
            )
        )

        self.action_service.register(
            "human_support",
            lambda session: ResponseService.human_support(session, self.config)
        )

        self.action_service.register(
            "faq",
            lambda session: ResponseService.show_faq(session, self.config)
        )

        self.action_service.register(
            "products",
            lambda session: ResponseService.show_products(session, self.config)
        )

        self.action_service.register(
            "promotions",
            lambda session: ResponseService.show_promotions(session, self.config)
        )

    def handle_message(self, message: str, session: Session) -> str:
        clean_message = message.strip()
        normalized = clean_message.lower()

        if len(session.history) == 1:
            session.language = LanguageDetector.detect(clean_message)
            return self._welcome(session)

        if normalized in ["menu", "menú"]:
            session.current_state = states.MAIN_MENU
            return MenuService.get_main_menu(session.language, self.config)

        return self._handle_state(clean_message, session)

    def _welcome(self, session: Session) -> str:
        welcome_text = MESSAGES["welcome"][session.language]
        menu = MenuService.get_main_menu(session.language, self.config)
        return f"{welcome_text}\n\n{menu}"

    def _handle_state(self, message: str, session: Session) -> str:
        if session.current_state == states.MAIN_MENU:
            return self._handle_main_menu(message, session)

        if session.current_state == states.BOOKING_SESSION_SELECTION:
            return BookingFlowService.handle_session_selection(
                message,
                session
            )
        if session.current_state == states.BOOKING_DATE_SELECTION:
            return BookingFlowService.handle_date_selection(
                message,
                session
            )

        if session.current_state == states.BOOKING_CONFIRMATION:
            return BookingFlowService.handle_confirmation(
                message,
                session,
                self.config
            )

        session.current_state = states.MAIN_MENU
        return MenuService.get_main_menu(session.language, self.config)

    def _handle_main_menu(self, option: str, session: Session) -> str:
        action = self.config.get_menu_action_by_number(option)

        if action == "booking":
            session.current_state = states.BOOKING_SESSION_SELECTION
            return ResponseService.ask_session_type(session)

        response = self.action_service.execute(action, session)

        if response is not None:
            return response

        return (
            MESSAGES["invalid_option"][session.language]
            + "\n\n"
            + MenuService.get_main_menu(session.language, self.config)
        )

