exec(open('tests/test_hudmin.py').read().split('async def main')[0])
# Every game uses Strike's corner menu: in Sandbox, Slice, Busy Board and Shapes (as in Strike and Smash) the in-game toolbar is ONE round pause
# button in the top corner (the same corner in EN and HE); a tap, Escape / P or a camera dwell opens the small sheet (Resume, Restart, Sound,
# Language, Stats, Home) over a dimmed veil and freezes the game (Sandbox: the physics; Slice: the fruit and the spawn clock; Shapes: the
# rocking / sliding box, the level clock and the banner timers; Busy Board: the tones stop, nothing animates); Resume carries on; each action
# works; the button never overlaps the mode's own HUD (phone 360x740 EN / HE, desktop). Screenshots: tests/out/menu_<mode>_{en,he}.png (sheet
# open, phone). State changes are polled (timing-independent).
MODES = ['sandbox', 'slice', 'busy', 'shapes']
BTN = "(() => { const r = $('pauseBtn').getBoundingClientRect(); return { l: r.left, r: r.right, t: r.top, b: r.bottom, w: r.width, h: r.height, W: innerWidth, H: innerHeight }; })()"
# each mode's own top UI (rects in CSS px) that must stay clear of the pause button
HUDR = """(() => { const R = []; const add = (k, r) => { if (r && r.w > 0 && r.h > 0) R.push({ k, x: r.x, y: r.y, w: r.w, h: r.h }); };
  if (coinUi.box) add('coins', coinUi.box);
  const hn = $('hint'); if (hn.classList.contains('show')) { const q = hn.getBoundingClientRect(); add('hint', { x: q.left, y: q.top, w: q.width, h: q.height }); }
  if (gameMode === 'slice') { const y = scoreY(); add('score', { x: W / 2 - 70, y: y - 45, w: 140, h: 75 }); add('hearts', { x: W / 2 - 50, y: y + 20, w: 100, h: 24 }); }
  if (gameMode === 'busy') add('board', busy.board);
  if (gameMode === 'shapes' && shapes.mat) { const S = shapes.S; shapes.shapes.forEach((s, i) => add('shape' + i, { x: s.x - 1.06 * S, y: s.y - 1.06 * S, w: 2.12 * S, h: 2.12 * S })); } // (no level title any more; the mat itself reaches up beside the button, its shapes keep clear)
  return R; })()"""
def hits(a, R):
    return [r['k'] for r in R if r['x'] < a['r'] and r['x'] + r['w'] > a['l'] and r['y'] < a['b'] and r['y'] + r['h'] > a['t']]

