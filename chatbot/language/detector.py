from __future__ import annotations

from abc import ABC, abstractmethod

from chatbot.language.models import Language


class BaseLanguageDetector(ABC):
    """
    Contract for FlowForge language detectors.

    A language detector analyses user-provided text and returns one of the
    languages supported by the application.

    When detection is inconclusive, implementations must return the supplied
    default language.
    """

    @abstractmethod
    def detect(
        self,
        text: str,
        default_language: Language = Language.ES,
    ) -> Language:
        """
        Detect the language used in the supplied text.

        Args:
            text:
                User-provided text to analyse.

            default_language:
                Language returned when the input is empty, too short or
                otherwise inconclusive.

        Returns:
            The detected language or the supplied default language.
        """

        raise NotImplementedError

    @staticmethod
    def is_detectable(text: str) -> bool:
        """
        Return whether the text contains enough alphabetic content to attempt
        language detection.

        Numeric values such as phone numbers, dates and times should not cause
        the conversation language to be selected.
        """

        alphabetic_characters = sum(
            character.isalpha()
            for character in text
        )

        return alphabetic_characters >= 2