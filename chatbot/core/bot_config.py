# chatbot/core/bot_config.py

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class BotConfig:
    name: str
    default_language: str = "es"
    supported_languages: List[str] = field(default_factory=lambda: ["es"])
    features: Dict[str, bool] = field(default_factory=dict)
    menu_items: List[Dict] = field(default_factory=list)
    menu_title: Dict[str, str] = field(default_factory=dict)
    menu_footer: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_template(
        cls,
        template: Dict,
        default_language: str = "es",
        supported_languages: List[str] | None = None,
    ) -> "BotConfig":
        return cls(
            name=template["name"],
            default_language=default_language,
            supported_languages=supported_languages or ["es"],
            features=template.get("features", {}),
            menu_items=template.get("menu_items", []),
            menu_title=template.get("menu_title", {}),
            menu_footer=template.get("menu_footer", {}),
        )

    def is_feature_enabled(self, feature_name: str) -> bool:
        return self.features.get(feature_name, False)

    def get_enabled_menu_items(self) -> List[Dict]:
        return [
            item
            for item in self.menu_items
            if self.is_feature_enabled(item["feature"])
        ]

    def get_menu_action_by_number(self, option_number: str) -> str | None:
        if not option_number.isdigit():
            return None

        index = int(option_number) - 1
        enabled_items = self.get_enabled_menu_items()

        if index < 0 or index >= len(enabled_items):
            return None

        return enabled_items[index]["id"]