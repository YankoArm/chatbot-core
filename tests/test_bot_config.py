from chatbot.core.bot_config import BotConfig
from chatbot.templates.sales_template import SALES_TEMPLATE


def test_bot_config_loads_template():
    config = BotConfig.from_template(
        SALES_TEMPLATE,
        default_language="es",
        supported_languages=["es", "en"],
    )

    assert config.name == "Sales Bot"
    assert config.default_language == "es"
    assert config.supported_languages == ["es", "en"]
    assert config.is_feature_enabled("products") is True
    assert config.is_feature_enabled("booking") is False


def test_bot_config_get_enabled_menu_items():
    config = BotConfig.from_template(SALES_TEMPLATE)

    enabled_items = config.get_enabled_menu_items()

    assert len(enabled_items) == 3
    assert enabled_items[0]["id"] == "products"
    assert enabled_items[1]["id"] == "promotions"
    assert enabled_items[2]["id"] == "human_support"


def test_bot_config_get_menu_action_by_number():
    config = BotConfig.from_template(SALES_TEMPLATE)

    assert config.get_menu_action_by_number("1") == "products"
    assert config.get_menu_action_by_number("2") == "promotions"
    assert config.get_menu_action_by_number("3") == "human_support"
    assert config.get_menu_action_by_number("99") is None
    assert config.get_menu_action_by_number("abc") is None