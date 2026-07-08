from chatbot.conversation import ConversationStore


def test_conversation_store_creates_context():
    store = ConversationStore()

    context = store.get("session_1")

    assert context.session_id == "session_1"
    assert store.count() == 1


def test_conversation_store_reuses_existing_context():
    store = ConversationStore()

    first = store.get("session_1")
    second = store.get("session_1")

    assert first is second
    assert store.count() == 1


def test_conversation_store_resets_context():
    store = ConversationStore()

    context = store.get("session_1")
    context.set_active_capability("booking")
    context.set_variable("date", "tomorrow")

    store.reset("session_1")

    assert context.active_capability is None
    assert context.get_variable("date") is None


def test_conversation_store_deletes_context():
    store = ConversationStore()

    store.get("session_1")
    store.delete("session_1")

    assert store.count() == 0