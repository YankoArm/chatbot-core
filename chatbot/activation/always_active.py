from chatbot.activation.action import ActivationAction
from chatbot.activation.policy import ActivationPolicy
from chatbot.activation.result import ActivationResult
from chatbot.activation.state import ActivationState


class AlwaysActivePolicy(ActivationPolicy):
    """
    Política para asistentes que no requieren activación previa.
    """

    def evaluate(
        self,
        message: str,
        state: ActivationState,
    ) -> ActivationResult:
        return ActivationResult(
            action=ActivationAction.CONTINUE,
        )