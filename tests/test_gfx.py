exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# The graphics pass: the quality level (auto drop on slow frames, recovery), prefers-reduced-motion, the pixel-ratio cap, the screen
# transition (iris) and its end state, the shared particle pool's bound, squash & stretch, the living start background, per-mode frame times.
G = "__grasp.gfx"
FT = """(() => { const raf = window.requestAnimationFrame.bind(window); const m = window.__ftm = { on: false, cb: 0, iv: [], js: [], last: 0 };
  window.requestAnimationFrame = (cb) => raf((t) => { const a = performance.now(); try { cb(t); } finally { if (m.on) m.cb += performance.now() - a; } });
  const loop = (t) => { if (m.on) { if (m.last) { m.iv.push(t - m.last); m.js.push(m.cb); } m.cb = 0; m.last = t; } raf(loop); }; raf(loop); })();"""
FT_READ = """(() => { const m = __ftm; m.on = false; const avg = (a) => a.reduce((x, y) => x + y, 0) / Math.max(1, a.length), s = m.js.slice().sort((x, y) => x - y);
  const r = { n: m.iv.length, fps: +(1000 / avg(m.iv)).toFixed(1), js: +avg(m.js).toFixed(2), js95: +(s[Math.floor(s.length * 0.95)] || 0).toFixed(2) }; m.iv.length = m.js.length = 0; m.last = 0; return r; })()"""

async def fresh(b, mobile=False, init='', rm=None, dsf=None):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=dsf or 3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800}, device_scale_factor=dsf or 1)
    if rm: opts['reduced_motion'] = rm
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + "localStorage.setItem('lang','en');" + FT + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_function("window.__grasp && __grasp.gfx", timeout=8000); await page.wait_for_timeout(300)
    return ctx, page, errs

