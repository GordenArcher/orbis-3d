import * as GaussianSplats3D from "https://cdn.jsdelivr.net/npm/@mkkellogg/gaussian-splats-3d@0.4.7/build/gaussian-splats-3d.module.js";

const DEFAULT_SCENE = "scene.ply";
const SUPPORTED_EXTENSIONS = new Set([".ply", ".splat", ".ksplat", ".spz"]);

// Zero alpha splats are invisible but still cost GPU time. The value is the
// library's usual default and only drops splats that contribute nothing.
const ALPHA_REMOVAL_THRESHOLD = 5;

const viewport = document.getElementById("viewport");
const status = document.getElementById("status");
const drop = document.getElementById("drop");
const input = document.getElementById("file");

// sharedMemoryForWorkers stays off on purpose: it requires cross origin
// isolation headers (COOP/COEP) that a plain static server does not send.
// Disabling it costs a little sorting speed and makes the bundle work anywhere,
// including a zip unzipped and served from anywhere with python -m http.server.
const viewer = new GaussianSplats3D.Viewer({
  rootElement: viewport,
  cameraUp: [0, -1, 0],
  initialCameraPosition: [0, 0, -3.5],
  initialCameraLookAt: [0, 0, 0],
  selfDrivenMode: true,
  useBuiltInControls: true,
  sharedMemoryForWorkers: false,
});

function setStatus(text) {
  status.textContent = text;
}

async function loadScene(source, label) {
  setStatus(`Loading ${label}...`);
  try {
    await viewer.addSplatScene(source, {
      splatAlphaRemovalThreshold: ALPHA_REMOVAL_THRESHOLD,
      // Progressive load shows something while the big PLY is still streaming
      // in, which matters because a person scan can be several hundred MB.
      progressiveLoad: true,
      showLoadingUI: false,
    });
    setStatus(`${label} loaded. Drop another file to replace it.`);
  } catch (error) {
    console.error(error);
    setStatus(`Could not load ${label}. Drop a splat file to try another.`);
    // The most common cause here is opening the page without scene.ply next to
    // it, so prompting for a file is more useful than an error text alone.
    if (label === DEFAULT_SCENE) {
      drop.classList.add("visible");
    }
  }
}

function extensionOf(name) {
  const dot = name.lastIndexOf(".");
  return dot === -1 ? "" : name.slice(dot).toLowerCase();
}

function loadLocalFile(file) {
  if (!SUPPORTED_EXTENSIONS.has(extensionOf(file.name))) {
    setStatus(`Unsupported file: ${file.name}`);
    return;
  }
  // Object URLs let the library fetch a picked File with no server involved.
  const url = URL.createObjectURL(file);
  loadScene(url, file.name);
}

input.addEventListener("change", () => {
  const file = input.files && input.files[0];
  if (file) loadLocalFile(file);
  input.value = "";
});

// Counting dragenter and dragleave keeps the overlay stable while the cursor
// moves across child elements inside the window.
let dragDepth = 0;

window.addEventListener("dragenter", (event) => {
  event.preventDefault();
  dragDepth += 1;
  drop.classList.add("visible");
});

window.addEventListener("dragover", (event) => {
  event.preventDefault();
});

window.addEventListener("dragleave", (event) => {
  event.preventDefault();
  dragDepth = Math.max(0, dragDepth - 1);
  if (dragDepth === 0) drop.classList.remove("visible");
});

window.addEventListener("drop", (event) => {
  event.preventDefault();
  dragDepth = 0;
  drop.classList.remove("visible");
  const file = event.dataTransfer && event.dataTransfer.files[0];
  if (file) loadLocalFile(file);
});

viewer.start();
loadScene(DEFAULT_SCENE, DEFAULT_SCENE);
