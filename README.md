# orbis-3d

Reconstructs a 3D, rotatable model of a person from a single walkaround video using Structure-from-Motion (COLMAP) and 3D Gaussian Splatting.

**Status:** research / experimentation — early planning phase.

## What it does

Record a video walking around a person, and orbis-3d turns it into a 3D scene you can freely rotate around in a browser — no game-engine export, no fancy rig, just a phone video in and a viewable 3D reconstruction out.

## Pipeline

```
video (walkaround) 
    → frame extraction (ffmpeg) 
    → camera pose estimation (COLMAP, via ns-process-data) 
    → Gaussian Splatting training (Nerfstudio splatfacto) 
    → real-time viewer (ns-viewer / web splat viewer)
```

## Tech stack

- [Nerfstudio](https://github.com/nerfstudio-project/nerfstudio) — pipeline orchestration, COLMAP wrapper, splatfacto training, built-in viewer
- COLMAP — Structure-from-Motion / camera pose estimation
- 3D Gaussian Splatting (splatfacto) — scene reconstruction
- ffmpeg — video frame extraction
- Python

## Requirements

- NVIDIA GPU (CUDA) — splatting/training is GPU-bound
- Python 3.10+

## Project layout

```
orbis-3d/
├── capture/       # raw input videos/photo sets
├── processing/    # COLMAP output, processed camera poses, extracted frames
├── viewer/         # web viewer / export assets
├── notes/         # dev log — what worked, what didn't, lessons learned
└── README.md
```

## Roadmap

- [ ] Sanity-check capture (simple object/room) to validate pipeline end-to-end
- [ ] First full person capture + reconstruction
- [ ] Tune capture technique (lighting, overlap, frame rate) based on results
- [ ] Shareable web viewer for finished scans