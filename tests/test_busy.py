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
"""
ARC_JS = """
// pinch at radius r around (cx, cy) and sweep from angle a0 to a1 over ms
window.arcHand = (cx, cy, r, a0, a1, ms) => { const t0 = performance.now(); window.__handFor = () => { const k = Math.min(1, (performance.now() - t0) / ms), a = a0 + (a1 - a0) * k; return handAt(cx + Math.cos(a) * r, cy + Math.sin(a) * r, 0.1); }; };
"""
W = "__grasp.busy.widgets"
def wjs(i): return f"(() => {{ const w = {W}[{i}]; return {{x: w.x, y: w.y, w: w.w, h: w.h, kind: w.kind, color: w.color, on: !!w.state.on, down: !!w.state.down, angle: w.state.angle || 0, detent: w.state.detent || 0}}; }})()"
PIX = "((x, y) => { const d = ctx.getImageData(Math.round(x * DPR), Math.round(y * DPR), 1, 1).data; return [d[0], d[1], d[2]]; })"
INSIDE = "(() => { const b = __grasp.busy.board; return " + W + ".every(w => w.x - w.w / 2 >= b.x && w.x + w.w / 2 <= b.x + b.w && w.y - w.h / 2 >= b.y && w.y + w.h / 2 <= b.y + b.h && w.x + w.w / 2 <= innerWidth && w.y + w.h / 2 <= innerHeight); })()"
OVERLAP = "(() => { const ws = " + W + "; for (let i = 0; i < ws.length; i++) for (let j = i + 1; j < ws.length; j++) { const a = ws[i], b = ws[j]; if (Math.abs(a.x - b.x) < (a.w + b.w) / 2 - 0.5 && Math.abs(a.y - b.y) < (a.h + b.h) / 2 - 0.5) return false; } return true; })()"

async def drag_arc(page, cx, cy, r, a0, a1, steps=12, wait=30):
    import math
    await page.mouse.move(cx + math.cos(a0) * r, cy + math.sin(a0) * r); await page.wait_for_timeout(60); await page.mouse.down(); await page.wait_for_timeout(60)
    for i in range(1, steps + 1):
        a = a0 + (a1 - a0) * i / steps
        await page.mouse.move(cx + math.cos(a) * r, cy + math.sin(a) * r); await page.wait_for_timeout(wait)
    await page.mouse.up(); await page.wait_for_timeout(250)

async def main():
    import math
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
        # --- mouse, desktop ---
        ctx = await b.new_context(viewport={'width':1280,'height':800}); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT)
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
        await page.click('.modes button[data-mode=busy]')
        check('menu shows busy board selected + description', await page.evaluate("document.querySelector('[data-mode=busy]').getAttribute('aria-pressed')==='true' && $('modeDesc').textContent.includes('busy board')"))
        check('mode cycle includes busy', await page.evaluate("MODE_NEXT.smash === 'busy' && MODE_NEXT.busy === 'sandbox'"))
        await page.click('#mouseBtn'); await page.wait_for_timeout(500)
        kinds = await page.evaluate("(() => { const k = {}; for (const w of " + W + ") k[w.kind] = (k[w.kind] || 0) + 1; return k; })()")
        check('busy mode: 4 switches, 4 buttons, 2 knobs', await page.evaluate("gameMode") == 'busy' and kinds == {'switch': 4, 'button': 4, 'knob': 2}, kinds)
        check('desktop: 4 columns, widgets inside the board, none overlapping', await page.evaluate("(() => { const ws = " + W + "; return new Set(ws.map(w => Math.round(w.x))).size === 4; })()") and await page.evaluate(INSIDE) and await page.evaluate(OVERLAP))
        check('widgets are big touch targets (>= 64 px)', await page.evaluate("Math.min(..." + W + ".map(w => Math.min(w.w, w.h)))") >= 64)
        bd = await page.evaluate("__grasp.busy.board")
        pix = await page.evaluate(PIX + f"({bd['x'] + 6}, {bd['y'] + bd['h'] / 2})")
        check('board draws warm wood', pix[0] > 100 and pix[0] > pix[1] > pix[2], pix)
        check('board sprite is cached', await page.evaluate("[...SPRITES.keys()].some(k => k.startsWith('busy|board|'))"))
        check('no score/timer in busy mode', await page.evaluate("!__grasp.busy.score && !__grasp.busy.endAt"))
        # switch
        s0 = await page.evaluate(wjs(0))
        await page.mouse.move(s0['x'], s0['y']); await page.wait_for_timeout(120)
        check('open hover highlights the widget', await page.evaluate("__grasp.busy.hover === " + W + "[0] && gesture === 'open'"))
        await page.mouse.click(s0['x'], s0['y']); await page.wait_for_timeout(450)
        st = await page.evaluate(wjs(0)); snd = await page.evaluate("__grasp.busy.sounds")
        led = await page.evaluate("(() => { const l = " + W + "[0].ledPos(); return " + PIX + "(l.x, l.y); })()")
        check('click flips the switch on + click sound', st['on'] and snd['click'] == 1, [st, snd])
        check('LED lights up when on', max(led) > 170, led)
        check('lever swung to the on side', await page.evaluate(W + "[0].state.pos") > 0.5)
        await page.mouse.click(s0['x'], s0['y']); await page.wait_for_timeout(450)
        st = await page.evaluate(wjs(0)); led2 = await page.evaluate("(() => { const l = " + W + "[0].ledPos(); return " + PIX + "(l.x, l.y); })()")
        check('second click flips it off, LED dark', not st['on'] and await page.evaluate("__grasp.busy.sounds.click") == 2 and max(led2) < max(led) - 40, [st, led, led2])
        # button
        b0 = await page.evaluate(wjs(4))
        await page.mouse.move(b0['x'], b0['y']); await page.wait_for_timeout(60); await page.mouse.down(); await page.wait_for_timeout(120)
        st = await page.evaluate(wjs(4)); snd = await page.evaluate("__grasp.busy.sounds")
        check('press depresses the button + plays a note + ring', b0['kind'] == 'button' and st['down'] and snd['note'] == 1 and await page.evaluate("rings.length") >= 1, [st, snd])
        await page.wait_for_timeout(400)
        check('holding keeps it down', await page.evaluate(W + "[4].state.down && " + W + "[4].state.k > 0.9"))
        await page.screenshot(path='tests/out/busy_press.png')
        await page.mouse.up(); await page.wait_for_timeout(150)
        check('release lets it up, no extra note', not (await page.evaluate(wjs(4)))['down'] and await page.evaluate("__grasp.busy.sounds.note") == 1)
        # sweep across the four buttons while pressing: each one sounds
        await page.mouse.move(b0['x'] - 20, b0['y']); await page.mouse.down()
        for i in range(4, 8):
            w = await page.evaluate(wjs(i)); await page.mouse.move(w['x'], w['y']); await page.wait_for_timeout(80)
        await page.mouse.up(); await page.wait_for_timeout(100)
        check('sweeping a press across buttons plays each', await page.evaluate("__grasp.busy.sounds.note") >= 4, await page.evaluate("__grasp.busy.sounds"))
        notes = await page.evaluate("[..." + W + ".filter(w => w.kind === 'button')].map(w => Math.round(w.freq)).sort((a, b) => a - b)")
        check('buttons are C4 E4 G4 C5', notes == [262, 330, 392, 523], notes)
        # knob: drag around its centre
        k0 = await page.evaluate(wjs(8)); r = k0['w'] * 0.32
        check('knob starts at the left stop', k0['kind'] == 'knob' and abs(k0['angle'] + math.pi * 0.75) < 0.01, k0)
        await drag_arc(page, k0['x'], k0['y'], r, 0, math.pi / 2)
        st = await page.evaluate(wjs(8)); snd = await page.evaluate("__grasp.busy.sounds")
        check('drag rotates the knob ~90 degrees', abs(st['angle'] - (-math.pi * 0.75 + math.pi / 2)) < 0.12, st)
        check('passes 3 detents with ratchet ticks', st['detent'] == 3 and snd['ratchet'] == 3, [st, snd])
        check('released knob snaps onto a detent', abs((st['angle'] + math.pi * 0.75) / (math.pi / 6) - 3) < 0.05, st['angle'])
        await drag_arc(page, k0['x'], k0['y'], r, math.pi / 2, math.pi / 2 - 4)  # far past the end stop: clamps
        st = await page.evaluate(wjs(8))
        check('turning past the stop clamps at the left end', abs(st['angle'] + math.pi * 0.75) < 0.01 and st['detent'] == 0, st)
        await page.mouse.click(k0['x'], k0['y']); await page.wait_for_timeout(300)
        # a click without a drag is a grab + drop, not a step
        check('click on a knob does not turn it', (await page.evaluate(wjs(8)))['detent'] == 0)
        await page.mouse.move(k0['x'] - 400, k0['y'] - 200); await page.wait_for_timeout(100)
        await page.screenshot(path='tests/out/busy_desktop.png')
        # reset re-randomises colours
        seed0 = await page.evaluate("__grasp.busy.seed"); cols0 = await page.evaluate(W + ".map(w => w.color).join()")
        await page.evaluate(W + "[1].press(performance.now())")
        await page.click('#resetBtn'); await page.wait_for_timeout(200)
        check('reset re-randomises the board and clears states', await page.evaluate("__grasp.busy.seed") != seed0 and await page.evaluate(W + ".length === 10 && " + W + ".every(w => !w.state.on && !w.state.down)"), [seed0, cols0])
        check('reset keeps everything inside the board', await page.evaluate(INSIDE) and await page.evaluate(OVERLAP))
        await page.click('#hudBtn'); await page.wait_for_timeout(700)
        check('HUD shows busy board', 'busy' in await page.inner_text('#hud'))
        await page.evaluate("__grasp.setGameMode('sandbox')"); await page.wait_for_timeout(300)
        check('switching back to sandbox restores objects', await page.evaluate("gameMode === 'sandbox' && bodies.length === 10"))
        check('mouse: no page errors', not errs, errs); await ctx.close()

        # --- camera stub, desktop: pinch + turn a knob, point at a button ---
        ctx = await b.new_context(permissions=['camera'], viewport={'width':1280,'height':800}); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + HAND_JS + POINT_JS + ARC_JS)
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
        await page.click('.modes button[data-mode=busy]'); await page.click('#camBtn')
        await page.wait_for_function("mode === 'camera'", timeout=15000)
        k0 = await page.evaluate(wjs(9)); r = k0['w'] * 0.32
        await page.evaluate(f"window.__handFor = () => handAt({k0['x'] + r}, {k0['y']}, 0.8)"); await page.wait_for_timeout(700)
        check('camera: open hand hovers the knob', await page.evaluate("gesture === 'open' && __grasp.busy.hover === " + W + "[9]"), await page.evaluate("[gesture, __grasp.state.cursor]"))
        await page.evaluate(f"window.__handFor = () => handAt({k0['x'] + r}, {k0['y']}, 0.1)"); await page.wait_for_timeout(400)
        check('camera: pinch grabs the knob', await page.evaluate("gesture === 'pinch' && __grasp.busy.grabbed === " + W + "[9]"))
        await page.evaluate(f"arcHand({k0['x']}, {k0['y']}, {r}, 0, {math.pi / 2}, 500)"); await page.wait_for_timeout(900)
        st = await page.evaluate(wjs(9)); snd = await page.evaluate("__grasp.busy.sounds")
        check('camera: turning the pinched hand rotates the knob past detents', st['detent'] >= 2 and st['angle'] > -math.pi * 0.75 + 0.6 and snd['ratchet'] >= 2, [st, snd])
        await page.screenshot(path='tests/out/busy_camera.png')
        await page.evaluate(f"window.__handFor = () => handAt({k0['x']}, {k0['y'] + r}, 0.8)"); await page.wait_for_timeout(400)
        check('camera: opening the hand lets go', await page.evaluate("__grasp.busy.grabbed === null && !" + W + "[9].state.held"))
        b0 = await page.evaluate(wjs(5))
        await page.evaluate(f"window.__handFor = () => pointAt({b0['x']}, {b0['y']})"); await page.wait_for_timeout(700)
        check('camera: pointing at a button presses it', await page.evaluate("gesture === 'point' && " + W + "[5].state.down && __grasp.busy.sounds.note === 1"), await page.evaluate("[gesture, __grasp.busy.sounds]"))
        s0 = await page.evaluate(wjs(1))
        await page.evaluate(f"window.__handFor = () => pointAt({s0['x']}, {s0['y']})"); await page.wait_for_timeout(500)
        check('camera: pointing at a switch flips it and releases the button', await page.evaluate(W + "[1].state.on && !" + W + "[5].state.down"))
        await page.evaluate("window.__handFor = null"); await page.wait_for_timeout(600)
        check('camera: hand lost releases everything', await page.evaluate("__grasp.busy.active === null && __grasp.busy.hover === null"))
        check('camera: no page errors', not errs, errs); await ctx.close()

        # --- phone (touch), English + Hebrew ---
        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx = await b.new_context(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs=[]
            page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT)
            await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
            if he: await page.tap('#startLang'); await page.wait_for_timeout(100)
            fits = await page.evaluate("(() => { const r = [...document.querySelectorAll('.modes button')].map(b => ({w: b.scrollWidth <= b.clientWidth + 1, in: b.getBoundingClientRect().right <= innerWidth})); const a = document.querySelector('#start a.link').getBoundingClientRect(); return r.length === 4 && r.every(x => x.w && x.in) && a.bottom <= innerHeight && a.width > 0; })()")
            check(tag + ' phone: 4 mode cards and link fit', fits)
            await page.tap('.modes button[data-mode=busy]')
            check(tag + ' phone: busy card label', await page.inner_text('.modes button[data-mode=busy]') == ('לוח עסוק' if he else 'Busy Board'))
            await page.screenshot(path='tests/out/busy_start' + ('_he' if he else '') + '.png')
            await page.tap('#mouseBtn'); await page.wait_for_timeout(500)
            hint = await page.inner_text('#hint')
            check(tag + ' phone: touch hint', ('הקישו' in hint) if he else ('Tap' in hint), hint)
            check(tag + ' phone: 2 columns, all widgets on screen, none overlapping', await page.evaluate("new Set(" + W + ".map(w => Math.round(w.x))).size === 2") and await page.evaluate(INSIDE) and await page.evaluate(OVERLAP))
            check(tag + ' phone: board clears the top buttons', await page.evaluate("(() => { const c = document.querySelector('.chrome').getBoundingClientRect(); return __grasp.busy.board.y >= c.bottom; })()"))
            s0 = await page.evaluate(wjs(2)); await page.tap('#stage', position={'x': s0['x'], 'y': s0['y']}); await page.wait_for_timeout(300)
            check(tag + ' phone: tap flips a switch', (await page.evaluate(wjs(2)))['on'])
            k0 = await page.evaluate(wjs(8)); r = k0['w'] * 0.3
            await page.evaluate("(() => { const w = " + W + "[9]; w.turnTo(0); w.state.detent = Math.round(Math.PI * 0.75 / (Math.PI / 6)); })()")
            await page.wait_for_timeout(600)
            await page.screenshot(path='tests/out/busy_phone' + ('_he' if he else '') + '.png')
            check(tag + ' phone: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
