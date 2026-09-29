exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
FIST_JS = """
window.mkFist = (cx, cy) => { // all four fingertips curled back toward the wrist, thumb away from the index tip (no pinch)
  const L = Array.from({length:21}, () => ({x: cx, y: cy + 0.10, z: 0}));
  L[0] = {x: cx, y: cy + 0.30, z:0}; L[9] = {x: cx, y: cy + 0.10, z:0}; L[4] = {x: cx - 0.14, y: cy + 0.16, z:0};
  for (const [tip, pip] of [[8,6],[12,10],[16,14],[20,18]]) { L[pip] = {x: cx + 0.02, y: cy + 0.02, z:0}; L[tip] = {x: cx + 0.02, y: cy + 0.14, z:0}; }
  return L;
};
window.fistAt = (X, Y) => { const m = 0.15; return mkFist(1 - (m + X / innerWidth * 0.7), m + Y / innerHeight * 0.7); };
window.sweep = (fn, x0, y0, x1, y1, ms) => { const t0 = performance.now(); window.__handFor = () => { const k = Math.min(1, (performance.now() - t0) / ms); return fn(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k); }; };
"""
async def punch(page, x0, x1, y, step=64, wait=16, shot=None):  # ~2 px/ms, well above PUNCH_SPEED
    await page.mouse.move(x0, y); await page.wait_for_timeout(120); await page.mouse.down()
    n = int(abs(x1 - x0) / step)
    for i in range(1, n + 1):
        await page.mouse.move(x0 + (x1 - x0) * i / n, y); await page.wait_for_timeout(wait)
        if shot and i == n // 2: await page.screenshot(path=shot)
    await page.mouse.up(); await page.wait_for_timeout(150)
