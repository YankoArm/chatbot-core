import pytest

from run_cli import build_argument_parser


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