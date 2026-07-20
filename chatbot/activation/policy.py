from abc import ABC, abstractmethod

from chatbot.activation.result import ActivationResult
from chatbot.activation.state import ActivationState


class ActivationPolicy(ABC):
    """
    Contrato base para las políticas de activación del asistente.
    """

    @abstractmethod
    def evaluate(
        self,
        message: str,
        state: ActivationState,
    ) -> ActivationResult:
        """
        Evalúa un mensaje entrante y decide qué debe hacer el sistema.
        """
        raise NotImplementedError