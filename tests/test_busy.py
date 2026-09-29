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
LINE_JS = """
// pinched hand sweeping in a straight line from (x0,y0) to (x1,y1) over ms
window.lineHand = (x0, y0, x1, y1, ms) => { const t0 = performance.now(); window.__handFor = () => { const k = Math.min(1, (performance.now() - t0) / ms); return handAt(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, 0.1); }; };
"""
TOUCH_JS = """
// one-finger drag as real touch pointer events on the canvas (Playwright has no touch drag)
window.touchDrag = async (x0, y0, x1, y1, steps, ms) => { const c = document.getElementById('stage');
  const ev = (t, x, y) => c.dispatchEvent(new PointerEvent(t, { pointerId: 7, pointerType: 'touch', isPrimary: true, clientX: x, clientY: y, bubbles: true, cancelable: true, button: 0, buttons: 1 }));
  ev('pointerdown', x0, y0);
  for (let i = 1; i <= steps; i++) { await new Promise((r) => setTimeout(r, ms)); ev('pointermove', x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps); }
  ev('pointerup', x1, y1); };
"""
W = "__grasp.busy.widgets"
KINDS = {'switch': 4, 'button': 4, 'knob': 2, 'slider': 2, 'zipper': 1, 'door': 1}
SURPRISES = ['sun', 'cat', 'star', 'rainbow']
def wjs(i): return f"(() => {{ const w = {W}[{i}]; return {{x: w.x, y: w.y, w: w.w, h: w.h, hw: w.hw, hh: w.hh, kind: w.kind, color: w.color, on: !!w.state.on, down: !!w.state.down, angle: w.state.angle || 0, detent: w.state.detent || 0, st: JSON.parse(JSON.stringify(w.state))}}; }})()"
HANDLE = lambda i: f"(() => {{ const w = {W}[{i}], g = w.geom(), tr = g.len - g.hw; return w.loc(-tr / 2 + w.state.v * tr, -g.thick * 0.12); }})()"  # slider handle centre on screen
COLS = lambda n: "(() => { const ws = " + W + ".filter(w => w.w === w.h && w.w === w.cell); return new Set(ws.map(w => Math.round(w.x))).size === " + str(n) + "; })()"  # 1x1 widgets sit in n columns
# on a scrolling board: every widget inside the board horizontally, the ones on screen not overlapping, n of them fully visible
VISIBLE = lambda n: "(() => { const b = __grasp.busy.board, ws = " + W + "; const vis = ws.filter(w => w.y + w.h / 2 > 0 && w.y - w.h / 2 < innerHeight); return ws.every(w => w.x - w.w / 2 >= b.x && w.x + w.w / 2 <= b.x + b.w && w.x + w.w / 2 <= innerWidth) && ws.filter(w => w.y - w.h / 2 >= 0 && w.y + w.h / 2 <= innerHeight).length >= " + str(n) + "; })()"
PIX = "((x, y) => { const d = ctx.getImageData(Math.round(x * DPR), Math.round(y * DPR), 1, 1).data; return [d[0], d[1], d[2]]; })"
INSIDE = "(() => { const b = __grasp.busy.board; return " + W + ".every(w => w.x - w.w / 2 >= b.x && w.x + w.w / 2 <= b.x + b.w && w.y - w.h / 2 >= b.y && w.y + w.h / 2 <= b.y + b.h && w.x + w.w / 2 <= innerWidth && w.y + w.h / 2 <= innerHeight); })()"
OVERLAP = "(() => { const ws = " + W + "; for (let i = 0; i < ws.length; i++) for (let j = i + 1; j < ws.length; j++) { const a = ws[i], b = ws[j]; if (Math.abs(a.x - b.x) < (a.w + b.w) / 2 - 0.5 && Math.abs(a.y - b.y) < (a.h + b.h) / 2 - 0.5) return false; } return true; })()"

