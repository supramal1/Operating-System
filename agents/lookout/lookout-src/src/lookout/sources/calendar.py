"""Lookout calendar source — Google Calendar OAuth client, READ-ONLY.

READ-ONLY CONTRACT (do not relax):
    This module imports only the read methods of the Google Calendar API
    (`service.events().list(...)`). It NEVER imports or invokes:
      - service.events().insert(...)
      - service.events().update(...)
      - service.events().delete(...)
      - service.events().patch(...)
    Adding a write method here is an AC-1 violation. The calendar adapter
    is a one-way valve from Calendar -> Lookout's prompt.

Auth pattern mirrors `co-platform/platform/library/scripts/drive_sweep.py`
get_credentials (installed-app OAuth, token cached at
`~/.config/co-lookout-calendar/token.json`, separate from Drive/Scout tokens
so they don't fight over scopes/refresh cycles).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .. import run_context as _rc  # avoid circular


SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
TOKEN_CACHE_PATH = Path.home() / ".config" / "co-lookout-calendar" / "token.json"


@dataclass(frozen=True)
class CalendarEvent:
    id: str
    summary: str
    description: str
    start: str            # ISO string (datetime or date for all-day)
    end: str
    attendees: list[dict[str, Any]]  # [{email, display_name, response_status}]
    organizer_email: str
    location: str
    all_day: bool
    hangout_link: str


@dataclass(frozen=True)
class CalendarRead:
    events: list[CalendarEvent]
    window_start: datetime
    window_end: datetime
    errors: list[str] = field(default_factory=list)


def _oauth_client_path() -> Path | None:
    """Resolve the installed-app OAuth client JSON.

    Source of truth: env var `LOOKOUT_GOOGLE_CLIENT_JSON`. If unset, we warn
    and fall back to the same client JSON Scout / drive_sweep already use,
    which is the only OAuth client that exists on Mal's machine today.
    """
    env_path = os.environ.get("LOOKOUT_GOOGLE_CLIENT_JSON")
    if env_path:
        p = Path(env_path).expanduser()
        if p.exists():
            return p
        print(
            f"[lookout/calendar] LOOKOUT_GOOGLE_CLIENT_JSON={env_path!r} does "
            f"not exist; falling back.",
            file=sys.stderr,
        )
    fallback = (
        Path.home()
        / "Desktop/Charlie-Oscar-OS-Prep/06-Agents/01-Agent-Build-Packs"
        / "Ai-ops/01-scout/oauth/google-drive-client.json"
    )
    if fallback.exists():
        print(
            "[lookout/calendar] using fallback OAuth client at Scout's "
            f"location ({fallback}). Set LOOKOUT_GOOGLE_CLIENT_JSON to "
            "override.",
            file=sys.stderr,
        )
        return fallback
    return None


def _get_credentials() -> Any | None:
    """Return Google API credentials or None on failure (do not raise)."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as e:
        print(f"[lookout/calendar] google libraries not importable: {e}", file=sys.stderr)
        return None

    creds: Any | None = None
    TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TOKEN_CACHE_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_CACHE_PATH), SCOPES)
        except Exception as e:
            print(f"[lookout/calendar] cached token unreadable: {e}", file=sys.stderr)
            creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[lookout/calendar] token refresh failed: {e}", file=sys.stderr)
                return None
        else:
            client_path = _oauth_client_path()
            if client_path is None:
                print(
                    "[lookout/calendar] no OAuth client JSON found. Set "
                    "LOOKOUT_GOOGLE_CLIENT_JSON to point at the installed-app "
                    "client_secret.json.",
                    file=sys.stderr,
                )
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
                print("[lookout/calendar] opening browser for Calendar OAuth consent...")
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"[lookout/calendar] OAuth flow failed: {e}", file=sys.stderr)
                return None
        try:
            TOKEN_CACHE_PATH.write_text(creds.to_json())
            os.chmod(TOKEN_CACHE_PATH, 0o600)
        except OSError as e:
            print(f"[lookout/calendar] could not cache token: {e}", file=sys.stderr)
    return creds


def _day_window(run_context: "_rc.RunContext") -> tuple[datetime, datetime]:
    tz = ZoneInfo(run_context.calendar_time_zone)
    start_local = datetime.combine(run_context.date, time.min, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def _normalise_event(raw: dict[str, Any]) -> CalendarEvent:
    start_obj = raw.get("start", {}) or {}
    end_obj = raw.get("end", {}) or {}
    all_day = "date" in start_obj and "dateTime" not in start_obj
    attendees_raw = raw.get("attendees", []) or []
    attendees = [
        {
            "email": a.get("email", ""),
            "display_name": a.get("displayName", ""),
            "response_status": a.get("responseStatus", ""),
        }
        for a in attendees_raw
        if isinstance(a, dict)
    ]
    return CalendarEvent(
        id=raw.get("id", ""),
        summary=raw.get("summary", ""),
        description=raw.get("description", ""),
        start=start_obj.get("dateTime") or start_obj.get("date", ""),
        end=end_obj.get("dateTime") or end_obj.get("date", ""),
        attendees=attendees,
        organizer_email=(raw.get("organizer") or {}).get("email", ""),
        location=raw.get("location", ""),
        all_day=all_day,
        hangout_link=raw.get("hangoutLink", ""),
    )


def fetch_today_events(run_context: "_rc.RunContext") -> CalendarRead:
    """Fetch the principal's events for `run_context.date`.

    Returns an empty CalendarRead with `errors` populated if OAuth or the API
    call fails. NEVER raises out of this function — Lookout should still run
    and surface the gap in the brief's "What I couldn't check" section.
    """
    window_start, window_end = _day_window(run_context)
    errors: list[str] = []

    creds = _get_credentials()
    if creds is None:
        errors.append("calendar-auth-unavailable")
        return CalendarRead(events=[], window_start=window_start, window_end=window_end, errors=errors)

    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError as e:
        errors.append(f"google-api-import-failed: {e}")
        return CalendarRead(events=[], window_start=window_start, window_end=window_end, errors=errors)

    try:
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        resp = (
            service.events()
            .list(
                calendarId=run_context.principal_id,
                timeMin=window_start.isoformat(),
                timeMax=window_end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=250,
            )
            .execute()
        )
    except HttpError as e:
        errors.append(f"calendar-api-error: {e}")
        return CalendarRead(events=[], window_start=window_start, window_end=window_end, errors=errors)
    except Exception as e:
        errors.append(f"calendar-unexpected-error: {e}")
        return CalendarRead(events=[], window_start=window_start, window_end=window_end, errors=errors)

    events = [_normalise_event(item) for item in resp.get("items", [])]
    return CalendarRead(
        events=events,
        window_start=window_start,
        window_end=window_end,
        errors=errors,
    )
