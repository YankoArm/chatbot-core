from __future__ import annotations

from abc import ABC, abstractmethod

from chatbot.leads.models import Lead


class LeadRepository(ABC):
    """
    Persistence contract for captured commercial leads.
    """

    @abstractmethod
    def save(
        self,
        lead: Lead,
    ) -> bool:
        """
        Store a lead.

        Return True when it is newly stored and False when its
        action identifier was already processed.
        """

        raise NotImplementedError

    @abstractmethod
    def list_by_client(
        self,
        *,
        client_id: str,
    ) -> tuple[Lead, ...]:
        raise NotImplementedError
