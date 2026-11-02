#!/usr/bin/env bash
# Install the GPU pipeline in a fresh Colab runtime.
#
# Colab already ships a CUDA build of torch. Nerfstudio pulls torch as a
# dependency, and a mismatch between that wheel and the runtime's CUDA driver is
# the usual reason splatfacto fails with "no kernel image is available". Pin
# Nerfstudio and let it keep the existing torch when the version satisfies it.
#
# First run builds tinycudann from source and takes roughly 5 to 10 minutes.
set -euo pipefail

NERFSTUDIO_VERSION="${NERFSTUDIO_VERSION:-1.1.5}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT"

# ns-process-data shells out to ffmpeg for frame extraction. Colab images do not
# always include it, and the failure appears deep inside Nerfstudio otherwise.
if ! command -v ffmpeg >/dev/null 2>&1; then
  apt-get -qq update
  apt-get -qq install -y ffmpeg >/dev/null
fi

# ninja is required for the tinycudann build. Installing it first avoids a slow
# fallback to distutils that also tends to time out.
python -m pip install -q ninja

python -m pip install -q "nerfstudio==${NERFSTUDIO_VERSION}"

# Editable install so the notebook runs the checked out CLI, not a copy.
python -m pip install -q -e .

python - <<'PY'
import torch

print("torch", torch.__version__)
print("cuda available", torch.cuda.is_available())
if not torch.cuda.is_available():
    raise SystemExit("CUDA is not available. Runtime > Change runtime type > GPU, then rerun.")
PY
