"""Thin subprocess and tool lookup helpers.

Every pipeline wrapper funnels through run() so commands stay in list form.
shell=True would break the moment a capture path contains a space, and it hides
which binary actually failed when Nerfstudio's own wrappers crash.
"""

import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path

from orbis_3d.config.defaults import DEFAULT_TIMEOUT_SECONDS
from orbis_3d.errors import MissingToolError, PipelineError

# Only the tail matters when a command fails. Full Colab logs can be thousands
# of lines of progress bars, and dumping all of them buries the actual error.
ERROR_TAIL_CHARS = 2000


def find_tool(name: str) -> str | None:
    return shutil.which(name)


def require_tool(name: str) -> str:
    path = find_tool(name)
    if path is None:
        raise MissingToolError(
            f"Required tool '{name}' is not on PATH. Install it or run 'orbis doctor' to see what is missing."
        )
    return path


def run(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    capture_output: bool = False,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    """Run a command, streaming output unless the caller needs it captured.

    Streaming is the default because ns-train writes progress to the terminal and
    a silent ten minute cell in Colab looks like a hang. ffprobe is the opposite
    case: it needs its JSON captured, so callers opt in.
    """
    args = [str(part) for part in command]
    try:
        return subprocess.run(
            args,
            cwd=None if cwd is None else str(cwd),
            check=True,
            text=True,
            capture_output=capture_output,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise MissingToolError(f"Command not found: '{args[0]}'") from exc
    except subprocess.CalledProcessError as exc:
        detail = ""
        if capture_output and exc.stderr:
            detail = f"\n{exc.stderr.strip()[-ERROR_TAIL_CHARS:]}"
        raise PipelineError(
            f"Command failed with exit code {exc.returncode}: {' '.join(args)}{detail}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise PipelineError(
            f"Command timed out after {timeout}s: {' '.join(args)}"
        ) from exc
