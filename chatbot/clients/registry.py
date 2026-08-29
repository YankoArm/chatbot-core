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


class UnknownTemplateError(ValueError):
    pass


TemplateFactory = Callable[
    [],
    TemplateDefinition,
]
InstanceDefinitionFactory = Callable[
    [],
    InstanceDefinition,
]


_TEMPLATE_REGISTRY: dict[
    str,
    TemplateFactory,
] = {
    "hairdressing": (
        create_hairdressing_template
    ),
    "tarot": create_tarot_template,
}


_CLIENT_DEFINITION_REGISTRY: dict[
    str,
    InstanceDefinitionFactory,
] = {
    "hairdressing_demo": (
        create_hairdressing_demo_definition
    ),
    "tarot_alvin": (
        create_tarot_alvin_definition
    ),
}


def list_client_ids(
) -> list[str]:
    """
    Return all built-in FlowForge client identifiers.
    """

    return sorted(
        _CLIENT_DEFINITION_REGISTRY
    )


def list_template_ids(
) -> list[str]:
    """
    Return all reusable FlowForge template identifiers.
    """

    return sorted(
        _TEMPLATE_REGISTRY
    )


def build_client_definition(
    client_id: str,
) -> InstanceDefinition:
    """
    Build one built-in client definition.
    """

    try:
        definition_factory = (
            _CLIENT_DEFINITION_REGISTRY[
                client_id
            ]
        )
    except KeyError as error:
        raise UnknownClientError(
            f"Unknown FlowForge client: {client_id}"
        ) from error

    return definition_factory()


def build_template_definition(
    template_id: str,
) -> TemplateDefinition:
    """
    Build one registered reusable business template.
    """

    try:
        template_factory = (
            _TEMPLATE_REGISTRY[
                template_id
            ]
        )
    except KeyError as error:
        raise UnknownTemplateError(
            f"Unknown FlowForge template: {template_id}"
        ) from error

    return template_factory()


def build_instance_from_definition(
    definition: InstanceDefinition,
) -> Instance:
    """
    Resolve a stored client definition against its template.
    """

    template = build_template_definition(
        definition.template_id
    )

    return InstanceResolver().resolve(
        template=template,
        definition=definition,
    )


def build_client_instance(
    client_id: str,
) -> Instance:
    """
    Build one configured built-in client instance.
    """

    definition = build_client_definition(
        client_id
    )

    return build_instance_from_definition(
        definition
    )