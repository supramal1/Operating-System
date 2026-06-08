"""Scout v1 CLI entry point.

One run:
    1. Load brief + material from disk.
    2. Generate the decision brief via Claude Agent SDK (no tools).
    3. Structurally validate the output (raises if it fails the contract).
    4. Render the file with front-matter + canonical filename.
    5. Write the file to the outputs folder.
    6. Stop.

There is no step 7. Nothing consumes the output automatically. Mal's review IS
the next step.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from . import __version__
from .agent import generate_brief, load_output_spec, load_system_prompt
from .contracts import (
    BriefError,
    OutputContractError,
    parse_brief,
    validate_output,
)
from .langfuse_trace import ScoutTrace, get_langfuse_client
from .render import render_brief_file


DEFAULT_DRIVE_ROOT = (
    Path(__file__).resolve().parents[2] / "drive" / "Charlie Oscar AI Ops"
)
DEFAULT_SPECS_DIR = (
    Path.home()
    / "Desktop" / "Charlie-Oscar-OS-Prep" / "co-platform"
    / "agents" / "scout" / "doc-store" / "specs"
)
DEFAULT_MODEL = "claude-opus-4-7"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="scout",
        description=(
            "Scout v1: run one decision-brief task. Reads brief + material, "
            "writes a spec-compliant brief to the outputs folder, then stops."
        ),
    )
    p.add_argument(
        "--brief", required=True, type=Path,
        help="Path to the filled-in brief file (see 05-brief-template.md).",
    )
    p.add_argument(
        "--material", required=True, type=Path,
        help="Path to the material file Scout will digest.",
    )
    p.add_argument(
        "--drive-root", type=Path, default=DEFAULT_DRIVE_ROOT,
        help=(
            "Root of the Charlie Oscar AI Ops Drive folder. Defaults to the "
            "local 'drive/Charlie Oscar AI Ops' mirror in this project."
        ),
    )
    p.add_argument(
        "--specs-dir", type=Path, default=DEFAULT_SPECS_DIR,
        help="Directory containing system-prompt.md and output-spec.md.",
    )
    p.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Claude model id (default: {DEFAULT_MODEL}).",
    )
    return p.parse_args(argv)


def _outputs_dir(drive_root: Path) -> Path:
    return drive_root / "Agents" / "Scout" / "outputs"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    brief_text = args.brief.read_text(encoding="utf-8")
    try:
        brief = parse_brief(brief_text)
    except BriefError as e:
        print(f"[brief-contract] {e}", file=sys.stderr)
        return 2

    material_text = args.material.read_text(encoding="utf-8")
    system_prompt = load_system_prompt(args.specs_dir)
    output_spec = load_output_spec(args.specs_dir)

    outputs_dir = _outputs_dir(args.drive_root)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    langfuse = get_langfuse_client()

    with ScoutTrace(brief_id=brief.brief_id, langfuse=langfuse) as trace:
        with trace.span(
            "input_load",
            input={"brief_path": str(args.brief), "material_path": str(args.material)},
            metadata={"brief_chars": len(brief_text), "material_chars": len(material_text)},
        ) as s:
            s.update(output={"brief_id": brief.brief_id, "fields": list(brief.fields.keys())})

        with trace.generation(
            "scout_generate",
            model=args.model,
            input={"system_prompt_chars": len(system_prompt), "user_prompt_chars": len(brief_text) + len(material_text)},
            metadata={"tools": "disabled (allowed=[] + disallowed=builtins + deny callback)"},
        ) as gen:
            result = asyncio.run(generate_brief(
                brief_text=brief_text,
                material_text=material_text,
                system_prompt=system_prompt,
                output_spec_text=output_spec,
                model=args.model,
                cwd=args.drive_root,
            ))
            gen.update(output=result.text)

        with trace.span("validate", input={"chars": len(result.text)}) as s:
            try:
                validated = validate_output(result.text, expected_brief_id=brief.brief_id)
            except OutputContractError as e:
                s.update(level="ERROR", status_message=str(e))
                print(f"[output-contract] {e}", file=sys.stderr)
                print(
                    "Scout produced output but it failed structural validation. "
                    "Not writing to outputs. See Langfuse trace for full text.",
                    file=sys.stderr,
                )
                trace.record_output({"status": "rejected", "reason": str(e)})
                return 3
            s.update(output={"decisions": len(validated.footer["decisions"])})

        with trace.span("render") as s:
            rendered = render_brief_file(
                brief_id=brief.brief_id,
                brief_date=brief.fields["DATE"],
                scout_output=validated.text,
                model=args.model,
                agent_version=__version__,
                trace_id=trace.trace_id or "unknown",
            )
            s.update(output={"filename": rendered.filename})

        output_path = outputs_dir / rendered.filename
        with trace.span("file_write", input={"path": str(output_path)}) as s:
            output_path.write_text(rendered.content, encoding="utf-8")
            s.update(output={"bytes": output_path.stat().st_size})

        trace.record_output({
            "status": "ok",
            "output_path": str(output_path),
            "decisions": [
                {"name": d["name"], "tag": d["tag"]}
                for d in validated.footer["decisions"]
            ],
        })

    print(f"Wrote: {output_path}")
    print(f"Langfuse trace id: {trace.trace_id}")
    if trace.trace_url:
        print(f"Langfuse trace url: {trace.trace_url}")
    print("Scout stops here. Review the brief and the trace before anything counts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
