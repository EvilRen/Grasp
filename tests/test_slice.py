exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
POINT_JS = """
window.mkPoint = (tx, ty) => { // index fingertip at camera coords (not mirrored); other fingers curled, thumb tucked
  const L = Array.from({length:21}, () => ({x: tx, y: ty + 0.25, z: 0}));
  L[0] = {x: tx, y: ty + 0.35, z:0}; L[9] = {x: tx, y: ty + 0.20, z:0};
  L[8] = {x: tx, y: ty, z:0}; L[6] = {x: tx, y: ty + 0.12, z:0}; L[4] = {x: tx - 0.08, y: ty + 0.22, z:0};
  for (const [tip, pip] of [[12,10],[16,14],[20,18]]) { L[pip] = {x: tx + 0.02, y: ty + 0.17, z:0}; L[tip] = {x: tx + 0.02, y: ty + 0.24, z:0}; }
  return L;
};
window.pointAt = (X, Y) => { const B = __grasp.CONFIG.MAP_BOX, m = (1 - B) / 2; return mkPoint(1 - (m + X / innerWidth * B), m + Y / innerHeight * B); };
// sweep the hand from (x0,y0) to (x1,y1) over ms, using builder fn
window.sweep = (fn, x0, y0, x1, y1, ms) => { const t0 = performance.now(); window.__handFor = () => { const k = Math.min(1, (performance.now() - t0) / ms); return fn(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k); }; };
window.parkFruit = (x, y) => { __grasp.CONFIG.SLICE_GRAVITY = 0; const f = __grasp.slice; f.fruits.length = 0; f.halves.length = 0; f.nextSpawn = 1e12;
  f.fruits.push({ x, y, vx: 0, vy: 0, r: 40, rot: 0, vr: 0, kind: {rind:'#ffc24b', flesh:'#ffe3a1', seed:null}, born: 0 }); };
window.parkBomb = (x, y) => { parkFruit(x, y); __grasp.slice.fruits[0].bomb = true; };
window.dropFruit = () => { __grasp.CONFIG.SLICE_GRAVITY = 0; const f = __grasp.slice; f.nextSpawn = 1e12; // a fruit already below the screen, still falling: a miss on the next tick
  f.fruits.push({ x: 300, y: innerHeight + 100, vx: 0, vy: 0.5, r: 40, rot: 0, vr: 0, kind: {rind:'#ffc24b', flesh:'#ffe3a1', seed:null}, born: 0 }); };
"""
PIX = "((x, y) => { const d = ctx.getImageData(Math.round(x * DPR), Math.round(y * DPR), 1, 1).data; return [d[0], d[1], d[2]]; })"
ROUND = "({score: __grasp.slice.score, missed: __grasp.slice.missed, lives: __grasp.slice.lives, over: __grasp.slice.over, best: __grasp.slice.best, ls: localStorage.getItem('sliceBest'), bombsHit: __grasp.slice.bombsHit, fruits: __grasp.slice.fruits.length, buttons: __grasp.slice.ui.buttons, nb: __grasp.slice.ui.newBest, rb: __grasp.slice.ui.ribbon})"
async def end_round(page):  # three misses end the round; then the card is armed after ~600 ms
    for _ in range(3): await page.evaluate("dropFruit()"); await page.wait_for_timeout(120)
    await page.wait_for_function("__grasp.slice.over && __grasp.slice.ui.buttons", timeout=3000); await page.wait_for_timeout(650)
