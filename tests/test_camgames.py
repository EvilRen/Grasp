exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# The camera games (Air Drums, Bubble Pop, Air Painting, Catch the Stars): the start screen's "Camera games" tile (one screen, no scroll: phone
# 360x740 and desktop, EN / HE) opens a picker; each game starts from it and from its own link (/drums, /bubbles, /paint, /stars); the camera prompt
# when started by touch ("Play with touch" / "Turn on camera"); the corner pause menu; per game with the camera stub (window.__handFor, two hands
# where it matters) and with touch / mouse: a drum strike plays the right pad and its sound (two hands, numHands 2), the backing beat, Follow the
# light (the sequence, a wrong pad ends it, the card, a pet snack); bubbles pop (fingertips, taps), combos, golden ones, Calm (no timer, a treat),
# the round's card; painting draws with a pinch, stops on an open hand, the palette by dwell / tap, the magic brushes, erase (fist shake / tap twice),
# the PNG save (download / share); the basket follows the hand / finger, catches, bombs and clouds, the speed-up, the card. Screenshots:
# tests/out/cam_*.png. State changes are polled (timing-independent).
POINT_JS = """
window.mkPoint = (tx, ty) => { const L = Array.from({length:21}, () => ({x: tx, y: ty + 0.25, z: 0}));
  L[0] = {x: tx, y: ty + 0.35, z:0}; L[9] = {x: tx, y: ty + 0.20, z:0}; L[8] = {x: tx, y: ty, z:0}; L[6] = {x: tx, y: ty + 0.12, z:0}; L[4] = {x: tx, y: ty - 0.09, z:0};
  for (const [tip, pip] of [[12,10],[16,14],[20,18]]) { L[pip] = {x: tx + 0.02, y: ty + 0.17, z:0}; L[tip] = {x: tx + 0.02, y: ty + 0.24, z:0}; } return L; };
window.mkFist = (cx, cy) => { const L = Array.from({length:21}, () => ({x: cx, y: cy + 0.10, z: 0}));
  L[0] = {x: cx, y: cy + 0.30, z:0}; L[9] = {x: cx, y: cy + 0.10, z:0}; L[4] = {x: cx - 0.14, y: cy + 0.16, z:0};
  for (const [tip, pip] of [[8,6],[12,10],[16,14],[20,18]]) { L[pip] = {x: cx + 0.02, y: cy + 0.02, z:0}; L[tip] = {x: cx + 0.02, y: cy + 0.14, z:0}; } return L; };
window.fistAt = (X, Y) => { const B = __grasp.CONFIG.MAP_BOX, m = (1 - B) / 2; return mkFist(1 - (m + X / innerWidth * B), m + Y / innerHeight * B); };
// a hand that waits at (x, y0) for hold ms, then strikes down to y1 in ms and stays (a drum hit); two at once for two hands
window.strikeFn = (x, y0, y1, ms, hold) => { const t0 = performance.now(); return () => { const e = performance.now() - t0, k = Math.max(0, Math.min(1, (e - hold) / ms)); return handAt(x, y0 + (y1 - y0) * k, 0.8); }; };
window.strike1 = (x, y0, y1, ms, hold) => { window.__handFor = strikeFn(x, y0, y1, ms, hold); };
window.strike2 = (a, b, ms, hold) => { const f = strikeFn(a[0], a[1], a[2], ms, hold), g = strikeFn(b[0], b[1], b[2], ms, hold); window.__handFor = () => [f(), g()]; };
window.lineFn = (fn, x0, y0, x1, y1, ms) => { const t0 = performance.now(); window.__handFor = () => { const k = Math.min(1, (performance.now() - t0) / ms); return fn(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k); }; };
window.touchDrag = async (x0, y0, x1, y1, steps, ms) => { const c = document.getElementById('stage'); // one finger dragged as touch pointer events
  const ev = (t, x, y) => c.dispatchEvent(new PointerEvent(t, { pointerId: 7, pointerType: 'touch', isPrimary: true, clientX: x, clientY: y, bubbles: true, cancelable: true, button: 0, buttons: 1 }));
  ev('pointerdown', x0, y0); for (let i = 1; i <= steps; i++) { await new Promise((r) => setTimeout(r, ms)); ev('pointermove', x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps); } ev('pointerup', x1, y1); };
window.shakeFist = (x, y, amp, period) => { const t0 = performance.now(); window.__handFor = () => { const e = performance.now() - t0; return fistAt(x + amp * Math.sin(e / period * Math.PI * 2), y); }; };
"""
def chk(name, cond, extra=''): check(name, cond, '' if cond else extra)  # (the details only on a failure)
CG = "__grasp.cg"
FRAMES = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
OUT = 'tests/out/'

async def fresh(b, mobile=False, he=False, init='', cam=False):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(permissions=['camera'], **opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + HAND_JS + POINT_JS + "localStorage.setItem('lang','" + ('he' if he else 'en') + "');" + ("localStorage.setItem('inputPref','camera');" if cam else '') + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_function("typeof __grasp !== 'undefined' && !!__grasp.cg", timeout=10000); await page.wait_for_timeout(500)
    return ctx, page, errs

async def press(page, mobile, sel):
    if mobile: await page.tap(sel)
    else: await page.click(sel)

async def start_game(page, m, mobile=False, touch_ok=True, cam=False):
    # the tile opens the picker; the card starts the game (with the remembered input); 'Play with touch' closes the camera prompt
    await press(page, mobile, '#camGamesBtn'); await page.wait_for_function("!$('cgPick').hidden", timeout=4000)
    await press(page, mobile, f'#cgPick [data-cg={m}]')
    if cam:
        await page.wait_for_function(f"mode === 'camera' && gameMode === '{m}'", timeout=15000)
    else:
        await page.wait_for_function(f"mode === 'mouse' && gameMode === '{m}'", timeout=8000)
        if touch_ok and await page.evaluate(f"{CG}.asking"): await press(page, mobile, '#cgCamTouch')
    await page.evaluate("hideHint()"); await page.evaluate(FRAMES)

async def btn(page, key):  # a canvas button's centre (cg.btns, drawn last frame)
    await page.wait_for_function(f"{CG}.btns().some(b => b.key === '{key}')", timeout=4000)
    r = await page.evaluate(f"{CG}.btns().find(b => b.key === '{key}')")
    return r['x'] + r['w'] / 2, r['y'] + r['h'] / 2

async def click_btn(page, key, mobile=False):
    x, y = await btn(page, key)
    if mobile: await page.touchscreen.tap(x, y)
    else: await page.mouse.click(x, y)

async def home(page):
    await page.evaluate("goHome()"); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=5000)

