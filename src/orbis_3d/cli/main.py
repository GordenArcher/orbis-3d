"""orbis CLI: validate a capture, run the pipeline, package and serve the scene.

Kept as plain argparse with no extra dependency because this runs inside a Colab
runtime where every added package risks disturbing the torch install.
"""

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from orbis_3d.capture.checks import inspect_capture
from orbis_3d.config.defaults import (
    DEFAULT_FRAMES_TARGET,
    DEFAULT_MAX_ITERATIONS,
    EXPORT_TOOLS,
    INSPECT_TOOLS,
    PROCESS_TOOLS,
    TRAIN_TOOLS,
    project_paths,
)
from orbis_3d.errors import OrbisError
from orbis_3d.pipeline.export import find_exported_splat
from orbis_3d.pipeline.run import run_pipeline
from orbis_3d.pipeline.share import build_share_bundle
from orbis_3d.pipeline.workspace import Workspace, default_workspace_name
from orbis_3d.shell.run import find_tool

EXIT_OK = 0
EXIT_FAILURE = 1


def _resolve_workspace(name: str | None, video: Path | None) -> Workspace:
    if name:
        return Workspace.under(project_paths().processing, name)
    if video is None:
        raise OrbisError("A workspace name is required when no video is given.")
    return Workspace.under(project_paths().processing, default_workspace_name(video))


def _print_report(report) -> None:
    print(f"Capture: {report.path}")
    if report.info is not None:
        info = report.info
        print(f"  duration:   {info.duration:.1f}s")
        print(f"  resolution: {info.width}x{info.height} (short edge {info.short_edge}px)")
        print(f"  fps:        {info.fps:.2f}" if info.fps else "  fps:        unknown")
        print(f"  codec:      {info.codec}")

    if report.problems:
        print("Problems:")
        for problem in report.problems:
            print(f"  - {problem}")
    if report.warnings:
        print("Warnings:")
        for warning in report.warnings:
            print(f"  - {warning}")
    if report.ok and not report.warnings:
        print("Capture looks good.")


def cmd_check(args: argparse.Namespace) -> int:
    report = inspect_capture(Path(args.video))
    _print_report(report)
    return EXIT_OK if report.ok else EXIT_FAILURE


def cmd_doctor(args: argparse.Namespace) -> int:
    print(f"Project root: {project_paths().root}")
    print(f"Python:       {sys.version.split()[0]}")
    groups = (
        ("inspection", INSPECT_TOOLS),
        ("processing", PROCESS_TOOLS),
        ("training", TRAIN_TOOLS),
        ("export", EXPORT_TOOLS),
    )
    missing = 0
    for label, tools in groups:
        print(f"{label}:")
        for tool in tools:
            path = find_tool(tool)
            if path is None:
                missing += 1
                print(f"  - {tool}: missing")
            else:
                print(f"  - {tool}: {path}")

    if missing:
        print(
            "\nMissing tools are expected on a recording machine. "
            "The GPU host needs all of them."
        )
    return EXIT_OK


def cmd_run(args: argparse.Namespace) -> int:
    video = Path(args.video).expanduser()
    report = inspect_capture(video)
    _print_report(report)
    if not report.ok:
        return EXIT_FAILURE

    workspace = _resolve_workspace(args.name, video)
    result = run_pipeline(
        video,
        workspace,
        max_iterations=args.max_iterations,
        frames_target=args.frames_target,
        skip_process=args.skip_process,
        skip_train=args.skip_train,
        skip_export=args.skip_export,
    )

    print("\nDone.")
    print(f"  config: {result.config_path}")
    print(f"  splat:  {result.ply_path}")
    print(f"  bundle: {result.share_zip}")
    print(f"  serve:  orbis serve --name {workspace.name}")
    return EXIT_OK


def cmd_package(args: argparse.Namespace) -> int:
    workspace = _resolve_workspace(args.name, None)
    ply = find_exported_splat(workspace.export_dir)
    zip_path = build_share_bundle(workspace, ply, project_paths().viewer)
    print(f"Bundle: {zip_path}")
    return EXIT_OK


def cmd_serve(args: argparse.Namespace) -> int:
    workspace = _resolve_workspace(args.name, None)
    if not (workspace.share_dir / "index.html").exists():
        raise OrbisError(
            f"No share bundle found in {workspace.share_dir}. "
            f"Run 'orbis run' or 'orbis package --name {workspace.name}' first."
        )

    # Replacing the process avoids a wrapper that has to forward Ctrl+C to a
    # child. The share dir is already the document root, so scene.ply resolves
    # relative to index.html.
    print(f"Serving {workspace.share_dir} on http://localhost:{args.port}")
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "http.server",
            str(args.port),
            "--directory",
            str(workspace.share_dir),
        ],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orbis",
        description="Turn a walkaround video into a 3D Gaussian Splat.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Validate a capture before spending GPU time.")
    check.add_argument("video", help="Path to the walkaround video.")
    check.set_defaults(handler=cmd_check)

    doctor = subparsers.add_parser("doctor", help="Show which pipeline tools are installed.")
    doctor.set_defaults(handler=cmd_doctor)

    run = subparsers.add_parser("run", help="Process, train, export, and package a capture.")
    run.add_argument("video", help="Path to the walkaround video.")
    run.add_argument("--name", help="Workspace name. Defaults to the video filename.")
    run.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help="Training iterations for splatfacto.",
    )
    run.add_argument(
        "--frames-target",
        type=int,
        default=DEFAULT_FRAMES_TARGET,
        help="Frame count to extract before COLMAP.",
    )
    run.add_argument("--skip-process", action="store_true", help="Reuse an existing dataset.")
    run.add_argument("--skip-train", action="store_true", help="Reuse an existing checkpoint.")
    run.add_argument("--skip-export", action="store_true", help="Reuse an existing PLY.")
    run.set_defaults(handler=cmd_run)

    package = subparsers.add_parser("package", help="Rebuild the share bundle from an export.")
    package.add_argument("--name", required=True, help="Workspace name.")
    package.set_defaults(handler=cmd_package)

    serve = subparsers.add_parser("serve", help="Serve a share bundle on localhost.")
    serve.add_argument("--name", required=True, help="Workspace name.")
    serve.add_argument("--port", type=int, default=8000, help="Port to listen on.")
    serve.set_defaults(handler=cmd_serve)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # Only expected failures become clean messages. A real bug keeps its
    # traceback, because hiding it would make pipeline work much harder.
    try:
        return args.handler(args)
    except OrbisError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
