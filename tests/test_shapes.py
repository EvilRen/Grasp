exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
import math
# Shapes: the shape sorter (6th mode). The start tile, level 1 (3 shapes + matching holes), a mouse drag into the right hole (clunk + rising chime +
# the spoken name, EN / HE, via a speechSynthesis stub), the wrong hole (boing, back home), a level completed (stars, coins, banner, next level with
# more shapes), rotated holes from level 4 (the wheel turns the shape; within 25° it snaps), the moving box (levels 6 / 7), a two-finger twist,
# a camera-stub pinch-drag, the round-over card from Home, and the start screen's 6 tiles on a phone (no scroll, no big gap under the top bar).
S = '__grasp.shapes'
SPEECH = """window.__spoken = []; try { Object.defineProperty(window, 'speechSynthesis', { configurable: true, get: () => ({ speak(u) { __spoken.push({ text: u.text, lang: u.lang }); }, cancel() {}, getVoices() { return [{ lang: 'en-US', name: 'E' }, { lang: 'he-IL', name: 'H' }]; } }) }); } catch (e) { window.__speechStubFailed = String(e); }"""
SFX_JS = "(() => { window.__sfx = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); o(k, a); }; })()"
FINGERS = """
// synthetic touch pointers on the canvas: down / move / up by id
window.fing = (type, id, x, y) => { const c = document.getElementById('stage'), e = new PointerEvent(type, { pointerId: id, pointerType: 'touch', clientX: x, clientY: y, isPrimary: id === 1, bubbles: true, cancelable: true, button: 0, buttons: type === 'pointerup' ? 0 : 1 }); (type === 'pointerdown' ? c : window).dispatchEvent(e); };
"""
LINE_JS = """
window.lineHand = (x0, y0, x1, y1, ms, pd) => { const t0 = performance.now(); window.__handFor = () => { const k = Math.min(1, (performance.now() - t0) / ms); return handAt(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, pd); }; };
"""

