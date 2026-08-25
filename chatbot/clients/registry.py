from __future__ import annotations

from collections.abc import Callable

from chatbot.business_templates.hairdressing import (
    create_hairdressing_template,
)
from chatbot.business_templates.tarot import (
    create_tarot_template,
)
from chatbot.clients.hairdressing_demo import (
    create_hairdressing_demo_definition,
)
from chatbot.clients.tarot_alvin import (
    create_tarot_alvin_definition,
)
from chatbot.instances import (
    Instance,
    InstanceDefinition,
    InstanceResolver,
    TemplateDefinition,
)


class UnknownClientError(ValueError):
    pass


TemplateFactory = Callable[[], TemplateDefinition]
InstanceDefinitionFactory = Callable[[], InstanceDefinition]
ClientFactories = tuple[
    TemplateFactory,
    InstanceDefinitionFactory,
]


_CLIENT_REGISTRY: dict[str, ClientFactories] = {
    "hairdressing_demo": (
        create_hairdressing_template,
        create_hairdressing_demo_definition,
    ),
    "tarot_alvin": (
        create_tarot_template,
        create_tarot_alvin_definition,
    ),
}


def list_client_ids() -> list[str]:
    """
    Return all registered FlowForge client identifiers.
    """

    return sorted(_CLIENT_REGISTRY)


def build_client_instance(
    client_id: str,
) -> Instance:
    """
    Build one configured client instance from its registered factories.
    """

    try:
        template_factory, definition_factory = (
            _CLIENT_REGISTRY[client_id]
        )
    except KeyError as error:
        raise UnknownClientError(
            f"Unknown FlowForge client: {client_id}"
        ) from error

    return InstanceResolver().resolve(
        template=template_factory(),
        definition=definition_factory(),
    )