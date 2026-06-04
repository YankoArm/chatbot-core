# chatbot/core/session.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from chatbot.core.states import MAIN_MENU


@dataclass
class Session:
    user_id: str
    history: List[Dict[str, str]] = field(default_factory=list)

    language: str = "es"
    current_state: str = MAIN_MENU

    selected_session: Optional[str] = None
    selected_date: Optional[str] = None
    booking_confirmed: bool = False

    def add_message(self, role: str, content: str):
        self.history.append({
            "role": role,
            "content": content
        })