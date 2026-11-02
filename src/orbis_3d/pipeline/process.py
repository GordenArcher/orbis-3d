"""Wrap ns-process-data, which extracts frames and runs COLMAP.

This stage is classical Structure-from-Motion, not learning. It produces the
camera intrinsics and poses that training needs, so it must succeed before any
GPU work can start.
"""

from pathlib import Path

from orbis_3d.config.defaults import DEFAULT_FRAMES_TARGET, TOOL_NS_PROCESS
from orbis_3d.errors import PipelineError
from orbis_3d.pipeline.workspace import Workspace
from orbis_3d.shell.run import require_tool, run

TRANSFORMS_FILENAME = "transforms.json"


def process_capture(
    workspace: Workspace,
    video: Path,
    frames_target: int = DEFAULT_FRAMES_TARGET,
) -> Path:
    """Extract frames and estimate camera poses into the workspace dataset dir.

    frames_target caps how many frames COLMAP has to match. A 60s walkaround can
    produce thousands of near duplicate frames, which multiplies matching time
    without adding viewpoints. 300 is a reasonable balance for a person scan.
    """
    require_tool(TOOL_NS_PROCESS)
    workspace.dataset_dir.mkdir(parents=True, exist_ok=True)

    command = [
        TOOL_NS_PROCESS,
        "video",
        "--data",
        str(video),
        "--output-dir",
        str(workspace.dataset_dir),
        "--num-frames-target",
        str(frames_target),
    ]
    run(command)

    transforms = workspace.dataset_dir / TRANSFORMS_FILENAME
    if not transforms.exists():
        # ns-process-data can exit zero after COLMAP fails to register enough
        # images, so the artifact check matters more than the return code.
        raise PipelineError(
            f"ns-process-data finished but {TRANSFORMS_FILENAME} is missing. "
            "COLMAP likely failed to register enough frames. Check the log above."
        )
    return workspace.dataset_dir
