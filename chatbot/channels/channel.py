from __future__ import annotations

from abc import ABC, abstractmethod

from chatbot.channels.message import IncomingMessage
from chatbot.channels.result import OutgoingMessage


class Channel(ABC):
    """
    Base contract implemented by every FlowForge communication channel.
    """

    @abstractmethod
    def receive(
        self,
        message: IncomingMessage,
    ) -> OutgoingMessage:
        """
        Process an incoming channel message and return the outgoing result.
        """
        raise NotImplementedError