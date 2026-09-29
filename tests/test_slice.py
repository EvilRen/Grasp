exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
POINT_JS = """
window.mkPoint = (tx, ty) => { // index fingertip at camera coords (not mirrored); other fingers curled, thumb tucked
  const L = Array.from({length:21}, () => ({x: tx, y: ty + 0.25, z: 0}));
  L[0] = {x: tx, y: ty + 0.35, z:0}; L[9] = {x: tx, y: ty + 0.20, z:0};
  L[8] = {x: tx, y: ty, z:0}; L[6] = {x: tx, y: ty + 0.12, z:0}; L[4] = {x: tx - 0.08, y: ty + 0.22, z:0};
  for (const [tip, pip] of [[12,10],[16,14],[20,18]]) { L[pip] = {x: tx + 0.02, y: ty + 0.17, z:0}; L[tip] = {x: tx + 0.02, y: ty + 0.24, z:0}; }
  return L;
};
window.pointAt = (X, Y) => { const m = 0.15; return mkPoint(1 - (m + X / innerWidth * 0.7), m + Y / innerHeight * 0.7); };
// sweep the hand from (x0,y0) to (x1,y1) over ms, using builder fn
window.sweep = (fn, x0, y0, x1, y1, ms) => { const t0 = performance.now(); window.__handFor = () => { const k = Math.min(1, (performance.now() - t0) / ms); return fn(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k); }; };
window.parkFruit = (x, y) => { __grasp.CONFIG.SLICE_GRAVITY = 0; const f = __grasp.slice; f.fruits.length = 0; f.halves.length = 0; f.nextSpawn = 1e12;
  f.fruits.push({ x, y, vx: 0, vy: 0, r: 40, rot: 0, vr: 0, kind: {rind:'#ffc24b', flesh:'#ffe3a1', seed:null}, born: 0 }); };
"""
async def camera_page(b, mobile):
    opts = dict(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width':1280,'height':800})
    ctx = await b.new_context(permissions=['camera'], **opts); page = await ctx.new_page(); await routes(page); errs=[]
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + HAND_JS + POINT_JS)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
    if mobile: await page.tap('.modes button[data-mode=slice]')
    else: await page.click('.modes button[data-mode=slice]')
    await page.click('#camBtn') if not mobile else await page.tap('#camBtn')
    await page.wait_for_function("mode === 'camera'", timeout=15000)
    return ctx, page, errs

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
        # --- mouse ---
        ctx = await b.new_context(viewport={'width':1280,'height':800}); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + POINT_JS)
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
        await page.click('.modes button[data-mode=slice]')
        check('menu shows slice selected + description', await page.evaluate("document.querySelector('[data-mode=slice]').getAttribute('aria-pressed')==='true' && $('modeDesc').textContent.includes('Fruit')"))
        await page.click('#mouseBtn'); await page.wait_for_timeout(2500)
        check('fruit spawns and flies up from below', await page.evaluate("__grasp.slice.fruits.some(f => f.vy < 0) || __grasp.slice.fruits.length > 0"), await page.evaluate("__grasp.slice.fruits.map(f=>[Math.round(f.y), +f.vy.toFixed(2)])"))
        await page.evaluate("parkFruit(640, 400)")
        await page.mouse.move(400, 400); await page.mouse.down()
        for i in range(1, 13): await page.mouse.move(400 + i*40, 400); await page.wait_for_timeout(16)
        await page.mouse.up(); await page.wait_for_timeout(100)
        st = await page.evaluate("({score: __grasp.slice.score, halves: __grasp.slice.halves.length, fruits: __grasp.slice.fruits.length})")
        check('fast drag slices fruit into 2 halves', st['score'] == 1 and st['halves'] == 2 and st['fruits'] == 0, st)
        await page.evaluate("parkFruit(640, 400)")
        await page.mouse.move(560, 400); await page.mouse.down()
        for i in range(1, 17): await page.mouse.move(560 + i*10, 400); await page.wait_for_timeout(60)
        await page.mouse.up(); await page.wait_for_timeout(100)
        check('slow drag does not slice', await page.evaluate("__grasp.slice.fruits.length") == 1 and await page.evaluate("__grasp.slice.score") == 1)
        await page.mouse.move(400, 400); await page.wait_for_timeout(50)
        for i in range(1, 13): await page.mouse.move(400 + i*40, 400); await page.wait_for_timeout(16)
        check('hover without pressing does not slice', await page.evaluate("__grasp.slice.fruits.length") == 1)
        await page.evaluate("__grasp.CONFIG.SLICE_GRAVITY = 0.0012; __grasp.slice.fruits.length = 0; __grasp.slice.nextSpawn = 0"); await page.wait_for_timeout(4500)
        check('unsliced fruit counts as missed', await page.evaluate("__grasp.slice.missed") >= 1, await page.evaluate("__grasp.slice.missed"))
        await page.screenshot(path='tests/out/slice_mouse.png')
        await page.click('#modeBtn'); await page.wait_for_timeout(300)
        check('mode chip switches back to sandbox', await page.evaluate("gameMode") == 'sandbox' and await page.inner_text('#modeBtn') == 'Slice')
        check('mouse: no page errors', not errs, errs); await ctx.close()

        # --- camera, phone ---
        ctx, page, errs = await camera_page(b, True)
        check('camera slice mode active on phone', await page.evaluate("gameMode") == 'slice')
        await page.evaluate("window.__handFor = () => pointAt(60, 300)"); await page.wait_for_timeout(700)
        check('pointing hand recognised', await page.evaluate("gesture") == 'point', await page.evaluate("[gesture, hand.pinchD]"))
        await page.evaluate("parkFruit(180, 300)")
        await page.evaluate("sweep(pointAt, 60, 300, 320, 300, 250)"); await page.wait_for_timeout(700)
        st = await page.evaluate("({score: __grasp.slice.score, halves: __grasp.slice.halves.length})")
        check('pointing swipe slices fruit', st['score'] == 1 and st['halves'] == 2, st)
        # open hand (not pointing) swipe must not cut
        await page.evaluate("window.__handFor = () => handAt(40, 400, 0.8)"); await page.wait_for_timeout(700)
        await page.evaluate("parkFruit(180, 400)")
        await page.evaluate("sweep((x,y) => handAt(x, y, 0.8), 40, 400, 320, 400, 250)"); await page.wait_for_timeout(700)
        check('open-hand swipe does not cut', await page.evaluate("__grasp.slice.fruits.length") == 1, await page.evaluate("[gesture, __grasp.slice.score]"))
        await page.evaluate("sweep((x,y) => handAt(x, y, 0.1), 320, 400, 40, 400, 250)"); await page.wait_for_timeout(700)
        check('pinch swipe does not cut', await page.evaluate("__grasp.slice.fruits.length") == 1)
        # hand gone -> world freezes, no-hand screen
        await page.evaluate("window.__handFor = null; __grasp.slice.fruits[0].vy = -0.5"); await page.wait_for_timeout(900)
        y1 = await page.evaluate("__grasp.slice.fruits[0].y"); await page.wait_for_timeout(500); y2 = await page.evaluate("__grasp.slice.fruits[0].y")
        check('no hand -> no-hand screen + fruit frozen', await page.evaluate("!statusEl.hidden") and y1 == y2, [y1, y2])
        await page.evaluate("__grasp.CONFIG.SLICE_GRAVITY = 0.0012; window.__handFor = () => pointAt(180, 300); __grasp.slice.nextSpawn = 0"); await page.wait_for_timeout(1500)
        await page.screenshot(path='tests/out/slice_phone.png')
        check('phone: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