START = """(() => { const st = $('start'), r = (el) => { const q = el.getBoundingClientRect(); return { l: q.left, r: q.right, t: q.top, b: q.bottom, w: q.width, h: q.height }; };
  const tiles = [...document.querySelectorAll('.modes > button[data-mode]')].map(b => r(b)), cam = r($('camGamesBtn')), pet = r($('petCorner')), seg = r($('camBtn')), link = r(document.querySelector('#start a.link'));
  const tx = $('camGamesBtn').querySelector('.ctTx b');
  return { noScroll: document.documentElement.scrollHeight <= innerHeight && st.scrollHeight <= st.clientHeight + 1, W: innerWidth, H: innerHeight, tiles, cam, pet, seg, link,
    label: tx.textContent, labelFits: tx.scrollWidth <= tx.clientWidth + 1, icons: $('camGamesBtn').querySelectorAll('.ctIcons svg').length }; })()"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--autoplay-policy=no-user-gesture-required'])

        # ---- the start screen: still one screen (phone + desktop, EN / HE, with the pet corner and the flame hint); the tile; the picker ----
        for mobile in (True, False):
            for he in (False, True):
                tag = ('phone ' if mobile else 'desktop ') + ('HE' if he else 'EN'); sfx = ('phone_' if mobile else 'desktop_') + ('he' if he else 'en')
                ctx, page, errs = await fresh(b, mobile, he, "localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, xpv: 2, habit: { streak: 2, last: '2020-01-01' } }));")
                await page.wait_for_timeout(900)
                L = await page.evaluate(START)
                inside = lambda q: q['l'] >= 0 and q['t'] >= 0 and q['r'] <= L['W'] + 0.5 and q['b'] <= L['H'] + 0.5 and q['w'] > 0
                chk(f'{tag}: the start screen has no scroll with the Camera games tile', L['noScroll'], L)
                chk(f'{tag}: the six game tiles, the Camera games tile, the toggle, the pet corner and the link all on screen', len(L['tiles']) == 6 and all(inside(q) for q in L['tiles']) and inside(L['cam']) and inside(L['seg']) and inside(L['pet']) and inside(L['link']), L)
                chk(f'{tag}: the tile is a full-width row under the grid, above the Camera | Touch toggle, named, 4 icons', L['cam']['t'] >= max(q['b'] for q in L['tiles']) and L['cam']['b'] <= L['seg']['t'] and L['cam']['w'] >= max(q['r'] for q in L['tiles']) - min(q['l'] for q in L['tiles']) - 1 and L['label'] == ('משחקי מצלמה' if he else 'Camera games') and L['labelFits'] and L['icons'] == 4, L)
                await page.screenshot(path=OUT + f'cam_start_{sfx}.png')
                await press(page, mobile, '#camGamesBtn'); await page.wait_for_function("!$('cgPick').hidden", timeout=4000); await page.wait_for_timeout(350)
                pk = await page.evaluate("""(() => { const s = $('cgPick').querySelector('.sheet').getBoundingClientRect(), cards = [...$('cgPick').querySelectorAll('[data-cg]')];
                  return { box: [s.left, s.top, s.right, s.bottom], W: innerWidth, H: innerHeight, cards: cards.map(c => [c.dataset.cg, c.querySelector('b').textContent, c.getBoundingClientRect().height]), cam: !$('cgPickCam').hidden, camText: $('cgPickCam').textContent }; })()""")
                chk(f'{tag}: the picker: four games, named, the sheet on screen', [c[0] for c in pk['cards']] == ['drums', 'bubbles', 'paint', 'stars'] and all(c[1] and c[2] >= 90 for c in pk['cards']) and pk['box'][0] >= 0 and pk['box'][2] <= pk['W'] and pk['box'][3] <= pk['H'], pk)
                chk(f'{tag}: the picker says the games are best with the camera (touch is the input)', pk['cam'] and (('מצלמה' in pk['camText']) if he else ('camera' in pk['camText'])), pk)
                if mobile: await page.screenshot(path=OUT + f"cam_picker_{'he' if he else 'en'}.png")
                await page.keyboard.press('Escape'); await page.wait_for_function("$('cgPick').hidden", timeout=3000)
                chk(f'{tag}: Escape closes the picker', True)
                chk(f'{tag}: no page errors', not errs, errs); await ctx.close()

        # ---- each game from the picker (touch: the camera prompt; 'Play with touch' once a session) and its direct link; the pause menu; Home ----
        ctx, page, errs = await fresh(b, True)
        for i, m in enumerate(['drums', 'bubbles', 'paint', 'stars']):
            await start_game(page, m, True, touch_ok=False)
            st = await page.evaluate(f"({{ gm: gameMode, mode, path: location.pathname, min: document.body.classList.contains('minChrome'), ask: {CG}.asking, route: __grasp.route.now }})")
            if i == 0:
                chk(f'{m}: started from the picker by touch: its path, the corner menu; the camera prompt shows', st['gm'] == m and st['mode'] == 'mouse' and st['path'] == '/' + m and st['min'] and st['ask'] and st['route'] == m, st)
                await page.screenshot(path=OUT + 'cam_ask_en.png')
                await page.tap('#cgCamTouch'); await page.wait_for_function(f"!{CG}.asking", timeout=3000)
            else: chk(f'{m}: started from the picker; after "Play with touch" no prompt again this session', st['gm'] == m and st['path'] == '/' + m and st['min'] and not st['ask'], st)
            await page.tap('#pauseBtn'); await page.wait_for_function("menu.open && pause.on", timeout=4000)
            chk(f'{m}: the corner pause menu opens (paused)', True)
            await page.tap('#resumeBtn'); await page.wait_for_function("!menu.open && !pause.on", timeout=4000)
            await home(page); await page.wait_for_function("location.pathname === '/' || location.pathname === '/index.html'", timeout=4000)
            chk(f'{m}: Home: the start screen, the address back (Back from the game)', await page.evaluate("__grasp.route.now") is None)
        chk('picker starts: no page errors', not errs, errs); await ctx.close()
        for m in ['drums', 'bubbles', 'paint', 'stars']:
            for path in ('/' + m, '/' + m + '/'):
                ctx = await b.new_context(viewport={'width': 360, 'height': 740}, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs = []
                page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + HAND_JS)
                await page.goto('http://localhost:8765' + path); await page.wait_for_function(f"typeof __grasp !== 'undefined' && !!__grasp.cg && mode === 'mouse' && gameMode === '{m}'", timeout=10000)
                st = await page.evaluate(f"({{ path: location.pathname, start: $('start').hidden, route: __grasp.route.now, ask: {CG}.asking }})")
                chk(f'direct link {path}: opens {m} at once (touch, the camera prompt)', st['path'] == '/' + m and st['start'] and st['route'] == m and st['ask'], st)
                chk(f'direct link {path}: no page errors', not errs, errs); await ctx.close()

        # ---- Air Drums by mouse / touch: each pad plays its own sound; several fingers at once; the beat; Follow the light ----
        ctx, page, errs = await fresh(b)
        await start_game(page, 'drums')
        pads = await page.evaluate(f"{CG}.pads()")
        chk('drums: six pads (hi-hat, cymbal, snare, tom, cowbell, kick), on screen, apart', [q['k'] for q in pads] == ['hihat', 'crash', 'snare', 'tom', 'cowbell', 'kick'] and all(q['r'] >= 60 and q['x'] - q['r'] >= 0 and q['x'] + q['r'] <= 1280 and q['y'] + q['r'] <= 800 for q in pads)
              and all(((a['x'] - c['x']) ** 2 + (a['y'] - c['y']) ** 2) ** 0.5 > a['r'] + c['r'] for i, a in enumerate(pads) for c in pads[i + 1:]), pads)
        ok = []
        for i, q in enumerate(pads):
            n0 = await page.evaluate(f"{CG}.drums.log.length")
            await page.mouse.click(q['x'] + q['r'] * 0.5, q['y'] - q['r'] * 0.3)
            await page.wait_for_function(f"{CG}.drums.log.length > {n0}", timeout=3000)
            r = await page.evaluate(f"(() => {{ const L = {CG}.drums.log, S = {CG}.drums.snd; return {{ pad: L[L.length - 1].pad, src: L[L.length - 1].src, snd: S[S.length - 1].k, beat: S[S.length - 1].beat }}; }})()")
            ok.append(r['pad'] == q['k'] and r['snd'] == q['k'] and r['src'] == 'tap' and not r['beat'])
        chk('drums: a click on each pad hits that pad and plays its own drum sound', all(ok), ok)
        n0 = await page.evaluate(f"{CG}.drums.log.length"); await page.mouse.click(640, 30); await page.wait_for_timeout(150)
        chk('drums: a click beside the pads hits nothing', await page.evaluate(f"{CG}.drums.log.length") == n0)
        played = await page.evaluate("""(() => { if (!audio || audio.state !== 'running') return 'no audio'; return __grasp.cg.sound('kick', 0.9) && __grasp.cg.sound('crash', 0.9) && __grasp.cg.sound('hihat', 0.5); })()""")
        chk('drums: the synthesized drums build and play on a running AudioContext', played is True, played)
        await page.evaluate(FRAMES); await page.screenshot(path=OUT + 'cam_drums_play.png')
        # the backing beat
        await click_btn(page, 'beat'); await page.wait_for_function(f"{CG}.drums.beat.on", timeout=3000)
        await page.wait_for_function(f"{CG}.drums.beat.n >= 8", timeout=6000)
        bt = await page.evaluate(f"(() => {{ const S = {CG}.drums.snd.filter(s => s.beat); return {{ kinds: [...new Set(S.map(s => s.k))].sort(), glow: {CG}.drums.pads.filter(p => performance.now() - p.beatAt < 2000).map(p => p.k).sort() }}; }})()")
        chk('drums: Beat on: a groove of kick, snare and hi-hat plays; those pads glow on its notes', bt['kinds'] == ['hihat', 'kick', 'snare'] and set(bt['glow']) >= {'kick', 'hihat'}, bt)
        await click_btn(page, 'beat'); await page.wait_for_function(f"!{CG}.drums.beat.on", timeout=3000)
        n1 = await page.evaluate(f"{CG}.drums.beat.n"); await page.wait_for_timeout(700)
        chk('drums: Beat off: it stops', await page.evaluate(f"{CG}.drums.beat.n") == n1)
        # Follow the light: watch, copy, one longer; a wrong pad ends it (the card, the best, a snack)
        await page.evaluate("__grasp.pet.set({ pantry: 0 })")
        await click_btn(page, 'simon'); await page.wait_for_function(f"{CG}.simon.on && {CG}.simon.phase === 'show'", timeout=3000)
        chk('drums: Follow the light starts with a sequence of one, shown first', len(await page.evaluate(f"{CG}.simon.seq")) == 1)
        await page.evaluate(FRAMES); await page.screenshot(path=OUT + 'cam_drums_simon.png')
        for rnd in (1, 2, 3):
            await page.wait_for_function(f"{CG}.simon.phase === 'play' && {CG}.simon.seq.length === {rnd}", timeout=9000)
            seq = await page.evaluate(f"{CG}.simon.seq")
            for k in seq: q = pads[k]; await page.mouse.click(q['x'], q['y']); await page.wait_for_timeout(90)
            await page.wait_for_function(f"{CG}.simon.level === {rnd}", timeout=3000)
        sm = await page.evaluate(f"{CG}.simon")
        chk('drums: copying the lights: each round one longer (3 rounds copied)', sm['level'] == 3 and sm['ok'] == 6, sm)
        await page.wait_for_function(f"{CG}.simon.phase === 'play' && {CG}.simon.seq.length === 4", timeout=9000)
        seq = await page.evaluate(f"{CG}.simon.seq"); wrong = (seq[0] + 1) % 6
        await page.mouse.click(pads[wrong]['x'], pads[wrong]['y'])
        await page.wait_for_function(f"{CG}.drums.over && {CG}.drums.ui.buttons", timeout=4000); await page.wait_for_timeout(1300)
        card = await page.evaluate(f"(() => {{ const D = {CG}.drums; return {{ over: D.over, best: D.best, keys: Object.keys(D.ui.buttons), tag: D.ui.petTag && D.ui.petTag.n, stored: localStorage.getItem('drumsBest'), pantry: __grasp.pet.p.pantry }}; }})()")
        chk('drums: a wrong pad ends it: the card (Play again / Home), the best (3), a snack for the pet', card['over'] and card['best'] == 3 and card['stored'] == '3' and 'again' in card['keys'] and 'home' in card['keys'] and card['tag'] and card['pantry'] >= 1, card)
        await page.screenshot(path=OUT + 'cam_drums_card.png')
        a = await page.evaluate(f"{CG}.drums.ui.buttons.again"); await page.mouse.click(a['x'] + a['w'] / 2, a['y'] + a['h'] / 2)
        await page.wait_for_function(f"!{CG}.drums.over && {CG}.simon.on && {CG}.simon.seq.length === 1", timeout=3000)
        chk('drums: Play again: a new Follow the light run', True)
        await click_btn(page, 'stop'); await page.wait_for_function(f"!{CG}.simon.on", timeout=3000)
        chk('drums: Stop: back to free play', True)
        # touch: two fingers at once hit two pads
        await page.evaluate(f"""(() => {{ const P = {CG}.pads(), c = canvas, ev = (id, p) => c.dispatchEvent(new PointerEvent('pointerdown', {{ pointerId: id, pointerType: 'touch', isPrimary: id === 21, clientX: p.x, clientY: p.y, bubbles: true, cancelable: true, button: 0, buttons: 1 }}));
          window.__n0 = {CG}.drums.log.length; ev(21, P[2]); ev(22, P[5]); }})()""")
        await page.wait_for_function(f"{CG}.drums.log.length >= window.__n0 + 2", timeout=3000)
        two = await page.evaluate(f"{CG}.drums.log.slice(-2).map(l => l.pad).sort()")
        chk('drums: two fingers at once: both pads (snare + kick)', two == ['kick', 'snare'], two)
        await page.evaluate("window.dispatchEvent(new PointerEvent('pointerup', { pointerId: 21, pointerType: 'touch', bubbles: true })); window.dispatchEvent(new PointerEvent('pointerup', { pointerId: 22, pointerType: 'touch', bubbles: true }))")
        chk('drums (mouse): no page errors', not errs, errs); await ctx.close()

        # ---- Air Drums with the camera: a downward strike hits the pad under the hand; two hands (numHands 2); a slow tracker falls back to one ----
        ctx, page, errs = await fresh(b, cam=True)
        await page.evaluate("window.__handFor = () => handAt(640, 300, 0.8)")
        await start_game(page, 'drums', cam=True)
        cr = await page.evaluate("window.__created.map(c => c.nh)")
        chk('drums camera: the tracker is made for two hands (numHands 2)', cr and cr[-1] == 2 and await page.evaluate(f"{CG}.numHands") == 2, cr)
        pads = await page.evaluate(f"{CG}.pads()")
        sn, kk = pads[2], pads[5]
        await page.evaluate(f"window.__handFor = () => handAt({sn['x']}, {sn['y'] - 260}, 0.8)"); await page.wait_for_timeout(500)
        n0 = await page.evaluate(f"{CG}.drums.log.length")
        await page.evaluate(f"strike1({sn['x']}, {sn['y'] - 260}, {sn['y'] + 10}, 160, 0)")
        await page.wait_for_function(f"{CG}.drums.log.length > {n0}", timeout=4000); await page.wait_for_timeout(300)
        L = await page.evaluate(f"{CG}.drums.log.slice({n0})")
        chk('drums camera: a fast downward strike hits the snare (the pad under the hand), once, with its sound', [l['pad'] for l in L] == ['snare'] and L[0]['src'] == 'h0' and await page.evaluate(f"{CG}.drums.snd.filter(s => !s.beat).slice(-1)[0].k") == 'snare', L)
        await page.evaluate(f"window.__handFor = () => handAt({kk['x']}, {kk['y'] - 120}, 0.8)"); await page.wait_for_timeout(500)
        n0 = await page.evaluate(f"{CG}.drums.log.length")
        await page.evaluate(f"lineFn((x, y) => handAt(x, y, 0.8), {kk['x']}, {kk['y'] - 120}, {kk['x']}, {kk['y'] + 10}, 2500)"); await page.wait_for_timeout(2800)
        chk('drums camera: a slow hand moving onto a pad does not hit it', await page.evaluate(f"{CG}.drums.log.length") == n0)
        # two hands strike two pads
        hh, cy = pads[0], pads[1]
        await page.evaluate(f"window.__handFor = () => [handAt({hh['x']}, {hh['y'] - 250}, 0.8), handAt({cy['x']}, {cy['y'] - 250}, 0.8)]")
        await page.wait_for_function(f"{CG}.ptrs.filter(p => p.hand).length === 2", timeout=4000); await page.wait_for_timeout(300)
        two = await page.evaluate(f"{CG}.ptrs.filter(p => p.hand).map(p => [p.id, p.tips])")
        chk('drums camera: both hands are tracked (two hand pointers with their fingertips)', [t[0] for t in two] == ['h0', 'h1'] and all(t[1] == 6 for t in two), two)
        n0 = await page.evaluate(f"{CG}.drums.log.length")
        await page.evaluate(f"strike2([{hh['x']}, {hh['y'] - 250}, {hh['y'] + 10}], [{cy['x']}, {cy['y'] - 250}, {cy['y'] + 10}], 170, 0)")
        await page.wait_for_function(f"{CG}.drums.log.length >= {n0} + 2", timeout=4000); await page.wait_for_timeout(300)
        L = await page.evaluate(f"{CG}.drums.log.slice({n0})")
        chk('drums camera: two hands strike the hi-hat and the cymbal together (one hit each)', sorted((l['pad'], l['src']) for l in L) == sorted([('hihat', 'h0'), ('crash', 'h1')]) or sorted(l['pad'] for l in L) == ['crash', 'hihat'] and len({l['src'] for l in L}) == 2, L)
        await page.evaluate(FRAMES); await page.screenshot(path=OUT + 'cam_drums_camera.png')
        # a slow tracker: back to one hand for the session
        await page.evaluate(f"{CG}.CG.twoMinFps = 1e6; {CG}.CG.twoSlowMs = 300")
        await page.wait_for_function(f"{CG}.numHands === 1 && {CG}.camg.twoOff", timeout=5000)
        so = await page.evaluate("(window.__setOpts || []).map(o => o.numHands)")
        chk('drums camera: a tracker slower than the floor goes back to one hand (setOptions numHands 1)', so and so[-1] == 1, so)
        await page.evaluate(f"{CG}.CG.twoMinFps = 5; {CG}.camg.twoOff = false; {CG}.CG.twoSlowMs = 3000; cgSyncHands()")
        await page.evaluate("__grasp.setGameMode('paint')"); await page.wait_for_timeout(200)
        chk('drums camera: leaving for Air Painting: one hand again', await page.evaluate(f"{CG}.numHands") == 1 and (await page.evaluate("window.__setOpts.map(o => o.numHands)"))[-1] == 1)
        chk('drums (camera): no page errors', not errs, errs); await ctx.close()

        # ---- Bubble Pop: taps, combos, golden, the round's card, Calm ----
        ctx, page, errs = await fresh(b, True)
        await start_game(page, 'bubbles', True)
        await page.evaluate(f"{CG}.bubbles.list.length = 0; {CG}.BUB.max = 0")  # (only the test's bubbles from here)
        bb = await page.evaluate(f"{CG}.spawnBubble({{ x: 180, y: 400, r: 40, vy: 0, amp: 0, gold: false }})")
        await page.touchscreen.tap(190, 410)
        await page.wait_for_function(f"{CG}.bubbles.popped === 1", timeout=3000)
        r = await page.evaluate(f"({{ score: {CG}.bubbles.score, log: {CG}.bubbles.log.slice(-1)[0], left: {CG}.bubbles.list.length }})")
        chk('bubbles: a tap on a bubble pops it (+1)', r['score'] == 1 and r['log']['id'] == bb['id'] and r['left'] == 0, r)
        await page.wait_for_timeout(800)  # (past the combo window)
        ids = [await page.evaluate(f"{CG}.spawnBubble({{ x: {x}, y: 300, r: 32, vy: 0, amp: 0, gold: false }}).id") for x in (70, 180, 290)]
        for x in (70, 180, 290): await page.touchscreen.tap(x, 300); await page.wait_for_timeout(60)
        await page.wait_for_function(f"{CG}.bubbles.popped === 4", timeout=3000)
        r = await page.evaluate(f"({{ score: {CG}.bubbles.score, combo: {CG}.bubbles.bestCombo, last: {CG}.bubbles.log.slice(-1)[0] }})")
        chk('bubbles: three quick pops chain a combo (x3: +1 extra)', r['combo'] == 3 and r['last']['combo'] == 3 and r['score'] == 1 + 1 + 1 + 2, r)
        await page.evaluate(f"{CG}.spawnBubble({{ x: 180, y: 520, r: 44, vy: 0, amp: 0, gold: true }})")
        await page.wait_for_timeout(800); await page.evaluate(FRAMES); await page.screenshot(path=OUT + 'cam_bubbles_play.png')
        s0 = await page.evaluate(f"{CG}.bubbles.score"); await page.touchscreen.tap(180, 520)
        await page.wait_for_function(f"{CG}.bubbles.golden === 1", timeout=3000)
        chk('bubbles: a golden bubble is +5', await page.evaluate(f"{CG}.bubbles.score") == s0 + 5)
        # pause freezes the clock and the bubbles
        await page.evaluate(f"{CG}.spawnBubble({{ x: 100, y: 600, r: 30, vy: -0.05, amp: 0, gold: false }})")
        await page.tap('#pauseBtn'); await page.wait_for_function("menu.open", timeout=3000)
        f0 = await page.evaluate(f"JSON.stringify([Math.round({CG}.bubbles.left / 100), {CG}.bubbles.list.map(b => Math.round(b.y))])"); await page.wait_for_timeout(600)
        f1 = await page.evaluate(f"JSON.stringify([Math.round({CG}.bubbles.left / 100), {CG}.bubbles.list.map(b => Math.round(b.y))])")
        chk('bubbles: the pause sheet freezes the clock and the bubbles', f0 == f1, [f0, f1])
        await page.tap('#resumeBtn'); await page.wait_for_function("!menu.open && !pause.on", timeout=3000)
        # the round's end: stars, the best, the card, a snack
        await page.evaluate("__grasp.pet.set({ pantry: 0 })"); await page.evaluate(f"{CG}.bubbles.score = 44; {CG}.end()")
        await page.wait_for_function(f"{CG}.bubbles.over && {CG}.bubbles.ui.buttons", timeout=4000); await page.wait_for_timeout(1400)
        c = await page.evaluate(f"(() => {{ const B = {CG}.bubbles; return {{ stars: B.starsN, row: B.ui.starsRow, best: B.best, stored: localStorage.getItem('bubblesBest'), keys: Object.keys(B.ui.buttons), tag: B.ui.petTag && B.ui.petTag.n, pantry: __grasp.pet.p.pantry }}; }})()")
        chk('bubbles: time up: 2 stars for 44, the best kept, the card (Play again / Home) with the pet snack', c['stars'] == 2 and c['row'] == 2 and c['best'] == 44 and c['stored'] == '44' and 'again' in c['keys'] and 'home' in c['keys'] and c['tag'] and c['pantry'] >= 1, c)
        await page.screenshot(path=OUT + 'cam_bubbles_card.png')
        a = await page.evaluate(f"{CG}.bubbles.ui.buttons.again"); await page.touchscreen.tap(a['x'] + a['w'] / 2, a['y'] + a['h'] / 2)
        await page.wait_for_function(f"!{CG}.bubbles.over && {CG}.bubbles.score === 0 && {CG}.bubbles.left > 59000", timeout=3000)
        chk('bubbles: Play again: a fresh 60 s round', True)
        # Calm: no timer, nothing ends; every 30 pops a treat (a snack)
        await click_btn(page, 'calm', True); await page.wait_for_function(f"{CG}.bubbles.calm", timeout=3000)
        l0 = await page.evaluate(f"{CG}.bubbles.left"); await page.wait_for_timeout(700)
        chk('bubbles: Calm on: the clock does not run (and it is remembered)', await page.evaluate(f"{CG}.bubbles.left") == l0 and await page.evaluate("localStorage.getItem('bubblesCalm')") == '1')
        await page.evaluate(f"{CG}.bubbles.list.length = 0; {CG}.BUB.maxCalm = 0; {CG}.bubbles.calmPops = 29; __grasp.pet.set({{ pantry: 0 }})")
        await page.evaluate(f"{CG}.spawnBubble({{ x: 180, y: 400, r: 40, vy: 0, amp: 0, gold: false }})"); await page.touchscreen.tap(180, 400)
        await page.wait_for_function(f"{CG}.bubbles.treats === 1", timeout=3000)
        tr = await page.evaluate("({ pantry: __grasp.pet.p.pantry, toast: __grasp.toasts.slice(-1)[0].key })")
        chk('bubbles: Calm: the 30th pop is a party and a snack for the pet', tr['pantry'] >= 1 and tr['toast'] == 'cgSnack', tr)
        await page.evaluate(FRAMES); await page.screenshot(path=OUT + 'cam_bubbles_calm.png')
        await click_btn(page, 'calm', True); await page.wait_for_function(f"!{CG}.bubbles.calm", timeout=3000)
        chk('bubbles (touch): no page errors', not errs, errs); await ctx.close()
        # camera: fingertips pop, both hands
        ctx, page, errs = await fresh(b, cam=True)
        await page.evaluate("window.__handFor = () => handAt(200, 600, 0.8)")
        await start_game(page, 'bubbles', cam=True)
        await page.evaluate(f"{CG}.bubbles.list.length = 0; {CG}.BUB.max = 0")
        await page.wait_for_timeout(300)
        a1 = await page.evaluate(f"{CG}.spawnBubble({{ x: 400, y: 300, r: 40, vy: 0, amp: 0, gold: false }}).id"); a2 = await page.evaluate(f"{CG}.spawnBubble({{ x: 900, y: 300, r: 40, vy: 0, amp: 0, gold: false }}).id")
        p0 = await page.evaluate(f"{CG}.bubbles.popped"); await page.wait_for_timeout(400)
        chk('bubbles camera: bubbles away from the hands stay', await page.evaluate(f"{CG}.bubbles.popped") == p0)
        await page.evaluate("window.__handFor = () => [handAt(400, 380, 0.8), handAt(900, 380, 0.8)]")  # (the hands' fingertips reach up into the bubbles)
        await page.wait_for_function(f"{CG}.bubbles.popped === {p0} + 2", timeout=4000)
        chk('bubbles camera: two hands\' fingers pop a bubble each', sorted(l['id'] for l in (await page.evaluate(f"{CG}.bubbles.log"))[-2:]) == sorted([a1, a2]))
        await page.evaluate(f"{CG}.spawnBubble({{ x: 640, y: 250, r: 50, vy: 0, amp: 0, gold: true }})"); await page.evaluate(f"{CG}.spawnBubble({{ x: 300, y: 200, r: 36, vy: 0, amp: 0, gold: false }})")
        await page.wait_for_timeout(300); await page.evaluate(FRAMES); await page.screenshot(path=OUT + 'cam_bubbles_camera.png')
        chk('bubbles (camera): no page errors', not errs, errs); await ctx.close()

        # ---- Air Painting: mouse drawing, the palette, magic brushes, erase, the PNG save ----
        ctx, page, errs = await fresh(b)
        await start_game(page, 'paint')
        await page.mouse.move(300, 300); await page.mouse.down()
        for i in range(1, 21): await page.mouse.move(300 + i * 20, 300 + (i % 5) * 6); await page.wait_for_timeout(16)
        await page.mouse.up(); await page.wait_for_function(f"!{CG}.paint.drawing", timeout=3000)
        P = await page.evaluate(f"({{ strokes: {CG}.paint.strokes, ink: {CG}.paint.ink, px: {CG}.paintInk(480, 290, 540, 330) }})")
        chk('paint: a mouse drag draws a glowing stroke (ink on the layer), the release ends it', P['strokes'] == 1 and P['ink'] > 300 and P['px'] > 200, P)
        await click_btn(page, 'c0'); await page.wait_for_function(f"{CG}.paint.color === 0", timeout=3000)
        await page.mouse.move(300, 450); await page.mouse.down()
        for i in range(1, 11): await page.mouse.move(300 + i * 20, 450); await page.wait_for_timeout(16)
        await page.mouse.up(); await page.wait_for_timeout(100)
        px = await page.evaluate(f"[{CG}.paintPixel(400, 450), {CG}.paintPixel(400, 454)]")  # (the white-hot core, then the red body beside it)
        chk('paint: a colour from the palette (red): the new stroke is red with a bright core', px[0][3] > 200 and px[0][0] > 200 and px[0][1] > 150 and px[1][3] > 200 and px[1][0] > 200 and px[1][1] < 140, px)
        await click_btn(page, 's2'); await click_btn(page, 'rainbow'); await click_btn(page, 'mirror')
        await page.wait_for_function(f"{CG}.paint.size === 2 && {CG}.paint.brush === 'rainbow' && {CG}.paint.mirror", timeout=3000)
        await page.mouse.move(200, 560); await page.mouse.down()
        for i in range(1, 16): await page.mouse.move(200 + i * 14, 560 - i * 8); await page.wait_for_timeout(16)
        await page.mouse.up(); await page.wait_for_timeout(100)
        mir = await page.evaluate(f"[{CG}.paintInk(250, 500, 330, 560), {CG}.paintInk(1280 - 330, 500, 1280 - 250, 560)]")
        chk('paint: a big rainbow stroke with Mirror: drawn on both sides', mir[0] > 200 and mir[1] > 200, mir)
        await click_btn(page, 'sparkle'); await page.wait_for_function(f"{CG}.paint.brush === 'sparkle'", timeout=3000)
        await page.mouse.move(700, 250); await page.mouse.down()
        for i in range(1, 16): await page.mouse.move(700 + i * 16, 250 + i * 6); await page.wait_for_timeout(16)
        await page.mouse.up(); await page.wait_for_timeout(100)
        chk('paint: Sparkles: little stars twinkle along the stroke', await page.evaluate(f"{CG}.paint.twinkles.length") > 3)
        await page.evaluate(FRAMES); await page.screenshot(path=OUT + 'cam_paint_magic.png')
        await click_btn(page, 'mirror'); await click_btn(page, 'c4')
        # the palette over the drawing area: a press on it never paints
        x, y = await btn(page, 'c2'); ink0 = await page.evaluate(f"{CG}.paint.ink")
        await page.mouse.move(x, y); await page.mouse.down(); await page.mouse.move(x + 30, y); await page.mouse.up(); await page.wait_for_timeout(100)
        chk('paint: pressing on the palette picks (yellow), it does not paint', await page.evaluate(f"{CG}.paint.color") == 2 and await page.evaluate(f"{CG}.paint.ink") == ink0)
        # the save: no share sheet here -> a PNG download (+ a snack for a real drawing)
        await page.evaluate("__grasp.pet.set({ pantry: 0 })")
        async with page.expect_download(timeout=8000) as dl:
            await click_btn(page, 'save')
        d = await dl.value
        await page.wait_for_function(f"{CG}.paint.saved && {CG}.paint.saved.how", timeout=5000)
        sv = await page.evaluate(f"({{ s: {CG}.paint.saved, pantry: __grasp.pet.p.pantry, toast: __grasp.toasts.slice(-1)[0].key }})")
        chk('paint: Save: a PNG download (grasp-drawing.png), a snack for the pet the first time', d.suggested_filename == 'grasp-drawing.png' and sv['s']['how'] == 'download' and sv['s']['type'] == 'image/png' and sv['s']['size'] > 2000 and sv['pantry'] >= 1 and sv['toast'] == 'pnSavedSnack', sv)
        p0 = sv['pantry']
        async with page.expect_download(timeout=8000) as dl: await click_btn(page, 'save')
        await dl.value; await page.wait_for_timeout(300)
        chk('paint: saving the same drawing again: no second snack', await page.evaluate("__grasp.pet.p.pantry") == p0 and await page.evaluate("__grasp.toasts.slice(-1)[0].key") == 'pnSaved')
        await page.evaluate("(() => { navigator.canShare = () => true; navigator.share = (o) => { window.__shared = { n: o.files.length, name: o.files[0].name, type: o.files[0].type }; return Promise.resolve(); }; return 1; })()")
        await click_btn(page, 'save'); await page.wait_for_function(f"window.__shared && {CG}.paint.saved.how === 'share'", timeout=5000)
        chk('paint: Save with a share sheet: the PNG goes to navigator.share', await page.evaluate("window.__shared") == {'n': 1, 'name': 'grasp-drawing.png', 'type': 'image/png'})
        # erase: tap the bin twice
        await click_btn(page, 'trash'); await page.wait_for_timeout(150)
        chk('paint: Erase once: it asks again (the drawing stays)', await page.evaluate(f"{CG}.paint.ink") > 0 and await page.evaluate(f"{CG}.paint.cleared") == 0)
        await click_btn(page, 'trash'); await page.wait_for_function(f"{CG}.paint.cleared === 1", timeout=3000)
        chk('paint: Erase twice: the drawing is gone', await page.evaluate(f"{CG}.paint.ink") == 0 and await page.evaluate(f"{CG}.paintInk(250, 280, 700, 600)") == 0)
        chk('paint (mouse): no page errors', not errs, errs); await ctx.close()
        # touch: a finger draws; camera: pinch draws, an open hand stops, a hold on a swatch picks it, a fist shake erases
        ctx, page, errs = await fresh(b, True)
        await start_game(page, 'paint', True)
        await page.evaluate("touchDrag(80, 200, 280, 380, 12, 20)"); await page.wait_for_timeout(500)
        chk('paint touch: a finger draws', await page.evaluate(f"{CG}.paint.strokes") == 1 and await page.evaluate(f"{CG}.paint.ink") > 150 and not await page.evaluate(f"{CG}.paint.drawing"))
        chk('paint (touch): no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, cam=True)
        await page.evaluate("window.__handFor = () => handAt(400, 300, 0.8)")
        await start_game(page, 'paint', cam=True)
        await page.wait_for_timeout(400)
        chk('paint camera: an open hand does not paint', await page.evaluate(f"{CG}.paint.strokes") == 0 and await page.evaluate(f"{CG}.numHands") == 1)
        await page.evaluate("window.__handFor = () => handAt(400, 300, 0.1)"); await page.wait_for_function(f"{CG}.paint.drawing", timeout=4000)
        await page.evaluate("lineFn((x, y) => handAt(x, y, 0.1), 400, 300, 800, 380, 900)"); await page.wait_for_timeout(1100)
        i1 = await page.evaluate(f"{CG}.paint.ink")
        chk('paint camera: a pinch paints along the hand', await page.evaluate(f"{CG}.paint.strokes") == 1 and i1 > 250 and await page.evaluate(f"{CG}.paintInk(560, 300, 660, 380)") > 100, i1)
        await page.evaluate("window.__handFor = () => handAt(800, 380, 0.8)"); await page.wait_for_function(f"!{CG}.paint.drawing", timeout=4000)
        await page.evaluate("lineFn((x, y) => handAt(x, y, 0.8), 800, 380, 900, 200, 600)"); await page.wait_for_timeout(800)
        chk('paint camera: an open hand stops painting (moving it adds no ink)', abs(await page.evaluate(f"{CG}.paint.ink") - i1) < 40)
        x, y = await btn(page, 'c1')
        await page.evaluate(f"lineFn((x, y) => handAt(x, y, 0.8), 900, 200, {x}, {y}, 500)"); await page.wait_for_timeout(450)
        await page.wait_for_function(f"{CG}.paint.color === 1", timeout=4000)
        pr = await page.evaluate(f"{CG}.camg.lastPress")
        chk('paint camera: holding the hand over a swatch picks it (orange, by dwell)', pr['key'] == 'c1' and pr['how'] == 'dwell', pr)
        await page.evaluate(f"lineFn((x, y) => handAt(x, y, 0.8), {x}, {y}, 640, 300, 400)"); await page.wait_for_timeout(600)
        await page.evaluate(FRAMES); await page.screenshot(path=OUT + 'cam_paint_camera.png')
        await page.evaluate("window.__handFor = () => fistAt(640, 300)"); await page.wait_for_function("gesture === 'fist'", timeout=4000); await page.wait_for_timeout(200)
        chk('paint camera: a fist asks to shake (the drawing stays)', await page.evaluate(f"{CG}.paint.fist.on") and await page.evaluate(f"{CG}.paint.cleared") == 0)
        await page.evaluate(FRAMES); await page.screenshot(path=OUT + 'cam_paint_shake.png')
        await page.evaluate("shakeFist(640, 300, 160, 500)"); await page.wait_for_function(f"{CG}.paint.cleared === 1", timeout=6000)
        chk('paint camera: shaking the fist erases everything', await page.evaluate(f"{CG}.paint.ink") == 0 and await page.evaluate(f"{CG}.paint.log.filter(l => l.ev === 'clear').slice(-1)[0].how") == 'shake')
        chk('paint (camera): no page errors', not errs, errs); await ctx.close()

        # ---- Catch the Stars: the basket follows, catches, bombs, clouds, misses, the speed-up, the card ----
        ctx, page, errs = await fresh(b)
        await start_game(page, 'stars')
        await page.evaluate(f"{CG}.CATCH.spawn = [1e9, 1e9]; {CG}.catcher.nextAt = 1e15; {CG}.catcher.items.length = 0")
        await page.mouse.move(300, 400); await page.wait_for_function(f"Math.abs({CG}.basket.x - 300) < 4", timeout=3000)
        chk('stars: the basket follows the mouse', True)
        bk = await page.evaluate(f"{CG}.basket")
        await page.evaluate(f"{CG}.drop('star', {bk['x']}, {bk['y'] - 220}, 0.6)")
        await page.wait_for_function(f"{CG}.catcher.caught === 1", timeout=3000)
        chk('stars: a star falling into the basket is caught (+1)', await page.evaluate(f"{CG}.catcher.score") == 1 and await page.evaluate(f"{CG}.catcher.log.slice(-1)[0].kind") == 'star')
        for k in ('coin', 'cookie', 'gold'):
            await page.evaluate(f"{CG}.drop('{k}', {bk['x']}, {bk['y'] - 220}, 0.6)"); await page.wait_for_timeout(600)
        chk('stars: a coin (+2), a cookie (+3), a golden star (+5)', await page.evaluate(f"{CG}.catcher.score") == 11 and await page.evaluate(f"{CG}.catcher.caught") == 4)
        await page.evaluate(f"{CG}.drop('bomb', {bk['x']}, {bk['y'] - 220}, 0.6)"); await page.wait_for_function(f"{CG}.catcher.bad === 1", timeout=3000)
        st = await page.evaluate(f"({{ s: {CG}.catcher.score, stun: {CG}.basket.stun, streak: {CG}.catcher.streak }})")
        chk('stars: a bomb in the basket: -3, the basket reels, the streak resets', st['s'] == 8 and st['stun'] and st['streak'] == 0, st)
        await page.evaluate(FRAMES); await page.screenshot(path=OUT + 'cam_stars_bomb.png')
        await page.evaluate(f"{CG}.drop('star', {bk['x']}, {bk['y'] - 60}, 0.6)"); await page.wait_for_timeout(500)
        chk('stars: while it reels nothing is caught', await page.evaluate(f"{CG}.catcher.caught") == 4)
        await page.wait_for_timeout(500)
        await page.evaluate(f"{CG}.drop('cloud', {bk['x']}, {bk['y'] - 220}, 0.6)"); await page.wait_for_function(f"{CG}.catcher.bad === 2", timeout=3000)
        chk('stars: a rain cloud: -1, a soggy basket', await page.evaluate(f"{CG}.catcher.score") == 7 and await page.evaluate(f"{CG}.basket.wet"))
        d0 = await page.evaluate(f"[{CG}.catcher.dodged, {CG}.catcher.missed]")
        await page.evaluate(f"{CG}.drop('bomb', 1100, -30, 0.9)"); await page.evaluate(f"{CG}.drop('star', 1150, -30, 0.9)")
        await page.wait_for_function(f"{CG}.catcher.dodged === {d0[0] + 1} && {CG}.catcher.missed === {d0[1] + 1}", timeout=4000)
        chk('stars: a bomb that falls past is dodged; a missed star is just gone', await page.evaluate(f"{CG}.catcher.score") == 7)
        v0 = await page.evaluate(f"(() => {{ {CG}.catcher.el = 0; let s = 0; for (let i = 0; i < 40; i++) s += {CG}.drop('star').id && {CG}.catcher.items.slice(-1)[0].vy; return s / 40; }})()")
        v1 = await page.evaluate(f"(() => {{ {CG}.catcher.el = 58000; let s = 0; for (let i = 0; i < 40; i++) s += {CG}.drop('star').id && {CG}.catcher.items.slice(-1)[0].vy; return s / 40; }})()")
        chk('stars: it speeds up over the round (falls ~1.8x faster at the end)', v1 > v0 * 1.5, [v0, v1])
        await page.evaluate(f"{CG}.catcher.items.length = 0; {CG}.CATCH.spawn = [950, 430]; {CG}.catcher.nextAt = 0; {CG}.catcher.el = 20000")
        await page.wait_for_timeout(2500); await page.evaluate(FRAMES); await page.screenshot(path=OUT + 'cam_stars_play.png')
        await page.evaluate("__grasp.pet.set({ pantry: 0 })"); await page.evaluate(f"{CG}.catcher.score = 85; {CG}.end()")
        await page.wait_for_function(f"{CG}.catcher.over && {CG}.catcher.ui.buttons", timeout=4000); await page.wait_for_timeout(1400)
        c = await page.evaluate(f"(() => {{ const C = {CG}.catcher; return {{ stars: C.starsN, best: C.best, stored: localStorage.getItem('starsBest'), keys: Object.keys(C.ui.buttons), tag: C.ui.petTag && C.ui.petTag.n, pantry: __grasp.pet.p.pantry, nb: C.ui.newBest }}; }})()")
        chk('stars: time up: 3 stars for 85, a new best, the card with the pet snack', c['stars'] == 3 and c['best'] == 85 and c['stored'] == '85' and c['nb'] and 'again' in c['keys'] and c['tag'] and c['pantry'] >= 1, c)
        await page.screenshot(path=OUT + 'cam_stars_card.png')
        h = await page.evaluate(f"{CG}.catcher.ui.buttons.home"); await page.mouse.click(h['x'] + h['w'] / 2, h['y'] + h['h'] / 2)
        await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=4000)
        chk('stars: Home from the card: the start screen', True)
        chk('stars (mouse): no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, cam=True)
        await page.evaluate("window.__handFor = () => handAt(640, 500, 0.8)")
        await start_game(page, 'stars', cam=True)
        await page.evaluate("lineFn((x, y) => handAt(x, y, 0.8), 640, 500, 300, 520, 600)")
        await page.wait_for_function(f"Math.abs({CG}.basket.x - 300) < 25", timeout=4000)
        chk('stars camera: the basket follows the hand', True)
        await page.evaluate("lineFn((x, y) => handAt(x, y, 0.8), 300, 520, 1000, 520, 600)")
        await page.wait_for_function(f"Math.abs({CG}.basket.x - 1000) < 25", timeout=4000)
        chk('stars camera: and back across', True)
        chk('stars (camera): no page errors', not errs, errs); await ctx.close()

        # ---- the camera prompt: Turn on camera switches the game to the camera ----
        ctx, page, errs = await fresh(b)
        await page.evaluate("window.__handFor = () => handAt(640, 400, 0.8)")
        await start_game(page, 'bubbles', touch_ok=False)
        chk('prompt: started by touch, the prompt asks', await page.evaluate(f"{CG}.asking"))
        b0 = await page.evaluate(f"JSON.stringify({CG}.bubbles.list.map(q => Math.round(q.y)))"); await page.wait_for_timeout(400)
        chk('prompt: the game waits under it', await page.evaluate(f"JSON.stringify({CG}.bubbles.list.map(q => Math.round(q.y)))") == b0)
        await page.click('#cgCamOn'); await page.wait_for_function("mode === 'camera' && gameMode === 'bubbles'", timeout=15000)
        chk('prompt: Turn on camera: the same game with the camera (remembered), two hands', await page.evaluate("localStorage.getItem('inputPref')") == 'camera' and not await page.evaluate(f"{CG}.asking") and await page.evaluate(f"{CG}.numHands") == 2)
        chk('prompt: no page errors', not errs, errs); await ctx.close()

        # ---- phone screenshots EN / HE of each game; the top row clear of the pause button ----
        for he in (False, True):
            ctx, page, errs = await fresh(b, True, he)
            for m in ['drums', 'bubbles', 'paint', 'stars']:
                await start_game(page, m, True)
                await page.wait_for_timeout(900 if m != 'stars' else 2600)
                if m == 'paint':
                    await page.evaluate("touchDrag(60, 220, 300, 330, 14, 16)"); await page.wait_for_timeout(400)
                    await click_btn(page, 'rainbow', True); await page.evaluate("touchDrag(70, 420, 290, 520, 14, 16)"); await page.wait_for_timeout(400)
                pb = await page.evaluate("(() => { const r = $('pauseBtn').getBoundingClientRect(); return { l: r.left, r: r.right, t: r.top, b: r.bottom }; })()")
                bs = await page.evaluate(f"{CG}.btns()")
                clash = [q['key'] for q in bs if q['x'] < pb['r'] and q['x'] + q['w'] > pb['l'] and q['y'] < pb['b'] and q['y'] + q['h'] > pb['t']]
                inside = all(q['x'] >= 0 and q['x'] + q['w'] <= 360 and q['y'] + q['h'] <= 740 for q in bs)
                chk(f"phone {'HE' if he else 'EN'} {m}: the game's buttons are on screen and clear of the pause button", not clash and inside, [clash, bs, pb])
                await page.evaluate(FRAMES); await page.screenshot(path=OUT + f"cam_{m}_{'he' if he else 'en'}.png")
                await home(page)
            chk(f"phone {'HE' if he else 'EN'} screenshots: no page errors", not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
