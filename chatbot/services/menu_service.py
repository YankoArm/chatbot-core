# chatbot/services/menu_service.py

from chatbot.core.bot_config import BotConfig


class MenuService:

    @staticmethod
    def get_main_menu(language: str, config: BotConfig) -> str:
        menu_title = config.menu_title.get(
            language,
            config.menu_title[config.default_language],
        )

        menu_footer = config.menu_footer.get(
            language,
            config.menu_footer[config.default_language],
        )

        enabled_items = config.get_enabled_menu_items()

        numbered_items = "\n".join(
            f"{index + 1}. {item['labels'].get(language, item['labels'][config.default_language])}"
            for index, item in enumerate(enabled_items)
        )

        return f"{menu_title}\n{numbered_items}\n\n{menu_footer}"