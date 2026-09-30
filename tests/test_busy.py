exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
POINT_JS = """
// pointing finger sweeping in a straight line, and an open hand doing the same
window.pointLine = (x0, y0, x1, y1, ms) => { const t0 = performance.now(); window.__handFor = () => { const k = Math.min(1, (performance.now() - t0) / ms); return pointAt(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k); }; };
window.openLine = (x0, y0, x1, y1, ms) => { const t0 = performance.now(); window.__handFor = () => { const k = Math.min(1, (performance.now() - t0) / ms); return handAt(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, 0.8); }; };
window.mkPoint = (tx, ty) => { // index fingertip at camera coords (not mirrored); other fingers curled; the thumb sits just above the tip so the pinch midpoint (the anchor before the point pose is confirmed) is only ~65 px off the tip on screen
  const L = Array.from({length:21}, () => ({x: tx, y: ty + 0.25, z: 0}));
  L[0] = {x: tx, y: ty + 0.35, z:0}; L[9] = {x: tx, y: ty + 0.20, z:0};
  L[8] = {x: tx, y: ty, z:0}; L[6] = {x: tx, y: ty + 0.12, z:0}; L[4] = {x: tx, y: ty - 0.09, z:0};
  for (const [tip, pip] of [[12,10],[16,14],[20,18]]) { L[pip] = {x: tx + 0.02, y: ty + 0.17, z:0}; L[tip] = {x: tx + 0.02, y: ty + 0.24, z:0}; }
  return L;
};
window.pointAt = (X, Y) => { const B = __grasp.CONFIG.MAP_BOX, m = (1 - B) / 2; return mkPoint(1 - (m + X / innerWidth * B), m + Y / innerHeight * B); };
"""
ARC_JS = """
// pinch at radius r around (cx, cy) and sweep from angle a0 to a1 over ms
// jump: the eased camera cursor glides through everything between two spots, so a hand that goes somewhere else first relaxes (open, 250 ms) at the old spot, moves there open (300 ms), then takes the pose
window.jump = (fn, x, y) => { const t0 = performance.now(), ox = cursor.x, oy = cursor.y; window.__handFor = () => { const e = performance.now() - t0; return e < 250 ? handAt(ox, oy, 0.8) : e < 550 ? handAt(x, y, 0.8) : fn(x, y); }; };
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
KINDS = {'switch': 4, 'button': 4, 'knob': 2, 'slider': 2, 'zipper': 1, 'door': 1, 'piano': 1, 'xylophone': 1, 'lights': 1, 'spinner': 1}
PIANO_BLACK = [(0, 'C#4'), (1, 'D#4'), (3, 'F#4'), (4, 'G#4'), (5, 'A#4')]  # white key each black key follows
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
        check('mode cycle includes busy', await page.evaluate("MODE_NEXT.smash === 'busy' && MODE_NEXT.busy === 'strike'"))
        await page.click('#mouseBtn'); await page.wait_for_timeout(500)
        kinds = await page.evaluate("(() => { const k = {}; for (const w of " + W + ") k[w.kind] = (k[w.kind] || 0) + 1; return k; })()")
        check('busy mode: 4 switches, 4 buttons, 2 knobs, 2 sliders, zipper, door, piano, xylophone, lights, spinner', await page.evaluate("gameMode") == 'busy' and kinds == KINDS, kinds)
        check('desktop: 7 columns, widgets inside the board, none overlapping, no scrolling needed', await page.evaluate(COLS(7)) and await page.evaluate(INSIDE) and await page.evaluate(OVERLAP) and await page.evaluate("__grasp.busy.maxScroll") == 0)
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
        # piano: press a key, sweep a glissando, black keys are the sharps
        pn = await page.evaluate(wjs(14)); kp = await page.evaluate(W + "[14].keyPos(2)")
        check('piano spans the full row: 8 white + 5 black keys', pn['kind'] == 'piano' and pn['w'] > 6 * pn['h'] and len(pn['st']['keys']) == 13, pn)
        await page.mouse.move(kp['x'], kp['y']); await page.wait_for_timeout(60); await page.mouse.down(); await page.wait_for_timeout(200)
        st = (await page.evaluate(wjs(14)))['st']; snd = await page.evaluate("__grasp.busy.sounds")
        check('pressing a key plays it (E4) and sinks it', st['last'] == 2 and st['keys'][2]['k'] > 0.8 and st['keys'][1]['k'] < 0.1 and snd['piano'] == 1 and round(await page.evaluate(W + "[14].freq(2)")) == 330, [st['last'], snd])
        for i in range(3, 8):
            q = await page.evaluate(W + f"[14].keyPos({i})"); await page.mouse.move(q['x'], q['y']); await page.wait_for_timeout(50)
        await page.mouse.up(); await page.wait_for_timeout(350)
        st = (await page.evaluate(wjs(14)))['st']
        check('sweeping the finger plays a glissando: every key it crosses', await page.evaluate("__grasp.busy.sounds.piano") == 6 and st['last'] is None and all(k['k'] < 0.2 for k in st['keys']), await page.evaluate("__grasp.busy.sounds"))
        q = await page.evaluate(W + "[14].keyPos(8)"); await page.mouse.click(q['x'], q['y']); await page.wait_for_timeout(60)
        check('clicking a black key plays it', await page.evaluate("__grasp.busy.sounds.piano") == 7 and await page.evaluate("performance.now() - " + W + "[14].state.keys[8].at") < 500 and await page.evaluate(W + "[14].keyAt(" + W + "[14].keyPos(8))") == 8)
        sharps = await page.evaluate("[8, 9, 10, 11, 12].map(i => [" + W + "[14].name(i), " + W + "[14].freq(i)])"); whites = await page.evaluate("[0, 1, 2, 3, 4, 5, 6, 7].map(i => " + W + "[14].freq(i))")
        check('white keys are C4..C5, black keys are the sharps a semitone above the white key to their left', [round(f) for f in whites] == [262, 294, 330, 349, 392, 440, 494, 523] and all(n == name and abs(f - whites[w] * 2 ** (1 / 12)) < 1 for (n, f), (w, name) in zip(sharps, PIANO_BLACK)), sharps)
        check('piano voice pool never exceeds 4', await page.evaluate("__grasp.pianoVoices") <= 4)
        # xylophone: hit a bar, sweep across with an open hand
        xy = await page.evaluate(wjs(15)); bx = await page.evaluate(W + "[15].x + " + W + "[15].barX(3)")
        check('xylophone spans the row: 8 bars, the last much shorter than the first', xy['kind'] == 'xylophone' and xy['w'] > 6 * xy['h'] and await page.evaluate(W + "[15].barLen(0) > " + W + "[15].barLen(7) * 1.5"))
        await page.mouse.click(bx, xy['y']); await page.wait_for_timeout(60)
        snd = await page.evaluate("__grasp.busy.sounds")
        check('hitting a bar plays it, bounces it and sparkles', snd['xylo'] == 1 and await page.evaluate("(() => { const w = " + W + "[15]; return Math.abs(w.bounce(3, w.state.bars[3].hit + 50)) > 2 && w.bounce(3, w.state.bars[3].hit + 400) === 0 && w.sparks.length > 0; })()"), snd)
        x0 = await page.evaluate(W + "[15].x + " + W + "[15].barX(0)"); x7 = await page.evaluate(W + "[15].x + " + W + "[15].barX(7)")
        await page.mouse.move(x0 - 60, xy['y']); await page.wait_for_timeout(150)
        check('a slow hover does not play', await page.evaluate("__grasp.busy.sounds.xylo") == 1)
        for i in range(1, 9): await page.mouse.move(x0 - 60 + (x7 + 60 - (x0 - 60)) * i / 8, xy['y']); await page.wait_for_timeout(8)
        await page.wait_for_timeout(150)
        check('a fast open sweep across the bars plays several of them', await page.evaluate("__grasp.busy.sounds.xylo") >= 4, await page.evaluate("__grasp.busy.sounds"))
        # lights: click toggles a bulb, holding pulses it
        lg = await page.evaluate(wjs(16)); b0 = await page.evaluate(W + "[16].bulbPos(0)"); b1 = await page.evaluate(W + "[16].bulbPos(1)")
        check('lights: 1x1 cell with 4 bulbs, all off', lg['kind'] == 'lights' and lg['w'] == lg['h'] and len(lg['st']['bulbs']) == 4 and not any(b['on'] for b in lg['st']['bulbs']))
        await page.mouse.click(b0['x'], b0['y']); await page.wait_for_timeout(350)
        st = (await page.evaluate(wjs(16)))['st']; snd = await page.evaluate("__grasp.busy.sounds"); pix = await page.evaluate(PIX + f"({b0['x']}, {b0['y']})")
        check('a click turns one bulb on with a tink; it glows', st['bulbs'][0]['on'] and st['bulbs'][0]['k'] > 0.8 and not st['bulbs'][1]['on'] and snd['tink'] == 1 and max(pix) > 200, [st['bulbs'][0], snd, pix])
        await page.mouse.click(b0['x'], b0['y']); await page.wait_for_timeout(450)
        st = (await page.evaluate(wjs(16)))['st']
        check('a second click turns it off', not st['bulbs'][0]['on'] and st['bulbs'][0]['k'] < 0.2 and await page.evaluate("__grasp.busy.sounds.tink") == 2, st['bulbs'][0])
        await page.mouse.move(b1['x'], b1['y']); await page.wait_for_timeout(60); await page.mouse.down(); await page.wait_for_timeout(150)
        check('a short hold has not pulsed yet', not (await page.evaluate(wjs(16)))['st']['bulbs'][1]['pulse'] and await page.evaluate("__grasp.busy.grabbed === " + W + "[16]"))
        await page.wait_for_timeout(400); ks = []
        for _ in range(7): ks.append(await page.evaluate(W + "[16].state.bulbs[1].k")); await page.wait_for_timeout(60)  # ~half a pulse period
        st = (await page.evaluate(wjs(16)))['st']
        check('pinch-and-hold makes the bulb pulse (glow rises and falls)', st['bulbs'][1]['pulse'] and max(ks) - min(ks) > 0.3 and max(ks) > 0.45 and await page.evaluate("__grasp.busy.sounds.tink") == 3, [ks, st['bulbs'][1]])
        await page.mouse.up(); await page.wait_for_timeout(100)
        st = (await page.evaluate(wjs(16)))['st']
        check('letting go stops the pulse without toggling', not st['bulbs'][1]['pulse'] and not st['bulbs'][1]['on'] and await page.evaluate("__grasp.busy.sounds.tink") == 3, st['bulbs'][1])
        # spinner: flick, spin down with clicks, stop on a wedge with a chord
        sp = await page.evaluate(wjs(17)); R = await page.evaluate(W + "[17].R()")
        check('spinner: 1x1 wheel with 8 wedges, still', sp['kind'] == 'spinner' and sp['w'] == sp['h'] and await page.evaluate("SPIN_N") == 8 and sp['st']['vel'] == 0 and sp['st']['winner'] is None)
        await page.mouse.move(sp['x'] - R * 0.9, sp['y'] - R * 0.4); await page.wait_for_timeout(60); await page.mouse.down(); await page.wait_for_timeout(30)
        for i in range(1, 6): await page.mouse.move(sp['x'] - R * 0.9 + R * 1.8 * i / 5, sp['y'] - R * 0.4); await page.wait_for_timeout(12)
        await page.mouse.up(); await page.wait_for_timeout(30)
        v0 = await page.evaluate(W + "[17].state.vel")
        await page.wait_for_timeout(300); v1 = await page.evaluate(W + "[17].state.vel"); c1 = await page.evaluate(W + "[17].state.clicks")
        await page.wait_for_timeout(400); v2 = await page.evaluate(W + "[17].state.vel"); c2 = await page.evaluate(W + "[17].state.clicks")
        check('a flick across the top sets a clockwise spin that slows with friction', v0 > 0.006 and 0 < v2 < v1 < v0, [v0, v1, v2])
        check('the pointer clicks as wedges pass, one sound per click', c2 > c1 >= 1 and await page.evaluate("__grasp.busy.sounds.cog") == c2 and await page.evaluate("__grasp.busy.sounds.chord") is None, [c1, c2])
        await page.wait_for_function(W + "[17].state.vel === 0 && " + W + "[17].state.winner !== null", timeout=8000)
        st = (await page.evaluate(wjs(17)))['st']; snd = await page.evaluate("__grasp.busy.sounds")
        check('it stops on a wedge: winner flashes, chord plays, ring', st['winner'] in range(8) and snd['chord'] == 1 and st['clicks'] >= 6 and await page.evaluate(W + "[17].wedgeAt()") == st['winner'] and await page.evaluate("rings.length") >= 1, [st['winner'], st['clicks'], snd])
        await page.mouse.move(sp['x'] - 500, sp['y'] - 300); await page.wait_for_timeout(120)
        await page.screenshot(path='tests/out/busy3_desktop.png')
        # reset re-randomises colours
        seed0 = await page.evaluate("__grasp.busy.seed"); cols0 = await page.evaluate(W + ".map(w => w.color).join()")
        await page.evaluate(W + "[1].press(performance.now()); " + W + "[10].grab({x: " + W + "[10].x, y: " + W + "[10].y})")
        check('a grabbed slider keeps its tone on', await page.evaluate("__grasp.busy.tone.active"))
        await page.click('#resetBtn'); await page.wait_for_timeout(200)
        check('reset re-randomises the board and clears states (and the tone)', await page.evaluate("__grasp.busy.seed") != seed0 and await page.evaluate(W + ".length === 18 && " + W + ".every(w => !w.state.on && !w.state.down && !w.state.held && !(w.state.v > 0))") and not await page.evaluate("__grasp.busy.tone.active"), [seed0, cols0])
        check('reset keeps everything inside the board', await page.evaluate(INSIDE) and await page.evaluate(OVERLAP))
        await page.evaluate(W + "[10].grab({x: " + W + "[10].x, y: " + W + "[10].y})")
        check('a grabbed slider sings again', await page.evaluate("__grasp.busy.tone.active"))
        await page.click('#homeBtn'); await page.wait_for_timeout(150)
        check('Home mid-drag stops the tone', await page.evaluate("mode === 'none' && !__grasp.busy.tone.active && liveTone.osc === null"))
        await page.click('#mouseBtn'); await page.wait_for_timeout(300)
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
        await page.evaluate(f"jump(pointAt, {b0['x']}, {b0['y']})"); await page.wait_for_timeout(1000)
        check('camera: pointing at a button presses it', await page.evaluate("gesture === 'point' && " + W + "[5].state.down && __grasp.busy.sounds.note === 1"), await page.evaluate("[gesture, __grasp.busy.sounds]"))
        s0 = await page.evaluate(wjs(1))
        await page.evaluate(f"jump(pointAt, {s0['x']}, {s0['y']})"); await page.wait_for_timeout(1000)
        check('camera: pointing at a switch flips it and releases the button', await page.evaluate(W + "[1].state.on && !" + W + "[5].state.down"))
        # pinch the slider handle and move the hand along the track
        hp = await page.evaluate(HANDLE(10)); tr = await page.evaluate("(() => { const g = " + W + "[10].geom(); return g.len - g.hw; })()")
        await page.evaluate(f"jump((x, y) => handAt(x, y, 0.8), {hp['x']}, {hp['y']})"); await page.wait_for_timeout(900)
        await page.evaluate(f"window.__handFor = () => handAt({hp['x']}, {hp['y']}, 0.1)"); await page.wait_for_timeout(400)
        check('camera: pinch grabs the slider and starts the tone', await page.evaluate("__grasp.busy.grabbed === " + W + "[10] && __grasp.busy.tone.active && __grasp.busy.sounds.tone === 1"))
        await page.evaluate(f"lineHand({hp['x']}, {hp['y']}, {hp['x'] + tr * 0.7}, {hp['y']}, 500)"); await page.wait_for_timeout(800)
        sl = await page.evaluate("({v: " + W + "[10].state.v, f: __grasp.busy.tone.f})")  # one read: the filtered hand is still settling
        check('camera: moving the pinched hand slides the handle', 0.55 < sl['v'] < 0.85 and abs(sl['f'] - 220 * 4 ** sl['v']) < 1, sl)
        await page.evaluate(f"window.__handFor = () => handAt({hp['x'] + tr * 0.7}, {hp['y']}, 0.8)"); await page.wait_for_timeout(400)
        check('camera: opening the hand drops the slider and stops the tone', await page.evaluate("__grasp.busy.grabbed === null && !__grasp.busy.tone.active"))
        dr = await page.evaluate(wjs(13))
        await page.evaluate(f"jump(pointAt, {dr['x']}, {dr['y'] + dr['h'] * 0.2})"); await page.wait_for_timeout(1000)
        check('camera: pointing at the locked door rattles it', await page.evaluate("__grasp.busy.sounds.thud") == 1 and not (await page.evaluate(wjs(13)))['st']['open'], [await page.evaluate("__grasp.busy.sounds"), (await page.evaluate(wjs(13)))['st'], await page.evaluate("[gesture, __grasp.state.cursor, __grasp.busy.active && __grasp.busy.active.kind, __grasp.busy.hover && __grasp.busy.hover.kind]"), dr])
        # piano: a pointing finger sweeping along the keys plays a glissando
        kq = [await page.evaluate(W + f"[14].keyPos({i})") for i in (0, 7)]
        await page.evaluate(f"jump(pointAt, {kq[0]['x']}, {kq[0]['y']})"); await page.wait_for_timeout(1000)
        check('camera: pointing at a key plays and sinks it', await page.evaluate("__grasp.busy.sounds.piano") == 1 and await page.evaluate(W + "[14].state.keys[0].k") > 0.8)
        await page.evaluate(f"pointLine({kq[0]['x']}, {kq[0]['y']}, {kq[1]['x']}, {kq[1]['y']}, 600)"); await page.wait_for_timeout(900)
        check('camera: sweeping the finger plays a glissando across the keys', await page.evaluate("__grasp.busy.sounds.piano") >= 6, await page.evaluate("__grasp.busy.sounds"))
        # lights: pinch-and-hold pulses a bulb
        b2 = await page.evaluate(W + "[16].bulbPos(2)")
        await page.evaluate(f"jump((x, y) => handAt(x, y, 0.8), {b2['x']}, {b2['y']})"); await page.wait_for_timeout(900)
        check('camera: open hand hovers the lights', await page.evaluate("__grasp.busy.hover === " + W + "[16]"))
        await page.evaluate(f"window.__handFor = () => handAt({b2['x']}, {b2['y']}, 0.1)"); await page.wait_for_timeout(800)
        st = (await page.evaluate(wjs(16)))['st']
        check('camera: pinch-and-hold on a bulb makes it pulse', st['bulbs'][2]['pulse'] and await page.evaluate("__grasp.busy.grabbed === " + W + "[16]") and await page.evaluate("__grasp.busy.sounds.tink") == 1, st['bulbs'][2])
        await page.evaluate(f"window.__handFor = () => handAt({b2['x']}, {b2['y']}, 0.8)"); await page.wait_for_timeout(300)
        st = (await page.evaluate(wjs(16)))['st']
        check('camera: opening the hand ends the pulse, bulb not toggled', not st['bulbs'][2]['pulse'] and not st['bulbs'][2]['on'] and await page.evaluate("__grasp.busy.sounds.tink") == 1, st['bulbs'][2])
        # spinner: a fast open-hand sweep flicks it
        sp = await page.evaluate(wjs(17)); R = await page.evaluate(W + "[17].R()")
        await page.evaluate(f"jump((x, y) => handAt(x, y, 0.8), {sp['x'] - 2 * R}, {sp['y'] - R * 0.4})"); await page.wait_for_timeout(900)
        await page.evaluate(f"openLine({sp['x'] - 2 * R}, {sp['y'] - R * 0.4}, {sp['x'] + 2 * R}, {sp['y'] - R * 0.4}, 160)"); await page.wait_for_timeout(400)
        st = (await page.evaluate(wjs(17)))['st']
        check('camera: an open-hand sweep spins the wheel (clicks follow)', st['spun'] and (st['vel'] > 0 or st['winner'] is not None) and st['clicks'] >= 1 and await page.evaluate("__grasp.busy.sounds.cog") >= 1, [st['vel'], st['clicks']])
        # xylophone: a fast open-hand sweep plays the bars it crosses
        xy = await page.evaluate(wjs(15)); x0 = await page.evaluate(W + "[15].x + " + W + "[15].barX(0)"); x7 = await page.evaluate(W + "[15].x + " + W + "[15].barX(7)")
        await page.evaluate(f"jump((x, y) => handAt(x, y, 0.8), {x0 - 60}, {xy['y']})"); await page.wait_for_timeout(900)
        await page.evaluate(f"openLine({x0 - 60}, {xy['y']}, {x7 + 60}, {xy['y']}, 260)"); await page.wait_for_timeout(500)
        check('camera: an open-hand sweep plays a run on the xylophone', await page.evaluate("__grasp.busy.sounds.xylo") >= 3, await page.evaluate("__grasp.busy.sounds"))
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
            fits = await page.evaluate("(() => { const m = document.querySelector('.modes').getBoundingClientRect(), sel = document.querySelector('.modes button[aria-pressed=true]').getBoundingClientRect(); const r = [...document.querySelectorAll('.modes button')].map(b => ({w: b.scrollWidth <= b.clientWidth + 1, in: m.right <= innerWidth && sel.right <= innerWidth && sel.left >= 0})); const a = document.querySelector('#start a.link').getBoundingClientRect(); return r.length === 5 && r.every(x => x.w && x.in) && a.bottom <= innerHeight && a.width > 0; })()")
            check(tag + ' phone: 5 mode cards and link fit', fits)
            await page.tap('.modes button[data-mode=busy]')
            check(tag + ' phone: busy card label', await page.inner_text('.modes button[data-mode=busy]') == ('לוח עסוק' if he else 'Busy Board'))
            await page.screenshot(path='tests/out/busy_start' + ('_he' if he else '') + '.png')
            await page.tap('#mouseBtn'); await page.wait_for_timeout(500)
            hint = await page.inner_text('#hint')
            check(tag + ' phone: touch hint', ('הקישו' in hint) if he else ('Tap' in hint), hint)
            check(tag + ' phone: touch hint mentions dragging the board', ('גררו את הלוח' in hint) if he else ('Drag the board' in hint), hint)
            kinds = await page.evaluate("(() => { const k = {}; for (const w of " + W + ") k[w.kind] = (k[w.kind] || 0) + 1; return k; })()")
            check(tag + ' phone: all 18 widgets, 2 columns, inside the board, none overlapping, 8 fully visible at the top', kinds == KINDS and await page.evaluate(COLS(2)) and await page.evaluate(VISIBLE(8)) and await page.evaluate(OVERLAP), kinds)
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
            off = await page.evaluate("Math.abs(" + W + "[2].y - (" + str(s0['y']) + " - __grasp.busy.scroll))")  # read in one go: the board may still be gliding
            check(tag + ' phone: widgets moved up with the board, nothing pressed', off < 1 and await page.evaluate("__grasp.busy.sounds.all") == 2, [s0['y'], s2, off, await page.evaluate("__grasp.busy.sounds")])
            await page.evaluate(f"touchDrag({ex}, 200, {ex}, 700, 6, 16)"); await page.wait_for_timeout(700)
            check(tag + ' phone: dragging down past the top clamps at 0', await page.evaluate("__grasp.busy.scroll") == 0 and await page.evaluate("__grasp.busy.scrollV") == 0)
            await page.mouse.wheel(0, 9000); await page.wait_for_timeout(700)
            check(tag + ' phone: wheel scrolls and clamps at the bottom', await page.evaluate("__grasp.busy.scroll === __grasp.busy.maxScroll"), await page.evaluate("[__grasp.busy.scroll, __grasp.busy.maxScroll]"))
            check(tag + ' phone: scrolled to the bottom, the zipper, piano and xylophone are fully on screen, still no overlaps', await page.evaluate("(() => { const ws = " + W + "; return [12, 14, 15].every(i => ws[i].y - ws[i].h / 2 >= 0 && ws[i].y + ws[i].h / 2 <= innerHeight); })()") and await page.evaluate(VISIBLE(4)) and await page.evaluate(OVERLAP))
            zp = await page.evaluate(wjs(12)); tx = await page.evaluate(W + "[12].tabX()")
            await page.evaluate(f"touchDrag({tx}, {zp['y']}, {tx + 90}, {zp['y']}, 8, 16)"); await page.wait_for_timeout(200)
            check(tag + ' phone: a finger drag on the zipper works the zipper, not the scroll', (await page.evaluate(wjs(12)))['st']['v'] > 0.2 and await page.evaluate("__grasp.busy.scroll === __grasp.busy.maxScroll"))
            await page.evaluate("(() => { const d = " + W + "[13]; d.state.locked = false; d.state.bolt = 1; d.poke(performance.now()); })()"); await page.wait_for_timeout(700)
            await page.screenshot(path='tests/out/busy2_phone_scrolled' + ('_he' if he else '') + '.png')
            # the new widgets on a phone: piano key tap, xylophone run, lights tap, spinner flick
            kp = await page.evaluate(W + "[14].keyPos(4)"); await page.tap('#stage', position={'x': kp['x'], 'y': kp['y']}); await page.wait_for_timeout(120)
            check(tag + ' phone: tapping a piano key plays it', await page.evaluate("__grasp.busy.sounds.piano") == 1 and await page.evaluate("performance.now() - " + W + "[14].state.keys[4].at") < 400)
            xy = await page.evaluate(wjs(15)); x0 = await page.evaluate(W + "[15].x + " + W + "[15].barX(0)"); x7 = await page.evaluate(W + "[15].x + " + W + "[15].barX(7)")
            await page.evaluate(f"touchDrag({x0}, {xy['y']}, {x7}, {xy['y']}, 8, 20)"); await page.wait_for_timeout(200)
            check(tag + ' phone: a finger run across the xylophone plays the bars', await page.evaluate("__grasp.busy.sounds.xylo") >= 4 and await page.evaluate("__grasp.busy.scroll === __grasp.busy.maxScroll"), await page.evaluate("__grasp.busy.sounds"))
            await page.screenshot(path='tests/out/busy3_phone_bottom' + ('_he' if he else '') + '.png')
            await page.mouse.wheel(0, -9000); await page.wait_for_timeout(700)
            check(tag + ' phone: wheel back up clamps at the top', await page.evaluate("__grasp.busy.scroll") == 0)
            await page.mouse.wheel(0, 520); await page.wait_for_timeout(700)
            lg = await page.evaluate(wjs(16)); sp = await page.evaluate(wjs(17)); R = await page.evaluate(W + "[17].R()")
            check(tag + ' phone: lights and spinner sit side by side, fully on screen after a short scroll', lg['y'] == sp['y'] and lg['x'] < sp['x'] and lg['y'] - lg['h'] / 2 >= 0 and lg['y'] + lg['h'] / 2 <= 740, [lg['y'], sp['y']])
            b3 = await page.evaluate(W + "[16].bulbPos(3)"); await page.tap('#stage', position={'x': b3['x'], 'y': b3['y']}); await page.wait_for_timeout(300)
            check(tag + ' phone: tapping a bulb lights it', (await page.evaluate(wjs(16)))['st']['bulbs'][3]['on'] and await page.evaluate("__grasp.busy.sounds.tink") == 1)
            await page.evaluate(f"touchDrag({sp['x'] - R * 0.9}, {sp['y'] - R * 0.4}, {sp['x'] + R * 0.9}, {sp['y'] - R * 0.4}, 5, 12)"); await page.wait_for_timeout(250)
            st = (await page.evaluate(wjs(17)))['st']
            check(tag + ' phone: a finger flick spins the wheel, board did not scroll', st['spun'] and (st['vel'] > 0 or st['winner'] is not None) and st['clicks'] >= 1 and await page.evaluate("__grasp.busy.scroll") > 0, [st['vel'], st['clicks']])
            await page.screenshot(path='tests/out/busy3_phone_mid' + ('_he' if he else '') + '.png')
            await page.wait_for_function(W + "[17].state.vel === 0", timeout=8000)
            check(tag + ' phone: the wheel stops with a chord', await page.evaluate("__grasp.busy.sounds.chord") == 1 and (await page.evaluate(wjs(17)))['st']['winner'] in range(8))
            check(tag + ' phone: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
