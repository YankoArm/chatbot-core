from chatbot.api.admin_services import (
    _build_unique_service_id,
)


def test_service_id_from_name() -> None:
    assert _build_unique_service_id(
        "Lectura de tarot 30 minutos",
        [],
    ) == "lectura_tarot_30_minutos"


def test_service_id_removes_accents() -> None:
    assert _build_unique_service_id(
        "Sesi\u00f3n b\u00e1sica",
        [],
    ) == "sesion_basica"


def test_service_id_avoids_duplicates() -> None:
    services = [
        {"id": "sesion_basica"},
        {"id": "sesion_basica_2"},
    ]

    assert _build_unique_service_id(
        "Sesi\u00f3n b\u00e1sica",
        services,
    ) == "sesion_basica_3"


def test_service_id_starts_with_letter() -> None:
    assert _build_unique_service_id(
        "30 minutos",
        [],
    ) == "service_30_minutos"
