from types import SimpleNamespace

from chatbot.application.application import (
    FlowForgeApplication,
)
from chatbot.conversation import ConversationStore
from chatbot.leads import (
    LeadCaptureActionDispatcher,
    SQLiteLeadRepository,
)
from chatbot.responses import Response


class EmptyCapabilityManager:
    def all(self) -> list:
        return []


class LeadProducingOrchestrator:
    def process(
        self,
        context,
        message: str,
    ) -> Response:
        context.add_pending_action(
            {
                "type": "lead_capture",
                "name": "Yanko",
                "phone": "+34600123123",
                "reason": "Necesito un presupuesto.",
            }
        )

        return Response(text="Solicitud recibida.")


class RecordingDispatcher:
    def __init__(self) -> None:
        self.actions: list[dict] = []

    def dispatch(
        self,
        *,
        instance,
        session_id: str,
        action: dict,
    ) -> bool:
        self.actions.append(
            {
                "client_id": instance.id,
                "session_id": session_id,
                "action": action,
            }
        )

        return action["type"] == "lead_capture"


def test_application_dispatches_processed_pending_actions():
    dispatcher = RecordingDispatcher()

    application = FlowForgeApplication(
        instance=SimpleNamespace(
            id="professional_services_demo",
        ),
        orchestrator=LeadProducingOrchestrator(),
        capability_manager=EmptyCapabilityManager(),
        conversation_store=ConversationStore(),
        pending_action_dispatcher=dispatcher,
    )

    response = application.chat(
        session_id="whatsapp:+34600123123",
        message="Necesito ayuda.",
    )

    context = application.conversation_store.get(
        "whatsapp:+34600123123"
    )

    assert response.text == "Solicitud recibida."
    assert dispatcher.actions == [
        {
            "client_id": "professional_services_demo",
            "session_id": "whatsapp:+34600123123",
            "action": {
                "type": "lead_capture",
                "name": "Yanko",
                "phone": "+34600123123",
                "reason": "Necesito un presupuesto.",
            },
        }
    ]
    assert context.pending_actions == []


def test_lead_action_dispatcher_persists_one_lead(
    tmp_path,
) -> None:
    repository = SQLiteLeadRepository(
        database_path=tmp_path / "leads.sqlite3",
    )
    dispatcher = LeadCaptureActionDispatcher(
        repository=repository,
    )
    instance = SimpleNamespace(
        id="professional_services_demo",
    )
    action = {
        "type": "lead_capture",
        "name": "Yanko",
        "phone": "+34600123123",
        "reason": "Necesito un presupuesto.",
    }

    assert dispatcher.dispatch(
        instance=instance,
        session_id="whatsapp:+34600123123",
        action=action,
    ) is True

    assert dispatcher.dispatch(
        instance=instance,
        session_id="whatsapp:+34600123123",
        action=action,
    ) is True

    assert repository.list_by_client(
        client_id="professional_services_demo",
    )[0].name == "Yanko"

    assert len(
        repository.list_by_client(
            client_id="professional_services_demo",
        )
    ) == 1

    repository.close()


def test_lead_action_dispatcher_ignores_other_actions(
    tmp_path,
) -> None:
    repository = SQLiteLeadRepository(
        database_path=tmp_path / "leads.sqlite3",
    )
    dispatcher = LeadCaptureActionDispatcher(
        repository=repository,
    )

    assert dispatcher.dispatch(
        instance=SimpleNamespace(
            id="professional_services_demo",
        ),
        session_id="session-1",
        action={
            "type": "human_transfer",
            "status": "pending",
        },
    ) is False

    repository.close()


def test_application_keeps_unhandled_pending_actions():
    class RejectingDispatcher:
        def dispatch(
            self,
            *,
            instance,
            session_id: str,
            action: dict,
        ) -> bool:
            return False

    application = FlowForgeApplication(
        instance=SimpleNamespace(
            id="professional_services_demo",
        ),
        orchestrator=LeadProducingOrchestrator(),
        capability_manager=EmptyCapabilityManager(),
        conversation_store=ConversationStore(),
        pending_action_dispatcher=RejectingDispatcher(),
    )

    application.chat(
        session_id="whatsapp:+34600123123",
        message="Necesito ayuda.",
    )

    context = application.conversation_store.get(
        "whatsapp:+34600123123"
    )

    assert context.pending_actions == [
        {
            "type": "lead_capture",
            "name": "Yanko",
            "phone": "+34600123123",
            "reason": "Necesito un presupuesto.",
        }
    ]
