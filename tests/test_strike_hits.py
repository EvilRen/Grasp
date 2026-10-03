exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Strike fairness fixes (reported from a real phone): (1) the ball touching the drawn hand (its fingers reach well above the cursor point) is a
# hit, and a ball clearly beside the hand still misses; (2) the ball threads a hole / gap untouched only when it really fits; a gap narrower than
# the ball is a normal hit. Also: the 3D renderer draws the bricks / holes at the logic's cells.
S = "__grasp.strike"
FRAMES = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
REACH = f"((b) => {{ const sc = ballScreen(b), reach = Math.max(sc.r * sd('STRIKE_HIT_RADIUS'), sd('STRIKE_HIT_NEAR') * strikeScale()) * reachMul() * strikeTuning().reach; return {{ sc, reach, d: pathDist(sc.x, sc.y, performance.now(), 160) }}; }})"

async def open_page(b, w, h, gfx=None):
    ctx = await b.new_context(viewport={'width': w, 'height': h}); page = await ctx.new_page(); errs = []
    await routes(page); page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + (f"window.__graspGfx = {gfx};" if gfx else ''))
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
    await page.evaluate("__grasp.setPlayerLevel(20)")  # the road unlocks everything (these suites test the run arc, not the meta gate)
    await page.evaluate(f"{S}.extrasOff = true; {S}.guestEvery = 0; __grasp.CONFIG.STRIKE_PU_RATE = 0; __grasp.CONFIG.STRIKE_MAGNET = 0")
    await page.click('#mouseBtn'); await page.click('.modes button[data-mode=strike]'); await page.click('#advEndless')
    await page.wait_for_function(f"gameMode === 'strike' && {S}.ball", timeout=10000)
    return ctx, page, errs

