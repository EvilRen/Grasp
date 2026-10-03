exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Strike's minimal in-game screen: the toolbar folds into one pause button (top corner); the HUD is one slim row with the hearts and the walls
# pill only (no score, progress line, wall pips, NEXT card, streak chip, perk badges or bottom power bar); the serve prompt stays. The pause
# button (tap, Escape or a camera dwell) freezes the game and opens a small sheet with Resume + the toolbar's own buttons (Restart, Sound,
# Language, Stats, Home); each works; Resume / a tap beside the sheet carries on. Other modes keep the full toolbar. Phone EN / HE, desktop,
# Adventure and Endless. The hit meter: a small power arc pops at the hit point on a hit and fades within ~1 s (2D and 3D). The Adventure clear
# card's stars line and Next / Play again / Map (phone EN / HE). Screenshots: tests/out/hud_min_*.png, tests/out/fix_*.png. State changes are polled (timing-independent).
A = "__grasp.adventure"; S = "__grasp.strike"
FRAMES = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
VIS = """(() => { const vis = el => { const r = el.getBoundingClientRect(), cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden'; };
  return [...document.querySelectorAll('.chrome > *')].filter(vis).map(e => e.id || e.className); })()"""
LAYOUT = """(() => { const u = __grasp.strike.ui, c = document.querySelector('.chrome').getBoundingClientRect(), p = $('pauseBtn').getBoundingClientRect(), pv = preview.getBoundingClientRect();
  return { hud: u.hud, parts: u.hudParts, pill: u.wallsPill, adv: u.advPill, hearts: u.hearts.length, heartsRow: u.heartsRow, next: u.nextCard, prog: u.progBar, pips: u.advPips || null, streak: u.streakBox, perks: u.perkIcons.length,
    serve: u.serve, waiting: __grasp.strike.waiting, chrome: { l: c.left, r: c.right, t: c.top, b: c.bottom }, btn: { l: p.left, r: p.right, t: p.top, b: p.bottom, w: p.width, h: p.height },
    prev: preview.hidden ? null : { r: pv.right, b: pv.bottom }, W: innerWidth, H: innerHeight, dir: document.documentElement.dir, min: document.body.classList.contains('minChrome') }; })()"""
SHEET = """(() => { const c = document.querySelector('.chrome'), r = c.getBoundingClientRect(), vis = el => { const q = el.getBoundingClientRect(); return q.width > 0 && q.height > 0 && getComputedStyle(el).display !== 'none'; };
  const btns = [...c.querySelectorAll('button')].filter(vis).sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top);
  return { open: c.classList.contains('open') && menu.open, veil: !$('menuVeil').hidden, paused: pause.on, ids: btns.map(b => b.id || (b.classList.contains('langBtn') ? 'lang' : '?')),
    labels: btns.map(b => (b.querySelector('.lb') || {}).textContent || ''), minH: Math.min(...btns.map(b => b.getBoundingClientRect().height)),
    box: { l: r.left, r: r.right, t: r.top, b: r.bottom }, W: innerWidth, H: innerHeight }; })()"""

SAMPLE = """new Promise(res => { let n = 0, k = 0; const f = () => { if (__grasp.strike.ui.meterPop) n++; if (++k < N) requestAnimationFrame(f); else res(n); }; requestAnimationFrame(f); })"""
POP = """(() => { const u = __grasp.strike.ui, p = u.meterPop, F = u.tierFlash, z = METER_ZONES.find(q => q[2] === p.tier), an = Math.PI * 0.75 + Math.min(p.fill, p.val) * 0.5 * Math.PI * 1.5;
  return { pop: p, zone: [z[0], z[1]], d: Math.hypot(p.x - F.x, p.y - F.y), px: __grasp.strike.pixel(p.x + Math.cos(an) * p.r, p.y + Math.sin(an) * p.r) }; })()"""

