exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
S = "__grasp.strike"
STATE = "(() => { const s = " + S + ", b = s.ball; return { z: b ? b.z : null, x: b ? b.x : null, y: b ? b.y : null, dir: b ? b.dir : 0, sup: !!(b && b.super), speed: s.speed, pace: s.pace, lives: s.lives, score: s.score, over: s.over, power: s.power, hits: s.hits, misses: s.misses, serves: s.serves, bounces: s.bounces, best: s.best }; })()"
PIX = "((x, y) => { const d = ctx.getImageData(Math.round(x * DPR), Math.round(y * DPR), 1, 1).data; return [d[0], d[1], d[2]]; })"
ROWS = "new Set([...document.querySelectorAll('.modes button')].map(b => Math.round(b.getBoundingClientRect().top / 20))).size"  # the pressed card is lifted 2 px
FITS = "(() => { const bs = [...document.querySelectorAll('.modes button')]; const a = document.querySelector('#start a.link').getBoundingClientRect(); return bs.length === 5 && bs.every(b => b.scrollWidth <= b.clientWidth + 1 && b.getBoundingClientRect().right <= innerWidth && b.getBoundingClientRect().left >= 0) && a.bottom <= innerHeight && a.width > 0; })()"
TOUCH_JS = """
window.touchAt = (t, x, y) => document.getElementById('stage').dispatchEvent(new PointerEvent(t, { pointerId: 7, pointerType: 'touch', isPrimary: true, clientX: x, clientY: y, bubbles: true, cancelable: true, button: 0, buttons: 1 }));
"""
# park an incoming ball at HIT_Z right under the cursor at (x, y); dx px of hand travel in the last ~60 ms sets the hand speed
def hit_js(x, y, dx=0):
    return f"(() => {{ const now = performance.now(); if ({dx}) {{ cursor.history.length = 0; cursor.history.push({{ t: now - 60, x: {x} - {dx}, y: {y} }}, {{ t: now, x: {x}, y: {y} }}); }} {S}.setBallZ(__grasp.CONFIG.STRIKE_HIT_Z, {x}, {y}); }})()"
