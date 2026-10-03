exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# The player serve (Breakout-style): at the round's start, at each level's start (after the release beat / perk pick) and after a miss, the ball
# waits in front of the player ('Pull back, then flick!') with the level's timers frozen, following the hand / finger / mouse (x, a little of y).
# A tap does nothing and a swipe through it does not serve: pull back (down >= 6% of the screen; a charge ring tightens), then a fast flick up
# launches it with the flick's speed tier (soft / medium / hard / SUPER) and a gentle sideways aim; a flick with no pull-back or a slow drift up
# does not. Mouse (with / without the button), touch (synthetic pointer events, released or not) and the camera stub. Never a guest; the daily's
# seeded run does not depend on the wait. Hooks: strike.waiting, strike.serveReady(), strike.playerServe(power), strike.lastServe, strike.pull, strike.ui.serve.
# Screenshots: tests/out/serve_wait.png, serve_follow_*.png (the ball under the finger), serve_charge_*.png (pulled back: the ring, band, arrows).
S = "__grasp.strike"
FRAMES = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"

async def frames(page, n=1):
    for _ in range(n): await page.evaluate(FRAMES)

# a pointer path driven on the page's own frames: keys = [[ms, x, y], ...] (cumulative ms), linear in between, so the sampled speed is the path's
# speed whatever the frame rate; type 'mouse' | 'touch'; down: a press at the first key (on the canvas), up: a release at the last
GEST_JS = """window.addEventListener('load', () => { try { __grasp.strike.noTiming = true; } catch (e) {} }); // v5: the serve tiers here are by flick speed alone (the PERFECT serve: test_addict)
window.__gest = (keys, o) => new Promise(res => { o = o || {}; const type = o.type || 'mouse', id = type === 'touch' ? 11 : 1; let t0 = null, k = 0;
  const fire = (kind, x, y, tg) => (tg || window).dispatchEvent(new PointerEvent(kind, { clientX: x, clientY: y, pointerType: type, pointerId: id, isPrimary: true, bubbles: true, cancelable: true, button: kind === 'pointermove' ? -1 : 0, buttons: o.down ? 1 : 0 }));
  if (o.down) fire('pointerdown', keys[0][1], keys[0][2], canvas);
  const step = (ts) => { if (t0 === null) t0 = ts; const t = ts - t0; while (k < keys.length - 1 && keys[k + 1][0] <= t) k++;
    let x, y; if (k >= keys.length - 1) { x = keys[keys.length - 1][1]; y = keys[keys.length - 1][2]; } else { const a = keys[k], b = keys[k + 1], q = (t - a[0]) / (b[0] - a[0]); x = a[1] + (b[1] - a[1]) * q; y = a[2] + (b[2] - a[2]) * q; }
    fire('pointermove', x, y);
    if (t >= keys[keys.length - 1][0]) { if (o.up) fire('pointerup', x, y); res(); return; } requestAnimationFrame(step); };
  requestAnimationFrame(step); });"""

def pull_flick(x, y, v, pull=110, dx=0.0, flick_ms=140, rest=200, scale=1.0):
    """keys: rest at (x, y), pull down `pull` px in 250 ms, hold, flick up at v (px/ms on the tier scale, times the screen's strikeScale) for flick_ms, hold"""
    sp = v * scale; up = sp * flick_ms
    return [[0, x, y], [rest, x, y], [rest + 250, x, y + pull], [rest + 400, x, y + pull], [rest + 400 + flick_ms, x + dx * up, y + pull - up], [rest + 700 + flick_ms, x + dx * up, y + pull - up]]

async def armed_wait(page):  # a fresh waiting ball, past its arming time, the pull state clear
    await page.evaluate(f"{S}.serveReady()"); await page.wait_for_function(f"{S}.waiting && performance.now() - {S}.waitSince > 420", timeout=4000)

async def new_page(b, gfx=None):
    ctx = await b.new_context(viewport={'width': 1280, 'height': 800}); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + GEST_JS + (f"window.__graspGfx = {gfx};" if gfx else ''))
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
    await page.evaluate("__grasp.setPlayerLevel(20)")
    return ctx, page, errs

