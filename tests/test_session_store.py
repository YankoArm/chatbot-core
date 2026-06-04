from chatbot.core.session import Session
from chatbot.storage.session_store import SessionStore


def test_session_store_saves_and_loads_session(tmp_path):
    file_path = tmp_path / "sessions.json"

    store = SessionStore(file_path=str(file_path))

    session = Session(user_id="test_user")
    session.language = "es"
    session.current_state = "MAIN_MENU"
    session.selected_session = "Sesión general"
    session.selected_date = "Lunes 10:00"
    session.booking_confirmed = True
    session.add_message("user", "hola")
    session.add_message("assistant", "Hola, ¿qué deseas hacer?")

    sessions = {
        "test_user": session
    }

    store.save_all(sessions)

    loaded_sessions = store.load_all()

    assert "test_user" in loaded_sessions

    loaded_session = loaded_sessions["test_user"]

    assert loaded_session.user_id == "test_user"
    assert loaded_session.language == "es"
    assert loaded_session.current_state == "MAIN_MENU"
    assert loaded_session.selected_session == "Sesión general"
    assert loaded_session.selected_date == "Lunes 10:00"
    assert loaded_session.booking_confirmed is True
    assert len(loaded_session.history) == 2
    assert loaded_session.history[0]["role"] == "user"
    assert loaded_session.history[0]["content"] == "hola"


def test_session_store_returns_empty_dict_when_file_does_not_exist(tmp_path):
    file_path = tmp_path / "missing_sessions.json"

    store = SessionStore(file_path=str(file_path))

    loaded_sessions = store.load_all()

    assert loaded_sessions == {}