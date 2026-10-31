exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
import os, json
# Pop It (/popit): the silicone fidget toy. It loads by its link with no page errors in EN and HE (390 x 844, a phone); a tap pops a bubble (its state,
# the pop sound in the hooks, a 10 ms vibration, the deep dimple, the feel lab's burst + ring, the board's flex; the iPhone's switch haptic); a finger sliding over a row pops each bubble it passes; two fingers pop at once; all popped = "FLIP!" and
# the board is full again; Race records a best and 1-3 stars (and "New record!"); Colours ignore a wrong colour without failing (it springs back);
# Remember (Simon) grows the sequence and replays it after a mistake (the kid flow: a gentle end card after two); a new board unlocks every 3 flips
# into the profile and the shelf. The Little ones tile opens Free mode, the Arcade row the mode picker.
# Screenshots: tests/out/popit_{free,race,pattern,simon,shelf}_{en,he}.png at 390 x 844 (+ popit_picker_*, popit_reveal_en, popit_boards_en).
PORT = int(os.environ.get('GRASP_PORT', '8765')); BASE = 'http://localhost:%d' % PORT
if PORT != 8765: srv.terminate()
OUT = 'tests/out/'
P = '__grasp.popit'
SPEECH = """window.__spoken = []; (() => { const ss = { speak: (u) => __spoken.push({ text: u.text, lang: u.lang }), cancel() {}, getVoices: () => [{ lang: 'en-US', name: 'E' }, { lang: 'he-IL', name: 'H' }], speaking: false };
  try { Object.defineProperty(window, 'speechSynthesis', { value: ss, configurable: true }); } catch (e) {} window.SpeechSynthesisUtterance = function (t) { this.text = t; }; })();"""
FINGERS = """window.fing = (type, id, x, y) => { const c = document.getElementById('stage'), e = new PointerEvent(type, { pointerId: id, pointerType: 'touch', clientX: x, clientY: y, isPrimary: id === 1, bubbles: true, cancelable: true, button: 0, buttons: type === 'pointerup' ? 0 : 1, width: 20, height: 20 }); (type === 'pointerdown' ? c : window).dispatchEvent(e); };
window.__vib = 0; window.__vibMs = []; try { navigator.vibrate = (ms) => { __vib++; __vibMs.push(ms); return true; }; } catch (e) {}"""

async def page_for(b, path='/', he=False, init=''):
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + SPEECH + FINGERS + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');") + init)
    await page.goto(BASE + path); await page.wait_for_function("typeof engine !== 'undefined' && !!engine", timeout=15000)
    return ctx, page, errs

async def wait(page, cond, timeout=8000):
    try: await page.wait_for_function(cond, timeout=timeout); return True
    except Exception: return False

async def tap(page, x, y, hold=60, pid=1):
    await page.evaluate(f"fing('pointerdown', {pid}, {x}, {y})"); await page.wait_for_timeout(hold)
    await page.evaluate(f"fing('pointerup', {pid}, {x}, {y})"); await page.wait_for_timeout(90)

async def drag(page, x0, y0, x1, y1, steps=10, pid=1):
    await page.evaluate(f"fing('pointerdown', {pid}, {x0}, {y0})"); await page.wait_for_timeout(50)
    for k in range(1, steps + 1):
        await page.evaluate(f"fing('pointermove', {pid}, {x0 + (x1 - x0) * k / steps}, {y0 + (y1 - y0) * k / steps})"); await page.wait_for_timeout(20)
    await page.evaluate(f"fing('pointerup', {pid}, {x1}, {y1})"); await page.wait_for_timeout(80)

async def bubbles(page): return await page.evaluate(f"{P}.bubbles()")
async def said(page): return [s['text'] for s in await page.evaluate("__grasp.tg.said")]
async def ui(page, uid): return next((u for u in await page.evaluate(f"{P}.ui") if u['id'] == uid), None)
async def press(page, uid):  # a canvas button by its id (waits until the overlay takes taps)
    await page.wait_for_timeout(450); u = await ui(page, uid)
    if not u: return False
    x, y = (u['x'], u['y']) if 'r' in u else (u['x'] + u['w'] / 2, u['y'] + u['h'] / 2)
    await tap(page, x, y); return True

def rows_of(bs):
    rows = {}
    for q in bs: rows.setdefault(round(q['y']), []).append(q)
    return [sorted(r, key=lambda q: q['x']) for _, r in sorted(rows.items())]

async def pop_all(page, only_up=True):
    for r in rows_of(await bubbles(page)):
        r = [q for q in r if not (only_up and q['down'])]
        if not r: continue
        if len(r) == 1: await tap(page, r[0]['x'], r[0]['y'])
        else: await drag(page, r[0]['x'] - r[0]['r'] * 0.5, r[0]['y'], r[-1]['x'] + r[-1]['r'] * 0.5, r[-1]['y'], steps=max(6, len(r) * 2))
    for q in await bubbles(page):  # (a stray one a row's sweep missed: tap it)
        if not q['down']: await tap(page, q['x'], q['y'])

