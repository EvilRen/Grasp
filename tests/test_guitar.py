# Busy Board: the electric guitar (strum / pluck, chord buttons, ROCK pedal, whammy, amp, sound chain, layout on phone + desktop)
exec(open('tests/test_busy.py').read().split('async def drag_line')[0])
G = W + "[18]"
GJ = "(() => { const w = " + G + ", g = w.geom(); return { x: w.x, y: w.y, w: w.w, h: w.h, o: g.o, T: g.T, sp0: g.sp0, kind: w.kind, st: JSON.parse(JSON.stringify(w.state)) }; })()"
LOG = G + ".state.log"
def notes_of(log): return [round(e['f'], 2) for e in log]
# every guitar part (amp, pedal, chord buttons, whammy tip, string ends) inside the widget's cell, and amp / pedal / buttons not overlapping
PARTS = "(() => { const w = " + G + ", g = w.geom(), r = (b) => { const q = w.toScreen(b.u, b.v); return { x0: q.x - b.w / 2, x1: q.x + b.w / 2, y0: q.y - b.h / 2, y1: q.y + b.h / 2 }; };" \
    " const bs = [r(g.amp), r(g.pedal), ...g.chords.map((c) => r({ u: c.u, v: c.v, w: g.btnR * 2, h: g.btnR * 2 }))], t = w.whammyPos(), ends = [0, 5].flatMap((i) => [w.toScreen(g.uB, g.vb[i]), w.toScreen(g.uN, g.vn[i])]);" \
    " const inR = (x, y) => x >= w.x - w.w / 2 && x <= w.x + w.w / 2 && y >= w.y - w.h / 2 && y <= w.y + w.h / 2;" \
    " const inside = bs.every((b) => inR(b.x0, b.y0) && inR(b.x1, b.y1)) && inR(t.x, t.y) && ends.every((q) => inR(q.x, q.y));" \
    " let apart = true; for (let i = 0; i < bs.length; i++) for (let j = i + 1; j < bs.length; j++) { const a = bs[i], b = bs[j]; if (a.x0 < b.x1 - 0.5 && b.x0 < a.x1 - 0.5 && a.y0 < b.y1 - 0.5 && b.y0 < a.y1 - 0.5) apart = false; }" \
    " return { inside, apart, btnR: g.btnR }; })()"

