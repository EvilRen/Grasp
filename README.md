# Grasp

Hand-gesture physics sandbox in one self-contained HTML file (`index.html`).
Your webcam is the controller: **pinch** to grab, **release** to throw, **point** to poke.
Mouse/touch fallback when the camera or tracker is unavailable.

- Physics: Matter.js 0.20.0 (cdnjs)
- Hand tracking: MediaPipe Tasks Vision HandLandmarker 0.10.35 (jsDelivr), VIDEO mode, 1 hand
- All tuning constants live in `CONFIG` at the top of the script
- Press **D** (or the HUD button) for live diagnostics

## Hosting

Camera mode does not work inside claude.ai artifacts (the iframe blocks the camera and
the CSP blocks the model/WASM). It is deployed as a static site on Vercel, project `grasp`.