STATE = "({score: __grasp.smash.score, bricks: __grasp.smash.bricks.length, pieces: __grasp.smash.pieces.length, cars: __grasp.smash.cars.length, over: __grasp.smash.over, walls: __grasp.smash.walls.length})"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
        # --- mouse, desktop ---
        ctx = await b.new_context(viewport={'width':1280,'height':800}); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT)
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
        link = await page.evaluate("(() => { const a = document.querySelector('#start a.link'); return a && [a.getAttribute('href'), a.textContent, a.getBoundingClientRect().width > 0]; })()")
        check('start screen links to Tremorti', link and link[0] == 'tremorti/' and 'Tremorti' in link[1] and link[2], link)
        await page.click('.modes button[data-mode=smash]')
        check('menu shows smash selected + description', await page.evaluate("document.querySelector('[data-mode=smash]').getAttribute('aria-pressed')==='true' && $('modeDesc').textContent.includes('fist')"))
        await page.click('#mouseBtn'); await page.wait_for_timeout(500)
        st = await page.evaluate(STATE)
        check('two brick walls stand, sandbox objects gone', st['walls'] == 2 and st['bricks'] >= 40 and await page.evaluate("bodies.length") == 0, st)
        check('bricks are static and rest on the floor', await page.evaluate("__grasp.smash.bricks.every(b => b.isStatic) && Math.max(...__grasp.smash.bricks.map(b => b.bounds.max.y)) <= innerHeight + 1"))
        left = await page.evaluate("__grasp.smash.endAt - performance.now()")
        check('60 s round timer running', 58000 < left <= 60000, left)
        await page.wait_for_timeout(600)
        left2 = await page.evaluate("__grasp.smash.endAt - performance.now()")
        check('timer counts down', left - left2 >= 500, [left, left2])
        # a fast drag through the top of the first wall
        tgt = await page.evaluate("(() => { const bs = __grasp.smash.bricks.filter(b => b.plugin.wall.id === 0); const top = Math.min(...bs.map(b => b.position.y)); return { x: __grasp.smash.walls[0].x, y: top + 10 }; })()")
        await punch(page, tgt['x'] - 260, tgt['x'] + 260, tgt['y'], shot='tests/out/smash_punch.png')
        st = await page.evaluate(STATE)
        check('fast drag knocks bricks loose + scores', st['pieces'] > 0 and st['bricks'] < 116 and st['score'] > 0, st)
        check('loose bricks are dynamic and moving', await page.evaluate("__grasp.smash.pieces.every(p => !p.isStatic) && __grasp.smash.pieces.some(p => p.speed > 0.5)"))
        check('gesture reads as fist while pressing', await page.evaluate("(() => { ptr.pinch = true; return readInput(performance.now()).fist; })()"))
        await page.evaluate("ptr.pinch = false")
        # slow drag: no punch
        s0 = await page.evaluate("__grasp.smash.score")
        tgt2 = await page.evaluate("(() => { const bs = __grasp.smash.bricks.filter(b => b.plugin.wall.id === 1); const top = Math.min(...bs.map(b => b.position.y)); return { x: __grasp.smash.walls[1].x, y: top + 10 }; })()")
        await punch(page, tgt2['x'] - 120, tgt2['x'] + 120, tgt2['y'], step=8, wait=60)
        check('slow drag does not smash', await page.evaluate("__grasp.smash.score") == s0, [s0, await page.evaluate("__grasp.smash.score")])
        # car
        await page.evaluate("__grasp.smash.nextCar = 0"); await page.wait_for_timeout(300)
        check('a car spawns and drives along the floor', await page.evaluate("__grasp.smash.cars.length >= 1 && __grasp.smash.cars[0].isStatic"))
        x0 = await page.evaluate("__grasp.smash.cars[0].position.x"); await page.wait_for_timeout(400)
        x1 = await page.evaluate("__grasp.smash.cars.length ? __grasp.smash.cars[0].position.x : NaN")
        check('car moves', abs(x1 - x0) > 20, [x0, x1])
        await page.evaluate("(() => { const c = __grasp.smash.cars[0]; M.Body.setPosition(c, { x: innerWidth * 0.5, y: c.plugin.y }); })()"); await page.wait_for_timeout(50)
        cy, cid = await page.evaluate("[__grasp.smash.cars[0].parts[1].position.y, __grasp.smash.cars[0].id]")
        s0, p0 = await page.evaluate("[__grasp.smash.score, __grasp.smash.pieces.length]")
        await punch(page, 640 - 300, 640 + 300, cy)
        st = await page.evaluate(STATE); gone = await page.evaluate("!__grasp.smash.cars.some(c => c.id === " + str(cid) + ")")
        check('punch crumples the car: parts fly, +25 and more', gone and st['pieces'] - p0 >= 12 and st['score'] - s0 >= 31, [st, s0, p0])
        check('glass shards are light sky triangles', await page.evaluate("__grasp.smash.pieces.filter(p => p.plugin.small && p.plugin.kind === 'poly').length") >= 6)
        # piece cap
        await page.evaluate("for (let i = 0; i < 40; i++) __grasp.spawnCar()")
        await page.evaluate("(() => { const now = performance.now(); for (const c of [...__grasp.smash.cars]) { M.Body.setPosition(c, {x: innerWidth/2, y: c.plugin.y}); } })()")
        for _ in range(4):
            await punch(page, 200, 1080, cy, step=80, wait=10)
            await page.evaluate("(() => { for (const c of __grasp.smash.cars) M.Body.setPosition(c, {x: innerWidth/2, y: c.plugin.y}); })()")
        n = await page.evaluate("__grasp.smash.pieces.length")
        check('dynamic pieces capped', n <= await page.evaluate("__grasp.CONFIG.SMASH_MAX_PIECES"), n)
        check('never more than 2 cars', await page.evaluate("__grasp.smash.cars.length") <= 2)
        await page.screenshot(path='tests/out/smash_mouse.png')
        # round end
        await page.evaluate("__grasp.setRoundEnd(performance.now() + 1000)"); await page.wait_for_timeout(1500)
        st = await page.evaluate(STATE); best = await page.evaluate("[__grasp.smash.best, localStorage.getItem('smashBest')]")
        check('round over after the timer', st['over'] and best[0] == st['score'] and best[1] == str(st['score']), [st, best])
        await page.screenshot(path='tests/out/smash_over.png')
        s_over = st['score']
        await page.mouse.move(300, 300); await page.mouse.down(); await page.mouse.up(); await page.wait_for_timeout(200)
        check('taps in the first second are ignored', await page.evaluate("__grasp.smash.over"))
        await page.wait_for_timeout(900)
        await page.mouse.down(); await page.mouse.up(); await page.wait_for_timeout(200)
        check('tap restarts a fresh round', await page.evaluate("!__grasp.smash.over && __grasp.smash.score === 0 && __grasp.smash.best === " + str(s_over)))
        await punch(page, tgt['x'] - 260, tgt['x'] + 260, tgt['y'])
        check('reset button restarts', await page.evaluate("__grasp.smash.score") > 0 and (await page.click('#resetBtn') or True) and await page.evaluate("__grasp.smash.score === 0 && __grasp.smash.pieces.length === 0"))
        await page.click('#hudBtn'); await page.wait_for_timeout(700)
        check('HUD shows smash + clock', 'smash' in await page.inner_text('#hud') and ':' in await page.inner_text('#hud'))
        await page.click('#modeBtn'); await page.wait_for_timeout(300)
        check('mode chip cycles smash -> sandbox and restores objects', await page.evaluate("gameMode === 'sandbox' && bodies.length === 10 && __grasp.smash.bricks.length === 0 && $('modeBtn').textContent === 'Slice'"))
        await page.click('#modeBtn'); await page.click('#modeBtn'); await page.wait_for_timeout(300)
        check('chip cycles sandbox -> slice -> smash', await page.evaluate("gameMode === 'smash' && __grasp.smash.bricks.length > 0 && $('modeBtn').textContent === 'Sandbox'"))
        check('mouse: no page errors', not errs, errs); await ctx.close()

        # --- camera fist, desktop ---
        ctx = await b.new_context(permissions=['camera'], viewport={'width':1280,'height':800}); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + HAND_JS + FIST_JS)
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
        await page.click('.modes button[data-mode=smash]'); await page.click('#camBtn')
        await page.wait_for_function("mode === 'camera'", timeout=15000)
        await page.evaluate("window.__handFor = () => fistAt(200, 300)"); await page.wait_for_timeout(700)
        check('camera: closed fist recognised', await page.evaluate("gesture") == 'fist', await page.evaluate("[gesture, hand.pinchD]"))
        await page.evaluate("window.__handFor = () => handAt(200, 300, 0.8)"); await page.wait_for_timeout(700)
        check('camera: open hand is not a fist', await page.evaluate("gesture") == 'open')
        tgt = await page.evaluate("(() => { const bs = __grasp.smash.bricks.filter(b => b.plugin.wall.id === 0); return { x: __grasp.smash.walls[0].x, y: Math.min(...bs.map(b => b.position.y)) + 10 }; })()")
        await page.evaluate(f"window.__handFor = () => fistAt({tgt['x'] - 250}, {tgt['y']})"); await page.wait_for_timeout(500)
        await page.evaluate(f"sweep(fistAt, {tgt['x'] - 250}, {tgt['y']}, {tgt['x'] + 250}, {tgt['y']}, 220)"); await page.wait_for_timeout(700)
        st = await page.evaluate(STATE)
        check('camera: fist punch smashes bricks', st['score'] > 0 and st['pieces'] > 0, st)
        check('camera: no page errors', not errs, errs); await ctx.close()

        # --- phone (touch), English + Hebrew ---
        for he in (False, True):
            ctx = await b.new_context(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs=[]
            page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT)
            await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
            if he: await page.tap('#startLang'); await page.wait_for_timeout(100)
            fits = await page.evaluate("(() => { const r = [...document.querySelectorAll('.modes button')].map(b => ({w: b.scrollWidth <= b.clientWidth + 1, in: b.getBoundingClientRect().right <= innerWidth})); const a = document.querySelector('#start a.link').getBoundingClientRect(); return r.every(x => x.w && x.in) && a.bottom <= innerHeight && a.width > 0; })()")
            check(('he' if he else 'en') + ' phone: 3 mode buttons and link fit', fits)
            if he: await page.screenshot(path='tests/out/smash_he_start.png')
            await page.tap('.modes button[data-mode=smash]'); await page.tap('#mouseBtn'); await page.wait_for_timeout(500)
            st = await page.evaluate(STATE)
            check(('he' if he else 'en') + ' phone: one wall on a narrow screen', st['walls'] == 1 and st['bricks'] > 15, st)
            tgt = await page.evaluate("(() => { const bs = __grasp.smash.bricks; return { x: __grasp.smash.walls[0].x, y: Math.min(...bs.map(b => b.position.y)) + 10 }; })()")
            await page.evaluate("__grasp.smash.nextCar = 0"); await page.wait_for_timeout(200)
            await punch(page, 20, 340, tgt['y'], step=40)
            st = await page.evaluate(STATE)
            check(('he' if he else 'en') + ' phone: touch swipe smashes', st['score'] > 0, st)
            await page.wait_for_timeout(400)
            await page.screenshot(path='tests/out/smash_phone' + ('_he' if he else '') + '.png')
            await page.evaluate("__grasp.setRoundEnd(performance.now() + 200)"); await page.wait_for_timeout(1600)
            check(('he' if he else 'en') + ' phone: round over', await page.evaluate("__grasp.smash.over"))
            await page.screenshot(path='tests/out/smash_phone_over' + ('_he' if he else '') + '.png')
            check(('he' if he else 'en') + ' phone: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
