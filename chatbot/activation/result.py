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
        Indicate whether the original message should continue
        to the conversation orchestrator.

        Activation commands are consumed by the activation layer.
        Only messages received while the session is already active
        continue to normal conversational processing.
        """

        return self.action == ActivationAction.CONTINUE

    @property
    def should_respond(self) -> bool:
        """
        Indica si debe enviarse una respuesta inmediata al usuario.
        """

        return self.action == ActivationAction.PROMPT and self.message is not None