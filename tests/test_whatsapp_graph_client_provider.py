from chatbot.connectors.whatsapp.graph_client import (
    WhatsAppGraphClientProvider,
)


def test_graph_client_provider_builds_and_caches_clients_by_phone_number(
) -> None:
    built_phone_number_ids: list[str] = []
    graph_client = object()

    def build_graph_client(
        phone_number_id: str,
    ) -> object:
        built_phone_number_ids.append(
            phone_number_id
        )
        return graph_client

    provider = WhatsAppGraphClientProvider(
        access_token="server-only-token",
        graph_client_factory=build_graph_client,
    )

    first_client = provider.get_client(
        "salon-norte-phone-id"
    )
    second_client = provider.get_client(
        "salon-norte-phone-id"
    )

    assert first_client is graph_client
    assert second_client is graph_client
    assert built_phone_number_ids == [
        "salon-norte-phone-id",
    ]