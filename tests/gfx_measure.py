exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Graphics pass: per-mode screenshots + frame times (rAF interval and JS time per frame), phone 360x740 + desktop 1280x800.
#   python3 tests/gfx_measure.py before|after [mode ...]   -> tests/out/gfx_<tag>_<mode>_{phone,desktop}.png + tests/out/gfx_<tag>_frames.json
# Works on any version of index.html (no hooks of the graphics pass needed): a wrapper round requestAnimationFrame sums every callback's time.
import json as _json
TAG = sys.argv[1] if len(sys.argv) > 1 else 'after'
ONLY = sys.argv[2:]
MODES = ['start', 'sandbox', 'slice', 'smash', 'busy', 'strike', 'strike3d', 'advmap', 'shapes', 'drums', 'bubbles', 'paint', 'stars', 'pause']
FT = """(() => { const raf = window.requestAnimationFrame.bind(window); const m = window.__ftm = { on: false, cb: 0, iv: [], js: [], last: 0 };
  window.requestAnimationFrame = (cb) => raf((t) => { const a = performance.now(); try { cb(t); } finally { if (m.on) m.cb += performance.now() - a; } });
  const loop = (t) => { if (m.on) { if (m.last) { m.iv.push(t - m.last); m.js.push(m.cb); } m.cb = 0; m.last = t; } raf(loop); }; raf(loop); })();"""
STRIKE_PLAY = "(() => { const s = __grasp.strike; s.lives = 99; window.__srv = setInterval(() => { try { s.lives = Math.max(s.lives, 9); if (s.waiting) playerServe('hard'); } catch (e) {} }, 300); })()"

async def setup(page, m):
    if m in ('start',): return
    if m == 'advmap':
        await page.evaluate("setInputPref('mouse'); document.querySelector('.modes button[data-mode=strike]').click()"); await page.wait_for_function("!$('advMap').hidden", timeout=8000); return
    if m in ('drums', 'bubbles', 'paint', 'stars'):
        await page.evaluate(f"camg.touchOk = true; setInputPref('mouse'); __grasp.cg.start('{m}', 'mouse')"); await page.wait_for_function(f"gameMode === '{m}' && mode !== 'none'", timeout=8000)
        if m == 'paint': await page.evaluate("$('cgCam') && ($('cgCam').hidden = true)")
        return
    gm = 'strike' if m in ('strike', 'strike3d', 'pause') else m
    await page.evaluate(f"setGameMode('{gm}')"); await page.evaluate(START_MOUSE)
    await page.wait_for_function("mode !== 'none'", timeout=10000)
    if gm == 'strike':
        await page.wait_for_function("__grasp.strike.ball", timeout=10000); await page.evaluate(STRIKE_PLAY)
    if m == 'pause':
        await page.wait_for_timeout(400); await page.click('#pauseBtn'); await page.wait_for_function("menu.open", timeout=4000)

async def run(b, m, mobile):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    gfx = "window.__graspGfx = { pr: 0.5, auto: false };" if m == 'strike3d' else "window.__graspGfx = { mode: '2d' };"
    await page.add_init_script(INIT + gfx + FT + "localStorage.setItem('lang','en');")
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(900)
    await setup(page, m)
    await page.wait_for_timeout(1500)
    W, H = (360, 740) if mobile else (1280, 800)
    await page.evaluate("__ftm.on = true")
    t0 = time.time()
    i = 0
    while time.time() - t0 < 3.0:  # the pointer sweeps (the same in every version)
        i += 1; x = W * (0.2 + 0.6 * ((i * 37) % 100) / 100); y = H * (0.3 + 0.4 * ((i * 53) % 100) / 100)
        if m not in ('pause', 'start', 'advmap'): await page.mouse.move(x, y, steps=2)
        await page.wait_for_timeout(60)
    r = await page.evaluate("""(() => { const m = __ftm; m.on = false; const s = (a) => a.slice().sort((x, y) => x - y), q = (a, p) => a.length ? s(a)[Math.min(a.length - 1, Math.floor(a.length * p))] : 0, avg = (a) => a.reduce((x, y) => x + y, 0) / Math.max(1, a.length);
      return { n: m.iv.length, fps: +(1000 / avg(m.iv)).toFixed(1), iv: +avg(m.iv).toFixed(2), iv95: +q(m.iv, 0.95).toFixed(2), js: +avg(m.js).toFixed(2), js95: +q(m.js, 0.95).toFixed(2), gfx3d: typeof gfx3dActive === 'function' ? gfx3dActive() : null }; })()""")
    await page.screenshot(path=f"tests/out/gfx_{TAG}_{m}_{'phone' if mobile else 'desktop'}.png")
    r['errs'] = errs[:3]
    await ctx.close(); return r

async def main():
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        for m in (ONLY or MODES):
            for mobile in (True, False):
                k = m + ('_phone' if mobile else '_desktop')
                try: out[k] = await run(b, m, mobile)
                except Exception as e: out[k] = {'error': str(e)[:200]}
                print(k, out[k], flush=True)
        await b.close()
    path = f'tests/out/gfx_{TAG}_frames.json'
    try: old = _json.load(open(path))
    except Exception: old = {}
    old.update(out); _json.dump(old, open(path, 'w'), indent=1)
    srv.terminate()

asyncio.run(main())
