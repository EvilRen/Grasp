export const FilesetResolver = { forVisionTasks: async () => ({}) };
export const HandLandmarker = { createFromOptions: async (fs, o) => {
  const d = o.baseOptions.delegate;
  window.__created.push({ d, det: o.minHandDetectionConfidence, pres: o.minHandPresenceConfidence, trk: o.minTrackingConfidence, mode: o.runningMode });
  return { detectForVideo(src, t) { window.__inputs.push((src.tagName || 'OFFSCREEN') + ':' + src.width + 'x' + src.height + ':' + d);
      const lm = window.__handFor ? window.__handFor(d) : null; return { landmarks: lm ? [lm] : [], handednesses: [] }; },
    close() { window.__closed.push(d); } };
} };
