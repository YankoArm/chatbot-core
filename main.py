from chatbot.core.engine import ChatEngine
from chatbot.interfaces.cli import CLIInterface
from chatbot.bots.flow_bot import FlowBot
from chatbot.core.bot_config import BotConfig
from chatbot.templates.registry import TEMPLATE_REGISTRY
from chatbot.config.settings import (
    ACTIVE_TEMPLATE,
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
)


def main():
    template = TEMPLATE_REGISTRY[ACTIVE_TEMPLATE]

    config = BotConfig.from_template(
        template,
        default_language=DEFAULT_LANGUAGE,
        supported_languages=SUPPORTED_LANGUAGES,
    )

    bot = FlowBot(config)
    engine = ChatEngine(bot)
    interface = CLIInterface(engine)
    interface.run()


if __name__ == "__main__":
    main()