# chatbot/bots/echo_bot.py

from chatbot.bots.base_bot import BaseBot
from chatbot.core.session import Session


class EchoBot(BaseBot):

    def handle_message(self, message: str, session: Session) -> str:
        return f"Echo: {message}"