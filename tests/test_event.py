exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# The weekly event: one event a week (Monday-Sunday, local time) picked from the week number (the same for everyone), a banner on the start screen,
# the event page (countdown, points, a 12-tier reward track with tap-to-claim chests, 3 event missions, the event stickers, next week's teaser),
# points from the featured game only, the gameplay twists (cows, space walls, the piñata, golden fruit, festival bubbles) for a real visitor (here
# switched on with __grasp.event.live(true)), the scarce economy (140 coins a week at most), catch-up until Sunday, exclusive items granted once,
# profile validation. Screenshots tests/out/event_*.png.
import os
OUT = 'tests/out/'; os.makedirs(OUT, exist_ok=True)
EV = '__grasp.event'
IDS = ['cows', 'space', 'smash', 'fruit', 'bubbles', 'speed']

def rects_overlap(a, b, slack=0):
    return a['l'] < b['r'] - slack and b['l'] < a['r'] - slack and a['t'] < b['b'] - slack and b['t'] < a['b'] - slack

async def fresh(b, mobile=False, he=False, date='2026-10-10', init='', live=None):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');") + (f"sessionStorage.setItem('grasp.testDate', '{date}');" if date else '') + init)
    await page.goto('http://localhost:8765/index.html')
    await page.wait_for_function("window.__grasp && __grasp.event && document.querySelector('#eventBtn .evName').textContent.length > 0", timeout=15000)
    await page.evaluate("for (const o of document.querySelectorAll('.ov')) o.hidden = true")
    if live is not None: await page.evaluate(f"{EV}.live({'true' if live else 'false'})")
    return ctx, page, errs