async def play(page):
    await page.click('#mouseBtn'); await page.click('.modes button[data-mode=strike]'); await page.click('#advEndless')
    await page.wait_for_function("gameMode === 'strike' && __grasp.strike.walls.length", timeout=8000)
    await page.evaluate("(() => { window.__sfx = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); o(k, a); }; })(); __grasp.grippy.on = false; __grasp.CONFIG.STRIKE_PU_RATE = 0")
    await page.mouse.move(640, 200)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        ctx, page, errs = await new_page(b)
        await play(page)
        # ---- round start: the ball waits in front of the player; nothing comes from the far end ----
        await page.wait_for_function(f"{S}.waiting", timeout=4000)
        w0 = await page.evaluate(f"({{ z: {S}.ball.z, dir: {S}.ball.dir, n: {S}.balls.length, sc: {S}.ballScreen(), ui: {S}.ui.serve, meter: {S}.ui.meterTop, hitZ: __grasp.CONFIG.STRIKE_HIT_Z, serves: {S}.serves, guest: {S}.ball.guest, beats: {S}.beats }})")
        await frames(page, 2); ui = await page.evaluate(f"{S}.ui.serve")
        check("round start: one ball waiting at the near plane (in the hit window), low on the screen above the power meter; 'Pull back, then flick!' over it",
              w0['n'] == 1 and w0['dir'] == 0 and 0 < w0['z'] <= w0['hitZ'] and w0['sc']['y'] > 800 * 0.55 and w0['sc']['y'] + w0['sc']['r'] <= w0['meter'] + 2 and ui and ui['text'] == 'Pull back, then flick!' and ui['ty'] < w0['sc']['y'] and w0['guest'] is None, [w0, ui])
        await page.wait_for_timeout(1500)
        w1 = await page.evaluate(f"({{ waiting: {S}.waiting, z: {S}.ball.z, dir: {S}.ball.dir, serves: {S}.serves, beats: {S}.beats, score: {S}.score }})")
        check('1.5 s later it is still waiting (no automatic serve, no heartbeat)', w1['waiting'] and w1['dir'] == 0 and w1['serves'] == w0['serves'] and w1['beats'] == w0['beats'] and w1['score'] == 0, w1)
        await page.screenshot(path='tests/out/serve_wait.png')
        # ---- frozen while waiting: power-up timers and the boss ----
        await page.evaluate(f"{S}.setPowerDuration(800); {S}.catchTest('big'); {S}.serveReady()")
        pu0 = await page.evaluate(f"{S}.powerups[0].until - performance.now()")
        await page.wait_for_timeout(1200)
        pu1 = await page.evaluate(f"({{ left: {S}.powerups.length ? {S}.powerups[0].until - performance.now() : -1, on: {S}.powerOn('big'), waiting: {S}.waiting }})")
        check('power-up timers freeze while the serve waits (an 0.8 s Big ball still on after 1.2 s)', pu1['waiting'] and pu1['on'] and pu1['left'] > pu0 - 150, [pu0, pu1])
        await page.evaluate(f"{S}.powerups.length = 0; {S}.setPowerDuration(0); {S}.spawnBoss(1); {S}.serveReady()"); await frames(page, 1)
        bz0 = await page.evaluate(f"{S}.boss.z"); await page.wait_for_timeout(700); bz1 = await page.evaluate(f"{S}.boss.z")
        check('the boss holds still while the serve waits', abs(bz1 - bz0) < 0.5 and await page.evaluate(f"{S}.waiting"), [bz0, bz1])
        await page.evaluate(f"{S}.boss = null; {S}.walls.length = 0; {S}.spawnWall('brick', 960)")
        # ---- the ball follows the hand sideways ----
        await page.mouse.move(300, 300, steps=4); await page.wait_for_timeout(900)
        fx = await page.evaluate(f"{S}.ballScreen().x")
        await page.mouse.move(1260, 300, steps=4); await page.wait_for_timeout(900)
        fx2 = await page.evaluate(f"{S}.ballScreen().x")
        check(f'while waiting the ball drifts toward the hand: x {fx:.0f} with the hand at 300; {fx2:.0f} (held inside the middle 60%) with it at 1260', abs(fx - 300) < 30 and abs(fx2 - 1024) < 30 and await page.evaluate(f"{S}.waiting"), [fx, fx2])
        # ---- ...and a little of its y (kept low, above the meter) ----
        await page.mouse.move(640, 300, steps=3); await page.wait_for_timeout(700); yh = await page.evaluate(f"{S}.ballScreen()")
        await page.mouse.move(640, 790, steps=3); await page.wait_for_timeout(700); yl = await page.evaluate(f"({{ sc: {S}.ballScreen(), meter: {S}.ui.meterTop }})")
        check(f"while waiting the ball follows the hand's y a little: {yh['y']:.0f} with the hand high, {yl['sc']['y']:.0f} with it low (still above the meter, low on the screen)",
              yl['sc']['y'] - yh['y'] > 25 and yh['y'] > 800 * 0.55 and yl['sc']['y'] + yl['sc']['r'] <= yl['meter'] + 2, [yh, yl])
        # ---- a tap / click does nothing; a swipe through the ball does not serve ----
        await armed_wait(page); sc = await page.evaluate(f"{S}.ballScreen()"); s0 = await page.evaluate(f"{S}.serves")
        await page.mouse.click(sc['x'], sc['y']); await frames(page, 4)
        await page.mouse.click(200, 300); await frames(page, 4)
        tp = await page.evaluate(f"({{ waiting: {S}.waiting, serves: {S}.serves, dir: {S}.ball.dir }})")
        check('a click on the waiting ball (or anywhere) does not serve it', tp['waiting'] and tp['serves'] == s0 and tp['dir'] == 0, tp)
        await armed_wait(page); sc = await page.evaluate(f"{S}.ballScreen()")
        await page.evaluate(f"__gest([[0, {sc['x'] - 300}, {sc['y']}], [120, {sc['x'] - 300}, {sc['y']}], [240, {sc['x'] + 300}, {sc['y']}], [400, {sc['x'] + 300}, {sc['y']}]])"); await frames(page, 2)
        check('a fast swipe sideways through the waiting ball (the old slap) does not serve it', await page.evaluate(f"{S}.waiting && {S}.serves === {s0}"))
        # ---- pull back, then flick: the charge cue, then the launch with the flick's tier ----
        scale = await page.evaluate(f"{S}.strikeScale ? {S}.strikeScale() : strikeScale()")
        await armed_wait(page)
        await page.evaluate("__gest([[0, 640, 520], [150, 640, 520], [400, 640, 640], [500, 640, 640]])"); await frames(page, 2)
        ch = await page.evaluate(f"({{ waiting: {S}.waiting, armed: {S}.pull.armed, c: {S}.pull.c, ui: {S}.ui.serve, want: t('flickNow') }})")
        check('pulled back 120 px (15% of the screen): armed, the charge full, the prompt says "Now flick it up!"', ch['waiting'] and ch['armed'] and ch['c'] == 1 and ch['ui']['armed'] and ch['ui']['text'] == ch['want'], ch)
        await page.screenshot(path='tests/out/serve_charge_desktop.png')
        await page.evaluate("__gest([[0, 640, 640], [900, 640, 505], [1000, 640, 505]])"); await frames(page, 2)  # a slow drift back up (0.15 px/ms)
        dr = await page.evaluate(f"({{ waiting: {S}.waiting, armed: {S}.pull.armed, serves: {S}.serves }})")
        check('a slow drift back up does not launch it (and un-arms the pull)', dr['waiting'] and not dr['armed'] and dr['serves'] == s0, dr)
        await page.evaluate("__gest([[0, 640, 640], [100, 640, 640]])"); await armed_wait(page)  # (the pointer parked low first: no jump down to count as a pull)
        await page.evaluate("__gest([[0, 640, 640], [300, 640, 640], [440, 640, 400], [600, 640, 400]])"); await frames(page, 2)  # a fast flick with no pull-back first
        check('a fast flick up with no pull-back does not launch it', await page.evaluate(f"{S}.waiting && {S}.serves === {s0}"))
        for v, want in ((0.42, 'soft'), (0.85, 'medium'), (1.7, 'hard'), (3.0, 'super')):
            await armed_wait(page); n0 = await page.evaluate(f"{S}.serves")
            await page.evaluate(f"__gest({json.dumps(pull_flick(640, 470, v, scale=scale))})")
            await page.wait_for_function(f"!{S}.waiting", timeout=3000)
            sv = await page.evaluate(f"({{ last: {S}.lastServe, dir: {S}.ball.dir, serves: {S}.serves, flash: {S}.ui.tierFlash && {S}.ui.tierFlash.tier, pop: {S}.ui.tierFlash && {S}.ui.tierFlash.val, tierOf: speedTier({S}.lastServe.v), score: {S}.score, hits: {S}.hits }})")
            check(f'pull back + flick at {v} px/ms: launched as "{want}" (its speed\'s tier; the hit-meter pop shows it); no points', sv['last']['flick'] and sv['last']['tier'] == want == sv['tierOf'] and sv['flash'] == want and sv['dir'] == -1 and sv['serves'] == n0 + 1 and sv['score'] == 0 and sv['hits'] == 0, sv)
        await armed_wait(page)
        await page.evaluate(f"__gest({json.dumps(pull_flick(640, 470, 1.4, dx=0.5, scale=scale))}, {{ down: true, up: true }})")
        await page.wait_for_function(f"!{S}.waiting", timeout=3000)
        am = await page.evaluate(f"({{ last: {S}.lastServe, vx: {S}.ball.vx, vy: {S}.ball.vy }})")
        check('with the button held, a flick up and to the right: launched, aimed gently right (aim <= 0.6, no vertical drift)', am['last']['flick'] and 0.2 < am['last']['aim'] <= 0.6 and am['vx'] > 0 and am['vy'] == 0, am)
        await page.wait_for_function(f"{S}.ball && {S}.ball.z > 1000", timeout=6000)
        check('...and it flies on down the corridor', await page.evaluate(f"{S}.ball.dir") == -1)
        su = await page.evaluate(f"(() => {{ const s = {S}; s.serveReady(); const t = s.playerServe('super'); return {{ t, sup: s.ball.super, dir: s.ball.dir, tier: s.ball.tier }}; }})()")
        check('the test hook: a SUPER serve is allowed: the ball goes as a SUPER ball', su['t'] == 'super' and su['sup'] and su['dir'] == -1, su)
        # ---- after a miss: waiting again ----
        await page.evaluate(f"{S}.lives = 3"); await page.mouse.move(1200, 150)
        await page.evaluate(f"(() => {{ const s = {S}; cursor.history.length = 0; s.setBallZ(-__grasp.CONFIG.STRIKE_HIT_Z * 0.7, 300, 650); }})()")
        await page.wait_for_function(f"{S}.misses > 0", timeout=4000)
        ms = await page.evaluate(f"({{ lives: {S}.lives, waiting: {S}.waiting }})")
        await page.wait_for_function(f"{S}.waiting", timeout=4000)
        check('after a miss (a life lost) the next ball waits for the player\'s serve again', ms['lives'] == 2 and not ms['waiting'] and await page.evaluate(f"{S}.ball.dir === 0 && !{S}.ball.guest"), ms)
        # ---- after the release beat: waiting ----
        await page.evaluate(f"(() => {{ const s = {S}; s.lives = 30; s.setLevel(4); s.setCleared(s.cleared + 7); }})()")
        rl = await page.evaluate(f"({{ level: {S}.level, rel: {S}.releaseUntil - performance.now(), balls: {S}.balls.length, waiting: {S}.waiting }})")
        await page.wait_for_function(f"{S}.waiting", timeout=6000)
        at = await page.evaluate(f"performance.now() - {S}.releaseUntil")
        check('a level completed: the release beat (no ball), then the new level starts with the waiting serve', rl['level'] == 5 and rl['rel'] > 2000 and rl['balls'] == 0 and not rl['waiting'] and at >= -50, [rl, at])
        # ---- never a guest as the waiting ball; guests still come in during the rally ----
        g = await page.evaluate(f"""(() => {{ const s = {S}; s.guestEvery = 1; const out = []; for (let i = 0; i < 6; i++) {{ s.serveReady(); out.push(s.ball.guest); }} s.playerServe('medium'); const gq = s.ball.guest; s.ball.z = __grasp.CONFIG.STRIKE_Z_FAR - 2; return {{ out, gq }}; }})()""")
        await frames(page, 2)
        g2 = await page.evaluate(f"({{ guest: {S}.ball.guest, dir: {S}.ball.dir }})")
        check('with a guest due on every serve: the waiting ball is never a guest; the launched ball neither; its rebound from the far end comes back as one', all(x is None for x in g['out']) and g['gq'] is None and g2['guest'] in ('cow', 'monkey') and g2['dir'] == 1, [g, g2])
        await page.evaluate(f"{S}.guestEvery = 0; {S}.ball.guest = null")
        check('serve: no page errors', not errs, errs); await ctx.close()

        # ---- a decluttered play screen (360 x 740, EN + HE): nothing of the HUD / toasts / NEXT in the central play area, no Grippy drawn ----
        for he in (False, True):
            ctx = await b.new_context(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs = []
            page.on('pageerror', lambda e: errs.append(str(e)))
            await page.add_init_script(INIT + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');"))
            await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600); await page.evaluate("__grasp.setPlayerLevel(20)")
            await page.tap('#mouseBtn'); await page.tap('.modes button[data-mode=strike]'); await page.tap('#advEndless')
            await page.wait_for_function("gameMode === 'strike' && __grasp.strike.walls.length", timeout=8000)
            await page.evaluate(f"(() => {{ const s = {S}; s.setLevel(4); s.serve(); s.setBallZ(2300, 30, 30); s.ball.speed = 0; s.lives = 6; s.streak = 7; s.catchTest('big'); s.perks = {{ wide: 1, lucky: 2 }}; __grasp.addCoins(4); __grasp.grippy.cool(); __grasp.grippy.say('start'); toast('copied', null, 'check'); }})()")
            await frames(page, 3); await page.wait_for_timeout(300)
            bx = await page.evaluate(f"""(() => {{ const s = {S}, u = s.ui, out = {{}}; const r = (e) => {{ const q = e.getBoundingClientRect(); return q.width && q.height ? {{ x: q.left, y: q.top, w: q.width, h: q.height }} : null; }};
              out.hud = u.hud; out.next = u.nextCard; out.streak = u.streakBox; out.tag = u.tagBox; out.coinPill = __grasp.coinUi.box; out.prog = u.progBar && {{ x: u.progBar.x, y: u.progBar.y, w: u.progBar.w, h: u.progBar.h }};
              out.meter = {{ x: 0, y: u.meterTop, w: innerWidth, h: innerHeight - u.meterTop }}; out.grippy = __grasp.grippy.box(); out.hint = $('hint').classList.contains('show') ? r($('hint')) : null;
              out.toasts = [...document.querySelectorAll('#metaToast .mt:not(.wait)')].map(r).filter(Boolean); out.icons = u.puIcons.map(p => ({{ x: p.x - p.r, y: p.y - p.r, w: p.r * 2, h: p.r * 2 }})); return out; }})()""")
            C = {'x': 360 * 0.15, 'y': 740 * 0.25, 'w': 360 * 0.7, 'h': 740 * 0.55}
            inter = lambda a, c: a and a['x'] < c['x'] + c['w'] and a['x'] + a['w'] > c['x'] and a['y'] < c['y'] + c['h'] and a['y'] + a['h'] > c['y']
            boxes = [(k, v) for k, v in bx.items() if k not in ('toasts', 'icons')] + [('toast', q) for q in bx['toasts']] + [('icon', q) for q in bx['icons']]
            bad = [k for k, v in boxes if inter(v, C)]
            tag = 'phone ' + ('he' if he else 'en')
            check(tag + ': in play nothing of the HUD row, coins, toasts, hint, Grippy or the tier flash sits in the central play area (x 15-85%, y 25-80%)', not bad and bx['hud'] and bx['hud']['h'] <= 32 and bx['coinPill'] is None and bx['grippy'] is None, [bad, bx])
            check(tag + ': minimal HUD: one slim row (<= 32 px) with only the hearts and walls pill: no NEXT card, streak chip or progress line even with a streak of 7 at level 4; no Grippy hand / bubble on screen (he is a voice now)', bx['next'] is None and bx['streak'] is None and bx['prog'] is None and await page.evaluate(f"{S}.ui.hudParts.join()") == 'hearts,walls' and bx['grippy'] is None and not await page.evaluate("!!document.querySelector('#grippy, .nuGrip')"), bx)
            hd = bx['hud']; pb = await page.evaluate("(() => { const r = $('pauseBtn').getBoundingClientRect(); return { l: r.left, t: r.top, b: r.bottom }; })()")
            check(tag + ': the HUD row shares the pause button\'s row and stays clear of it', hd['y'] < pb['b'] and hd['y'] + hd['h'] > pb['t'] and hd['x'] + hd['w'] <= pb['l'], [hd, pb])
            await page.screenshot(path='tests/out/serve_declutter_' + ('he' if he else 'en') + '.png')
            hid = await page.evaluate(f"(() => {{ const s = {S}; s.setLevel(2); s.setBallZ(2300, 30, 30); s.ball.speed = 0; return 1; }})()"); await frames(page, 2)
            n2 = await page.evaluate(f"{S}.ui.nextCard")
            await page.evaluate(f"(() => {{ const s = {S}; s.setLevel(5); s.setBallZ(600, 180, 400); s.ball.speed = 0; }})()"); await frames(page, 2)
            n3 = await page.evaluate(f"{S}.ui.nextCard")
            check(tag + ': NEXT hidden on levels 1-2 and while an incoming ball is close', n2 is None and n3 is None, [n2, n3])
            check(tag + ' declutter: no page errors', not errs, errs); await ctx.close()

        # ---- phone (touch, 360 x 740), EN + HE: a tap does nothing; the ball follows the finger; drag down + flick up (released or not) serves ----
        for he in (False, True):
            tag = 'phone ' + ('he' if he else 'en')
            ctx = await b.new_context(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs = []
            page.on('pageerror', lambda e: errs.append(str(e)))
            await page.add_init_script(INIT + GEST_JS + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');"))
            await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600); await page.evaluate("__grasp.setPlayerLevel(20)")
            await page.tap('#mouseBtn'); await page.tap('.modes button[data-mode=strike]'); await page.tap('#advEndless')
            await page.wait_for_function(f"gameMode === 'strike' && {S}.waiting && !{S}.ui.levelBanner", timeout=10000)
            await page.evaluate("__grasp.grippy.on = false; hideHint()")
            tip = await page.evaluate("({ seen: __grasp.profile.tips.slice(), shown: __grasp.grippy.tips.map(x => x.text), want: t('tipFlick') })")
            check(tag + ': the first serve ever explains the gesture once (the hint toast, in the UI language)', 'flick' in tip['seen'] and tip['shown'] == [tip['want']] and (not he or re.search('[\u0590-\u05ff]', tip['want'])), tip)
            await armed_wait(page); sc = await page.evaluate(f"{S}.ballScreen()"); n0 = await page.evaluate(f"{S}.serves")
            await page.touchscreen.tap(sc['x'], sc['y']); await frames(page, 2)
            await page.touchscreen.tap(180, 300); await frames(page, 4)
            check(tag + ': a tap on the ball or anywhere does not serve', await page.evaluate(f"{S}.waiting && {S}.serves === {n0}"))
            await page.evaluate("__gest([[0, 300, 560], [300, 300, 560], [1200, 300, 560]], { type: 'touch', down: true })"); await page.wait_for_timeout(200)
            fo = await page.evaluate(f"({{ sc: {S}.ballScreen(), ui: {S}.ui.serve, want: t('hitToStart') }})")
            check(tag + f": the waiting ball follows the finger (x {fo['sc']['x']:.0f} with the finger at 300 is clamped to the middle 60%: 288); prompt in the UI language, kept on screen", abs(fo['sc']['x'] - 288) < 20 and fo['ui']['text'] == fo['want'] and fo['ui']['tx'] - fo['ui']['tw'] / 2 >= 0 and fo['ui']['tx'] + fo['ui']['tw'] / 2 <= 360 and (not he or re.search('[\u0590-\u05ff]', fo['want'])), fo)
            await page.screenshot(path=f"tests/out/serve_follow_{'he' if he else 'en'}.png")
            await page.evaluate("__gest([[0, 300, 560], [250, 300, 640], [600, 300, 640]], { type: 'touch' })"); await frames(page, 1)
            ch = await page.evaluate(f"({{ armed: {S}.pull.armed, ui: {S}.ui.serve, waiting: {S}.waiting }})")
            check(tag + ': finger dragged down 80 px (11%): armed, the prompt says flick', ch['waiting'] and ch['armed'] and ch['ui']['armed'] and ch['ui']['charge'] == 1, ch)
            await page.screenshot(path=f"tests/out/serve_charge_{'he' if he else 'en'}.png")
            await page.evaluate("__gest([[0, 300, 640], [130, 300, 450]], { type: 'touch', up: true })")  # flick up (1.46 px/ms) and lift the finger
            await page.wait_for_function(f"!{S}.waiting", timeout=3000)
            sv = await page.evaluate(f"({{ last: {S}.lastServe, tierOf: speedTier({S}.lastServe.v), dir: {S}.ball.dir }})")
            check(tag + ': ...then a flick up (finger lifted at its end) serves it with its speed tier (hard / SUPER on a phone-sized screen)', sv['last']['flick'] and sv['last']['tier'] == sv['tierOf'] and sv['last']['tier'] in ('hard', 'super') and sv['dir'] == -1, sv)
            await armed_wait(page)
            await page.evaluate("__gest([[0, 180, 500], [200, 180, 500], [450, 180, 580], [600, 180, 580], [740, 180, 420], [900, 180, 420]], { type: 'touch', down: true })")
            await page.wait_for_function(f"!{S}.waiting", timeout=3000)
            check(tag + ': the finger still down after the flick: served too', await page.evaluate(f"{S}.lastServe.flick && {S}.ball.dir === -1"))
            await page.evaluate("(() => { const e = new PointerEvent('pointerup', { pointerType: 'touch', pointerId: 11, clientX: 180, clientY: 420, bubbles: true }); window.dispatchEvent(e); })()")
            check(tag + ' touch serve: no page errors', not errs, errs); await ctx.close()

        # ---- camera stub: the hand moves down, then up fast; a slow drift up does not serve ----
        ctx = await b.new_context(permissions=['camera'], viewport={'width': 1280, 'height': 800}); page = await ctx.new_page(); await routes(page); errs = []
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + HAND_JS + GEST_JS)
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600); await page.evaluate("__grasp.setPlayerLevel(20)")
        await page.evaluate("window.__hy = () => 420; window.__handFor = () => handAt(640, __hy(), 0.8)")
        await page.click('#camBtn'); await page.click('.modes button[data-mode=strike]'); await page.click('#advEndless')
        await page.wait_for_function(f"mode === 'camera' && gameMode === 'strike' && {S}.waiting", timeout=20000)
        await page.evaluate("__grasp.grippy.on = false; __grasp.CONFIG.STRIKE_PU_RATE = 0")
        await armed_wait(page); await page.wait_for_timeout(1700); n0 = await page.evaluate(f"{S}.serves")
        # (path: y(t) in ms since T0, piecewise linear)
        PATH = "window.__path = (keys) => { const T0 = performance.now(); window.__hy = () => { const t = performance.now() - T0; let k = 0; while (k < keys.length - 1 && keys[k + 1][0] <= t) k++; if (k >= keys.length - 1) return keys[keys.length - 1][1]; const a = keys[k], b = keys[k + 1]; return a[1] + (b[1] - a[1]) * (t - a[0]) / (b[0] - a[0]); }; }"
        await page.evaluate(PATH)
        await page.evaluate("__path([[0, 420], [400, 560], [800, 560], [2200, 380]])"); await page.wait_for_timeout(2500)  # down 140 px, then a slow drift up (0.13 px/ms)
        cs = await page.evaluate(f"({{ waiting: {S}.waiting, serves: {S}.serves, armed: {S}.pull.armed }})")
        check('camera: hand down then a slow drift up: no serve', cs['waiting'] and cs['serves'] == n0 and not cs['armed'], cs)
        await page.wait_for_timeout(1700)
        await page.evaluate("__path([[0, 380], [200, 160], [600, 160]])"); await page.wait_for_timeout(800)  # a fast flick up with no pull-back
        check('camera: a fast flick up with no pull-back: no serve', await page.evaluate(f"{S}.waiting && {S}.serves === {n0}"))
        await page.evaluate("__path([[0, 160], [500, 160], [900, 330], [1300, 330], [1500, 60], [1900, 60]])")  # pull back 170 px, then flick up 270 px in 0.2 s
        await page.wait_for_function(f"!{S}.waiting", timeout=5000)
        cv = await page.evaluate(f"({{ last: {S}.lastServe, tierOf: speedTier({S}.lastServe.v), dir: {S}.ball.dir }})")
        check('camera: the hand pulled back, then flicked up fast: served with its speed tier', cv['last']['flick'] and cv['last']['tier'] == cv['tierOf'] and cv['last']['tier'] != 'soft' and cv['dir'] == -1, cv)
        check('camera serve: no page errors', not errs, errs); await ctx.close()

        # ---- incoming balls never pass through a live brick; guests pop out in front of the nearest wall ----
        ctx, page, errs = await new_page(b); await play(page)
        await page.evaluate(f"(() => {{ const s = {S}; s.lives = 40; s.walls.length = 0; }})()")
        r = await page.evaluate(f"""(() => {{ const s = {S}; s.walls.length = 0; const w = s.spawnWall('brick', 900); for (const k of w.bricks) k.hp = 1; s.serve(); const b = s.ball; b.guest = null; b.z = 1000; b.x0 = b.x = 0; b.y0 = b.y = 0; b.tx = 0; b.ty = 0; b.curve = 0; b.speed = s.pace; return {{ id: w.id, left: w.left }}; }})()""")
        worst = 0
        for _ in range(40):
            q = await page.evaluate(f"(() => {{ const s = {S}, w = s.walls.find(x => x.id === {r['id']}), b = s.ball; if (!w || !b) return {{ done: true }}; const rr = ballRad(b); let o = 0; if (b.z <= w.z && b.z > w.z - 40) for (const k of w.bricks) if (k.alive) {{ const c = brickCell(w, k.col, k.row); const d = Math.hypot(Math.max(0, Math.abs(b.x - c.x) - c.w / 2), Math.max(0, Math.abs(b.y - c.y) - c.h / 2)); if (d < rr - 1) o++; }} return {{ z: b.z, o, left: w.left, done: b.z < w.z - 60 }}; }})()")
            worst = max(worst, q.get('o', 0))
            if q.get('done'): break
            await page.evaluate(FRAMES)
        aft = await page.evaluate(f"(() => {{ const w = {S}.walls.find(x => x.id === {r['id']}); return {{ left: w ? w.left : 0, back: {S}.lastBack }}; }})()")
        check('an incoming ball meeting an intact wall from behind knocks out the bricks it overlaps (debris toward the player) and never overlaps a live brick as it crosses', aft['left'] < r['left'] and aft['back'] and worst == 0, [r, aft, worst])
        gz = await page.evaluate(f"(() => {{ const s = {S}; s.walls.length = 0; s.spawnWall('brick', 900); s.spawnWall('brick', 1300); const b = s.spawnGuest('cow'); const near = Math.min(...s.walls.filter(w => w.left > 0).map(w => w.z)); return {{ z: b.z, near, pop: !!b.popAt }}; }})()")
        check('a guest pops out in front of the nearest standing wall (its z < the wall\'s), with a puff', gz['z'] < gz['near'] and gz['pop'], gz)
        check('incoming walls: no page errors', not errs, errs); await ctx.close()

        # ---- the daily: the seeded run does not depend on how long the serve waits ----
        seq = []
        for wait in (250, 1600):
            ctx, page, errs = await new_page(b)
            await page.evaluate("__grasp.daily.forceModifier = 'tiny'; __grasp.setGameMode('strike'); __grasp.startDaily()")
            await page.wait_for_function(f"__grasp.daily.on && {S}.waiting", timeout=8000)
            await page.wait_for_timeout(wait)
            seq.append(await page.evaluate(f"(() => {{ const s = {S}; s.playerServe('medium'); return {{ walls: s.walls.map(w => w.kind + ':' + w.bricks.filter(k => k.pu).length), gq: s.guestQ && s.guestQ.at, r: ['serve', 'walls', 'bricks', 'guest'].map(c => __grasp.strikeRand(c)) }}; }})()"))
            check(f'daily (waited {wait} ms): no page errors', not errs, errs); await ctx.close()
        check('daily: the same seeded run whether the serve waited 0.25 s or 1.6 s (walls, guest schedule, every random channel)', seq[0] == seq[1], seq)

        # ---- 3D: the waiting ball is drawn by the WebGL renderer at the logic's spot ----
        ctx, page, errs = await new_page(b, gfx="{ pr: 0.5, auto: false, shadows: false }")
        await play(page)
        await page.wait_for_function(f"({S}.gfx === '3d' || {S}.gfxInfo.state === 'failed') && {S}.waiting", timeout=20000)
        if await page.evaluate(f"{S}.gfx") == '3d':
            await page.mouse.move(640, 150); await page.wait_for_timeout(600)
            sc = await page.evaluate(f"{S}.ballScreen()")
            c3 = max([await page.evaluate(f"{S}.pixel3d({sc['x'] + dx * sc['r']}, {sc['y'] + dy * sc['r']})") for dx, dy in ((0, 0), (-0.4, 0.3), (0.4, 0.3), (0, 0.5), (-0.5, -0.2))], key=lambda c: c[0] - c[2])  # (the most saturated of a few points: the near ball catches a bright highlight)
            ui = await page.evaluate(f"{S}.ui.serve")
            check('3D: the waiting ball is drawn (the coral 3D ball at ballScreen()), with the prompt over it', c3[0] > 150 and c3[0] > c3[2] + 40 and ui and ui['text'] == 'Pull back, then flick!', [c3, sc, ui])
            await page.screenshot(path='tests/out/serve_wait_3d.png')
            await page.evaluate(f"{S}.playerServe('hard')"); await page.wait_for_timeout(300)
            check('3D: served, it flies away', await page.evaluate(f"{S}.ball.dir === -1 && {S}.ball.z > 100"))
        else: print('INFO no WebGL: 3D serve check skipped')
        check('3D serve: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