async def ctx_page(b, mobile=False, he=False, init='', camera=False):
    opts = dict(viewport={'width':360,'height':740}, device_scale_factor=2, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width':1280,'height':800})
    if camera: opts['permissions'] = ['camera']
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + SPEECH + HAND_JS + FINGERS + LINE_JS + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');") + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_function("typeof engine !== 'undefined' && !!engine", timeout=15000)
    return ctx, page, errs

async def wait(page, cond, timeout=8000):
    try: await page.wait_for_function(cond, timeout=timeout); return True
    except Exception: return False

async def drag(page, x0, y0, x1, y1, steps=12):
    await page.mouse.move(x0, y0); await page.mouse.down(); await page.wait_for_timeout(60)
    await page.mouse.move(x1, y1, steps=steps); await page.wait_for_timeout(60)

# ---- toddler play (phone): tap a shape, then tap a hole; touch-drag help (grab radius, lift, smoothing, magnet, release help, grace) ----
NAMES = {False: {'circle': 'Circle', 'square': 'Square', 'triangle': 'Triangle'}, True: {'circle': 'עיגול', 'square': 'ריבוע', 'triangle': 'משולש'}}
FING_W = """window.fingW = (type, id, x, y, w) => { const c = document.getElementById('stage'), e = new PointerEvent(type, { pointerId: id, pointerType: 'touch', clientX: x, clientY: y, width: w, height: w, isPrimary: id === 1, bubbles: true, cancelable: true, button: 0, buttons: type === 'pointerup' ? 0 : 1 }); (type === 'pointerdown' ? c : window).dispatchEvent(e); };"""

async def tap(page, x, y, jitter=0, hold=70, pid=1):
    await page.evaluate(f"fing('pointerdown', {pid}, {x}, {y})"); await page.wait_for_timeout(hold // 2)
    if jitter: await page.evaluate(f"fing('pointermove', {pid}, {x + jitter}, {y + jitter * 0.4})")
    await page.wait_for_timeout(hold - hold // 2)
    await page.evaluate(f"fing('pointerup', {pid}, {x + jitter}, {y + jitter * 0.4})"); await page.wait_for_timeout(120)

async def fdrag(page, x0, y0, x1, y1, steps=10, up=True, pid=1):
    await page.evaluate(f"fing('pointerdown', {pid}, {x0}, {y0})"); await page.wait_for_timeout(120)
    for k in range(1, steps + 1):
        await page.evaluate(f"fing('pointermove', {pid}, {x0 + (x1 - x0) * k / steps}, {y0 + (y1 - y0) * k / steps})"); await page.wait_for_timeout(35)
    await page.wait_for_timeout(350)
    if up: await page.evaluate(f"fing('pointerup', {pid}, {x1}, {y1})")

def empty_spot(st, r):
    m = st['mat']
    best = None
    for gx in range(12):
        for gy in range(8):
            x = m['x'] + 20 + (m['w'] - 40) * gx / 11; y = m['y'] + 20 + (m['h'] - 40) * gy / 7
            d = min([math.hypot(x - s['x'], y - s['y']) for s in st['shapes']] + [math.hypot(x - h['x'], y - h['y']) for h in st['holes']])
            if best is None or d > best[0]: best = (d, x, y)
    return best

async def tap_tests(b, he):
    tag = 'he' if he else 'en'
    ctx, page, errs = await ctx_page(b, True, he, init=FING_W)
    await page.tap('.modes button[data-mode=shapes]'); await wait(page, "mode === 'mouse' && gameMode === 'shapes'"); await page.wait_for_timeout(700)
    await page.evaluate(SFX_JS)
    tip = 'הקישו על צורה ואז על החור שלה!' if he else 'Tap a shape, then tap its hole!'
    ok = await wait(page, f"!!{S}.demo && {S}.ui.demo && {S}.ui.demo.on", 4000)
    tips = await page.evaluate("__grasp.grippy.tips.map(x => x.text)")
    check(tag + ' phone: first play: the one-time tip "' + tip + '" and a finger demo', ok and tip in tips and await page.evaluate("document.querySelector('#hint .tx, .hint .tx') ? true : true"), tips)
    await page.wait_for_timeout(500); await page.screenshot(path=f'tests/out/shapes_tap_demo_{tag}.png')
    st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes, mat: {S}.mat, R: {S}.grabR, S: {S}.shapes[0].size / 2 }})")
    check(tag + ' phone: big hit areas (grab radius >= 44 px: >= 88 px across)', st['R'] >= 44, st['R'])
    s0 = st['shapes'][0]
    # tap a shape: it is picked (hop, glow, wiggle, boop), holes pulse, it stays on its spot
    await tap(page, s0['x'] + 5, s0['y'] - 4)
    ok = await wait(page, f"{S}.sel === 0 && {S}.ui.selFx && {S}.ui.selFx.i === 0", 3000)
    await page.wait_for_timeout(120)
    r = await page.evaluate(f"({{ sel: {S}.sel, held: {S}.held, fx: {S}.ui.selFx, pulse: {S}.ui.holePulse, sfx: __sfx.slice(), s: {S}.shapes[0], demo: {S}.ui.demo }})")
    fx = r['fx'] or {}
    check(tag + ' phone: a tap on a shape picks it: lifted + glowing + bigger, a boop, every free hole pulses; nothing held, it stays on its spot',
          ok and r['sel'] == 0 and r['held'] == -1 and fx.get('dy', 0) < -3 and fx.get('glow', 0) > 0.2 and fx.get('scale', 0) > 1.05 and 'boop' in r['sfx'] and r['pulse'] == 3
          and abs(r['s']['x'] - s0['x']) < 1 and abs(r['s']['y'] - s0['y']) < 1 and r['s']['selected'] and r['s']['anim'] is None, r)
    check(tag + ' phone: the first touch ends the finger demo', not r['demo'], r['demo'])
    await page.screenshot(path=f'tests/out/shapes_tap_selected_{tag}.png')
    # tap it again: deselected
    await tap(page, s0['x'], s0['y'])
    r = await page.evaluate(f"({{ sel: {S}.sel, log: {S}.tapLog.slice(-1)[0] }})")
    check(tag + ' phone: tapping the picked shape again drops the pick', r['sel'] == -1 and r['log']['k'] == 'deselect' and r['log']['why'] == 'again', r)
    if not he:
        # another shape switches the pick; a tap elsewhere drops it; a hole with no pick does nothing
        s1 = st['shapes'][1]
        await tap(page, s0['x'], s0['y']); await tap(page, s1['x'], s1['y'])
        check('phone: tapping another shape switches the pick', await page.evaluate(f"{S}.sel") == 1)
        d, ex, ey = empty_spot(st, st['R'])
        await tap(page, ex, ey)
        r = await page.evaluate(f"({{ sel: {S}.sel, log: {S}.tapLog.slice(-1)[0] }})")
        check(f'phone: a tap on an empty spot ({d:.0f} px from anything) drops the pick', r['sel'] == -1 and r['log']['why'] == 'elsewhere', r)
        h_any = st['holes'][0]
        await tap(page, h_any['x'], h_any['y'])
        r = await page.evaluate(f"({{ sel: {S}.sel, anims: {S}.shapes.map(s => s.anim), placed: {S}.shapes.filter(s => s.placed).length }})")
        check('phone: a tap on a hole with nothing picked does nothing', r['sel'] == -1 and all(a is None for a in r['anims']) and r['placed'] == 0, r)
        # a small jitter (12 px) still counts as a tap
        await tap(page, s1['x'], s1['y'], jitter=12)
        r = await page.evaluate(f"({{ sel: {S}.sel, s: {S}.shapes[1], press: {S}.press }})")
        check('phone: a tap that wobbles 12 px still picks (and the shape stays home)', r['sel'] == 1 and abs(r['s']['x'] - s1['x']) < 1 and abs(r['s']['y'] - s1['y']) < 1 and r['press']['maxD'] > 8, r)
        await tap(page, s1['x'], s1['y'])
        # two fingers (or a palm) are no tap
        await page.evaluate(f"fing('pointerdown', 1, {s0['x']}, {s0['y']})"); await page.wait_for_timeout(40)
        await page.evaluate(f"fing('pointerdown', 2, {s0['x'] + 70}, {s0['y'] + 10})"); await page.wait_for_timeout(60)
        await page.evaluate("fing('pointerup', 2, 0, 0); fing('pointerup', 1, " + str(s0['x']) + ", " + str(s0['y']) + ")"); await page.wait_for_timeout(500)
        check('phone: a two-finger touch is no tap (nothing picked)', await page.evaluate(f"{S}.sel") == -1)
        await page.evaluate(f"fingW('pointerdown', 1, {s0['x']}, {s0['y']}, 130)"); await page.wait_for_timeout(150)
        pg = await page.evaluate(f"{S}.held"); await page.evaluate(f"fingW('pointerup', 1, {s0['x']}, {s0['y']}, 130)"); await page.wait_for_timeout(200)
        check('phone: a palm-sized contact neither grabs nor picks', pg == -1 and await page.evaluate(f"{S}.sel") == -1, pg)
    # pick, then the WRONG hole: it flies there, boings, flies home; no mistake
    st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes }})")
    s0 = st['shapes'][0]; wj = next(j for j, h in enumerate(st['holes']) if h['kind'] != s0['kind'])
    await tap(page, s0['x'], s0['y']); await page.evaluate("__sfx.length = 0")
    await page.evaluate(f"fing('pointerdown', 1, {st['holes'][wj]['x'] + 6}, {st['holes'][wj]['y'] - 5})"); await page.wait_for_timeout(40); await page.evaluate(f"fing('pointerup', 1, {st['holes'][wj]['x'] + 6}, {st['holes'][wj]['y'] - 5})")
    ok = await wait(page, f"{S}.shapes[0].anim === 'fly' && {S}.shapes[0].flyTo === {wj}", 2000)
    await page.wait_for_timeout(150)
    fl = await page.evaluate(f"{S}.shapes[0]")
    check(tag + ' phone: the picked shape, a tap on another hole: it flies there on an arc (above the straight line)', ok and fl['anim'] == 'fly' and fl['y'] < s0['y'] + (st['holes'][wj]['y'] - s0['y']) * 0.6, fl)
    await page.screenshot(path=f'tests/out/shapes_tap_flight_wrong_{tag}.png')
    ok = await wait(page, f"{S}.shapes[0].anim === 'back'", 3000)
    r = await page.evaluate(f"({{ sfx: __sfx.slice(), m: {S}.mistakes, placed: {S}.shapes[0].placed, filled: {S}.holes.filter(h => h.filled).length }})")
    check(tag + ' phone: ...the wrong hole: a boing, it bounces off and flies home (no mistake counted)', ok and 'boing' in r['sfx'] and 'clunk' not in r['sfx'] and r['m'] == 0 and not r['placed'] and r['filled'] == 0, r)
    ok = await wait(page, f"!{S}.shapes[0].anim", 3000); bk = await page.evaluate(f"{S}.shapes[0]")
    check(tag + ' phone: ...and lands back on its spot', ok and abs(bk['x'] - s0['x']) < 1 and abs(bk['y'] - s0['y']) < 1, bk)
    # pick, then its own hole: flies, drops in with the celebration, the name spoken
    hj = next(j for j, h in enumerate(st['holes']) if h['kind'] == s0['kind']); hl = st['holes'][hj]
    await tap(page, s0['x'], s0['y']); await page.evaluate("__sfx.length = 0")
    await page.evaluate(f"fing('pointerdown', 1, {hl['x'] - 8}, {hl['y'] + 6})"); await page.wait_for_timeout(40); await page.evaluate(f"fing('pointerup', 1, {hl['x'] - 8}, {hl['y'] + 6})")
    ok = await wait(page, f"{S}.shapes[0].anim === 'fly'", 2000); await page.wait_for_timeout(230)
    await page.screenshot(path=f'tests/out/shapes_tap_flight_{tag}.png')
    ok = ok and await wait(page, f"{S}.shapes[0].placed && !{S}.shapes[0].anim", 4000)
    r = await page.evaluate(f"({{ sfx: __sfx.slice(), spoken: {S}.spoken, said: __spoken.slice(-1)[0], filled: {S}.holes[{hj}].filled, ev: __grasp.events.slice(-4), parts: particles.length }})")
    check(tag + ' phone: ...its own hole: it flies in, clunk + chime + burst, the name spoken (' + NAMES[he][s0['kind']] + ')', ok and r['filled'] and 'clunk' in r['sfx'] and 'rise' in r['sfx'] and r['spoken'] == NAMES[he][s0['kind']] and r['said'] == {'text': NAMES[he][s0['kind']], 'lang': 'he-IL' if he else 'en-US'} and ['shape', 1] in r['ev'], r)
    await page.wait_for_timeout(250); await page.screenshot(path=f'tests/out/shapes_tap_placed_{tag}.png')
    if not he:
        # a real drag still drags (touch): picked nothing, the shape moved with the finger and stays where it was let go on the mat
        st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes, mat: {S}.mat }})"); LIFT = await page.evaluate(f"{S}.lift")  # (40 px x the shapes' size boost)
        i1 = next(i for i, s in enumerate(st['shapes']) if not s['placed']); s1 = st['shapes'][i1]
        # (big shapes: the release help reaches 4.2 S from its hole, most of the mat; drop it at the mat spot farthest from its hole)
        HR = await page.evaluate(f"{S}.helpR"); S1 = s1['size'] / 2; m = st['mat']; own = next(h for h in st['holes'] if h['kind'] == s1['kind'])
        tx, ty = max(((m['x'] + 1.3 * S1 + (m['w'] - 2.6 * S1) * gx / 10, m['y'] + 1.3 * S1 + (m['h'] - 2.6 * S1) * gy / 6) for gx in range(11) for gy in range(7) if math.hypot(m['x'] + 1.3 * S1 + (m['w'] - 2.6 * S1) * gx / 10 - s1['x'], m['y'] + 1.3 * S1 + (m['h'] - 2.6 * S1) * gy / 6 - s1['y']) > 60),
                     key=lambda p: math.hypot(p[0] - own['x'], p[1] - own['y']))
        await fdrag(page, s1['x'], s1['y'] + LIFT, tx, ty + LIFT, up=False)
        mid = await page.evaluate(f"({{ held: {S}.held, s: {S}.shapes[{i1}], info: {S}.heldInfo }})")
        check(f'phone: a real drag drags: held, the shape sits ~lift ({LIFT:.0f}) px above the finger', mid['held'] == i1 and abs(mid['s']['x'] - tx) < 4 and abs(mid['s']['y'] - ty) < 4 and mid['info']['help'], mid)
        await page.evaluate(f"fing('pointerup', 1, {tx}, {ty + LIFT})"); await page.wait_for_timeout(400)
        r = await page.evaluate(f"({{ sel: {S}.sel, s: {S}.shapes[{i1}], held: {S}.held }})")
        check(f'phone: ...let go on the mat ({math.hypot(tx - own["x"], ty - own["y"]):.0f} px from its hole, help reach {HR:.0f}): no pick, it stays where it was dropped (no fly-back)', math.hypot(tx - own['x'], ty - own['y']) > HR and r['sel'] == -1 and r['held'] == -1 and not r['s']['placed'] and r['s']['anim'] is None and abs(r['s']['x'] - tx) < 4 and abs(r['s']['hx'] - r['s']['x']) < 1, r)
        # a pick dropped by a drag of another shape
        i2 = next(i for i, s in enumerate(st['shapes']) if not s['placed'] and i != i1); s2 = (await page.evaluate(f"{S}.shapes"))[i2]
        await tap(page, s2['x'], s2['y']); p1 = await page.evaluate(f"{S}.sel")
        s1 = (await page.evaluate(f"{S}.shapes"))[i1]
        await fdrag(page, s1['x'], s1['y'], s1['x'], s1['y'] + 40, steps=5, up=False)
        r = await page.evaluate(f"({{ sel: {S}.sel, held: {S}.held }})"); await page.evaluate(f"fing('pointerup', 1, {s1['x']}, {s1['y'] + 40})"); await page.wait_for_timeout(300)
        check('phone: dragging a shape drops a tap pick', p1 == i2 and r['sel'] == -1 and r['held'] == i1, [p1, r])

        # ---- touch-drag help ----
        await page.evaluate(f"{S}.setLevel(1)"); await page.wait_for_timeout(600)
        st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes, mat: {S}.mat, R: {S}.grabR, M: {S}.magnetR, Hr: {S}.helpR }})")
        S_ = st['shapes'][0]['size'] / 2; s0 = st['shapes'][0]
        # grab assist: a touch 1.6 x the shape's radius away still grabs it; the shape jumps above the finger
        # (the direction away from the other shapes and inside the mat: with big shapes the mat is crowded, and the nearest shape wins)
        def _away(a):
            x, y = s0['x'] + S_ * 1.6 * math.cos(a), s0['y'] + S_ * 1.6 * math.sin(a)
            inside = st['mat']['x'] < x < st['mat']['x'] + st['mat']['w'] and st['mat']['y'] < y < st['mat']['y'] + st['mat']['h']
            return (inside, min(math.hypot(x - q['x'], y - q['y']) for q in st['shapes'][1:]))
        ga = max([math.radians(d) for d in range(0, 360, 15)], key=_away)
        gx, gy = s0['x'] + S_ * 1.6 * math.cos(ga), s0['y'] + S_ * 1.6 * math.sin(ga)
        await page.evaluate(f"fing('pointerdown', 1, {gx}, {gy})"); await page.wait_for_timeout(400)
        r = await page.evaluate(f"({{ held: {S}.held, s: {S}.shapes[0] }})")
        check(f'phone help: a touch {S_ * 1.6:.0f} px from a shape still grabs it (radius {st["R"]:.0f}); it sits ~lift px above the finger', r['held'] == 0 and abs(r['s']['x'] - gx) < 3 and abs(r['s']['y'] - (gy - LIFT)) < 3, r)
        J = 160 if gx < 180 else -160
        # smoothing: a sudden 160 px jump of the finger is followed smoothly (not in one frame)
        trail = await page.evaluate(f"""(async () => {{ const out = []; fing('pointermove', 1, {gx + J}, {gy}); for (let i = 0; i < 4; i++) {{ await new Promise(r => requestAnimationFrame(r)); out.push(__grasp.shapes.shapes[0].x); }} return out; }})()""")
        await page.wait_for_timeout(500); xe = await page.evaluate(f"{S}.shapes[0].x")
        check('phone help: shaky fingers are smoothed: the shape glides after a 160 px jump (not there at once), then catches up', abs(trail[0] - (gx + J)) > 1.5 and all(abs(trail[i + 1] - (gx + J)) <= abs(trail[i] - (gx + J)) + 0.01 for i in range(3)) and abs(xe - (gx + J)) < 2, [trail, xe, gx + J])
        # a second finger landing mid-drag: still held
        await page.evaluate(f"fing('pointerdown', 2, {gx + 60}, {gy + 90})"); await page.wait_for_timeout(150); h2 = await page.evaluate(f"{S}.held")
        await page.evaluate("fing('pointerup', 2, 0, 0)"); await page.wait_for_timeout(150)
        check('phone help: a second finger landing mid-drag does not drop the shape', h2 == 0 and await page.evaluate(f"{S}.held") == 0)
        # lifted for a moment (a bounce of the finger): still held; back down: carries on
        await page.evaluate(f"fing('pointerup', 1, {gx + J}, {gy})"); await page.wait_for_timeout(50)
        hb = await page.evaluate(f"{S}.held")
        await page.evaluate(f"fing('pointerdown', 1, {gx + J * 0.94}, {gy + 4})"); await page.wait_for_timeout(250)
        check('phone help: the finger bouncing off the glass (up for ~50 ms) keeps the shape held', hb == 0 and await page.evaluate(f"{S}.held") == 0)
        # magnet: near its hole the shape is pulled in (and turned); let go inside the zone: it drops in
        hl = next(h for h in st['holes'] if h['kind'] == s0['kind'])
        fx_, fy_ = hl['x'] + st['M'] * 0.75 * (1 if hl['x'] < 180 else -1), hl['y'] + LIFT  # the shape's target: 0.75 x the magnet radius to the side of the hole (the side with room)
        steps = 8; cx, cy = gx + J * 0.94, gy + 4
        for k in range(1, steps + 1):
            await page.evaluate(f"fing('pointermove', 1, {cx + (fx_ - cx) * k / steps}, {cy + (fy_ - cy) * k / steps})"); await page.wait_for_timeout(35)
        await page.wait_for_timeout(450)
        r = await page.evaluate(f"({{ mag: {S}.magnet, s: {S}.shapes[0], hj: {S}.holes.findIndex(h => h.kind === {S}.shapes[0].kind) }})")
        dS = math.hypot(r['s']['x'] - hl['x'], r['s']['y'] - hl['y'])
        check(f'phone help: magnet: {st["M"] * 0.75:.0f} px beside its hole the shape is pulled in ({dS:.0f} px from it)', r['mag'] == r['hj'] and dS < st['M'] * 0.75 - 8, [r, dS])
        await page.screenshot(path='tests/out/shapes_drag_magnet.png')
        await page.evaluate(f"fing('pointerup', 1, {fx_}, {fy_})")
        ok = await wait(page, f"{S}.shapes[0].placed", 3000)
        check('phone help: ...let go inside the magnet zone: it drops in', ok)
        # release help: let go between the magnet and the help radius (not over another hole): it slides to its hole
        st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes }})")
        s1 = st['shapes'][1]; h1 = next(h for h in st['holes'] if h['kind'] == s1['kind'] and not h['filled'])
        M_, H_ = await page.evaluate(f"[{S}.magnetR, {S}.helpR]"); dist = min(H_ - 6, max((M_ + H_) / 2, M_ + 48))  # the finger (40 px below the shape) outside the magnet too
        tx, ty = h1['x'], h1['y'] - dist  # straight above its hole (toward the mat)
        await fdrag(page, s1['x'], s1['y'], tx, ty + 40, up=False)
        under = await page.evaluate(f"({{ mag: {S}.magnet, s: {S}.shapes[1] }})")
        await page.evaluate(f"fing('pointerup', 1, {tx}, {ty + LIFT})")
        ok = await wait(page, f"{S}.shapes[1].anim === 'fly'", 1500)
        lg = await page.evaluate(f"{S}.tapLog.slice(-1)[0]")
        ok2 = await wait(page, f"{S}.shapes[1].placed", 3000)
        check(f'phone help: let go {dist:.0f} px from its hole (outside the magnet): it slides in by itself', ok and ok2 and under['mag'] == -1 and lg['k'] == 'fly' and lg['why'] == 'help', [under, lg])
        # edge slip: the finger slides off the screen edge: still held for a moment, then it settles (on the mat it stays)
        s2 = (await page.evaluate(f"{S}.shapes"))[2]
        m = st['mat'] if 'mat' in st else await page.evaluate(f"{S}.mat")
        await fdrag(page, s2['x'], s2['y'], 1, s2['y'], up=False)
        await page.evaluate(f"fing('pointerup', 1, 1, {s2['y']})"); await page.wait_for_timeout(300)
        r1 = await page.evaluate(f"({{ held: {S}.held, info: {S}.heldInfo }})")
        await page.wait_for_timeout(700); r2 = await page.evaluate(f"({{ held: {S}.held, s: {S}.shapes[2] }})")
        check('phone help: a finger slipping off the screen edge keeps the shape a moment (0.3 s later still held), then lets it settle', r1['held'] == 2 and r1['info']['edge'] and r2['held'] == -1 and not r2['s']['placed'], [r1, r2])
        await wait(page, f"!{S}.shapes[2].anim", 2000)
        # a cancelled touch over its hole: no drop, no boing: it just settles
        s2 = (await page.evaluate(f"{S}.shapes"))[2]; h2 = next(h for h in (await page.evaluate(f"{S}.holes")) if h['kind'] == s2['kind'])
        await page.evaluate("__sfx.length = 0")
        await fdrag(page, s2['x'], s2['y'], h2['x'], h2['y'] + 40, up=False)
        await page.evaluate(f"fing('pointercancel', 1, {h2['x']}, {h2['y'] + LIFT})"); await page.wait_for_timeout(400)
        r = await page.evaluate(f"({{ held: {S}.held, s: {S}.shapes[2], sfx: __sfx.slice() }})")
        check('phone help: a cancelled touch (the browser took it) is no drop: the shape settles back, no boing', r['held'] == -1 and not r['s']['placed'] and 'boing' not in r['sfx'], r)
        # rotated level: a drag into the magnet drops it in at any angle; the magnet is weaker on harder levels
        await page.evaluate(f"{S}.setLevel(4)"); await page.wait_for_timeout(600)
        st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes, sym: {S}.sym }})")
        cand = [(i, s, h) for i, s in enumerate(st['shapes']) for h in st['holes'] if h['kind'] == s['kind'] and st['sym'][s['kind']] in (2, 3, 4, 5, 1) and abs(math.degrees(h['angle'])) > 30]
        i4, s4, h4 = cand[0] if cand else (0, st['shapes'][0], next(h for h in st['holes'] if h['kind'] == st['shapes'][0]['kind']))
        await fdrag(page, s4['x'], s4['y'], h4['x'], h4['y'] + LIFT)
        ok = await wait(page, f"{S}.shapes[{i4}].placed", 3000)
        check(f'phone help: level 4: dragged onto its rotated hole ({math.degrees(h4["angle"]):.0f}°) it turns itself and drops in', ok, [s4['kind'], h4['angle']])
        mr = await page.evaluate("(() => { const out = []; for (const n of [1, 4, 8]) { __grasp.shapes.setLevel(n); out.push(__grasp.shapes.magnetR / (__grasp.shapes.shapes[0].size / 2)); } return out; })()")
        check('phone help: the magnet is weaker on harder levels (in shape radii: L1 > L4 > L8)', mr[0] > mr[1] > mr[2] >= 1.5, mr)
    # tap-tap on the harder levels: rotated holes (4), the rocking box (6), the sliding holes (7): it turns itself and follows the hole
    for lv in (4, 6, 7):
        await page.evaluate(f"{S}.setLevel({lv})"); await page.wait_for_timeout(500)
        st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes, sym: {S}.sym }})")
        i, s = max(enumerate(st['shapes']), key=lambda q: abs(next(h for h in st['holes'] if h['kind'] == q[1]['kind'])['angle']) * (1 if st['sym'][q[1]['kind']] else 0))
        await tap(page, s['x'], s['y'])
        hj = next(j for j, h in enumerate(await page.evaluate(f"{S}.holes")) if h['kind'] == s['kind'])
        h = (await page.evaluate(f"{S}.holes"))[hj]
        await page.evaluate(f"fing('pointerdown', 1, {h['x']}, {h['y']})"); await page.wait_for_timeout(40); await page.evaluate(f"fing('pointerup', 1, {h['x']}, {h['y']})")
        await wait(page, f"{S}.shapes[{i}].anim === 'fly'", 2000)
        hx0 = await page.evaluate(f"[{S}.holes[{hj}].x, {S}.holes[{hj}].angle]")
        ok = await wait(page, f"{S}.shapes[{i}].placed", 4000)
        hx1 = await page.evaluate(f"[{S}.holes[{hj}].x, {S}.holes[{hj}].angle]")
        moving = (lv == 4) or abs(hx1[0] - hx0[0]) > 0.3 or abs(hx1[1] - hx0[1]) > 0.0005
        check(f'{tag} phone: tap-tap on level {lv} ({ {4: "rotated holes", 6: "rocking box", 7: "sliding holes"}[lv]}): the {s["kind"]} turns itself, follows its moving hole and drops in', ok and moving, [s['kind'], hx0, hx1])
    check(tag + ' phone (tap): no page errors', not errs, errs); await ctx.close()