async def strum_mouse(page, down=True, steps=10, wait=25, after=120):
    a = await page.evaluate(G + ".stringPos(0)"); z = await page.evaluate(G + ".stringPos(5)"); g = await page.evaluate(GJ)
    ext = g['sp0'] * 0.9  # start / end beyond the outer strings
    dx, dy = (0, ext) if g['o'] == 'h' else (ext, 0)
    p0 = (a['x'] - dx, a['y'] - dy); p1 = (z['x'] + dx, z['y'] + dy)
    if not down: p0, p1 = p1, p0
    await page.mouse.move(*p0); await page.wait_for_timeout(50); await page.mouse.down(); await page.wait_for_timeout(40)
    for i in range(1, steps + 1): await page.mouse.move(p0[0] + (p1[0] - p0[0]) * i / steps, p0[1] + (p1[1] - p0[1]) * i / steps); await page.wait_for_timeout(wait)
    await page.mouse.up(); await page.wait_for_timeout(after)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--autoplay-policy=no-user-gesture-required'])
        # --- desktop, mouse ---
        ctx = await b.new_context(viewport={'width': 1280, 'height': 800}); page = await ctx.new_page(); await routes(page); errs = []
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT)
        await page.goto('http://localhost:8765/busy'); await page.wait_for_function("mode === 'mouse' && gameMode === 'busy'", timeout=10000)
        await page.mouse.click(5, 790); await page.wait_for_timeout(200)  # a user gesture: the AudioContext starts
        g = await page.evaluate(GJ)
        check('desktop: a guitar on the board, laid flat, spanning 6 cells x 2 rows', g['kind'] == 'guitar' and g['o'] == 'h' and abs(g['w'] - 6 * g['h'] / 2) < 1, g)
        check('desktop: whole board still fits (no scroll), inside the board, no widget overlaps', await page.evaluate("__grasp.busy.maxScroll") == 0 and await page.evaluate(INSIDE) and await page.evaluate(OVERLAP))
        parts = await page.evaluate(PARTS)
        check('desktop: amp, pedal, chord buttons, whammy and strings inside the guitar cell, apart from each other; buttons big', parts['inside'] and parts['apart'] and parts['btnR'] >= 22, parts)
        await page.wait_for_function("audio && audio.state === 'running'", timeout=5000)
        made0 = await page.evaluate("__grasp.gtr.made")
        # down-strum: six notes, low E to high E, in order
        await strum_mouse(page, True, after=0)
        fx = await page.evaluate("({ w: [3, 4, 5].map(i => " + G + ".wobble(i, performance.now())), level: " + G + ".state.level })")
        log = await page.evaluate(LOG); defn = await page.evaluate("__grasp.gtr.def.f")
        check('down-strum plays all 6 strings in order (low to high), dir +1, the default E5 chord', [e['i'] for e in log] == [0, 1, 2, 3, 4, 5] and all(e['dir'] == 1 for e in log) and notes_of(log) == [round(f, 2) for f in defn], log)
        check('the notes are heard (6 voices made) and counted in the board sounds', await page.evaluate("__grasp.gtr.made") - made0 == 6 and all(e['heard'] for e in log) and await page.evaluate("__grasp.busy.sounds.guitar") == 6)
        check('notes sound in crossing order (scheduled times rise)', all(log[i]['at'] <= log[i + 1]['at'] for i in range(5)), [e['at'] for e in log])
        check('strummed strings wobble visibly', min(fx['w']) > 1, fx)
        check('the amp speaker pulses with the sound', fx['level'] > 0.3, fx)
        await page.wait_for_timeout(1500)
        check('the wobble and the amp pulse decay', await page.evaluate("Math.max(...[0, 1, 2, 3, 4, 5].map(i => " + G + ".wobble(i, performance.now())))") < 0.3 and await page.evaluate(G + ".state.level") < 0.05)
        check('one note per string: at most 6 voices ringing', await page.evaluate("__grasp.gtr.voices") <= 6)
        await page.evaluate(G + ".state.log.length = 0")
        await strum_mouse(page, False)
        log = await page.evaluate(LOG)
        check('up-strum plays all 6 in reverse order, dir -1', [e['i'] for e in log] == [5, 4, 3, 2, 1, 0] and all(e['dir'] == -1 for e in log), log)
        check('a full strum is recorded with its direction', await page.evaluate(G + ".state.lastStrum.dir") == -1 and await page.evaluate(G + ".state.strums") == 2)
        # tap = pluck one string
        await page.evaluate(G + ".state.log.length = 0"); await page.wait_for_timeout(100)
        q = await page.evaluate(G + ".stringPos(3)"); await page.mouse.click(q['x'], q['y']); await page.wait_for_timeout(150)
        log = await page.evaluate(LOG)
        check('a tap on a string plucks just that string', [e['i'] for e in log] == [3] and log[0]['dir'] == 0 and round(log[0]['f'], 2) == round(defn[3], 2), log)
        # chord buttons
        chords = await page.evaluate("__grasp.gtr.chords")
        for k in range(4):
            await page.evaluate(G + ".state.log.length = 0")
            q = await page.evaluate(G + f".chordPos({k})"); await page.mouse.click(q['x'], q['y']); await page.wait_for_timeout(300)
            log = await page.evaluate(LOG)
            check(f'chord button {chords[k]["id"]} latches its chord and strums it once', await page.evaluate(G + ".state.chord") == k and notes_of(log) == [round(f, 2) for f in chords[k]['f']] and all(e['chord'] == chords[k]['id'] for e in log), log)
        await page.evaluate(G + ".state.log.length = 0"); await page.wait_for_timeout(100)
        await strum_mouse(page, True)
        log = await page.evaluate(LOG)
        check('with Em held a strum plays Em (E2 B2 E3 G3 B3 E4)', notes_of(log) == [82.41, 123.47, 164.81, 196.0, 246.94, 329.63], notes_of(log))
        check('chords differ: G, C, D, Em, default all different', len({tuple(c['f']) for c in chords} | {tuple(defn)}) == 5)
        q = await page.evaluate(G + ".chordPos(3)"); await page.mouse.click(q['x'], q['y']); await page.wait_for_timeout(200)
        check('tapping the held chord again goes back to the default', await page.evaluate(G + ".state.chord") is None and await page.evaluate(G + ".notes()") == defn)
        q = await page.evaluate(G + ".chordPos(1)"); await page.mouse.click(q['x'], q['y']); await page.wait_for_timeout(200)  # C for the screenshot
        # distortion pedal
        pd = await page.evaluate("(() => { const w = " + G + ", g = w.geom(); return w.toScreen(g.pedal.u, g.pedal.v); })()")
        check('clean to begin with: clean path open, crunch closed', await page.evaluate("(() => { const c = __grasp.gtr.chain(); return c && c.clean > 0.95 && c.dist < 0.01 && c.curve && c.verb && c.comp >= 10; })()"), await page.evaluate("__grasp.gtr.chain()"))
        await page.mouse.click(pd['x'], pd['y']); await page.wait_for_timeout(300)
        check('the pedal turns the crunch on: the chain goes through the waveshaper', await page.evaluate(G + ".state.dist") and await page.evaluate("__grasp.gtr.dist") and await page.evaluate("(() => { const c = __grasp.gtr.chain(); return c.clean < 0.05 && c.dist > 0.25; })()") and await page.evaluate("__grasp.busy.sounds.stomp") == 1, await page.evaluate("__grasp.gtr.chain()"))
        check('the pedal reads ROCK! when on', await page.evaluate("[...SPRITES.keys()].some(k => k.startsWith('busy|gtp|') && k.endsWith('|1|ROCK!'))"))
        # no clipping: hard strums with the crunch on stay under full scale (limiter)
        peaks = []
        for _ in range(3):
            await strum_mouse(page, True, steps=4, wait=12); await strum_mouse(page, False, steps=4, wait=12)
            for _ in range(4): peaks.append(await page.evaluate("__grasp.gtr.peak()")); await page.wait_for_timeout(40)
        check('distorted strums are loud but never clip (peak < 0.98)', 0.02 < max(peaks) < 0.98, [round(x, 3) for x in peaks])
        await page.mouse.move(640, 790); await page.wait_for_timeout(50)
        await strum_mouse(page, True)
        await page.screenshot(path='tests/out/guitar_desktop.png')
        await page.mouse.click(pd['x'], pd['y']); await page.wait_for_timeout(300)
        check('the pedal again: back to clean', not await page.evaluate(G + ".state.dist") and await page.evaluate("(() => { const c = __grasp.gtr.chain(); return c.clean > 0.95 && c.dist < 0.01; })()"))
        # whammy: grab the arm and push it toward the strings: the pitch dives; it springs back on release
        await page.wait_for_timeout(1500)
        tip = await page.evaluate(G + ".whammyPos()"); T = g['T']
        await strum_mouse(page, True); await page.wait_for_timeout(50)
        await page.mouse.move(tip['x'], tip['y']); await page.wait_for_timeout(50); await page.mouse.down(); await page.wait_for_timeout(50)
        for i in range(1, 7): await page.mouse.move(tip['x'], tip['y'] - T * 0.2 * i / 6); await page.wait_for_timeout(30)
        await page.wait_for_timeout(120)
        mid = await page.evaluate("({ bend: " + G + ".state.bend, rate: __grasp.gtr.rate, rates: __grasp.gtr.rates(), mode: " + G + ".state.mode })")
        check('pushing the whammy bends the pitch down (all ringing notes follow)', mid['mode'] == 'whammy' and mid['bend'] <= -2.5 and mid['rate'] < 0.88 and mid['rates'] and all(r < 0.9 for r in mid['rates']), mid)
        for i in range(1, 7): await page.mouse.move(tip['x'], tip['y'] - T * 0.2 + T * 0.3 * i / 6); await page.wait_for_timeout(30)
        await page.wait_for_timeout(80)
        up = await page.evaluate("({ bend: " + G + ".state.bend, rate: __grasp.gtr.rate })")
        check('pulling it the other way bends up (capped)', 0.5 < up['bend'] <= 1.5 and up['rate'] > 1.02, up)
        await page.mouse.up(); await page.wait_for_timeout(700)
        check('released: the arm springs back, pitch back to normal', await page.evaluate(G + ".state.bend") == 0 and abs(await page.evaluate("__grasp.gtr.rate") - 1) < 1e-6)
        check('a whammy drag plays no extra strings', all(e['dir'] == 1 for e in (await page.evaluate(LOG))[-6:]))
        # mute: strings still move and count, but no voice is made
        await page.evaluate("__grasp.muted = true"); made1 = await page.evaluate("__grasp.gtr.made"); n1 = await page.evaluate("__grasp.busy.sounds.guitar")
        await strum_mouse(page, True)
        check('muted: a strum shows (wobble, count) but makes no sound', await page.evaluate("__grasp.gtr.made") == made1 and await page.evaluate("__grasp.gtr.voices") == 0 and await page.evaluate("__grasp.busy.sounds.guitar") == n1 + 6 and not any(e['heard'] for e in (await page.evaluate(LOG))[-6:]))
        await page.evaluate("__grasp.muted = false"); await strum_mouse(page, True)
        check('unmuted: sound again', await page.evaluate("__grasp.gtr.made") == made1 + 6)
        # amp poke strums; mouse hover sweep (open hand) strums too
        A = await page.evaluate("(() => { const w = " + G + ", g = w.geom(); return w.toScreen(g.amp.u, g.amp.v); })()")
        n2 = await page.evaluate("__grasp.busy.sounds.guitar"); await page.mouse.click(A['x'], A['y']); await page.wait_for_timeout(300)
        check('poking the amp strums the chord', await page.evaluate("__grasp.busy.sounds.guitar") == n2 + 6)
        await menu_click(page, '#resetBtn'); await page.wait_for_timeout(300)
        check('reset: default chord, clean, no bend, guitar still there and fits', await page.evaluate(G + ".kind === 'guitar' && " + G + ".state.chord === null && !" + G + ".state.dist && !__grasp.gtr.dist") and await page.evaluate(OVERLAP) and await page.evaluate("__grasp.busy.maxScroll") == 0)
        check('desktop: no page errors', not errs, errs); await ctx.close()

        # --- camera stub: pointing finger strums across, an open-hand swipe strums ---
        ctx = await b.new_context(permissions=['camera'], viewport={'width': 1280, 'height': 800}); page = await ctx.new_page(); await routes(page); errs = []
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + HAND_JS + POINT_JS + ARC_JS + LINE_JS)
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
        await page.click('#camBtn'); await page.click('.modes button[data-mode=busy]')
        await page.wait_for_function("mode === 'camera'", timeout=15000)
        g = await page.evaluate(GJ); a = await page.evaluate(G + ".stringPos(0)"); z = await page.evaluate(G + ".stringPos(5)"); ext = g['sp0'] * 1.2
        await page.evaluate(f"jump(pointAt, {a['x']}, {a['y'] - ext})")
        try: await page.wait_for_function("gesture === 'point' && __grasp.busy.active === " + G, timeout=5000)
        except Exception: pass
        await page.wait_for_timeout(300); await page.evaluate(G + ".state.log.length = 0")
        await page.evaluate(f"pointLine({a['x']}, {a['y'] - ext}, {z['x']}, {z['y'] + ext}, 500)")
        try: await page.wait_for_function(G + ".state.log.length >= 6", timeout=4000)
        except Exception: pass
        log = await page.evaluate(LOG)
        check('camera: a pointing finger moved across the strings strums them in order', [e['i'] for e in log][:6] == [0, 1, 2, 3, 4, 5] and all(e['dir'] == 1 for e in log[:6]), [await page.evaluate("gesture"), log])
        await page.evaluate(f"jump((x, y) => handAt(x, y, 0.8), {z['x']}, {z['y'] + ext * 2})"); await page.wait_for_timeout(1000)
        await page.evaluate(G + ".state.log.length = 0")
        await page.evaluate(f"openLine({z['x']}, {z['y'] + ext * 2}, {a['x']}, {a['y'] - ext * 2}, 220)")
        try: await page.wait_for_function(G + ".state.log.length >= 3", timeout=3000)
        except Exception: pass
        log = await page.evaluate(LOG)
        ii = [e['i'] for e in log]
        check('camera: a fast open-hand swipe up strums (several strings, high to low)', len(log) >= 3 and ii == sorted(ii, reverse=True) and all(e['dir'] == -1 for e in log), [await page.evaluate("gesture"), log])
        check('camera: no page errors', not errs, errs); await ctx.close()

        # --- phone portrait, touch, EN + HE ---
        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx = await b.new_context(viewport={'width': 360, 'height': 740}, device_scale_factor=3, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs = []
            page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + TOUCH_JS)
            await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
            if he: await page.tap('#startLang'); await page.wait_for_timeout(100)
            await page.tap('.modes button[data-mode=busy]'); await page.evaluate(START_MOUSE); await page.wait_for_timeout(500)
            g = await page.evaluate(GJ)
            check(tag + ' phone: the guitar stands up, 2 columns x 3 rows', g['o'] == 'v' and abs(g['h'] - 1.5 * g['w']) < 1 and await page.evaluate(COLS(2)), g)
            check(tag + ' phone: no widget overlaps, all inside the board horizontally', await page.evaluate(OVERLAP) and await page.evaluate(VISIBLE(8)))
            # scroll so the guitar is fully on screen (under the top row)
            await page.evaluate("(() => { const w = " + G + "; busy.scroll = Math.max(0, Math.min(busy.maxScroll, w.by - w.h / 2 - busy.top - 6)); applyBusyScroll(); })()"); await page.wait_for_timeout(200)
            g = await page.evaluate(GJ); parts = await page.evaluate(PARTS)
            check(tag + ' phone: scrolled, the whole guitar is on screen below the top buttons', g['y'] - g['h'] / 2 >= await page.evaluate("busy.top") - 1 and g['y'] + g['h'] / 2 <= 740, g)
            check(tag + ' phone: amp, pedal, chord buttons, whammy and strings inside the guitar cell, apart', parts['inside'] and parts['apart'] and parts['btnR'] >= 17, parts)
            await page.tap('#stage', position={'x': 3, 'y': 735}); await page.wait_for_timeout(100)
            a = await page.evaluate(G + ".stringPos(0)"); z = await page.evaluate(G + ".stringPos(5)"); ext = g['sp0'] * 0.9
            await page.evaluate(G + ".state.log.length = 0")
            await page.evaluate(f"touchDrag({a['x'] - ext}, {a['y']}, {z['x'] + ext}, {z['y']}, 10, 20)"); await page.wait_for_timeout(200)
            log = await page.evaluate(LOG)
            check(tag + ' phone: a finger swipe left to right strums down, 6 strings in order', [e['i'] for e in log] == [0, 1, 2, 3, 4, 5] and all(e['dir'] == 1 for e in log), log)
            await page.evaluate(G + ".state.log.length = 0")
            await page.evaluate(f"touchDrag({z['x'] + ext}, {z['y']}, {a['x'] - ext}, {a['y']}, 10, 20)"); await page.wait_for_timeout(200)
            log = await page.evaluate(LOG)
            check(tag + ' phone: right to left strums up', [e['i'] for e in log] == [5, 4, 3, 2, 1, 0] and all(e['dir'] == -1 for e in log), log)
            check(tag + ' phone: strumming did not scroll the board', abs(await page.evaluate(G + ".y") - g['y']) < 0.5)
            await page.evaluate(G + ".state.log.length = 0"); await page.wait_for_timeout(100)
            q = await page.evaluate(G + ".stringPos(2)"); await page.tap('#stage', position={'x': q['x'], 'y': q['y']}); await page.wait_for_timeout(150)
            check(tag + ' phone: a tap plucks one string', [e['i'] for e in await page.evaluate(LOG)] == [2])
            q = await page.evaluate(G + ".chordPos(0)"); await page.tap('#stage', position={'x': q['x'], 'y': q['y']}); await page.wait_for_timeout(200)
            check(tag + ' phone: tapping G selects it', await page.evaluate(G + ".state.chord") == 0)
            pd = await page.evaluate("(() => { const w = " + G + ", g = w.geom(); return w.toScreen(g.pedal.u, g.pedal.v); })()")
            await page.tap('#stage', position={'x': pd['x'], 'y': pd['y']}); await page.wait_for_timeout(200)
            label = 'רוק!' if he else 'ROCK!'
            check(tag + ' phone: tapping the pedal turns on the crunch, labelled ' + label, await page.evaluate(G + ".state.dist") and await page.evaluate("[...SPRITES.keys()].some(k => k.startsWith('busy|gtp|') && k.endsWith('|1|" + label + "'))"))
            await page.evaluate(f"touchDrag({a['x'] - ext}, {a['y']}, {z['x'] + ext}, {z['y']}, 8, 18)"); await page.wait_for_timeout(60)
            await page.screenshot(path='tests/out/guitar_phone' + ('_he' if he else '') + '.png')
            check(tag + ' phone: no page errors', not errs, errs); await ctx.close()

        # --- other screens: the board re-flows without overlaps ---
        for vw, vh, mob in ((740, 360, True), (820, 1180, True), (1024, 768, False), (1920, 1080, False)):
            ctx = await b.new_context(viewport={'width': vw, 'height': vh}, is_mobile=mob, has_touch=mob); page = await ctx.new_page(); await routes(page)
            await page.add_init_script(INIT); await page.goto('http://localhost:8765/busy'); await page.wait_for_function("mode === 'mouse' && gameMode === 'busy'", timeout=10000); await page.wait_for_timeout(300)
            ok = await page.evaluate(OVERLAP) and await page.evaluate("(() => { const b = __grasp.busy.board; return " + W + ".every(w => w.x - w.w / 2 >= b.x - 0.5 && w.x + w.w / 2 <= b.x + b.w + 0.5); })()") and (await page.evaluate(PARTS))['inside']
            check(f'{vw}x{vh}: board re-flows with the guitar, no overlaps, guitar parts inside', ok, await page.evaluate("[__grasp.busy.maxScroll, " + G + ".w, " + G + ".h]"))
            await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
