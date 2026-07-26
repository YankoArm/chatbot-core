from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


DEFAULT_GOOGLE_CALENDAR_SCOPES = (
    "https://www.googleapis.com/auth/calendar.events",
)


def build_google_calendar_service(
    *,
    credentials_path: str | Path,
    token_path: str | Path,
    scopes: Sequence[str] | None = None,
) -> Any:
    """
    Build an authenticated Google Calendar API service.

    The OAuth client configuration is loaded from credentials_path.
    The resulting user credentials are persisted in token_path so
    future executions do not require authorization through the browser.
    """

    normalized_credentials_path = _normalize_path(
        credentials_path,
        field_name="credentials_path",
    )

    normalized_token_path = _normalize_path(
        token_path,
        field_name="token_path",
    )

    normalized_scopes = _normalize_scopes(
        scopes
    )

    if not normalized_credentials_path.is_file():
        raise FileNotFoundError(
            "Google OAuth credentials file was not found: "
            f"{normalized_credentials_path}"
        )

    credentials = _load_stored_credentials(
        token_path=normalized_token_path,
        scopes=normalized_scopes,
    )

    if credentials is None or not credentials.valid:
        credentials = _authorize_credentials(
            credentials=credentials,
            credentials_path=normalized_credentials_path,
            scopes=normalized_scopes,
        )

        _save_credentials(
            credentials=credentials,
            token_path=normalized_token_path,
        )

    return build(
        "calendar",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )


def _load_stored_credentials(
    *,
    token_path: Path,
    scopes: tuple[str, ...],
) -> Credentials | None:
    if not token_path.is_file():
        return None

    return Credentials.from_authorized_user_file(
        str(token_path),
        scopes=list(scopes),
    )


def _authorize_credentials(
    *,
    credentials: Credentials | None,
    credentials_path: Path,
    scopes: tuple[str, ...],
) -> Credentials:
    if (
        credentials is not None
        and credentials.expired
        and credentials.refresh_token
    ):
        credentials.refresh(
            Request()
        )

        return credentials

    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path),
        scopes=list(scopes),
    )

    return flow.run_local_server(
        port=0,
    )


def _save_credentials(
    *,
    credentials: Credentials,
    token_path: Path,
) -> None:
    token_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    token_path.write_text(
        credentials.to_json(),
        encoding="utf-8",
    )


def _normalize_path(
    value: str | Path,
    *,
    field_name: str,
) -> Path:
    if isinstance(value, Path):
        normalized_path = value
    elif isinstance(value, str):
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        normalized_path = Path(
            normalized_value
        )
    else:
        raise TypeError(
            f"{field_name} must be a string or Path."
        )

    return normalized_path.expanduser()


def _normalize_scopes(
    scopes: Sequence[str] | None,
) -> tuple[str, ...]:
    if scopes is None:
        return DEFAULT_GOOGLE_CALENDAR_SCOPES

    normalized_scopes = tuple(
        scope.strip()
        for scope in scopes
        if isinstance(scope, str)
        and scope.strip()
    )

    if not normalized_scopes:
        raise ValueError(
            "Google Calendar scopes cannot be empty."
        )

    if len(set(normalized_scopes)) != len(
        normalized_scopes
    ):
        raise ValueError(
            "Google Calendar scopes cannot contain duplicates."
        )

    return normalized_scopes