async def click_click(b):
    ctx, page, errs = await ctx_page(b)
    await page.click('.modes button[data-mode=shapes]'); await wait(page, "mode === 'mouse' && gameMode === 'shapes'"); await page.wait_for_timeout(600)
    st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes }})")
    s0 = st['shapes'][1]; hl = next(h for h in st['holes'] if h['kind'] == s0['kind'])
    await page.mouse.click(s0['x'] + 3, s0['y'] + 3); await page.wait_for_timeout(150)
    sel = await page.evaluate(f"{S}.sel")
    check('mouse: assists off (a mouse drag stays exact)', not await page.evaluate(f"{S}.assist"))
    await page.mouse.click(hl['x'], hl['y'])
    ok = await wait(page, f"{S}.shapes[1].placed", 4000)
    check('mouse: click a shape, then click its hole: it flies in (click-click)', sel == 1 and ok, sel)
    check('mouse click-click: no page errors', not errs, errs); await ctx.close()

# ---- big shapes (a 2-year-old on a phone): levels 1-3 ~1.5x the classic size (a shape >= ~30% of the screen width), a gradual step back from
# level 4, never smaller than the classic size; no overlaps on the mat or in the box (pixel test of the real outlines); the toddler aids scale ----
# the classic S (before this change) per level 1..10, measured with the old layout
CLASSIC = {(360, 740): [36.6, 42.1, 36.2, 35.9, 35.9, 35.9, 29.3, 28.1, 22.9, 19.5], (390, 844): [39.7, 45.6, 39.2, 38.9, 38.9, 38.9, 31.7, 30.5, 25.9, 21.1],
           (412, 915): [41.9, 48.2, 41.5, 41.1, 41.1, 41.1, 33.5, 32.2, 27.3, 22.3], (1280, 800): [70, 63, 58.8, 56, 56, 56, 56, 56, 51.6, 45.7],
           (740, 360): [33.8, 22.8, 22.2, 22.9, 22.9, 20.3, 22.9, 19.5, 22.9, 18]}