async def free_tests(b, he):
    tag = 'free ' + ('HE' if he else 'EN')
    ctx, page, errs = await page_for(b, '/popit', he)
    ok = await wait(page, "mode === 'mouse' && gameMode === 'popit' && $('start').hidden")
    check(tag + ': /popit opens Pop It at once (touch), Free mode, the little ones\' flow', ok and await page.evaluate("pi.mode === 'free' && pi.flow === 'little' && !pi.over"), await page.evaluate("[mode, gameMode, location.pathname]"))
    ok = await wait(page, "__grasp.tg.demoOn() && __grasp.tg.said.length > 0", 4000); w = await said(page)
    check(tag + ': first play: the demo finger + <= 3 words, voiced', ok and len(w[0].replace('!', '').split()) <= 3 and w[0] == ('מפוצצים בועות!' if he else 'Pop the bubbles!'), w)
    check(tag + ': the corner sticker is the way out (minChrome)', await page.evaluate("document.body.classList.contains('minChrome') && !$('pauseBtn').hidden"))
    bs = await bubbles(page)
    sq = await page.evaluate("({ bw: pi.L.bw, rows: pi.L.U.rows })"); pitch = sq["bw"] * 0.9 / 4; W0, H0 = await page.evaluate("[innerWidth, innerHeight]")
    check(tag + ': the square board: 4 columns of large bubbles (r = 0.45 x pitch, pitch = board width x 0.9 / 4: ~35 px at 390 px), as many rows as the height holds (the owner: more rows; 7 at 390 x 844), each >= 44 px across', len(bs) == 4 * sq['rows'] and 4 <= sq['rows'] <= 8 and (sq['rows'] >= 6 or W0 > H0) and all(abs(q['r'] - 0.45 * pitch) < 0.6 for q in bs) and 30 <= bs[0]['r'] <= 40 and min(q['r'] for q in bs) * 2 >= 44, (len(bs), sq, bs[0]['r']))
    # a tap pops one
    q = bs[0]; n0 = await page.evaluate("[__grasp.tg.snd.length, __vib]")
    await tap(page, q['x'], q['y'])
    st = await page.evaluate(f"({{ down: pi.st[0].down, snd: {P}.snd.slice(-3), tg: __grasp.tg.snd.slice(-3), vib: __vib, demo: __grasp.tg.demoOn(), pops: pi.pops }})")
    check(tag + ': a tap pops the bubble (state), the pop sound in the hooks, a vibration; the demo is done', st['down'] and 'pi_pop' in st['snd'] and 'pi_pop' in st['tg'] and st['vib'] > n0[1] and not st['demo'] and st['pops'] == 1, st)
    fe = await page.evaluate(f"""({{ ms: __vibMs.slice(-1)[0], parts: pi.parts.length, few: gfxLevel() === 0 || gfxReduced(), ring: pi.rings.length ? pi.rings[pi.rings.length - 1].r1 / {q['r']} : 0, rmax: Math.max(...pi.parts.map(p => p.r)),
      deep: [...SPRITES.keys()].some(k => k.startsWith('pib|' + pi.L.bubbles[0].col + '|') && k.includes('|deep|')), run: !!audio && audio.state === 'running', bus: !!audio && !!audio.__popBus && audio.__popBus.gain.value, last: pi.popLast,
      xylo: __grasp.tg.snd.slice(-4).includes('xylo') }})""")
    check(tag + ': the pop\'s feel: navigator.vibrate(10); the burst (9-12 bits sized by the bubble, half at the low graphics level) + a white ring to 1.45 r; the deep dimple sprite', fe['ms'] == 10 and ((4 <= fe['parts'] <= 6) if fe['few'] else (9 <= fe['parts'] <= 12)) and abs(fe['ring'] - 1.45) < 0.01 and fe['rmax'] > 3 and fe['deep'], fe)
    check(tag + ': the sound: sound B (crisp) through the pop sub-bus (gain 1.3), no row note', (not fe['run'] or (abs(fe['bus'] - 1.3) < 1e-6 and fe['last'] and fe['last']['k'] > 0.4)) and not fe['xylo'] and await page.evaluate("!/PI_RAINBOW|o\\.col/.test(piPopSyn.toString()) && /5200/.test(piPopSyn.toString())"), fe)
    cx, hw = await page.evaluate("[pi.L.bx + pi.L.bw / 2, pi.L.bw / 2]")
    await tap(page, q['x'], q['y'])
    st2 = await page.evaluate(f"({{ down: pi.st[0].down, pops: pi.pops, snd: {P}.snd.slice(-1) }})")
    check(tag + ': a popped bubble stays popped (a soft tock, no second pop)', st2['down'] and st2['pops'] == 1 and st2['snd'] == ['pi_tock'], st2)
    q1 = bs[1]; await page.evaluate("pi.flex.x = pi.flex.v = 0")
    k = await page.evaluate(f"(() => {{ fing('pointerdown', 6, {q1['x']}, {q1['y']}); const r = [pi.st[1].down, pi.flex.v, pi.flex.dirT]; fing('pointerup', 6, {q1['x']}, {q1['y']}); return r; }})()")
    check(tag + ': the board flex: a pop kicks the spring (the feel lab\'s 0.011), tilting toward its side', k[0] and abs(k[1] - 0.011) < 1e-6 and abs(k[2] - (q1['x'] - cx) / hw) < 0.01, k)
    await page.wait_for_timeout(1500); await page.evaluate("pi.flex.x = pi.flex.v = 0"); qq = q  # (held on the popped one: nothing more pops)
    await page.evaluate(f"fing('pointerdown', 7, {qq['x']}, {qq['y']})"); await page.wait_for_timeout(450); held = await page.evaluate("pi.flex.x")
    await page.evaluate(f"fing('pointerup', 7, {qq['x']}, {qq['y']})"); await page.wait_for_timeout(1500); rel = await page.evaluate("pi.flex.x")
    check(tag + ': a finger held on the board presses it down a little; let go, it springs back', 0.2 < held < 1.2 and abs(rel) < 0.15, (held, rel))
    # a tap between bubbles: a very soft tick, no xylophone note
    R0 = rows_of(await bubbles(page)); mx, my = (R0[0][1]['x'] + R0[1][2]['x']) / 2, (R0[0][1]['y'] + R0[1][2]['y']) / 2
    pops0 = await page.evaluate("pi.pops"); await tap(page, mx, my)
    m = await page.evaluate("({ snd: __grasp.popit.snd.slice(-1), tg: __grasp.tg.snd.slice(-3), pops: pi.pops })")
    check(tag + ': a tap between bubbles: only a very soft tick (no xylophone note, nothing pops)', m['snd'] == ['pi_tick'] and 'xylo' not in m['tg'] and m['pops'] == pops0, m)
    # a finger sliding over a row pops each one
    R = rows_of(await bubbles(page)); row = R[2]
    await drag(page, row[0]['x'] - 20, row[0]['y'] + 2, row[-1]['x'] + 20, row[-1]['y'] - 2, steps=12)
    got = await page.evaluate(f"{P}.bubbles().filter(b => Math.round(b.y) === {round(row[0]['y'])}).map(b => b.down)")
    check(tag + ': a swipe across a row pops every bubble it passes (%d)' % len(row), len(got) >= 3 and all(got), got)
    # two fingers at once
    a, c = R[3][0], R[3][-1]
    await page.evaluate(f"fing('pointerdown', 1, {a['x']}, {a['y']}); fing('pointerdown', 2, {c['x']}, {c['y']})"); await page.wait_for_timeout(80)
    await page.evaluate(f"fing('pointerup', 1, {a['x']}, {a['y']}); fing('pointerup', 2, {c['x']}, {c['y']})"); await page.wait_for_timeout(120)
    two = await page.evaluate(f"[pi.st[{a['i']}].down, pi.st[{c['i']}].down]")
    check(tag + ': two fingers pop two bubbles at once', two == [True, True], two)
    await page.wait_for_timeout(300); await page.screenshot(path=OUT + 'popit_free_%s.png' % ('he' if he else 'en'))
    # all popped: FLIP!
    side0 = await page.evaluate("pi.side")
    await pop_all(page)
    ok = await wait(page, "!!pi.flip", 3000); fl = await page.evaluate("[pi.flipText ? 1 : 0, __grasp.tg.said.map(x => x.text), __grasp.tg.snd.slice(-6)]")
    check(tag + ': every bubble popped: the board flips ("FLIP!" on screen, the louder whoosh; less talking: not said)', ok and fl[0] == 1 and ('הופכים!' if he else 'Flip!') not in fl[1] and 'pi_whoosh' in fl[2], fl)
    ok = await wait(page, "!pi.flip && pi.st.every(s => !s.down)", 4000)
    ld = await page.evaluate("({ snd: __grasp.popit.snd.slice(-8), ms: __vibMs.slice(-3), flash: document.querySelectorAll('.flash, #flash').length })")
    check(tag + ': the flip lands: a thump with a little sparkle (pi_land), a stronger vibration (30 ms), no screen flash', 'pi_land' in ld['snd'] and 30 in ld['ms'] and ld['flash'] == 0, ld)
    r = await page.evaluate("({ side: pi.side, flips: profile.popit.flips, prog: profile.popit.prog, left: __grasp.popit.left(), n: pi.L.bubbles.length })")
    check(tag + ': after the flip every bubble is up again (the other side: the board mirrored); the flip counted', ok and r['side'] != side0 and r['flips'] == 1 and r['prog'] == 1 and r['left'] == r['n'], r)
    # the house in the corner: one tap, home
    r = await page.evaluate("({ homeOnly: document.body.classList.contains('homeOnly'), label: $('pauseBtn').getAttribute('aria-label'), home: t('home') })")
    check(tag + ': nothing to pause: the corner sticker is the house alone (homeOnly, label Home)', r['homeOnly'] and r['label'] == r['home'], r)
    await page.tap('#pauseBtn'); ok = await wait(page, "mode === 'none' && !$('start').hidden", 4000)
    check(tag + ': one tap on the house goes home at once (no sheet); the address is / again', ok and not await page.evaluate("menu.open") and await page.evaluate("location.pathname") == '/', await page.evaluate("[mode, gameMode, menu.open, location.pathname]"))
    check(tag + ': the profile keeps the flips', await page.evaluate("JSON.parse(localStorage.getItem('grasp.profile')).popit.flips") == 1)
    check(tag + ': no page errors', not errs, errs); await ctx.close()