R = "(e) => { const q = e.getBoundingClientRect(); return { l: q.left, r: q.right, t: q.top, b: q.bottom, w: q.width, h: q.height }; }"
LAYOUT = f"""(() => {{ const r = {R}, st = $('start'), vis = (e) => e && !e.hidden && getComputedStyle(e).display !== 'none';
  const tiles = [...document.querySelectorAll('.modes > button')].map(r);
  return {{ ban: r($('eventBtn')), tiles, row: r(document.querySelector('#start .metaRow')), pill: r($('metaPill')), habit: r($('habitBar')), lang: r($('startLang')), h1: r(document.querySelector('#start h1')),
    seg: r(document.querySelector('#start .seg')), pet: r($('petCorner')), link: r(document.querySelector('#start a.link')), hint: vis($('flameHint')) ? r($('flameHint')) : null,
    noScroll: document.documentElement.scrollHeight <= innerHeight + 1 && st.scrollHeight <= st.clientHeight + 1, noX: document.documentElement.scrollWidth <= innerWidth + 1 && st.scrollWidth <= st.clientWidth + 1,
    W: innerWidth, H: innerHeight, name: document.querySelector('#eventBtn .evName').textContent, left: document.querySelector('#eventBtn .evLeft').textContent, line: document.querySelector('#eventBtn .evLine').textContent,
    fit: [...$('eventBtn').querySelectorAll('.evName, .evLine, .evLeft')].every((e) => e.getBoundingClientRect().right <= $('eventBtn').getBoundingClientRect().right + 1 && e.getBoundingClientRect().left >= $('eventBtn').getBoundingClientRect().left - 1) }}; }})()"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ---- the calendar: one event a week by the week number, Monday -> Sunday, the same for everyone; the rotation; the ISO week; the countdown ----
        ctx, page, errs = await fresh(b)
        C = await page.evaluate(f"""(() => {{ const E = {EV}, days = []; for (let i = 0; i < 7; i++) days.push(E.at(addDays('2026-10-05', i)));
          const weeks = []; for (let w = 0; w < 13; w++) weeks.push(E.at(addDays('2026-10-05', 7 * w)).id);
          return {{ days: days.map((d) => [d.id, d.wk, d.left, d.ends, d.iso]), weeks, iso: ['2026-01-01', '2021-01-03', '2026-10-10', '2024-12-30', '2027-01-03'].map((d) => E.isoWeek(d).key),
            mon: ['2026-10-05', '2026-10-08', '2026-10-11', '2026-10-12'].map(E.monday), ids: E.cfg.ids, ed: [E.at('2026-10-05').ed, E.at(addDays('2026-10-05', 42)).ed], before: E.at('2025-06-04').id,
            next: E.at('2026-10-10').next, w2: E.at('2026-10-12').id }}; }})()""")
        check('Monday to Sunday: the same event, its Monday, 7..1 days left, ends on Sunday, ISO week 2026-W41', len({d[0] for d in C['days']}) == 1 and all(d[1] == '2026-10-05' and d[3] == '2026-10-11' and d[4] == '2026-W41' for d in C['days']) and [d[2] for d in C['days']] == [7, 6, 5, 4, 3, 2, 1], C['days'])
        check('the next Monday: the next event (its teaser named in advance)', C['w2'] != C['days'][0][0] and C['w2'] == C['next'], [C['w2'], C['next']])
        check('the rotation: 6 different events in 6 weeks, then they cycle in the same order', len(set(C['weeks'][:6])) == 6 and C['weeks'][6:12] == C['weeks'][:6] and C['weeks'][12] == C['weeks'][0] and set(C['weeks'][:6]) == set(IDS), C['weeks'])
        check('ISO weeks: 2026-01-01 = W01, 2021-01-03 = 2020-W53, 2024-12-30 = 2025-W01, 2027-01-03 = 2026-W53', C['iso'] == ['2026-W01', '2020-W53', '2026-W41', '2025-W01', '2026-W53'], C['iso'])
        check('the week starts on Monday (local)', C['mon'] == ['2026-10-05', '2026-10-05', '2026-10-05', '2026-10-12'], C['mon'])
        check('editions: 6 weeks later the same event is the next edition; dates before the epoch still map to an event', C['ed'][1] == C['ed'][0] + 1 and C['before'] in IDS, C)
        # the same date in another browser (another profile) = the same event
        ctx2, page2, _ = await fresh(b, init="localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, coins: 77 }));")
        same = await page2.evaluate(f"{EV}.state.id") == await page.evaluate(f"{EV}.state.id"); await ctx2.close()
        check('deterministic: another player on the same day gets the same event', same)
        txt = await page.evaluate(f"""(() => {{ const o = []; for (const d of ['2026-10-05', '2026-10-09', '2026-10-10', '2026-10-11']) {{ __grasp.setDate(d); o.push(document.querySelector('#eventBtn .evLeft').textContent); }} return o; }})()""")
        check('the countdown on the banner follows the date: 7 days left, 3 days left, 2 days left, Last day!', txt == ['7 days left', '3 days left', '2 days left', 'Last day!'], txt)
        await page.evaluate("setLang('he')"); he = await page.evaluate("[document.querySelector('#eventBtn .evLeft').textContent, (__grasp.setDate('2026-10-07'), document.querySelector('#eventBtn .evLeft').textContent)]")
        check('the countdown in Hebrew', he == ['יום אחרון!', 'עוד 5 ימים'], he)
        await page.evaluate("setLang('en'); __grasp.setDate('2026-10-10')")
        check('calendar: no page errors', not errs, errs); await ctx.close()

        # ---- the start-screen banner: on one screen with everything else (phone + desktop, EN / HE, the flame hint showing), overlapping nothing ----
        for mobile in (True, False):
            for he in (False, True):
                tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en')
                ctx, page, errs = await fresh(b, mobile, he, init="localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, habit: { play: ['2026-10-08', '2026-10-09'] } }));")
                await page.wait_for_timeout(1500)  # (the entrance)
                L = await page.evaluate(LAYOUT)
                others = L['tiles'] + [L['row'], L['pill'], L['habit'], L['lang'], L['h1'], L['seg'], L['pet'], L['link']] + ([L['hint']] if L['hint'] else [])
                bn = L['ban']
                check(tag + ': still one screen (no scroll either way), with the flame hint showing', L['noScroll'] and L['noX'] and L['hint'] is not None, L)
                check(tag + ': the banner fully on screen, a big tile (>= 48 px tall, >= 300 px wide)', bn['l'] >= 0 and bn['r'] <= L['W'] + 0.5 and bn['t'] >= 0 and bn['b'] <= L['H'] and bn['h'] >= 48 and bn['w'] >= 300, bn)
                check(tag + ': the banner overlaps nothing (tiles, icon row, pill, top bar, wordmark, toggle, pet, link, hint)', not any(rects_overlap(bn, x, 1) for x in others), [bn, others])
                check(tag + ': its name, countdown and line fit inside it', L['fit'] and L['name'] and L['left'], L)
                if mobile: check(tag + ': between the icon row and the games', L['row']['b'] <= bn['t'] and bn['b'] <= min(t['t'] for t in L['tiles']), [L['row'], bn])
                else: check(tag + ': up in the top bar, between the wordmark and the buttons', bn['b'] <= L['pill']['t'] and bn['t'] < 20, bn)
                await page.screenshot(path=OUT + 'event_banner_%s_%s.png' % ('phone' if mobile else 'desktop', 'he' if he else 'en'))
                check(tag + ': no page errors', not errs, errs); await ctx.close()

        # ---- each event: the banner and its page (name, rule, countdown, play button, the track, missions, stickers, teaser), screenshots ----
        ctx, page, errs = await fresh(b, mobile=True)
        for i, eid in enumerate(IDS):
            await page.evaluate(f"""(() => {{ {EV}.force('{eid}'); {EV}.points({[30, 120, 230, 400, 560, 920][i]}); {EV}.claim(0); }})()""")
            ms0 = await page.evaluate(f"{EV}.cfg.by['{eid}'].ms[0]")
            await page.evaluate(f"{EV}.add('{'cow' if eid == 'cows' else 'round'}', 2); {EV}.add(__grasp.event.cfg.by['{eid}'].ms[0].k, {ms0['n']})")  # (the first mission done: its claim button lights up)
            S = await page.evaluate(f"{EV}.state")
            await page.click('#eventBtn'); await page.wait_for_function("!$('evSheet').hidden", timeout=3000); await page.wait_for_timeout(400)
            P = await page.evaluate("""(() => { const P = $('evSheet'); return { title: $('evTitle').textContent, rule: $('evRule').textContent, left: $('evLeftBig').textContent, play: $('evPlay').textContent, tiers: [...P.querySelectorAll('.evTier')].map((t) => t.dataset.st),
              ms: [...P.querySelectorAll('.evM')].map((m) => [m.querySelector('.mTx').textContent, m.className, m.querySelector('.mGo').disabled]), stk: P.querySelectorAll('.evStk').length, next: $('evNext').textContent, ec: getComputedStyle(P.querySelector('.sheet')).getPropertyValue('--ec').trim(),
              mascot: (() => { const c = $('evMascotBig'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let k = 3; k < d.length; k += 4) if (d[k] > 0) n++; return n / (c.width * c.height); })() }; })()""")
            D = await page.evaluate(f"{EV}.cfg.by['{eid}']")
            check(f'{eid}: the page shows its name, rule, countdown, a Play button, 12 tiers, 3 missions, 6 sticker slots, next week', P['title'] == S['name'] and len(P['rule']) > 20 and P['left'] == '2 days left' and P['play'].startswith('Play') and len(P['tiers']) == 12 and len(P['ms']) == 3 and P['stk'] == 6 and S['nextName'] in P['next'], P)
            check(f'{eid}: its colour accent and a drawn mascot', P['ec'].lower() == D['col'].lower() and P['mascot'] > 0.08, [P['ec'], P['mascot']])
            check(f'{eid}: the tiers: the first claimed, the reached ones ready, the rest locked', P['tiers'][0] == 'got' and all(st == ('ready' if EVENT_AT <= S['pts'] else 'locked') for st, EVENT_AT in zip(P['tiers'][1:], [60, 100, 150, 210, 280, 360, 450, 550, 660, 780, 900])), [P['tiers'], S['pts']])
            check(f'{eid}: the first mission done (its claim button on), the others not', 'done' in P['ms'][0][1] and not P['ms'][0][2] and P['ms'][1][2] and P['ms'][2][2], P['ms'])
            await page.evaluate("$('metaToast').replaceChildren()"); await page.screenshot(path=OUT + f'event_{eid}.png')
            await page.keyboard.press('Escape'); await page.wait_for_function("$('evSheet').hidden", timeout=3000)
            ban = await page.evaluate("[document.querySelector('#eventBtn').dataset.ev, document.querySelector('#eventBtn .evName').textContent, !document.querySelector('#eventBtn .dot').hidden, getComputedStyle($('eventBtn')).getPropertyValue('--ec').trim()]")
            check(f'{eid}: the banner shows it (name, accent, the red dot with rewards to claim)', ban[0] == eid and ban[1] == S['name'] and ban[2] and ban[3].lower() == D['col'].lower(), ban)
            await page.screenshot(path=OUT + f'event_{eid}_banner.png', clip={'x': 0, 'y': 0, 'width': 360, 'height': 300})
        check('pages: no page errors', not errs, errs); await ctx.close()

        # ---- points: only the featured game counts; per action; missions; claims ----
        ctx, page, errs = await fresh(b, live=False)
        await page.evaluate(f"{EV}.force('cows')")
        await page.evaluate("setGameMode('slice')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse' && gameMode === 'slice'", timeout=10000)
        q = await page.evaluate(f"(() => {{ track('wall', 3); track('fruit', 4); return {EV}.state.pts; }})()")
        check('Cow Stampede: walls / fruit in Slice score nothing (not the featured game)', q == 0, q)
        await page.evaluate("goHome()"); await page.wait_for_function("mode === 'none'", timeout=5000)
        await page.evaluate("setGameMode('strike')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse' && gameMode === 'strike' && __grasp.strike.ball", timeout=10000)
        await page.evaluate("__grasp.CONFIG.STRIKE_PU_RATE = 0; __grasp.strike.lives = 40")
        q = await page.evaluate(f"(() => {{ const p0 = {EV}.state.pts; track('wall', 3); return {EV}.state.pts - p0; }})()")
        check('Cow Stampede in Strike: 3 walls = 3 points', q == 3, q)
        PARK = """((z, x, y) => { const s = __grasp.strike, b = s.ball; const g = b.guest; s.setBallZ(z, x, y); b.guest = g; b.speed = 0; b.rot = 0; b.tumble = 0; b.trail.length = 0; s.serveAt = performance.now() + 1e9; s.lives = 40; return ballScreen(b); })"""
        await page.evaluate("__grasp.strike.guestEvery = 0; __grasp.strike.spawnGuest('cow')"); await page.evaluate(PARK + "(30, 640, 420)")
        q = await page.evaluate(f"(() => {{ const s = __grasp.strike, p0 = {EV}.state.pts, m0 = {EV}.state.ms[0]; strikeHit(s.ball, performance.now()); return [{EV}.state.pts - p0, {EV}.state.ms[0] - m0, s.guestHits]; }})()")
        check('a cow slapped (strikeHit): +8 points and the "Slap 8 cows" mission +1', q[0] == 8 and q[1] == 1 and q[2] == 1, q)
        q = await page.evaluate(f"(() => {{ const p0 = {EV}.state.pts; meta.toasts.length = 0; {EV}.roundDone(); return [{EV}.state.pts - p0, {EV}.state.ms[1], meta.toasts.map((t) => t.key)]; }})()")
        check('a finished Strike round: +10, the rounds mission +1; not live (automation): no event toast', q[0] == 10 and q[1] == 1 and 'evRoundToast' not in q[2], q)
        await page.evaluate(f"{EV}.live(true)")
        q = await page.evaluate(f"(() => {{ meta.toasts.length = 0; track('wall', 2); {EV}.roundDone(); return meta.toasts.map((t) => t.text); }})()")
        check('live: the round toast says the event and its points ("Cow Stampede: +12 points")', any('Cow Stampede: +12 points' in x for x in q), q)
        # missions: done -> claim pays its points (no coins); a max-type mission (Speed Week's best run)
        q = await page.evaluate(f"""(() => {{ const c0 = __grasp.profile.coins, s0 = {EV}.state; {EV}.add('cow', 20); const s1 = {EV}.state, pts = {EV}.claimMs(0), again = {EV}.claimMs(0), s2 = {EV}.state;
          return {{ ms: s1.ms[0], ready: s1.msReady, pts, again, d: s2.pts - s1.pts, mc: s2.mc[0], coins: __grasp.profile.coins - c0, notDone: {EV}.claimMs(2) }}; }})()""")
        check('a mission past its goal is capped (8/8) and ready; claiming pays +40 points once, no coins; an unfinished one pays nothing', q['ms'] == 8 and 0 in q['ready'] and q['pts'] == 40 and q['again'] == 0 and q['d'] == 40 + 0 and q['mc'] and q['coins'] == 0 and q['notDone'] == 0, q)
        await page.evaluate("goHome()"); await page.wait_for_function("mode === 'none'", timeout=5000)
        await page.evaluate(f"{EV}.force('speed')")
        await page.evaluate("strikeFrenzy('mouse')"); await page.wait_for_function("mode === 'mouse' && frenzy.on && __grasp.strike.ball", timeout=10000)
        q = await page.evaluate(f"(() => {{ const p0 = {EV}.state.pts; for (let i = 0; i < 12; i++) rallyUp(performance.now()); const s = {EV}.state; return [s.pts - p0, s.ms[0], s.ms[1]]; }})()")
        check('Speed Week in Frenzy: 12 hits = 12 + 5 (10 in a row) points; hits mission 12, best-in-a-row mission 12 (the best, not a sum)', q == [17, 12, 12], q)
        q = await page.evaluate(f"(() => {{ __grasp.strike.rally = 0; for (let i = 0; i < 3; i++) rallyUp(performance.now()); return {EV}.state.ms[1]; }})()")
        check('a shorter run later keeps the best (12)', q == 12, q)
        check('points: no page errors', not errs, errs); await ctx.close()

        # ---- the gameplay twists (live): cows everywhere, space walls, the piñata, golden fruit, festival bubbles ----
        ctx, page, errs = await fresh(b, live=True)
        await page.evaluate(f"{EV}.force('cows')"); await page.evaluate("setGameMode('strike')"); await page.evaluate(START_MOUSE)
        await page.wait_for_function("mode === 'mouse' && gameMode === 'strike' && __grasp.strike.ball", timeout=10000)
        q = await page.evaluate("(() => { const s = __grasp.strike, out = []; for (let i = 0; i < 12; i++) { guestRoll(); out.push([s.guestQ && s.guestQ.kind, s.guestQ && s.guestQ.at - s.pitches]); } return { on: guestsOn(), level: s.level, out }; })()")
        check('Cow Stampede (live): guests from level 1, always a cow, every 2-3 serves', q['on'] and q['level'] == 1 and all(k == 'cow' and n in (2, 3) for k, n in q['out']), q)
        await page.evaluate("__grasp.strike.guestEvery = 0; __grasp.strike.spawnGuest('cow')"); await page.evaluate(PARK + "(380, 180, 470)"); await page.wait_for_timeout(250)
        await page.screenshot(path=OUT + 'event_cows_play.png')
        await page.evaluate(f"{EV}.live(false)"); q = await page.evaluate("(() => { __grasp.strike.guestEvery = null; return guestsOn(); })()")
        check('not live (or another week): no guests at level 1 (the normal road)', q is False, q)
        await page.evaluate(f"{EV}.live(true); goHome()"); await page.wait_for_function("mode === 'none'", timeout=5000)
        # Space Weekend: space walls in a world-1 Adventure stage; advPlan itself stays pure
        await page.evaluate(f"{EV}.force('space')")
        q = await page.evaluate(f"(() => {{ const a = advPlan(4), e = {EV}.plan(4), b = advPlan(4); return {{ a: a.kinds, e: e.kinds, b: b.kinds, n: e.n, walls: e.walls, boss: {EV}.plan(8).kinds, w6: {EV}.plan(41).kinds.join() === advPlan(41).kinds.join() }}; }})()")
        check('Space Weekend: a world-1 stage gets asteroid / force walls (same wall count, the first wall still plain); advPlan is untouched', any(k in ('asteroid', 'force') for k in q['e']) and q['a'] == q['b'] and not any(k in ('asteroid', 'force') for k in q['a']) and len(q['e']) == len(q['a']) and q['e'][0] == 'brick' and q['w6'], q)
        await page.evaluate("profile.adv.unlocked = 8; __grasp.adventure.start(4, 'mouse')"); await page.wait_for_function("mode === 'mouse' && __grasp.adventure.on && __grasp.adventure.plan", timeout=10000)
        q = await page.evaluate("(() => { const P = adv.plan; return { space: !!P.evSpace, kinds: P.kinds }; })()")
        check('the stage plays the space plan', q['space'] and any(k in ('asteroid', 'force') for k in q['kinds']), q)
        q = await page.evaluate(f"""(() => {{ const p0 = {EV}.state.pts; track('wall', 1); evAct('spacewall'); const p1 = {EV}.state.pts; adv.lost = 0; const r = advClear(performance.now()); return {{ wall: p1 - p0, clear: {EV}.state.pts - p1, stars: r && r.stars, sticker: r && r.sticker, ms: {EV}.state.ms }}; }})()""")
        check('Space Weekend points: a wall 2 + a space wall 2 more; a 3-star first clear = 5 + 15 (stars) + 30 (a new sticker, double) + 10 (the round)', q['wall'] == 4 and q['clear'] == 60 and q['stars'] == 3 and q['sticker'] == 4, q)
        check('Space Weekend missions: 1 clear, 1 space wall, 1 three-star stage', q['ms'] == [1, 1, 1], q['ms'])
        await page.evaluate("goHome()"); await page.wait_for_function("mode === 'none'", timeout=5000)
        # Smash Mania: the boss is the piñata, beating it = 40
        await page.evaluate(f"{EV}.force('smash')"); await page.evaluate("setGameMode('smash')"); await page.evaluate(START_MOUSE)
        await page.wait_for_function("mode === 'mouse' && gameMode === 'smash' && __grasp.smash.objs.length > 0", timeout=10000)
        q = await page.evaluate(f"(() => {{ const p0 = {EV}.state.pts; track('smash', 10); return {EV}.state.pts - p0; }})()")
        check('Smash Mania: 10 things smashed = 3 points (0.3 each, the fraction carried)', q == 3, q)
        await page.evaluate("__grasp.sm.toBoss()"); await page.wait_for_function("__grasp.smash.boss && __grasp.smash.phase === 'play'", timeout=10000); await page.wait_for_timeout(300)
        q = await page.evaluate("[__grasp.smash.boss.extra.kind, __grasp.smash.tag && __grasp.smash.tag.text]")
        check('Smash Mania: the scene\'s boss is the event piñata ("Piñata time!")', q == ['pinata', 'Piñata time!'], q)
        await page.evaluate("$('metaToast').replaceChildren()"); await page.screenshot(path=OUT + 'event_smash_pinata.png')
        q = await page.evaluate(f"(() => {{ const p0 = {EV}.state.pts; smBossDown(__grasp.smash.boss, performance.now()); return [{EV}.state.pts - p0, {EV}.state.ms[1]]; }})()")
        check('the piñata down: +40 points, the piñata mission +1', q == [40, 1], q)
        await page.evaluate("goHome()"); await page.wait_for_function("mode === 'none'", timeout=5000)
        # Fruit Frenzy: golden fruit in Slice (about 1 in 6), +5 score, 1 + 10 points
        await page.evaluate(f"{EV}.force('fruit')"); await page.evaluate("setGameMode('slice')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse' && gameMode === 'slice'", timeout=10000)
        q = await page.evaluate("(() => { const s = __grasp.slice; let n = 0, g = 0; for (let i = 0; i < 150; i++) { s.fruits.length = 0; spawnWave(performance.now()); for (const f of s.fruits) if (!f.bomb) { n++; if (f.gold) g++; } } s.fruits.length = 0; return [n, g]; })()")
        check('Fruit Frenzy: some golden fruit (about 18%)', q[0] > 100 and 0.06 < q[1] / q[0] < 0.35, q)
        await page.evaluate("(() => { const s = __grasp.slice, now = performance.now(), r = sliceScale().r; s.nextSpawn = now + 1e9; s.fruits.length = 0; s.fruits.push({ x: innerWidth * 0.5, y: innerHeight * 0.45, vx: 0, vy: -0.05, r, rot: 0, vr: 0, kind: FRUITS[0], bomb: false, born: now, gold: true }, { x: innerWidth * 0.25, y: innerHeight * 0.4, vx: 0, vy: -0.05, r, rot: 0, vr: 0, kind: FRUITS[1], bomb: false, born: now, gold: false }); })()")
        await page.wait_for_timeout(700); await page.evaluate("$('metaToast').replaceChildren()"); await page.screenshot(path=OUT + 'event_fruit_play.png')
        q = await page.evaluate(f"(() => {{ const s = __grasp.slice, f = s.fruits.find((x) => x.gold), sc0 = s.score, p0 = {EV}.state.pts; s.fruits.splice(s.fruits.indexOf(f), 1); cutFruit(f, 1, 0, performance.now()); return [s.score - sc0, {EV}.state.pts - p0, {EV}.state.ms[1]]; }})()")
        check('a golden fruit cut: +5 score, 1 + 10 event points, the golden mission +1', q == [5, 11, 1], q)
        await page.evaluate(f"{EV}.live(false)")
        q = await page.evaluate("(() => { const s = __grasp.slice; let g = 0; for (let i = 0; i < 40; i++) { s.fruits.length = 0; spawnWave(performance.now()); g += s.fruits.filter((f) => f.gold).length; } s.fruits.length = 0; return g; })()")
        check('not live: no golden fruit', q == 0, q)
        await page.evaluate(f"{EV}.live(true); goHome()"); await page.wait_for_function("mode === 'none'", timeout=5000)
        # Bubble Festival: festival bubbles (+3, 8 points + half a point a pop)
        await page.evaluate(f"{EV}.force('bubbles')"); await page.evaluate("camg.touchOk = true; cgStart('bubbles', 'mouse')"); await page.wait_for_function("mode === 'mouse' && gameMode === 'bubbles'", timeout=10000)
        q = await page.evaluate("(() => { let n = 0; for (let i = 0; i < 300; i++) { const b = bubbleSpawn(performance.now(), { y: innerHeight + 200 }); if (b.ev) n++; } bubbles.list.length = 0; return n; })()")
        check('Bubble Festival: festival bubbles among the others (about 1 in 7)', 15 < q < 90, q)
        await page.evaluate("__grasp.cg.spawnBubble({ x: innerWidth * 0.5, y: innerHeight * 0.5, vy: 0, amp: 0, ev: true, r: 44 }); __grasp.cg.spawnBubble({ x: innerWidth * 0.3, y: innerHeight * 0.3, vy: 0, amp: 0, r: 30 })")
        await page.wait_for_timeout(700); await page.evaluate("$('metaToast').replaceChildren()"); await page.screenshot(path=OUT + 'event_bubbles_play.png')
        q = await page.evaluate(f"(() => {{ const B = bubbles, b = B.list.find((x) => x.ev), s0 = B.score, p0 = {EV}.state.pts; B.list.splice(B.list.indexOf(b), 1); bubblePop(b, performance.now()); return [B.score - s0, {EV}.state.pts - p0, {EV}.state.ms[1]]; }})()")
        check('a festival bubble popped: +3 score, 8 event points (+ the half point carried), the festival mission +1', q[0] == 3 and q[1] in (8, 9) and q[2] == 1, q)
        check('twists: no page errors', not errs, errs); await ctx.close()

        # ---- the reward track: thresholds, tap to claim (a chest opens), each once, the scarce economy, catch-up until Sunday, exclusives once ----
        ctx, page, errs = await fresh(b, mobile=True, init="localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, pet: { hatched: true, food: 12, pantry: 0, born: '2026-10-01', last: '2026-10-09', seen: 2 } }));")
        await page.evaluate(f"{EV}.force('cows')")
        q = await page.evaluate(f"(() => {{ {EV}.points(24); const a = {EV}.claim(0); {EV}.points(25); const b = {EV}.claim(0), c = {EV}.claim(0); return [a, b, c, {EV}.state.got]; }})()")
        check('a tier below its points cannot be claimed; at 25 the first pays 10 coins once', q[0] is None and q[1] == {'coins': 10, 'chest': False} and q[2] is None and q[3] == [0], q)
        await page.evaluate(f"{EV}.points(300)"); await page.click('#eventBtn'); await page.wait_for_function("!$('evSheet').hidden", timeout=3000); await page.wait_for_timeout(300)
        vis = await page.evaluate("(() => { const t = $('evTrack'), r = t.getBoundingClientRect(), e = t.querySelector('.evTier[data-i=\"1\"]').getBoundingClientRect(); return e.left >= r.left - 1 && e.right <= r.right + 1; })()")
        check('the strip opens on the first tier to claim', vis)
        c0 = await page.evaluate("[__grasp.profile.coins, __grasp.pet.p.pantry]")
        await page.click('.evTier[data-i="1"]')
        await page.wait_for_function("document.querySelector('.evTier[data-i=\"1\"]').classList.contains('opening')", timeout=2000)
        await page.wait_for_timeout(120); await page.screenshot(path=OUT + 'event_claim_open.png')
        await page.wait_for_function("document.querySelectorAll('.gfly').length > 0 && document.querySelectorAll('#evSheet .cf').length > 0", timeout=3000)
        await page.screenshot(path=OUT + 'event_claim_fly.png')
        await page.wait_for_function("document.querySelector('.evTier[data-i=\"1\"]').dataset.st === 'got'", timeout=3000)
        c1 = await page.evaluate("[__grasp.profile.coins, __grasp.pet.p.pantry]")
        check('tapping a ready tier: the chest shakes, confetti and snacks fly, then it shows its prize with a check (+2 snacks in the pet\'s box)', c1[1] - c0[1] == 2 and c1[0] == c0[0], [c0, c1])
        await page.click('.evTier[data-i="3"]'); await page.wait_for_function("document.querySelector('.evTier[data-i=\"3\"]').dataset.st === 'got'", timeout=3000)
        q = await page.evaluate("[__grasp.event.x.stickers, document.querySelector('.evStk[data-ev=cows]').classList.contains('got')]")
        check('the sticker tier: the Stampede Cow sticker, on the shelf', q[0] == ['cows'] and q[1], q)
        await page.click('.evTier[data-i="11"]'); await page.wait_for_timeout(200)
        q = await page.evaluate("[document.querySelector('.evTier[data-i=\"11\"]').dataset.st, __grasp.event.state.got.includes(11)]")
        check('a locked tier (900) does nothing but shake', q == ['locked', False], q)
        # catch-up: the rest stays claimable until Sunday; Monday it is gone
        await page.evaluate("__grasp.setDate('2026-10-11')")
        q = await page.evaluate(f"[{EV}.state.claimable, {EV}.state.countdown]")
        check('catch-up: on the last day the reached tiers are still waiting (2, 4, 5)', q[0] == [2, 4, 5] and q[1] == 'Last day!', q)
        q = await page.evaluate(f"(() => {{ const c0 = __grasp.profile.coins; {EV}.claim(2); {EV}.claim(5); return __grasp.profile.coins - c0; }})()")
        check('claimed on Sunday: 15 + 20 coins', q == 35, q)
        await page.evaluate(f"{EV}.force(null); __grasp.setDate('2026-10-12')")
        q = await page.evaluate(f"{EV}.state")
        check('next Monday: the next event, a fresh track (0 points, nothing to claim: last week\'s leftovers are gone)', q['id'] != 'cows' and q['pts'] == 0 and q['got'] == [] and q['claimable'] == [] and q['left'] == 7, q)
        await page.evaluate(f"__grasp.setDate('2026-10-10'); {EV}.force('cows')")
        # the whole track: <= 150 coins, snacks, the hat, the edition ball; exclusives once (the next edition: snacks instead, a new ball)
        q = await page.evaluate(f"""(() => {{ const T = {EV}.cfg.track, coins = T.reduce((a, t) => a + (t.coins || 0), 0); const c0 = __grasp.profile.coins, s0 = __grasp.pet.p.pantry;
          {EV}.points(900); for (let i = 0; i < 12; i++) {{ {EV}.claim(i); {EV}.claimMs(0); }} const st = {EV}.state;
          return {{ coins, earned: __grasp.profile.coins - c0, snacks: __grasp.pet.p.pantry - s0, x: JSON.parse(JSON.stringify({EV}.x)), done: st.done, ed: st.ed, ball: __grasp.profile.unlocked.filter((u) => u.startsWith('evb_')), item: ITEMS.find((i) => i.id === 'evb_cows_' + st.ed) }}; }})()""")
        check('the economy: the track holds 140 coins a week (<= 150), missions pay only points', q['coins'] == 140 and q['coins'] <= 150, q)
        check('a whole week claimed: exactly 140 coins, 2 + 3 + 4 snacks (+3 for the sticker already won), the cowboy hat, the edition ball as a Shop item', q['done'] and q['earned'] == 140 and q['snacks'] == 12 and q['x']['hats'] == ['cowboy'] and q['ball'] == ['evb_cows_%d' % q['ed']] and q['item'] and q['item']['type'] == 'ball', q)
        ed1 = q['ed']
        await page.evaluate("__grasp.setDate('2026-11-16')")  # six weeks later: Cow Stampede again, the next edition
        q = await page.evaluate(f"""(() => {{ const s = {EV}.state, s0 = __grasp.pet.p.pantry; {EV}.points(900); const p3 = {EV}.prize(3), p6 = {EV}.prize(6), p11 = {EV}.prize(11); for (let i = 0; i < 12; i++) {{ if (i !== 3) {EV}.claim(i); }} const a = __grasp.pet.p.pantry; {EV}.claim(3);
          return {{ id: s.id, ed: s.ed, p3, p6, p11, dup: __grasp.pet.p.pantry - a, x: JSON.parse(JSON.stringify({EV}.x)), balls: __grasp.profile.unlocked.filter((u) => u.startsWith('evb_')) }}; }})()""")
        check('six weeks later the same event, the next edition', q['id'] == 'cows' and q['ed'] == ed1 + 1, q)
        check('exclusives once: the sticker and the hat already owned turn into 3 snacks; the new edition ball is new', q['p3'] == {'snacks': 3, 'dup': 'sticker'} and q['p6'] == {'snacks': 3, 'dup': 'hat'} and q['p11']['ball'] == 'cows_%d' % q['ed'] and len(q['balls']) == 2 and q['x']['stickers'] == ['cows'] and q['x']['hats'] == ['cowboy'], q)
        # the hat in the wardrobe, the ball in the Shop
        await page.evaluate(f"{EV}.close(); __grasp.setDate('2026-10-10'); {EV}.force('cows')")
        await page.click('#petInfoBtn'); await page.wait_for_function("!$('petRoom').hidden", timeout=3000)
        await page.click('#petItems .pitem[data-id=cowboy]'); hat = await page.evaluate("__grasp.pet.p.head")
        check('the cowboy hat shows in the wardrobe and the pet wears it', hat == 'cowboy', hat)
        await page.wait_for_timeout(300); await page.screenshot(path=OUT + 'event_pet_hat.png')
        await page.keyboard.press('Escape'); await page.wait_for_function("$('petRoom').hidden", timeout=3000)
        await page.click('#collectionBtn'); await page.wait_for_function("!$('collection').hidden", timeout=3000)
        q = await page.evaluate("(() => { const t = [...document.querySelectorAll('#ctypes .tile')].filter((x) => x.dataset.id.startsWith('evb_')); return t.map((x) => [x.dataset.id, x.className, x.querySelector('.nm').textContent]); })()")
        check('the Shop: both edition balls owned (Equip), named "Cow Stampede ball #n"', len(q) == 2 and all('locked' not in c and n.startswith('Cow Stampede ball #') for _, c, n in q), q)
        await page.click('#ctypes .tile[data-id="%s"]' % q[0][0]); eq = await page.evaluate("__grasp.profile.equipped.ball")
        check('equipping an edition ball', eq.startswith('ev_cows_'), eq)
        await page.evaluate("document.querySelector('#ctypes .tile[data-id^=evb_]').scrollIntoView({ block: 'center' })"); await page.wait_for_timeout(150)
        await page.screenshot(path=OUT + 'event_shop_ball.png')
        check('track: no page errors', not errs, errs); await ctx.close()

        # ---- the profile: validated on load; what was won survives a reload; a hat not owned cannot be worn ----
        ctx, page, errs = await fresh(b)
        q = await page.evaluate(f"""(() => {{ const V = {EV}.validate, X = {EV}.validateX;
          return {{ junk: [V(null), V('x'), V([1]), V({{ wk: 'monday', id: 'cows' }}), V({{ wk: '2026-10-05', id: 'pirates' }})],
            good: V({{ wk: '2026-10-05', id: 'cows', pts: 230.7, got: [0, 1, 1, 4, 5, 99, -1, 'x'], ms: [3, 999, -4], mc: [true, true, 'yes'], seen: 1 }}),
            x: X({{ stickers: ['cows', 'cows', 'nope', 3], hats: ['cowboy', 'crown', 'viking'], balls: ['cows_3', 'cows_0', 'x_2', 'speed_12', '../a', 'space_99999'] }}), xj: X('junk') }}; }})()""")
        d0 = {'wk': '', 'id': '', 'pts': 0, 'got': [], 'ms': [0, 0, 0], 'mc': [False, False, False], 'seen': False}
        check('junk, a bad week or an unknown event: the default state', all(x == d0 for x in q['junk']), q['junk'])
        g = q['good']
        check('a good state kept and clamped: points floored, claimed tiers only reached ones (no dupes), missions capped, claimed only when done, seen a boolean', g['pts'] == 230 and g['got'] == [0, 1, 4] and g['ms'] == [3, 4, 0] and g['mc'] == [False, True, False] and g['seen'] is False, g)
        check('the prizes kept for good: only known stickers / event hats / well-formed edition balls', q['x'] == {'stickers': ['cows'], 'hats': ['cowboy', 'viking'], 'balls': ['cows_3', 'speed_12']} and q['xj'] == {'stickers': [], 'hats': [], 'balls': []}, q['x'])
        await page.evaluate("""localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, unlocked: ['ball_classic', 'evb_cows_3', 'evb_space_2'], equipped: { ball: 'ev_cows_3' }, evx: { stickers: ['space'], hats: ['antenna'], balls: ['cows_3'] },
          event: { wk: '2026-10-05', id: 'fruit', pts: 70, got: [0], ms: [2, 0, 0], mc: [false, false, false], seen: true }, pet: { hatched: true, food: 3, born: '2026-10-01', head: 'antenna' } }))""")
        await page.reload(); await page.wait_for_function("window.__grasp && __grasp.event", timeout=15000)
        q = await page.evaluate(f"[__grasp.profile.unlocked.filter((u) => u.startsWith('evb_')), __grasp.profile.equipped.ball, {EV}.x, __grasp.pet.p.head, {EV}.state.pts, {EV}.state.got]")
        check('reload: an owned edition ball stays (an unlisted one is dropped), still equipped; the hat owned is worn; this week\'s points kept', q[0] == ['evb_cows_3'] and q[1] == 'ev_cows_3' and q[2]['hats'] == ['antenna'] and q[3] == 'antenna' and q[4] == 70 and q[5] == [0], q)
        await page.evaluate("""localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, pet: { hatched: true, food: 3, born: '2026-10-01', head: 'viking' } }))"""); await page.reload(); await page.wait_for_function("window.__grasp && __grasp.event", timeout=15000)
        q = await page.evaluate("[__grasp.pet.p.head, __grasp.pet.equip('head', 'viking'), [...document.querySelectorAll('#petItems .pitem')].map((x) => x.dataset.id)]")
        check('a hat not won: not worn, cannot be put on, not in the wardrobe', q[0] == '' and q[1] is False and 'viking' not in q[2], q)
        check('profile: no page errors', not errs, errs); await ctx.close()

        # ---- the banner opens the page (tap), Escape / X / backdrop close it, Play starts the featured game; rewards to claim light the banner ----
        ctx, page, errs = await fresh(b, mobile=True, he=True)
        await page.evaluate(f"{EV}.force('fruit'); {EV}.points(0)")
        q = await page.evaluate("[$('eventBtn').classList.contains('fresh'), document.querySelector('#eventBtn .dot').hidden]")
        check('a new week: the banner shines (not seen yet), no dot with nothing to claim', q == [True, True], q)
        await page.tap('#eventBtn'); await page.wait_for_function("!$('evSheet').hidden", timeout=3000)
        q = await page.evaluate(f"[{EV}.state.seen, $('eventBtn').classList.contains('fresh'), document.documentElement.dir, $('evTitle').textContent, $('evPlay').textContent]")
        check('tapped: the page opens (RTL, Hebrew), the shine stops', q[0] and not q[1] and q[2] == 'rtl' and q[3] == 'טירוף פירות' and q[4] == 'לשחק בחיתוך', q)
        f0 = await page.evaluate(f"{EV}.frames"); await page.wait_for_timeout(400); f1 = await page.evaluate(f"{EV}.frames")
        check('the big mascot animates while the page is open', f1 > f0, [f0, f1])
        await page.screenshot(path=OUT + 'event_page_he.png')
        await page.tap('#evSheet .xBtn'); await page.wait_for_function("$('evSheet').hidden", timeout=3000)
        f2 = await page.evaluate(f"{EV}.frames"); await page.wait_for_timeout(300)
        check('X closes it; the mascot loop stops', await page.evaluate(f"{EV}.frames") == f2)
        await page.tap('#eventBtn'); await page.wait_for_function("!$('evSheet').hidden", timeout=3000)
        await page.mouse.click(5, 735); await page.wait_for_function("$('evSheet').hidden", timeout=3000)
        check('a tap on the backdrop closes it', True)
        await page.evaluate(f"{EV}.points(130)")
        q = await page.evaluate("[document.querySelector('#eventBtn .dot').hidden, $('eventBtn').classList.contains('ready'), document.querySelector('#eventBtn .evLine').textContent, document.querySelector('#eventBtn .evPts').textContent]")
        check('rewards waiting: the red dot, the glow, "Rewards to claim: 3" (HE), points to the next tier', q[0] is False and q[1] and q[2] == 'פרסים לאסוף: 3' and q[3] == '130/150', q)
        await page.tap('#eventBtn'); await page.wait_for_function("!$('evSheet').hidden", timeout=3000); await page.tap('#evPlay')
        await page.wait_for_function("mode === 'mouse' && gameMode === 'slice'", timeout=10000)
        check('Play: the page closes and Slice starts', await page.evaluate("$('evSheet').hidden && $('start').hidden"))
        await page.evaluate("goHome()"); await page.wait_for_function("mode === 'none'", timeout=5000)
        await page.evaluate(f"{EV}.force('speed')"); await page.tap('#eventBtn'); await page.wait_for_function("!$('evSheet').hidden", timeout=3000); await page.tap('#evPlay')
        await page.wait_for_function("mode === 'mouse' && frenzy.on", timeout=10000)
        check('Speed Week\'s Play starts Frenzy', True)
        await page.evaluate("goHome()"); await page.wait_for_function("mode === 'none'", timeout=5000)
        await page.evaluate(f"{EV}.force('bubbles')"); await page.tap('#eventBtn'); await page.wait_for_function("!$('evSheet').hidden", timeout=3000); await page.tap('#evPlay')
        await page.wait_for_function("gameMode === 'bubbles' && mode !== 'none'", timeout=10000)
        check('Bubble Festival\'s Play starts Bubble Pop', True)
        # all done: the banner teases next week
        await page.evaluate("goHome()"); await page.wait_for_function("mode === 'none'", timeout=5000)
        await page.evaluate(f"(() => {{ {EV}.force('cows'); setLang('en'); {EV}.points(900); for (let i = 0; i < 12; i++) {EV}.claim(i); }})()")
        q = await page.evaluate("document.querySelector('#eventBtn .evLine').textContent")
        check('everything claimed: the banner says "All done! Next week: Space Weekend"', q == 'All done! Next week: Space Weekend', q)
        check('ui: no page errors', not errs, errs); await ctx.close()

        await b.close()
    srv.terminate()
    print('\n' + ('ALL PASS' if check.fails == 0 else f'{check.fails} FAILED'))
    sys.exit(1 if check.fails else 0)

asyncio.run(main())
