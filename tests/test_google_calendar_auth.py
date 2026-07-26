from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import chatbot.calendar.google_auth as google_auth


class FakeCredentials:
    def __init__(
        self,
        *,
        valid: bool,
        expired: bool = False,
        refresh_token: str | None = None,
        serialized: str = '{"token": "saved"}',
    ) -> None:
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.serialized = serialized
        self.refresh_calls: list[Any] = []

    def refresh(
        self,
        request: Any,
    ) -> None:
        self.refresh_calls.append(
            request
        )
        self.valid = True
        self.expired = False

    def to_json(
        self,
    ) -> str:
        return self.serialized


class FakeInstalledAppFlow:
    def __init__(
        self,
        credentials: FakeCredentials,
    ) -> None:
        self.credentials = credentials
        self.run_local_server_calls: list[
            dict[str, Any]
        ] = []

    def run_local_server(
        self,
        **kwargs: Any,
    ) -> FakeCredentials:
        self.run_local_server_calls.append(
            kwargs
        )

        return self.credentials


def test_build_google_calendar_service_uses_valid_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credentials_path = (
        tmp_path / "credentials.json"
    )
    token_path = tmp_path / "token.json"

    credentials_path.write_text(
        "{}",
        encoding="utf-8",
    )
    token_path.write_text(
        "{}",
        encoding="utf-8",
    )

    credentials = FakeCredentials(
        valid=True
    )

    loaded_calls: list[
        tuple[str, list[str]]
    ] = []

    def fake_load(
        path: str,
        scopes: list[str],
    ) -> FakeCredentials:
        loaded_calls.append(
            (path, scopes)
        )
        return credentials

    build_calls: list[
        dict[str, Any]
    ] = []

    expected_service = object()

    def fake_build(
        service_name: str,
        version: str,
        **kwargs: Any,
    ) -> object:
        build_calls.append(
            {
                "service_name": service_name,
                "version": version,
                **kwargs,
            }
        )

        return expected_service

    monkeypatch.setattr(
        google_auth.Credentials,
        "from_authorized_user_file",
        fake_load,
    )
    monkeypatch.setattr(
        google_auth,
        "build",
        fake_build,
    )

    service = (
        google_auth
        .build_google_calendar_service(
            credentials_path=credentials_path,
            token_path=token_path,
        )
    )

    assert service is expected_service

    assert loaded_calls == [
        (
            str(token_path),
            [
                "https://www.googleapis.com/"
                "auth/calendar.events"
            ],
        )
    ]

    assert build_calls == [
        {
            "service_name": "calendar",
            "version": "v3",
            "credentials": credentials,
            "cache_discovery": False,
        }
    ]


def test_build_google_calendar_service_refreshes_expired_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credentials_path = (
        tmp_path / "credentials.json"
    )
    token_path = tmp_path / "token.json"

    credentials_path.write_text(
        "{}",
        encoding="utf-8",
    )
    token_path.write_text(
        "{}",
        encoding="utf-8",
    )

    credentials = FakeCredentials(
        valid=False,
        expired=True,
        refresh_token="refresh-token",
    )

    monkeypatch.setattr(
        google_auth.Credentials,
        "from_authorized_user_file",
        lambda path, scopes: credentials,
    )

    fake_request = object()

    monkeypatch.setattr(
        google_auth,
        "Request",
        lambda: fake_request,
    )

    expected_service = object()

    monkeypatch.setattr(
        google_auth,
        "build",
        lambda *args, **kwargs: expected_service,
    )

    service = (
        google_auth
        .build_google_calendar_service(
            credentials_path=credentials_path,
            token_path=token_path,
        )
    )

    assert service is expected_service
    assert credentials.refresh_calls == [
        fake_request
    ]

    assert token_path.read_text(
        encoding="utf-8"
    ) == '{"token": "saved"}'


def test_build_google_calendar_service_runs_oauth_flow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credentials_path = (
        tmp_path / "credentials.json"
    )
    token_path = tmp_path / "auth/token.json"

    credentials_path.write_text(
        "{}",
        encoding="utf-8",
    )

    credentials = FakeCredentials(
        valid=True,
        serialized='{"token": "oauth"}',
    )

    flow = FakeInstalledAppFlow(
        credentials
    )

    flow_creation_calls: list[
        tuple[str, list[str]]
    ] = []

    def fake_from_client_secrets_file(
        path: str,
        scopes: list[str],
    ) -> FakeInstalledAppFlow:
        flow_creation_calls.append(
            (path, scopes)
        )
        return flow

    monkeypatch.setattr(
        google_auth.InstalledAppFlow,
        "from_client_secrets_file",
        fake_from_client_secrets_file,
    )

    expected_service = object()

    monkeypatch.setattr(
        google_auth,
        "build",
        lambda *args, **kwargs: expected_service,
    )

    service = (
        google_auth
        .build_google_calendar_service(
            credentials_path=credentials_path,
            token_path=token_path,
        )
    )

    assert service is expected_service

    assert flow_creation_calls == [
        (
            str(credentials_path),
            [
                "https://www.googleapis.com/"
                "auth/calendar.events"
            ],
        )
    ]

    assert flow.run_local_server_calls == [
        {
            "port": 0,
        }
    ]

    assert token_path.read_text(
        encoding="utf-8"
    ) == '{"token": "oauth"}'


def test_build_google_calendar_service_requires_credentials_file(
    tmp_path: Path,
) -> None:
    missing_path = (
        tmp_path / "missing.json"
    )

    with pytest.raises(
        FileNotFoundError,
        match="credentials file was not found",
    ):
        google_auth.build_google_calendar_service(
            credentials_path=missing_path,
            token_path=tmp_path / "token.json",
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "credentials_path",
        "token_path",
    ),
    [
        (
            "credentials_path",
            " ",
            "token.json",
        ),
        (
            "token_path",
            "credentials.json",
            " ",
        ),
    ],
)
def test_build_google_calendar_service_rejects_empty_paths(
    field_name: str,
    credentials_path: str,
    token_path: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=f"{field_name} cannot be empty",
    ):
        google_auth.build_google_calendar_service(
            credentials_path=credentials_path,
            token_path=token_path,
        )


def test_build_google_calendar_service_rejects_empty_scopes(
    tmp_path: Path,
) -> None:
    credentials_path = (
        tmp_path / "credentials.json"
    )

    credentials_path.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="scopes cannot be empty",
    ):
        google_auth.build_google_calendar_service(
            credentials_path=credentials_path,
            token_path=tmp_path / "token.json",
            scopes=[],
        )


def test_build_google_calendar_service_rejects_duplicate_scopes(
    tmp_path: Path,
) -> None:
    credentials_path = (
        tmp_path / "credentials.json"
    )

    credentials_path.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="cannot contain duplicates",
    ):
        google_auth.build_google_calendar_service(
            credentials_path=credentials_path,
            token_path=tmp_path / "token.json",
            scopes=[
                "scope-a",
                "scope-a",
            ],
        )