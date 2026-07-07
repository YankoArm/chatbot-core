from chatbot.capabilities.base_capability import BaseCapability


class CapabilityManager:
    def __init__(self):
        self._capabilities: dict[str, BaseCapability] = {}

    def register(self, capability: BaseCapability) -> None:
        self._capabilities[capability.name] = capability

    def get(self, name: str) -> BaseCapability | None:
        return self._capabilities.get(name)

    def all(self) -> list[BaseCapability]:
        return list(self._capabilities.values())

    def is_enabled(self, name: str) -> bool:
        return name in self._capabilities