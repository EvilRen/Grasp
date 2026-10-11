// test-only: an Adventure walls stage played out on a virtual clock (nothing drawn) by a simulated player (panel fix: the Easy pacing measure).
// 'still': a still finger (the panel's toddler): returns every ball with a soft hit, serves with a medium flick; 'kid': returns 95%, a mix of
// soft / medium / hard (30 / 50 / 20%). Returns { t (s to clear, null if not), walls, hits, tiers, misses, lost }.
window.advSim = (o) => {
  o = Object.assign({ player: 'still', seed: 1, maxS: 400, fps: 50, noFail: true, react: 900 }, o || {});
  if (!adv.on || adv.phase !== 'play') return null;
  const realNow = performance.now, R = mulberry32(o.seed), t0 = realNow.call(performance), dt = 1000 / o.fps, still = o.player === 'still';
  const st = { player: o.player, n: adv.n, t: null, hits: 0, misses: 0, lost: 0, tiers: { soft: 0, medium: 0, hard: 0, super: 0 }, walls0: strike.cleared };
  let vt = t0; const lost0 = adv.lost; cursor.present = false; cursor.history.length = 0;
  const tier = () => { if (still) return 'soft'; const r = R(); return r < 0.3 ? 'soft' : r < 0.8 ? 'medium' : 'hard'; };
  performance.now = () => vt;
  try {
    while (vt - t0 < o.maxS * 1000) {
      vt += dt; if (!adv.on || adv.phase !== 'play' || strike.over) break;
      if (o.noFail && strike.lives < 2) strike.lives = 2;
      if (strike.waiting && vt - strike.waitSince > o.react) playerServe(still ? 'medium' : tier(), vt);
      const Zn = hitZone();
      for (const bl of strike.balls.slice()) {
        if (bl.dir < 0) { bl._sim = 0; continue; }
        if (bl._sim || bl.z - ballSpeedNow(bl, vt) * dt * 1.5 > Zn.zi) continue; bl._sim = 1;
        if (!still && R() >= 0.95) { st.misses++; continue; }
        const k = tier(); strikeHit(bl, vt, k, null); st.hits++; st.tiers[k]++;
      }
      strikeTick(vt, dt);
      if (o.trace && Math.floor((vt - t0) / 2000) !== st._tr) { st._tr = Math.floor((vt - t0) / 2000); (st.trace = st.trace || []).push([st._tr * 2, strike.walls.map(w => w.bricks.filter(k => k.alive).length + '@' + Math.round(w.z)).join(' '), strike.balls.map(b => Math.round(b.z) + (b.dir < 0 ? 'out' : 'in') + (b.wait ? 'W' : '')).join(' ')]); }
      if (strike.lastSmash && strike.lastSmash !== st._ls) { st._ls = strike.lastSmash; (st.smash = st.smash || []).push([Math.round((vt - t0) / 100) / 10, strike.lastSmash.tier, strike.lastSmash.n, strike.lastSmash.shape]); }
    }
  } finally { performance.now = realNow; }
  const done = adv.on && adv.result && adv.result.clear;
  st.t = done ? Math.round((vt - t0) / 100) / 10 : null; st.lost = adv.lost - lost0; st.walls = strike.cleared - st.walls0; st.left = strike.walls.length;
  delete st._ls; delete st._tr;
  const back = realNow.call(performance) - vt;
  for (const k of ['clearAt', 'cardAt']) if (isFinite(adv[k]) && adv[k]) adv[k] += back;
  for (const k of ['releaseUntil', 'serveAt', 'stopUntil', 'slowUntil', 'overAt', 'camPushAt', 'hotUntil', 'perfectAt', 'hitAt', 'handHit', 'flash', 'superFlash', 'tntAt', 'waitSince']) if (isFinite(strike[k]) && strike[k] > 0) strike[k] += back;
  for (const k of ['tierFlash', 'comboPop', 'speedPop', 'heartLost', 'meterPop', 'levelBanner']) { const u = strike.ui[k]; if (u && isFinite(u.t)) u.t += back; }
  if (adv.travel) adv.travel.t += back;
  return st;
};
