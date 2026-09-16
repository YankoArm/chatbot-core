import pytest

from run_cli import build_argument_parser, main


def test_cli_uses_tarot_alvin_by_default():
    parser = build_argument_parser()

    arguments = parser.parse_args([])

    assert arguments.client == "tarot_alvin"


def test_cli_accepts_hairdressing_demo():
    parser = build_argument_parser()

    arguments = parser.parse_args(
        [
            "--client",
            "hairdressing_demo",
        ]
    )

    assert arguments.client == "hairdressing_demo"


def test_cli_rejects_unknown_client():
    parser = build_argument_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--client",
                "missing_client",
            ]
        )

def test_cli_booking_database_is_optional():
    parser = build_argument_parser()

    arguments = parser.parse_args([])

    assert arguments.booking_database is None


def test_cli_accepts_custom_booking_database():
    parser = build_argument_parser()

    arguments = parser.parse_args(
        [
            "--client",
            "hairdressing_demo",
            "--booking-database",
            "persistent/demo.sqlite3",
        ]
    )

    assert arguments.booking_database == (
        "persistent/demo.sqlite3"
    )

def test_cli_runs_professional_services_demo_without_booking(
    monkeypatch,
    capsys,
):
    class FakeCLIChannel:
        def __init__(
            self,
            application_channel,
        ) -> None:
            self.application_channel = application_channel

        def run(self) -> None:
            pass

    def calendar_must_not_be_built():
        raise AssertionError(
            "Calendar must not be built without booking"
        )

    monkeypatch.setattr(
        "run_cli.CLIChannel",
        FakeCLIChannel,
    )
    monkeypatch.setattr(
        "run_cli.build_calendar_service",
        calendar_must_not_be_built,
    )

    main(
        [
            "--client",
            "professional_services_demo",
        ]
    )

    output = capsys.readouterr().out

    assert "FlowForge CLI - Nexo Servicios" in output
    assert "Google Calendar integration enabled." not in output
    assert "Client booking configuration loaded." not in output
