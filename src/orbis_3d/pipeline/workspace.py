"""Per capture directory layout.

One folder per capture under processing/ keeps the dataset, training logs,
export, and share bundle together. Cleanup is then a single rm, and the Colab
handoff is a single zip instead of four unrelated paths.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from orbis_3d.config.defaults import (
    DATASET_DIRNAME,
    DEFAULT_EXPERIMENT,
    DEFAULT_METHOD,
    DEFAULT_RUN_TIMESTAMP,
    EXPORT_DIRNAME,
    OUTPUTS_DIRNAME,
    SHARE_DIRNAME,
    SHARE_ZIP_SUFFIX,
)
from orbis_3d.errors import WorkspaceNameError

# The name becomes a directory name, so anything with a slash or a leading dot
# has to be rejected. This is a whitelist rather than a blacklist because the
# name is also used in zip file names that users open on other machines.
WORKSPACE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
MAX_WORKSPACE_NAME_LENGTH = 64
SLUG_SEPARATOR = "-"
SLUG_FALLBACK = "capture"


def validate_workspace_name(name: str) -> str:
    if len(name) > MAX_WORKSPACE_NAME_LENGTH:
        raise WorkspaceNameError(
            f"Workspace name is {len(name)} characters, limit is {MAX_WORKSPACE_NAME_LENGTH}."
        )
    if not WORKSPACE_NAME_PATTERN.fullmatch(name):
        raise WorkspaceNameError(
            f"Invalid workspace name '{name}'. Use letters, numbers, dot, dash, underscore, "
            "and start with a letter or number."
        )
    return name


def default_workspace_name(video: Path) -> str:
    """Derive a name from the video filename so --name stays optional."""
    slug = re.sub(r"[^a-zA-Z0-9._-]+", SLUG_SEPARATOR, video.stem).strip(SLUG_SEPARATOR)
    # Stripping can leave a leading dot or dash, which the whitelist rejects.
    slug = slug.lstrip("._-")
    return slug[:MAX_WORKSPACE_NAME_LENGTH] or SLUG_FALLBACK


@dataclass(frozen=True)
class Workspace:
    name: str
    root: Path

    @classmethod
    def under(cls, processing_dir: Path, name: str) -> "Workspace":
        return cls(name=validate_workspace_name(name), root=processing_dir / name)

    @property
    def dataset_dir(self) -> Path:
        return self.root / DATASET_DIRNAME

    @property
    def outputs_dir(self) -> Path:
        return self.root / OUTPUTS_DIRNAME

    @property
    def export_dir(self) -> Path:
        return self.root / EXPORT_DIRNAME

    @property
    def share_dir(self) -> Path:
        return self.root / SHARE_DIRNAME

    @property
    def share_zip(self) -> Path:
        return self.root / f"{self.name}{SHARE_ZIP_SUFFIX}"

    @property
    def config_path(self) -> Path:
        return (
            self.outputs_dir
            / DEFAULT_EXPERIMENT
            / DEFAULT_METHOD
            / DEFAULT_RUN_TIMESTAMP
            / "config.yml"
        )

    def create(self) -> None:
        for directory in (self.dataset_dir, self.outputs_dir, self.export_dir, self.share_dir):
            directory.mkdir(parents=True, exist_ok=True)
