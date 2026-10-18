exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Phase 1 (ROADMAP "The front door and the first 60 seconds"; panels D / E P1 bugs): every player type gets a win before anything else happens.
#  1  no pop-up before the first finished round; the gift calendar from day 2, only after a round (never on open); the hero plays stage 1 at once
#  2  Adventure stages 1-3 cannot be failed: the bumper sends a missed ball back (a star, never a heart); hearts from stage 4; stars reflect the
#     misses; the 'Skip to stage 4' chip after a 3-star stage 1 / 2; a seeded kid-like bot (the finger follows the ball with a lag, ~60% returns)
#     clears stage 1 in <= 60 s, 10 / 10 runs
#  3  the first serve / Slice / Smash: an animated finger + <= 3 words, spoken once (EN / HE), one instruction at a time
#  4  the cards: Share only on a record or a boss; no Duel on a fail card or stages 1-3; the replay only for a moment >= 50; stage 64: 'The End'
#  5  no technical text anywhere: getUserMedia rejecting with a TypeError (EN / HE) gives "Camera is resting — play with your finger 👆", the details
#     behind More help, no 'Error' / 'TypeError' in the DOM or on the canvas
#  6  the streak flame hidden from the Today panel in the Little ones flow
#  7  the gift calendar's backdrop never passes a tap below and never loses the gift
#  8  a double tap on a card's Home (150 / 300 / 600 ms) never acts on the start screen; Shapes: a double tap picks once
#  9  nothing on the start screen changes the difficulty
#  10 the weekly event's rollover grants what was earned, then 'While you were away' after the next round (not on open)
#  11 the app hidden pauses Strike / Slice / Smash / Catch the Stars (the pause sheet, a 3-2-1 on resume); free modes play on
#  12 the steel daily: no overheat, a medium hit breaks a plate; a casual bot breaks >= 1 wall in 60 s
#  13 the Road's NEW UNLOCKED card waits for the start screen and skips what the Adventure has shown
#  14-16 the sound button on the start screen; the camera prompt's buttons apart; the Hebrew wording
# Screenshots: tests/out/phase1_after_*.png (the before shots, from the commit before phase 1: tests/out/phase1_before_*.png).
A = "__grasp.adventure"; S = "__grasp.strike"; H = "__grasp.home2"; G = "__grasp.gifts"
OUT = 'tests/out/'
OPEN = "[...document.querySelectorAll('.ov, #advMap, #smashMap')].filter(o => !o.hidden).map(o => o.id)"
SPEECH = """window.__spoken = []; (() => { const ss = { speak: (u) => __spoken.push({ text: u.text, lang: u.lang }), cancel() {}, getVoices: () => [{ lang: 'en-US', name: 'E' }, { lang: 'he-IL', name: 'H' }], speaking: false };
  try { Object.defineProperty(window, 'speechSynthesis', { value: ss, configurable: true }); } catch (e) {} window.SpeechSynthesisUtterance = function (t) { this.text = t; }; })();"""
CAM_FAIL = """(() => { const md = navigator.mediaDevices || {}; md.getUserMedia = () => Promise.reject(new TypeError("Cannot read properties of undefined (reading 'getUserMedia')")); try { Object.defineProperty(navigator, 'mediaDevices', { value: md, configurable: true }); } catch (e) {} })();"""
DRAWN = "(() => { window.__drawn = new Set(); for (const f of ['textSprite', 'bigTextSprite']) { const o = window[f]; window[f] = function (txt, ...a) { __drawn.add(String(txt)); return o.call(this, txt, ...a); }; } })()"
HIDE = """(() => { Object.defineProperty(document, 'hidden', { value: true, configurable: true }); Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true });
  document.dispatchEvent(new Event('visibilitychange')); delete document.hidden; delete document.visibilityState; })()"""
