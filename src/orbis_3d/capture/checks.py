"""Preflight checks before a capture is sent to the GPU.

A Colab session is billed by wall clock and a bad capture is only discovered
after frame extraction, COLMAP, and the first training steps. Everything here is
cheap to check locally, so the failures surface before the expensive part starts.
"""

from dataclasses import dataclass
from pathlib import Path

from orbis_3d.capture.probe import VideoInfo, probe_video
from orbis_3d.config.defaults import (
    MIN_CAPTURE_SECONDS,
    MIN_FPS,
    MIN_SHORT_EDGE_PX,
    RECOMMENDED_CAPTURE_SECONDS,
    VIDEO_EXTENSIONS,
)
from orbis_3d.errors import CaptureValidationError, OrbisError


@dataclass(frozen=True)
class CaptureReport:
    path: Path
    info: VideoInfo | None
    problems: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.problems


def inspect_capture(path: Path) -> CaptureReport:
    """Validate one video without raising, so the CLI can print every issue at once.

    Missing file and wrong extension return before ffprobe runs. That keeps the
    report useful on a machine where ffmpeg is not installed yet, which is the
    normal state of the Mac used to record captures.
    """
    path = path.expanduser()
    problems: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return CaptureReport(path, None, (f"File does not exist: {path}",), ())
    if not path.is_file():
        return CaptureReport(path, None, (f"Not a file: {path}",), ())
    if path.suffix.lower() not in VIDEO_EXTENSIONS:
        supported = ", ".join(sorted(VIDEO_EXTENSIONS))
        return CaptureReport(
            path,
            None,
            (f"Unsupported extension '{path.suffix}'. Expected one of: {supported}",),
            (),
        )
    if path.stat().st_size == 0:
        return CaptureReport(path, None, (f"File is empty: {path}",), ())

    try:
        info = probe_video(path)
    except OrbisError as exc:
        # Probe failures are reported, not raised, for the same reason: the user
        # should see the whole picture in one pass.
        return CaptureReport(path, None, (str(exc),), ())

    if info.duration < MIN_CAPTURE_SECONDS:
        problems.append(
            f"Capture is {info.duration:.1f}s, below the {MIN_CAPTURE_SECONDS:.0f}s minimum. "
            "COLMAP needs more frames to recover a stable camera track."
        )
    elif info.duration < RECOMMENDED_CAPTURE_SECONDS:
        warnings.append(
            f"Capture is {info.duration:.1f}s. Aim for {RECOMMENDED_CAPTURE_SECONDS:.0f}s or more "
            "so every side of the subject is covered."
        )

    if info.short_edge < MIN_SHORT_EDGE_PX:
        problems.append(
            f"Video short edge is {info.short_edge}px, below {MIN_SHORT_EDGE_PX}px. "
            "Low resolution frames produce noisy splats."
        )

    if info.fps and info.fps < MIN_FPS:
        warnings.append(
            f"Video is {info.fps:.1f} fps. Below {MIN_FPS:.0f} fps the walkaround can skip past "
            "viewpoints, which hurts camera matching."
        )

    return CaptureReport(path, info, tuple(problems), tuple(warnings))


def ensure_capture(path: Path) -> CaptureReport:
    report = inspect_capture(path)
    if not report.ok:
        raise CaptureValidationError("; ".join(report.problems))
    return report