OVERLAP_JS = r"""(() => { // pixel test of the real outlines: the mat's shapes (at home, upright) and the holes' recesses never overlap; each stays inside its mat / lid
  const c = document.createElement('canvas'); c.width = innerWidth; c.height = innerHeight; const g = c.getContext('2d', { willReadFrequently: true });
  const S = shapes.S, b = shapes.box, m = shapes.mat, its = [];
  for (const s of shapes.shapes) its.push({ k: s.kind, x: s.hx, y: s.hy, a: 0, r: S, w: 'mat', pad: 2 });
  for (const h of shapes.holes) its.push({ k: h.kind, x: h.x, y: h.y, a: h.wa, r: S * 1.08, w: 'box', pad: 1 });
  const draw = (it, pad) => { g.save(); g.lineJoin = 'round'; g.translate(it.x, it.y); g.rotate(it.a); shapePath(g, it.k, it.r); g.fill(); if (pad) { g.lineWidth = pad * 2; g.stroke(); } g.restore(); };
  const any = (x0, y0, x1, y1) => { x0 = Math.max(0, Math.floor(x0)); y0 = Math.max(0, Math.floor(y0)); x1 = Math.min(c.width, Math.ceil(x1)); y1 = Math.min(c.height, Math.ceil(y1)); if (x1 <= x0 || y1 <= y0) return 0;
    const d = g.getImageData(x0, y0, x1 - x0, y1 - y0).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 40) n++; return n; };
  const over = [], out = [];
  for (let i = 0; i < its.length; i++) for (let j = i + 1; j < its.length; j++) {
    const A = its[i], B = its[j]; if (A.w !== B.w) continue; const R = 1.6 * S + 4;
    const x0 = Math.max(A.x, B.x) - R, x1 = Math.min(A.x, B.x) + R, y0 = Math.max(A.y, B.y) - R, y1 = Math.min(A.y, B.y) + R; if (x1 <= x0 || y1 <= y0) continue;
    g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, c.width, c.height); g.fillStyle = g.strokeStyle = '#f00'; draw(A, A.pad); g.globalCompositeOperation = 'source-in'; draw(B, B.pad);
    const n = any(x0, y0, x1, y1); if (n) over.push([A.w, A.k, B.k, n]);
  }
  for (const it of its) { // inside: the shape on the mat, the hole and its rim on the lid
    g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, c.width, c.height); g.fillStyle = g.strokeStyle = '#f00'; draw(it, it.w === 'box' ? Math.max(4, S * 0.17) : 0);
    g.globalCompositeOperation = 'destination-out'; g.fillStyle = '#000'; if (it.w === 'mat') g.fillRect(m.x, m.y, m.w, m.h); else g.fillRect(b.x - b.w / 2, b.y - b.h / 2, b.w, b.h);
    const n = any(it.x - 1.8 * S, it.y - 1.8 * S, it.x + 1.8 * S, it.y + 1.8 * S); if (n) out.push([it.w, it.k, n]);
  }
  return { over, out, S, n: shapes.shapes.length, grid: shapes.grid, matBottom: m.y + m.h, boxTop: b.y - b.h / 2 - Math.abs(Math.sin(b.rock || 0)) * b.w / 2 };
})()"""

