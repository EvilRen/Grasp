// Stub MediaPipe: fingertip + palm oscillate vertically at window.__camHz with amplitude __camAmp (normalized)
export const FilesetResolver = { forVisionTasks: async () => ({}) };
export const HandLandmarker = { createFromOptions: async (fs, o) => ({
  detectForVideo(src, t) {
    if (window.__camNoHand) return { landmarks: [] };
    const s = Math.sin(2 * Math.PI * (window.__camHz || 4) * t / 1000) * (window.__camAmp || 0.005);
    const L = Array.from({ length: 21 }, () => ({ x: 0.5, y: 0.5 + s, z: 0 }));
    L[0] = { x: 0.5, y: 0.7 + s, z: 0 }; L[9] = { x: 0.5, y: 0.5 + s, z: 0 }; L[8] = { x: 0.52, y: 0.3 + s, z: 0 };
    return { landmarks: [L] };
  }, close() {} }) };
