"""Lookout cornerstone source — read-only HTTP wrapper for the local backend.

READ-ONLY CONTRACT (do not relax):
    This module ONLY uses the `/context` read endpoint of Cornerstone's HTTP
    API. It NEVER imports or invokes:
      - /remember
      - /add_fact
      - /add_note
      - /save_conversation
      - /forget
    Adding any of those here is an AC-1 / MC-6 violation. The cornerstone
    adapter is a one-way valve from Cornerstone -> Lookout's prompt.

MC-6 ENFORCEMENT (do not relax):
    Every call MUST carry an explicit `client_scope`. The wrapper raises
    `ValueError("MC-6: client_scope is required")` if the RunContext's
    `client_scope` is empty. This catches misuse at the edge.

Net-new code (no existing Python cornerstone client in co-platform as of
2026-06-03; confirmed during scaffold).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import httpx

from .. import run_context as _rc


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class CornerstoneRead:
    text: str
    items_retrieved: int
    context_request_id: str | None
    errors: list[str] = field(default_factory=list)


def _resolve_base_url() -> str:
    return os.environ.get("CORNERSTONE_URL", DEFAULT_BASE_URL).rstrip("/")


def _resolve_api_key() -> str:
    key = os.environ.get("MEMORY_API_KEY")
    if not key:
        raise ValueError(
            "MEMORY_API_KEY is required for Lookout's cornerstone read. "
            "Set it in the environment before running."
        )
    return key


def query(
    run_context: "_rc.RunContext",
    ask: str,
    detail_level: str = "standard",
) -> CornerstoneRead:
    """One Cornerstone /context read.

    Args:
        run_context: AC-4 scope. `client_scope` MUST be non-empty (MC-6).
        ask: Natural-language query string.
        detail_level: "standard" | "full" (passed through to backend).

    Returns:
        CornerstoneRead. On connection error we retry once; on the second
        failure we return an empty read with the error captured in `errors`.
        On HTTP 4xx/5xx we capture the status + message in `errors` and
        return whatever partial payload (if any) was received.

    Raises:
        ValueError: if `client_scope` is empty (MC-6 violation at the edge)
            or if MEMORY_API_KEY is unset.
    """
    if not run_context.client_scope:
        raise ValueError("MC-6: client_scope is required")

    base_url = _resolve_base_url()
    api_key = _resolve_api_key()
    body = {
        "query": ask,
        "namespace": run_context.cornerstone_namespace,
        "detail_level": detail_level,
        "client_scope": run_context.client_scope,
    }
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    url = f"{base_url}/context"

    errors: list[str] = []
    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
                resp = client.post(url, json=body, headers=headers)
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            last_exc = e
            continue
        # Connected: do not retry on HTTP error, just record it.
        if resp.status_code >= 400:
            errors.append(
                f"cornerstone-http-{resp.status_code}: {resp.text[:200]!r}"
            )
            return CornerstoneRead(
                text="",
                items_retrieved=0,
                context_request_id=None,
                errors=errors,
            )
        try:
            data = resp.json()
        except Exception as e:
            errors.append(f"cornerstone-bad-json: {e}")
            return CornerstoneRead(
                text="",
                items_retrieved=0,
                context_request_id=None,
                errors=errors,
            )
        if not isinstance(data, dict):
            errors.append("cornerstone-unexpected-shape: top-level not an object")
            return CornerstoneRead(
                text="",
                items_retrieved=0,
                context_request_id=None,
                errors=errors,
            )
        return CornerstoneRead(
            text=str(data.get("text") or data.get("context") or ""),
            items_retrieved=int(data.get("items_retrieved") or data.get("count") or 0),
            context_request_id=data.get("context_request_id"),
            errors=errors,
        )

    # Both attempts failed at the network layer.
    errors.append(f"cornerstone-connect-failed: {last_exc!r}")
    return CornerstoneRead(
        text="",
        items_retrieved=0,
        context_request_id=None,
        errors=errors,
    )
