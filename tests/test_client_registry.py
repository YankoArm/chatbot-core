import pytest

from chatbot.clients.registry import (
    UnknownClientError,
    UnknownTemplateError,
    build_client_definition,
    build_client_instance,
    build_instance_from_definition,
    build_template_definition,
    list_client_ids,
    list_template_ids,
)
from chatbot.instances import InstanceDefinition


def test_list_client_ids():
    assert list_client_ids() == [
        "hairdressing_demo",
        "tarot_alvin",
    ]


def test_list_template_ids():
    assert list_template_ids() == [
        "hairdressing",
        "tarot",
    ]


@pytest.mark.parametrize(
    ("client_id", "expected_name", "expected_template_id"),
    [
        (
            "hairdressing_demo",
            "Salón Estilo",
            "hairdressing",
        ),
        (
            "tarot_alvin",
            "Tarot Alvin",
            "tarot",
        ),
    ],
)
def test_build_registered_client_instance(
    client_id: str,
    expected_name: str,
    expected_template_id: str,
):
    instance = build_client_instance(
        client_id
    )

    assert instance.id == client_id
    assert instance.name == expected_name
    assert instance.template_id == (
        expected_template_id
    )


def test_build_registered_client_definition():
    definition = build_client_definition(
        "hairdressing_demo"
    )

    assert definition.id == (
        "hairdressing_demo"
    )
    assert definition.name == (
        "Salón Estilo"
    )
    assert definition.template_id == (
        "hairdressing"
    )


def test_build_registered_template_definition():
    template = build_template_definition(
        "hairdressing"
    )

    assert template.id == "hairdressing"
    assert template.name == (
        "Hairdressing Assistant"
    )


def test_build_instance_from_dynamic_definition():
    definition = InstanceDefinition(
        id="salon_norte",
        name="Salón Norte",
        template_id="hairdressing",
        settings={
            "branding": {
                "display_name": "Salón Norte",
            },
        },
    )

    instance = build_instance_from_definition(
        definition
    )

    assert instance.id == "salon_norte"
    assert instance.name == "Salón Norte"
    assert instance.template_id == (
        "hairdressing"
    )
    assert "booking" in instance.capabilities
    assert "whatsapp" in instance.channels
    assert instance.settings[
        "branding"
    ]["display_name"] == "Salón Norte"


def test_reject_unknown_client_id():
    with pytest.raises(
        UnknownClientError,
        match=(
            "Unknown FlowForge client: "
            "missing_client"
        ),
    ):
        build_client_instance(
            "missing_client"
        )


def test_reject_unknown_template_id():
    with pytest.raises(
        UnknownTemplateError,
        match=(
            "Unknown FlowForge template: "
            "missing_template"
        ),
    ):
        build_template_definition(
            "missing_template"
        )


def test_reject_dynamic_definition_with_unknown_template():
    definition = InstanceDefinition(
        id="unknown_business",
        name="Unknown Business",
        template_id="missing_template",
    )

    with pytest.raises(
        UnknownTemplateError,
        match=(
            "Unknown FlowForge template: "
            "missing_template"
        ),
    ):
        build_instance_from_definition(
            definition
        )