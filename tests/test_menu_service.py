from chatbot.core.bot_config import BotConfig
from chatbot.templates.sales_template import SALES_TEMPLATE
from chatbot.services.menu_service import MenuService


def test_menu_service_generates_spanish_menu():
    config = BotConfig.from_template(SALES_TEMPLATE)

    menu = MenuService.get_main_menu("es", config)

    assert "Ver productos" in menu
    assert "Ver promociones" in menu
    assert "Hablar con ventas" in menu


def test_menu_service_generates_english_menu():
    config = BotConfig.from_template(SALES_TEMPLATE)

    menu = MenuService.get_main_menu("en", config)

    assert "View products" in menu
    assert "View promotions" in menu
    assert "Talk to sales" in menu