# Strike's rally ("faster and faster") and Frenzy (טירוף).
# Covers: in normal play (Endless, Adventure, the daily) every return makes the ball a step faster (+5%), capped (+70%; +45% on world 1's gentle
# first stages; +60% in Endless on Easy), and a miss drops it back to the base speed; the speed really moves the ball (speedMul) and widens the
# reach a little; the visuals scale with it (the ball's heat colour white -> yellow -> orange -> blazing, its glow, speed lines), the whoosh's
# pitch rises, a 'x1.4 SPEED' pop at every +20% and at the cap; points x the speed bonus on top of the combo; more power (a growing chance of one
# tier more, never past SUPER, never extra heat); a fast rally heats the hand less; the test flag noRally and extrasOff turn it off. Frenzy: the
# map footer's button (EN / HE, its best under it), /frenzy; one heart + a shield for the very first miss (the speed drops back halfway), the
# uncapped rally (+4% a hit), clean walls, no heat; the run ends on the next miss: hits in a row, the top speed, NEW RECORD!, the best kept
# (validated on load), a share line; Play again stays in Frenzy, Home leaves it. Screenshots tests/out/frenzy_*.png (phone EN / HE, 3D).
exec(open('tests/test_challenge.py').read().split('async def main')[0])
F = "__grasp.frenzy"; RL = "__grasp.rally"
NO_RALLY = False  # (the shared helpers leave the rally on here)

HIT = """((n, tier) => { const s = __grasp.strike, out = []; for (let i = 0; i < n; i++) { s.setBallZ(200, 640, 420); s.ball.speed = s.pace; strikeHit(s.ball, performance.now(), tier || 'medium', null); park(); s.heat = 0; s.hotUntil = 0; out.push(+rallyK().toFixed(3)); } return out; })"""

