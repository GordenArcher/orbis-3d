"""Wrap ns-train for splatfacto.

This is the actual training step. Gaussian Splatting starts from random Gaussians
and optimizes them against the posed frames, so there is no pretrained checkpoint
to load. "Training" here means per scene optimization, not fitting a model to a
dataset once and reusing it.
"""

from collections.abc import Sequence
from pathlib import Path

from orbis_3d.config.defaults import (
    DEFAULT_EXPERIMENT,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_METHOD,
    DEFAULT_RUN_TIMESTAMP,
    TOOL_NS_TRAIN,
)
from orbis_3d.errors import PipelineError
from orbis_3d.pipeline.process import TRANSFORMS_FILENAME
from orbis_3d.pipeline.workspace import Workspace
from orbis_3d.shell.run import require_tool, run


def train_splatfacto(
    workspace: Workspace,
    *,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    extra_args: Sequence[str] = (),
) -> Path:
    require_tool(TOOL_NS_TRAIN)

    transforms = workspace.dataset_dir / TRANSFORMS_FILENAME
    if not transforms.exists():
        raise PipelineError(
            f"Missing {transforms}. Run the processing stage before training."
        )

    command = [
        TOOL_NS_TRAIN,
        DEFAULT_METHOD,
        "--data",
        str(workspace.dataset_dir),
        "--output-dir",
        str(workspace.outputs_dir),
        "--experiment-name",
        DEFAULT_EXPERIMENT,
        # Fixed timestamp keeps the config path predictable, see defaults.py.
        "--timestamp",
        DEFAULT_RUN_TIMESTAMP,
        "--max-num-iterations",
        str(max_iterations),
        # Without this the training process opens a viewer and never exits, which
        # hangs the notebook cell forever on a headless Colab runtime.
        "--viewer.quit-on-train-completion",
        "True",
        *extra_args,
    ]
    run(command)

    if not workspace.config_path.exists():
        raise PipelineError(
            f"Training finished but {workspace.config_path} is missing. "
            "The run may have been interrupted before the checkpoint was written."
        )
    return workspace.config_path