async def drag_line(page, x0, y0, x1, y1, steps=10, wait=30, mid=None):
    await page.mouse.move(x0, y0); await page.wait_for_timeout(60); await page.mouse.down(); await page.wait_for_timeout(60)
    out = None
    for i in range(1, steps + 1):
        await page.mouse.move(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps); await page.wait_for_timeout(wait)
        if mid and i == steps // 2: out = await page.evaluate(mid)
    await page.mouse.up(); await page.wait_for_timeout(250)
    return out

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
        check('busy mode: 4 switches, 4 buttons, 2 knobs, 2 sliders, zipper, door', await page.evaluate("gameMode") == 'busy' and kinds == KINDS, kinds)
        check('desktop: 4 columns, widgets inside the board, none overlapping, no scrolling needed', await page.evaluate(COLS(4)) and await page.evaluate(INSIDE) and await page.evaluate(OVERLAP) and await page.evaluate("__grasp.busy.maxScroll") == 0)
        check('widgets are big touch targets (>= 64 px)', await page.evaluate("Math.min(..." + W + ".map(w => Math.min(w.hw, w.hh)))") >= 64)
        check('sliders: one horizontal, one vertical, different colours', await page.evaluate("(() => { const [a, b] = " + W + ".filter(w => w.kind === 'slider'); return !a.vertical && b.vertical && a.color !== b.color && a.w > a.h && b.h > b.w; })()"))
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
        # slider: drag the handle along the track; a tone follows while held
        sl = await page.evaluate(wjs(10)); hp = await page.evaluate(HANDLE(10)); tr = await page.evaluate("(() => { const g = " + W + "[10].geom(); return g.len - g.hw; })()")
        check('horizontal slider starts at 0, handle at the left end', sl['kind'] == 'slider' and sl['st']['v'] == 0 and hp['x'] < sl['x'] - tr * 0.4, [sl['st'], hp])
        mid = await drag_line(page, hp['x'], hp['y'], hp['x'] + tr * 0.6, hp['y'], mid="({v: " + W + "[10].state.v, tone: {...__grasp.busy.tone}, held: " + W + "[10].state.held})")
        sl = await page.evaluate(wjs(10)); snd = await page.evaluate("__grasp.busy.sounds")
        check('slider drag moves the handle (~0.6) and starts one tone', 0.5 < sl['st']['v'] < 0.7 and snd['tone'] == 1, [sl['st'], snd])
        check('while dragging: tone active, pitch 220->880 follows the value', mid['held'] and mid['tone']['active'] and abs(mid['tone']['f'] - 220 * 4 ** mid['v']) < 1 and 220 < mid['tone']['f'] < 880, mid)
        check('release stops the tone', not sl['st']['held'] and not await page.evaluate("__grasp.busy.tone.active"))
        led = await page.evaluate("(() => { const w = " + W + "[10], g = w.geom(), tr = g.len - g.hw; return [0.5 / 8, 7.5 / 8].map(k => { const q = w.loc(-tr / 2 + k * tr, g.thick * 0.3); return " + PIX + "(q.x, q.y); }); })()")
        check('LED strip: first LED lit, last LED dark', max(led[0]) > 170 and max(led[1]) < max(led[0]) - 40, led)
        sv = await page.evaluate(wjs(11)); hp = await page.evaluate(HANDLE(11)); tr = await page.evaluate("(() => { const g = " + W + "[11].geom(); return g.len - g.hw; })()")
        await drag_line(page, hp['x'], hp['y'], hp['x'], hp['y'] - tr * 0.5)
        sv = await page.evaluate(wjs(11))
        check('vertical slider: dragging up raises the value', 0.4 < sv['st']['v'] < 0.6 and await page.evaluate("__grasp.busy.sounds.tone") == 2, sv['st'])
        await drag_line(page, hp['x'], hp['y'] - tr * 0.5, hp['x'], hp['y'] + 500)  # far past the end: clamps
        check('slider clamps at the bottom end', (await page.evaluate(wjs(11)))['st']['v'] == 0)
        # zipper: drag the pull-tab to open, teeth split behind it
        zp = await page.evaluate(wjs(12)); L = await page.evaluate(W + "[12].len()"); tx = await page.evaluate(W + "[12].tabX()")
        check('zipper is wide and starts closed', zp['kind'] == 'zipper' and zp['w'] >= 4 * zp['h'] - 1 and zp['st']['v'] == 0 and await page.evaluate(W + "[12].gap(" + W + "[12].x - " + str(L) + " / 2 + 6)") == 0, zp)
        await drag_line(page, tx, zp['y'], tx + L * 0.5, zp['y'], steps=14, wait=25)
        zp = await page.evaluate(wjs(12)); snd = await page.evaluate("__grasp.busy.sounds"); gap = await page.evaluate(W + "[12].gap(" + W + "[12].x - " + str(L) + " / 2 + 6)")
        check('dragging the tab opens the zipper halfway with a run of zip sounds', 0.4 < zp['st']['v'] < 0.6 and snd['zip'] >= 8 and await page.evaluate(W + "[12].openLen()") > L * 0.4, [zp['st'], snd])
        check('teeth behind the tab are split apart, ahead of it still joined', gap > 8 and await page.evaluate(W + "[12].gap(" + W + "[12].tabX() + 10)") == 0, gap)
        await page.screenshot(path='tests/out/busy2_desktop_open.png')
        zips = snd['zip']
        await drag_line(page, tx + L * 0.5, zp['y'], tx - 200, zp['y'], steps=14, wait=25)
        zp = await page.evaluate(wjs(12))
        check('dragging back closes it fully (clamped) with more zips', zp['st']['v'] == 0 and await page.evaluate("__grasp.busy.sounds.zip") > zips, zp['st'])
        # latch + door
        dr = await page.evaluate(wjs(13)); g = await page.evaluate(W + "[13].geom()")
        door_y = dr['y'] + dr['h'] * 0.2
        check('door starts closed and locked', dr['kind'] == 'door' and dr['st']['locked'] and not dr['st']['open'] and dr['st']['surprise'] is None, dr['st'])
        await page.mouse.click(dr['x'], door_y); await page.wait_for_timeout(300)
        st = (await page.evaluate(wjs(13)))['st']; snd = await page.evaluate("__grasp.busy.sounds")
        check('poking a locked door only rattles it (thud)', not st['open'] and st['ang'] < 0.01 and snd['thud'] == 1 and not snd.get('squeak'), [st, snd])
        bx = dr['x'] - g['fw'] * 0.11  # bar centre when locked
        await drag_line(page, bx, g['boltY'], bx + g['travel'] * 1.3, g['boltY'])
        st = (await page.evaluate(wjs(13)))['st']; snd = await page.evaluate("__grasp.busy.sounds")
        check('sliding the bolt unlocks: metallic slide + clack', not st['locked'] and st['bolt'] > 0.9 and snd['slide'] >= 3 and snd['clack'] == 1, [st, snd])
        await page.mouse.click(dr['x'], door_y); await page.wait_for_timeout(120)
        st = (await page.evaluate(wjs(13)))['st']; snd = await page.evaluate("__grasp.busy.sounds")
        check('poke swings the unlocked door open with a squeak; a surprise is picked', st['open'] and st['surprise'] in SURPRISES and snd['squeak'] == 1, [st, snd])
        await page.wait_for_timeout(700)
        st = (await page.evaluate(wjs(13)))['st']; snd = await page.evaluate("__grasp.busy.sounds")
        check('door swung open: chime + sparkle burst', st['ang'] > 0.8 and st['celebrated'] and snd['chime'] == 1 and await page.evaluate(W + "[13].sparks.length + particles.length") > 0, [st, snd])
        await page.mouse.move(dr['x'] - 400, dr['y'] - 200); await page.wait_for_timeout(100)
        await page.screenshot(path='tests/out/busy2_door_open.png')
        first = st['surprise']
        await page.mouse.click(dr['x'], door_y); await page.wait_for_timeout(900)
        st = (await page.evaluate(wjs(13)))['st']; snd = await page.evaluate("__grasp.busy.sounds")
        check('poke again closes the door (squeak, then a clack as it shuts)', not st['open'] and st['ang'] < 0.05 and snd['squeak'] == 2 and snd['clack'] == 2, [st, snd])
        seen = {first}
        for _ in range(6):  # the surprise changes between openings
            await page.mouse.click(dr['x'], door_y); await page.wait_for_timeout(60); seen.add((await page.evaluate(wjs(13)))['st']['surprise'])
            await page.mouse.click(dr['x'], door_y); await page.wait_for_timeout(60)
        check('surprise is random each time (never the same twice in a row)', len(seen) >= 2 and seen <= set(SURPRISES), seen)
        await page.wait_for_timeout(600)
        bx = dr['x'] + g['fw'] * 0.19  # bar centre when unlocked
        await drag_line(page, bx, g['boltY'], bx - g['travel'] * 1.3, g['boltY'])
        st = (await page.evaluate(wjs(13)))['st']
        check('bolt slides back to lock', st['locked'] and st['bolt'] < 0.1, st)
        await page.mouse.click(dr['x'], door_y); await page.wait_for_timeout(200)
        check('locked again: poke does not open', not (await page.evaluate(wjs(13)))['st']['open'] and await page.evaluate("__grasp.busy.sounds.thud") == 2)
        await page.mouse.move(k0['x'] - 400, k0['y'] - 200); await page.wait_for_timeout(100)
        await page.screenshot(path='tests/out/busy_desktop.png')
        # reset re-randomises colours
        seed0 = await page.evaluate("__grasp.busy.seed"); cols0 = await page.evaluate(W + ".map(w => w.color).join()")
        await page.evaluate(W + "[1].press(performance.now()); " + W + "[10].grab({x: " + W + "[10].x, y: " + W + "[10].y})")
        check('a grabbed slider keeps its tone on', await page.evaluate("__grasp.busy.tone.active"))
        await page.click('#resetBtn'); await page.wait_for_timeout(200)
        check('reset re-randomises the board and clears states (and the tone)', await page.evaluate("__grasp.busy.seed") != seed0 and await page.evaluate(W + ".length === 14 && " + W + ".every(w => !w.state.on && !w.state.down && !w.state.held && !(w.state.v > 0))") and not await page.evaluate("__grasp.busy.tone.active"), [seed0, cols0])
        check('reset keeps everything inside the board', await page.evaluate(INSIDE) and await page.evaluate(OVERLAP))
        await page.click('#hudBtn'); await page.wait_for_timeout(700)
        check('HUD shows busy board', 'busy' in await page.inner_text('#hud'))
        await page.evaluate("__grasp.setGameMode('sandbox')"); await page.wait_for_timeout(300)
        check('switching back to sandbox restores objects', await page.evaluate("gameMode === 'sandbox' && bodies.length === 10"))
        check('mouse: no page errors', not errs, errs); await ctx.close()

        # --- camera stub, desktop: pinch + turn a knob, point at a button ---
        ctx = await b.new_context(permissions=['camera'], viewport={'width':1280,'height':800}); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + HAND_JS + POINT_JS + ARC_JS + LINE_JS)
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
        # pinch the slider handle and move the hand along the track
        hp = await page.evaluate(HANDLE(10)); tr = await page.evaluate("(() => { const g = " + W + "[10].geom(); return g.len - g.hw; })()")
        await page.evaluate(f"window.__handFor = () => handAt({hp['x']}, {hp['y']}, 0.8)"); await page.wait_for_timeout(400)
        await page.evaluate(f"window.__handFor = () => handAt({hp['x']}, {hp['y']}, 0.1)"); await page.wait_for_timeout(400)
        check('camera: pinch grabs the slider and starts the tone', await page.evaluate("__grasp.busy.grabbed === " + W + "[10] && __grasp.busy.tone.active && __grasp.busy.sounds.tone === 1"))
        await page.evaluate(f"lineHand({hp['x']}, {hp['y']}, {hp['x'] + tr * 0.7}, {hp['y']}, 500)"); await page.wait_for_timeout(800)
        sl = await page.evaluate(wjs(10))
        check('camera: moving the pinched hand slides the handle', 0.55 < sl['st']['v'] < 0.85 and abs(await page.evaluate("__grasp.busy.tone.f") - 220 * 4 ** sl['st']['v']) < 1, sl['st'])
        await page.evaluate(f"window.__handFor = () => handAt({hp['x'] + tr * 0.7}, {hp['y']}, 0.8)"); await page.wait_for_timeout(400)
        check('camera: opening the hand drops the slider and stops the tone', await page.evaluate("__grasp.busy.grabbed === null && !__grasp.busy.tone.active"))
        dr = await page.evaluate(wjs(13))
        await page.evaluate(f"window.__handFor = () => pointAt({dr['x']}, {dr['y'] + dr['h'] * 0.2})"); await page.wait_for_timeout(600)
        check('camera: pointing at the locked door rattles it', await page.evaluate("__grasp.busy.sounds.thud") == 1 and not (await page.evaluate(wjs(13)))['st']['open'])
        await page.evaluate("window.__handFor = null"); await page.wait_for_timeout(600)
        check('camera: hand lost releases everything', await page.evaluate("__grasp.busy.active === null && __grasp.busy.hover === null"))
        check('camera: no page errors', not errs, errs); await ctx.close()

        # --- phone (touch), English + Hebrew ---
        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx = await b.new_context(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs=[]
            page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + TOUCH_JS)
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
            check(tag + ' phone: touch hint mentions dragging the board', ('גררו את הלוח' in hint) if he else ('Drag the board' in hint), hint)
            kinds = await page.evaluate("(() => { const k = {}; for (const w of " + W + ") k[w.kind] = (k[w.kind] || 0) + 1; return k; })()")
            check(tag + ' phone: all 14 widgets, 2 columns, inside the board, none overlapping, 8 fully visible at the top', kinds == KINDS and await page.evaluate(COLS(2)) and await page.evaluate(VISIBLE(8)) and await page.evaluate(OVERLAP), kinds)
            check(tag + ' phone: board is taller than the screen and scrollable; zipper is below the fold', await page.evaluate("__grasp.busy.maxScroll > 300 && __grasp.busy.scroll === 0 && " + W + "[12].y - " + W + "[12].h / 2 > innerHeight"), await page.evaluate("[__grasp.busy.maxScroll, __grasp.busy.board.h]"))
            check(tag + ' phone: widgets are big touch targets (>= 64 px)', await page.evaluate("Math.min(..." + W + ".map(w => Math.min(w.hw, w.hh)))") >= 64)
            check(tag + ' phone: board clears the top buttons', await page.evaluate("(() => { const c = document.querySelector('.chrome').getBoundingClientRect(); return __grasp.busy.board.y >= c.bottom; })()"))
            s0 = await page.evaluate(wjs(2)); await page.tap('#stage', position={'x': s0['x'], 'y': s0['y']}); await page.wait_for_timeout(300)
            check(tag + ' phone: tap flips a switch', (await page.evaluate(wjs(2)))['on'])
            k0 = await page.evaluate(wjs(8)); r = k0['w'] * 0.3
            await page.evaluate("(() => { const w = " + W + "[9]; w.turnTo(0); w.state.detent = Math.round(Math.PI * 0.75 / (Math.PI / 6)); })()")
            await page.wait_for_timeout(600)
            await page.screenshot(path='tests/out/busy_phone' + ('_he' if he else '') + '.png')
            await page.screenshot(path='tests/out/busy2_phone_top' + ('_he' if he else '') + '.png')
            # one-finger drag on empty board (left margin, between the widget cells) scrolls it; the fling carries on after release
            ex = await page.evaluate("__grasp.busy.board.x + 8")
            check(tag + ' phone: the left margin is empty board', not await page.evaluate("(() => { const p = {x: " + str(ex) + ", y: 400}; return " + W + ".some(w => w.hit(p)); })()"))
            await page.evaluate(f"touchDrag({ex}, 460, {ex}, 200, 8, 16)"); s1 = await page.evaluate("__grasp.busy.scroll")
            await page.wait_for_timeout(500); s2 = await page.evaluate("__grasp.busy.scroll")
            check(tag + ' phone: finger drag scrolls the board, then it glides on', 200 < s1 < 360 and s2 > s1 + 20 and await page.evaluate("__grasp.busy.scrollDrag === null"), [s1, s2])
            check(tag + ' phone: widgets moved up with the board, nothing pressed', abs((await page.evaluate(wjs(2)))['y'] - (s0['y'] - s2)) < 1 and await page.evaluate("__grasp.busy.sounds.all") == 2, [s0['y'], s2, (await page.evaluate(wjs(2)))['y'], await page.evaluate("__grasp.busy.sounds")])
            await page.evaluate(f"touchDrag({ex}, 200, {ex}, 700, 6, 16)"); await page.wait_for_timeout(700)
            check(tag + ' phone: dragging down past the top clamps at 0', await page.evaluate("__grasp.busy.scroll") == 0 and await page.evaluate("__grasp.busy.scrollV") == 0)
            await page.mouse.wheel(0, 9000); await page.wait_for_timeout(700)
            check(tag + ' phone: wheel scrolls and clamps at the bottom', await page.evaluate("__grasp.busy.scroll === __grasp.busy.maxScroll"), await page.evaluate("[__grasp.busy.scroll, __grasp.busy.maxScroll]"))
            check(tag + ' phone: scrolled to the bottom, the zipper and door are fully on screen, still no overlaps', await page.evaluate("(() => { const ws = " + W + "; return [12, 13].every(i => ws[i].y - ws[i].h / 2 >= 0 && ws[i].y + ws[i].h / 2 <= innerHeight); })()") and await page.evaluate(VISIBLE(4)) and await page.evaluate(OVERLAP))
            zp = await page.evaluate(wjs(12)); tx = await page.evaluate(W + "[12].tabX()")
            await page.evaluate(f"touchDrag({tx}, {zp['y']}, {tx + 90}, {zp['y']}, 8, 16)"); await page.wait_for_timeout(200)
            check(tag + ' phone: a finger drag on the zipper works the zipper, not the scroll', (await page.evaluate(wjs(12)))['st']['v'] > 0.2 and await page.evaluate("__grasp.busy.scroll === __grasp.busy.maxScroll"))
            await page.evaluate("(() => { const d = " + W + "[13]; d.state.locked = false; d.state.bolt = 1; d.poke(performance.now()); })()"); await page.wait_for_timeout(700)
            await page.screenshot(path='tests/out/busy2_phone_scrolled' + ('_he' if he else '') + '.png')
            await page.mouse.wheel(0, -9000); await page.wait_for_timeout(700)
            check(tag + ' phone: wheel back up clamps at the top', await page.evaluate("__grasp.busy.scroll") == 0)
            check(tag + ' phone: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
