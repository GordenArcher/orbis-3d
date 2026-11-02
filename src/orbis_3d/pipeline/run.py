"""End to end orchestration shared by the CLI and the Colab notebook.

The sequence lives here instead of in the notebook so a local run and a Colab run
execute exactly the same code path. The notebook only decides where files come
from and where the zip goes.
"""

import time
from dataclasses import dataclass
from pathlib import Path

from orbis_3d.config.defaults import DEFAULT_FRAMES_TARGET, DEFAULT_MAX_ITERATIONS, project_paths
from orbis_3d.errors import PipelineError
from orbis_3d.pipeline.export import SPLAT_PATTERN, export_splat
from orbis_3d.pipeline.process import TRANSFORMS_FILENAME, process_capture
from orbis_3d.pipeline.share import build_share_bundle
from orbis_3d.pipeline.train import train_splatfacto
from orbis_3d.pipeline.workspace import Workspace


@dataclass(frozen=True)
class RunResult:
    workspace: Workspace
    config_path: Path
    ply_path: Path
    share_zip: Path


def _log(message: str) -> None:
    # Flush matters in Colab: without it the step header can appear only after
    # the long command it was announcing has already finished.
    print(message, flush=True)


def _step(label: str, started: float) -> None:
    _log(f"[orbis] {label} finished in {time.monotonic() - started:.1f}s")


def run_pipeline(
    video: Path,
    workspace: Workspace,
    *,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    frames_target: int = DEFAULT_FRAMES_TARGET,
    skip_process: bool = False,
    skip_train: bool = False,
    skip_export: bool = False,
    viewer_dir: Path | None = None,
) -> RunResult:
    """Run processing, training, export, and packaging in order.

    Skip flags are for iterating on one stage without redoing the expensive ones.
    When a stage is skipped its output is still verified, because a silent fall
    through to an empty export wastes more time than a clear error here.
    """
    workspace.create()
    resolved_viewer_dir = viewer_dir or project_paths().viewer

    if skip_process:
        transforms = workspace.dataset_dir / TRANSFORMS_FILENAME
        if not transforms.exists():
            raise PipelineError(f"Cannot skip processing: {transforms} does not exist.")
        _log(f"[orbis] skipping processing, reusing {workspace.dataset_dir}")
    else:
        _log(f"[orbis] processing {video.name} with COLMAP")
        started = time.monotonic()
        process_capture(workspace, video, frames_target=frames_target)
        _step("processing", started)

    if skip_train:
        if not workspace.config_path.exists():
            raise PipelineError(
                f"Cannot skip training: {workspace.config_path} does not exist."
            )
        _log(f"[orbis] skipping training, reusing {workspace.config_path}")
    else:
        _log(f"[orbis] training {workspace.name} for {max_iterations} iterations")
        started = time.monotonic()
        train_splatfacto(workspace, max_iterations=max_iterations)
        _step("training", started)

    if skip_export:
        existing = sorted(
            workspace.export_dir.rglob(SPLAT_PATTERN),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not existing:
            raise PipelineError(
                f"Cannot skip export: no {SPLAT_PATTERN} under {workspace.export_dir}."
            )
        ply_path = existing[0]
        _log(f"[orbis] skipping export, reusing {ply_path}")
    else:
        _log("[orbis] exporting Gaussian Splat PLY")
        started = time.monotonic()
        ply_path = export_splat(workspace)
        _step("export", started)

    _log("[orbis] packaging share bundle")
    started = time.monotonic()
    share_zip = build_share_bundle(workspace, ply_path, resolved_viewer_dir)
    _step("packaging", started)

    return RunResult(
        workspace=workspace,
        config_path=workspace.config_path,
        ply_path=ply_path,
        share_zip=share_zip,
    )
