from chatbot.bots.flow_bot import FlowBot
from chatbot.core.bot_config import BotConfig
from chatbot.core.session import Session
from chatbot.templates.sales_template import SALES_TEMPLATE


def create_sales_bot():
    config = BotConfig.from_template(
        SALES_TEMPLATE,
        default_language="es",
        supported_languages=["es", "en"],
    )

    return FlowBot(config)


def test_flow_bot_welcome_message_in_spanish():
    bot = create_sales_bot()
    session = Session(user_id="test-user")

    session.add_message("user", "hola")

    response = bot.handle_message("hola", session)

    assert "Hola" in response
    assert "Menú principal" in response
    assert "Ver productos" in response


def test_flow_bot_shows_products_from_sales_template():
    bot = create_sales_bot()
    session = Session(user_id="test-user")

    session.add_message("user", "hola")
    bot.handle_message("hola", session)

    session.add_message("user", "1")
    response = bot.handle_message("1", session)

    assert "Productos disponibles" in response
    assert "TPV Básico" in response


def test_flow_bot_invalid_menu_option():
    bot = create_sales_bot()
    session = Session(user_id="test-user")

    session.add_message("user", "hola")
    bot.handle_message("hola", session)

    session.add_message("user", "99")
    response = bot.handle_message("99", session)

    assert "Opción no válida" in response
    assert "Menú principal" in response