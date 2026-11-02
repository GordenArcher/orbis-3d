"""Build a self contained folder that can be zipped and opened in a browser.

The bundle keeps the viewer assets and the PLY side by side with relative paths.
That means it works from a shared zip, a USB stick, or any static file host with
no path rewriting and no build step.
"""

import shutil
import zipfile
from pathlib import Path

from orbis_3d.config.defaults import SHARE_PLY_NAME
from orbis_3d.errors import PipelineError
from orbis_3d.pipeline.workspace import Workspace

VIEWER_ASSETS = ("index.html", "viewer.css", "viewer.js")

SHARE_NOTES = """orbis-3d scene bundle

scene.ply is the Gaussian Splat. index.html is a viewer that runs in the browser.

Option 1, serve this folder:
    python -m http.server 8000
    open http://localhost:8000

Option 2, drag and drop:
    Open index.html directly, then drag scene.ply onto the window.

A local server is needed for the automatic load because browsers block fetch()
on file:// URLs. Drag and drop works either way.
"""


def build_share_bundle(workspace: Workspace, ply: Path, viewer_dir: Path) -> Path:
    if not ply.exists():
        raise PipelineError(f"Cannot package a scene that does not exist: {ply}")

    for asset in VIEWER_ASSETS:
        if not (viewer_dir / asset).exists():
            raise PipelineError(f"Viewer asset missing: {viewer_dir / asset}")

    # Rebuild from scratch. A second export would otherwise leave stale files in
    # the bundle, and a stale viewer.js is very hard to spot when debugging.
    if workspace.share_dir.exists():
        shutil.rmtree(workspace.share_dir)
    workspace.share_dir.mkdir(parents=True)

    shutil.copy2(ply, workspace.share_dir / SHARE_PLY_NAME)
    for asset in VIEWER_ASSETS:
        shutil.copy2(viewer_dir / asset, workspace.share_dir / asset)
    (workspace.share_dir / "README.txt").write_text(SHARE_NOTES, encoding="utf-8")

    return zip_share_dir(workspace)


def zip_share_dir(workspace: Workspace) -> Path:
    """Zip the directory contents, not the directory itself.

    Unzipping then gives index.html at the top level, which is what people
    expect. Zipping the parent folder would bury everything one level down and
    break the relative scene.ply reference.
    """
    zip_path = workspace.share_zip
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(workspace.share_dir.rglob("*")):
            if file.is_file():
                archive.write(file, file.relative_to(workspace.share_dir))
    return zip_path
