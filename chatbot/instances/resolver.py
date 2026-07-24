from __future__ import annotations

from copy import deepcopy
from typing import Any

from chatbot.instances.definition import InstanceDefinition
from chatbot.instances.instance import Instance
from chatbot.instances.template import TemplateDefinition


class InstanceResolver:
    """
    Combine a business template with a client-specific definition.

    The result is a fully resolved Instance ready to be passed to
    FlowForge Bootstrap.
    """

    def resolve(
        self,
        template: TemplateDefinition,
        definition: InstanceDefinition,
    ) -> Instance:
        self._validate_template_reference(
            template=template,
            definition=definition,
        )

        capabilities = self._merge_named_items(
            inherited=template.capabilities,
            added=definition.capabilities,
            disabled=definition.disabled_capabilities,
        )

        connectors = self._merge_named_items(
            inherited=template.connectors,
            added=definition.connectors,
            disabled=definition.disabled_connectors,
        )

        channels = self._merge_named_items(
            inherited=template.channels,
            added=definition.channels,
        )

        supported_languages = (
            list(definition.supported_languages)
            if definition.supported_languages is not None
            else list(template.supported_languages)
        )

        default_language = (
            definition.default_language
            or template.default_language
        )

        self._validate_languages(
            default_language=default_language,
            supported_languages=supported_languages,
        )

        return Instance(
            id=definition.id,
            name=definition.name,
            template_id=template.id,
            default_language=default_language,
            supported_languages=supported_languages,
            channels=channels,
            capabilities=capabilities,
            connectors=connectors,
            knowledge_path=(
                definition.knowledge_path
                or template.knowledge_path
            ),
            settings=self._deep_merge(
                template.settings,
                definition.settings,
            ),
            metadata=self._deep_merge(
                template.metadata,
                definition.metadata,
            ),
            activation=(
                definition.activation
                if definition.activation is not None
                else deepcopy(template.activation)
            ),
        )

    @staticmethod
    def _validate_template_reference(
        template: TemplateDefinition,
        definition: InstanceDefinition,
    ) -> None:
        if definition.template_id != template.id:
            raise ValueError(
                "Instance definition references template "
                f"{definition.template_id!r}, but template "
                f"{template.id!r} was provided."
            )

    @staticmethod
    def _validate_languages(
        default_language: str,
        supported_languages: list[str],
    ) -> None:
        if not supported_languages:
            raise ValueError(
                "An instance must support at least one language."
            )

        if default_language not in supported_languages:
            raise ValueError(
                f"Default language {default_language!r} must be "
                "included in supported_languages."
            )

    @staticmethod
    def _merge_named_items(
        inherited: list[str],
        added: list[str],
        disabled: list[str] | None = None,
    ) -> list[str]:
        disabled_items = set(disabled or [])

        result: list[str] = []

        for item in [*inherited, *added]:
            if item in disabled_items:
                continue

            if item not in result:
                result.append(item)

        return result

    @classmethod
    def _deep_merge(
        cls,
        inherited: dict[str, Any],
        overrides: dict[str, Any],
    ) -> dict[str, Any]:
        result = deepcopy(inherited)

        for key, value in overrides.items():
            inherited_value = result.get(key)

            if (
                isinstance(inherited_value, dict)
                and isinstance(value, dict)
            ):
                result[key] = cls._deep_merge(
                    inherited_value,
                    value,
                )
            else:
                result[key] = deepcopy(value)

        return result