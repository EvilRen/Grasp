exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
import os, math
# The Little ones games (toddlers 1.5-4): Animal sounds (/animals), Colors (/colors, + the camera's "Show me something red!"), Peekaboo (/peekaboo),
# Feed the animal (/feed), Giant puzzle (/puzzle). For each: it loads by its link with no page errors in EN and HE (390 x 844, a phone) and from its
# Little ones tile; the first-play demo finger + <= 3 words is voiced; a right tap / drag moves the game on; a wrong one never fails (no buzzer,
# nothing lost, the game goes on); a double tap counts once; the pause button is the way out. Colors' camera: a frame coloured red (injected
# through the debug hook, the real analysis) is found after ~1 s held; a grey frame never is; no camera = the "camera is resting" card + touch play.
# Screenshots: tests/out/toddler_<game>_{en,he}.png (+ a few extra moments).
PORT = int(os.environ.get('GRASP_PORT', '8765')); BASE = 'http://localhost:%d' % PORT
if PORT != 8765: srv.terminate()  # (another server, e.g. a dev one: the prelude's own 8765 server is not needed)
OUT = 'tests/out/'
T = '__grasp.tg'
SPEECH = """window.__spoken = []; (() => { const ss = { speak: (u) => __spoken.push({ text: u.text, lang: u.lang }), cancel() {}, getVoices: () => [{ lang: 'en-US', name: 'E' }, { lang: 'he-IL', name: 'H' }], speaking: false };
  try { Object.defineProperty(window, 'speechSynthesis', { value: ss, configurable: true }); } catch (e) {} window.SpeechSynthesisUtterance = function (t) { this.text = t; }; })();"""
FINGERS = """window.fing = (type, id, x, y) => { const c = document.getElementById('stage'), e = new PointerEvent(type, { pointerId: id, pointerType: 'touch', clientX: x, clientY: y, isPrimary: id === 1, bubbles: true, cancelable: true, button: 0, buttons: type === 'pointerup' ? 0 : 1 }); (type === 'pointerdown' ? c : window).dispatchEvent(e); };"""

