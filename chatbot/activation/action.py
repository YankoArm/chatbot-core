from enum import Enum


class ActivationAction(str, Enum):
    """
    Resultado operativo de evaluar una política de activación.

    ACTIVATE:
        La sesión estaba inactiva y debe activarse.

    CONTINUE:
        La sesión ya estaba activa y el mensaje debe continuar
        hacia el flujo conversacional normal.

    PROMPT:
        La sesión está inactiva y debe enviarse un mensaje
        indicando cómo activar el asistente.

    SILENT:
        La sesión está inactiva y no debe enviarse ninguna respuesta.
    """

    ACTIVATE = "activate"
    CONTINUE = "continue"
    PROMPT = "prompt"
    SILENT = "silent"