async def kid_open(b, he, init=''):
    ctx, page, errs = await page_for(b, '/', he, init)
    await page.tap('#bigPopit')  # (navigation v2: the Big kids sticker: Free play at once; the modes in the corner)
    sub = await wait(page, "gameMode === 'popit' && mode === 'mouse' && !pi.over && pi.mode === 'free' && pi.flow === 'kid'", 6000)
    await page.wait_for_timeout(300); cr = await ui(page, 'corner'); await tap(page, cr['x'] + cr['w'] / 2, cr['y'] + cr['h'] / 2)
    ok = await wait(page, "pi.over && pi.over.kind === 'picker'", 3000); await page.wait_for_timeout(300)
    return ctx, page, errs, ok, sub

async def race_tests(b, he):
    tag = 'race ' + ('HE' if he else 'EN')
    ctx, page, errs, ok, sub = await kid_open(b, he)
    check(tag + ': the Big kids sticker opens Pop It in Free play at once (the kid flow, no picker first); its corner opens the mode picker', ok and sub and await page.evaluate("pi.flow === 'kid' && location.pathname === '/popit'"), sub)
    ids = [u['id'] for u in await page.evaluate(f"{P}.ui")]
    check(tag + ': the picker: Pop, Race, Colors, Remember, Boards (big round icons)', ids == ['mode:free', 'mode:race', 'mode:color', 'mode:simon', 'mode:shelf'] and all(u.get('r', 0) >= 44 for u in await page.evaluate(f"{P}.ui")), ids)
    if not he: await page.screenshot(path=OUT + 'popit_picker_en.png')
    else: await page.screenshot(path=OUT + 'popit_picker_he.png')
    await press(page, 'mode:race'); ok = await wait(page, "pi.mode === 'race' && !pi.over", 3000)
    check(tag + ': Race picked; the clock waits for the first pop', ok and await page.evaluate("!pi.race.on && pi.race.ms === 0"))
    bs = await bubbles(page); await tap(page, bs[0]['x'], bs[0]['y'])
    check(tag + ': the first pop starts the clock', await page.evaluate("pi.race.on"))
    await page.evaluate("pi.race.ms = 20000")  # (a slow round: 1 star, no new board)
    await pop_all(page)
    ok = await wait(page, "pi.race.done && pi.over && pi.over.kind === 'race'", 4000)
    r = await page.evaluate("({ o: pi.over, best: profile.popit.best.square, stars: profile.popit.stars.square, t3: __grasp.popit.raceT(pi.L.bubbles.length, 3), t2: __grasp.popit.raceT(pi.L.bubbles.length, 2) })")
    o = r['o'] or {}; exp = 3 if o.get('ms', 1e9) <= r['t3'] else 2 if o.get('ms', 1e9) <= r['t2'] else 1
    check(tag + ': all popped: the time card; the best stored; 1-3 stars by the time (%s ms; 3* <= %d, 2* <= %d)' % (o.get('ms'), r['t3'], r['t2']), ok and o.get('ms', 0) > 0 and r['best'] == o['ms'] and o['stars'] == exp == r['stars'] and not o['record'], r)
    check(tag + ': stars: a slow time still gets 1 star; thresholds grow with the board (16 big bubbles: 4 s / 8 s; a small board at least 3 s / 6 s)', await page.evaluate("__grasp.popit.raceT(36, 3) === 8500 && __grasp.popit.raceT(36, 2) === 18000 && __grasp.popit.raceT(14, 3) < __grasp.popit.raceT(36, 3) && __grasp.popit.raceT(16, 3) === 4000 && __grasp.popit.raceT(16, 2) === 8000 && __grasp.popit.raceT(8, 3) === 3000 && __grasp.popit.raceT(8, 2) === 6000"))
    await page.wait_for_timeout(1200); await page.screenshot(path=OUT + 'popit_race_%s.png' % ('he' if he else 'en'))
    # Again: the board flips, a new race; a faster time = "New record!" (3 stars: a new board too)
    got0 = await page.evaluate("profile.popit.got.length")
    await press(page, 'again'); ok = await wait(page, "!pi.over && !pi.flip && pi.mode === 'race' && !pi.race.done && pi.st.every(s => !s.down)", 5000)
    check(tag + ': Again: the board flips back up, a new race', ok)
    bs = await bubbles(page); await tap(page, bs[0]['x'], bs[0]['y'])
    await page.evaluate("pi.race.ms = 600")  # (a fast hand)
    await pop_all(page)
    ok = await wait(page, "pi.over && pi.over.kind === 'race'", 4000)
    r = await page.evaluate("({ o: pi.over, best: profile.popit.best.square, got: profile.popit.got.slice(), q: pi.queue.map(x => x.kind) })")
    check(tag + ': a faster time: "New record!", 3 stars, the best updated', ok and r['o']['record'] and r['o']['stars'] == 3 and r['best'] == r['o']['ms'] and ('שיא חדש!' if he else 'New record!') not in await said(page) and 'record' in await page.evaluate("pi.snd"), r)
    check(tag + ': a 3-star race unlocks a new board (shown after the card)', len(r['got']) == got0 + 1 and r['q'] == ['reveal'], r)
    # Remember in the kid flow: two mistakes = a gentle end card
    check(tag + ': the race card: Again (big), Home (navigation v2: the modes stay in the corner)', [u['id'] for u in await page.evaluate(f"{P}.ui")][-2:] == ['again', 'home'])
    await press(page, 'again'); ok = await wait(page, "pi.over && pi.over.kind === 'reveal'", 3000)
    await page.wait_for_timeout(800); await tap(page, 195, 700); ok = await wait(page, "!pi.over || pi.over.kind === 'picker'", 3000)
    await page.evaluate(f"{P}.setMode('simon')"); ok = await wait(page, "pi.simon.phase === 'input'", 6000)
    seq = await page.evaluate("pi.simon.seq.slice()"); bs = await bubbles(page); wrong = next(q for q in bs if q['i'] != seq[0])
    await tap(page, wrong['x'], wrong['y']); ok1 = await wait(page, "pi.simon.phase === 'wait' || pi.simon.phase === 'show'", 2000)
    await wait(page, "pi.simon.phase === 'input'", 6000); await tap(page, wrong['x'], wrong['y'])
    ok = await wait(page, "pi.over && pi.over.kind === 'simon'", 3000)
    check(tag + ': Remember (kids): a mistake replays the sequence; a second = a gentle end card ("You remembered ...", the best)', ok1 and ok and await page.evaluate("pi.over.n >= 1 && pi.over.best >= 1"), await page.evaluate("[pi.simon.phase, pi.over]"))
    check(tag + ': no page errors', not errs, errs); await ctx.close()