async def miss(page):
    await page.evaluate(f"{S}.setBallZ(4, innerWidth * 0.5, innerHeight * 0.5)"); await page.wait_for_timeout(250)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
        # --- mouse, desktop ---
        ctx = await b.new_context(viewport={'width':1280,'height':800}); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT)
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
        check('desktop: 5 mode cards in one row fit', await page.evaluate(FITS) and await page.evaluate(ROWS) == 1)
        await page.click('.modes button[data-mode=strike]')
        check('menu shows strike selected + description', await page.evaluate("document.querySelector('[data-mode=strike]').getAttribute('aria-pressed')==='true' && $('modeDesc').textContent.includes('corridor')"))
        check('mode cycle includes strike', await page.evaluate("MODE_NEXT.busy === 'strike' && MODE_NEXT.strike === 'sandbox'"))
        cfg = await page.evaluate("({ zf: __grasp.CONFIG.STRIKE_Z_FAR, hz: __grasp.CONFIG.STRIKE_HIT_Z, base: __grasp.CONFIG.STRIKE_BASE_SPEED, max: __grasp.CONFIG.STRIKE_MAX_SPEED, lives: __grasp.CONFIG.STRIKE_LIVES, sup: __grasp.CONFIG.STRIKE_SUPER_SPEED })")
        check('CONFIG has the strike constants', all(v > 0 for v in cfg.values()) and cfg['hz'] < cfg['zf'] and cfg['base'] < cfg['max'], cfg)
        await page.click('#mouseBtn'); await page.wait_for_timeout(900)
        st = await page.evaluate(STATE)
        check('strike mode starts: ball served from the far end, 3 lives, score 0', await page.evaluate("gameMode") == 'strike' and st['z'] is not None and st['z'] > cfg['zf'] * 0.7 and st['lives'] == cfg['lives'] and st['score'] == 0 and st['dir'] == 1, st)
        check('strike.walls list exists for step 2', await page.evaluate(f"Array.isArray({S}.walls)"))
        z0 = st['z']; await page.wait_for_timeout(250); z1 = await page.evaluate(f"{S}.ball.z")
        check('ball approaches: z decreases at the base speed', z0 - z1 > 150 and z0 - z1 < 600, [z0, z1])
        # corridor + ball pixels (the mouse is present, parked low so the hand sprite stays clear of the probes)
        await page.mouse.move(640, 600); await page.wait_for_timeout(150)
        await page.evaluate(f"{S}.setBallZ(900, 200, 700)"); await page.wait_for_timeout(50)
        floor = await page.evaluate(PIX + "(640, 796)"); far = await page.evaluate(PIX + "(640, 368)"); wall = await page.evaluate(PIX + "(6, 400)")
        check('corridor drawn: bright floor near the player, dark fog at the vanishing point, side wall', floor[2] > floor[0] and floor[2] > 60 and sum(far) < sum(floor) and wall[2] > wall[0], [floor, far, wall])
        await page.evaluate(f"{S}.setBallZ(900, 640, 380)"); await page.wait_for_timeout(50)
        bpx = await page.evaluate(PIX + "(640, 380)")
        check('ball drawn as a coral sphere', bpx[0] > 170 and bpx[0] > bpx[2] + 40, bpx)
        await page.screenshot(path='tests/out/strike_desktop.png')
        # hit: cursor parked on the ball, hand still = soft
        await page.evaluate(hit_js(640, 600)); await page.wait_for_timeout(120)
        st = await page.evaluate(STATE)
        check('cursor on the ball at HIT_Z: hit, +1, direction reversed', st['dir'] == -1 and st['score'] == 1 and st['hits'] == 1 and st['z'] > 0, st)
        check('still hand = soft tier, slow return', st['power'] == 'soft' and st['speed'] < st['pace'], st)
        check('hit floater shows the tier', await page.evaluate(f"{S}.floaters.some(f => f.text.includes('Soft'))"))
        pace0 = st['pace']
        await page.wait_for_function(f"{S}.bounces >= 1", timeout=8000)
        st = await page.evaluate(STATE)
        check('returned ball bounces off the far end and comes back 5% faster', st['dir'] == 1 and st['z'] > cfg['zf'] * 0.9 and abs(st['pace'] - pace0 * 1.05) < 1e-6 and st['speed'] == st['pace'], [st, pace0])
        # power tiers from the hand speed over the last 100 ms
        await page.mouse.move(640, 400); await page.wait_for_timeout(120)
        for dx, tier, pts in [(60, 'medium', 2), (130, 'hard', 3), (320, 'super', 6)]:
            s0 = (await page.evaluate(STATE))['score']
            await page.evaluate(hit_js(640, 400, dx)); await page.wait_for_timeout(120)
            st = await page.evaluate(STATE)
            check(f'hand speed {dx}px/60ms -> {tier} tier, +{pts}', st['power'] == tier and st['score'] - s0 == pts and st['dir'] == -1, [st, s0])
        check('SUPER: ball glows and flies back fast', st['sup'] and st['speed'] > st['pace'] * 1.5, st)
        check('faster hand = faster return', await page.evaluate(f"{S}.lastHit.pw") > 0.99)
        await page.wait_for_timeout(60); await page.screenshot(path='tests/out/strike_super.png')
        # lateral direction from where the ball was hit
        await page.evaluate(hit_js(600, 400)); await page.mouse.move(560, 400); await page.wait_for_timeout(30)
        await page.evaluate(hit_js(600, 400)); await page.wait_for_timeout(100)
        check('hit on the left side of the ball sends it right', await page.evaluate(f"{S}.ball.dir === -1 && {S}.ball.vx > 0"), await page.evaluate(STATE))
        # miss
        await page.mouse.move(100, 100); await page.wait_for_timeout(100)
        await miss(page)
        st = await page.evaluate(STATE)
        check('ball passes the cursor: miss, one life lost, red flash', st['lives'] == cfg['lives'] - 1 and st['misses'] == 1 and st['z'] is None and await page.evaluate(f"performance.now() - {S}.flash < 600"), st)
        await page.wait_for_timeout(900)
        st = await page.evaluate(STATE)
        check('new serve ~800 ms after a miss', st['z'] is not None and st['z'] > cfg['zf'] * 0.7 and st['serves'] == 2, st)
        sc = st['score']
        await miss(page); await page.wait_for_timeout(900); await miss(page)
        st = await page.evaluate(STATE); best = await page.evaluate("localStorage.getItem('strikeBest')")
        check('three misses: round over, best saved', st['over'] and st['lives'] == 0 and st['best'] == sc and best == str(sc), [st, best])
        await page.wait_for_timeout(1100); await page.screenshot(path='tests/out/strike_over.png')
        await page.mouse.move(300, 300); await page.mouse.down(); await page.mouse.up(); await page.wait_for_timeout(200)
        st = await page.evaluate(STATE)
        check('tap restarts a fresh round, best kept', not st['over'] and st['lives'] == cfg['lives'] and st['score'] == 0 and st['best'] == sc, st)
        await page.wait_for_timeout(700)
        await page.mouse.move(640, 400); await page.wait_for_timeout(100); await page.evaluate(hit_js(640, 400)); await page.wait_for_timeout(120)
        check('reset button restarts', await page.evaluate(f"{S}.score") > 0 and (await page.click('#resetBtn') or True) and await page.evaluate(f"{S}.score === 0 && {S}.lives === {cfg['lives']} && !{S}.over"))
        await page.click('#hudBtn'); await page.wait_for_timeout(700)
        check('HUD shows strike + lives', 'strike' in await page.inner_text('#hud') and 'lives' in await page.inner_text('#hud'))
        await page.evaluate("__grasp.setGameMode('sandbox')"); await page.wait_for_timeout(300)
        check('switching back to sandbox restores objects', await page.evaluate("gameMode === 'sandbox' && bodies.length === 10"))
        check('mouse: no page errors', not errs, errs); await ctx.close()

        # --- camera stub, desktop: an open hand on the ball hits it ---
        ctx = await b.new_context(permissions=['camera'], viewport={'width':1280,'height':800}); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + HAND_JS)
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
        await page.click('.modes button[data-mode=strike]'); await page.click('#camBtn')
        await page.wait_for_function("mode === 'camera'", timeout=15000)
        await page.evaluate("window.__handFor = () => handAt(640, 400, 0.8)"); await page.wait_for_timeout(900)
        cur = await page.evaluate("[gesture, cursor.x, cursor.y, cursor.present]")
        check('camera: open hand tracked as the cursor', cur[0] == 'open' and cur[3] and abs(cur[1] - 640) < 30 and abs(cur[2] - 400) < 30, cur)
        await page.evaluate(f"{S}.setBallZ(__grasp.CONFIG.STRIKE_HIT_Z, cursor.x, cursor.y)"); await page.wait_for_timeout(120)
        st = await page.evaluate(STATE)
        check('camera: open hand at the ball position hits it', st['dir'] == -1 and st['score'] >= 1, st)
        await page.wait_for_timeout(40); await page.screenshot(path='tests/out/strike_camera.png')
        await page.evaluate("window.__handFor = () => null"); await page.wait_for_timeout(700)
        z0 = await page.evaluate(f"{S}.ball && {S}.ball.z"); await page.wait_for_timeout(300); z1 = await page.evaluate(f"{S}.ball && {S}.ball.z")
        check('camera: the ball waits while the hand is missing', await page.evaluate("noHandShown") and z0 == z1, [z0, z1])
        check('camera: no page errors', not errs, errs); await ctx.close()

        # --- phone (touch), English + Hebrew ---
        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx = await b.new_context(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs=[]
            page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + TOUCH_JS)
            await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
            if he: await page.tap('#startLang'); await page.wait_for_timeout(100)
            rows = await page.evaluate(ROWS)
            check(tag + ' phone: 5 mode cards (3 + 2) and link fit', await page.evaluate(FITS) and rows == 2, rows)
            await page.screenshot(path='tests/out/strike_start_' + tag + '.png')
            await page.tap('.modes button[data-mode=strike]')
            check(tag + ' phone: strike description', await page.evaluate("$('modeDesc').textContent.includes(" + ("'מסדרון'" if he else "'corridor'") + ")"))
            await page.tap('#mouseBtn'); await page.wait_for_timeout(900)
            st = await page.evaluate(STATE)
            check(tag + ' phone: ball served', st['z'] is not None and st['lives'] == 3, st)
            await page.evaluate("touchAt('pointerdown', 180, 360)"); await page.wait_for_timeout(80)
            await page.evaluate(f"{S}.setBallZ(700, 180, 360)"); await page.wait_for_timeout(50)
            await page.screenshot(path='tests/out/strike_phone_' + tag + '.png')
            await page.evaluate(hit_js(180, 360)); await page.wait_for_timeout(120)
            st = await page.evaluate(STATE)
            check(tag + ' phone: a finger on the ball hits it', st['dir'] == -1 and st['score'] >= 1 and st['lives'] == 3, st)
            await page.evaluate("touchAt('pointerup', 180, 360)"); await page.wait_for_timeout(300)
            for _ in range(3): await miss(page); await page.wait_for_timeout(900)
            check(tag + ' phone: round over after 3 misses', await page.evaluate(f"{S}.over"))
            await page.wait_for_timeout(300); await page.screenshot(path='tests/out/strike_over_' + tag + '.png')
            check(tag + ' phone: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
