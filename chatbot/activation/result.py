from dataclasses import dataclass

from chatbot.activation.action import ActivationAction


@dataclass(frozen=True)
class ActivationResult:
    """
    Resultado de evaluar una política de activación.
    """

    action: ActivationAction
    message: str | None = None

    @property
    def should_process_message(self) -> bool:
        """
        Indica si el mensaje debe continuar hacia el orquestador.
        """

        return self.action in {
            ActivationAction.ACTIVATE,
            ActivationAction.CONTINUE,
        }

    @property
    def should_respond(self) -> bool:
        """
        Indica si debe enviarse una respuesta inmediata al usuario.
        """

        return self.action == ActivationAction.PROMPT and self.message is not None