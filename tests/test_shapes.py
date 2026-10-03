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

        # level 3: 5 shapes in similar colours; level 5: 6 shapes, two of them in another one's colour
        await page.evaluate(f"{S}.setLevel(3)"); l3 = await page.evaluate(f"{S}.shapes")
        warm = await page.evaluate("SHAPE_WARM")
        check('level 3: 5 shapes in similar (warm) colours', len(l3) == 5 and all(s['color'] in warm for s in l3), [s['color'] for s in l3])
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