async def pattern_tests(b, he):
    tag = 'colors ' + ('HE' if he else 'EN')
    ctx, page, errs = await page_for(b, '/popit', he, "localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, tips: ['tg_popit'] }));")
    await wait(page, "gameMode === 'popit' && mode === 'mouse'")
    # the little ones' Pop It has no mode button (navigation v2: no door elsewhere in a toddler game); the picker, through its hook (the little ones: no Race)
    check(tag + ': the little flow: no corner button drawn', await ui(page, 'corner') is None)
    await page.evaluate(f"{P}.act('corner')")
    ok = await wait(page, "pi.over && pi.over.kind === 'picker'", 2000); await page.wait_for_timeout(300)
    ids = [u['id'] for u in await page.evaluate(f"{P}.ui")]
    check(tag + ': the corner button opens the mode picker; the little ones get Pop, Colors, Remember, Boards', ok and ids == ['mode:free', 'mode:color', 'mode:simon', 'mode:shelf'], ids)
    await press(page, 'mode:color'); ok = await wait(page, "pi.mode === 'color' && !!pi.color.target", 3000)
    await page.wait_for_timeout(600)
    tgt = await page.evaluate("pi.color.target"); names = {'red': 'האדומות', 'blue': 'הכחולות', 'green': 'הירוקות', 'yellow': 'הצהובות', 'orange': 'הכתומות', 'purple': 'הסגולות'}
    w = await said(page)
    check(tag + ': Colors: the voice names the colour only ("%s!")' % tgt, ok and any(((names[tgt] + '!') if he else (tgt.capitalize() + '!')) == s for s in w), w[-2:])
    bs = await bubbles(page); wrong = next(q for q in bs if q['col'] != tgt); right = [q for q in bs if q['col'] == tgt]
    await tap(page, wrong['x'], wrong['y'])
    st = await page.evaluate(f"[pi.st[{wrong['i']}].down, pi.color.wrong]")
    await page.wait_for_timeout(500)
    st2 = await page.evaluate(f"({{ down: pi.st[{wrong['i']}].down, snd: {P}.snd.slice(-4), mode: pi.mode, target: pi.color.target, over: pi.over }})")
    check(tag + ': a wrong colour pops, then springs back up with a boing: never a fail (same colour asked, no card)', st[0] and st[1] == 1 and not st2['down'] and 'boing' in st2['snd'] and st2['mode'] == 'color' and st2['target'] == tgt and not st2['over'], [st, st2])
    for q in right[:-1]: await tap(page, q['x'], q['y'])
    await page.wait_for_timeout(250); await page.screenshot(path=OUT + 'popit_pattern_%s.png' % ('he' if he else 'en'))
    await tap(page, right[-1]['x'], right[-1]['y'])
    ok = await wait(page, "!!pi.color.okAt", 2000); w = await said(page)
    check(tag + ': every %s one popped: a party (its chord), no "Well done!" line' % tgt, ok and not any(('כל הכבוד' in x if he else 'Well done' in x) for x in w) and 'chord' in await page.evaluate("__grasp.tg.snd.slice(-6)"), w[-1:])
    ok = await wait(page, f"pi.color.target && pi.color.target !== '{tgt}' && !pi.color.okAt", 4000)
    check(tag + ': then the next colour', ok, await page.evaluate("pi.color.target"))
    # Remember (Simon), the little ones' flow: the sequence plays, repeat it, it grows; a mistake replays it (no end)
    await page.evaluate(f"{P}.setMode('simon')")
    ok = await wait(page, "pi.simon.phase === 'show' && pi.simon.shown >= 0", 4000); await page.wait_for_timeout(150)
    lit = await page.evaluate("pi.st.filter(s => performance.now() - s.lit < 600).length")
    await page.screenshot(path=OUT + 'popit_simon_%s.png' % ('he' if he else 'en'))
    check(tag + ': Remember: the bubbles light up in order (a note each)', ok and lit >= 1 and 'pi_note' in await page.evaluate(f"{P}.snd"), lit)
    ok = await wait(page, "pi.simon.phase === 'input'", 6000); seq = await page.evaluate("pi.simon.seq.slice()"); bs = await bubbles(page)
    for i in seq: await tap(page, bs[i]['x'], bs[i]['y']); await page.wait_for_timeout(60)
    ok2 = await wait(page, "pi.simon.phase === 'ok' || pi.simon.seq.length === %d" % (len(seq) + 1), 2000)
    ok3 = await wait(page, "pi.simon.seq.length === %d && pi.simon.phase === 'input'" % (len(seq) + 1), 9000)
    check(tag + ': the sequence repeated: it grows by one (%d -> %d) and plays again' % (len(seq), len(seq) + 1), ok and ok2 and ok3 and await page.evaluate("pi.simon.best") == len(seq), await page.evaluate("[pi.simon.phase, pi.simon.seq.length]"))
    seq = await page.evaluate("pi.simon.seq.slice()"); wrong = next(q for q in bs if q['i'] != seq[0])
    await tap(page, wrong['x'], wrong['y'])
    ok = await wait(page, "pi.simon.phase === 'show'", 3000)
    check(tag + ': a mistake (little ones): the same sequence plays again, no end card', ok and await page.evaluate("pi.simon.seq.length") == len(seq) and not await page.evaluate("pi.over"))
    check(tag + ': no page errors', not errs, errs); await ctx.close()