# the kid: on a virtual clock (nothing drawn); the finger follows the ball's screen path with a lag; for each approach it decides (seeded) whether it
# gets there: then it catches up onto the ball over the last stretch (a real hit, judged by the game's own reach and speed); else it is still far
KID = """window.kidSim = (o) => {
  o = Object.assign({ seed: 1, maxS: 120, fps: 50, reach: 0.6, lag: 220, react: 800 }, o || {});
  if (!adv.on || adv.phase !== 'play') return null;
  const realNow = performance.now, R = mulberry32(o.seed), t0 = realNow.call(performance), dt = 1000 / o.fps;
  const st = { n: adv.n, t: null, hits: 0, misses: 0, balls: 0, bumps0: strike.bumps || 0, lives0: strike.lives, minLives: strike.lives };
  let vt = t0, w = 0, fx = W / 2, fy = H * 0.7; const path = []; cursor.present = true; cursor.history.length = 0;
  performance.now = () => vt;
  try {
    while (vt - t0 < o.maxS * 1000) {
      vt += dt; if (!adv.on || adv.phase !== 'play' || strike.over) break;
      if (strike.waiting) { if (!w) w = vt + o.react + R() * 600; if (vt >= w) { w = 0; playerServe(R() < 0.7 ? 'medium' : 'soft', vt); } }
      for (const q of strike.balls) if (q.dir < 0) q._kid = undefined;
      const b = strike.balls.filter((q) => q.dir > 0 && !q.wait).sort((p, q) => p.z - q.z)[0];
      if (b) {
        if (b._kid === undefined) { b._kid = R() < o.reach; st.balls++; }
        const sc = ballScreen(b); path.push({ t: vt, x: sc.x, y: sc.y }); while (path.length && vt - path[0].t > o.lag + 400) path.shift();
        const lg = path.find((q) => q.t >= vt - o.lag) || path[0]; let tx = lg.x, ty = lg.y;
        if (b._kid && b.z < CONFIG.STRIKE_HIT_Z * 3) { tx = sc.x + (R() - 0.5) * sc.r * 0.6; ty = sc.y + (R() - 0.5) * sc.r * 0.6; }
        if (!b._kid) { tx = sc.x + (sc.x < W / 2 ? 1 : -1) * Math.max(170, W * 0.45); ty = sc.y + H * 0.12; }
        const k = Math.min(1, dt / 90); fx += (tx - fx) * k + (R() - 0.5) * 3; fy += (ty - fy) * k + (R() - 0.5) * 3;
      }
      cursor.present = true; cursor.x = fx; cursor.y = fy; cursor.history.push({ t: vt, x: fx, y: fy }); while (cursor.history.length > 40) cursor.history.shift();
      const h0 = strike.hits; strikeTick(vt, dt); st.hits += strike.hits - h0; st.minLives = Math.min(st.minLives, strike.lives);
    }
  } finally { performance.now = realNow; }
  st.t = adv.result && adv.result.clear ? Math.round((vt - t0) / 100) / 10 : null; st.misses = (strike.bumps || 0) - st.bumps0; st.lost = adv.lost; st.stars = adv.result ? adv.result.stars : null; st.lives = strike.lives;
  const back = realNow.call(performance) - vt;
  for (const k of ['clearAt', 'cardAt']) if (isFinite(adv[k]) && adv[k]) adv[k] += back;
  for (const k of ['releaseUntil', 'serveAt', 'stopUntil', 'slowUntil', 'overAt', 'camPushAt', 'hotUntil', 'perfectAt', 'hitAt', 'handHit', 'flash', 'superFlash', 'tntAt', 'waitSince', 'beatAt']) if (isFinite(strike[k]) && strike[k] > 0) strike[k] += back;
  if (adv.travel) adv.travel.t += back;
  return st;
};"""
# a casual adult who takes "Steel day: hit them hard" at its word: returns ~85%, soft / medium / hard 15 / 25 / 60 %, on a virtual clock
CASUAL = """window.casualSim = (o) => {
  o = Object.assign({ seed: 1, maxS: 60, fps: 50, ret: 0.85, mix: [0.15, 0.25, 0.6] }, o || {});
  const realNow = performance.now, R = mulberry32(o.seed), t0 = realNow.call(performance), dt = 1000 / o.fps, mix = o.mix;
  const st = { hits: 0, misses: 0, walls0: strike.cleared, oh0: strike.overheats || 0, maxHeat: 0 };
  let vt = t0, w = 0; cursor.present = false; cursor.history.length = 0;
  const tier = () => { const r = R(); return r < mix[0] ? 'soft' : r < mix[0] + mix[1] ? 'medium' : 'hard'; };
  performance.now = () => vt;
  try {
    while (vt - t0 < o.maxS * 1000) {
      vt += dt; if (strike.over) break;
      if (strike.lives < 2) strike.lives = 2;
      if (strike.waiting) { if (!w) w = vt + 700 + R() * 600; if (vt >= w) { w = 0; playerServe(tier(), vt); } }
      const Zn = hitZone();
      for (const bl of strike.balls.slice()) {
        if (bl.dir < 0) { bl._sim = 0; continue; }
        if (bl._sim || bl.z - ballSpeedNow(bl, vt) * dt * 1.5 > Zn.zi) continue; bl._sim = 1;
        if (R() >= o.ret) { st.misses++; continue; }
        const sc = ballScreen(bl); cursor.x = sc.x + (R() - 0.5) * sc.r * 0.8; cursor.y = sc.y + (R() - 0.5) * sc.r * 0.8; strikeHit(bl, vt, tier(), null); st.hits++;
      }
      strikeTick(vt, dt); st.maxHeat = Math.max(st.maxHeat, strike.heat);
    }
  } finally { performance.now = realNow; }
  st.walls = strike.cleared - st.walls0; st.overheats = (strike.overheats || 0) - st.oh0; delete st.walls0; delete st.oh0;
  const back = realNow.call(performance) - vt;
  for (const k of ['releaseUntil', 'serveAt', 'stopUntil', 'slowUntil', 'overAt', 'camPushAt', 'hotUntil', 'perfectAt', 'hitAt', 'handHit', 'flash', 'superFlash', 'tntAt', 'waitSince', 'beatAt']) if (isFinite(strike[k]) && strike[k] > 0) strike[k] += back;
  return st;
};"""

def prof(**kw):  # a stored profile (merged over the defaults by the game), seeded once a context
    d = dict(v=1, coins=0, xp=0); d.update(kw)
    return "if (!sessionStorage.getItem('__seeded')) { localStorage.setItem('grasp.profile', " + json.dumps(json.dumps(d)) + "); sessionStorage.setItem('__seeded', '1'); }"

def stars(n):
    return {str(i): 3 for i in range(1, n + 1)}

