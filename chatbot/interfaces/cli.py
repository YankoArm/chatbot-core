# chatbot/interfaces/cli.py

from chatbot.core.engine import ChatEngine


class CLIInterface:

    def __init__(self, engine: ChatEngine):
        self.engine = engine
        self.user_id = "local_user"

    def run(self):
        print("Chatbot iniciado. Escribe 'exit' para salir.\n")

        while True:
            user_input = input("Tú: ")

            if user_input.lower() in ["exit", "salir"]:
                print("Saliendo...")
                break

            response = self.engine.process_message(self.user_id, user_input)

            print(f"Bot: {response}")