async def page_for(b, path='/', he=False, init='', mobile=True):
    opts = dict(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + SPEECH + FINGERS + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');") + init)
    await page.goto(BASE + path); await page.wait_for_function("typeof engine !== 'undefined' && !!engine", timeout=15000)
    return ctx, page, errs

async def wait(page, cond, timeout=8000):
    try: await page.wait_for_function(cond, timeout=timeout); return True
    except Exception: return False

async def tap(page, x, y, hold=70, pid=1):
    await page.evaluate(f"fing('pointerdown', {pid}, {x}, {y})"); await page.wait_for_timeout(hold)
    await page.evaluate(f"fing('pointerup', {pid}, {x}, {y})"); await page.wait_for_timeout(120)

async def drag(page, x0, y0, x1, y1, steps=10, pid=1):
    await page.evaluate(f"fing('pointerdown', {pid}, {x0}, {y0})"); await page.wait_for_timeout(80)
    for k in range(1, steps + 1):
        await page.evaluate(f"fing('pointermove', {pid}, {x0 + (x1 - x0) * k / steps}, {y0 + (y1 - y0) * k / steps})"); await page.wait_for_timeout(30)
    await page.wait_for_timeout(80); await page.evaluate(f"fing('pointerup', {pid}, {x1}, {y1})"); await page.wait_for_timeout(150)

async def said(page): return [s['text'] for s in await page.evaluate(f"{T}.said")]
async def snd(page): return await page.evaluate(f"{T}.snd.slice()")

async def link_tests(b, game, he, extra=None):
    """the game's own link: it starts at once (touch), the demo finger + its words (voiced), the pause button, no page errors"""
    tag = game + ' ' + ('HE' if he else 'EN')
    ctx, page, errs = await page_for(b, '/' + game, he)
    ok = await wait(page, f"mode === 'mouse' && gameMode === '{game}' && $('start').hidden")
    check(tag + ': /' + game + ' opens the game at once (touch)', ok, await page.evaluate("[mode, gameMode, location.pathname]"))
    ok = await wait(page, f"{T}.demoOn() && {T}.said.length > 0", 4000)
    words = await said(page)
    check(tag + ': first play: the demo finger and <= 3 words, voiced', ok and len(words[0].replace('!', '').split()) <= 3, words)
    check(tag + ': the pause button is the way out (minChrome, nothing else on the canvas)', await page.evaluate("document.body.classList.contains('minChrome') && !$('pauseBtn').hidden"))
    r = extra and await extra(page, tag)
    await page.wait_for_timeout(400); await page.screenshot(path=OUT + 'toddler_%s_%s.png' % (game, 'he' if he else 'en'))
    await page.tap('#pauseBtn'); ok = await wait(page, "menu.open", 3000)
    check(tag + ': the pause menu opens', ok)
    await page.click('#homeBtn'); ok = await wait(page, "mode === 'none' && !$('start').hidden", 4000)
    check(tag + ': Home from the pause menu leaves; the address is / again', ok and await page.evaluate("location.pathname") == '/')
    check(tag + ': no page errors', not errs, errs); await ctx.close()

# ---------------- Animal sounds ----------------
async def animals_extra(page, tag):
    st = await page.evaluate(f"{T}.an.list.map(a => ({{ k: a.kind, x: a.x, y: a.y, c: a.cell, R: a.R }}))")
    check(tag + ': 8 animals, every target >= 120 px', len(st) == 8 and all(a['c']['w'] >= 120 and a['c']['h'] >= 120 for a in st), [(a['k'], round(a['c']['w']), round(a['c']['h'])) for a in st])
    cow = next(a for a in st if a['k'] == 'cow'); pig = next(a for a in st if a['k'] == 'pig')
    await tap(page, cow['x'], cow['y'])
    ok = await wait(page, f"{T}.snd.includes('an_cow') && !{T}.demoOn()", 3000)
    await page.wait_for_timeout(1100); w = await said(page); name = 'פרה' if 'HE' in tag else 'Cow'
    check(tag + ': a tap: the cow bounces, moos, and the voice says "' + name + '!" (the demo is done)', ok and any(name + '!' in s for s in w) and await page.evaluate(f"performance.now() - {T}.an.list.find(a => a.kind === 'cow').hit < 3000"), w[-2:])
    # a double tap on the same animal counts once
    n0 = (await snd(page)).count('an_pig')
    await page.evaluate(f"fing('pointerdown', 1, {pig['x']}, {pig['y']})"); await page.evaluate(f"fing('pointerup', 1, {pig['x']}, {pig['y']})"); await page.wait_for_timeout(120)
    await page.evaluate(f"fing('pointerdown', 1, {pig['x']}, {pig['y']})"); await page.evaluate(f"fing('pointerup', 1, {pig['x']}, {pig['y']})"); await page.wait_for_timeout(200)
    check(tag + ': a double tap on the pig plays it once', (await snd(page)).count('an_pig') - n0 == 1, (await snd(page))[-4:])
    # "Where is the pig?": a wrong animal just plays; the right one = confetti, "Yes!"
    await page.wait_for_timeout(500); await page.evaluate(f"{T}.anAsk('pig')"); await page.wait_for_timeout(300)
    q = 'איפה החזיר?' if 'HE' in tag else 'Where is the pig?'
    check(tag + ': the question is asked: "' + q + '"', q in await said(page), (await said(page))[-2:])
    await tap(page, cow['x'], cow['y']); await page.wait_for_timeout(300)
    r = await page.evaluate(f"({{ ask: {T}.an.ask, found: {T}.an.found, snd: {T}.snd.slice(-3) }})")
    check(tag + ': a wrong animal (the cow) just moos: the question stays, nothing lost, no buzzer', r['ask'] and r['ask']['kind'] == 'pig' and not r['ask'].get('ok') and r['found'] == 0 and r['snd'][-1] == 'an_cow', r)
    await page.screenshot(path=OUT + 'toddler_animals_ask_%s.png' % ('he' if 'HE' in tag else 'en'))
    await tap(page, pig['x'], pig['y']); await page.wait_for_timeout(900)
    r = await page.evaluate(f"({{ ask: {T}.an.ask, found: {T}.an.found, snd: {T}.snd.slice(-4) }})")
    yes = ('נכון! חזיר!' if 'HE' in tag else 'Yes! Pig!')
    check(tag + ': the right animal: found (confetti), "' + yes + '"', r['found'] == 1 and r['ask'] and r['ask'].get('ok') and 'an_pig' in r['snd'] and yes in await said(page), [r, (await said(page))[-2:]])
    await page.wait_for_timeout(2600)
    check(tag + ': the next question follows after a moment (never a timer, never an end)', await page.evaluate(f"!!{T}.an.ask && !{T}.an.ask.ok && {T}.an.ask.kind !== 'pig'"), await page.evaluate(f"{T}.an.ask"))

# ---------------- Colors: find, then sort ----------------
CO_NAMES = {False: {'red': 'Red', 'blue': 'Blue', 'yellow': 'Yellow', 'green': 'Green', 'orange': 'Orange', 'purple': 'Purple', 'pink': 'Pink', 'brown': 'Brown'},
            True: {'red': 'אדום', 'blue': 'כחול', 'yellow': 'צהוב', 'green': 'ירוק', 'orange': 'כתום', 'purple': 'סגול', 'pink': 'ורוד', 'brown': 'חום'}}
async def co_round(page): return await page.evaluate(f"(() => {{ const r = {T}.co.round; return r && {{ target: r.target, ok: r.ok, n: r.objs.length, objs: r.objs.map(o => ({{ col: o.col, x: o.x, y: o.y, R: o.R }})) }}; }})()")
async def colors_extra(page, tag):
    he = 'HE' in tag; N = CO_NAMES[he]
    r = await co_round(page)
    check(tag + ': find: 2 big things to start with (>= 120 px), one of them the colour asked', r and r['n'] == 2 and all(o['R'] * 2 >= 120 for o in r['objs']) and r['target'] in [o['col'] for o in r['objs']], r)
    await page.wait_for_timeout(1800); q = ('איפה ה%s?' if he else 'Where is the %s one?') % (N[r['target']] if he else N[r['target']].lower())
    check(tag + ': the voice asks "' + q + '"', q in await said(page), (await said(page))[-3:])
    wrong = next(o for o in r['objs'] if o['col'] != r['target']); right = next(o for o in r['objs'] if o['col'] == r['target'])
    tw0 = await page.evaluate(T + ".tg.twinkles || 0"); await tap(page, 20, 838); await page.wait_for_timeout(150)
    check(tag + ': every touch answers: a tap on nothing in particular twinkles (a note + sparkles)', await page.evaluate(T + ".tg.twinkles || 0") == tw0 + 1 and (await snd(page))[-1] == 'xylo', (await snd(page))[-2:])
    await tap(page, wrong['x'], wrong['y']); await page.wait_for_timeout(250)
    r2 = await co_round(page)
    check(tag + ': a wrong one wiggles and says its own colour ("' + N[wrong['col']] + '!"); no fail, the round goes on', not r2['ok'] and r2['target'] == r['target'] and (N[wrong['col']] + '!') in await said(page) and await page.evaluate(f"{T}.co.right") == 0, (await said(page))[-2:])
    await tap(page, right['x'], right['y']); await page.wait_for_timeout(500)
    praise = N[right['col']] + ('! כל הכבוד!' if he else '! Well done!')
    check(tag + ': the right one pops: "' + praise + '"', await page.evaluate(f"{T}.co.right") == 1 and praise in await said(page) and 'pop' in await snd(page), (await said(page))[-2:])
    await page.screenshot(path=OUT + 'toddler_colors_pop_%s.png' % ('he' if he else 'en'))
    if not he: # levels: every 3 right answers a level: more choices, more colours
        seen = []
        for k in range(8):
            await wait(page, f"{T}.co.round && !{T}.co.round.ok && {T}.co.round.objs.every(o => performance.now() - o.born > 0)", 5000)
            r = await co_round(page); seen.append(r['n']); o = next(o for o in r['objs'] if o['col'] == r['target'])
            await tap(page, o['x'], o['y']); await page.wait_for_timeout(250)
        lv = await page.evaluate(f"{T}.co.level")
        check('colors: levels grow: 2 -> 3 -> 4 choices (3 -> 8 colours)', lv >= 2 and max(seen) >= 3 and await page.evaluate(f"{T}.CO_COLS.length") == 8, [lv, seen])
    # sort
    await page.evaluate(f"{T}.coAct('sort')"); await page.wait_for_timeout(500)
    st = await page.evaluate(f"({{ items: {T}.co.items.map(i => ({{ col: i.col, x: i.x, y: i.y, R: i.R }})), b: {T}.co.baskets.map(b => ({{ col: b.col, x: b.x, y: b.y, w: b.w, h: b.h }})) }})")
    check(tag + ': sort: 4 things, 2 baskets (>= 120 px wide)', len(st['items']) == 4 and len(st['b']) == 2 and all(b['w'] >= 120 for b in st['b']), st)
    it = st['items'][0]; good = next(b for b in st['b'] if b['col'] == it['col']); bad = next(b for b in st['b'] if b['col'] != it['col'])
    await drag(page, it['x'], it['y'], bad['x'], bad['y'] - 10); await page.wait_for_timeout(700)
    r = await page.evaluate(f"({{ it: {T}.co.items[0], sorted: {T}.co.sorted }})")
    check(tag + ': the wrong basket: it bounces home, its colour is said, nothing lost', not r['it']['done'] and abs(r['it']['x'] - r['it']['hx']) < 2 and r['sorted'] == 0 and (N[it['col']] + '!') in await said(page), r)
    await drag(page, it['x'], it['y'], good['x'], good['y'] - 10); await page.wait_for_timeout(700)
    check(tag + ': dragged into its basket: in, a plop', await page.evaluate(f"{T}.co.items[0].done && {T}.co.sorted === 1"))
    it2 = st['items'][1]; b2 = next(b for b in st['b'] if b['col'] == it2['col'])
    await tap(page, it2['x'], it2['y']); await page.wait_for_timeout(200)
    check(tag + ': tap-tap: a tap picks it', await page.evaluate(f"{T}.co.sel === {T}.co.items[1]"))
    await tap(page, b2['x'], b2['y']); await page.wait_for_timeout(700)
    check(tag + ': ... a tap on its basket puts it in', await page.evaluate(f"{T}.co.items[1].done && {T}.co.sorted === 2"))
    for i in (2, 3):
        it3 = st['items'][i]; b3 = next(b for b in st['b'] if b['col'] == it3['col']); await drag(page, it3['x'], it3['y'], b3['x'], b3['y']); await page.wait_for_timeout(600)
    ok = await wait(page, f"{T}.co.sets === 1", 3000); await page.wait_for_timeout(300)
    await page.screenshot(path=OUT + 'toddler_colors_sort_%s.png' % ('he' if he else 'en'))
    ok2 = await wait(page, f"{T}.co.items.length === 6 && {T}.co.baskets.length === 3", 5000)
    check(tag + ': all sorted: a party, then 3 baskets / 6 things', ok and ok2)
    await page.evaluate(f"{T}.coAct('find')")

# ---------------- Colors with the camera: "Show me something red!" ----------------
CAM_FAIL = """(() => { const md = navigator.mediaDevices || {}; md.getUserMedia = () => Promise.reject(new TypeError("Cannot read properties of undefined (reading 'getUserMedia')")); try { Object.defineProperty(navigator, 'mediaDevices', { value: md, configurable: true }); } catch (e) {} })();"""
async def cam_tests(b, he):
    tag = 'colors camera ' + ('HE' if he else 'EN'); N = CO_NAMES[he]
    ctx, page, errs = await page_for(b, '/colors', he, init="localStorage.setItem('grasp.profile.tips.seen','1');")
    posts = []; page.on('request', lambda r: posts.append(r.url) if r.method != 'GET' else None)
    await wait(page, "gameMode === 'colors' && mode === 'mouse'")
    chip = await page.evaluate(f"{T}.co.chips.find(c => c.key === 'cam')")
    check(tag + ': a camera chip in the top row', chip is not None and chip['r'] * 2 >= 44, chip)
    await tap(page, chip['x'], chip['y'])
    ok = await wait(page, f"{T}.co.act === 'cam' && {T}.cc.state === 'on'", 10000)
    await page.evaluate(f"{T}.ccInject({{ rgb: null }})"); await page.wait_for_timeout(1400)
    show = ('תראו לי משהו %s!' if he else 'Show me something %s!') % (N['red'] if he else N['red'].lower())
    check(tag + ': the camera turns on (its own stream); the voice asks "' + show + '"', ok and show in await said(page), [await page.evaluate(f"{T}.cc.log"), (await said(page))[-2:]])
    # a grey frame: nothing, however long
    await page.wait_for_timeout(2200)
    r = await page.evaluate(f"({{ found: {T}.cc.found, prog: {T}.cc.prog, res: {T}.cc.res }})")
    check(tag + ': a grey frame never matches (grey / dark pixels are skipped)', r['found'] == 0 and r['prog'] == 0 and r['res'] and r['res']['best'] is None, r)
    # a short flash of red is not enough: it must be held ~1 s
    await page.evaluate(f"{T}.ccInject({{ rgb: [220, 40, 40] }})"); await page.wait_for_timeout(450); await page.evaluate(f"{T}.ccInject({{ rgb: null }})"); await page.wait_for_timeout(900)
    check(tag + ': red for half a second is not enough (held ~1 s)', await page.evaluate(f"{T}.cc.found") == 0)
    t0 = await page.evaluate(f"(() => {{ {T}.ccInject({{ rgb: [220, 40, 40] }}); return performance.now(); }})()")
    ok = await wait(page, f"{T}.cc.found === 1", 4000); dt = await page.evaluate(f"performance.now() - {t0}")
    await page.wait_for_timeout(500)
    seen = N['red'] + ('! מדהים!' if he else '! Amazing!')
    check(tag + ': red held up: found after ~1 s, a big party, "' + seen + '", a photo-sticker (memory only)', ok and 900 <= dt <= 2500 and seen in await said(page) and await page.evaluate(f"{T}.cc.stickers.length === 1 && {T}.cc.stickers[0].c instanceof HTMLCanvasElement"), [dt, (await said(page))[-2:]])
    await page.screenshot(path=OUT + 'toddler_colors_cam_found_%s.png' % ('he' if he else 'en'))
    if not he:
        await page.wait_for_timeout(2800)
        # a dim room: a dark red on a dark background (the gain lifts it)
        await page.evaluate(f"{T}.ccTarget('red'); {T}.ccInject({{ rgb: [62, 11, 11], bg: [30, 30, 32] }})")
        ok1 = await wait(page, f"{T}.cc.found === 2", 4000); await page.wait_for_timeout(2900)
        # warm light: a blue thing under a yellowish lamp (the white balance from the grey around it)
        await page.evaluate(f"{T}.ccTarget('blue'); {T}.ccInject({{ rgb: [55, 85, 150], bg: [160, 128, 96] }})")
        ok2 = await wait(page, f"{T}.cc.found === 3", 4000); await page.wait_for_timeout(2900)
        # orange accepts its neighbour: a brown-orange thing
        await page.evaluate(f"{T}.ccTarget('orange'); {T}.ccInject({{ rgb: [205, 105, 40] }})")
        ok3 = await wait(page, f"{T}.cc.found === 4", 4000); await page.wait_for_timeout(2900)
        # a white thing under a warm lamp is not blue / yellow
        await page.evaluate(f"{T}.ccTarget('blue'); {T}.ccInject({{ rgb: [250, 225, 180], bg: [160, 128, 96] }})"); await page.wait_for_timeout(2200)
        ok4 = await page.evaluate(f"{T}.cc.found === 4")
        check('colors camera: forgiving: a dim room (dark red), a warm lamp (blue), orange = a brownish orange; a white thing under the lamp is not blue', ok1 and ok2 and ok3 and ok4, [ok1, ok2, ok3, ok4, await page.evaluate(f"{T}.cc.log.slice(-8)")])
        r = await page.evaluate(f"{T}.ccAnalyze((() => {{ const c = document.createElement('canvas'); c.width = c.height = 48; const g = c.getContext('2d'); g.fillStyle = '#808080'; g.fillRect(0, 0, 48, 48); return g.getImageData(0, 0, 48, 48); }})())")
        check('colors camera: ccAnalyze on a plain grey frame: no colour', r['best'] is None and r['chroma'] == 0, r)
    check(tag + ': nothing is sent anywhere (no POST / PUT)', not posts, posts)
    await page.evaluate("goHome()"); await page.wait_for_timeout(300)
    check(tag + ': Home stops the camera', await page.evaluate(f"{T}.cc.state === 'off' && !{T}.cc.stream"))
    check(tag + ': no page errors', not errs, errs); await ctx.close()
    # no camera: the friendly card, the touch game
    ctx, page, errs = await page_for(b, '/colors', he, init=CAM_FAIL)
    await wait(page, "gameMode === 'colors' && mode === 'mouse'"); await page.evaluate(f"{T}.coAct('cam')")
    ok = await wait(page, f"!$('banner').hidden && {T}.co.act === 'find' && {T}.cc.state === 'resting'", 8000); await page.wait_for_timeout(400)
    txt = await page.evaluate("document.body.innerText"); rest = 'המצלמה נחה' if he else 'Camera is resting'
    check(tag + ': no camera: "' + rest + ' ..." and the touch game (find) goes on; no technical text', ok and rest in txt and 'TypeError' not in txt and 'getUserMedia' not in txt and await page.evaluate("$('bannerList').hidden"), txt[:200])
    await page.screenshot(path=OUT + 'toddler_colors_cam_resting_%s.png' % ('he' if he else 'en'))
    check(tag + ' (no camera): no page errors', not errs, errs); await ctx.close()

# ---------------- Peekaboo ----------------
PK_NAMES = {False: {'dog': 'puppy', 'cat': 'kitty', 'duck': 'duck', 'pig': 'pig', 'bunny': 'bunny', 'monkey': 'monkey', 'cow': 'cow', 'sheep': 'sheep'},
            True: {'dog': 'כלבלב', 'cat': 'חתלתול', 'duck': 'ברווז', 'pig': 'חזיר', 'bunny': 'ארנב', 'monkey': 'קוף', 'cow': 'פרה', 'sheep': 'כבשה'}}
async def peekaboo_extra(page, tag):
    he = 'HE' in tag; N = PK_NAMES[he]
    st = await page.evaluate(f"({{ spots: {T}.pk.spots.map(s => ({{ kind: s.kind, who: s.who, x: s.x, y: s.y, c: s.cell }})), target: {T}.pk.target }})")
    check(tag + ': 6 hiding spots (bush, door, cloud, box, curtain, tree), each >= 120 px; one hides the animal asked for', sorted(s['kind'] for s in st['spots']) == sorted(['bush', 'door', 'cloud', 'box', 'curtain', 'tree']) and all(s['c']['w'] >= 120 and s['c']['h'] >= 120 for s in st['spots']) and [s['who'] for s in st['spots']].count(st['target']) == 1, st)
    await page.wait_for_timeout(1700); tgt = st['target']
    q = ('איפה ה%s %s?' % (N[tgt], 'מתחבאת' if tgt in ('cow', 'sheep') else 'מתחבא')) if he else "Where's the %s hiding?" % N[tgt]
    check(tag + ': the voice asks "' + q + '"', q in await said(page), (await said(page))[-2:])
    empty = next(s for s in st['spots'] if not s['who']); other = next(s for s in st['spots'] if s['who'] and s['who'] != tgt); right = next(s for s in st['spots'] if s['who'] == tgt)
    SPOT = T + ".pk.spots.find(s => s.kind === '%s')"
    await tap(page, empty['x'], empty['y']); await page.wait_for_timeout(500)
    r = await page.evaluate("({ st: " + (SPOT % empty['kind']) + ".state, snd: " + T + ".snd.slice(-2), found: " + T + ".pk.found, target: " + T + ".pk.target })")
    check(tag + ': an empty spot opens: a funny boing (a butterfly), nothing lost', r['st'] in ('open', 'opening') and 'boing' in r['snd'] and r['found'] == 0 and r['target'] == tgt, r)
    await tap(page, other['x'], other['y']); await page.wait_for_timeout(500)
    peek = 'קוקו!' if he else 'Peekaboo!'
    r = await page.evaluate("({ st: " + (SPOT % other['kind']) + ".state, snd: " + T + ".snd.slice(-3), found: " + T + ".pk.found })")
    check(tag + ': another animal pops out with a giggle and "' + peek + '"; the round goes on', r['st'] == 'open' and 'peek' in r['snd'] and r['found'] == 0 and peek in await said(page), r)
    await page.wait_for_timeout(2300)
    check(tag + ': ... and it hides again', await page.evaluate((SPOT % other['kind']) + ".state") in ('closing', 'closed'))
    await tap(page, right['x'], right['y']); await page.wait_for_timeout(1300)
    found = ('מצאת את ה%s!' % N[tgt]) if he else 'You found the %s!' % N[tgt]
    check(tag + ': the right spot: the animal pops out, confetti, "' + found + '"', await page.evaluate(T + ".pk.found") == 1 and found in await said(page), (await said(page))[-3:])
    await page.screenshot(path=OUT + 'toddler_peekaboo_found_%s.png' % ('he' if he else 'en'))
    ok = await wait(page, T + ".pk.round === 2 && !" + T + ".pk.done", 6000)
    check(tag + ': then a new round (another animal, shuffled spots)', ok and await page.evaluate(T + ".pk.target") != tgt)

# ---------------- Feed the animal ----------------
FD_NAMES = {False: {'carrot': 'carrot', 'bone': 'bone', 'fish': 'fish', 'banana': 'banana', 'snack': 'cookie'}, True: {'carrot': 'גזר', 'bone': 'עצם', 'fish': 'דג', 'banana': 'בננה', 'snack': 'עוגייה'}}
FE_AN = {False: {'bunny': 'bunny', 'dog': 'dog', 'cat': 'cat', 'monkey': 'monkey'}, True: {'bunny': 'ארנב', 'dog': 'כלב', 'cat': 'חתול', 'monkey': 'קוף'}}
async def fe_state(page): return await page.evaluate("(() => { const F = " + T + ".fe; return { who: F.who, fed: F.fed, state: F.state, tummy: F.tummy, foods: F.foods.map(f => ({ kind: f.kind, x: f.x, y: f.y, hx: f.hx, hy: f.hy, cell: f.cell, anim: f.anim && f.anim.k })), geo: F.geo, like: " + T + ".FE_LIKES[F.who], yucks: F.yucks, total: F.total, petSnack: F.petSnack, log: F.log.slice(-6) }; })()")
async def feed_one(page, kind, how='drag'):
    st = await fe_state(page); f = next(x for x in st['foods'] if x['kind'] == kind); G = st['geo']
    if how == 'drag': await drag(page, f['x'], f['y'], G['cx'], G['hy'] + G['R'] * 0.4)
    else: await tap(page, f['x'], f['y']); await page.wait_for_timeout(250); await tap(page, G['cx'], G['hy'])
async def feed_extra(page, tag):
    he = 'HE' in tag
    await wait(page, T + ".fe.state === 'wait'", 4000); await page.wait_for_timeout(1700)
    st = await fe_state(page)
    want = ('ה%s רוצה %s!' % (FE_AN[he][st['who']], FD_NAMES[he][st['like']])) if he else 'The %s wants a %s!' % (FE_AN[he][st['who']], FD_NAMES[he][st['like']])
    check(tag + ': a hungry animal (the bunny), 3 foods >= 120 px apart, the voice: "' + want + '"', st['who'] == 'bunny' and len(st['foods']) == 3 and all(f['cell']['w'] >= 120 for f in st['foods']) and st['like'] in [f['kind'] for f in st['foods']] and want in await said(page), [st['foods'], (await said(page))[-2:]])
    bad = next(f['kind'] for f in st['foods'] if f['kind'] != st['like'])
    await feed_one(page, bad); await page.wait_for_timeout(700)
    r = await fe_state(page); yuck = 'איכס!' if he else 'Yuck!'
    check(tag + ': the wrong food: a funny "' + yuck + '" face; nothing counted, never a fail', r['state'] == 'yuck' and r['fed'] == 0 and 'yuck' in await snd(page) and yuck in await said(page), r)
    await page.screenshot(path=OUT + 'toddler_feed_yuck_%s.png' % ('he' if he else 'en'))
    ok = await wait(page, T + ".fe.state === 'wait' && " + T + ".fe.foods.every(f => !f.anim)", 4000)
    check(tag + ': ... and it hops back to the blanket', ok)
    await feed_one(page, st['like']); await page.wait_for_timeout(900)
    r = await fe_state(page); yum = 'יאמי!' if he else 'Yummy!'
    check(tag + ': the liked food (dragged): chomp, "' + yum + '", the tummy grows', r['fed'] == 1 and r['tummy'] > 1 and 'munch' in await snd(page) and yum in await said(page), r)
    await wait(page, T + ".fe.state === 'wait'", 4000)
    await feed_one(page, st['like'], how='tap'); ok = await wait(page, T + ".fe.fed === 2", 3000)
    check(tag + ': tap-tap: a tap on the food, a tap on the animal: eaten', ok)
    if not he:
        for k in range(3):
            await wait(page, T + ".fe.state === 'wait'", 4000); await feed_one(page, st['like']); await page.wait_for_timeout(500)
        ok = await wait(page, T + ".fe.state === 'burp'", 4000); await page.wait_for_timeout(900)
        await page.screenshot(path=OUT + 'toddler_feed_burp_en.png')
        check('feed: 5 good bites: a burp + confetti ("Burp! Excuse me!")', ok and 'burp' in await snd(page) and 'Burp! Excuse me!' in await said(page))
        ok = await wait(page, T + ".fe.who !== 'bunny' && " + T + ".fe.state === 'wait'", 6000)
        check('feed: then the next animal comes in (hungry again)', ok and (await fe_state(page))['fed'] == 0)
        # the player's pet joins and gets +1 snack
        p0 = await page.evaluate("(() => { const P = petP(); P.hatched = true; P.egg = true; P.name = 'Bobo'; P.pantry = 2; saveProfile(); " + T + ".reset('feed'); return P.pantry; })()")
        order = await page.evaluate(T + ".fe.order")
        await page.evaluate(T + ".feEnter('pet')"); await wait(page, T + ".fe.state === 'wait'", 4000); await page.wait_for_timeout(300)
        check('feed: a hatched pet comes as one of the animals and asks for its cookie ("Bobo wants a cookie!")', 'pet' in order and 'Bobo wants a cookie!' in await said(page), [order, (await said(page))[-2:]])
        await feed_one(page, 'snack'); await page.wait_for_timeout(1200)
        r = await fe_state(page); p1 = await page.evaluate("petP().pantry")
        await page.screenshot(path=OUT + 'toddler_feed_pet_en.png')
        check('feed: the pet eats its cookie: +1 snack in its box', r['fed'] == 1 and p1 == p0 + 1 and r['petSnack'], [p0, p1, r['log']])
        await wait(page, T + ".fe.state === 'wait'", 4000); await feed_one(page, 'snack'); await page.wait_for_timeout(1200)
        check('feed: ... once a visit', await page.evaluate("petP().pantry") == p0 + 1)

# ---------------- Giant puzzle ----------------
async def pz_state(page): return await page.evaluate("(() => { const Z = " + T + ".pz; return { n: Z.n, pic: Z.pic, done: Z.done, solved: Z.solved, board: Z.board, pieces: Z.pieces.map(p => ({ i: p.i, x: p.x, y: p.y, w: p.sw * p.k, h: p.sh * p.k, sw: p.sw, sh: p.sh, tx: p.tx, ty: p.ty, placed: p.placed, snap: Math.max(" + T + ".PZ.snapMin, " + T + ".PZ.snapK * Math.max(p.sw, p.sh)) })) }; })()")
async def puzzle_extra(page, tag):
    he = 'HE' in tag
    st = await pz_state(page); P = st['pieces']
    check(tag + ': 2 big pieces (>= 120 px), a generous snap radius (>= 25% of the piece)', st['n'] == 2 and all(min(q['w'], q['h']) >= 120 for q in P) and all(q['snap'] >= 0.25 * max(q['sw'], q['sh']) for q in P), P)
    a, b = P[0], P[1]
    await drag(page, a['x'], a['y'], b['tx'], b['ty']); await page.wait_for_timeout(300)
    r = (await pz_state(page))['pieces'][0]
    check(tag + ': dropped on the wrong place: it just stays there (no fail)', not r['placed'] and abs(r['x'] - b['tx']) < 30, r)
    await drag(page, r['x'], r['y'], -300, 1200); await page.wait_for_timeout(300)
    r = (await pz_state(page))['pieces'][0]
    check(tag + ': dragged off the screen: it stays fully on the screen', not r['placed'] and r['x'] - r['w'] / 2 >= 0 and r['x'] + r['w'] / 2 <= 390 and r['y'] - r['h'] / 2 >= 0 and r['y'] + r['h'] / 2 <= 844, r)
    await drag(page, r['x'], r['y'], a['tx'] + a['snap'] * 0.7, a['ty'] - a['snap'] * 0.3); await page.wait_for_timeout(600)
    r = (await pz_state(page))['pieces'][0]
    check(tag + ': dropped near its place (within the snap radius): it snaps in with a click', r['placed'] and abs(r['x'] - a['tx']) < 1 and 'clunk' in await snd(page), r)
    await tap(page, b['x'], b['y']); await page.wait_for_timeout(200)
    check(tag + ': tap-tap: a tap picks the other piece', await page.evaluate(T + ".pz.sel && " + T + ".pz.sel.i === 1"))
    await tap(page, b['tx'] + 10, b['ty'] + 15); await page.wait_for_timeout(700)
    st = await pz_state(page); done = ('הידד! מכונית!' if he else 'Hooray! A car!')
    check(tag + ': ... a tap on its place: it flies in; the picture is whole and comes alive (the car drives off)', st['done'] and st['solved'] == 1 and all(q['placed'] for q in st['pieces']), st)
    await page.wait_for_timeout(1700); await page.screenshot(path=OUT + 'toddler_puzzle_alive_%s.png' % ('he' if he else 'en'))
    check(tag + ': "' + done + '" + confetti', done in await said(page), (await said(page))[-2:])
    ok = await wait(page, T + ".pz.n === 3 && !" + T + ".pz.done", 6000)
    check(tag + ': then the next picture with 3 pieces', ok and (await pz_state(page))['pic'] == 'cow')
    if not he:
        n = await page.evaluate(T + ".pzNext()"); await page.wait_for_timeout(300); st = await pz_state(page)
        check('puzzle: then 4 pieces (quarters), each still >= 120 px', n == 4 and len(st['pieces']) == 4 and all(min(q['w'], q['h']) >= 120 or min(q['sw'], q['sh']) >= 120 for q in st['pieces']), [(round(q['w']), round(q['h']), round(q['sw']), round(q['sh'])) for q in st['pieces']])
        for q in st['pieces']: await drag(page, q['x'], q['y'], q['tx'] + 12, q['ty'] - 12); await page.wait_for_timeout(450)
        ok = await wait(page, T + ".pz.done > 0", 3000)
        await page.screenshot(path=OUT + 'toddler_puzzle_4_en.png')
        check('puzzle: 4 pieces dragged in: done', ok)

async def picker_tests(b, games):
    for he in (False, True):
        ctx, page, errs = await page_for(b, '/', he)
        await page.tap('#littleBtn'); await wait(page, "!$('littlePick').hidden", 3000); await page.wait_for_timeout(500)
        L = await page.evaluate("""(() => { const P = $('littlePick'), sh = $('mbPager').getBoundingClientRect(); return [...P.querySelectorAll('.mbPg .stk')].map(b => { const q = b.getBoundingClientRect(), c = b.querySelector('.ic svg.mbI'); return { m: b.dataset.mode || b.id, w: q.width, h: q.height, inside: q.top >= sh.top - 8 && q.bottom <= sh.bottom + 8 && q.bottom <= innerHeight, art: !!c && c.childElementCount >= 2 && c.getBoundingClientRect().width > 60 }; }); })()""")  # (menu B: the Little ones room's pages of 4 stickers)
        tg_tiles = [x for x in L if x['m'] in games]
        check(('HE' if he else 'EN') + ': the Little ones room has a big sticker (its drawing) for each new game, each on its page, on screen', [x['m'] for x in tg_tiles] == games and all(x['art'] and x['inside'] and x['w'] >= 90 and x['h'] >= 90 for x in tg_tiles), L)
        await page.screenshot(path=OUT + 'toddler_picker_%s.png' % ('he' if he else 'en'))
        if not he:
            await page.evaluate("setInputPref('camera')")
            for g in games:
                if await page.evaluate("$('littlePick').hidden"): await page.tap('#littleBtn'); await wait(page, "!$('littlePick').hidden", 3000); await page.wait_for_timeout(500)
                await page.evaluate("(() => { const b = document.querySelector('#littlePick button[data-mode=%s]'); __grasp.menub.page([...$('mbPager').querySelectorAll('.mbPg')].indexOf(b.closest('.mbPg')), true); })()" % g); await page.wait_for_timeout(300)  # (its page)
                await page.tap('#littlePick button[data-mode=%s]' % g)
                ok = await wait(page, f"gameMode === '{g}' && mode === 'mouse' && $('start').hidden && location.pathname === '/{g}'", 6000)
                check('the ' + g + ' tile starts it by touch (even with the camera chosen) and pushes /' + g, ok)
                await page.evaluate("goHome()"); await page.wait_for_timeout(600)
        check(('HE' if he else 'EN') + ' picker: no page errors', not errs, errs); await ctx.close()

GAMES = ['animals', 'colors', 'peekaboo', 'feed', 'puzzle']
EXTRA = {'animals': animals_extra, 'colors': colors_extra, 'peekaboo': peekaboo_extra, 'feed': feed_extra, 'puzzle': puzzle_extra}

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--autoplay-policy=no-user-gesture-required'])
        only = os.environ.get('TG_ONLY', '')
        for g in GAMES:
            if only and g not in only.split(','): continue
            for he in (False, True): await link_tests(b, g, he, EXTRA.get(g))
        if not only or 'cam' in only:
            for he in (False, True): await cam_tests(b, he)
        if not only or 'picker' in only: await picker_tests(b, GAMES)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()  # (never leave a server behind, even after an error)
if check.fails: sys.exit(1)