async def big_layout(b, w, h, mobile, he=False, shots=()):
    tag = f'{w}x{h}' + ('_he' if he else '')
    ctx = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2, is_mobile=mobile, has_touch=mobile)
    page = await ctx.new_page(); await routes(page); errs = []; page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + SPEECH + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');"))
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_function("typeof engine !== 'undefined' && !!engine", timeout=15000)
    await (page.tap if mobile else page.click)('.modes button[data-mode=shapes]'); await wait(page, "gameMode === 'shapes' && !!shapes.box", 15000); await page.wait_for_timeout(300)
    sizes, bad = [], []
    for n in range(1, 11):
        worst = None
        for rep in range(1 if n == 1 else 4): # random kinds (and hole angles from level 4): a few builds per level
            r = await page.evaluate(f"(() => {{ __grasp.shapes.setLevel({n}); return {OVERLAP_JS}; }})()")
            if r['over'] or r['out'] or r['matBottom'] > r['boxTop'] + 0.5: bad.append((n, r))
            worst = r if worst is None or r['S'] < worst['S'] else worst
        sizes.append(worst['S'])
        if n in shots:
            await page.evaluate(f"__grasp.shapes.setLevel({n}); shapes.demo = null"); await page.wait_for_timeout(700)
            await page.screenshot(path=f'tests/out/shapes_big_{shots[n]}.png')
    check(f'big {tag}: levels 1-10 fit with no overlaps on the mat or in the box, everything inside its mat / lid', not bad, bad[:3])
    cl = CLASSIC[(w, h)]
    check(f'big {tag}: never smaller than the classic size (levels 1-10)', all(sizes[i] >= cl[i] - 0.5 for i in range(10)), [(round(a, 1), c) for a, c in zip(sizes, cl)])
    if mobile and w < h:
        check(f'big {tag}: levels 1-3 very big: a shape >= 30% of the screen width ({", ".join(f"{2 * x / w:.0%}" for x in sizes[:3])}), >= 1.3x the classic level-2 size',
              all(2 * x >= 0.30 * w for x in sizes[:3]) and sizes[1] >= 1.3 * cl[1], [round(x, 1) for x in sizes])
        check(f'big {tag}: then a gradual step back (3 > 4 >= 5 >= 6, level 8 near the classic size)', sizes[3] < sizes[2] and sizes[4] <= sizes[3] + 0.5 and sizes[5] <= sizes[4] + 0.5 and sizes[7] < sizes[3] and sizes[7] / cl[7] < sizes[0] / cl[0], [round(x, 1) for x in sizes])
    else:
        check(f'big {tag}: early levels bigger than the classic size but capped by the height (no giant blobs: S <= 12% of the height)', sizes[0] >= cl[0] and max(sizes) <= 0.12 * h + 0.5 and (w < 1000 or sizes[0] >= 1.25 * cl[0]), [round(x, 1) for x in sizes])
    check(f'big {tag}: no page errors', not errs, errs); await ctx.close()
    return sizes

async def big_play(b, he):
    tag = 'he' if he else 'en'
    ctx, page, errs = await ctx_page(b, True, he, init=FING_W)
    await page.tap('.modes button[data-mode=shapes]'); await wait(page, "mode === 'mouse' && gameMode === 'shapes'"); await page.wait_for_timeout(700)
    ok = await wait(page, f"!!{S}.ui.demo && {S}.ui.demo.on", 4000)
    d = await page.evaluate(f"{S}.ui.demo")
    check(tag + ' big: the finger demo grows with the shapes', ok and d and d.get('scale', 0) > 1.2, d)
    await page.evaluate(SFX_JS)
    for lv in (1, 3):
        await page.evaluate(f"{S}.setLevel({lv})"); await page.wait_for_timeout(500)
        st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes, S: {S}.S, big: {S}.big, R: {S}.grabR, M: {S}.magnetR, slop: {S}.slop, lift: {S}.lift }})")
        S_ = st['S']
        # tap-tap: a tap near the shape's edge picks it, a tap on the hole's rim sends it in
        s0 = st['shapes'][0]; hl = next(h for h in st['holes'] if h['kind'] == s0['kind'])
        await tap(page, s0['x'] + 0.9 * S_, s0['y'] + 0.3 * S_, jitter=int(st['slop'] - 4))
        ok = await wait(page, f"{S}.sel === 0", 2000)
        ai = await page.evaluate(f"({{ S: {S}.S, big: {S}.big, R: {S}.grabR, M: {S}.magnetR, H: {S}.helpR, slop: {S}.slop, lift: {S}.lift, assist: {S}.assist }})")  # (touch: the assists are on)
        check(f'{tag} big L{lv}: the aids scale with the shapes (grab {ai["R"]:.0f} px = 1.75 S, magnet = 2.4 S, help = 4.2 S, lift {ai["lift"]:.0f} > 40, slop {ai["slop"]:.0f} > 20)',
              ai['assist'] and ai['big'] > 1.15 and abs(ai['R'] - 1.75 * S_) < 1 and abs(ai['M'] - 2.4 * S_) < 1 and abs(ai['H'] - 4.2 * S_) < 1 and ai['lift'] > 44 and ai['slop'] > 22, ai)
        if lv == 1: await page.wait_for_timeout(200); await page.screenshot(path=f'tests/out/shapes_big_tap_selected_{tag}.png')
        await page.evaluate("rings.length = 0")
        await tap(page, hl['x'] - 1.2 * S_, hl['y'])
        ok2 = await wait(page, f"{S}.shapes[0].placed", 3000)
        rw = await page.evaluate("Math.max(0, ...rings.map(r => r.width))")
        check(f'{tag} big L{lv}: tap the shape (at its edge, a {st["slop"] - 4:.0f} px wobble), then the hole (at its rim): it flies in; a wider ring', ok and ok2 and rw > 6.5, [ok, ok2, rw])
        if lv == 1: await page.wait_for_timeout(250); await page.screenshot(path=f'tests/out/shapes_big_placed_{tag}.png')
        # a touch drag: the shape rides lift px above the finger; let go over the hole: in
        st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes }})")
        s1 = st['shapes'][1]; hl = next(h for h in st['holes'] if h['kind'] == s1['kind'] and not h['filled'])
        await fdrag(page, s1['x'], s1['y'] + 0.5 * S_, hl['x'], hl['y'] + await page.evaluate(f"{S}.lift"), up=False)
        hi = await page.evaluate(f"({{ h: {S}.heldInfo, y: {S}.shapes[1].y, m: {S}.magnet }})")
        if lv == 1: await page.screenshot(path=f'tests/out/shapes_big_drag_{tag}.png')
        await page.evaluate(f"fing('pointerup', 1, {hl['x']}, {hl['y']})")
        ok = await wait(page, f"{S}.shapes[1].placed", 3000)
        check(f'{tag} big L{lv}: a touch drag from the shape\'s lower half: held above the finger, pulled by its hole\'s magnet, let go: in', ok and hi['h'] and hi['h']['i'] == 1 and hi['h']['oy'] < -44 and hi['m'] >= 0, hi)
    check(tag + ' big: no page errors', not errs, errs); await ctx.close()

