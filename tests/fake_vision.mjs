export const FilesetResolver = { forVisionTasks: async () => ({}) };
// window.__handFor(delegate) returns one hand (21 landmarks), an array of hands (the camera games' two hands: [[...21], [...21]]) or null; the tracker
// returns at most numHands of them (createFromOptions / setOptions), as MediaPipe does. window.__created logs each tracker made (nh: numHands), window.__setOpts each setOptions.
export const HandLandmarker = { createFromOptions: async (fs, o) => {
  const d = o.baseOptions.delegate; let nh = o.numHands || 1;
  window.__created.push({ d, det: o.minHandDetectionConfidence, pres: o.minHandPresenceConfidence, trk: o.minTrackingConfidence, mode: o.runningMode, nh });
  return { detectForVideo(src, t) { window.__inputs.push((src.tagName || 'OFFSCREEN') + ':' + src.width + 'x' + src.height + ':' + d);
      const lm = window.__handFor ? window.__handFor(d) : null, all = !lm ? [] : Array.isArray(lm[0]) ? lm.filter(Boolean) : [lm];
      return { landmarks: all.slice(0, nh), handednesses: [] }; },
    setOptions(q) { (window.__setOpts = window.__setOpts || []).push(q); if (q && q.numHands) nh = q.numHands; return Promise.resolve(); },
    close() { window.__closed.push(d); } };
} };