async def fresh(b, he=False, init='', w=390, h=844, mobile=True, date='2026-10-02', camera=False):
    opts = dict(viewport={'width': w, 'height': h}, device_scale_factor=2, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': w, 'height': h})
    if camera: opts['permissions'] = ['camera']
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + HAND_JS + "localStorage.setItem('lang','" + ('he' if he else 'en') + "');"
                               + ("if (!sessionStorage.getItem('grasp.testDate')) sessionStorage.setItem('grasp.testDate','" + date + "');" if date else '') + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_function("window.__grasp && __grasp.home2 && document.readyState === 'complete'", timeout=10000)
    await page.wait_for_timeout(400)
    return ctx, page, errs

async def reload(page):
    await page.reload(); await page.wait_for_function("window.__grasp && __grasp.home2 && document.readyState === 'complete'", timeout=10000); await page.wait_for_timeout(500)

async def card_tap(page, E, key):  # a card button: a tap on the canvas at its centre, once the card is armed
    await page.wait_for_function(f"{E}.over && {E}.ui.buttons && {E}.ui.buttons.{key} && performance.now() - {E}.overAt > 900", timeout=15000)
    r = await page.evaluate(f"{E}.ui.buttons.{key}")
    await page.touchscreen.tap(r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)

async def stage_card(page, n, lost=0, score=None):  # stage n played and cleared at once (finishTest); its card up
    await page.evaluate(f"{A}.start({n}, 'mouse')"); await page.wait_for_function(f"adv.on && adv.n === {n} && adv.phase === 'play'", timeout=10000)
    if score is not None: await page.evaluate(f"strike.score = {score}")
    await page.evaluate(f"{A}.finishTest({lost})")
    await page.wait_for_function("strike.over && adv.phase === 'card' && strike.ui.buttons && performance.now() - strike.overAt > 900", timeout=20000)
    await page.wait_for_timeout(300)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ===== 1. the first open: nothing pops up; the hero plays stage 1 at once; the gift calendar from day 2, only after a round =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he=he, init="window.__graspPopups = true; window.__graspGiftAuto = true;")
            await page.wait_for_timeout(1200)
            o = await page.evaluate(OPEN)
            check(tg + ': first open (a real visitor\'s pop-ups on): nothing pops up, the hero says "' + ('שלב 1' if he else 'Stage 1') + '" (menu B: the Strike sticker\'s ribbon)', o == [] and await page.evaluate("$('heroSub').textContent") == ('שלב 1' if he else 'Stage 1') and await page.evaluate("profile.habit.first") == '2026-10-02', o)
            await page.screenshot(path=OUT + 'phase1_after_first_open_%s.png' % ('he' if he else 'en'))
            if he: await ctx.close(); continue
            await page.tap('#heroPlay')
            await page.wait_for_function(f"{A}.on && {A}.stage === 1 && mode === 'mouse' && $('start').hidden && $('advMap').hidden", timeout=10000)
            check('the hero on a fresh profile: Strike stage 1 directly (no map, no sheet)', await page.evaluate(OPEN) == [])
            await page.evaluate(f"{A}.finishTest(0)"); await card_tap(page, 'strike', 'map')
            await page.wait_for_function("!$('advMap').hidden", timeout=8000); await page.wait_for_timeout(600)
            await page.evaluate("$('advBack').click()"); await page.wait_for_timeout(900)
            o = await page.evaluate(OPEN)
            check('day 1, a round finished: no gift calendar (the first day has none)', 'gifts' not in o and await page.evaluate(G + ".shown") is False, o)
            if await page.evaluate("$('bubuBtn').dataset.call === 'hatch'"):  # (navigation v2: the egg earned on stage 1 waits behind Bubu's glow; the child taps it)
                await page.wait_for_timeout(1300); await page.tap('#bubuBtn'); await page.wait_for_function("!$('petRoom').hidden", timeout=4000)
            await page.evaluate("__grasp.home2.closeSheets(); __grasp.setDate('2026-10-03')"); await reload(page)
            await page.wait_for_timeout(600)
            o = await page.evaluate(OPEN)
            check('day 2, on open: still nothing (the calendar never comes on open)', 'gifts' not in o, o)
            await page.evaluate("__grasp.home2.closeSheets()"); await page.wait_for_timeout(200)
            await page.tap('#heroPlay'); await page.wait_for_function(f"{A}.on && adv.phase === 'play'", timeout=10000)
            await page.evaluate(f"{A}.finishTest(0)"); await page.wait_for_function("strike.over && adv.phase === 'card'", timeout=15000)
            await page.evaluate("goHome()"); await page.wait_for_function(G + ".shown", timeout=5000)
            check('day 2, back home after a round: the gift calendar, the session\'s one popup', await page.evaluate(OPEN) == ['gifts'] and await page.evaluate(H + ".h2.popup") == 'gift')
            check('first open: no page errors', not errs, errs); await ctx.close()

        # ===== 2. stages 1-3 cannot be failed: the bumper; hearts from stage 4; the kid bot; the skip chip =====
        ctx, page, errs = await fresh(b, init=KID)
        res = []
        for seed in range(1, 11):
            await page.evaluate("localStorage.removeItem('grasp.profile')"); await reload(page)
            await page.evaluate(f"{A}.start(1, 'mouse')"); await page.wait_for_function("adv.on && adv.phase === 'play'", timeout=8000)
            res.append(await page.evaluate(f"kidSim({{ seed: {seed} }})"))
        hits = sum(r['hits'] for r in res); balls = sum(r['hits'] + r['misses'] for r in res)
        check('the kid bot (lagging finger, ~60% reach, seeded): stage 1 cleared in <= 60 s, 10 / 10 runs: ' + ', '.join(str(r['t']) for r in res),
              all(r['t'] is not None and r['t'] <= 60 for r in res), res)
        check('...and it never lost a heart (the bumper took every miss: %d misses, return rate %.0f%%)' % (sum(r['misses'] for r in res), 100 * hits / max(1, balls)),
              all(r['minLives'] == r['lives0'] for r in res) and sum(r['misses'] for r in res) >= 10 and 0.45 <= hits / max(1, balls) <= 0.85, res)
        check('the stars still count the misses: 0 = 3★, 1 = 2★, more = 1★', all(r['stars'] == (3 if r['lost'] == 0 else 2 if r['lost'] == 1 else 1) for r in res), [(r['lost'], r['stars']) for r in res])
        await ctx.close()
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he=he, w=360, h=740, init=prof(adv={'stars': stars(3), 'unlocked': 5}))
            await page.evaluate(f"{A}.start(1, 'mouse')"); await page.wait_for_function("adv.on && adv.phase === 'play' && strike.waiting && !strike.ui.levelBanner", timeout=12000)
            bn = await page.evaluate("({ row: strike.ui.heartsRow, lives: strike.lives })")
            check(tg + ': stage 1: the HUD shows the stage\'s 3 stars, not hearts', bn['row'].get('stars') == 3, bn)
            await page.evaluate("playerServe('medium')")
            await page.wait_for_function("strike.ui.bumpAt > 0", timeout=20000); await page.wait_for_timeout(90)
            bu = await page.evaluate("({ lives: strike.lives, max: strike.maxLives, lost: adv.lost, bumps: strike.bumps, over: strike.over, phase: adv.phase, out: strike.balls.filter(b => b.dir < 0).length, bumper: strike.ui.bumper, row: strike.ui.heartsRow, floats: strike.floaters.map(f => f.text) })")  # before the screenshot: the flare fades in 650 ms
            if not he: await page.screenshot(path=OUT + 'phase1_after_bumper.png')
            check(tg + ': a miss on stage 1: the bumper flares and sends the ball back, a star dims (3 -> 2), no heart lost, play goes on',
                  bu['lives'] == bu['max'] and bu['lost'] == 1 and bu['bumps'] == 1 and bu['out'] == 1 and not bu['over'] and bu['phase'] == 'play' and bu['bumper'] and bu['bumper']['flare'] > 0 and bu['row'].get('stars') == 2, bu)
            for _ in range(4):
                await page.wait_for_function("strike.waiting || strike.balls.some(b => b.dir > 0)", timeout=20000)
                if await page.evaluate("strike.waiting"): await page.evaluate("playerServe('medium')")
                n0 = await page.evaluate("strike.bumps"); await page.wait_for_function(f"strike.bumps > {n0}", timeout=25000)
            bu = await page.evaluate("({ lives: strike.lives, lost: adv.lost, over: strike.over, row: strike.ui.heartsRow })")
            check(tg + ': five misses in a row on stage 1: never a fail, still every heart, 1 star left on the HUD', not bu['over'] and bu['lives'] == 3 and bu['lost'] == 5 and bu['row'].get('stars') == 1, bu)
            await page.evaluate("goHome()"); await page.wait_for_timeout(300)
            await page.evaluate(f"{A}.start(4, 'mouse')"); await page.wait_for_function("adv.on && adv.n === 4 && adv.phase === 'play' && strike.waiting && !strike.ui.levelBanner", timeout=12000)
            await page.evaluate("playerServe('medium')"); await page.wait_for_function("strike.lives < strike.maxLives", timeout=20000)
            h4 = await page.evaluate("({ lives: strike.lives, max: strike.maxLives, bumps: strike.bumps || 0, row: strike.ui.heartsRow, rule: t('starsRule') })")
            check(tg + ': stage 4: the hearts are back: a miss costs a heart (no bumper)', h4['lives'] == h4['max'] - 1 and h4['bumps'] == 0 and 'stars' not in h4['row'], h4)
            check(tg + ': no page errors (bumper)', not errs, errs); await ctx.close()
        # the card after a 3-star stage 1: 'Skip to stage 4'; not after 2 stars, not on stage 3
        ctx, page, errs = await fresh(b, w=360, h=740)
        await stage_card(page, 1, 0)
        c1 = await page.evaluate("({ b: Object.keys(strike.ui.buttons), skip: strike.ui.skip, hint: strike.ui.advStarHint && strike.ui.advStarHint.text, H: innerHeight })")
        check('a 3-star stage 1 (navigation v2: at most 3 buttons a card, so no "Skip to stage 4" chip): Next / Home / Map; the line says "Perfect — no misses!"', 'skip' not in c1['b'] and not c1['skip'] and c1['b'] == ['next', 'home', 'map'] and c1['hint'] == 'Perfect — no misses!', c1)
        await page.screenshot(path=OUT + 'phase1_after_skip_chip.png')
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        await stage_card(page, 2, 1)
        c2 = await page.evaluate("({ b: Object.keys(strike.ui.buttons), hint: strike.ui.advStarHint.text })")
        check('a 2-star stage 2: no skip chip; the line counts misses, not hearts', 'skip' not in c2['b'] and c2['hint'].startswith('Missed once'), c2)
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        await stage_card(page, 3, 0)
        check('a 3-star stage 3: no skip chip', 'skip' not in await page.evaluate("Object.keys(strike.ui.buttons)"))
        check('skip chip: no page errors', not errs, errs); await ctx.close()

        # ===== 3. show, don't tell: the instruction fingers (serve, Slice, Smash), <= 3 words, spoken once, one instruction at a time =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'; lt = 'he' if he else 'en'
            ctx, page, errs = await fresh(b, he=he, w=360, h=740, init="window.__graspFd = true;" + SPEECH)
            await page.tap('#heroPlay'); await page.wait_for_function("adv.on && strike.waiting && !strike.ui.levelBanner && fd.ui && fd.ui.id === 'serve'", timeout=12000)
            await page.wait_for_timeout(700)
            f = await page.evaluate("({ ui: fd.ui, said: fd.said.slice(), sp: __spoken.map(x => x.text), line: strike.ui.serve.shown, hint: $('hint').classList.contains('show') })")
            check(tg + ': the first serve: a finger on the ball + "' + f['ui']['words'] + '" (<= 3 words), said once, the serve line and toasts held back',
                  len(f['ui']['words'].split()) <= 3 and f['ui']['words'] == await page.evaluate("t('fdServe')") and [x['id'] for x in f['said']] == ['serve'] and f['ui']['words'] in f['sp'] and not f['line'] and not f['hint'], f)
            await page.screenshot(path=OUT + 'phase1_after_finger_serve_%s.png' % lt)
            await page.evaluate("playerServe('medium')"); await page.wait_for_timeout(500)
            check(tg + ': the serve done: the finger goes, "fd_serve" kept (never again on this profile)', await page.evaluate("!fd.on && profile.tips.includes('fd_serve')"))
            await page.evaluate("goHome()"); await page.wait_for_timeout(600)
            await page.tap('#start button[data-mode=slice]'); await page.wait_for_function("gameMode === 'slice' && fd.ui && fd.ui.id === 'slice'", timeout=10000)
            await page.wait_for_timeout(1300)
            f = await page.evaluate("({ ui: fd.ui, said: fd.said.map(x => x.id), hint: $('hint').classList.contains('show') })")
            check(tg + ': Slice\'s first round: a finger swiping + "' + f['ui']['words'] + '", no how-to toast with it', len(f['ui']['words'].split()) <= 3 and f['said'] == ['serve', 'slice'] and not f['hint'], f)
            await page.screenshot(path=OUT + 'phase1_after_finger_slice_%s.png' % lt)
            await page.evaluate("goHome()"); await page.wait_for_timeout(600)
            await page.evaluate("setGameMode('smash'); smashStageStart(1, 'mouse')"); await page.wait_for_function("gameMode === 'smash' && fd.ui && fd.ui.id === 'smash' && !smash.banner", timeout=12000)
            await page.wait_for_timeout(500)
            f = await page.evaluate("({ ui: fd.ui, said: fd.said.map(x => x.id), hint: $('hint').classList.contains('show') })")
            check(tg + ': Smash\'s first stage: after its banner, a finger tapping + "' + f['ui']['words'] + '"', len(f['ui']['words'].split()) <= 3 and f['said'] == ['serve', 'slice', 'smash'] and not f['hint'], f)
            await page.screenshot(path=OUT + 'phase1_after_finger_smash_%s.png' % lt)
            await page.touchscreen.tap(195, 420); await page.wait_for_timeout(500)
            check(tg + ': a tap ends Smash\'s finger', await page.evaluate("!fdActive() && profile.tips.includes('fd_smash')"))
            check(tg + ': fingers: no page errors', not errs, errs); await ctx.close()

        # ===== 4. the cards: Share / Duel / the replay; the ending after stage 64 =====
        ctx, page, errs = await fresh(b, w=360, h=740, init=prof(adv={'stars': stars(7), 'unlocked': 8, 'best': {'2': 10}}))
        await stage_card(page, 1, 1)
        check('a stage 1 clear, no record: no Share', 'share' not in await page.evaluate("Object.keys(strike.ui.buttons)"))
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        await stage_card(page, 2, 0, score=500)
        c = await page.evaluate("({ b: Object.keys(strike.ui.buttons), rec: adv.result.record })")
        check('a stage 2 record: Share', c['rec'] and 'share' in c['b'], c)
        await card_tap(page, 'strike', 'share'); await page.wait_for_function("!$('shareSheet').hidden", timeout=5000)
        check('...its sheet: no Challenge a friend on stages 1-3', await page.evaluate("$('shDuel').hidden"))
        await page.evaluate("__grasp.home2.share.close(); goHome()"); await page.wait_for_timeout(300)
        await page.evaluate(f"{A}.start(5, 'mouse')"); await page.wait_for_function("adv.on && adv.phase === 'play'", timeout=8000)
        await page.evaluate(f"{A}.failTest()"); await page.wait_for_function("strike.over && strike.ui.buttons", timeout=10000); await page.wait_for_timeout(600)
        check('a fail card: Try again, Home, Map only (no Share, no Duel)', sorted(await page.evaluate("Object.keys(strike.ui.buttons)")) == ['home', 'map', 'retry'])
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        await stage_card(page, 8, 0)
        check('a boss clear (stage 8): Share, and Challenge a friend in its sheet', 'share' in await page.evaluate("Object.keys(strike.ui.buttons)") and await page.evaluate("__grasp.home2.share.ctx().duel"))
        rq = await page.evaluate("(() => { const o = { ok: rp.ok, clip: rp.clip }; rp.ok = true; rp.clip = { round: rp.round, score: 30, frames: [] }; const a = __grasp.home2.share.ctx(); rp.clip.score = 60; const b = __grasp.home2.share.ctx(); rp.ok = o.ok; rp.clip = o.clip; return { low: a.replay, high: b.replay }; })()")
        check('the replay in the Share sheet only for a moment worth 50+ (30: no, 60: yes)', not rq['low'] and rq['high'], rq)
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        await page.evaluate("setGameMode('slice'); strikeStart('mouse')"); await page.wait_for_function("gameMode === 'slice' && mode === 'mouse'", timeout=8000)
        await page.evaluate("slice.best = 999; slice.score = 3; slice.lives = 1"); await page.wait_for_function("slice.over && slice.ui.buttons && performance.now() - slice.overAt > 600", timeout=30000)
        check('a Slice round with no new best: no Share', 'share' not in await page.evaluate("Object.keys(slice.ui.buttons)"))
        check('cards: no page errors', not errs, errs); await ctx.close()
        for he in (False, True):
            ctx, page, errs = await fresh(b, he=he, w=360, h=740, init=prof(adv={'stars': stars(63), 'unlocked': 64}))
            await stage_card(page, 64, 0)
            await page.wait_for_timeout(1300)
            e = await page.evaluate("({ title: strike.ui.advTitle, fin: strike.ui.finale, b: Object.keys(strike.ui.buttons), line: strike.ui.againLine, tapNext: t('advTapNext') })")
            check(('HE' if he else 'EN') + ': after stage 64: "' + e['title'] + '" with Map + Home + Share and a finale line; no Next, no "Tap Next for the next stage"',
                  e['title'] == ('הסוף 🎉' if he else 'The End 🎉') and e['fin'] and e['b'] == ['map', 'home', 'share'] and e['line'] != e['tapNext'] and 'next' not in e['b'], e)
            await page.screenshot(path=OUT + 'phase1_after_end64_%s.png' % ('he' if he else 'en'))
            if not he:
                await card_tap(page, 'strike', 'map'); await page.wait_for_function("!$('advMap').hidden", timeout=8000)
                check('...its Map opens the map', True)
            check('ending: no page errors', not errs, errs); await ctx.close()

        # ===== 5. no technical text: the camera fails with a TypeError (EN / HE), the hero and a camera game =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he=he, w=360, h=740, init=CAM_FAIL)
            await page.evaluate(DRAWN); await page.evaluate("setInputPref('camera')")
            await page.tap('#heroPlay'); await page.wait_for_function("!$('banner').hidden && mode === 'mouse'", timeout=25000); await page.wait_for_timeout(1500)
            vis = await page.evaluate("document.body.innerText"); drawn = await page.evaluate("[...__drawn]")
            bn = await page.evaluate("({ title: $('banner').querySelector('strong').textContent, more: $('bannerMore').textContent, list: $('bannerList').hidden, h: $('bannerMore').getBoundingClientRect().height })")
            check(tg + ': getUserMedia rejects with a TypeError: "' + bn['title'] + '" with More help (details hidden)', bn['title'] == ('המצלמה נחה — משחקים עם האצבע 👆' if he else 'Camera is resting — play with your finger 👆') and bn['list'] and bn['h'] >= 44, bn)
            bad = [x for x in drawn if re.search(r'Error|TypeError|undefined', x)]
            check(tg + ': no "Error" / "TypeError" visible: not in the DOM text, not on the canvas', not re.search(r'Error|TypeError|getUserMedia|undefined', vis) and not bad, [vis[:300], bad])
            if he: await page.screenshot(path=OUT + 'phase1_after_nocam_he.png')
            await page.tap('#bannerMore'); await page.wait_for_timeout(250)
            li = await page.evaluate("[...$('bannerList').children].map(l => l.textContent)")
            check(tg + ': More help reveals the details, in plain words (still no technical text)', not await page.evaluate("$('bannerList').hidden") and li and not any(re.search(r'Error|TypeError|undefined|\(', x) for x in li), li)
            await page.evaluate("goHome()"); await page.wait_for_timeout(400)
            await page.evaluate("$('banner').hidden = true; localStorage.removeItem('cgTouchOk'); cgStart('stars')"); await page.wait_for_function("!$('cgCam').hidden", timeout=8000); await page.wait_for_timeout(500)
            await page.click('#cgCamOn'); await page.wait_for_function("!$('banner').hidden", timeout=25000); await page.wait_for_timeout(800)
            vis = await page.evaluate("document.body.innerText"); bad = [x for x in await page.evaluate("[...__drawn]") if re.search(r'Error|TypeError', x)]
            check(tg + ': a camera game\'s "Turn on camera" failing: the same resting card, no technical text', not re.search(r'Error|TypeError|getUserMedia', vis) and not bad, [vis[:200], bad])
            check(tg + ': no page errors (camera fail)', not errs, errs); await ctx.close()

        # ===== 6. the streak flame: quiet; hidden from the Today panel in the Little ones flow =====
        ctx, page, errs = await fresh(b, init=prof(habit={'play': ['2026-09-29', '2026-09-30', '2026-10-01']}))
        await page.evaluate("openPanel('today')"); await page.wait_for_timeout(300)
        a1 = await page.evaluate("!$('todayStreak').hidden")
        await page.evaluate("closePanel('today')"); await page.tap('#littleBtn'); await page.wait_for_timeout(600); await page.tap('#littlePick button[data-mode=busy]')
        await page.wait_for_function("gameMode === 'busy' && mode === 'mouse'", timeout=8000); await page.evaluate("goHome()"); await page.wait_for_timeout(400)
        await page.evaluate("openPanel('today')"); await page.wait_for_timeout(300)
        a2 = await page.evaluate("$('todayStreak').hidden")
        check('the streak: a quiet chip in the Today panel; after a Little ones game (Busy Board) it is hidden', a1 and a2, [a1, a2])
        check('no streak text outside the Today panel on the start screen', not re.search(r'streak|רצף', await page.evaluate("$('start').innerText"), re.I))
        await ctx.close()

        # ===== 7. the gift calendar's backdrop =====
        for where in ('above', 'below'):
            ctx, page, errs = await fresh(b, init="window.__graspPopups = true; window.__graspGiftAuto = true;" + prof(pet={'egg': True, 'eggSeen': True, 'pantry': 1}))
            await page.evaluate("__grasp.setDate('2026-10-03'); h2.rounds = 1; goHome()"); await page.wait_for_function(G + ".shown", timeout=5000); await page.wait_for_timeout(700)
            sh = await page.evaluate("(() => { const q = $('gifts').querySelector('.sheet').getBoundingClientRect(); return [q.top, q.bottom]; })()")
            if where == 'below': await page.evaluate(G + ".claim()"); await page.wait_for_timeout(100)
            c0 = await page.evaluate("profile.coins")
            y = sh[0] - 40 if where == 'above' else sh[1] + 30
            await page.touchscreen.tap(195, y); await page.wait_for_timeout(400)
            g1 = await page.evaluate(f"({{ shown: {G}.shown, coins: profile.coins, opened: giftState().opened, open: {OPEN}, mode }})")
            if where == 'above':
                check('the unopened gift: a tap beside it (above, where the Events banner was) opens it (+5 coins), nothing below gets the tap', g1['opened'] and g1['coins'] == c0 + 5 and g1['open'] == ['gifts'] and g1['mode'] == 'none', g1)
                await page.wait_for_function("!" + G + ".shown", timeout=4000); await page.wait_for_timeout(500)
                check('...then it closes by itself; still nothing else opened (no pet room, no event page)', await page.evaluate(OPEN) == [])
            else:
                await page.wait_for_timeout(500)
                check('the opened gift: a tap below it (where the pet tab is) only closes it: no pet room, nothing else', not g1['shown'] and await page.evaluate(OPEN) == [] and g1['coins'] == c0, g1)
            check('gift backdrop: no page errors', not errs, errs); await ctx.close()

        # ===== 8. input safety: a double tap on a card's Home; Shapes' double tap =====
        for gap in (150, 300, 600):
            ctx, page, errs = await fresh(b, init="window.__graspTapGuard = true;" + prof(pet={'egg': True, 'eggSeen': True, 'pantry': 1}))
            await page.tap('#start button[data-mode=slice]'); await page.wait_for_function("gameMode === 'slice' && mode === 'mouse'", timeout=8000); await page.wait_for_timeout(700)
            await page.evaluate("slice.lives = 1"); await page.wait_for_function("slice.over && slice.ui.buttons && slice.ui.buttons.home && performance.now() - slice.overAt > 900", timeout=30000)
            r = await page.evaluate("slice.ui.buttons.home"); x = r['x'] + r['w'] / 2; y = r['y'] + r['h'] / 2
            await page.touchscreen.tap(x, y); await page.wait_for_timeout(gap); await page.touchscreen.tap(x, y); await page.wait_for_timeout(900)
            st = await page.evaluate(f"({{ start: !$('start').hidden, open: {OPEN}, mode, eaten: tapg.eaten + (__grasp.nav.nav.landEaten || 0), log: tapg.log.slice(-3) }})")  # (navigation v2: the landing guard may be the one that eats it)
            check(f'a double tap on the Slice card\'s Home, {gap} ms apart: the start screen, and the second tap does nothing there', st['start'] and st['open'] == [] and st['mode'] == 'none' and st['eaten'] >= 1, st)
            check('double tap: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, init="window.__graspTapGuard = true;")
        await page.evaluate("document.querySelector('#littlePick [data-mode=shapes]').click()"); await page.wait_for_function("mode === 'mouse' && gameMode === 'shapes' && __grasp.shapes.phase === 'play'", timeout=10000); await page.wait_for_timeout(900)
        s0 = (await page.evaluate("__grasp.shapes.shapes"))[0]
        await page.touchscreen.tap(s0['x'], s0['y']); await page.wait_for_timeout(120); await page.touchscreen.tap(s0['x'], s0['y']); await page.wait_for_timeout(400)
        sl = await page.evaluate("({ sel: __grasp.shapes.sel, log: __grasp.shapes.tapLog.slice(-3).map(q => q.k + ':' + (q.why || '')) })")
        check('Shapes: a double tap on a shape picks it once (not picked and dropped again)', sl['sel'] == 0 and 'deselect:again' not in sl['log'], sl)
        await page.wait_for_timeout(500); await page.touchscreen.tap(s0['x'], s0['y']); await page.wait_for_timeout(300)
        check('...a later, separate tap still drops the pick', await page.evaluate("__grasp.shapes.sel") == -1)
        check('shapes double tap: no page errors', not errs, errs); await ctx.close()

        # ===== 9. nothing on the start screen changes the difficulty =====
        ctx, page, errs = await fresh(b)
        d0 = await page.evaluate("[strike.diff, localStorage.getItem('strikeDiff')]")
        hits = await page.evaluate("(() => { const out = []; for (const b of [...$('start').querySelectorAll('button')].filter(b => b.offsetParent)) { const q = b.getBoundingClientRect(); out.push([b.id || b.dataset.mode || b.className, q.left + q.width / 2, q.bottom - 4]); } return out; })()")
        check('no Easy / Normal switch anywhere on the start screen (it lives on the Adventure map\'s header)', await page.evaluate("!$('start').querySelector('[data-diff], #strikeDiff')"))
        await page.wait_for_timeout(800)  # (menu B: after the stickers' entrance)
        r = await page.evaluate("(() => { const q = document.querySelector('#start button[data-mode=strike]').getBoundingClientRect(); return [q.left + q.width / 2, q.bottom - 9]; })()")  # (menu B: the Map chip is tilted 4 degrees: its bottom edge, inside the chip)
        await page.touchscreen.tap(r[0], r[1]); await page.wait_for_timeout(500)
        check('a tap on the bottom edge of the Strike tile (the hero\'s Map) opens the map, the difficulty unchanged', await page.evaluate("!$('advMap').hidden") and await page.evaluate("[strike.diff, localStorage.getItem('strikeDiff')]") == d0, hits)
        await ctx.close()

        # ===== 10. the weekly event's rollover: granted, then 'While you were away' after the next round =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he=he, date='2026-10-11')
            ev0 = await page.evaluate("(() => { const E = evEnsure('2026-10-11'); E.pts = 319; E.ms[0] = 999; saveProfile(); return { id: evAt('2026-10-11').id, claimable: evClaimable(E), coins: profile.coins, x: JSON.parse(JSON.stringify(profile.evx)) }; })()")
            await page.evaluate("__grasp.setDate('2026-10-12')"); await reload(page)
            a = await page.evaluate(f"({{ open: {OPEN}, away: profile.evAway, coins: profile.coins, x: profile.evx, ev: profile.event.id, wk: profile.event.wk, pts: profile.event.pts }})")
            check(tg + ': Sunday: 6 tiers reached, nothing claimed; Monday: a fresh event and last week\'s tiers granted (coins, the sticker), no card on open',
                  ev0['claimable'] == [0, 1, 2, 3, 4, 5] and a['wk'] == '2026-10-12' and a['pts'] == 0 and a['coins'] > ev0['coins'] and ev0['id'] in a['x']['stickers'] and a['away'] and a['open'] == [], [ev0, a])
            await page.tap('#heroPlay'); await page.wait_for_function(f"{A}.on && adv.phase === 'play'", timeout=10000)
            await page.evaluate(f"{A}.finishTest(0)"); await card_tap(page, 'strike', 'map'); await page.wait_for_function("!$('advMap').hidden", timeout=8000); await page.wait_for_timeout(500)
            check(tg + ': the card never comes over a game, a card or the map', await page.evaluate("$('awayCard').hidden"))
            await page.evaluate("$('advBack').click()"); await page.wait_for_function("!$('awayCard').hidden", timeout=5000); await page.wait_for_timeout(600)
            it = await page.evaluate("({ title: $('awayT').textContent, items: [...$('awayList').children].map(l => l.textContent), open: " + OPEN + " })")
            check(tg + ': back home after the round: "' + it['title'] + '": ' + ' · '.join(it['items']), it['title'] == ('בזמן שלא הייתם' if he else 'While you were away') and len(it['items']) >= 2 and it['open'] == ['awayCard'], it)
            await page.screenshot(path=OUT + 'phase1_after_away_%s.png' % ('he' if he else 'en'))
            await page.tap('#awayOk'); await page.wait_for_timeout(400)
            check(tg + ': Yay closes it, once (profile.evAway cleared)', await page.evaluate("$('awayCard').hidden && profile.evAway === null"))
            check(tg + ': rollover: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, init=prof(evAway={'coins': -5, 'snacks': 'x', 'stickers': ['nope', 'cows'], 'hats': [1], 'balls': ['<script>']}))
        check('a stored "away" summary is validated (bad numbers / ids dropped)', await page.evaluate("JSON.stringify(profile.evAway)") == json.dumps({'coins': 0, 'snacks': 0, 'stickers': ['cows'], 'hats': [], 'balls': [], 'evs': []}, separators=(',', ':')))
        await ctx.close()

        # ===== 11. the app hidden: the pause sheet, a 3-2-1 on resume; free modes play on =====
        ctx, page, errs = await fresh(b, init="localStorage.setItem('cgTouchOk','1');" + prof(adv={'stars': stars(4), 'unlocked': 5}))
        for m, start in (('strike', f"{A}.start(5, 'mouse')"), ('slice', "setGameMode('slice'); strikeStart('mouse')"), ('smash', "setGameMode('smash'); smashStageStart(1, 'mouse')"), ('stars', "cgStart('stars')")):
            await page.evaluate(start); await page.wait_for_function(f"gameMode === '{m}' && mode === 'mouse'", timeout=10000); await page.wait_for_timeout(900)
            await page.evaluate(HIDE); await page.wait_for_timeout(200)
            a = await page.evaluate("({ menu: menu.open, pause: pause.on, log: hidp.log.slice(-1)[0] })")
            if m == 'strike': await page.screenshot(path=OUT + 'phase1_after_hidden_pause.png')
            await page.click('#resumeBtn'); await page.wait_for_timeout(250)
            r = await page.evaluate("({ menu: menu.open, pause: pause.on, count: pause.count })")
            await page.wait_for_function("!pause.on", timeout=6000)
            check(f'{m}: the app hidden: the pause sheet; Resume: a 3-2-1, then play', a['menu'] and a['pause'] and a['log'] == 'hidden:' + m and not r['menu'] and r['pause'] and r['count'] in (2, 3), [a, r])
            await page.evaluate("goHome()"); await page.wait_for_timeout(400)
        await page.evaluate("setGameMode('slice'); strikeStart('mouse')"); await page.wait_for_function("gameMode === 'slice' && mode === 'mouse'", timeout=8000); await page.wait_for_timeout(600)
        await page.evaluate("dispatchEvent(new Event('pagehide'))"); await page.wait_for_timeout(150)
        check('pagehide pauses too', await page.evaluate("menu.open && hidp.log.slice(-1)[0] === 'pagehide:slice'"))
        await page.evaluate("closeMenu(true)"); await page.wait_for_function("!pause.on", timeout=6000)
        await page.evaluate("window.__graspGapPause = true; lastFrame = performance.now() - 3000"); await page.wait_for_timeout(200)
        check('a frozen page (a 3 s gap in the frames, no event) pauses too', await page.evaluate("menu.open && hidp.log.slice(-1)[0] === 'gap:slice'"))
        await page.evaluate("closeMenu(true); goHome()"); await page.wait_for_timeout(400)
        for m in ('drums', 'paint'):
            await page.evaluate(f"cgStart('{m}')"); await page.wait_for_function(f"gameMode === '{m}' && mode === 'mouse'", timeout=8000); await page.wait_for_timeout(500)
            await page.evaluate(HIDE); await page.wait_for_timeout(200)
            check(f'{m} (a free mode): hidden or not, it plays on (no pause sheet)', not await page.evaluate("menu.open || pause.on"))
            await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        check('hidden pause: no page errors', not errs, errs); await ctx.close()

        # ===== 12. the steel daily =====
        ctx, page, errs = await fresh(b, init=CASUAL)
        rs = []
        for seed in (1, 2, 3):
            await page.evaluate("goHome()"); await page.wait_for_timeout(300)
            await page.evaluate("__grasp.daily.forceModifier = 'steel'; __grasp.startDaily('mouse')"); await page.wait_for_function("daily.on && mode === 'mouse' && daily.modifier === 'steel'", timeout=8000); await page.wait_for_timeout(500)
            rs.append(await page.evaluate(f"casualSim({{ seed: {seed} }})"))
        check('Steel day: a casual bot hitting hard breaks >= 1 wall in 60 s (3 / 3 seeds: %s walls); its hand never overheats' % [r['walls'] for r in rs],
              all(r['walls'] >= 1 and r['overheats'] == 0 and r['maxHeat'] == 0 for r in rs), rs)
        MED = """(() => { const w = strike.walls[0]; w.kind = 'steel'; for (const k of w.bricks) { k.hp = 3; k.armor = false; k.pu = null; k.tnt = false; k.weak = false; k.key = false; k.gold = false; }
          const k = w.bricks.find(q => q.alive && q.row === 1 && q.col === 1) || w.bricks[0], c = brickCell(w, k.col, k.row);
          smashWall(w, { x: c.x, y: c.y, z: w.z + 1, lx: c.x, ly: c.y, tier: 'medium', dir: -1, speed: 1, vx: 0, vy: 0, spin: 0, trail: [] }, performance.now()); return { hp: k.hp, dent: k.dent || 0 }; })()"""
        u = await page.evaluate(MED)
        check('Steel day: a medium hit takes 1 off the steel plate it lands on', u == {'hp': 2, 'dent': 0}, u)
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        await page.evaluate("__grasp.daily.forceModifier = 'glass'; __grasp.startDaily('mouse')"); await page.wait_for_function("daily.on && daily.modifier === 'glass'", timeout=8000)
        u = await page.evaluate(MED)
        check('another daily: a medium hit only dents steel, and the overheat stays', u == {'hp': 3, 'dent': 1} and await page.evaluate("!steelDay() && (heatHit('hard', performance.now()), heatHit('hard', performance.now()), strike.heat > 0)"), u)
        check('steel daily: no page errors', not errs, errs); await ctx.close()

        # ===== 13. the Road's NEW UNLOCKED card =====
        ctx, page, errs = await fresh(b, init=prof(xp=179, xpv=2))
        await page.evaluate("setGameMode('slice'); strikeStart('mouse')"); await page.wait_for_function("gameMode === 'slice' && mode === 'mouse'", timeout=8000); await page.wait_for_timeout(500)
        await page.evaluate("slice.score = 40; slice.lives = 1"); await page.wait_for_function("slice.over && performance.now() - slice.overAt > 1500", timeout=30000)
        n1 = await page.evaluate("({ level: profile.level, cards: profile.road.cards.slice(), shown: !$('newCard').hidden })")
        check('a level-up at the end of a Slice round: the NEW UNLOCKED card waits (not over the Slice card)', n1['level'] >= 2 and n1['cards'] and not n1['shown'], n1)
        await card_tap(page, 'slice', 'home'); await page.wait_for_function("!$('newCard').hidden", timeout=5000)
        check('...and shows on the start screen', await page.evaluate("$('nuName').textContent") == await page.evaluate("t('rd_glass')"))
        await page.evaluate("closeNewCard()"); await page.wait_for_timeout(500)
        await page.evaluate(f"{A}.start(1, 'mouse')"); await page.wait_for_function("adv.on && adv.phase === 'play'", timeout=8000)
        await page.evaluate("profile.adv.seen = ['glass', 'steel']; addXp(Math.max(0, xpForLevel(5) - profile.xp))"); await page.evaluate(f"{A}.failTest()")
        await page.wait_for_function("strike.over && performance.now() - strike.overAt > 1500", timeout=10000)
        n2 = await page.evaluate("({ level: profile.level, cards: profile.road.cards.slice(), shown: !$('newCard').hidden })")
        check('levels 3-5 during a Strike stage: no card over its card; "Steel walls" (already met in the Adventure) not announced', n2['level'] == 5 and not n2['shown'] and 'steel' not in n2['cards'] and n2['cards'], n2)
        check('NEW UNLOCKED: no page errors', not errs, errs); await ctx.close()

        # ===== 14-16. the sound button; the camera prompt; the Hebrew wording =====
        for he in (False, True):
            ctx, page, errs = await fresh(b, he=he, w=360, h=740, init=prof(coins=1234, xp=900))
            sb = await page.evaluate("(() => { const q = $('startSound').getBoundingClientRect(), m = $('lockBtn').getBoundingClientRect(); return { w: q.width, h: q.height, l: q.left, r: q.right, ml: m.left, mr: m.right, W: innerWidth, muted, p: $('startSound').getAttribute('aria-pressed') }; })()")
            await page.tap('#startSound'); await page.wait_for_timeout(200)
            m1 = await page.evaluate("[muted, localStorage.getItem('muted'), $('startSound').getAttribute('aria-pressed')]")
            check(('HE' if he else 'EN') + ': the speaker beside ⋯ (44 px, on screen): one tap mutes, remembered', sb['w'] >= 44 and sb['h'] >= 44 and sb['l'] >= 0 and sb['r'] <= sb['W'] and not sb['muted'] and m1 == [True, '1', 'false'], [sb, m1])
            await page.tap('#startSound'); await page.wait_for_timeout(200)
            check(('HE' if he else 'EN') + ': ...and one more brings it back', await page.evaluate("!muted"))
            await page.evaluate("localStorage.removeItem('cgTouchOk'); cgStart('bubbles')"); await page.wait_for_function("!$('cgCam').hidden", timeout=8000); await page.wait_for_timeout(500)
            cb = await page.evaluate("(() => { const a = $('cgCamTouch').getBoundingClientRect(), b = $('cgCamOn').getBoundingClientRect(); return { gap: Math.max(a.top - b.bottom, b.top - a.bottom, a.left - b.right, b.left - a.right), stacked: Math.abs(a.left - b.left) < 2 }; })()")
            check(('HE' if he else 'EN') + ': the camera prompt: "Play with touch" and "Turn on camera" >= 16 px apart, stacked on a phone', cb['gap'] >= 16 and cb['stacked'], cb)
            if he:
                hw = await page.evaluate("({ name: t('petNameTitle'), eq: t('equipped'), equip: t('equip') })")
                check('HE: the pet naming sheet is neutral (the Hebrew pass: the plural "איך נקרא לחיה שלכם?"); an equipped look is "נבחר"', hw == {'name': 'איך נקרא לחיה שלכם?', 'eq': 'נבחר', 'equip': 'לבחור'}, hw)
            await ctx.close()
        ctx, page, errs = await fresh(b, mobile=False, w=1280, h=800)
        await page.evaluate("localStorage.removeItem('cgTouchOk'); cgStart('bubbles')"); await page.wait_for_function("!$('cgCam').hidden", timeout=8000); await page.wait_for_timeout(500)
        cb = await page.evaluate("(() => { const a = $('cgCamTouch').getBoundingClientRect(), b = $('cgCamOn').getBoundingClientRect(); return { gap: Math.max(a.left - b.right, b.left - a.right) }; })()")
        check('desktop: side by side, >= 16 px apart', cb['gap'] >= 16, cb)
        await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
