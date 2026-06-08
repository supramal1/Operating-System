"""Lookout drive delta source — thin wrapper around the existing drive_sweep.

This module IMPORTS `sweep` from `platform.library.scripts.drive_sweep` and
calls it with LOOKOUT-OWNED paths. It does NOT mutate or wrap any sweep
internals.

IMPORTANT: we pass a LOOKOUT-OWNED `library_root` (under
`run_context.state_dir`), NEVER `co-platform/platform/library/`. The
stewardship sweep owns that root; sharing would race per the librarian's
warning. Lookout's mirror is its own sandbox.

READ-ONLY CONTRACT: `sweep` itself is operator-driven and read-from-Drive;
this wrapper does not add any write capability. It only consumes the
`delta.json` artifact `sweep` produces.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .. import run_context as _rc


_PLATFORM_LIBRARY_SCRIPTS = (
    Path.home()
    / "Desktop/Charlie-Oscar-OS-Prep/co-platform/platform/library/scripts"
)


def _load_sweep() -> Callable[..., int] | None:
    """Import `sweep` from drive_sweep without making the platform a package.

    The platform library scripts dir is not on PYTHONPATH and not a python
    package (no __init__.py). We load it directly from its file path.
    """
    try:
        # Preferred path: it IS importable as a module if PYTHONPATH includes it.
        from platform.library.scripts.drive_sweep import sweep  # type: ignore
        return sweep
    except Exception:
        pass
    script_path = _PLATFORM_LIBRARY_SCRIPTS / "drive_sweep.py"
    if not script_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("co_drive_sweep", script_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    # Make the script's local sibling modules importable if it has any.
    sys.modules["co_drive_sweep"] = module
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"[lookout/drive_delta] could not load drive_sweep: {e}", file=sys.stderr)
        return None
    return getattr(module, "sweep", None)


@dataclass(frozen=True)
class DriveDeltaRead:
    added: list[dict[str, Any]]
    modified: list[dict[str, Any]]
    removed: list[dict[str, Any]]
    unchanged_count: int
    errors: list[str] = field(default_factory=list)


_EMPTY = DriveDeltaRead(added=[], modified=[], removed=[], unchanged_count=0)


def _read_delta_file(delta_path: Path) -> dict[str, Any] | None:
    if not delta_path.exists():
        return None
    try:
        return json.loads(delta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def fetch_delta(run_context: "_rc.RunContext") -> DriveDeltaRead:
    """Run a drive sweep against the lookout-owned library mirror and read
    the resulting delta.json.

    Lookout's state layout (under run_context.state_dir):
        library-mirror/        -- the sweep writes library-tagged docs here
        coverage-index.json    -- the sweep's coverage index
        delta.json             -- the sweep's delta vs the previous coverage

    On ANY failure (sweep raises, import fails, delta unreadable) we return an
    empty DriveDeltaRead with the error captured in `errors`. Lookout still
    runs and the gap surfaces in the brief.
    """
    state_dir = run_context.state_dir
    library_mirror = state_dir / "library-mirror"
    coverage_index_path = state_dir / "coverage-index.json"
    delta_path = state_dir / "delta.json"

    errors: list[str] = []

    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        library_mirror.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        errors.append(f"drive-delta-state-mkdir-failed: {e}")
        return DriveDeltaRead(
            added=[], modified=[], removed=[], unchanged_count=0, errors=errors,
        )

    sweep = _load_sweep()
    if sweep is None:
        errors.append(
            "drive-delta-sweep-unavailable: could not import "
            "platform.library.scripts.drive_sweep.sweep"
        )
        return DriveDeltaRead(
            added=[], modified=[], removed=[], unchanged_count=0, errors=errors,
        )

    try:
        rc = sweep(
            library_root=library_mirror,
            root_folder_id=run_context.drive_root_folder_id,
            coverage_index_path=coverage_index_path,
            delta_path=delta_path,
            dry_run=False,
            run_check=False,
        )
    except Exception as e:
        errors.append(f"drive-delta-sweep-raised: {e}")
        return DriveDeltaRead(
            added=[], modified=[], removed=[], unchanged_count=0, errors=errors,
        )

    if rc != 0:
        errors.append(f"drive-delta-sweep-exit-{rc}")

    payload = _read_delta_file(delta_path)
    if payload is None:
        errors.append(f"drive-delta-no-delta-file: {delta_path}")
        return DriveDeltaRead(
            added=[], modified=[], removed=[], unchanged_count=0, errors=errors,
        )

    return DriveDeltaRead(
        added=list(payload.get("added") or []),
        modified=list(payload.get("modified") or []),
        removed=list(payload.get("removed") or []),
        unchanged_count=int(payload.get("unchanged_count") or 0),
        errors=errors,
    )
