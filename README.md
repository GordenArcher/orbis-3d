# orbis-3d

Reconstructs a 3D, rotatable model of a person from a single walkaround video using
Structure-from-Motion (COLMAP) and 3D Gaussian Splatting.

**Status:** in development. The pipeline runs end to end, first milestone is a sanity check
capture of an object.

## What it does

Record a video walking around a subject, and orbis-3d turns it into a 3D scene you can
freely rotate in a browser. Phone video in, viewable splat out. No game engine export, no rig,
no manual cleanup.

## How it works

```
video (walkaround)
    -> frame extraction + camera poses (ns-process-data / COLMAP)
    -> Gaussian Splat training (nerfstudio splatfacto)
    -> PLY export (ns-export gaussian-splat)
    -> static browser viewer (viewer/)
```

Two stages, and only one of them learns anything:

| Stage | What happens | Needs a GPU |
| --- | --- | --- |
| Processing | Classical Structure-from-Motion recovers camera intrinsics and poses | Recommended, not required |
| Training | Gaussians are optimized against the posed frames for N iterations | Yes |

Training is **per-scene optimization**, not training a model on a dataset. There is no
pretrained checkpoint to download and no labelled data. splatfacto starts from random
Gaussians and fits them to the video, so every capture produces its own trained scene.

## Requirements

**Recording machine:** ffmpeg (for `orbis check`). No GPU needed.

**GPU host:** Linux with an NVIDIA GPU, or a Colab GPU runtime. Needs `colmap`, `ffmpeg`,
and Nerfstudio. Python 3.10 to 3.12 is the realistic range for the Nerfstudio/torch stack.

A free Colab T4 is enough for a 300 frame person scan at the default iteration count.

## Quick start

### Colab

1. Put the walkaround video in Google Drive.
2. Open `notebooks/orbis_train.ipynb` in Colab.
3. Set `Runtime > Change runtime type > T4 GPU`.
4. Edit the settings cell, then run all.

The notebook is a thin wrapper. It mounts Drive, installs the same code you run locally, calls
the `orbis` CLI, and downloads a share bundle.

### Local GPU host

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Then:

```bash
orbis check capture/chair.mp4
orbis run capture/chair.mp4 --name chair
```

Output lands in `processing/chair/`:

```
processing/chair/
├── dataset/          # extracted frames, COLMAP output, transforms.json
├── outputs/          # nerfstudio checkpoints and config.yml
├── export/           # splat PLY
└── share/            # scene.ply + viewer, self contained
```

The packaged bundle is `processing/chair/chair-share.zip`.

## Commands

```bash
orbis check <video>                  # validate duration, resolution, fps before GPU time
orbis doctor                         # print which pipeline tools are installed
orbis run <video> --name <name>      # process, train, export, package
orbis run <video> --name <name> --skip-process   # reuse dataset
orbis run <video> --name <name> --skip-train     # reuse checkpoint
orbis run <video> --name <name> --skip-export    # reuse PLY
orbis package --name <name>          # rebuild the share bundle from an existing export
orbis serve --name <name>            # serve the bundle on http://localhost:8000
```

Useful flags on `run`:

- `--frames-target 300` frames extracted before COLMAP. Raise it if the camera track is unstable.
- `--max-iterations 30000` splatfacto iterations. More detail, more GPU time.

## Viewing a scene

Unzip the bundle and serve it:

```bash
cd chair-share
python -m http.server 8000
```

Open http://localhost:8000. The viewer loads `scene.ply` automatically and accepts a dragged
`.ply`, `.splat`, `.ksplat`, or `.spz` file. It needs internet access for the three.js CDN.

Opening `index.html` directly also works if you drag `scene.ply` onto the window. Automatic
loading requires a server because browsers block `fetch()` on `file://` URLs.

## Project layout

```
orbis-3d/
├── capture/                 # raw input videos (gitignored)
├── processing/              # per capture workspaces (gitignored)
├── viewer/                  # static browser viewer, no build step
├── notebooks/               # thin Colab wrapper
├── scripts/                 # colab_setup.sh
├── src/orbis_3d/
│   ├── capture/             # ffprobe metadata + preflight checks
│   ├── config/              # paths and constants
│   ├── pipeline/            # process, train, export, package, orchestrate
│   ├── shell/               # subprocess wrapper and tool lookup
│   └── cli/                 # argparse entry point
├── tests/                   # stdlib unittest, no GPU required
├── notes/                   # dev log
├── Makefile
├── pyproject.toml
└── requirements.txt
```

## Tests

```bash
make test
```

Tests cover capture validation, workspace path construction, and the share bundle layout. They
run without ffmpeg or a GPU, so they work on the recording machine.

## Capture guidance

- Aim for 30 seconds or more, walking a full circle with overlap between viewpoints.
- Keep the subject still. Moving limbs break the assumption that the scene is static.
- Even, diffuse lighting. Hard shadows and reflective surfaces confuse COLMAP.
- 1080p minimum short edge. Higher resolution helps the splat, but raises training time.
- Fill the frame with the subject, but keep enough background for camera tracking.

## Roadmap

- [x] Project scaffold, CLI, Colab workflow, viewer
- [ ] Sanity check capture (simple object) to validate the pipeline end to end
- [ ] First full person capture and reconstruction
- [ ] Tune capture technique (lighting, overlap, frame rate) based on results
- [ ] Shareable web viewer for finished scans
