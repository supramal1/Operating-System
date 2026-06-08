"""Langfuse instrumentation for Lookout (Langfuse Python SDK v4).

One trace per `run_id`. Spans capture the steps reviewers actually look at:
    - input_load        : composing the run-context
    - calendar_pull     : the Google Calendar read
    - cornerstone_pull  : the Cornerstone HTTP read
    - drive_delta       : the drive_sweep delta read
    - lookout_generate  : the model call (generation span)
    - validate          : structural validation of Lookout's output
    - render            : building the final file body
    - file_write        : writing the markdown to the outputs folder

If `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` are unset, EVERY span /
generation call here is a NO-OP. Lookout still runs; nothing is sent. This
mirrors Scout's pattern — Langfuse is optional infra, not a hard dep at
runtime.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator


def _load_env_from_dotenv() -> None:
    """Minimal .env loader so users do not need a `python-dotenv` dependency.

    Only sets vars that are not already in the environment. Silently no-ops if
    the .env file is absent.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        candidate = os.path.join(here, ".env")
        if os.path.isfile(candidate):
            with open(candidate, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ.setdefault(key, value)
            return
        parent = os.path.dirname(here)
        if parent == here:
            return
        here = parent


def _langfuse_configured() -> bool:
    return bool(
        os.environ.get("LANGFUSE_PUBLIC_KEY")
        and os.environ.get("LANGFUSE_SECRET_KEY")
    )


def get_langfuse_client() -> Any | None:
    """Return a configured Langfuse client, or None if env keys are unset.

    No-op posture: callers should treat None as "no observability this run"
    and continue. Lookout must run even without Langfuse.
    """
    _load_env_from_dotenv()
    if not _langfuse_configured():
        return None
    try:
        from langfuse import Langfuse
    except ImportError:
        return None
    host = os.environ.get("LANGFUSE_HOST") or os.environ.get("LANGFUSE_BASE_URL")
    return Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        host=host,
    )


class _NoopSpan:
    """Stand-in for a Langfuse span when Langfuse is unconfigured."""

    def update(self, **_: Any) -> None:
        return None


class LookoutTrace:
    """One trace per Lookout run, keyed by run_id.

    Implemented on top of the v4 SDK's `start_as_current_observation` context
    manager when Langfuse is configured. When it isn't, every method here is
    a no-op and `trace_id` stays None.
    """

    SPAN_NAMES = (
        "input_load",
        "calendar_pull",
        "cornerstone_pull",
        "drive_delta",
        "lookout_generate",
        "validate",
        "render",
        "file_write",
    )

    def __init__(self, run_id: str, langfuse: Any | None) -> None:
        self.run_id = run_id
        self._langfuse = langfuse
        self.trace_id: str | None = None
        self.trace_url: str | None = None
        self._root_cm: Any = None
        self._root_span: Any = None

    def __enter__(self) -> "LookoutTrace":
        if self._langfuse is None:
            return self
        self._root_cm = self._langfuse.start_as_current_observation(
            as_type="span",
            name=f"lookout/{self.run_id}",
            input={"run_id": self.run_id},
            metadata={
                "agent": "Lookout",
                "version": "0.1.0",
                "run_id": self.run_id,
            },
        )
        self._root_span = self._root_cm.__enter__()
        self.trace_id = self._langfuse.get_current_trace_id()
        if self.trace_id:
            self.trace_url = self._langfuse.get_trace_url(trace_id=self.trace_id)
        self._langfuse.set_current_trace_io(input={"run_id": self.run_id})
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._langfuse is None:
            return None
        try:
            if exc is not None and self._root_span is not None:
                self._root_span.update(level="ERROR", status_message=str(exc))
            if self._root_cm is not None:
                self._root_cm.__exit__(exc_type, exc, tb)
        finally:
            try:
                self._langfuse.flush()
            except Exception:
                pass
        return None

    @contextmanager
    def span(
        self,
        name: str,
        *,
        input: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[Any]:
        """Open a child span. No-op when Langfuse is unconfigured."""
        if self._langfuse is None:
            yield _NoopSpan()
            return
        with self._langfuse.start_as_current_observation(
            as_type="span",
            name=name,
            input=input,
            metadata=metadata or {},
        ) as s:
            try:
                yield s
            except Exception as e:
                s.update(level="ERROR", status_message=str(e))
                raise

    @contextmanager
    def generation(
        self,
        name: str,
        *,
        model: str,
        input: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[Any]:
        """Open a child generation span. No-op when Langfuse is unconfigured."""
        if self._langfuse is None:
            yield _NoopSpan()
            return
        with self._langfuse.start_as_current_observation(
            as_type="generation",
            name=name,
            model=model,
            input=input,
            metadata=metadata or {},
        ) as g:
            try:
                yield g
            except Exception as e:
                g.update(level="ERROR", status_message=str(e))
                raise

    def record_output(self, output: Any) -> None:
        """Attach the final brief output to the trace + root span. No-op if unconfigured."""
        if self._langfuse is None or self._root_span is None:
            return
        self._root_span.update(output=output)
        self._langfuse.set_current_trace_io(output=output)
