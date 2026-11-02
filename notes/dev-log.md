# orbis-3d/notes/dev-log.md
# Dev Log

Track decisions, what worked, and what didn't. Useful for the resume story later.

## Entries

- 2026-11-02: Pipeline scaffolded into a real CLI. Decided on per-capture workspaces under
  `processing/<name>/` so cleanup is one delete and the Colab handoff is one zip.
  Pinned `nerfstudio==1.1.5` because the torch, gsplat, and tinycudann versions are coupled.
  Fixed the `--timestamp run` flag on `ns-train` to make the config path deterministic instead
  of globbing for the newest run directory.
  Viewer is a static page using `@mkkellogg/gaussian-splats-3d` from a CDN with an import map,
  so there is no npm build step and the share bundle stays a zip of five files.
  Turned off `sharedMemoryForWorkers` in the viewer: it needs COOP/COEP headers that a plain
  `python -m http.server` does not send, and the sort speed cost is not worth requiring a
  custom server.
- YYYY-MM-DD: Project started. Chose Nerfstudio (COLMAP + splatfacto) pipeline over raw NeRF
  or classic mesh photogrammetry for quality + real-time rendering.