async def park(page):  # no serve coming, the ball out of the way, walls cleared
    await page.evaluate(f"(() => {{ const s = {S}; s.serveAt = performance.now() + 1e9; s.walls.length = 0; s.setBallZ(2300, 30, 30); s.ball.speed = 0; }})()")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        # ===== phone-sized screen (360 x 740): small ball, big Easy hand =====
        ctx, page, errs = await open_page(b, 360, 740)
        await park(page); await page.mouse.move(180, 600); await page.wait_for_timeout(250)
        hs = await page.evaluate(f"(() => {{ const h = {S}.handShape(); return {{ x: h.x, y: h.y, scale: h.scale, palm: h.palm, fingers: h.fingers, inPalm: h.dist(h.x, h.y + 10), tip: h.dist(h.fingers[1].x1, h.fingers[1].y1 - h.fingers[1].r), far: h.dist(h.x + 200, h.y) }}; }})()")
        top = min(f['y1'] - f['r'] for f in hs['fingers'])
        check(f"strike.handShape(): the drawn hand (x{hs['scale']} on Easy) = palm + 4 fingers + thumb; fingertips {hs['y'] - top:.0f} px above the cursor point", hs['scale'] == 1.6 and hs['inPalm'] < 0 and abs(hs['tip']) < 1 and hs['far'] > 100 and len(hs['fingers']) == 5 and hs['y'] - top > 100, hs)
        # (1) the ball's circle touches the middle fingertip; its centre is beyond the old reach circle -> still a hit
        t = await page.evaluate(f"""(() => {{ const s = {S}, z = __grasp.CONFIG.STRIKE_HIT_Z, h = s.handShape(), f = h.fingers[1];
          s.setBallZ(z, f.x1, f.y1 - 40); s.ball.speed = 0; const r = s.ballScreen().r; s.setBallZ(z, f.x1, f.y1 - f.r - r * 0.6); s.ball.speed = 0;
          cursor.history.length = 0; cursor.history.push({{ t: performance.now(), x: h.x, y: h.y }}); s.serveAt = performance.now() + 1e9;
          const q = {REACH}(s.ball); return {{ r, d: q.d, reach: q.reach, shape: h.dist(q.sc.x, q.sc.y), hits: s.hits }}; }})()""")
        await page.evaluate(f"{S}.ball.speed = __grasp.strike.pace"); await page.wait_for_function(f"{S}.hits > {t['hits']} || !{S}.ball || {S}.misses > 0", timeout=8000)
        h1 = await page.evaluate(f"({{ hits: {S}.hits, dir: {S}.ball ? {S}.ball.dir : 0, misses: {S}.misses }})")
        check(f"ball touching the drawn fingertips (centre {t['d']:.0f} px from the cursor, beyond the reach circle {t['reach']:.0f}; {t['shape'] - t['r']:.0f} px overlap) -> a hit, the ball goes back", t['d'] > t['reach'] and t['shape'] < t['r'] and h1['hits'] == t['hits'] + 1 and h1['dir'] == -1 and h1['misses'] == 0, [t, h1])
        # beside the hand: right of the palm, clear of the drawn outline and of the reach circle -> a miss
        await park(page); await page.mouse.move(120, 600); await page.wait_for_timeout(250)
        m = await page.evaluate(f"""(() => {{ const s = {S}, z = __grasp.CONFIG.STRIKE_HIT_Z, h = s.handShape(); s.setBallZ(z, 330, h.y); s.ball.speed = 0; const r = s.ballScreen().r;
          cursor.history.length = 0; cursor.history.push({{ t: performance.now(), x: h.x, y: h.y }}); const q = {REACH}(s.ball); return {{ r, d: q.d, reach: q.reach, gap: h.dist(q.sc.x, q.sc.y) - r, misses: s.misses, hits: s.hits }}; }})()""")
        await page.evaluate(f"{S}.ball.speed = __grasp.strike.pace"); await page.wait_for_function(f"{S}.misses > {m['misses']} || {S}.hits > {m['hits']}", timeout=8000)
        m2 = await page.evaluate(f"({{ hits: {S}.hits, misses: {S}.misses }})")
        check(f"ball beside the hand ({m['gap']:.0f} px clear of the drawn outline, outside the reach circle) -> a miss, no hit", m['gap'] > 10 and m['d'] > m['reach'] and m2['hits'] == m['hits'] and m2['misses'] == m['misses'] + 1, [m, m2])
        await page.evaluate(f"{S}.lives = {S}.maxLives; {S}.over = false")
        # (2) holes: the phone grid's cells vs a Big ball
        async def wall_with_gap(cells):  # a brick wall at z 900 with these cells knocked out as holes; the returning ball parked just before it at the gap's centre
            return await page.evaluate(f"""(() => {{ const s = {S}; s.walls.length = 0; const w = s.spawnWall('brick', 900); for (const k of w.bricks) k.hp = 1;
              const cells = {cells}.map(([c, r]) => w.bricks.find(k => k.col === c && k.row === r)); for (const k of cells) {{ k.alive = false; k.hole = true; k.hp = 0; w.left--; }}
              s.smashTest('medium'); const b = s.ball, cs = cells.map(k => brickCell(w, k.col, k.row)); b.x = cs.reduce((a, c) => a + c.x, 0) / cs.length; b.y = cs.reduce((a, c) => a + c.y, 0) / cs.length;
              b.lx = b.x; b.ly = b.y; const gc = s.ballGapContact(w, b); const c0 = brickCell(w, 0, 0); return {{ id: w.id, left: w.left, fits: s.ballFitsGap(w), clear: gc.over.length === 0, clip: gc.over.length, open: gc.open, r: ballRad(b), cw: c0.w, ch: c0.h, cols: w.cols, rows: w.rows }}; }})()""")
        await park(page)
        g = await page.evaluate(f"(() => {{ const w = {S}.spawnWall('brick', 900); return {{ cols: w.cols, rows: w.rows }}; }})()")
        mid = [g['cols'] // 2, g['rows'] // 2]
        await page.evaluate(f"{S}.catchTest('big')")
        for tier in ('medium', 'soft'):
            h = await wall_with_gap(f"[[{mid[0]}, {mid[1]}]]")
            await page.evaluate(f"{S}.ball.tier = '{tier}'; {S}.ball.super = false")
            await page.wait_for_function(f"(() => {{ const w = {S}.walls.find(q => q.id === {h['id']}); return !w || w.left < {h['left']} || ({S}.ball && {S}.ball.dir > 0); }})()", timeout=8000)
            a = await page.evaluate(f"(() => {{ const w = {S}.walls.find(q => q.id === {h['id']}); return {{ left: w ? w.left : 0, dir: {S}.ball ? {S}.ball.dir : 0 }}; }})()")
            check(f"Big ball (diameter {h['r'] * 2:.0f}) at a 1-cell hole ({h['cw']:.0f} x {h['ch']:.0f}) on a {tier} hit: does not fit -> no free pass; it breaks the bricks it overlaps" + (' (mostly in the hole: it flies on; else it bounces back)' if tier == 'soft' else ''),
                  not h['fits'] and h['r'] * 2 > min(h['cw'], h['ch']) and a['left'] < h['left'] and (tier != 'soft' or a['dir'] == (-1 if h['open'] >= 0.5 else 1)), [h, a])
        await page.evaluate(f"{S}.powerups.length = 0")
        # a normal ball and a 2 x 2 hole: it fits and flies through untouched
        await park(page)
        c0, r0 = max(0, mid[0] - 1), max(0, mid[1] - 1)
        h = await wall_with_gap(f"[[{c0}, {r0}], [{c0 + 1}, {r0}], [{c0}, {r0 + 1}], [{c0 + 1}, {r0 + 1}]]")
        zb = await page.evaluate(f"{S}.ball.z")
        await page.wait_for_function(f"{S}.ball && {S}.ball.z > 940", timeout=8000)
        a = await page.evaluate(f"(() => {{ const w = {S}.walls.find(q => q.id === {h['id']}); return {{ left: w ? w.left : -1, dir: {S}.ball.dir }}; }})()")
        check(f"ball (diameter {h['r'] * 2:.0f}) at a 2 x 2 hole ({h['cw'] * 2:.0f} x {h['ch'] * 2:.0f}): flies on (no bounce); untouched if its full circle fits, else only the edge bricks it clips go", a['dir'] == -1 and (a['left'] == h['left'] if h['clear'] else h['left'] - a['left'] == h['clip']), [h, a])
        # a ball off-centre in that hole, overlapping the bricks round it, does not fit
        nf = await page.evaluate(f"(() => {{ const s = {S}, w = s.walls.find(q => q.id === {h['id']}), c = brickCell(w, {c0}, {r0}); return s.ballFitsGap(w, {{ x: c.x + c.w / 2, y: c.y - c.h * 0.45, guest: null }}); }})()")
        check('the same ball half over the hole edge: does not fit (no free pass)', nf is False, nf)
        hf = await page.evaluate(f"(() => {{ const s = {S}, out = []; for (let i = 0; i < 12; i++) {{ s.walls.length = 0; const w = s.spawnWall('holed', 900), cs = w.bricks.filter(k => k.hole).map(k => brickCell(w, k.col, k.row)); out.push(s.ballFitsGap(w, {{ x: cs.reduce((a, c) => a + c.x, 0) / cs.length, y: cs.reduce((a, c) => a + c.y, 0) / cs.length, guest: null }})); }} return out; }})()")
        check('every spawned holed wall (12 on the phone grid) has a hole the ball fits through at its centre', all(hf), hf)
        check('phone: no page errors', not errs, errs); await ctx.close()

        # ===== the hole edge (desktop, 2D then 3D): the ball's FULL circle, swept over the crossing; clipped edge bricks go, the ball flies on =====
        for gfx in (None, "{ pr: 0.4, auto: false, shadows: false }"):
            tag = '3D' if gfx else '2D'
            ctx, page, errs = await open_page(b, 1280, 800, gfx=gfx)
            if gfx:
                await page.wait_for_function(f"{S}.gfx === '3d' || {S}.gfxInfo.state === 'failed'", timeout=20000)
                if await page.evaluate(f"{S}.gfx") != '3d': print('INFO no WebGL: 3D hole-edge check skipped'); await ctx.close(); continue
            await park(page)
            HOLE = f"""((dx, dy, lat) => {{ const s = {S}; s.walls.length = 0; const w = s.spawnWall('brick', 900); for (const k of w.bricks) k.hp = 1;
              const c0 = Math.max(0, Math.floor(w.cols / 2) - 1), r0 = Math.max(0, Math.floor(w.rows / 2) - 1);
              for (const [c, r] of [[c0, r0], [c0 + 1, r0], [c0, r0 + 1], [c0 + 1, r0 + 1]]) {{ const k = w.bricks.find(q => q.col === c && q.row === r); k.alive = false; k.hole = true; k.hp = 0; w.left--; }}
              const a = brickCell(w, c0, r0), z = brickCell(w, c0 + 1, r0 + 1), L = a.x - a.w / 2, Rr = z.x + z.w / 2, T = a.y - a.h / 2, B = z.y + z.h / 2;
              s.smashTest('medium'); const b = s.ball, r = ballRad(b); b.vx = b.vy = 0; b.spin = 0; b.speed = 0; // (held at the wall: the checks call smashWall themselves, or set the speed)
              b.x = (L + Rr) / 2 + dx * r; b.y = (T + B) / 2 + dy * r; b.lx = b.x + (lat || 0) * r; b.ly = b.y;
              return {{ id: w.id, left: w.left, r, hole: [L, Rr, T, B], x: b.x, y: b.y }}; }})"""
            OVER = f"""((id) => {{ const s = {S}, w = s.walls.find(q => q.id === id), b = s.ball; if (!w) return []; return w.bricks.filter(k => k.alive && sweptDist(w, k, b) < ballRad(b) - 0.5).map(k => [k.col, k.row]); }})"""
            # the ball's circle reaching over the hole's left edge by 5% / 15% of its radius
            for pen in (0.05, 0.15):
                h = await page.evaluate(HOLE + "(0, 0, 0)")
                hw = (h['hole'][1] - h['hole'][0]) / 2
                r = await page.evaluate(f"(() => {{ const s = {S}, w = s.walls.find(q => q.id === {h['id']}), b = s.ball, r = ballRad(b); b.x = {h['hole'][0]} + r * (1 - {pen}); b.lx = b.x; b.speed = s.pace; const spd = b.speed, pre = {OVER}({h['id']}), out = smashWall(w, b, performance.now()); return {{ pre, spd, out, left: w.left, clip: s.lastClip, speed: b.speed, dir: b.dir }}; }})()"); pre = r['pre']; spd = r['spd']
                post = await page.evaluate(OVER + f"({h['id']})")
                check(f"{tag}: ball overlapping the hole edge by {int(pen * 100)}% of its radius: exactly the {len(pre)} brick(s) it overlaps are knocked out, it flies on (no bounce, no slow-down), none left under its circle",
                      len(pre) >= 1 and r['out'] == 'pass' and h['left'] - r['left'] == len(pre) and r['clip'] and r['clip']['n'] == len(pre) and r['speed'] == spd and r['dir'] == -1 and post == [], [pre, r, post])
            h = await page.evaluate(HOLE + "(0, 0, 0)")
            r = await page.evaluate(f"(() => {{ const s = {S}, w = s.walls.find(q => q.id === {h['id']}); s.lastClip = null; const out = smashWall(w, s.ball, performance.now()); return {{ out, left: w.left, clip: s.lastClip }}; }})()")
            check(f'{tag}: ball wholly inside the hole: passes, no brick destroyed', r['out'] == 'pass' and r['left'] == h['left'] and r['clip'] is None, [h['left'], r])
            # swept: centred in the hole at the crossing, but it came in sideways from over the edge bricks this frame
            h = await page.evaluate(HOLE + "(0, 0, -3.2)")
            r = await page.evaluate(f"(() => {{ const s = {S}, w = s.walls.find(q => q.id === {h['id']}), b = s.ball; b.lx = b.x - 3.2 * ballRad(b); const pre = {OVER}({h['id']}), out = smashWall(w, b, performance.now()); return {{ pre, out, left: w.left }}; }})()"); pre = r['pre']
            check(f'{tag}: a crossing with lateral motion clips the edge brick(s) it swept over: destroyed, the ball passes', len(pre) >= 1 and r['out'] == 'pass' and h['left'] - r['left'] == len(pre), [pre, r])
            # mostly blocked: the ball's circle mostly over the bricks beside the hole -> a normal (medium) hit, not a clip
            h = await page.evaluate(HOLE + "(0, 0, 0)")
            r = await page.evaluate(f"(() => {{ const s = {S}, w = s.walls.find(q => q.id === {h['id']}), b = s.ball, r = ballRad(b); b.x = {h['hole'][0]} - r * 0.3; b.lx = b.x; s.lastClip = null; const open = s.ballGapContact(w).open, out = smashWall(w, b, performance.now()); return {{ open, out, left: w.left, clip: s.lastClip }}; }})()"); gc = r['open']
            check(f'{tag}: the circle mostly over the bricks (open {gc:.2f} < 0.5): a normal hit (v4: the medium footprint, the brick + a neighbour), not a clip, and the ball bounces', gc < 0.5 and r['clip'] is None and 1 <= h['left'] - r['left'] <= 2 and r['out'] == 'bounce', [gc, r])
            # a real flight across the edge: at the crossing frame (and after) no live brick overlaps the ball's circle, and the drawn bricks (3D) match
            h = await page.evaluate(HOLE + "(0, 0, 0)")
            await page.evaluate(f"(() => {{ const b = {S}.ball, r = ballRad(b); b.x = {h['hole'][0]} + r * 0.9; b.lx = b.x; b.vx = -0.05; b.speed = {S}.pace; }})()")
            await page.wait_for_function(f"!{S}.ball || {S}.ball.z > 905 || {S}.ball.dir > 0", timeout=8000); await page.evaluate(FRAMES)
            fl = await page.evaluate(f"(() => {{ const s = {S}, w = s.walls.find(q => q.id === {h['id']}); if (!w) return {{ gone: true }}; const e = typeof G3 !== 'undefined' && G3.walls && gfx3dActive() ? G3.walls.get(w.id) : null; let inst = null; if (e) {{ inst = 0; for (const k in e.ims) inst += e.ims[k].count; }} return {{ dir: s.ball.dir, over: {OVER}({h['id']}), live: w.left, inst, left0: {h['left']} }}; }})()")
            check(f'{tag}: a real flight over the hole edge: through (no bounce), edge bricks gone, no live brick under the ball after the crossing' + (', the 3D bricks match the live ones' if gfx else ''),
                  fl.get('gone') or (fl['dir'] == -1 and fl['over'] == [] and fl['live'] < fl['left0'] and (not gfx or fl['inst'] == fl['live'])), fl)
            check(f'{tag} hole edge: no page errors', not errs, errs); await ctx.close()

        # ===== 3D: the WebGL bricks and hole outlines sit at the logic's cells =====
        ctx, page, errs = await open_page(b, 1280, 800, gfx="{ pr: 0.4, auto: false, shadows: false }")
        await page.wait_for_function(f"{S}.gfx === '3d' || {S}.gfxInfo.state === 'failed'", timeout=20000)
        if await page.evaluate(f"{S}.gfx") == '3d':
            await park(page)
            r3 = await page.evaluate(f"""(async () => {{ const s = {S}; s.walls.length = 0; const w = s.spawnWall('holed', 900); await {FRAMES};
              const e = G3.walls.get(w.id), m = new G3.T.Matrix4(), p = new G3.T.Vector3(), got = [], want = [], holes = [];
              for (const k in e.ims) {{ const im = e.ims[k]; for (let i = 0; i < im.count; i++) {{ im.getMatrixAt(i, m); p.setFromMatrixPosition(m); got.push([Math.round(p.x + e.group.position.x), Math.round(-p.y)]); }} }}
              for (const k of w.bricks) {{ const c = brickCell(w, k.col, k.row); if (k.alive) want.push([Math.round(c.x), Math.round(c.y)]); else holes.push(c); }}
              const key = (a) => a.map(q => q.join(',')).sort().join(';'); let worst = 0;
              for (const k of w.bricks) {{ const c = brickCell(w, k.col, k.row), a = proj(c.x, c.y, w.z), q = s.project3d(c.x, c.y, w.z); worst = Math.max(worst, Math.hypot(a.x - q.x, a.y - q.y)); }}
              let hn = 0; if (e.holes) for (let i = 0; i < e.holes.count; i++) {{ e.holes.getMatrixAt(i, m); p.setFromMatrixPosition(m); if (holes.some(c => Math.abs(p.x - c.x) <= c.w / 2 + 1 && Math.abs(-p.y - c.y) <= c.h / 2 + 1)) hn++; }}
              return {{ same: key(got) === key(want), n: got.length, alive: want.length, holes: holes.length, outl: e.holes ? e.holes.count : 0, inHole: hn, worst }}; }})()""")
            check(f"3D: the instanced bricks are exactly the live logic cells ({r3['n']}), the hole outlines lie on the {r3['holes']} hole cells, and every cell projects where proj() puts it (worst {r3['worst']:.3f} px)", r3['same'] and r3['n'] == r3['alive'] and r3['holes'] >= 1 and r3['outl'] == r3['inHole'] == r3['holes'] * 4 and r3['worst'] < 1.5, r3)
            mv = await page.evaluate(f"""(async () => {{ const s = {S}; s.walls.length = 0; const w = s.spawnWall('moving', 900); w.phase = 1.1; await {FRAMES}; const e = G3.walls.get(w.id);
              const c = brickCell(w, 0, 0), m = new G3.T.Matrix4(), p = new G3.T.Vector3(); e.ims[Object.keys(e.ims).find(k => e.ims[k].count)].getMatrixAt(0, m); p.setFromMatrixPosition(m);
              return {{ ox: w.ox, gx: e.group.position.x, brick0: Math.abs(p.x + e.group.position.x - c.x) < 1 }}; }})()""")
            check("3D moving wall: the group follows the wall's ox, so its free column is where the logic has it", abs(mv['ox'] - mv['gx']) < 0.01 and mv['brick0'], mv)
        else: print('INFO no WebGL here: 3D hole check skipped')
        check('3D page: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)

asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