async def big_tests(b):
    for (w, h) in ((360, 740), (390, 844), (412, 915)):
        await big_layout(b, w, h, True, shots={1: f'phone_l1_{w}', 2: f'phone_l2_{w}', 3: f'phone_l3_{w}', 4: f'phone_l4_{w}', 8: f'phone_l8_{w}'} if w == 360 else {1: f'phone_l1_{w}'})
    await big_layout(b, 360, 740, True, he=True, shots={1: 'phone_l1_he', 3: 'phone_l3_he'})
    await big_layout(b, 1280, 800, False, shots={1: 'desktop_l1', 4: 'desktop_l4'})
    await big_layout(b, 740, 360, True, shots={1: 'landscape_l1'})
    for he in (False, True): await big_play(b, he)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])

        # ---- desktop, mouse: the tile starts the game; level 1 ----
        ctx, page, errs = await ctx_page(b)
        check('speechSynthesis stub installed', await page.evaluate("!window.__speechStubFailed && typeof speechSynthesis.speak === 'function'"), await page.evaluate("window.__speechStubFailed || ''"))
        await page.click('.modes button[data-mode=shapes]')
        ok = await wait(page, "mode === 'mouse' && gameMode === 'shapes' && $('start').hidden")
        check('the Shapes tile starts the game at once (mouse)', ok, await page.evaluate("[mode, gameMode]"))
        await page.evaluate(SFX_JS); await page.wait_for_timeout(500)
        st = await page.evaluate(f"({{ level: {S}.level, shapes: {S}.shapes, holes: {S}.holes, held: {S}.held, phase: {S}.phase }})")
        kinds = sorted(s['kind'] for s in st['shapes'])
        check('level 1: 3 big shapes (circle, square, triangle) and a matching hole for each', st['level'] == 1 and kinds == ['circle', 'square', 'triangle'] and sorted(h['kind'] for h in st['holes']) == kinds and not any(s['placed'] for s in st['shapes']) and st['held'] == -1 and st['phase'] == 'play', st)
        check('level 1: holes unrotated, shapes upright, all on screen; the box below the mat', all(abs(h['angle']) < 1e-6 for h in st['holes']) and all(0 < s['x'] < 1280 and 0 < s['y'] < 800 for s in st['shapes']) and min(h['y'] for h in st['holes']) > max(s['y'] for s in st['shapes']), st)
        check('level 1: big shapes (>= 100 px on a desktop)', st['shapes'][0]['size'] >= 100, st['shapes'][0]['size'])
        await page.screenshot(path='tests/out/shapes_l1_desktop.png')

        # drag a shape onto its hole: lifts while held, clunk + rising chime, the spoken name
        s0 = st['shapes'][0]; h0 = next(h for h in st['holes'] if h['kind'] == s0['kind'])
        await drag(page, s0['x'] + 6, s0['y'] + 4, h0['x'] + 6, h0['y'] + 4)
        hd = await page.evaluate(f"({{ held: {S}.held, x: {S}.shapes[0].x, y: {S}.shapes[0].y, lift: __grasp.shapes.held >= 0 ? shapes.held.s.lift : 0 }})")
        check('mouse press on a shape grabs it; it follows the pointer and lifts', hd['held'] == 0 and abs(hd['x'] - h0['x']) < 3 and abs(hd['y'] - h0['y']) < 3 and hd['lift'] > 0.5, hd)
        await page.screenshot(path='tests/out/shapes_held.png')
        await page.mouse.up()
        ok = await wait(page, f"{S}.shapes[0].placed && !{S}.shapes[0].anim")
        r = await page.evaluate(f"({{ placed: {S}.shapes[0].placed, held: {S}.held, sfx: __sfx.slice(), sounds: {S}.sounds.slice(), spoken: {S}.spoken, said: __spoken.slice(), filled: {S}.holes.filter(h => h.filled).map(h => h.kind), ev: __grasp.events.slice(-3) }})")
        names = {'circle': 'Circle', 'square': 'Square', 'triangle': 'Triangle'}
        check('released over its hole: it drops in (placed, the hole filled)', ok and r['placed'] and r['held'] == -1 and r['filled'] == [s0['kind']], r)
        check('a clunk and a rising chime', 'clunk' in r['sfx'] and 'rise' in r['sfx'] and r['sounds'][-2:] == ['clunk', 'rise'], r['sfx'])
        check('the name is spoken in English (' + names[s0['kind']] + ', en-US)', r['spoken'] == names[s0['kind']] and r['said'] and r['said'][-1] == {'text': names[s0['kind']], 'lang': 'en-US'}, r['said'])
        check('track("shape") counts for the mission', ['shape', 1] in r['ev'], r['ev'])

        # the wrong hole: a soft boing, it hops back home, the box keeps its holes
        st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes }})")
        i1 = next(i for i, s in enumerate(st['shapes']) if not s['placed']); s1 = st['shapes'][i1]
        wh = next(h for h in st['holes'] if not h['filled'] and h['kind'] != s1['kind'])
        await page.evaluate("__sfx.length = 0")
        await drag(page, s1['x'], s1['y'], wh['x'], wh['y']); await page.mouse.up()
        await page.wait_for_timeout(80)
        w = await page.evaluate(f"({{ placed: {S}.shapes[{i1}].placed, anim: {S}.shapes[{i1}].anim, sfx: __sfx.slice(), mistakes: {S}.mistakes, filled: {S}.holes.filter(h => h.filled).length }})")
        check('wrong hole: not placed, a boing, it bounces back (a mistake counted)', not w['placed'] and w['anim'] == 'back' and 'boing' in w['sfx'] and 'clunk' not in w['sfx'] and w['mistakes'] == 1 and w['filled'] == 1, w)
        ok = await wait(page, f"!{S}.shapes[{i1}].anim")
        bk = await page.evaluate(f"{S}.shapes[{i1}]")
        check('...and lands back on its spot on the mat', ok and abs(bk['x'] - s1['x']) < 1 and abs(bk['y'] - s1['y']) < 1, [bk, s1])
        # dropped on the mat: stays there
        await drag(page, s1['x'], s1['y'], s1['x'] + 60, s1['y'] + 10); await page.mouse.up(); await page.wait_for_timeout(150)
        mv = await page.evaluate(f"{S}.shapes[{i1}]")
        check('dropped on the mat: it stays where it was let go', abs(mv['x'] - (s1['x'] + 60)) < 2 and abs(mv['y'] - (s1['y'] + 10)) < 2 and not mv['placed'] and mv['anim'] is None, mv)

        # level completed: confetti, stars, coins, Grippy's spoken cheer, then the 'Level 2' banner and 4 shapes
        c0 = await page.evaluate("__grasp.profile.coins")
        await page.evaluate("__sfx.length = 0; __grasp.grippy.cool()")
        n_ok = await page.evaluate(f"{S}.shapes.map((s, i) => s.placed ? true : {S}.placeTest(i))")
        check('placeTest(i) drops each remaining shape into its hole', all(n_ok), n_ok)
        ok = await wait(page, f"{S}.phase === 'done'")
        await page.wait_for_timeout(900)
        res = await page.evaluate(f"({{ phase: {S}.phase, res: {S}.result, coins: __grasp.profile.coins, sfx: __sfx.slice(), grip: __grasp.grippy.said.map(x => x.event), spoken: __spoken.slice(), particles: particles.length, best: localStorage.getItem('shapesBest'), done: {S}.levelsDone, stars: {S}.stars }})")
        rr = res['res'] or {}
        check('level 1 done: the result (1 mistake: 2 stars), coins via ECONOMY.shapes (2), levelup sound, confetti', ok and rr.get('level') == 1 and rr.get('stars') == 2 and rr.get('coins') == 2 and res['coins'] - c0 == 2 and 'levelup' in res['sfx'] and res['particles'] > 40, [res, c0])
        lv = await page.evaluate("__grasp.grippy.lines.en.shapesLevel")
        check('Grippy: a level-done line spoken aloud (EN, en-US); best level saved', 'shapesLevel' in res['grip'] and any(x['text'] in lv and x['lang'] == 'en-US' for x in res['spoken']) and res['best'] == '1' and res['done'] == 1 and res['stars'] == 2, res)
        check('ECONOMY.shapes: 2 a level, +1 for 3 stars', await page.evaluate("ECONOMY.shapes.level === 2 && ECONOMY.shapes.star3 === 1"))
        await page.screenshot(path='tests/out/shapes_level_done.png')
        ok = await wait(page, f"{S}.phase === 'banner'", 6000)
        bn = await page.evaluate(f"({{ level: {S}.level, n: {S}.shapes.length, holes: {S}.holes.length }})")
        check("then a 'Level 2' banner with the next level's 4 shapes", ok and bn == {'level': 2, 'n': 4, 'holes': 4}, bn)
        await page.wait_for_timeout(250); await page.screenshot(path='tests/out/shapes_banner.png')
        ok = await wait(page, f"{S}.phase === 'play'", 4000)
        check('...and level 2 is playable', ok)
        # a perfect, quick level: 3 stars, 3 coins
        c1 = await page.evaluate("__grasp.profile.coins")
        await page.evaluate(f"{S}.shapes.forEach((s, i) => {S}.placeTest(i))")
        await wait(page, f"{S}.phase === 'done'")
        rr = await page.evaluate(f"{S}.result")
        check('a quick level without mistakes: 3 stars and 3 coins', rr['stars'] == 3 and rr['coins'] == 3 and await page.evaluate("__grasp.profile.coins") - c1 == 3, rr)

        # Hebrew: the names are spoken in Hebrew
        await page.evaluate("setLang('he'); __grasp.shapes.setLevel(1)"); await page.wait_for_timeout(200)
        heb = {'circle': 'עיגול', 'square': 'ריבוע', 'triangle': 'משולש'}
        said = []
        for i in range(3):
            kd = await page.evaluate(f"{S}.shapes[{i}].kind"); await page.evaluate(f"{S}.placeTest({i})")
            said.append([kd, await page.evaluate(f"{S}.spoken"), await page.evaluate("__spoken[__spoken.length - 1]")])
        check('HE: the names are spoken in Hebrew (he-IL): ' + ', '.join(x[1] for x in said), all(x[1] == heb[x[0]] and x[2] == {'text': heb[x[0]], 'lang': 'he-IL'} for x in said), said)
        allnames = await page.evaluate("__grasp.shapes.kinds.map(k => [I18N.en['shp_' + k], I18N.he['shp_' + k]])")
        check('all 12 shapes have EN and HE names', len(allnames) == 12 and [x[1] for x in allnames] == ['עיגול', 'ריבוע', 'משולש', 'כוכב', 'לב', 'משושה', 'מלבן', 'אליפסה', 'סהר', 'מעוין', 'צלב', 'מחומש'] and all(x[0] for x in allnames), allnames)
        await page.evaluate("setLang('en')")

        # level 3: 4 shapes in similar colours; level 5: 6 shapes, two of them in another one's colour
        await page.evaluate(f"{S}.setLevel(3)"); l3 = await page.evaluate(f"{S}.shapes")
        warm = await page.evaluate("SHAPE_WARM")
        check('level 3: 4 shapes (toddler-big levels 1-3) in similar (warm) colours', len(l3) == 4 and all(s['color'] in warm for s in l3), [s['color'] for s in l3])
        await page.evaluate(f"{S}.setLevel(5)"); l5 = await page.evaluate(f"{S}.shapes")
        cols = [s['color'] for s in l5]
        check('level 5: 6 shapes, two decoys share a colour with another shape (different outline)', len(l5) == 6 and len(set(cols)) == 4 and len({s['kind'] for s in l5}) == 6, cols)

        # level 4: rotated holes. Unturned: it bounces; the wheel turns it 15° a notch; > 25° off no snap, within 25° it snaps; then it drops in
        await page.evaluate(f"{S}.setLevel(4)"); await page.wait_for_timeout(300)
        st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes, sym: {S}.sym }})")
        def diff(a, b, sym):
            if not sym: return 0
            P = 2 * math.pi / sym; d = ((a - b) % P + P) % P
            return d - P if d > P / 2 else d
        rot = [h for h in st['holes'] if st['sym'][h['kind']] and abs(diff(0, h['angle'], st['sym'][h['kind']])) > math.radians(30)]
        check('level 4: rotated holes (the turnable ones > 25° off upright)', len(st['holes']) == 5 and len(rot) >= 2 and all(abs(diff(0, h['angle'], st['sym'][h['kind']])) > math.radians(25) for h in st['holes'] if st['sym'][h['kind']] and st['sym'][h['kind']] < 6), [(h['kind'], round(math.degrees(h['angle']))) for h in st['holes']])
        hole = max(rot, key=lambda h: abs(diff(0, h['angle'], st['sym'][h['kind']])))
        si = next(i for i, s in enumerate(st['shapes']) if s['kind'] == hole['kind']); sh = st['shapes'][si]; sym = st['sym'][hole['kind']]
        await page.evaluate("__sfx.length = 0")
        await drag(page, sh['x'], sh['y'], hole['x'], hole['y']); await page.mouse.up(); await page.wait_for_timeout(80)
        bo = await page.evaluate(f"({{ placed: {S}.shapes[{si}].placed, anim: {S}.shapes[{si}].anim, sfx: __sfx.slice(), mistakes: {S}.mistakes }})")
        check('rotated hole, unturned shape: it does not fit (boing, back home; no mistake: right hole)', not bo['placed'] and bo['anim'] == 'back' and 'boing' in bo['sfx'] and bo['mistakes'] == 0, [bo, hole['kind'], math.degrees(hole['angle'])])
        await wait(page, f"!{S}.shapes[{si}].anim")
        sh = await page.evaluate(f"{S}.shapes[{si}]")
        need = -diff(sh['angle'], hole['angle'], sym)  # the turn that fits
        notches = round(need / math.radians(15)); sign = 1 if notches > 0 else -1
        await drag(page, sh['x'], sh['y'], hole['x'], hole['y'])
        k1 = max(k for k in range(abs(notches) + 1) if abs(need - k * sign * math.radians(15)) > math.radians(27))  # the most notches that still leave it > 27° off
        for k in range(k1): await page.mouse.wheel(0, 100 * sign); await page.wait_for_timeout(40)
        await page.wait_for_timeout(200)
        a1 = await page.evaluate(f"{S}.shapes[{si}].angle"); off1 = diff(a1, hole['angle'], sym)
        check(f'the wheel turns the held shape 15° a notch; still {abs(math.degrees(off1)):.0f}° off (> 25°): no snap', abs(off1) > math.radians(25) and abs(abs(math.degrees(off1)) - abs(math.degrees(need - k1 * sign * math.radians(15)))) < 0.5, [math.degrees(a1), math.degrees(off1), notches, k1])
        for k in range(abs(notches) - k1): await page.mouse.wheel(0, 100 * sign); await page.wait_for_timeout(40)
        await page.wait_for_timeout(400)
        a2 = await page.evaluate(f"{S}.shapes[{si}].angle"); off2 = diff(a2, hole['angle'], sym)
        check(f'more notches: within 25° it snaps to the hole\'s angle ({math.degrees(off2):.2f}° off)', abs(off2) < math.radians(0.5), [math.degrees(a2), math.degrees(hole['angle'])])
        await page.screenshot(path='tests/out/shapes_rotated.png')
        await page.mouse.up()
        ok = await wait(page, f"{S}.shapes[{si}].placed")
        check('...and it drops into the rotated hole', ok)
        # snapping tolerance at the release: 20° off fits, 30° off does not
        st = await page.evaluate(f"({{ shapes: {S}.shapes, sym: {S}.sym }})")
        cand = [(i, s) for i, s in enumerate(st['shapes']) if not s['placed'] and st['sym'][s['kind']] in (1, 2, 3, 4, 5)]
        if cand:
            i, s = cand[0]
            tol = await page.evaluate(f"""(() => {{ const sh = shapes.shapes[{i}], j = shapes.holes.findIndex(h => !h.filled && h.kind === sh.kind), h = shapes.holes[j], out = [];
              for (const deg of [30, 20]) {{ sh.anim = null; sh.x = h.x; sh.y = h.y; sh.angle = h.wa + deg * Math.PI / 180; shapes.held = {{ i: {i}, s: sh, ox: 0, oy: 0, roll: 0, tw: 0, two: false, t0: 0, overSince: 0, overHole: -1 }}; shapesRelease(performance.now()); out.push([deg, sh.placed]); }}
              return out; }})()""")
            check('release tolerance: 30° off bounces, 20° off drops in (snaps to the hole)', tol == [[30, False], [20, True]], tol)

        # levels 6 / 7: the box rocks; the holes slide; a shape still drops in while they move
        await page.evaluate(f"{S}.setLevel(6)"); a = await page.evaluate(f"{S}.box.angle"); await page.wait_for_timeout(900); b2 = await page.evaluate(f"{S}.box.angle")
        h6 = await page.evaluate(f"{S}.holes[0]"); await page.wait_for_timeout(300); h6b = await page.evaluate(f"{S}.holes[0]")
        check('level 6: the box slowly rocks (its holes turn with it)', abs(b2 - a) > 0.005 and abs(b2) < 0.25 and abs(h6b['angle'] - h6['angle']) > 0.001, [a, b2])
        await page.screenshot(path='tests/out/shapes_l6.png')
        await page.evaluate(f"{S}.setLevel(7)"); x0 = await page.evaluate(f"{S}.holes[0].x"); await page.wait_for_timeout(900); x1 = await page.evaluate(f"{S}.holes[0].x")
        check('level 7: the holes slide left / right (the box does not rock)', abs(x1 - x0) > 3 and await page.evaluate(f"{S}.box.angle") == 0, [x0, x1])
        ok = await page.evaluate(f"{S}.placeTest(0)")
        check('level 7: a shape still drops into its sliding hole', ok)
        await page.evaluate(f"{S}.setLevel(9)"); l9 = await page.evaluate(f"({{ n: {S}.shapes.length, spec: {S}.spec }})")
        check('level 8+: more shapes, faster motion', l9['n'] == 8 and l9['spec']['slideW'] > (await page.evaluate("shapeLevelSpec(7).slideW")), l9)

        # Home: the round-over card (levels done, stars, best level), then home; the tile shows the best level
        await menu_click(page, '#homeBtn'); await page.wait_for_timeout(700)
        ec = await page.evaluate(f"({{ over: {S}.over, mode, b: {S}.ui.buttons, done: {S}.levelsDone, stars: {S}.stars, best: localStorage.getItem('shapesBest'), nb: {S}.ui.newBest }})")
        check('Home in a Shapes round: the round-over card first (levels done 2, stars 5, best level 2 saved, new best)', ec['over'] and ec['mode'] == 'mouse' and ec['b'] and 'home' in ec['b'] and ec['done'] == 2 and ec['stars'] == 5 and ec['best'] == '2' and ec['nb'], ec)
        await page.screenshot(path='tests/out/shapes_endcard.png')
        hb = ec['b']['home']; await page.mouse.click(hb['x'] + hb['w'] / 2, hb['y'] + hb['h'] / 2); await page.wait_for_timeout(400)
        check("the card's Home goes to the start screen; the tile shows the best level", await page.evaluate("mode === 'none' && !$('start').hidden") and await page.evaluate("document.querySelector('.modes button[data-mode=shapes] .best').textContent") == '★ L2')
        check('mission pool: "Sort 15 shapes"', await page.evaluate("(() => { const m = __grasp.missionPool.find(q => q.id === 'shapes'); return !!m && m.ev === 'shape' && m.goals[0] === 15 && t('ms_shapes', { n: 15 }) === 'Sort 15 shapes'; })()"))
        gl = await page.evaluate("({ en: __grasp.grippy.lines.en, he: __grasp.grippy.lines.he })")
        check('Grippy (voice): >= 3 short (1-3 words) distinct lines EN / HE for a level done; a match is quiet (the shape name is spoken instead)', all(len(gl[l]['shapesLevel']) >= 3 and len(set(gl[l]['shapesLevel'])) == len(gl[l]['shapesLevel']) and all(1 <= len(x.split()) <= 3 for x in gl[l]['shapesLevel']) for l in ('en', 'he')) and 'shapesMatch' not in gl['en'] and 'shapesMatch' not in gl['he'])
        await page.click('.modes button[data-mode=shapes]'); await page.wait_for_timeout(300)
        check('a new round starts at level 1 with nothing sorted', await page.evaluate(f"{S}.level === 1 && !{S}.over && {S}.levelsDone === 0 && {S}.shapes.every(s => !s.placed)"))
        check('desktop: no page errors', not errs, errs); await ctx.close()

        # ---- phone, touch: a two-finger twist turns the held shape; HE screenshots ----
        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx, page, errs = await ctx_page(b, True, he)
            await page.tap('.modes button[data-mode=shapes]'); await wait(page, "mode === 'mouse' && gameMode === 'shapes'"); await page.wait_for_timeout(600)
            st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes, box: {S}.box, mat: {S}.mat }})")
            check(tag + ' phone: level 1 fits the screen (mat over the box, all shapes and holes inside)', all(12 <= s['x'] <= 348 and st['mat']['y'] <= s['y'] <= st['mat']['y'] + st['mat']['h'] for s in st['shapes']) and all(0 < h['x'] < 360 and h['y'] < 740 for h in st['holes']) and st['box']['y'] + st['box']['h'] / 2 + st['box']['depth'] <= 740, st)
            await page.screenshot(path='tests/out/shapes_phone_' + tag + '.png')
            s0 = st['shapes'][0]; h0 = next(h for h in st['holes'] if h['kind'] == s0['kind'])
            await page.evaluate(f"(async () => {{ fing('pointerdown', 1, {s0['x']}, {s0['y']}); }})()"); await page.wait_for_timeout(150)
            g1 = await page.evaluate(f"{S}.held")
            await page.evaluate(f"fing('pointerdown', 2, {s0['x'] + 80}, {s0['y']})"); await page.wait_for_timeout(120)
            a0 = await page.evaluate(f"shapes.shapes[0].angle")
            for k in range(1, 7):
                ang = math.radians(5 * k)
                await page.evaluate(f"fing('pointermove', 2, {s0['x'] + 80 * math.cos(ang)}, {s0['y'] + 80 * math.sin(ang)})"); await page.wait_for_timeout(50)
            await page.wait_for_timeout(150)
            a1 = await page.evaluate(f"shapes.shapes[0].angle")
            check(tag + ' phone: one finger grabs, a second finger twisting 30° turns the held shape 30°', g1 == 0 and await page.evaluate(f"{S}.held") == 0 and abs(math.degrees(a1 - a0) - 30) < 2, [g1, math.degrees(a1 - a0)])
            await page.evaluate(f"fing('pointerup', 2, 0, 0)"); await page.wait_for_timeout(100)
            for k in range(1, 9):
                await page.evaluate(f"fing('pointermove', 1, {s0['x'] + (h0['x'] - s0['x']) * k / 8}, {s0['y'] + (h0['y'] - s0['y']) * k / 8})"); await page.wait_for_timeout(40)
            await page.wait_for_timeout(200)
            await page.evaluate(f"fing('pointerup', 1, {h0['x']}, {h0['y']})")
            ok = await wait(page, f"{S}.shapes[0].placed")
            check(tag + ' phone: back to one finger, dragged onto its hole: it drops in, the name spoken', ok and await page.evaluate(f"{S}.spoken") == ({'circle': 'עיגול', 'square': 'ריבוע', 'triangle': 'משולש'} if he else {'circle': 'Circle', 'square': 'Square', 'triangle': 'Triangle'})[s0['kind']])
            await page.evaluate(f"{S}.setLevel(8)"); await page.wait_for_timeout(500)
            st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes, box: {S}.box }})")
            check(tag + ' phone: level 8 (7 shapes) fits too', len(st['shapes']) == 7 and all(10 <= s['x'] <= 350 and 90 < s['y'] < st['box']['y'] - st['box']['h'] / 2 for s in st['shapes']), st)
            await page.screenshot(path='tests/out/shapes_phone_l8_' + tag + '.png')
            check(tag + ' phone: no page errors', not errs, errs); await ctx.close()

        # ---- toddler play: tap a shape, tap a hole; touch-drag help (phone EN / HE); mouse click-click ----
        for he in (False, True): await tap_tests(b, he)
        await big_tests(b)
        await click_click(b)

        # ---- camera stub: an open hand hovers, a pinch grabs, the pinched hand carries it to its hole, opening the hand drops it in ----
        ctx, page, errs = await ctx_page(b, camera=True)
        await page.click('#camBtn'); await page.click('.modes button[data-mode=shapes]')
        ok = await wait(page, "mode === 'camera' && gameMode === 'shapes'", 15000)
        check('camera: the Shapes tile starts the camera game', ok)
        await page.wait_for_timeout(500)
        st = await page.evaluate(f"({{ shapes: {S}.shapes, holes: {S}.holes }})")
        s0 = st['shapes'][1]; h0 = next(h for h in st['holes'] if h['kind'] == s0['kind'])
        await page.evaluate(f"window.__handFor = () => handAt({s0['x']}, {s0['y']}, 0.8)")
        ok = await wait(page, f"gesture === 'open' && !pause.on && !pause.resumeT && Math.hypot(cursor.x - {s0['x']}, cursor.y - {s0['y']}) < 20", 12000)
        check('camera: an open hand over a shape (no grab yet)', ok and await page.evaluate(f"{S}.held") == -1, await page.evaluate("[gesture, cursor.x, cursor.y, pause.on]"))
        await page.evaluate(f"window.__handFor = () => handAt({s0['x']}, {s0['y']}, 0.1)")
        ok = await wait(page, f"{S}.held === 1", 5000)
        check('camera: a pinch grabs the shape', ok, await page.evaluate("[gesture, " + S + ".held]"))
        await page.evaluate(f"lineHand({s0['x']}, {s0['y']}, {h0['x']}, {h0['y']}, 700, 0.1)")
        ok = await wait(page, f"Math.hypot({S}.shapes[1].x - {h0['x']}, {S}.shapes[1].y - {h0['y']}) < 12 && {S}.held === 1", 6000)
        check('camera: the pinched hand carries it over its hole', ok, await page.evaluate(f"[{S}.shapes[1], {S}.held]"))
        await page.screenshot(path='tests/out/shapes_camera.png')
        await page.evaluate(f"window.__handFor = () => handAt({h0['x']}, {h0['y']}, 0.8)")
        ok = await wait(page, f"{S}.shapes[1].placed", 5000)
        check('camera: opening the hand drops it in; its name is spoken', ok and await page.evaluate(f"{S}.spoken") == {'circle': 'Circle', 'square': 'Square', 'triangle': 'Triangle'}[s0['kind']])
        check('camera: no page errors', not errs, errs); await ctx.close()

        # ---- start screen: 6 tiles (3 x 2) fit 360 x 740 with no scroll and no big gap under the top bar, EN / HE; desktop too ----
        LAY = """(() => { const tiles = [...document.querySelectorAll('.modes > button[data-mode]')].map(b => { const r = b.getBoundingClientRect(); return { m: b.dataset.mode, in: r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight, top: Math.round(r.top), w: r.width, name: b.querySelector('[data-i18n]').textContent }; });
          const st = $('start'), h1 = document.querySelector('.panel h1').getBoundingClientRect(), lb = $('startLang').getBoundingClientRect(), pill = $('metaPill').getBoundingClientRect(), row = document.querySelector('.metaRow').getBoundingClientRect(), md = document.querySelector('.modes').getBoundingClientRect(), seg = document.querySelector('#start .seg').getBoundingClientRect(), a = document.querySelector('#start a.link').getBoundingClientRect();
          return { noScroll: document.documentElement.scrollHeight <= innerHeight && st.scrollHeight <= st.clientHeight + 1, tiles, rows: new Set(tiles.map(t => Math.round(t.top / 20))).size, barBottom: Math.max(h1.bottom, lb.bottom), pillTop: pill.top,
            gaps: [row.top - pill.bottom, md.top - row.bottom, seg.top - md.bottom, a.top - seg.bottom].map(Math.round), link: a.bottom <= innerHeight }; })()"""
        for mobile in (True, False):
            for he in (False, True):
                tag = ('phone_' if mobile else 'desktop_') + ('he' if he else 'en')
                ctx, page, errs = await ctx_page(b, mobile, he); await page.wait_for_timeout(1900)
                L = await page.evaluate(LAY)
                check(tag + ': 6 game tiles in 3 x 2, all on screen, named; no scroll', len(L['tiles']) == 6 and L['rows'] == 2 and all(t['in'] and t['w'] > 80 and t['name'] for t in L['tiles']) and L['noScroll'] and L['link'] and [t['m'] for t in L['tiles']] == ['sandbox', 'slice', 'smash', 'busy', 'strike', 'shapes'], L)
                check(tag + ': the Shapes tile is named ' + ('צורות' if he else 'Shapes'), L['tiles'][5]['name'] == ('צורות' if he else 'Shapes'))
                if mobile:
                    gap = L['pillTop'] - L['barBottom']
                    check(tag + f': no big gap under the top bar ({gap:.0f} px), the blocks evenly spaced', 0 <= gap <= 30 and max(L['gaps']) - min(L['gaps']) <= 12 and min(L['gaps']) >= 6, L)
                pv0 = await page.evaluate("document.querySelector('.modes button[data-mode=shapes] canvas').toDataURL()"); await page.wait_for_timeout(400)
                pv1 = await page.evaluate("document.querySelector('.modes button[data-mode=shapes] canvas').toDataURL()")
                check(tag + ': the Shapes tile has a live preview', pv0 != pv1 and await page.evaluate("__grasp.previews.running"))
                await page.screenshot(path='tests/out/shapes_start_' + tag + '.png')
                check(tag + ': no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
