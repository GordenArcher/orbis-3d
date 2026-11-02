"""Tests for the share bundle.

The bundle is the only artifact a user actually opens, so the zip layout is
asserted rather than assumed: index.html must be at the top level or the relative
scene.ply reference breaks.
"""

import tempfile
import unittest
import zipfile
from pathlib import Path

from orbis_3d.pipeline.share import build_share_bundle
from orbis_3d.pipeline.workspace import Workspace


def make_viewer(directory: Path) -> None:
    (directory / "index.html").write_text("<html></html>")
    (directory / "viewer.css").write_text("body { margin: 0; }")
    (directory / "viewer.js").write_text("console.error('viewer');")


class BuildShareBundleTests(unittest.TestCase):
    def test_zip_has_flat_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            viewer = root / "viewer"
            viewer.mkdir()
            make_viewer(viewer)

            workspace = Workspace.under(root / "processing", "chair")
            workspace.create()

            source_ply = root / "splat.ply"
            source_ply.write_bytes(b"ply")

            zip_path = build_share_bundle(workspace, source_ply, viewer)

            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())

        self.assertEqual(
            names, {"index.html", "scene.ply", "viewer.css", "viewer.js", "README.txt"}
        )

    def test_rebuild_replaces_stale_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            viewer = root / "viewer"
            viewer.mkdir()
            make_viewer(viewer)

            workspace = Workspace.under(root / "processing", "chair")
            workspace.create()
            workspace.share_dir.mkdir(parents=True, exist_ok=True)
            (workspace.share_dir / "stale.txt").write_text("old")

            source_ply = root / "splat.ply"
            source_ply.write_bytes(b"ply")

            build_share_bundle(workspace, source_ply, viewer)

        self.assertFalse((workspace.share_dir / "stale.txt").exists())


if __name__ == "__main__":
    unittest.main()
