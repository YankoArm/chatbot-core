from chatbot.connectors.whatsapp.bootstrap import (
    build_tenant_whatsapp_message_handler,
)


class TenantRouter:
    def resolve_client_id(
        self,
        message,
    ) -> str | None:
        return "salon_norte"


class Application:
    def chat(
        self,
        *,
        session_id: str,
        message: str,
    ):
        return type(
            "Response",
            (),
            {
                "text": "Hola desde Salón Norte",
            },
        )()


class ApplicationRegistry:
    def get_application(
        self,
        client_id: str,
    ) -> object | None:
        assert client_id == "salon_norte"
        return Application()


class GraphClient:
    def __init__(
        self,
    ) -> None:
        self.to: str | None = None
        self.text: str | None = None

    def send_text_message(
        self,
        *,
        to: str,
        text: str,
    ) -> object:
        self.to = to
        self.text = text
        return object()


class GraphClientProvider:
    def __init__(
        self,
        graph_client: GraphClient,
    ) -> None:
        self.graph_client = graph_client
        self.phone_number_id: str | None = None

    def get_client(
        self,
        phone_number_id: str,
    ) -> GraphClient:
        self.phone_number_id = phone_number_id
        return self.graph_client


def test_tenant_bootstrap_routes_and_sends_from_receiver_number(
) -> None:
    graph_client = GraphClient()
    provider = GraphClientProvider(
        graph_client
    )

    handler = build_tenant_whatsapp_message_handler(
        tenant_router=TenantRouter(),
        application_registry=ApplicationRegistry(),
        graph_client_provider=provider,
    )

    result = handler.handle(
        {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {
                                    "phone_number_id": (
                                        "salon-norte-phone-id"
                                    ),
                                },
                                "messages": [
                                    {
                                        "from": "34600000000",
                                        "text": {
                                            "body": "Hola",
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                }
            ]
        }
    )

    assert result == "Hola desde Salón Norte"
    assert provider.phone_number_id == (
        "salon-norte-phone-id"
    )
    assert graph_client.to == "34600000000"
    assert graph_client.text == (
        "Hola desde Salón Norte"
    )