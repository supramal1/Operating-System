"""Langfuse instrumentation for Scout (Langfuse Python SDK v4).

One trace per `brief_id`. Spans capture the reasoning steps the user reviews:
    - input_load     : reading brief + material from disk
    - scout_generate : the model call (generation span, with the model id)
    - validate       : structural validation of Scout's output
    - render         : building the final file body
    - file_write     : writing the markdown to the outputs folder

The user reviews traces in Langfuse as part of the gate. If you cannot find a
clean trace for a given brief_id, the run did not happen as the user expects.
That is a deliberate inversion: the trace IS the management surface.

v4 SDK note: child spans nest automatically via OpenTelemetry context propagation
when you use `start_as_current_observation`. Span names follow `<step>.scout` so
they are easy to filter in the UI.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

from langfuse import Langfuse


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


def get_langfuse_client() -> Langfuse:
    """Create the Langfuse client from env. Raises if keys are missing."""
    _load_env_from_dotenv()
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_HOST") or os.environ.get("LANGFUSE_BASE_URL")
    if not (public_key and secret_key and host):
        raise RuntimeError(
            "Langfuse env vars missing. Set LANGFUSE_PUBLIC_KEY, "
            "LANGFUSE_SECRET_KEY, LANGFUSE_HOST (see .env.example)."
        )
    return Langfuse(public_key=public_key, secret_key=secret_key, host=host)


class ScoutTrace:
    """One trace per Scout run, keyed by brief_id.

    Implemented on top of the v4 SDK's `start_as_current_observation` context
    manager. The root span's name becomes the trace name in the Langfuse UI.
    Child spans (`.span(...)`, `.generation(...)`) nest via OTel context.
    """

    def __init__(self, brief_id: str, langfuse: Langfuse) -> None:
        self.brief_id = brief_id
        self._langfuse = langfuse
        self.trace_id: str | None = None
        self.trace_url: str | None = None
        self._root_cm: Any = None
        self._root_span: Any = None

    def __enter__(self) -> "ScoutTrace":
        self._root_cm = self._langfuse.start_as_current_observation(
            as_type="span",
            name=f"scout/{self.brief_id}",
            input={"brief_id": self.brief_id},
            metadata={
                "agent": "Scout",
                "version": "0.1.0",
                "brief_id": self.brief_id,
            },
        )
        self._root_span = self._root_cm.__enter__()
        self.trace_id = self._langfuse.get_current_trace_id()
        if self.trace_id:
            self.trace_url = self._langfuse.get_trace_url(trace_id=self.trace_id)
        # Set trace-level IO so the brief_id is visible on the trace card.
        self._langfuse.set_current_trace_io(input={"brief_id": self.brief_id})
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc is not None:
                self._root_span.update(level="ERROR", status_message=str(exc))
            self._root_cm.__exit__(exc_type, exc, tb)
        finally:
            self._langfuse.flush()

    @contextmanager
    def span(
        self,
        name: str,
        *,
        input: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[Any]:
        """Open a child span. Use for non-LLM steps (load, validate, render, write)."""
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
        """Open a child generation span. Use for the model call itself."""
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
        """Attach the final brief output to the trace + root span for easy review."""
        self._root_span.update(output=output)
        self._langfuse.set_current_trace_io(output=output)