async def frenzy_start(page, click=True):
    if click:
        await page.evaluate("profile.adv.unlocked = 1; saveProfile(); setInputPref('mouse')")
        await page.click('.modes button[data-mode=strike]'); await page.wait_for_function("advMapOpen()", timeout=8000)
        await page.click('#advFrenzy')
    await page.wait_for_function(f"{F}.on && gameMode === 'strike' && mode === 'mouse' && {S}.walls.length === 4", timeout=10000)
    await page.evaluate(f"__grasp.CONFIG.STRIKE_PU_RATE = 0; {S}.guestEvery = 0")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ===== R1: the rally in normal play (Endless) =====
        ctx, page, errs = await fresh(b); await endless(page)
        await page.evaluate(f"{S}.noSpecials = true; {S}.noTiming = true")
        k0 = await page.evaluate(f"({{ on: {RL}.on(), k: {RL}.k(), cap: {RL}.cap(), easy: strikeEasy() }})")
        check('the rally is on in Endless and starts at the base speed (x1)', k0['on'] and k0['k'] == 1, k0)
        ks = await page.evaluate(f"{HIT}(16)")
        cap = 1 + k0['cap']
        check('every return makes the ball a step faster (+5% a hit: 1.05, 1.10, ...)', ks[:4] == [1.05, 1.1, 1.15, 1.2], ks)
        check(f'the speed-up is capped in normal play (Endless on {"Easy" if k0["easy"] else "Normal"}: x{cap:.2f}; never past +80%)', abs(max(ks) - cap) < 1e-6 and cap <= 1.8 and ks[-1] == ks[-2], ks)
        sp = await page.evaluate(f"""(() => {{ const s = {S}; s.setBallZ(2000, 640, 420); const b = s.ball; b.speed = s.pace; const z0 = b.z; ballTick(b, performance.now(), 16, false, speedMul()); const fast = z0 - b.z;
          const r = s.rally; s.rally = 0; b.z = z0; ballTick(b, performance.now(), 16, false, speedMul()); const base = z0 - b.z; s.rally = r; park(); return {{ fast, base, mul: speedMul(), reach: {RL}.reach() }}; }})()""")
        check('the speed really moves the ball: a tick at the cap travels x the rally factor; the reach widens a little with it', abs(sp['fast'] / sp['base'] - cap) < 0.02 and abs(sp['mul'] - cap) < 1e-6 and 1.1 < sp['reach'] < 1.3, sp)
        sf = await page.evaluate("__sfxa.filter(a => a[0] === 'rally').map(a => +a[1].toFixed(3))")
        check('a whoosh on every speed step, its pitch rising with the speed', len(sf) >= 10 and sf == sorted(sf) and sf[0] < sf[-1], sf)
        pop = await page.evaluate(f"{S}.ui.speedPop")
        check('a speed pop at the cap ("MAX SPEED!")', pop and pop['max'] and abs(pop['k'] - cap) < 1e-6, pop)
        await page.evaluate(f"{S}.rally = 0; {S}.ui.speedPop = null")
        p4 = await page.evaluate(f"(() => {{ const r = {HIT}(4); return {{ r, pop: {S}.ui.speedPop }}; }})()")
        check('a pop at every +20% (x1.2 after 4 returns), saying "×1.2 SPEED"', p4['pop'] and abs(p4['pop']['k'] - 1.2) < 1e-6 and not p4['pop']['max'], p4)
        await page.wait_for_timeout(120)
        sb = await page.evaluate(f"{S}.ui.speedBox")
        check('the pop is drawn by the HUD pill (shared place with the combo pop), inside the screen', sb and '1.2' in sb['text'] and 'SPEED' in sb['text'] and 0 <= sb['x'] and sb['x'] + sb['w'] <= 1280 and sb['y'] < 200, sb)
        # the miss: back to the base speed
        ms = await page.evaluate(f"(() => {{ const s = {S}; {HIT}(10); const k1 = rallyK(); s.lives = 40; s.setBallZ(100, 640, 420); strikeMiss(s.ball, performance.now()); return {{ k1, k2: rallyK(), rally: s.rally, lost: s.rallyLost, pop: s.ui.speedPop }}; }})()")
        check('a miss drops the rally back to the stage\'s base speed (x1), a grey pop with the speed that was lost', ms['k1'] > 1.4 and ms['k2'] == 1 and ms['rally'] == 0 and ms['lost']['n'] >= 10 and ms['pop'] and ms['pop']['lost'], ms)
        # the visuals scale with the speed
        vis = []
        for n in (0, 4, 8, 14):
            await page.evaluate(f"(() => {{ const s = {S}; s.rally = {n}; s.setBallZ(900, 640, 400); s.ball.speed = 0; s.lives = 40; }})()")
            await page.wait_for_timeout(80)
            vis.append(await page.evaluate(f"(() => {{ const r = {S}.ui.rally; return r ? {{ k: r.k, h: r.h, col: r.col, lines: r.lines, halo: r.halos[0] && r.halos[0].r }} : null; }})()"))
        check('at the base speed nothing extra is drawn (no clutter)', vis[0] is None, vis[0])
        c1, c2, c3 = vis[1]['col'], vis[2]['col'], vis[3]['col']
        check('the ball heats with the speed: yellowish at x1.2, orange at x1.4, blazing red-orange at the cap (blue drains, then green)', c1[2] < 200 and c1[1] > 200 and c2[1] < c1[1] and c3[1] < c2[1] and c3[0] == 255 and c3[1] < 110, [c1, c2, c3])
        check('the glow and the speed lines grow with the speed', vis[1]['halo'] < vis[2]['halo'] < vis[3]['halo'] and vis[1]['lines'] < vis[3]['lines'], vis)
        cols = await page.evaluate(f"[0, 0.33, 0.66, 1].map(h => {RL}.col(h))")
        check('the heat ramp: white -> yellow -> orange -> blazing', cols[0] == [255, 255, 255] and cols[1][2] < 120 and cols[2][1] < 170 and cols[3][1] < 90, cols)
        await page.evaluate(f"(() => {{ const s = {S}; s.rally = 14; s.setBallZ(1600, 700, 380); s.ball.speed = s.pace; }})()"); await page.wait_for_timeout(260)
        await page.screenshot(path='tests/out/frenzy_rally_en.png')
        # points: x the speed bonus on top of the combo
        pt = await page.evaluate(f"""(() => {{ const s = {S}, f = (n) => {{ s.rally = n; s.streak = 6; s.setBallZ(200, 640, 420); const s0 = s.score, m = comboMul(), k = rallyK(); strikeHit(s.ball, performance.now(), 'super', null); park(); s.heat = 0; s.hotUntil = 0; return {{ d: s.score - s0, m, k, base: 1 + STRIKE_BONUS.super }}; }};
          return [f(0), f(14)]; }})()""")
        b0, b1 = pt
        check('faster = more points: a hit at the cap pays x(1 + 0.5 x the speed-up) on top of the combo (a SUPER: its points x combo x speed)', b0['d'] == round(b0['base'] * b0['m']) and b1['d'] == round(b1['base'] * b1['m'] * (1 + 0.5 * (b1['k'] - 1))) and b1['d'] > b0['d'], pt)
        # power: a growing chance of one tier more, bounded at SUPER, no extra heat
        pw = await page.evaluate(f"""(() => {{ const s = {S}, run = (n, tier) => {{ let up = 0, sup = 0, heat = 0; for (let i = 0; i < 200; i++) {{ s.rally = n; s.setBallZ(200, 640, 420); s.heat = 0; s.hotUntil = 0; const q = slapLaunch(s.ball, performance.now(), tier, null); if (q.boost) up++; if (q.tier === 'super') sup++; if (q.heatTier !== tier) heat++; }} park(); return {{ up, sup, heat }}; }};
          return {{ base: run(0, 'medium'), fast: run(14, 'medium'), sup: run(14, 'super') }}; }})()""")
        check('slightly more power: no boost at the base speed; at the cap ~40% of medium hits go out hard; SUPER stays SUPER (bounded); the heat counts the hand\'s own tier', pw['base']['up'] == 0 and 40 <= pw['fast']['up'] <= 125 and pw['sup']['up'] == 0 and pw['sup']['sup'] == 200 and pw['fast']['heat'] == 0, pw)
        ht = await page.evaluate(f"(() => {{ const s = {S}, f = (n) => {{ s.rally = n; s.heat = 0; s.hotUntil = 0; heatHit('hard', performance.now()); return s.heat; }}; const r = [f(0), f(14)]; s.heat = 0; s.rally = 0; return r; }})()")
        check('overheat is not a second punishment for speed: a hard hit heats the hand less in a fast rally (/ the speed factor)', ht[1] < ht[0] and abs(ht[0] / ht[1] - cap) < 0.02, ht)
        nr = await page.evaluate(f"(() => {{ const s = {S}; s.noRally = true; s.rally = 0; const r = {HIT}(5); const k = rallyK(5); s.noRally = false; s.extrasOff = true; const k2 = rallyK(5); s.extrasOff = false; s.rally = 0; return {{ r, k, k2 }}; }})()")
        check('the test flag noRally (and the older suites\' extrasOff) keep the ball at its base speed', nr['r'] == [1, 1, 1, 1, 1] and nr['k'] == 1 and nr['k2'] == 1, nr)
        ad = await page.evaluate("(() => { setStrikeDiff('normal'); const a = __grasp.rally.cap(); setStrikeDiff('easy'); return a; })()")
        check('Endless on Normal: capped at +70%', abs(ad - 0.7) < 1e-9, ad)
        check('R1: no page errors', not errs, errs); await ctx.close()

        # ===== R2: Adventure caps (world 1's gentle on-ramp vs later) + the daily =====
        ctx, page, errs = await fresh(b); await stage(page, 1)
        c1 = await page.evaluate(f"{RL}.cap()")
        await page.evaluate(f"{A}.start(12)"); await page.wait_for_function(f"{A}.stage === 12 && {A}.phase === 'play'", timeout=8000)
        c12 = await page.evaluate(f"{RL}.cap()")
        r12 = await page.evaluate(f"(() => {{ {S}.noSpecials = true; {S}.noTiming = true; park(); return {HIT}(3); }})()")
        check('Adventure: world 1\'s gentle first stages cap the rally at +45%, later stages at +70%; it climbs there too', abs(c1 - 0.45) < 1e-9 and abs(c12 - 0.7) < 1e-9 and r12 == [1.05, 1.1, 1.15], [c1, c12, r12])
        await page.evaluate(f"{A}.start(12)"); await page.wait_for_function(f"{A}.stage === 12 && {A}.phase === 'play'", timeout=8000)
        check('a new stage starts the rally afresh (x1)', await page.evaluate("rallyK() === 1 && __grasp.strike.rally === 0"))
        await page.evaluate("goHome()"); await page.wait_for_timeout(200)
        await page.evaluate("__grasp.startDaily ? __grasp.startDaily() : null"); await page.wait_for_timeout(600)
        dl = await page.evaluate(f"({{ daily: daily.on, on: {RL}.on(), cap: {RL}.cap(), frenzy: frenzy.on }})")
        check('the daily has the rally too (capped), never Frenzy', dl['daily'] and dl['on'] and 0.6 <= dl['cap'] <= 0.7 and not dl['frenzy'], dl)
        check('R2: no page errors', not errs, errs); await ctx.close()

        # ===== F1: Frenzy from the map (EN) =====
        ctx, page, errs = await fresh(b)
        await page.click('.modes button[data-mode=strike]'); await page.wait_for_function("advMapOpen()", timeout=8000)
        mb = await page.evaluate("(() => { const e = $('advFrenzy'), r = e.getBoundingClientRect(), n = $('advEndless').getBoundingClientRect(); return { text: e.innerText.replace(/\\s+/g, ' ').trim(), h: r.height, inScreen: r.right <= innerWidth + 1 && r.left >= -1 && r.bottom <= innerHeight + 1, sameRow: Math.abs((r.top + r.bottom) / 2 - (n.top + n.bottom) / 2) < 30 }; })()")
        check('the map footer has a Frenzy button next to Endless ("Frenzy" / "Faster and faster!")', 'Frenzy' in mb['text'] and 'Faster and faster' in mb['text'] and mb['h'] >= 44 and mb['inScreen'] and mb['sameRow'], mb)
        await page.click('#advFrenzy'); await frenzy_start(page, click=False)
        st = await page.evaluate(f"({{ path: location.pathname, lives: {S}.lives, shield: {S}.shield, cfg: challengeCfg() === CH_NONE, up: upgLv('heart'), banner: {S}.ui.levelBanner && {S}.ui.levelBanner.frenzy, now: __grasp.route.now }})")
        check('Frenzy starts: /frenzy, one heart + a shield for the first miss, clean walls (no specials), no upgrades, the "Frenzy!" banner', st['path'] == '/frenzy' and st['lives'] == 1 and st['shield'] == 1 and st['cfg'] and st['up'] == 0 and st['banner'] and st['now'] == 'frenzy', st)
        await page.evaluate(f"{S}.noTiming = true; {S}.playerServe('medium'); park(2300); {S}.lives = 1")
        ks = await page.evaluate(f"(() => {{ const r = {HIT}(60); {S}.lives = 1; return r; }})()")
        check('Frenzy: the rally never stops climbing (small +4% steps, no cap: x3.4 after 60 hits)', ks[:3] == [1.04, 1.08, 1.12] and abs(ks[-1] - 3.4) < 1e-6 and all(ks[i] < ks[i + 1] for i in range(59)), ks[-5:])
        hb = await page.evaluate(f"(() => {{ heatHit('super', performance.now()); return {{ heat: {S}.heat, pop: {S}.ui.speedPop }}; }})()")
        check('Frenzy: no heat (the speed is the challenge); the speed pop keeps counting (x3.4 SPEED)', hb['heat'] == 0 and hb['pop'] and hb['pop']['k'] > 3, hb)
        await page.evaluate(f"(() => {{ const s = {S}; s.setBallZ(1500, 700, 380); s.ball.speed = s.pace; }})()"); await page.wait_for_timeout(200)
        hud = await page.evaluate(f"({{ pill: {S}.ui.wallsPill && {S}.ui.wallsPill.text, ring: {S}.ui.shieldRing, rally: {S}.ui.rally && {{ k: {S}.ui.rally.k, h: {S}.ui.rally.h }} }})")
        check('the HUD pill counts the hits in a row (⚡60); the heart wears the shield ring; the ball blazes', hud['pill'] and '60' in hud['pill'] and '⚡' in hud['pill'] and hud['ring'] and hud['rally']['h'] > 1, hud)
        # the first miss: the shield
        m1 = await page.evaluate(f"(() => {{ const s = {S}; s.setBallZ(100, 640, 420); strikeMiss(s.ball, performance.now()); return {{ over: s.over, lives: s.lives, shield: s.shield, rally: s.rally, k: rallyK(), fl: s.floaters.map(f => f.text) }}; }})()")
        check('the very first miss is shielded: the run goes on (still one heart), the speed drops back halfway (x2.2), "Shield!"', not m1['over'] and m1['lives'] == 1 and m1['shield'] == 0 and m1['rally'] == 30 and abs(m1['k'] - 2.2) < 1e-6 and 'Shield!' in m1['fl'], m1)
        await page.wait_for_function(f"{S}.waiting", timeout=5000)
        await page.evaluate(f"{S}.playerServe('medium'); park(2300); {S}.lives = 1")
        await page.evaluate(f"{HIT}(5)")
        m2 = await page.evaluate(f"(() => {{ const s = {S}; s.lives = 1; s.setBallZ(100, 640, 420); strikeMiss(s.ball, performance.now()); return {{ over: s.over, res: {F}.result, prof: {F}.profile, newBest: s.ui.newBest, top: s.rallyTop }}; }})()")
        r = m2['res']
        check('the next miss ends the run: 65 hits in a row, top speed x3.4, NEW RECORD! (the first run), the best saved', m2['over'] and r and r['hits'] == 65 and abs(r['top'] - 3.4) < 1e-6 and r['record'] and m2['newBest'] and m2['prof']['best'] == 65 and abs(m2['prof']['top'] - 3.4) < 1e-6 and m2['prof']['runs'] == 1, m2)
        await page.wait_for_timeout(700)
        cd = await page.evaluate(f"({{ btn: Object.keys({S}.ui.buttons || {{}}), best: {S}.ui.bestLine, ribbon: !!{S}.ui.ribbon, sfx: __sfx.includes('record') }})")
        check('the card: NEW RECORD!, the ribbon, Play again / Home / Share, the record fanfare', 'share' in cd['btn'] and 'again' in cd['btn'] and 'home' in cd['btn'] and cd['best'] == 'NEW RECORD!' and cd['ribbon'] and cd['sfx'], cd)
        await page.screenshot(path='tests/out/frenzy_card_en.png')
        sh = await page.evaluate(f"(async () => {{ try {{ Object.defineProperty(navigator, 'share', {{ configurable: true, value: undefined }}); }} catch (e) {{}} const w = []; try {{ navigator.clipboard.writeText = async (x) => {{ w.push(x); }}; }} catch (e) {{}} const r = await {F}.share(); return {{ r, text: {F}.lastShare, w }}; }})()")
        check('Share: a ready line "Grasp Frenzy ⚡ 65 hits in a row · top speed ×3.4"', sh['text'] == 'Grasp Frenzy ⚡ 65 hits in a row · top speed ×3.4', sh)
        await page.evaluate("endCardAction('again', performance.now())"); await page.wait_for_timeout(150)
        ag = await page.evaluate(f"({{ on: {F}.on, over: {S}.over, lives: {S}.lives, shield: {S}.shield, k: rallyK(), hits: {S}.hits, path: location.pathname }})")
        check('Play again: a new Frenzy run (one heart, the shield back, x1, 0 hits)', ag['on'] and not ag['over'] and ag['lives'] == 1 and ag['shield'] == 1 and ag['k'] == 1 and ag['hits'] == 0 and ag['path'] == '/frenzy', ag)
        await page.evaluate(f"{S}.noTiming = true; {S}.playerServe('medium'); park(2300); {S}.lives = 1; {S}.shield = 0")
        await page.evaluate(f"(() => {{ {HIT}(7); const s = {S}; s.lives = 1; s.shield = 0; s.setBallZ(100, 640, 420); strikeMiss(s.ball, performance.now()); }})()")
        await page.wait_for_timeout(500)
        r2 = await page.evaluate(f"({{ res: {F}.result, best: {S}.ui.bestLine, nb: {S}.ui.newBest, prof: {F}.profile }})")
        check('a shorter run: no record, "Best: 65 in a row", the best kept', not r2['res']['record'] and not r2['nb'] and r2['best'] == 'Best: 65 in a row' and r2['prof']['best'] == 65 and r2['prof']['runs'] == 2, r2)
        await page.evaluate("endCardAction('home', performance.now())"); await page.wait_for_timeout(400)
        hm = await page.evaluate(f"({{ on: {F}.on, path: location.pathname, mode }})")
        check('Home leaves Frenzy (and the address bar goes back to where the game was entered from)', not hm['on'] and hm['path'] in ('/', '/index.html') and hm['mode'] == 'none', hm)
        await page.click('.modes button[data-mode=strike]'); await page.wait_for_function("advMapOpen()", timeout=8000)
        sub = await page.evaluate("$('advFrenzySub').textContent")
        check('the map\'s Frenzy button shows the best under it ("Best: 65 in a row")', sub == 'Best: 65 in a row', sub)
        await page.click('#advEndless'); await page.wait_for_function(f"gameMode === 'strike' && mode === 'mouse' && {S}.walls.length === 4", timeout=10000)
        en = await page.evaluate(f"({{ on: {F}.on, lives: {S}.lives, path: location.pathname }})")
        check('Endless after Frenzy is the normal run again', not en['on'] and en['lives'] > 1 and en['path'] == '/strike', en)
        # the profile: validated on load
        bad = await page.evaluate("(() => { const p = JSON.parse(localStorage.getItem(PROFILE_KEY)); p.frenzy = { best: -4, top: 'x', runs: 1e12 }; localStorage.setItem(PROFILE_KEY, JSON.stringify(p)); const a = loadProfile().frenzy; p.frenzy = { best: 12.4, top: 2.345, runs: 3 }; localStorage.setItem(PROFILE_KEY, JSON.stringify(p)); const b = loadProfile().frenzy; p.frenzy = 'junk'; localStorage.setItem(PROFILE_KEY, JSON.stringify(p)); const c = loadProfile().frenzy; return { a, b, c }; })()")
        check('profile.frenzy is validated on load (bad values -> defaults; a junk field -> defaults)', bad['a']['best'] == 0 and bad['a']['top'] == 1 and bad['a']['runs'] == 1000000 and bad['b'] == {'best': 12, 'top': 2.35, 'runs': 3} and bad['c'] == {'best': 0, 'top': 1, 'runs': 0}, bad)
        check('F1: no page errors', not errs, errs); await ctx.close()

        # ===== F2: the direct link /frenzy =====
        ctx = await b.new_context(viewport={'width': 1280, 'height': 800}); page = await ctx.new_page(); await routes(page); errs = []
        page.on('pageerror', lambda e: errs.append(str(e)))
        await page.add_init_script(INIT + "localStorage.setItem('lang','en');")
        await page.goto('http://localhost:8765/frenzy'); await frenzy_start(page, click=False)
        dl = await page.evaluate(f"({{ path: location.pathname, on: {F}.on, start: $('start').hidden, map: advMapOpen(), now: __grasp.route.now, of: __grasp.route.of('/frenzy'), of2: __grasp.route.of('/frenzy/') }})")
        check('/frenzy opens Frenzy at once (no start screen, no map); route.of knows it', dl['path'] == '/frenzy' and dl['on'] and dl['start'] and not dl['map'] and dl['now'] == 'frenzy' and dl['of'] == 'frenzy' and dl['of2'] == 'frenzy', dl)
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        bk = await page.evaluate(f"({{ mode, on: {F}.on, path: location.pathname }})")
        check('Home from the direct link: the start screen at /', bk['mode'] == 'none' and not bk['on'] and bk['path'] == '/', bk)
        await page.goto('http://localhost:8765/frenzy/'); await frenzy_start(page, click=False)
        check('/frenzy/ (a trailing slash) works too', await page.evaluate(f"{F}.on"))
        check('F2: no page errors', not errs, errs); await ctx.close()

        # ===== F3: phone screenshots, EN / HE (+ 3D): the map footer and a hot fast ball =====
        for he, g3 in ((False, False), (True, False), (False, True)):
            tag = ('he' if he else 'en') + '_phone' + ('_3d' if g3 else '')
            ctx, page, errs = await fresh(b, mobile=True, he=he, gfx="{ pr: 0.2, shadows: false, auto: false }" if g3 else None)
            await page.evaluate("profile.frenzy = { best: 42, top: 2.6, runs: 5 }; saveProfile(); setInputPref('mouse')")
            await page.tap('.modes button[data-mode=strike]'); await page.wait_for_function("advMapOpen()", timeout=8000); await page.wait_for_timeout(300)
            mp = await page.evaluate("(() => { const e = $('advFrenzy').getBoundingClientRect(), n = $('advEndless').getBoundingClientRect(); return { f: [e.left, e.right, e.bottom, e.height], n: [n.left, n.right], W: innerWidth, H: innerHeight, sub: $('advFrenzySub').textContent, noX: document.documentElement.scrollWidth <= innerWidth + 1 }; })()")
            check(tag + ': the map footer fits the phone: Endless and Frenzy side by side, both inside the screen, the best under Frenzy', mp['f'][0] >= -1 and mp['f'][1] <= mp['W'] + 1 and mp['n'][0] >= -1 and mp['n'][1] <= mp['W'] + 1 and mp['f'][2] <= mp['H'] + 1 and mp['f'][3] >= 44 and mp['noX'] and ('42' in mp['sub']), mp)
            if not g3: await page.screenshot(path=f'tests/out/frenzy_map_{tag}.png')
            await page.tap('#advFrenzy'); await frenzy_start(page, click=False)
            if g3: await page.wait_for_function(f"{S}.gfx === '3d'", timeout=30000)
            await page.wait_for_timeout(2300)  # (the banner reads)
            await page.evaluate(f"(() => {{ const s = {S}; s.noTiming = true; s.playerServe('medium'); s.shield = 3; s.lives = 1; s.hits = 34; s.rally = 34; s.rallyTop = rallyK(); s.ui.speedPop = {{ t: performance.now(), k: rallyK() }}; s.setBallZ(1400, innerWidth * 0.6, innerHeight * 0.42); s.ball.speed = s.pace; }})()")
            await page.wait_for_timeout(240)
            hv = await page.evaluate(f"({{ r: {S}.ui.rally && {{ h: {S}.ui.rally.h, lines: {S}.ui.rally.lines, halos: {S}.ui.rally.halos.length }}, sb: {S}.ui.speedBox, W: innerWidth, dir: {S}.ball && {S}.ball.dir }})")
            check(tag + ': a hot fast ball (x2.4: blazing glow, embers, speed lines) and the speed pop inside the screen', hv['r'] and hv['r']['h'] > 1.5 and hv['r']['lines'] >= 30 and hv['r']['halos'] == 1 and hv['sb'] and 0 <= hv['sb']['x'] and hv['sb']['x'] + hv['sb']['w'] <= hv['W'], hv)
            await page.screenshot(path=f'tests/out/frenzy_hot_{tag}.png')
            await page.evaluate(f"(() => {{ const s = {S}; s.shield = 0; s.setBallZ(100, 180, 420); strikeMiss(s.ball, performance.now()); }})()"); await page.wait_for_timeout(700)
            fc = await page.evaluate(f"({{ over: {S}.over, card: {S}.ui.card, W: innerWidth, H: innerHeight, title: {S}.ui.titleBox, share: {S}.ui.buttons && {S}.ui.buttons.share }})")
            check(tag + ': the Frenzy card fits the phone (title, Share button inside)', fc['over'] and fc['card'] and fc['card']['x'] >= 0 and fc['card']['x'] + fc['card']['w'] <= fc['W'] and fc['share'] and fc['share']['y'] + fc['share']['h'] <= fc['H'], fc)
            if not g3: await page.screenshot(path=f'tests/out/frenzy_card_{tag}.png')
            if he:
                hs = await page.evaluate(f"({{ best: {S}.ui.bestLine, share: {F}.shareText(), btn: $('advFrenzy').innerText }})")
                check('HE: "טירוף" on the button, "שיא: 42 ברצף" on the card, a Hebrew share line', 'טירוף' in hs['btn'] and hs['best'] == 'שיא: 42 ברצף' and 'טירוף' in hs['share'] and 'ברצף' in hs['share'], hs)
            check(tag + ': no page errors', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
