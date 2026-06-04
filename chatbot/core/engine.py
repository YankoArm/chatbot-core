# chatbot/core/engine.py

from chatbot.core.session import Session
from chatbot.bots.base_bot import BaseBot
from chatbot.storage.session_store import SessionStore


class ChatEngine:

    def __init__(self, bot: BaseBot, session_store: SessionStore | None = None):
        self.bot = bot
        self.session_store = session_store or SessionStore()
        self.sessions = self.session_store.load_all()

    def get_session(self, user_id: str) -> Session:
        if user_id not in self.sessions:
            self.sessions[user_id] = Session(user_id=user_id)

        return self.sessions[user_id]

    def process_message(self, user_id: str, message: str) -> str:
        session = self.get_session(user_id)

        session.add_message("user", message)

        response = self.bot.handle_message(message, session)

        session.add_message("assistant", response)

        self.session_store.save_all(self.sessions)

        return response