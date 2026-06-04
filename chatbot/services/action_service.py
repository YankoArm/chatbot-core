# chatbot/services/action_service.py

class ActionService:

    def __init__(self):
        self.actions = {}

    def register(self, action_id, handler):
        self.actions[action_id] = handler

    def execute(self, action_id, session):
        if action_id not in self.actions:
            return None

        return self.actions[action_id](session)