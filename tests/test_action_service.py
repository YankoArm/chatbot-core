from chatbot.services.action_service import ActionService


def test_action_service_executes_registered_action():
    service = ActionService()

    service.register("hello", lambda session: "Hello world")

    result = service.execute("hello", session=None)

    assert result == "Hello world"


def test_action_service_returns_none_for_unknown_action():
    service = ActionService()

    result = service.execute("unknown", session=None)

    assert result is None