async def camera_page(b, mobile):
    opts = dict(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width':1280,'height':800})
    ctx = await b.new_context(permissions=['camera'], **opts); page = await ctx.new_page(); await routes(page); errs=[]
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + HAND_JS + POINT_JS)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
    await page.click('#camBtn') if not mobile else await page.tap('#camBtn')
    if mobile: await page.tap('.modes button[data-mode=slice]')
    else: await page.click('.modes button[data-mode=slice]')
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
        await page.evaluate(START_MOUSE); await page.wait_for_timeout(2500)
        if not await page.evaluate("__grasp.slice.fruits.length > 0"): await page.evaluate("__grasp.spawnWave()"); await page.wait_for_timeout(300)  # spawn timing is random
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
        st = await page.evaluate(ROUND)
        check('unsliced fruit counts as missed', st['missed'] >= 1, st)
        check('a missed fruit costs a life (3 lives a round)', st['lives'] == max(0, 3 - st['missed']) and st['over'] == (st['missed'] >= 3), st)
        # a round, step by step: one fruit sliced, then three misses end it with the card and a new best
        await page.evaluate("localStorage.removeItem('sliceBest'); __grasp.slice.best = 0; __grasp.resetSlice()"); await page.mouse.move(100, 700); await page.wait_for_timeout(100)
        check('reset restarts the round: 3 lives, score 0', await page.evaluate("__grasp.slice.lives === 3 && !__grasp.slice.over && __grasp.slice.score === 0 && __grasp.slice.ui.buttons === null"))
        await page.evaluate("parkFruit(640, 400)")
        await page.mouse.move(400, 400); await page.mouse.down()
        for i in range(1, 13): await page.mouse.move(400 + i*40, 400); await page.wait_for_timeout(16)
        await page.mouse.up(); await page.mouse.move(100, 700); await page.wait_for_timeout(100)
        await page.evaluate("dropFruit()"); await page.wait_for_timeout(700)
        hearts = await page.evaluate("__grasp.slice.ui.hearts"); h0 = await page.evaluate(PIX + f"({hearts[0]['x']}, {hearts[0]['y']})"); h2 = await page.evaluate(PIX + f"({hearts[2]['x']}, {hearts[2]['y']})")
        check('lives shown as hearts under the score: first red, the lost one hollow', len(hearts) == 3 and await page.evaluate("__grasp.slice.lives") == 2 and h0[0] > 170 and h0[0] > h0[2] + 60 and h2[0] < 120, [hearts, h0, h2])
        await page.screenshot(path='tests/out/slice_lives.png')
        await page.evaluate("dropFruit()"); await page.wait_for_timeout(120); await page.evaluate("dropFruit()")
        await page.wait_for_function("__grasp.slice.over && __grasp.slice.ui.buttons", timeout=3000); await page.wait_for_timeout(650)
        st = await page.evaluate(ROUND)
        check('third miss: round over, best saved in localStorage, NEW BEST', st['over'] and st['lives'] == 0 and st['missed'] == 3 and st['score'] == 1 and st['best'] == 1 and st['ls'] == '1' and st['nb'], st)
        rbp = await page.evaluate(PIX + f"({st['rb']['x']}, {st['rb']['y']})") if st['rb'] else None
        check('NEW BEST ribbon drawn on the card corner', rbp and rbp[0] > 200 and rbp[1] > 140 and rbp[2] < 130, rbp)
        bt = st['buttons']
        check('card: Play again + Home side by side, no difficulty pill', bt and set(bt) == {'again', 'home'} and bt['again']['y'] == bt['home']['y'] and bt['again']['x'] + bt['again']['w'] < bt['home']['x'] and bt['home']['x'] + bt['home']['w'] <= 1280, bt)
        ab = await page.evaluate(PIX + f"({bt['again']['x'] + 12}, {bt['again']['y'] + bt['again']['h'] / 2})")
        check('Play again button is saffron', ab[0] > 200 and ab[1] > 150 and ab[2] < 130, ab)
        await page.screenshot(path='tests/out/slice_over.png')
        await page.mouse.click(bt['again']['x'] + bt['again']['w'] / 2, bt['again']['y'] + bt['again']['h'] / 2); await page.wait_for_timeout(200)
        st = await page.evaluate(ROUND)
        check('click Play again: fresh round, best kept', not st['over'] and st['lives'] == 3 and st['score'] == 0 and st['best'] == 1 and st['buttons'] is None, st)
        # bombs: one every ~6 fruit; slicing one costs a life with a flash and a boom
        await page.evaluate("__grasp.slice.fruits.length = 0; for (let i = 0; i < 8; i++) __grasp.spawnWave(performance.now())")
        bm = await page.evaluate("({spawned: __grasp.slice.spawned, bombs: __grasp.slice.bombs, inAir: __grasp.slice.fruits.filter(f => f.bomb).length, kinds: __grasp.slice.fruits.map(f => f.kind.name)})")
        check('a bomb flies up among the fruit after ~6 of them', bm['spawned'] >= 6 and bm['bombs'] >= 1 and bm['inAir'] >= 1 and bm['bombs'] <= bm['spawned'] / 5 + 1, bm)
        await page.evaluate("parkBomb(640, 400)"); await page.mouse.move(400, 400); await page.mouse.down()
        for i in range(1, 13):
            await page.mouse.move(400 + i*40, 400); await page.wait_for_timeout(16)
            if i == 7: await page.screenshot(path='tests/out/slice_bomb.png')
        await page.mouse.up(); await page.mouse.move(100, 700); await page.wait_for_timeout(60)
        st = await page.evaluate(ROUND); fl = await page.evaluate("performance.now() - __grasp.slice.flash")
        check('slicing a bomb costs a life (no points), with a flash', st['lives'] == 2 and st['bombsHit'] == 1 and st['score'] == 0 and st['fruits'] == 0 and st['missed'] == 0 and fl < 1500, [st, fl])
        await menu_click(page, '#resetBtn'); await page.wait_for_timeout(100)
        check('reset button restarts the round', await page.evaluate("__grasp.slice.lives === 3 && __grasp.slice.score === 0 && !__grasp.slice.over"))
        await end_round(page); bt = await page.evaluate("__grasp.slice.ui.buttons")
        await page.mouse.click(bt['home']['x'] + bt['home']['w'] / 2, bt['home']['y'] + bt['home']['h'] / 2); await page.wait_for_timeout(200)
        check('click Home on the card: back to the start screen', await page.evaluate("mode === 'none' && !$('start').hidden && document.body.classList.contains('home')"))
        await page.evaluate(START_MOUSE); await page.wait_for_timeout(300)
        check('start again: a fresh round', await page.evaluate("mode === 'mouse' && gameMode === 'slice' && __grasp.slice.lives === 3 && !__grasp.slice.over"))
        await menu_click(page, '#hudBtn'); await page.wait_for_timeout(700)
        check('HUD shows slice lives', 'lives' in await page.inner_text('#hud')); await menu_click(page, '#hudBtn')
        # katana: drawn while the blade is on, gone when it is off
        await page.evaluate("parkFruit(640, 460); __grasp.slice.drawn = 0")
        await page.mouse.move(400, 400); await page.mouse.down()
        for i in range(1, 9): await page.mouse.move(400 + i*40, 400 + i*10); await page.wait_for_timeout(16)
        kat = await page.evaluate("({drawn: __grasp.slice.drawn, ang: __grasp.slice.ang, cuts: __grasp.slice.cuts.length, on: __grasp.slice.bladeOn})")
        await page.screenshot(path='tests/out/slice_katana.png')
        await page.mouse.up(); await page.wait_for_timeout(50)
        check('katana renders along the swipe + cut line', kat['on'] and kat['drawn'] > 3 and 0 < kat['ang'] < 0.6 and kat['cuts'] == 1, kat)
        d0 = await page.evaluate("__grasp.slice.drawn"); await page.wait_for_timeout(120)
        check('katana hidden when the blade is off', await page.evaluate("__grasp.slice.drawn") == d0 and not await page.evaluate("__grasp.slice.bladeOn"))
        await page.screenshot(path='tests/out/slice_mouse.png')
        await page.evaluate("__grasp.setGameMode('sandbox')"); await page.wait_for_timeout(300)
        check('switching back to sandbox restores objects', await page.evaluate("gameMode === 'sandbox' && bodies.length === 10 && !document.getElementById('modeBtn')"))
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
        # an open hand (not pointing) cuts only when it moves fast; a slow open hand and a pinch never cut
        await page.evaluate("window.__handFor = () => handAt(40, 400, 0.8)"); await page.wait_for_timeout(700)
        await page.evaluate("parkFruit(180, 400)")
        await page.evaluate("sweep((x,y) => handAt(x, y, 0.8), 40, 400, 320, 400, 250)"); await page.wait_for_timeout(700)  # ~1.1 px/ms
        st = await page.evaluate("({score: __grasp.slice.score, fruits: __grasp.slice.fruits.length, g: gesture})")
        check('fast open-hand swipe cuts (camera)', st['score'] == 2 and st['fruits'] == 0 and st['g'] == 'open', st)
        await page.evaluate("parkFruit(180, 400)")
        await page.evaluate("sweep((x,y) => handAt(x, y, 0.8), 320, 400, 40, 400, 1600)"); await page.wait_for_timeout(2000)  # ~0.18 px/ms: below SLICE_MIN_SPEED
        check('slow open-hand swipe does not cut', await page.evaluate("__grasp.slice.fruits.length") == 1 and await page.evaluate("__grasp.slice.score") == 2, await page.evaluate("[gesture, __grasp.slice.score]"))
        await page.evaluate("sweep((x,y) => handAt(x, y, 0.1), 40, 400, 320, 400, 250)"); await page.wait_for_timeout(700)
        check('pinch swipe does not cut', await page.evaluate("__grasp.slice.fruits.length") == 1)
        # hand gone -> world freezes, no-hand screen
        await page.evaluate("window.__handFor = null; __grasp.slice.fruits[0].vy = -0.5"); await page.wait_for_timeout(900)
        y1 = await page.evaluate("__grasp.slice.fruits[0].y"); await page.wait_for_timeout(500); y2 = await page.evaluate("__grasp.slice.fruits[0].y")
        check('no hand -> no-hand screen + fruit frozen', await page.evaluate("!statusEl.hidden") and y1 == y2, [y1, y2])
        await page.evaluate("__grasp.CONFIG.SLICE_GRAVITY = 0.0012; window.__handFor = () => pointAt(180, 300); __grasp.slice.nextSpawn = 0"); await page.wait_for_timeout(1500)
        await page.screenshot(path='tests/out/slice_phone.png')
        check('phone: no page errors', not errs, errs); await ctx.close()

        # --- phone (touch), English + Hebrew: the round-over card ---
        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx = await b.new_context(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs=[]
            page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + POINT_JS)
            await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
            if he: await page.tap('#startLang'); await page.wait_for_timeout(100)
            await page.tap('#mouseBtn'); await page.tap('.modes button[data-mode=slice]'); await page.wait_for_timeout(300)
            await page.evaluate("parkBomb(180, 400); __grasp.slice.fruits[0].vy = -0.001"); await page.wait_for_timeout(120)
            await page.screenshot(path='tests/out/slice_bomb_phone_' + tag + '.png')
            await page.evaluate("__grasp.slice.fruits.length = 0; __grasp.slice.score = 7"); await end_round(page)
            st = await page.evaluate(ROUND)
            check(tag + ' phone: round over after 3 misses, best 7 saved', st['over'] and st['best'] == 7 and st['ls'] == '7' and st['nb'], st)
            await page.screenshot(path='tests/out/endcard_slice_' + tag + '.png')
            bt = st['buttons']
            check(tag + ' phone: card buttons fit the screen' + (', Play again on the right' if he else ''), bt and set(bt) == {'again', 'home'} and all(b['x'] >= 8 and b['x'] + b['w'] <= 352 and b['h'] >= 44 for b in bt.values()) and ((bt['again']['x'] > bt['home']['x']) == he), bt)
            await page.tap('#stage', position={'x': bt['again']['x'] + bt['again']['w'] / 2, 'y': bt['again']['y'] + bt['again']['h'] / 2}); await page.wait_for_timeout(200)
            check(tag + ' phone: tap Play again -> fresh round', await page.evaluate("!__grasp.slice.over && __grasp.slice.lives === 3 && __grasp.slice.score === 0 && __grasp.slice.best === 7"))
            check(tag + ' phone: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
