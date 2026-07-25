import pytest

from chatbot.knowledge.provider import KnowledgeProvider


def test_knowledge_provider_cannot_be_instantiated():
    with pytest.raises(TypeError):
        KnowledgeProvider()