async def fresh(b, mobile=False, he=False, init=''):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(permissions=['camera'], **opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + "localStorage.setItem('lang','" + ('he' if he else 'en') + "');" + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(700)
    return ctx, page, errs

async def press(page, mobile, sel):
    if mobile: await page.tap(sel)
    else: await page.click(sel)

def layout_ok(L):
    h, bt = L['hud'], L['btn']
    return (h is not None and h['h'] <= 32 and h['y'] < bt['b'] and h['y'] + h['h'] > bt['t']  # one slim row, on the pause button's row
            and h['x'] + h['w'] <= L['chrome']['l'] - 4 and h['x'] >= (L['prev']['r'] + 4 if L['prev'] else 0) and h['x'] + h['w'] <= L['W'])  # clear of the button and the camera preview

async def adventure_stage(page, mobile):
    await press(page, mobile, '.modes button[data-mode=strike]'); await page.wait_for_function(A + ".mapOpen", timeout=8000)
    await press(page, mobile, '#advPath .anode[data-n="1"]')
    await page.wait_for_function(f"{A}.on && {A}.stage === 1 && mode === 'mouse' && {S}.walls.length === 4 && {S}.ui.hud && {S}.ui.serve", timeout=10000)
    await page.wait_for_function(f"!{S}.ui.levelBanner", timeout=6000)  # (the 'Stage 1' banner slides away)
    await page.evaluate(FRAMES)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ---- phone, EN and HE: an Adventure stage at its start: pause button + hearts + walls pill + the serve prompt; nothing else ----
        for he in (False, True):
            tag = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, mobile=True, he=he, init="localStorage.setItem('inputPref','mouse');")
            await adventure_stage(page, True)
            L = await page.evaluate(LAYOUT); vis = await page.evaluate(VIS)
            check(tag + ' phone: in Strike the toolbar is one round pause button (no home / language / stats / sound / restart icons)', vis == ['pauseBtn'] and L['min'] and L['btn']['w'] >= 40 and abs(L['btn']['w'] - L['btn']['h']) < 1, vis)
            check(tag + ' phone: the pause button sits in the top corner, inside the screen', L['btn']['r'] <= L['W'] - 4 and L['btn']['r'] >= L['W'] - 24 and L['btn']['t'] >= 4 and L['btn']['b'] <= 70, L['btn'])
            check(tag + ' phone: the HUD is one slim row (hearts + walls pill) on the button\'s row, clear of it', L['parts'] == ['hearts', 'walls'] and L['hearts'] == 3 and layout_ok(L), L)
            check(tag + ' phone: the walls pill reads "0/4" (Adventure stage 1)', L['pill'] and L['pill']['text'].endswith('0/4') and L['adv'] and L['adv']['text'] == L['pill']['text'], L['pill'])
            check(tag + ' phone: no NEXT card, progress line, wall pips, streak chip or perk badges', L['next'] is None and L['prog'] is None and L['pips'] is None and L['streak'] is None and L['perks'] == 0, L)
            check(tag + ' phone: the serve prompt ("Hit to start!" + ring) still shows', L['waiting'] and L['serve'] and L['serve']['ty'] > L['hud']['y'] + L['hud']['h'], L['serve'])
            hc = L['heartsRow']['x'] + L['heartsRow']['w'] / 2; pc = L['pill']['x'] + L['pill']['w'] / 2
            check(tag + ' phone: mirrored in Hebrew (hearts at the start side, the pill at the end side)', (pc < hc) if he else (pc > hc), [hc, pc, L['dir']])
            await page.screenshot(path=f'tests/out/hud_min_{tag.lower()}.png')
            # the sheet: tap the pause button
            await press(page, True, '#pauseBtn'); await page.wait_for_function("menu.open && pause.on", timeout=4000); await page.evaluate(FRAMES)
            sh = await page.evaluate(SHEET)
            check(tag + ' phone: the pause sheet opens over a veil, paused: Resume, Restart, Sound, Language, Stats, Home (labelled, tall rows)', sh['open'] and sh['veil'] and sh['paused'] and sh['ids'] == ['resumeBtn', 'resetBtn', 'muteBtn', 'lang', 'hudBtn', 'homeBtn'] and all(sh['labels']) and sh['minH'] >= 44, sh)
            check(tag + ' phone: the sheet fits on screen', sh['box']['l'] >= 0 and sh['box']['r'] <= sh['W'] and sh['box']['b'] <= sh['H'], sh['box'])
            want = ['המשך', 'מההתחלה'] if he else ['Resume', 'Restart']
            check(tag + ' phone: sheet labels in the page language', sh['labels'][:2] == want, sh['labels'])
            await page.screenshot(path=f'tests/out/hud_min_sheet_{tag.lower()}.png')
            await press(page, True, '#resumeBtn'); await page.wait_for_function("!menu.open && !pause.on", timeout=4000)
            check(tag + ' phone: Resume closes the sheet and play goes on', await page.evaluate("$('menuVeil').hidden && !document.querySelector('.chrome.open')"))
            check(tag + ' phone: no page errors', not errs, errs); await ctx.close()

        # ---- desktop, Endless: the pause freezes the ball and the clock; each action works; other modes keep the full toolbar ----
        ctx, page, errs = await fresh(b, init="localStorage.setItem('inputPref','mouse');")
        await page.evaluate("__grasp.setPlayerLevel(20)")
        await page.click('.modes button[data-mode=strike]'); await page.click('#advEndless')
        await page.wait_for_function(f"gameMode === 'strike' && mode === 'mouse' && !{A}.on && {S}.ui.hud && {S}.ui.wallsPill", timeout=10000)
        L = await page.evaluate(LAYOUT); vis = await page.evaluate(VIS)
        check('desktop Endless: only the pause button; HUD = hearts + walls toward the next level ("0/goal")', vis == ['pauseBtn'] and L['parts'] == ['hearts', 'walls'] and layout_ok(L) and L['adv'] is None
              and L['pill']['text'].endswith('0/' + str(await page.evaluate(S + '.goal'))), [vis, L])
        check('desktop Endless: the HUD row is centred at the top', abs(L['hud']['x'] + L['hud']['w'] / 2 - 640) < 2, L['hud'])
        await page.evaluate(f"{S}.setLevel && {S}.setLevel(3)"); await page.evaluate(FRAMES)
        L3 = await page.evaluate(LAYOUT)
        check('desktop Endless level 3: still no NEXT card (the telegraph does not draw)', L3['next'] is None and L3['parts'] == ['hearts', 'walls'], L3)
        await page.screenshot(path='tests/out/hud_min_desktop.png')
        # a ball in flight; pause freezes it
        await page.mouse.move(640, 500)
        for _ in range(60):  # (the serve comes after the level banner; a click serves a waiting ball)
            st = await page.evaluate(f"({{ w: {S}.waiting, z: {S}.ball && {S}.ball.z, dir: {S}.ball && {S}.ball.dir }})")
            if not st['w'] and st['z'] and st['z'] > 300: break
            if st['w']: await page.mouse.click(640, 500)
            await page.wait_for_timeout(150)
        await page.click('#pauseBtn'); await page.wait_for_function("menu.open && pause.on", timeout=4000)
        f0 = await page.evaluate(f"({{ z: {S}.ball.z, n: {S}.balls.length, serve: {S}.serveAt - performance.now() }})"); await page.wait_for_timeout(700)
        f1 = await page.evaluate(f"({{ z: {S}.ball.z, n: {S}.balls.length, serve: {S}.serveAt - performance.now(), music: musicWant() }})")
        check('pause sheet: the ball is frozen in flight (and the serve clock waits)', f0['z'] == f1['z'] and f0['n'] == f1['n'] and abs(f0['serve'] - f1['serve']) < 120, [f0, f1])
        await page.mouse.click(640, 600)  # a click on the canvas area (the veil): no serve, no hit; the veil resumes
        await page.wait_for_function("!menu.open && !pause.on", timeout=4000)
        z0 = await page.evaluate(f"{S}.ball && {S}.ball.z"); await page.wait_for_timeout(250); z1 = await page.evaluate(f"{S}.ball && {S}.ball.z")
        check('a click beside the sheet resumes: the ball moves again', z0 is not None and z1 is not None and z0 != z1, [z0, z1])
        # Escape toggles
        await page.keyboard.press('Escape'); await page.wait_for_function("menu.open && pause.on", timeout=4000)
        await page.keyboard.press('Escape'); await page.wait_for_function("!menu.open && !pause.on", timeout=4000)
        check('Escape opens and closes the pause sheet', True)
        # Sound: toggles, the sheet stays open
        await page.click('#pauseBtn'); await page.wait_for_function("menu.open")
        m0 = await page.evaluate("__grasp.muted"); await page.click('#muteBtn'); await page.wait_for_timeout(100)
        m1 = await page.evaluate("({ m: __grasp.muted, open: menu.open, paused: pause.on, lb: $('muteLb').textContent })")
        check('Sound in the sheet: mutes (its label says so), the sheet stays open and paused', m1['m'] != m0 and m1['open'] and m1['paused'] and m1['lb'] == ('Sound off' if m1['m'] else 'Sound on'), m1)
        await page.click('#muteBtn'); await page.wait_for_timeout(100)
        check('Sound again: back to the first state', await page.evaluate("__grasp.muted") == m0)
        # Language: switches, the sheet stays open with translated labels
        await page.click('.chrome .langBtn'); await page.wait_for_timeout(150)
        lg = await page.evaluate("({ dir: document.documentElement.dir, open: menu.open, lb: document.querySelector('#resumeBtn .lb').textContent })")
        check('Language in the sheet: switches to Hebrew (RTL), the sheet stays open, labels translated', lg['dir'] == 'rtl' and lg['open'] and lg['lb'] == 'המשך', lg)
        await page.screenshot(path='tests/out/hud_min_sheet_desktop_he.png')
        await page.click('.chrome .langBtn'); await page.wait_for_timeout(150)
        check('Language again: back to English', await page.evaluate("document.documentElement.dir === 'ltr' && document.querySelector('#resumeBtn .lb').textContent === 'Resume'"))
        # Stats: shows the stats panel and resumes
        await page.click('#hudBtn'); await page.wait_for_function("!menu.open && !pause.on", timeout=4000)
        check('Stats in the sheet: the stats panel shows and play resumes', await page.evaluate("!hudEl.hidden && $('hudBtn').getAttribute('aria-pressed') === 'true'"))
        await page.click('#pauseBtn'); await page.click('#hudBtn'); await page.wait_for_function("!menu.open && hudEl.hidden", timeout=4000)
        # Restart: a fresh round, resumed
        await page.evaluate(f"{S}.score = 120"); await page.click('#pauseBtn'); await page.wait_for_function("menu.open")
        await page.click('#resetBtn'); await page.wait_for_function(f"!menu.open && !pause.on && {S}.score === 0 && !{S}.over", timeout=4000)
        check('Restart in the sheet: a fresh round (score 0, full hearts), the sheet closes, play goes on', await page.evaluate(f"{S}.lives === {S}.maxLives || {S}.lives >= 3"))
        # Home: the start screen
        await page.click('#pauseBtn'); await page.wait_for_function("menu.open"); await page.click('#homeBtn')
        await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=4000)
        check('Home in the sheet: back to the start screen, the sheet gone, nothing paused', await page.evaluate("!menu.open && !pause.on && $('menuVeil').hidden && document.body.classList.contains('home')"))
        # other modes: the full toolbar
        await page.click('.modes button[data-mode=slice]'); await page.wait_for_function("gameMode === 'slice' && mode !== 'none'", timeout=8000); await page.wait_for_timeout(200)
        vis = await page.evaluate(VIS)
        check('other modes (Slice) keep the full 5-icon toolbar, no pause button', vis == ['homeBtn', 'chip langBtn', 'hudBtn', 'muteBtn', 'resetBtn'] and not await page.evaluate("document.body.classList.contains('minChrome')"), vis)
        check('desktop: no page errors', not errs, errs); await ctx.close()

        # ---- camera: a pinch held on the pause button opens the sheet; one held on Resume closes it (then the 3-2-1) ----
        ctx, page, errs = await fresh(b, mobile=True, init=HAND_JS)
        await page.evaluate("window.__handFor = () => handAt(innerWidth * 0.5, innerHeight * 0.5, 0.8)")
        await page.evaluate("__grasp.setPlayerLevel(20)")
        await page.tap('#camBtn'); await page.tap('.modes button[data-mode=strike]'); await page.tap('#advEndless')
        await page.wait_for_function(f"mode === 'camera' && gameMode === 'strike' && {S}.ui.hud && cursor.present", timeout=15000); await page.wait_for_timeout(400)
        L = await page.evaluate(LAYOUT)
        check('camera phone: the HUD row sits between the camera preview and the pause button', L['prev'] is not None and layout_ok(L), L)
        await page.screenshot(path='tests/out/hud_min_camera.png')
        bc = await page.evaluate("(() => { const r = $('pauseBtn').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()")
        await page.evaluate(f"window.__handFor = () => handAt({bc['x']}, {bc['y']}, 0.1)")
        try: await page.wait_for_function("menu.open && pause.on", timeout=6000); ok = True
        except Exception: ok = False
        check('camera: a pinch held on the pause button opens the sheet (a dwell ring fills)', ok, await page.evaluate("({ c: [cursor.x, cursor.y], g: gesture, open: menu.open })"))
        await page.evaluate("window.__handFor = () => handAt(innerWidth * 0.5, innerHeight * 0.7, 0.8)"); await page.wait_for_timeout(300)
        check('camera: while the sheet is open a ring follows the hand', await page.evaluate("!$('menuDwell').hidden && menu.open"))
        rc = await page.evaluate("(() => { const r = $('resumeBtn').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()")
        await page.evaluate(f"window.__handFor = () => handAt({rc['x']}, {rc['y']}, 0.1)")
        try: await page.wait_for_function("!menu.open && pause.resumeT > 0", timeout=6000); ok = True
        except Exception: ok = False
        check('camera: a pinch held on Resume closes the sheet; the 3-2-1 countdown runs', ok, await page.evaluate("({ c: [cursor.x, cursor.y], g: gesture, open: menu.open, r: pause.resumeT })"))
        await page.evaluate("window.__handFor = () => handAt(innerWidth * 0.5, innerHeight * 0.6, 0.8)")
        await page.wait_for_function("!pause.on", timeout=8000)
        check('camera: after the countdown play goes on', True)
        check('camera: no page errors', not errs, errs); await ctx.close()

        # ---- the hit meter: a small power arc pops up at the hit point on a hit (its tier's colour and name), fills to the hit's power, gone within ~1 s; never there otherwise (2D and 3D) ----
        for g3 in (False, True):
            tag = '3D' if g3 else '2D'
            ctx, page, errs = await fresh(b, mobile=True, init="localStorage.setItem('inputPref','mouse');" + ("window.__graspGfx = { pr: 0.12, shadows: false, auto: false };" if g3 else ''))
            await page.evaluate("__grasp.setPlayerLevel(20)")
            await page.tap('.modes button[data-mode=strike]'); await page.tap('#advEndless')
            await page.wait_for_function(f"gameMode === 'strike' && mode === 'mouse' && {S}.ui.hud && {S}.waiting && !{S}.ui.levelBanner" + (f" && {S}.gfx === '3d'" if g3 else ''), timeout=25000)
            idle = await page.evaluate(SAMPLE.replace('N', '30'))
            check(tag + ': before any hit no meter is drawn (30 frames)', idle == 0, idle)
            await page.evaluate("playerServe('hard')")
            await page.wait_for_function(f"{S}.ui.meterPop && performance.now() - {S}.ui.tierFlash.t > 300 && performance.now() - {S}.ui.tierFlash.t < 650", timeout=4000, polling=20)
            mp = await page.evaluate(POP)
            z = mp['zone']
            check(tag + ': a hard serve pops the arc: tier "hard", labelled "Hard", filled inside the hard zone, fully shown', mp['pop']['tier'] == 'hard' and mp['pop']['label'] == 'Hard' and z[0] < mp['pop']['val'] <= z[1] and abs(mp['pop']['fill'] - mp['pop']['val']) < 0.03 and mp['pop']['a'] > 0.95, mp)
            check(tag + ': the arc sits at the hit point (the ball), small, inside the screen', mp['d'] < 50 and mp['pop']['r'] <= 40 and mp['pop']['box']['x'] >= 0 and mp['pop']['box']['x'] + mp['pop']['box']['w'] <= 360 and mp['pop']['box']['y'] > 60, mp)
            px = mp['px']
            check(tag + ': its fill is drawn in the hard tier\'s saffron', px[0] > 190 and px[1] > 130 and px[2] < 130, px)
            await page.evaluate("hideHint(); __grasp.strike.ui.tierFlash.t = performance.now() - 350"); await page.evaluate(FRAMES)  # (the first-play tip toast out of the picture)
            await page.screenshot(path=f'tests/out/fix_meter_pop{"_3d" if g3 else ""}.png')
            await page.wait_for_function(f"performance.now() - {S}.ui.tierFlash.t > 1200", timeout=4000)
            gone = await page.evaluate(SAMPLE.replace('N', '20'))
            check(tag + ': gone ~1.2 s after the hit (20 frames, none drawn)', gone == 0, gone)
            for tier, lb in (('soft', 'Soft'), ('super', 'SUPER!')):
                await page.evaluate(f"playerServe('{tier}')")
                await page.wait_for_function(f"{S}.ui.meterPop && {S}.ui.meterPop.tier === '{tier}'", timeout=3000, polling=20)
                q = await page.evaluate(POP)
                check(tag + f': a {tier} hit: the arc shows "{lb}" in its zone', q['pop']['label'] == lb and q['zone'][0] < q['pop']['val'] <= q['zone'][1], q)
            check(tag + ' meter: no page errors', not errs, errs); await ctx.close()

        # ---- the Adventure clear card with 2 stars, phone EN / HE: the stars line, Next / Play again / Map ----
        for he in (False, True):
            tag = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, mobile=True, he=he, init="localStorage.setItem('inputPref','mouse');")
            await adventure_stage(page, True)
            await page.evaluate(A + ".finishTest(1)")
            await page.wait_for_function(f"{S}.over && {A}.phase === 'card' && {S}.ui.advStarHint && {S}.ui.advStarHint.a >= 1 && {S}.ui.advStars.shown === 2", timeout=10000)
            await page.wait_for_timeout(300)
            c = await page.evaluate(f"({{ h: {S}.ui.advStarHint, lb: {S}.ui.advLabels, card: {S}.ui.card, W: innerWidth, want: t('starsLost1') }})")
            hw = c['h']
            check(tag + ' phone: 2 stars, the line under them: "' + c['want'] + '"', hw['text'] == c['want'] and (hw['text'].startswith('איבדתם לב אחד') if he else hw['text'].startswith('Lost 1 heart')) and '★★★' in hw['text'], hw)
            check(tag + ' phone: the line fits inside the card', hw['x'] >= c['card']['x'] + 4 and hw['x'] + hw['w'] <= c['card']['x'] + c['card']['w'] - 4 and c['card']['x'] + c['card']['w'] <= c['W'], [hw, c['card']])
            want = {'next': 'הבא', 'retry': 'לשחק שוב', 'map': 'מפה'} if he else {'next': 'Next', 'retry': 'Play again', 'map': 'Map'}
            check(tag + ' phone: buttons Next / Play again / Map', c['lb'] == want, c['lb'])
            await page.screenshot(path=f'tests/out/fix_clear_2star_{tag.lower()}.png')
            check(tag + ' card: no page errors', not errs, errs); await ctx.close()

        await b.close()
    srv.terminate()
    print('FAILURES:', check.fails); sys.exit(1 if check.fails else 0)

asyncio.run(main())