# a frozen-state probe per mode: JSON of what moves while playing
PROBE = {
    'sandbox': "JSON.stringify(bodies.map(b => [Math.round(b.position.x * 10), Math.round(b.position.y * 10)]))",
    'slice': "JSON.stringify({ f: __grasp.slice.fruits.map(f => [Math.round(f.x), Math.round(f.y)]), n: Math.round((__grasp.slice.nextSpawn - performance.now()) / 150) })",
    'busy': "JSON.stringify({ a: __grasp.busy.widgets.find(w => w.kind === 'spinner').state.ang.toFixed(3) })",
    'shapes': "JSON.stringify({ a: shapes.boxAng.toFixed(4), s: shapes.slide.toFixed(2), c: Math.round(shapes.clock), l: Math.round((performance.now() - shapes.levelStart) / 150) })",
}
# make something move in each mode
MOVE = {
    'sandbox': "engine.gravity.y = 0; for (const b of bodies) { M.Body.setVelocity(b, { x: (Math.random() - 0.5) * 12, y: (Math.random() - 0.5) * 12 }); }",
    'slice': "(() => { const s = __grasp.slice; __grasp.CONFIG.SLICE_GRAVITY = 0; s.fruits.length = 0; s.nextSpawn = performance.now() + 60000; s.fruits.push({ x: 100, y: 500, vx: 0.08, vy: -0.05, r: 30, rot: 0, vr: 0.001, kind: FRUITS[0], bomb: false, born: 0 }); })()",
    'busy': "(() => { const w = __grasp.busy.widgets.find(w => w.kind === 'spinner'); w.state.vel = 0.02; })()",
    'shapes': "__grasp.shapes.setLevel(9)",
}
async def start_mode(page, m, mobile):
    await press(page, mobile, f'.modes button[data-mode={m}]')
    await page.wait_for_function(f"mode === 'mouse' && gameMode === '{m}' && $('start').hidden", timeout=8000)
    if m == 'shapes': await page.wait_for_function("shapes.mat && shapes.box", timeout=5000)
    await page.evaluate(FRAMES)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ---- layout: phone EN / HE and desktop: only the pause button, in Strike's corner, clear of each mode's HUD; the sheet (screenshots) ----
        for mobile, he in ((True, False), (True, True), (False, False), (False, True)):
            tag = ('phone ' if mobile else 'desktop ') + ('HE' if he else 'EN')
            ctx, page, errs = await fresh(b, mobile=mobile, he=he)
            for m in MODES:
                await start_mode(page, m, mobile)
                vis = await page.evaluate(VIS); bt = await page.evaluate(BTN)
                check(f'{tag} {m}: the toolbar is one round pause button (no home / language / stats / sound / restart icons)', vis == ['pauseBtn'] and await page.evaluate("document.body.classList.contains('minChrome')") and bt['w'] >= 40 and abs(bt['w'] - bt['h']) < 1, vis)
                check(f'{tag} {m}: the button sits in the top-right corner (as in Strike, also in Hebrew)', bt['W'] - 24 <= bt['r'] <= bt['W'] - 4 and 4 <= bt['t'] and bt['b'] <= 70, bt)
                # the HUD, polled over a few frames (the hint toast and the coin pill appear in the first frames)
                bad = []
                for _ in range(4):
                    R = await page.evaluate(HUDR); bad += hits(bt, R); await page.wait_for_timeout(120)
                check(f'{tag} {m}: the mode\'s own HUD stays clear of the button', not bad, [bad, bt, R])
                if m == 'busy': check(f'{tag} busy: the board starts under the button', await page.evaluate("busy.board.y") >= bt['b'], [await page.evaluate("busy.board"), bt])
                await press(page, mobile, '#pauseBtn'); await page.wait_for_function("menu.open && pause.on", timeout=4000); await page.evaluate(FRAMES)
                sh = await page.evaluate(SHEET)
                check(f'{tag} {m}: the sheet opens over a veil, paused: Resume, Restart, Sound, Language, Stats, Home', sh['open'] and sh['veil'] and sh['paused'] and sh['ids'] == ['resumeBtn', 'resetBtn', 'muteBtn', 'lang', 'hudBtn', 'homeBtn'] and all(sh['labels']) and sh['minH'] >= 44, sh)
                check(f'{tag} {m}: the sheet fits on screen, labels in the page language', sh['box']['l'] >= 0 and sh['box']['r'] <= sh['W'] and sh['box']['b'] <= sh['H'] and sh['labels'][0] == ('המשך' if he else 'Resume'), sh)
                if mobile: await page.screenshot(path=f"tests/out/menu_{m}_{'he' if he else 'en'}.png")
                await press(page, mobile, '#resumeBtn'); await page.wait_for_function("!menu.open && !pause.on", timeout=4000)
                await menu_click(page, '#homeBtn', tap=mobile); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=5000)
                check(f'{tag} {m}: Home from the sheet goes to the start screen (no toolbar there)', await page.evaluate("!menu.open && !pause.on && document.body.classList.contains('home') && getComputedStyle(document.querySelector('.chrome')).display === 'none'"))
            check(f'{tag}: no page errors', not errs, errs); await ctx.close()

        # ---- desktop: per mode the sheet freezes the game, Resume carries on; Escape / P toggle; Restart, Sound, Language, Stats work ----
        ctx, page, errs = await fresh(b)
        for m in MODES:
            await start_mode(page, m, False)
            await page.evaluate(MOVE[m]); await page.wait_for_timeout(250)
            a0 = await page.evaluate(PROBE[m]); await page.wait_for_timeout(300); a1 = await page.evaluate(PROBE[m])
            check(f'{m}: moving before the pause (the probe changes)', a0 != a1, [a0, a1])
            if m == 'busy':
                await page.evaluate("(() => { const w = __grasp.busy.widgets.find(w => w.kind === 'slider'); w.grab({ x: w.x, y: w.y }); })()")
                check('busy: a grabbed slider sings', await page.evaluate("__grasp.busy.tone.active"))
            await page.click('#pauseBtn'); await page.wait_for_function("menu.open && pause.on", timeout=4000); await page.evaluate(FRAMES)
            f0 = await page.evaluate(PROBE[m]); await page.wait_for_timeout(600); f1 = await page.evaluate(PROBE[m])
            check(f'{m}: the sheet freezes the game (and its clocks)', f0 == f1, [f0, f1])
            if m == 'busy': check('busy: the sheet silences the board (the slider tone, the guitar)', await page.evaluate("!__grasp.busy.tone.active && __grasp.gtr.voices === 0"))
            await page.click('#resumeBtn'); await page.wait_for_function("!menu.open && !pause.on", timeout=4000)
            r0 = await page.evaluate(PROBE[m]); await page.wait_for_timeout(400); r1 = await page.evaluate(PROBE[m])
            check(f'{m}: Resume: it moves again', r0 != r1, [r0, r1])
            await page.keyboard.press('Escape'); await page.wait_for_function("menu.open && pause.on", timeout=4000)
            await page.keyboard.press('Escape'); await page.wait_for_function("!menu.open && !pause.on", timeout=4000)
            await page.keyboard.press('p'); await page.wait_for_function("menu.open && pause.on", timeout=4000)
            await page.keyboard.press('P'); await page.wait_for_function("!menu.open && !pause.on", timeout=4000)
            check(f'{m}: Escape and P open and close the sheet', True)
            await page.click('#pauseBtn'); await page.wait_for_function("menu.open")
            await page.mouse.click(640, 700); await page.wait_for_function("!menu.open && !pause.on", timeout=4000)
            check(f'{m}: a click beside the sheet resumes', True)
            # Sound: toggles, the sheet stays open; Language: switches (RTL), the sheet stays open, labels translated
            await page.click('#pauseBtn'); await page.wait_for_function("menu.open")
            m0 = await page.evaluate("__grasp.muted"); await page.click('#muteBtn'); await page.wait_for_timeout(100)
            s1 = await page.evaluate("({ m: __grasp.muted, open: menu.open, paused: pause.on })")
            check(f'{m}: Sound mutes, the sheet stays open and paused', s1['m'] != m0 and s1['open'] and s1['paused'], s1)
            await page.click('#muteBtn'); await page.wait_for_timeout(100)
            await page.click('.chrome .langBtn'); await page.wait_for_timeout(150)
            lg = await page.evaluate("({ dir: document.documentElement.dir, open: menu.open, lb: document.querySelector('#resumeBtn .lb').textContent })")
            check(f'{m}: Language switches to Hebrew (RTL) inside the open sheet', lg['dir'] == 'rtl' and lg['open'] and lg['lb'] == 'המשך' and await page.evaluate("__grasp.muted") == m0, lg)
            await page.click('.chrome .langBtn'); await page.wait_for_timeout(150)
            check(f'{m}: Language again: English', await page.evaluate("document.documentElement.dir === 'ltr'"))
            # Stats: the panel shows, play goes on; again: hidden
            await page.click('#hudBtn'); await page.wait_for_function("!menu.open && !pause.on && !hudEl.hidden", timeout=4000)
            check(f'{m}: Stats shows the stats panel and resumes', await page.evaluate(f"hudEl.textContent.length > 20"))
            await menu_click(page, '#hudBtn'); await page.wait_for_function("!menu.open && hudEl.hidden", timeout=4000)
            # Restart: the mode's own reset, the sheet closes and play goes on
            prep = {'sandbox': "for (const b of bodies) M.Body.setPosition(b, { x: 640, y: 400 }); 1", 'slice': "__grasp.slice.score = 7; __grasp.slice.lives = 1; 1",
                    'busy': "__grasp.busy.seed", 'shapes': "shapes.mistakes = 3; shapes.level"}[m]
            v0 = await page.evaluate(prep)
            await menu_click(page, '#resetBtn'); await page.wait_for_function("!menu.open && !pause.on", timeout=4000); await page.evaluate(FRAMES)
            done = {'sandbox': "bodies.length === 10 && bodies.filter(b => Math.abs(b.position.x - 640) < 1 && Math.abs(b.position.y - 400) < 1).length < 3",
                    'slice': "__grasp.slice.score === 0 && __grasp.slice.lives === 3 && !__grasp.slice.over",
                    'busy': f"__grasp.busy.seed !== {v0}", 'shapes': f"shapes.mistakes === 0 && shapes.level === {v0}"}[m]
            check(f'{m}: Restart restarts the round, closes the sheet, play goes on', await page.evaluate(done), v0)
            await menu_click(page, '#homeBtn'); await page.wait_for_function("mode === 'none'", timeout=5000)
        # Shapes: Home after something was sorted shows the round-over card first, the sheet closes
        await start_mode(page, 'shapes', False); await page.evaluate("__grasp.shapes.placeTest(0)")
        await menu_click(page, '#homeBtn'); await page.wait_for_function("shapes.over && !menu.open && !pause.on", timeout=4000)
        check('shapes: Home in the sheet after a sort: the round-over card, the sheet gone', await page.evaluate("mode === 'mouse' && $('menuVeil').hidden"))
        await menu_click(page, '#homeBtn'); await page.wait_for_function("mode === 'none'", timeout=5000)
        check('desktop: no page errors', not errs, errs); await ctx.close()

        # ---- camera (phone): a pinch held on the pause button opens the sheet in every mode; one held on Resume closes it (3-2-1) ----
        ctx, page, errs = await fresh(b, mobile=True, init=HAND_JS)
        await page.evaluate("window.__handFor = () => handAt(innerWidth * 0.5, innerHeight * 0.5, 0.8)")
        await page.tap('#camBtn'); await page.tap('.modes button[data-mode=sandbox]')
        await page.wait_for_function("mode === 'camera' && gameMode === 'sandbox' && cursor.present", timeout=15000)
        for m in MODES:
            await page.evaluate(f"__grasp.setGameMode('{m}')"); await page.evaluate("window.__handFor = () => handAt(innerWidth * 0.5, innerHeight * 0.5, 0.8)")
            await page.wait_for_function("cursor.present && !pause.on", timeout=8000); await page.wait_for_timeout(300)
            bt = await page.evaluate(BTN); pv = await page.evaluate("preview.getBoundingClientRect().right")
            check(f'camera {m}: only the pause button, clear of the camera preview', await page.evaluate(VIS) == ['pauseBtn'] and bt['l'] >= pv + 4, [bt, pv])
            await page.evaluate(f"window.__handFor = () => handAt({(bt['l'] + bt['r']) / 2}, {(bt['t'] + bt['b']) / 2}, 0.1)")
            try: await page.wait_for_function("menu.open && pause.on", timeout=6000); ok = True
            except Exception: ok = False
            check(f'camera {m}: a pinch held on the pause button opens the sheet', ok, await page.evaluate("({ c: [cursor.x, cursor.y], g: gesture, open: menu.open })"))
            if m == 'sandbox': check('camera sandbox: the dwell pinch grabbed nothing', await page.evaluate("held === null"))
            await page.evaluate("window.__handFor = () => handAt(innerWidth * 0.5, innerHeight * 0.75, 0.8)"); await page.wait_for_timeout(300)
            rc = await page.evaluate("(() => { const r = $('resumeBtn').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()")
            await page.evaluate(f"window.__handFor = () => handAt({rc['x']}, {rc['y']}, 0.1)")
            try: await page.wait_for_function("!menu.open && pause.resumeT > 0", timeout=6000); ok = True
            except Exception: ok = False
            check(f'camera {m}: a pinch held on Resume closes the sheet; the 3-2-1 runs', ok, await page.evaluate("({ c: [cursor.x, cursor.y], g: gesture, open: menu.open, r: pause.resumeT })"))
            await page.evaluate("window.__handFor = () => handAt(innerWidth * 0.5, innerHeight * 0.6, 0.8)")
            await page.wait_for_function("!pause.on", timeout=8000)
        check('camera: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
    sys.exit(1 if check.fails else 0)

asyncio.run(main()); srv.terminate()
