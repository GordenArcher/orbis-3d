"""Tests for capture validation.

These run without ffmpeg on purpose: the checks that do not need ffprobe are the
ones most likely to regress, and they must keep working on a bare machine.
"""

import tempfile
import unittest
from pathlib import Path

from orbis_3d.capture.checks import inspect_capture


class InspectCaptureTests(unittest.TestCase):
    def test_missing_file_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = inspect_capture(Path(tmp) / "nope.mp4")

        self.assertFalse(report.ok)
        self.assertIn("does not exist", report.problems[0])

    def test_unsupported_extension_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "notes.txt"
            video.write_text("not a video")

            report = inspect_capture(video)

        self.assertFalse(report.ok)
        self.assertIn("Unsupported extension", report.problems[0])

    def test_empty_video_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "empty.mp4"
            video.touch()

            report = inspect_capture(video)

        self.assertFalse(report.ok)
        self.assertIn("empty", report.problems[0])


if __name__ == "__main__":
    unittest.main()