async def shelf_tests(b, he):
    tag = 'boards ' + ('HE' if he else 'EN')
    ctx, page, errs = await page_for(b, '/popit', he, "localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, tips: ['tg_popit'], popit: { got: ['square', 'nope', 'heart'], board: 'nope', prog: 2, flips: 8, best: { square: 9000, bad: 4, heart: -3 }, stars: { square: 2, circle: 7 }, simon: 'x' } }));")
    await wait(page, "gameMode === 'popit' && mode === 'mouse'")
    P0 = await page.evaluate("profile.popit")
    check(tag + ': the stored profile is validated (unknown boards / bad numbers dropped, the 3 first boards always there)', P0['got'] == ['square', 'circle', 'heart'] and P0['board'] == 'square' and P0['best'] == {'square': 9000} and P0['stars'] == {'square': 2} and P0['simon'] == 0 and P0['prog'] == 2 and P0['flips'] == 8, P0)
    # the 9th flip (3 since the last board): a new board
    await pop_all(page)
    ok = await wait(page, "pi.over && pi.over.kind === 'reveal'", 5000)
    r = await page.evaluate("({ got: profile.popit.got.slice(), stored: JSON.parse(localStorage.getItem('grasp.profile')).popit.got, id: pi.over && pi.over.id, prog: profile.popit.prog })")
    await page.wait_for_timeout(700); w = await said(page)
    if not he: await page.screenshot(path=OUT + 'popit_reveal_en.png')
    check(tag + ': every 3 flips a new board: "New board!" (the star), in the profile and stored', ok and r['id'] == 'star' and 'star' in r['got'] and 'star' in r['stored'] and r['prog'] == 0 and not any(('לוח חדש!' if he else 'New board!') in s for s in w) and 'unlock' in await page.evaluate("pi.snd"), [r, w[-2:]])
    await tap(page, 195, 760); ok = await wait(page, "!pi.over && pi.board === 'star'", 3000)
    check(tag + ': a tap: play the new board', ok and await page.evaluate("profile.popit.board") == 'star')
    # the shelf: every board, the locked ones as silhouettes
    await page.evaluate(f"{P}.act('corner')"); await wait(page, "pi.over && pi.over.kind === 'picker'", 2000)  # (the little flow: no corner button: its hook)
    await press(page, 'mode:shelf'); ok = await wait(page, "pi.over && pi.over.kind === 'shelf'", 2000); await page.wait_for_timeout(500)
    tiles = [u['id'] for u in await page.evaluate(f"{P}.ui") if u['id'].startswith('board:')]
    check(tag + ': the shelf shows the 4 boards got as tiles (the 6 others locked)', ok and tiles == ['board:square', 'board:circle', 'board:heart', 'board:star'], tiles)
    await page.screenshot(path=OUT + 'popit_shelf_%s.png' % ('he' if he else 'en'))
    await press(page, 'board:heart'); ok = await wait(page, "!pi.over && pi.board === 'heart'", 2000)
    check(tag + ': a tile picks that board', ok and await page.evaluate("profile.popit.board") == 'heart')
    if not he:  # every board draws (the special ones too), a few bubbles popped
        await page.evaluate("profile.popit.got = __grasp.popit.ids.slice()")
        from PIL import Image
        shots = []; r_sq = None
        for bid in await page.evaluate(f"{P}.ids"):
            await page.evaluate(f"{P}.board('{bid}')"); await page.wait_for_timeout(250)
            bs = await bubbles(page); n = len(bs)
            r_min = min(q['r'] for q in bs); r_sq = r_sq or r_min
            check(tag + ': board %s: 8-32 large bubbles (the square\'s size, at most a little smaller to fit 8; the square: 4 a row, rows to the height), >= 44 px' % bid, 8 <= n <= 32 and r_min >= 22 and r_min >= r_sq * 0.88, (n, round(r_min, 1), round(r_sq, 1)))
            for q in bs[::3]: await page.evaluate(f"pi.st[{q['i']}].down = true")
            await page.wait_for_timeout(200); p = OUT + 'popit_b_%s.png' % bid; await page.screenshot(path=p); shots.append(p)
        ims = [Image.open(p).crop((0, 300, 780, 1500)).resize((260, 400)) for p in shots]
        sheet = Image.new('RGB', (260 * 5, 800), 'white')
        for k, im in enumerate(ims): sheet.paste(im, ((k % 5) * 260, (k // 5) * 400))
        sheet.save(OUT + 'popit_boards_en.png')
        for p in shots: os.remove(p)
    check(tag + ': no page errors', not errs, errs); await ctx.close()

async def feel_tests(b):  # reduced motion: no flex; the iPhone (no Vibration API): the switch haptic, never throwing
    ctx, page, errs = await page_for(b, '/popit', False, "localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, tips: ['tg_popit'] }));")
    await wait(page, "gameMode === 'popit' && mode === 'mouse'")
    await page.evaluate("gfxq.reducedTest = true"); bs = await bubbles(page)
    await page.evaluate(f"fing('pointerdown', 3, {bs[0]['x']}, {bs[0]['y']})"); await page.wait_for_timeout(400); f = await page.evaluate("[pi.flex.x, pi.flex.v, pi.st[0].down, pi.parts.length]")
    await page.evaluate(f"fing('pointerup', 3, {bs[0]['x']}, {bs[0]['y']})"); await page.evaluate("gfxq.reducedTest = null")
    check('reduced motion: a pop and a held finger leave the board still (no flex), half the bits', f[0] == 0 and f[1] == 0 and f[2] and 4 <= f[3] <= 6, f)
    check('feel: no page errors', not errs, errs); await ctx.close()
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True, user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1')
    page = await ctx.new_page(); await routes(page); errs = []; page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + SPEECH + FINGERS.split('window.__vib')[0] + "localStorage.setItem('lang','en'); delete Navigator.prototype.vibrate; window.__clicks = 0; document.addEventListener('click', () => __clicks++);")
    await page.goto(BASE + '/popit'); await wait(page, "typeof gameMode !== 'undefined' && gameMode === 'popit' && mode === 'mouse'", 15000)
    bs = await bubbles(page); await tap(page, bs[0]['x'], bs[0]['y']); await tap(page, bs[1]['x'], bs[1]['y'])
    r = await page.evaluate("({ vibApi: 'vibrate' in navigator, hap: pi.hapIOS | 0, el: !!document.querySelector('label[aria-hidden=true] > input[type=checkbox][switch]'), down: pi.st[0].down && pi.st[1].down, clicks: __clicks })")
    check('iPhone (no navigator.vibrate): each pop toggles the hidden switch (the iOS 18 haptic tick), its click kept from the page, no errors', not r['vibApi'] and r['hap'] == 2 and r['el'] and r['down'] and r['clicks'] == 0 and not errs, [r, errs])
    await ctx.close()

async def picker_tests(b):
    for he in (False, True):
        ctx, page, errs = await page_for(b, '/', he)
        await page.tap('#littleBtn'); await wait(page, "!$('littlePick').hidden", 3000); await page.evaluate("__grasp.menub.page(3, true)"); await page.wait_for_timeout(500)
        t = await page.evaluate("""(() => { const b = $('lilPopit'), q = b.getBoundingClientRect(), pg = $('mbPager').getBoundingClientRect(); return { w: q.width, h: q.height, inside: q.left >= pg.left - 0.5 && q.right <= pg.right + 0.5 && q.bottom <= innerHeight, art: !!b.querySelector('.ic svg, .ic canvas'), label: b.querySelector('.lb').textContent.trim() }; })()""")
        check(('HE' if he else 'EN') + ': Little ones has a big Pop It sticker (page 4), on screen', t['art'] and t['inside'] and t['w'] >= 90 and t['h'] >= 90 and t['label'] == ('פופ איט' if he else 'Pop It'), t)
        await page.tap('#lilPopit')
        ok = await wait(page, "gameMode === 'popit' && mode === 'mouse' && location.pathname === '/popit' && pi.mode === 'free' && pi.flow === 'little' && !pi.over", 6000)
        check(('HE' if he else 'EN') + ': the tile opens Free mode at once', ok)
        check(('HE' if he else 'EN') + ' picker: no page errors', not errs, errs); await ctx.close()

async def fart_tests(b):
    # the owner: a Pop It mode, off by default (Settings: "Pop It: farts"), where every pop is a different, weird fart or burp
    ctx, page, errs = await page_for(b, '/popit', True); await wait(page, "mode === 'mouse' && gameMode === 'popit' && $('start').hidden")
    bs = await bubbles(page); await page.touchscreen.tap(bs[0]['x'], bs[0]['y']); await page.wait_for_timeout(200)
    check('farts: off by default: a pop is the crisp pop, no rude noise', 'rude' not in await page.evaluate("pi.snd") and 'pi_pop' in await page.evaluate("pi.snd"))
    await page.evaluate("localStorage.setItem('grasp.fun.popFart', '1'); audioInit(); rudeLoad(); Promise.all(Object.values(rude.buf))"); await page.wait_for_timeout(1500)
    n0 = await page.evaluate("rude.n")
    for q in bs[1:7]: await page.touchscreen.tap(q['x'], q['y']); await page.wait_for_timeout(260)
    r = await page.evaluate("({ n: rude.n, rude: pi.snd.filter(x => x === 'rude').length, loaded: Object.values(rude.buf).filter(x => x instanceof AudioBuffer).length, tot: RUDE.length })")
    check('farts: on: every pop plays a rude noise (real recordings, all 15 load), a different one each time', r['rude'] == 6 and r['n'] - n0 == 6 and r['loaded'] == r['tot'] == 15, r)
    check('farts: no page errors', not errs, errs); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        only = os.environ.get('PI_ONLY', '')
        for he in (False, True):
            if not only or 'free' in only: await free_tests(b, he)
            if not only or 'race' in only: await race_tests(b, he)
            if not only or 'pattern' in only: await pattern_tests(b, he)
            if not only or 'shelf' in only: await shelf_tests(b, he)
        if not only or 'feel' in only: await feel_tests(b)
        if not only or 'picker' in only: await picker_tests(b)
        if not only or 'fart' in only: await fart_tests(b)
        await b.close()
    srv.terminate()
    print('FAILS', check.fails); sys.exit(1 if check.fails else 0)

asyncio.run(main())
