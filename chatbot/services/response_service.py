# chatbot/services/response_service.py

from chatbot.services.content_service import ContentService
from chatbot.services.menu_service import MenuService
from chatbot.config.messages import MESSAGES


class ResponseService:

    @staticmethod
    def show_sessions(session, config) -> str:
        sessions = ContentService.get_sessions(session.language)
        sessions_text = "\n".join(
            f"{index + 1}. {session_name}"
            for index, session_name in enumerate(sessions)
        )

        header = (
            "Available session types:"
            if session.language == "en"
            else "Tipos de sesión disponibles:"
        )

        text = f"{header}\n{sessions_text}"
        return f"{text}\n\n{MenuService.get_main_menu(session.language, config)}"

    @staticmethod
    def show_prices(session, config) -> str:
        prices = ContentService.get_prices(session.language)
        return f"{prices}\n\n{MenuService.get_main_menu(session.language, config)}"

    @staticmethod
    def show_dates(session, config, include_menu: bool = False) -> str:
        dates = ContentService.get_dates(session.language)
        dates_text = "\n".join(
            f"{index + 1}. {date}"
            for index, date in enumerate(dates)
        )

        header = (
            "Available dates:"
            if session.language == "en"
            else "Fechas disponibles:"
        )

        response = f"{header}\n{dates_text}"

        if include_menu:
            response += f"\n\n{MenuService.get_main_menu(session.language, config)}"

        return response

    @staticmethod
    def show_faq(session, config) -> str:
        faq_items = ContentService.get_faq(session.language)

        lines = []
        for index, item in enumerate(faq_items):
            lines.append(
                f"{index + 1}. {item['question']}\n"
                f"   {item['answer']}"
            )

        header = (
            "Frequently asked questions:"
            if session.language == "en"
            else "Preguntas frecuentes:"
        )

        text = f"{header}\n" + "\n\n".join(lines)
        return f"{text}\n\n{MenuService.get_main_menu(session.language, config)}"

    @staticmethod
    def human_support(session, config) -> str:
        if session.language == "en":
            text = "A person from the team will contact you as soon as possible."
        else:
            text = "Una persona del equipo contactará contigo lo antes posible."

        return f"{text}\n\n{MenuService.get_main_menu(session.language, config)}"

    @staticmethod
    def ask_session_type(session) -> str:
        sessions = ContentService.get_sessions(session.language)
        sessions_text = "\n".join(
            f"{index + 1}. {session_name}"
            for index, session_name in enumerate(sessions)
        )

        prompt = MESSAGES["choose_session_type"][session.language]
        back = MESSAGES["back_to_menu"][session.language]

        return f"{prompt}\n{sessions_text}\n\n{back}"

    @staticmethod
    def show_dates_for_booking(session) -> str:
        dates = ContentService.get_dates(session.language)
        dates_text = "\n".join(
            f"{index + 1}. {date}"
            for index, date in enumerate(dates)
        )

        header = (
            "Available dates:"
            if session.language == "en"
            else "Fechas disponibles:"
        )

        prompt = MESSAGES["choose_date"][session.language]
        back = MESSAGES["back_to_menu"][session.language]

        return f"{prompt}\n{header}\n{dates_text}\n\n{back}"
    
    @staticmethod
    def main_menu(session, config) -> str:
        return MenuService.get_main_menu(session.language, config)
    
    @staticmethod
    def show_products(session, config) -> str:
        products = ContentService.get_products(session.language)

        products_text = "\n".join(
            f"{index + 1}. {product}"
            for index, product in enumerate(products)
        )

        header = (
            "Available products:"
            if session.language == "en"
            else "Productos disponibles:"
        )

        text = f"{header}\n{products_text}"
        menu = MenuService.get_main_menu(session.language, config)

        return f"{text}\n\n{menu}"

    @staticmethod
    def show_promotions(session, config) -> str:
        promotions = ContentService.get_promotions(session.language)

        promotions_text = "\n".join(
            f"{index + 1}. {promotion}"
            for index, promotion in enumerate(promotions)
        )

        header = (
            "Current promotions:"
            if session.language == "en"
            else "Promociones actuales:"
        )

        text = f"{header}\n{promotions_text}"
        menu = MenuService.get_main_menu(session.language, config)

        return f"{text}\n\n{menu}"