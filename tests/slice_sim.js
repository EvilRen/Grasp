// test-only: a Slice round on a virtual clock (nothing drawn) by a simulated child: each fruit is cut with probability p.hit x sqrt(r / 34 px) (decided once, when it
// nears its apex), a bomb is cut by accident with p.bomb, at most one cut per p.gap ms. Returns { t (s until the round ends), score, missed, bombsHit, spawned, lives0 }.
window.sliceSim = (o) => {
  o = Object.assign({ seed: 1, maxS: 300, fps: 50, hit: 0.7, bomb: 0.2, gap: 350 }, o || {});
  const realNow = performance.now, R = mulberry32(o.seed), t0 = realNow.call(performance), dt = 1000 / o.fps, rnd = Math.random;
  let vt = t0, last = -1e9; performance.now = () => vt; Math.random = R;
  if (o.first && typeof sliceRounds !== 'undefined') sliceRounds = 0; // (the session's first round)
  resetSlice(); const lives0 = slice.lives, seen = new WeakSet(), waves = [];
  try {
    while (vt - t0 < o.maxS * 1000 && !slice.over) {
      vt += dt; const n0 = slice.spawned;
      for (const f of slice.fruits.slice()) {
        if (vt < f.born || seen.has(f) || f.vy < -0.15) continue; seen.add(f);
        if (vt - last < o.gap) { if (R() < 0.5) seen.delete(f); continue; }
        if (R() < (f.bomb ? o.bomb : Math.min(0.92, o.hit * Math.sqrt(f.r / 34)))) { last = vt; slice.fruits.splice(slice.fruits.indexOf(f), 1); if (f.bomb) hitBomb(f, vt); else cutFruit(f, 1, 0, vt); if (slice.over) break; }
      }
      if (!slice.over) sliceTick(vt, dt);
      if (slice.spawned > n0) waves.push(slice.spawned - n0);
    }
  } finally { performance.now = realNow; Math.random = rnd; }
  const st = { t: Math.round((vt - t0) / 100) / 10, score: slice.score, missed: slice.missed, bombsHit: slice.bombsHit, spawned: slice.spawned, lives0, perWave: waves.length ? +(waves.reduce((a, b) => a + b, 0) / waves.length).toFixed(2) : 0, over: slice.over };
  const back = realNow.call(performance) - vt; slice.overAt += back; slice.nextSpawn += back; for (const f of slice.fruits) f.born += back; slice.combo.t += back; slice.flash += back;
  return st;
};
