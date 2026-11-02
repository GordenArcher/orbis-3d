"""Tests for workspace naming and paths.

The name is interpolated into directory and zip paths, so the validation tests
here are guarding against path traversal rather than style.
"""

import tempfile
import unittest
from pathlib import Path

from orbis_3d.errors import WorkspaceNameError
from orbis_3d.pipeline.workspace import (
    Workspace,
    default_workspace_name,
    validate_workspace_name,
)


class ValidateWorkspaceNameTests(unittest.TestCase):
    def test_accepts_plain_names(self):
        self.assertEqual(validate_workspace_name("chair"), "chair")
        self.assertEqual(validate_workspace_name("scan-01.a"), "scan-01.a")

    def test_rejects_traversal_and_separators(self):
        for name in ("../escape", "a/b", ".hidden", "", "has space"):
            with self.subTest(name=name):
                with self.assertRaises(WorkspaceNameError):
                    validate_workspace_name(name)

    def test_rejects_overlong_names(self):
        with self.assertRaises(WorkspaceNameError):
            validate_workspace_name("a" * 65)


class DefaultWorkspaceNameTests(unittest.TestCase):
    def test_slugifies_filename(self):
        self.assertEqual(default_workspace_name(Path("My Chair Scan.mp4")), "My-Chair-Scan")


class WorkspacePathTests(unittest.TestCase):
    def test_paths_are_derived_from_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Workspace.under(Path(tmp), "chair")

        self.assertEqual(workspace.dataset_dir, Path(tmp) / "chair" / "dataset")
        self.assertEqual(workspace.share_zip, Path(tmp) / "chair" / "chair-share.zip")
        self.assertEqual(
            workspace.config_path,
            Path(tmp) / "chair" / "outputs" / "orbis" / "splatfacto" / "run" / "config.yml",
        )


if __name__ == "__main__":
    unittest.main()
