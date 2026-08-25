import pytest

from chatbot.clients.registry import (
    UnknownClientError,
    build_client_instance,
    list_client_ids,
)


def test_list_client_ids():
    assert list_client_ids() == [
        "hairdressing_demo",
        "tarot_alvin",
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
    instance = build_client_instance(client_id)

    assert instance.id == client_id
    assert instance.name == expected_name
    assert instance.template_id == expected_template_id


def test_reject_unknown_client_id():
    with pytest.raises(
        UnknownClientError,
        match="Unknown FlowForge client: missing_client",
    ):
        build_client_instance("missing_client")