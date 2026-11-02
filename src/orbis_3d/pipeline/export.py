"""Export the trained scene to a standard Gaussian Splat PLY.

The PLY is the interchange format: the web viewer, SuperSplat, and Blender
importers all read it. Nerfstudio's own viewer needs the full checkpoint, which
is far too heavy to ship to a browser.
"""

from pathlib import Path

from orbis_3d.config.defaults import TOOL_NS_EXPORT
from orbis_3d.errors import PipelineError
from orbis_3d.pipeline.workspace import Workspace
from orbis_3d.shell.run import require_tool, run

SPLAT_PATTERN = "*.ply"


def export_splat(workspace: Workspace) -> Path:
    require_tool(TOOL_NS_EXPORT)

    if not workspace.config_path.exists():
        raise PipelineError(
            f"Missing {workspace.config_path}. Train the workspace before exporting."
        )

    workspace.export_dir.mkdir(parents=True, exist_ok=True)
    command = [
        TOOL_NS_EXPORT,
        "gaussian-splat",
        "--load-config",
        str(workspace.config_path),
        "--output-dir",
        str(workspace.export_dir),
    ]
    run(command)
    return find_exported_splat(workspace.export_dir)


def find_exported_splat(export_dir: Path) -> Path:
    """Return the newest PLY under the export dir.

    The exporter has shipped as splat.ply and point_cloud.ply across Nerfstudio
    releases. Sorting by mtime instead of hardcoding a filename survives that and
    also picks the right file if an old export was left behind.
    """
    candidates = sorted(
        export_dir.rglob(SPLAT_PATTERN),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise PipelineError(
            f"ns-export finished but no {SPLAT_PATTERN} file appeared in {export_dir}. "
            "Check the exporter log above."
        )
    return candidates[0]