async def start(page, m):
    if m in ('drums', 'bubbles', 'paint', 'stars'):
        await page.evaluate(f"camg.touchOk = true; setInputPref('mouse'); __grasp.cg.start('{m}', 'mouse')")
    else:
        await page.evaluate(f"setGameMode('{m}')"); await page.evaluate(START_MOUSE)
    await page.wait_for_function(f"gameMode === '{m}' && mode !== 'none'", timeout=10000)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ---- the quality rule, fed frame times directly (deterministic) ----
        ctx, page, errs = await fresh(b)
        r = await page.evaluate(f"""(() => {{ const g = {G}, q = g.q; q.auto = false; q.level = 2; q.ema = 16.7; q.slow = q.fast = 0; q.recover = g.cfg.recover0; q.log.length = 0; const out = {{}};
          for (let t = 0; t < 1900; t += 25) g.step(25); out.before2s = q.level;            // 25 ms frames (40 fps) for 1.9 s: not yet
          for (let t = 0; t < 400; t += 25) g.step(25); out.after2s = q.level;              // past 2 s: one level down
          for (let t = 0; t < 2400; t += 25) g.step(25); out.after4s = q.level;             // another 2 s: the lowest
          for (let t = 0; t < 4000; t += 25) g.step(25); out.floor = q.level;               // never below 0
          for (let t = 0; t < 5000; t += 16.7) g.step(16.7); out.fast5s = q.level;          // 60 fps for 5 s: not yet back (6 s needed)
          for (let t = 0; t < 1500; t += 16.7) g.step(16.7); out.fast6s = q.level;          // past 6 s: one level back
          out.recover = q.recover; for (let t = 0; t < 8500; t += 16.7) g.step(16.7); out.fast8s = q.level; // the next one waits longer (9 s: hysteresis)
          for (let t = 0; t < 1000; t += 16.7) g.step(16.7); out.fast9s = q.level;
          for (let i = 0; i < 50; i++) g.step(400); out.stall = q.level;                  // a stalled tab (>= 250 ms frames) is ignored
          for (let t = 0; t < 3000; t += 16.7) {{ g.step(16.7); g.step(30); }} out.mixed = q.level; // a jittery ~43 fps (the average just under 25 ms): drops
          out.log = q.log.map(e => e.l + ':' + e.why); q.auto = true; return out; }})()""")
        check('quality rule: frame times > 20 ms for 2 s drop a level (2 -> 1 -> 0, never below 0)', r['before2s'] == 2 and r['after2s'] == 1 and r['after4s'] == 0 and r['floor'] == 0, r)
        check('quality rule: a steady 60 fps brings a level back after 6 s, the next one after longer (9 s); stalls are ignored', r['fast5s'] == 0 and r['fast6s'] == 1 and r['recover'] > 6000 and r['fast8s'] == 1 and r['fast9s'] == 2 and r['stall'] == 2, r)
        check('quality rule: a jittery ~43 fps also drops it; every change logged with its reason', r['mixed'] < 2 and r['log'][:4] == ['1:slow', '0:slow', '1:fast', '2:fast'], r)

        # ---- the real watch: a slow device (a busy loop in every frame) drops the level, the extras shrink, then it recovers ----
        await page.evaluate(f"(() => {{ const q = {G}.q; {G}.set(2); q.ema = 16.7; q.slow = q.fast = 0; q.recover = {G}.cfg.recover0; }})()")
        await start(page, 'sandbox'); await page.wait_for_timeout(300)
        c0 = await page.evaluate(f"({{ l: {G}.level(), cap: ({G}.q.ema = 16.7, {G}.cap()), cls: document.body.className }})")  # (the cap at a steady frame: under load fxLoad() also halves it for the moment)
        await page.evaluate(f"{G}.q.burn = 40")
        await page.wait_for_function(f"{G}.level() < 2", timeout=15000, polling=100)
        c1 = await page.evaluate(f"({{ l: {G}.level(), cap: (() => {{ const e = {G}.q.ema; {G}.q.ema = 16.7; const c = {G}.cap(); {G}.q.ema = e; return c; }})(), cls: document.body.className, log: {G}.q.log.slice(-1)[0] }})")
        check('slow frames (a 40 ms busy loop a frame) drop the quality within seconds: body class, a smaller particle cap', c0['l'] == 2 and c1['l'] < 2 and c1['cap'] < c0['cap'] and ('gfx1' in c1['cls'] or 'gfx0' in c1['cls']) and c1['log']['why'] == 'slow', [c0, c1])
        await page.wait_for_function(f"{G}.level() === 0", timeout=15000, polling=100)
        sq = await page.evaluate(f"{G}.squash({{ t: performance.now(), k: 0.2, ang: 0 }}, performance.now())")
        check('lowest quality: no squash & stretch, the start screen\'s motes off', sq is None and await page.evaluate("document.body.classList.contains('gfx0')"))
        await page.evaluate(f"{G}.q.burn = 0; {G}.q.recover = {G}.cfg.recover0")
        t0 = time.time()
        await page.wait_for_function(f"{G}.level() >= 1", timeout=45000, polling=200)
        check(f'fast frames again: the quality comes back by itself ({time.time() - t0:.1f} s)', await page.evaluate(f"{G}.q.log.slice(-1)[0].why") == 'fast')
        await page.evaluate(f"{G}.set(2)")
        check('quality: no page errors', not errs, errs); await ctx.close()

        # ---- the pixel ratio: capped at 2 (a dpr-3 phone draws at 2x, crisp, not 3x), 1x and 1.5x as they are; the dot grid drawn at the ratio ----
        for mobile, dsf, want in ((True, 3, 2), (False, 1, 1), (False, 1.5, 1.5)):
            ctx, page, errs = await fresh(b, mobile, dsf=dsf)
            d = await page.evaluate(f"(() => {{ resize(); return {{ dpr: DPR, ss: SS, c: {G}.canvas(), grid: gridCanvas.width, pv: document.querySelector('canvas.pvc').width }}; }})()")
            W_ = 360 if mobile else 1280
            check(f'dpr {dsf}: the canvas draws at {want}x (capped at 2), sprites at the same scale, the dot grid and previews too', d['dpr'] == want and d['ss'] == want and d['c']['w'] == round(W_ * want) and d['c']['cw'] == W_ and d['grid'] == 32 * max(1, round(want)) and d['pv'] == round(120 * want), d)
            await ctx.close()

        # ---- the screen transition: a tile tap starts the game at once under an iris that opens from the tile and ends cleanly ----
        for mobile in (True, False):
            tag = 'phone' if mobile else 'desktop'
            ctx, page, errs = await fresh(b, mobile)
            await page.wait_for_timeout(1300)
            check(f'{tag}: the iris takes about a third of a second', await page.evaluate(f"{G}.XF.ms") == 340)
            await page.evaluate(f"{G}.XF.ms = 1200")  # (slowed down so the checks below catch it mid-way on a loaded machine)
            sel = '.modes button[data-mode=slice]'
            box = await page.evaluate(f"(() => {{ const r = document.querySelector('{sel}').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }})()")
            await (page.tap(sel) if mobile else page.click(sel))
            a = await page.evaluate(f"({{ on: {G}.xf.on, shown: !$('xfade').hidden, mode, gm: gameMode, start: $('start').hidden, last: {G}.xf.log.slice(-1)[0], runs: {G}.xf.runs, pe: getComputedStyle($('xfade')).pointerEvents }})")
            check(f'{tag}: a tile tap starts the game at once (state not delayed) under the iris, which lets taps through', a['mode'] != 'none' and a['gm'] == 'slice' and a['start'] and a['on'] and a['shown'] and a['pe'] == 'none', a)
            check(f'{tag}: the iris opens from the tapped tile', abs(a['last']['x'] - box[0]) < 40 and abs(a['last']['y'] - box[1]) < 40, [a['last'], box])
            await page.wait_for_timeout(120)
            if mobile: await page.screenshot(path='tests/out/gfx_iris_phone.png')
            await page.wait_for_function(f"!{G}.xf.on", timeout=3000)
            e = await page.evaluate(f"({{ shown: !$('xfade').hidden, bg: $('xfade').style.background, done: {G}.xf.done, mode, gm: gameMode }})")
            e['dur'] = await page.evaluate(f"{G}.xf.dur")
            check(f'{tag}: the iris ends on time: hidden, cleared, the game on screen', not e['shown'] and e['bg'] == '' and e['done'] >= 1 and e['gm'] == 'slice' and e['mode'] != 'none' and 1150 <= e['dur'] < 2500, e)
            await page.evaluate(f"{G}.XF.ms = 340")
            await page.evaluate("goHome()")
            h = await page.evaluate(f"({{ on: {G}.xf.on, kind: {G}.xf.kind, start: !$('start').hidden, mode }})")
            check(f'{tag}: Home: back on the start screen at once, under an iris from the centre', h['on'] and h['kind'] == 'home' and h['start'] and h['mode'] == 'none', h)
            await page.wait_for_function(f"!{G}.xf.on && $('xfade').hidden", timeout=3000)
            sel = '.modes button[data-mode=strike]'
            await (page.tap(sel) if mobile else page.click(sel))
            await page.wait_for_function("!$('advMap').hidden", timeout=4000)
            check(f'{tag}: the Strike tile: the iris onto the Adventure map', await page.evaluate(f"{G}.xf.log.slice(-1)[0].kind === 'in' && {G}.xf.runs >= 3"))
            await page.wait_for_function(f"!{G}.xf.on", timeout=3000)
            check(f'{tag}: transitions: no page errors', not errs, errs); await ctx.close()

        # ---- prefers-reduced-motion: no iris, no ambient motion, half the particles, a tiny shake ----
        ctx, page, errs = await fresh(b, False, rm='reduce')
        rm = await page.evaluate(f"({{ red: {G}.reduced(), calm: document.body.classList.contains('gfxCalm'), blob: getComputedStyle(document.querySelector('#startFx .blob')).animationName, sh: getComputedStyle(document.querySelector('#startFx .sh')).display, tile: getComputedStyle(document.querySelector('.modes button[aria-pressed=true]'), '::after').animationName, cap: {G}.cap() }})")
        await page.click('.modes button[data-mode=slice]'); await page.wait_for_function("gameMode === 'slice' && mode !== 'none'", timeout=8000)
        x = await page.evaluate(f"({{ on: {G}.xf.on, shown: !$('xfade').hidden, skipped: {G}.xf.skipped, log: {G}.xf.log.slice(-1)[0] }})")
        await page.evaluate("shakeScreen(4)"); sh = await page.evaluate("shake.amp")
        check('reduced motion: detected (body.gfxCalm); the start background still (no drifting blobs / shapes), no tile glow', rm['red'] and rm['calm'] and rm['blob'] == 'none' and rm['sh'] == 'none' and rm['tile'] == 'none', rm)
        check('reduced motion: no iris (skipped, the game at once), a tiny shake, half the particle cap', not x['on'] and not x['shown'] and x['skipped'] >= 1 and x['log']['skipped'] == 'reduced' and sh <= 0.6 and rm['cap'] == 160, [x, sh, rm['cap']])
        check('reduced motion: no page errors', not errs, errs); await ctx.close()

        # ---- the particle pool: bounded, recycled, no growth; every kind drawn; squash & stretch ----
        for mobile in (False, True):
            ctx, page, errs = await fresh(b, mobile)
            await start(page, 'sandbox'); await page.wait_for_timeout(200)
            r = await page.evaluate(f"""(() => {{ const g = {G}, P = g.fxp, n0 = P.pool.length; g.q.auto = false; g.q.ema = 16.7; const cap = g.cap();  // (a steady frame for this check: under load fxLoad() would halve the bursts)
              for (let i = 0; i < 400; i++) g.burst(200 + i % 300, 300, ['spark', 'star', 'shard', 'dot', 'confetti', 'drop', 'dust', 'glow'][i % 8], {{ n: 12, col: ['#ff6f59', '#ffc24b'] }});
              g.q.auto = true; return {{ n: P.n, cap, pool: P.pool.length, n0, recycled: P.recycled, kinds: [...new Set(P.pool.slice(0, P.n).map(q => q.k))].length }}; }})()""")
            tag = 'phone' if mobile else 'desktop'
            check(f'{tag}: 4800 particles asked -> the pool stays at its cap ({r["cap"]}), the oldest recycled, no new objects', r['n'] == r['cap'] and r['pool'] == r['n0'] == 320 and r['recycled'] > 4000 and r['kinds'] == 8, r)
            await page.evaluate(f"__ftm.on = true"); await page.wait_for_timeout(700); ft = await page.evaluate(FT_READ)
            if not mobile: await page.screenshot(path='tests/out/gfx_pool_full.png')
            check(f'{tag}: a full pool still draws in a few ms a frame ({ft["js"]} ms avg JS, {ft["fps"]} fps)', ft['js'] < 12 and ft['n'] > 5, ft)
            await page.wait_for_function(f"{G}.fxp.n === 0", timeout=6000)
            check(f'{tag}: every particle fades out (the pool empties by itself)', True)
            sq = await page.evaluate(f"(() => {{ const t = performance.now(), s = {G}.squash, q = {{ t, k: 0.2, ang: 0.5 }}; return [s(q, t), s(q, t + 200), s(q, t + 500), s(null, t)]; }})()")
            check(f'{tag}: squash & stretch: squashed along the hit first, springs back, gone after 0.42 s', sq[0][0] < 0.9 and sq[0][1] > 1.1 and abs(sq[1][0] - 1) < 0.06 and sq[2] is None and sq[3] is None, sq)
            m0 = await page.evaluate(f"(() => {{ bodies.forEach((b, i) => {{ b.plugin.sq = null; M.Body.setPosition(b, {{ x: (i + 0.5) * innerWidth / bodies.length, y: innerHeight * 0.35 }}); M.Body.setVelocity(b, {{ x: 0, y: 25 }}); }}); return {G}.fxp.made; }})()")
            await page.wait_for_function("bodies.some(b => b.plugin.sq)", timeout=8000, polling=30)
            check(f'{tag}: sandbox bodies that hit hard get their squash and the shared impact juice', await page.evaluate(f"bodies.filter(b => b.plugin.sq).every(b => b.plugin.sq.k > 0) && {G}.fxp.made > {m0}"))
            f0 = await page.evaluate("burst(300, 300, undefined, 20); particles.push({ x: 200, y: 200, vx: 0, vy: 0, life: 1, decay: 0.001, r: 5 }); __grasp.gfx.q.frames")
            await page.wait_for_timeout(300)
            check(f'{tag}: an older particle with no colour draws (white) and the game loop keeps running', await page.evaluate("__grasp.gfx.q.frames") - f0 >= 5)
            check(f'{tag}: pool: no page errors', not errs, errs); await ctx.close()

        # ---- the start screen's living background: on screen, moving, inside the screen (no scroll), the tiles' spring ----
        ctx, page, errs = await fresh(b, True)
        await page.wait_for_timeout(1300)
        L = await page.evaluate("""(() => { const f = $('startFx'), r = f.getBoundingClientRect(), st = $('start'); const tr = () => [...f.querySelectorAll('.blob, .sh')].map(e => getComputedStyle(e).transform).join('|');
          return { n: f.querySelectorAll('.blob').length, sh: f.querySelectorAll('.sh').length, m: f.querySelectorAll('.m').length, full: r.width >= innerWidth - 1 && r.height >= innerHeight - 1, noScroll: st.scrollHeight <= st.clientHeight + 1 && document.documentElement.scrollHeight <= innerHeight, pe: getComputedStyle(f).pointerEvents, a: tr() }; })()""")
        await page.wait_for_timeout(500)
        a2 = await page.evaluate("[...$('startFx').querySelectorAll('.blob, .sh')].map(e => getComputedStyle(e).transform).join('|')")
        check('start screen: a living background (4 colour blobs, drifting shapes, twinkling motes) behind everything, never scrolls, takes no taps', L['n'] == 4 and L['sh'] >= 7 and L['m'] >= 8 and L['full'] and L['noScroll'] and L['pe'] == 'none', L)
        check('start screen: the background moves (CSS animations, no JS per frame)', a2 != L['a'])
        tr = await page.evaluate("(() => { const b = document.querySelector('.modes button[data-mode=slice]'); return getComputedStyle(b).transitionTimingFunction; })()")
        check('tiles: a springy transition (an overshooting cubic-bezier)', '1.56' in tr, tr)
        await page.screenshot(path='tests/out/gfx_start_phone.png')
        check('start: no page errors', not errs, errs); await ctx.close()

        # ---- per-mode frame-time sanity in headless (phone, 2D): every mode keeps its frames cheap with the new effects ----
        res = {}
        for m in ('sandbox', 'slice', 'smash', 'busy', 'strike', 'shapes', 'drums', 'bubbles', 'paint', 'stars'):
            ctx, page, errs = await fresh(b, True, init="window.__graspGfx = { mode: '2d' };")
            await start(page, m)
            if m == 'strike': await page.wait_for_function("__grasp.strike.ball", timeout=10000); await page.evaluate("(() => { const s = __grasp.strike; window.__srv = setInterval(() => { try { s.lives = Math.max(s.lives, 9); if (s.waiting) playerServe('hard'); } catch (e) {} }, 300); })()")
            await page.wait_for_timeout(800)
            await page.evaluate(f"{G}.impact(180, 300, '#ffc24b', 1); {G}.confetti(180, 300, 30)")  # a burst on screen while measuring
            await page.evaluate("__ftm.on = true"); await page.wait_for_timeout(1500)
            r = await page.evaluate(FT_READ); res[m] = r
            check(f'{m}: frame time sane in headless with the new effects ({r["js"]} ms avg JS / {r["js95"]} p95, {r["fps"]} fps)', r['n'] >= 20 and r['js'] < 8 and r['js95'] < 20, r)
            check(f'{m}: no page errors', not errs, errs); await ctx.close()
        print('INFO frame times (phone, 2D):', json.dumps(res))
        await b.close()
    srv.terminate()
    print('ALL PASS' if check.fails == 0 else f'{check.fails} FAILED'); sys.exit(1 if check.fails else 0)

asyncio.run(main())
