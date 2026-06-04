# chatbot/bots/base_bot.py

from abc import ABC, abstractmethod
from chatbot.core.session import Session


class BaseBot(ABC):

    @abstractmethod
    def handle_message(self, message: str, session: Session) -> str:
        pass