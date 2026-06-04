# chatbot/storage/session_store.py

import json
from pathlib import Path
from typing import Dict

from chatbot.core.session import Session


class SessionStore:
    def __init__(self, file_path: str = "data/sessions.json"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load_all(self) -> Dict[str, Session]:
        if not self.file_path.exists():
            return {}

        with self.file_path.open("r", encoding="utf-8") as file:
            raw_sessions = json.load(file)

        sessions = {}

        for user_id, data in raw_sessions.items():
            session = Session(user_id=user_id)
            session.history = data.get("history", [])
            session.language = data.get("language", "es")
            session.current_state = data.get("current_state", "MAIN_MENU")
            session.selected_session = data.get("selected_session")
            session.selected_date = data.get("selected_date")
            session.booking_confirmed = data.get("booking_confirmed", False)

            sessions[user_id] = session

        return sessions

    def save_all(self, sessions: Dict[str, Session]) -> None:
        raw_sessions = {}

        for user_id, session in sessions.items():
            raw_sessions[user_id] = {
                "history": session.history,
                "language": session.language,
                "current_state": session.current_state,
                "selected_session": session.selected_session,
                "selected_date": session.selected_date,
                "booking_confirmed": session.booking_confirmed,
            }

        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(raw_sessions, file, ensure_ascii=False, indent=2)