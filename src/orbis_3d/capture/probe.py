"""Read video metadata with ffprobe.

We call the ffprobe binary directly instead of depending on ffmpeg-python. The
pipeline only needs the metadata JSON, and every extra Python package is another
chance to collide with Nerfstudio's pinned torch stack on the GPU host.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from orbis_3d.config.defaults import TOOL_FFPROBE
from orbis_3d.errors import CaptureValidationError, PipelineError
from orbis_3d.shell.run import require_tool, run


@dataclass(frozen=True)
class VideoInfo:
    path: Path
    duration: float
    width: int
    height: int
    fps: float
    codec: str

    @property
    def short_edge(self) -> int:
        return min(self.width, self.height)


def _parse_rate(raw: str | None) -> float:
    # ffprobe reports frame rates as "30000/1001" style fractions. Some containers
    # report "0/0", which we treat as unknown rather than dividing by zero.
    if not raw or "/" not in raw:
        return 0.0
    numerator, _, denominator = raw.partition("/")
    try:
        divisor = float(denominator)
        if divisor == 0:
            return 0.0
        return float(numerator) / divisor
    except ValueError:
        return 0.0


def probe_video(path: Path) -> VideoInfo:
    require_tool(TOOL_FFPROBE)

    command = [
        TOOL_FFPROBE,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,avg_frame_rate,codec_name,duration:format=duration",
        "-of",
        "json",
        str(path),
    ]
    result = run(command, capture_output=True)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CaptureValidationError(f"ffprobe returned unreadable JSON for {path}") from exc

    streams = payload.get("streams") or []
    if not streams:
        raise CaptureValidationError(f"No video stream found in {path}")

    stream = streams[0]
    # Container level duration is the reliable one for mp4/mov. Stream level is
    # the fallback for webm and other formats where the container omits it.
    format_duration = (payload.get("format") or {}).get("duration")
    stream_duration = stream.get("duration")
    # ffprobe reports "N/A" for some containers instead of omitting the field, so
    # the float conversion has to tolerate non numeric values.
    try:
        duration = float(format_duration or stream_duration or 0.0)
    except (TypeError, ValueError):
        duration = 0.0

    try:
        width = int(stream.get("width") or 0)
        height = int(stream.get("height") or 0)
    except (TypeError, ValueError) as exc:
        raise CaptureValidationError(f"ffprobe returned non numeric dimensions for {path}") from exc

    if width == 0 or height == 0:
        raise CaptureValidationError(f"ffprobe could not read frame dimensions from {path}")
    if duration <= 0.0:
        raise PipelineError(f"ffprobe could not read a positive duration from {path}")

    return VideoInfo(
        path=path,
        duration=duration,
        width=width,
        height=height,
        fps=_parse_rate(stream.get("avg_frame_rate")),
        codec=str(stream.get("codec_name") or "unknown"),
    )
