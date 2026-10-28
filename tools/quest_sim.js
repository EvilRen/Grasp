// Quest balance: a greedy bot plays 400 runs per hero and length with the rules in index.html (QC). node tools/quest_sim.js
const QC = (() => { const src = require('fs').readFileSync(require('path').join(__dirname, '..', 'index.html'), 'utf8'), i = src.indexOf('const QC = (() => {'), j = src.indexOf('})();', i) + 5; return new Function(src.slice(i, j) + '; return QC;')(); })();
function bot(run, f) { // greedy: play affordable cards, powers first, then attacks on the lowest-hp enemy; block when the hit coming is big
  let guard = 0;
  while (!f.over && guard++ < 40) {
    const inc = f.mons.filter((m) => m.hp > 0).reduce((s, m) => s + (m.intent || []).filter((x) => x[0] === 'atk').reduce((a, x) => a + (x[1] + m.st.str) * (x[2] || 1), 0), 0);
    const opts = f.hand.map((id, i) => ({ id, i, c: QC.cardOf(id) })).filter((o) => o.c.c <= f.en);
    if (!opts.length) break;
    const val = (o) => { let v = 0; for (const [k, n, x = 1] of o.c.fx) { if (k === 'dmg') v += n * x * (o.c.tg === 'all' ? f.mons.filter((m) => m.hp > 0).length : 1); if (k === 'blk') v += Math.min(n, Math.max(0, inc - f.blk)) * 1.1; if (k === 'blkdmg') v += f.blk; if (k === 'draw') v += 4 * n; if (k === 'en') v += 6 * n; if (k === 'poi') v += n * 1.5; if (k === 'weak' || k === 'vul') v += 3 * n; if (k === 'str') v += 5 * n; if (k === 'heal') v += run.hp < run.max * 0.7 ? n : 0; if (k[0] === 'p' || k === 'thorns') v += f.turn < 4 ? 14 : 4; } return v / Math.max(0.6, o.c.c); };
    opts.sort((a, b) => val(b) - val(a)); const o = opts[0]; if (val(o) <= 0.5) break;
    const live = f.mons.filter((m) => m.hp > 0).sort((a, b) => a.hp - b.hp); QC.play(run, f, o.i, live[0] ? live[0].i : 0);
  }
  QC.endTurn(run, f);
}
function sim(hero, len, seed) {
  const run = QC.newRun(hero, len, seed); let rooms = 0;
  while (!run.won && run.hp > 0 && rooms++ < 80) {
    const doors = run.doors, d = doors.includes('rest') && run.hp < run.max * 0.5 ? 'rest' : doors.includes('fight') ? 'fight' : doors[0];
    if (['fight', 'elite', 'boss'].includes(d)) { const f = QC.newFight(run, d); let t = 0; while (!f.over && t++ < 60) bot(run, f); if (f.over !== 'won') break; const w = QC.winFight(run, f); const c = w.cards.map((id) => QC.cardOf(id)).sort((a, b) => ({ r: 3, u: 2, c: 1 }[b.r] - { r: 3, u: 2, c: 1 }[a.r]))[0]; if (run.deck.length < 22) run.deck.push(c.id); }
    else if (d === 'rest') { if (run.hp < run.max * 0.7) QC.rest(run, 'heal'); else { const id = run.deck.find((x) => QC.upgradable(x) && QC.cardOf(x).r !== 's') || run.deck.find((x) => QC.upgradable(x)); QC.rest(run, 'up', id); } }
    else if (d === 'event') { const ev = QC.pick(run, QC.EVENTS); QC.doEvent(run, ev.id, 0) || QC.doEvent(run, ev.id, 1); }
    else if (d === 'chest') QC.relicFor(run);
    QC.nextRoom(run);
  }
  return { won: !!run.won, li: run.li, room: run.room, hp: run.hp };
}
for (const len of ['short', 'normal', 'epic']) for (const hero of ['knight', 'wizard', 'robot']) {
  let w = 0, land = [0, 0, 0, 0, 0]; const N = 400; for (let s = 1; s <= N; s++) { const r = sim(hero, len, s * 7919); if (r.won) w++; else land[r.li]++; }
  console.log(len.padEnd(7), hero.padEnd(7), 'win', (100 * w / N).toFixed(0) + '%', 'died in land', land.join('/'));
}
