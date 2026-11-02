"""Single source of truth for directory layout and pipeline constants.

The CLI, the pipeline, and the tests all import from here so they cannot drift
apart. Paths are derived from the project root instead of the current working
directory, which means `orbis run` behaves the same from any subfolder.
"""

import os
from dataclasses import dataclass
from pathlib import Path

# ORBIS_HOME exists for the Colab notebook: the repo is cloned into /content but
# artifacts should survive a runtime reset by landing on Drive. One env var is
# cheaper than threading an output root through every function.
HOME_ENV_VAR = "ORBIS_HOME"


def project_root() -> Path:
    override = os.environ.get(HOME_ENV_VAR)
    if override:
        return Path(override).expanduser().resolve()

    # This file lives at src/orbis_3d/config/defaults.py, so four parents up is
    # the repo root. An editable install keeps that layout. A wheel install does
    # not, which is exactly why ORBIS_HOME exists as an escape hatch.
    return Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @property
    def capture(self) -> Path:
        return self.root / "capture"

    @property
    def processing(self) -> Path:
        return self.root / "processing"

    @property
    def viewer(self) -> Path:
        return self.root / "viewer"


def project_paths() -> ProjectPaths:
    return ProjectPaths(root=project_root())


# splatfacto is the only method wired up on purpose. splatfacto-big needs more
# VRAM than a free Colab GPU reliably gives, and plain NeRF variants are far
# slower per iteration for a worse real time result.
DEFAULT_METHOD = "splatfacto"
DEFAULT_EXPERIMENT = "orbis"

# A fixed timestamp makes the config path deterministic. Nerfstudio's default is
# a timestamp string, which forces us to glob for the newest run every time.
DEFAULT_RUN_TIMESTAMP = "run"

DEFAULT_MAX_ITERATIONS = 30_000
DEFAULT_FRAMES_TARGET = 300

# Capture guidance, not hard failures. MIN_ values fail preflight because below
# them COLMAP cannot recover a usable camera track, so the GPU run is guaranteed
# waste. RECOMMENDED_ only warns.
MIN_CAPTURE_SECONDS = 8.0
RECOMMENDED_CAPTURE_SECONDS = 30.0
MIN_SHORT_EDGE_PX = 720
MIN_FPS = 24.0

VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"})

TOOL_FFMPEG = "ffmpeg"
TOOL_FFPROBE = "ffprobe"
TOOL_COLMAP = "colmap"
TOOL_NS_PROCESS = "ns-process-data"
TOOL_NS_TRAIN = "ns-train"
TOOL_NS_EXPORT = "ns-export"

INSPECT_TOOLS = (TOOL_FFPROBE,)
PROCESS_TOOLS = (TOOL_FFMPEG, TOOL_COLMAP, TOOL_NS_PROCESS)
TRAIN_TOOLS = (TOOL_NS_TRAIN,)
EXPORT_TOOLS = (TOOL_NS_EXPORT,)

DATASET_DIRNAME = "dataset"
OUTPUTS_DIRNAME = "outputs"
EXPORT_DIRNAME = "export"
SHARE_DIRNAME = "share"

SHARE_PLY_NAME = "scene.ply"
SHARE_ZIP_SUFFIX = "-share.zip"

# Three hours is generous for a 300 frame splatfacto run on a Colab T4. The
# timeout exists to stop a hung preflight from burning the whole session, not to
# cut a healthy run short.
DEFAULT_TIMEOUT_SECONDS = 3 * 60 * 60
