from __future__ import annotations

from abc import ABC, abstractmethod

from chatbot.language.models import Language


class BaseLanguageDetector(ABC):
    """
    Contract for FlowForge language detectors.
    """

    @abstractmethod
    def detect(
        self,
        text: str,
        default_language: Language = Language.ES,
    ) -> Language:
        """
        Detect the language of a text.

        Return the default language when detection is inconclusive.
        """
        raise NotImplementedError