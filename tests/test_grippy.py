exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Step 4: Grippy the commentator (lines per event in EN / HE, no immediate repeat, one line per 4 s except the important ones, the on / off toggle),
# the end card's "One more?" teaser (nearest goal for crafted profiles) and its pulsing Play again, and toasts that never cover a round-over card.
# Timing-independent: rounds end by parking the ball behind the player (or dropping fruit / calling the life loss) and polling for the state.
G = "__grasp.grippy"; S = "__grasp.strike"
SFX_JS = "(() => { window.__sfx = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); o(k, a); }; })()"
DATE = '2026-10-02'
ALL_CHEAP = ['ball_beach', 'ball_soccer', 'hand_mint', 'hand_sky', 'hand_lilac', 'hand_robot', 'blade_neon', 'blade_rainbow', 'trail_sparkle', 'trail_fire']

def prof(coins=0, xp=0, unlocked=(), missions=None):
    p = {'v': 1, 'coins': coins, 'xp': xp, 'unlocked': list(unlocked)}
    if missions is not None: p['missions'] = {'date': DATE, 'list': [dict(id=i, progress=pr, goal=g, reward=20, done=False, claimed=False) for i, pr, g in missions]}
    return "localStorage.setItem('grasp.profile', " + json.dumps(json.dumps(p)) + ");"

async def fresh(b, mobile=False, he=False, init=''):
    opts = dict(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width':1280,'height':800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + "localStorage.setItem('lang','" + ('he' if he else 'en') + "'); sessionStorage.setItem('grasp.testDate','" + DATE + "');" + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(700)
    return ctx, page, errs
async def play(page, m, mobile=False):
    await page.evaluate("__grasp.setGameMode('" + m + "')")
    if mobile: await page.tap('#mouseBtn')
    else: await page.click('#mouseBtn')
    await page.wait_for_function("mode === 'mouse'", timeout=8000); await page.evaluate(SFX_JS)
async def end_strike(page, score=0, lives=1):
    await page.evaluate(f"(() => {{ const s = {S}; s.score = {score}; s.lives = {lives}; s.setBallZ(-500); }})()")
    await page.wait_for_function(f"{S}.over && {S}.ui.card && performance.now() - {S}.overAt > 450", timeout=8000)
async def end_slice(page, score=0):
    await page.evaluate(f"(() => {{ const s = __grasp.slice; s.score = {score}; s.nextSpawn = 1e12; s.fruits.length = 0; s.lives = 1; sliceLoseLife(performance.now()); }})()")
    await page.wait_for_function("__grasp.slice.over && __grasp.slice.ui.card && performance.now() - __grasp.slice.overAt > 450", timeout=8000)
def inter(a, b):  # overlap area of two {x, y, w, h} boxes
    return max(0, min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x'])) * max(0, min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']))

# samples every frame until no toast is left: each visible toast's rect against the end card's, the toolbar's, and how many show at once
SAMPLER = """(E => new Promise((done) => { const out = { n: 0, maxOver: 0, maxBar: 0, maxAtOnce: 0, texts: new Set(), oneLine: true, inside: true, frames: 0 }, t0 = performance.now();
  const bar = document.querySelector('.chrome').getBoundingClientRect();
  (function smp() { const c = E().ui.card, live = [...document.querySelectorAll('#metaToast .mt')].filter(e => !e.classList.contains('wait') && e.getBoundingClientRect().height > 0);
    out.frames++; out.maxAtOnce = Math.max(out.maxAtOnce, live.length);
    for (const e of live) { const r = e.getBoundingClientRect(), ov = (a, b) => Math.max(0, Math.min(a.right, b.x + b.w) - Math.max(a.left, b.x)) * Math.max(0, Math.min(a.bottom, b.y + b.h) - Math.max(a.top, b.y));
      out.texts.add(e.querySelector('.tx').textContent); out.maxOver = Math.max(out.maxOver, ov(r, c)); out.maxBar = Math.max(out.maxBar, ov(r, { x: bar.left, y: bar.top, w: bar.width, h: bar.height }));
      if (r.height > 40) out.oneLine = false; if (r.left < 0 || r.right > innerWidth || r.top < 0) out.inside = false; out.card = c; out.last = { x: r.left, y: r.top, w: r.width, h: r.height }; }
    if (!document.querySelector('#metaToast .mt') || performance.now() - t0 > 20000) { out.texts = [...out.texts]; done(out); } else requestAnimationFrame(smp); })(); }))"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])

        # ---- the lines: >= 6 per event, EN and HE, non-empty, translated ----
        ctx, page, errs = await fresh(b)
        ln = await page.evaluate(G + ".lines")
        evs = await page.evaluate(G + ".events")
        need = ['start', 'daily', 'firstHit', 'combo', 'streak5', 'streak10', 'super', 'close', 'boss', 'bossDown', 'levelUp', 'pu_multi', 'pu_big', 'pu_slow', 'pu_fire', 'pu_life', 'miss', 'lastLife', 'newBest', 'mission']
        check('Grippy has lines for every event (power-ups per kind)', set(need) <= set(evs) and set(evs) == set(ln['he']), evs)
        bad = [e + ':' + l for e in need for l in ('en', 'he') if len(ln[l][e]) < 6 or any(not x.strip() or len(x) > 48 for x in ln[l][e]) or len(set(ln[l][e])) != len(ln[l][e])]
        check('>= 6 distinct, short, non-empty lines per event in EN and HE', not bad, bad)
        heb = [e for e in need if any(x in ln['en'][e] for x in ln['he'][e]) or not all(re.search('[֐-׿]', x) for x in ln['he'][e])]
        check('HE lines are Hebrew and differ from the EN ones', not heb, heb)
        check('daily lines mention the modifier ({mod})', all('{mod}' in x for l in ('en', 'he') for x in ln[l]['daily']))
        check('the start screen: no Grippy, say() does nothing', await page.evaluate(G + ".say('start')") is False and not await page.evaluate(G + ".visible"))

        # ---- in a Strike round: appears on round start, a line for each event, no repeat, rate limit ----
        await play(page, 'strike')
        await page.wait_for_function(G + ".visible && " + G + ".last && " + G + ".last.event === 'start'", timeout=5000)
        st = await page.evaluate(G + ".last")
        check('round start: Grippy pops up with a start line', st['text'] in ln['en']['start'] and await page.evaluate(G + ".on"), st)
        bx = await page.evaluate(G + ".box()")
        check('desktop: the mascot at the bottom start corner, inside the screen', bx and bx['x'] <= 16 and bx['y'] + bx['h'] <= 800 and bx['mascot']['w'] >= 50 and bx['bubble']['x'] > bx['mascot']['x'], bx)
        await page.screenshot(path='tests/out/grippy_desktop_start.png')
        said = await page.evaluate("(evs => evs.map(e => { __grasp.grippy.cool(); const ok = __grasp.grippy.say(e); return [e, ok, __grasp.grippy.last.event, __grasp.grippy.last.text]; }))(" + json.dumps(need) + ")")
        badsay = [x for x in said if not x[1] or x[2] != x[0] or (x[0] != 'daily' and x[3] not in ln['en'][x[0]])]
        check('say(event): a line from that event\'s list for all ' + str(len(need)) + ' events', not badsay, badsay)
        dl = [x[3] for x in said if x[0] == 'daily'][0]
        check('daily line: the modifier filled in', '{' not in dl and any(dl.startswith(x.split('{mod}')[0]) for x in ln['en']['daily']), dl)
        seq = await page.evaluate("(() => { const out = []; for (let i = 0; i < 40; i++) { __grasp.grippy.cool(); __grasp.grippy.say('miss'); out.push(__grasp.grippy.last.i); } return out; })()")
        check('no immediate repeat (40 miss lines in a row), and the lines vary', all(a != b2 for a, b2 in zip(seq, seq[1:])) and len(set(seq)) >= 4, seq)
        rl = await page.evaluate("""(() => { const g = __grasp.grippy, r = {}; g.cool();
          r.a = g.say('combo'); r.b = g.say('firstHit'); r.c = g.say('super'); r.after = g.last.event;
          r.boss = g.say('boss'); r.bossEv = g.last.event; r.best = g.say('newBest'); r.last = g.say('lastLife'); r.ev = g.last.event;
          r.minor = g.say('pu_big'); r.gap = g.gapMs; r.show = g.showMs; return r; })()""")
        check('rate limit: two events within 1 s give one line (the second and third are dropped)', rl['a'] and not rl['b'] and not rl['c'] and rl['after'] == 'combo', rl)
        check('important events cut in: boss, new best, last life', rl['boss'] and rl['best'] and rl['last'] and rl['ev'] == 'lastLife' and not rl['minor'], rl)
        check('one line per 4 s, each shown 2.2 s', rl['gap'] == 4000 and rl['show'] == 2200, rl)
        await page.evaluate(G + ".say('boss')")
        await page.wait_for_function("!" + G + ".visible", timeout=6000)
        hid = await page.evaluate("performance.now() - " + G + ".last.t")
        check('the line goes away after ~2.2 s', 2150 <= hid <= 5000, hid)
        # real triggers: a hit, a power-up, a close one, a boss, a miss, the last life, a mission, a new best
        await page.evaluate(S + ".extrasOff = true")
        real = await page.evaluate(f"""(() => {{ const s = {S}, g = __grasp.grippy, r = {{}}, now = performance.now();
          g.cool(); s.setBallZ(60, innerWidth / 2, innerHeight / 2); s.hits = 0; strikeHit(s.ball, now); r.hit = g.last.event;
          g.cool(); s.catchTest('fire'); r.pu = g.last.event;
          g.cool(); closeOne(s.ball, performance.now(), 'test'); r.close = g.last.event;
          s.spawnBoss(); r.boss = g.last.event; return r; }})()""")
        check('real triggers: a Strike hit -> firstHit, a caught Fireball -> pu_fire, a close one, a boss', real == {'hit': 'firstHit', 'pu': 'pu_fire', 'close': 'close', 'boss': 'boss'}, real)
        await page.evaluate(G + ".cool(); " + S + ".boss = null; " + S + ".lives = 3; " + S + ".ball = null; " + S + ".serve(); " + S + ".setBallZ(-500)")
        await page.wait_for_function(S + ".lives === 2 && " + G + ".last.event === 'miss'", timeout=6000)
        check('a missed ball (lives left) -> miss', True)
        await page.wait_for_function(S + ".balls.length > 0", timeout=6000)
        await page.evaluate(S + ".setBallZ(-500)")
        await page.wait_for_function(S + ".lives === 1 && " + G + ".last.event === 'lastLife'", timeout=6000)
        check('the next miss leaves one heart -> lastLife (cuts in without waiting)', True)
        mi = await page.evaluate("(() => { __grasp.grippy.cool(); const m = __grasp.missions.find(q => !q.done); const def = __grasp.missionPool.find(q => q.id === m.id); __grasp.track(def.ev, m.goal); return __grasp.grippy.last.event; })()")
        check('a mission done -> mission line', mi == 'mission', mi)
        await page.evaluate(S + ".best = 0")
        await page.wait_for_function(S + ".balls.length > 0", timeout=6000)
        await end_strike(page, 50)
        check('a new best at the end -> newBest line', await page.evaluate(G + ".last.event") == 'newBest' and await page.evaluate(S + ".ui.newBest"))
        # muted: lines still show, only the sound is muted
        await page.evaluate("__grasp.muted = true; " + G + ".cool(); __sfx.length = 0")
        mu = await page.evaluate("({ ok: __grasp.grippy.say('miss'), vis: __grasp.grippy.visible, text: __grasp.grippy.last.text, sfx: __sfx.slice() })")
        check('muted: the line still shows (the pop sound asked for, silenced by sfx)', mu['ok'] and mu['vis'] and mu['text'] and 'grippy' in mu['sfx'], mu)
        await page.evaluate("__grasp.muted = false")
        check('no page errors (desktop)', not errs, errs); await ctx.close()

        # ---- HE lines in game; the toggle in the Collection header (persists), off hides him ----
        ctx, page, errs = await fresh(b, True, True)
        await play(page, 'slice', True)
        await page.wait_for_function(G + ".visible && " + G + ".last.event === 'start'", timeout=5000)
        hl = await page.evaluate(G + ".last.text")
        check('HE: the start line is one of the Hebrew lines', hl in ln['he']['start'], hl)
        await page.evaluate(G + ".cool()")
        hs = await page.evaluate("(() => { const s = __grasp.slice; s.score = 0; s.lives = 3; s.nextSpawn = 1e12; s.fruits.length = 0; s.fruits.push({ x: 180, y: innerHeight + 100, vx: 0, vy: 0.5, r: 40, rot: 0, vr: 0, kind: {rind:'#ffc24b', flesh:'#ffe3a1', seed:null}, born: 0 }); return 1; })()")
        await page.wait_for_function("__grasp.slice.lives === 2 && " + G + ".last.event === 'miss'", timeout=6000)
        check('HE slice: a missed fruit -> a Hebrew miss line', await page.evaluate(G + ".last.text") in ln['he']['miss'])
        await page.wait_for_timeout(200); await page.screenshot(path='tests/out/grippy_phone_slice_he.png')
        bx = await page.evaluate(G + ".box()")
        check('HE: Grippy at the bottom right (start side in RTL), inside the screen', bx and bx['x'] + bx['w'] >= 340 and bx['x'] >= 0 and bx['mascot']['x'] > bx['bubble']['x'], bx)
        await page.tap('#homeBtn'); await page.wait_for_timeout(300)
        check('home: Grippy hidden', not await page.evaluate(G + ".visible"))
        await page.tap('#collectionBtn'); await page.wait_for_timeout(400)
        tb = await page.evaluate("(() => { const b = $('grippyBtn'), r = b.getBoundingClientRect(), h = b.closest('header').getBoundingClientRect(), x = b.closest('header').querySelector('.xBtn').getBoundingClientRect(); return { pressed: b.getAttribute('aria-pressed'), label: b.getAttribute('aria-label'), inHeader: r.top >= h.top - 1 && r.bottom <= h.bottom + 1 && r.left >= 0 && r.right <= innerWidth, noOverlap: r.right <= x.left || r.left >= x.right, w: r.width }; })()")
        check('Collection header: the Grippy toggle, on by default, labelled, fits beside the close button', tb['pressed'] == 'true' and 'גריפי' in tb['label'] and tb['inHeader'] and tb['noOverlap'], tb)
        await page.screenshot(path='tests/out/grippy_toggle_he.png')
        await page.tap('#grippyBtn'); await page.wait_for_timeout(150)
        check('tap: off (aria-pressed false), saved in the profile', await page.evaluate("$('grippyBtn').getAttribute('aria-pressed')") == 'false' and await page.evaluate("JSON.parse(localStorage.getItem('grasp.profile')).grippy") is False)
        await page.reload(); await page.wait_for_timeout(700)
        check('off survives a reload', await page.evaluate(G + ".on") is False and await page.evaluate("$('grippyBtn').getAttribute('aria-pressed')") == 'false')
        await play(page, 'strike', True)
        await page.wait_for_timeout(600)
        off = await page.evaluate("(() => { __grasp.grippy.cool(); return { say: __grasp.grippy.say('boss'), vis: __grasp.grippy.visible, hidden: $('grippy').hidden }; })()")
        check('off: no line on round start or say(), Grippy hidden', not off['say'] and not off['vis'] and off['hidden'], off)
        await page.evaluate(G + ".on = true; " + G + ".cool()")
        check('back on: he speaks again', await page.evaluate(G + ".say('super')") and await page.evaluate(G + ".visible"))
        check('no page errors (HE / toggle)', not errs, errs); await ctx.close()

        # ---- the mascot never covers the HUD card, the power meter or the hint toast (phone, EN / HE) ----
        for he in (False, True):
            tag = 'phone ' + ('he' if he else 'en')
            ctx, page, errs = await fresh(b, True, he)
            await play(page, 'strike', True)
            await page.wait_for_function(G + ".visible && " + S + ".ui.hud && " + S + ".ui.meterTop > 0 && $('hint').classList.contains('show')", timeout=6000)
            await page.wait_for_timeout(700)  # the hint has slid up
            r = await page.evaluate("(() => { const h = $('hint').getBoundingClientRect(); return { g: __grasp.grippy.box(), hud: __grasp.strike.ui.hud, meter: __grasp.strike.ui.meterTop, hint: { x: h.left, y: h.top, w: h.width, h: h.height } }; })()")
            g = r['g']
            ok = g and inter(g, r['hud']) == 0 and inter(g, r['hint']) == 0 and g['y'] + g['h'] <= r['meter'] and g['x'] >= 0 and g['x'] + g['w'] <= 360 and g['y'] >= 0
            check(tag + ' strike: Grippy box clear of the HUD card, the hint toast and the power meter', ok, r)
            await page.screenshot(path='tests/out/grippy_strike_phone_' + ('he' if he else 'en') + '.png')
            await page.evaluate("hideHint()"); await page.wait_for_timeout(600); await page.evaluate(G + ".cool(); " + G + ".say('super')"); await page.wait_for_timeout(100)
            r2 = await page.evaluate("({ g: __grasp.grippy.box(), meter: __grasp.strike.ui.meterTop, hud: __grasp.strike.ui.hud })")
            check(tag + ' strike, no hint: still above the meter', r2['g'] and r2['g']['y'] + r2['g']['h'] <= r2['meter'] and inter(r2['g'], r2['hud']) == 0, r2)
            check(tag + ': no page errors', not errs, errs); await ctx.close()

        # ---- "One more?" teaser: the nearest goal for crafted profiles; Play again dominant and pulsing ----
        cases = [
            ('coins', prof(coins=263, unlocked=ALL_CHEAP, missions=[('walls', 0, 6), ('fruit', 0, 40), ('boss', 0, 1)]), 'Only 37 coins to the Disco ball!', 'רק עוד 37 מטבעות לכדור דיסקו!'),
            ('xp', prof(xp=438, missions=[('walls', 0, 6), ('fruit', 0, 40), ('boss', 0, 1)]), '12 XP to Level 4', 'עוד 12 XP לרמה 4'),
            ('mission', prof(missions=[('walls', 4, 6), ('fruit', 10, 40), ('boss', 0, 1)]), '2 more walls for the mission', 'עוד 2 קירות למשימה'),
            ('buy', prof(coins=420, unlocked=ALL_CHEAP, missions=[('walls', 0, 6), ('fruit', 0, 40), ('boss', 0, 1)]), 'You can buy the Disco ball now!', 'יש לכם מספיק מטבעות לכדור דיסקו!'),
        ]
        for kind, init, en, hetext in cases:
            for he in ((False, True) if kind in ('coins', 'mission') else (False,)):
                tag = kind + ' ' + ('he' if he else 'en')
                ctx, page, errs = await fresh(b, he, he, init)
                await play(page, 'strike', he)
                await end_strike(page, 0)
                tz = await page.evaluate(S + ".ui.teaser")
                exp = hetext if he else en
                check('teaser (' + tag + '): "' + exp + '"', tz and tz['text'] == exp and tz['kind'] == kind and (tz['item'] == 'ball_disco') == (kind in ('coins', 'buy')), tz)
                c = await page.evaluate(S + ".ui.card"); bt = await page.evaluate(S + ".ui.buttons")
                check('teaser (' + tag + '): inside the card, under the stats, above the buttons', tz and tz['x'] >= c['x'] and tz['x'] + tz['w'] <= c['x'] + c['w'] and tz['y'] > c['y'] + 200 and tz['y'] + tz['h'] < bt['again']['y'], [tz, c])
                if kind == 'coins':
                    await page.wait_for_timeout(300); await page.screenshot(path='tests/out/grippy_teaser_' + ('he' if he else 'en') + '.png')
                    p1 = await page.evaluate(S + ".ui.againPulse")
                    await page.wait_for_function(f"Math.abs({S}.ui.againPulse - {p1}) > 0.01", timeout=4000)
                    check('Play again pulses (scale changes over time, within a few %), and is wider than Home', 1 <= p1 <= 1.04 and bt['again']['w'] > bt['home']['w'] * 1.2, [p1, bt])
                if kind == 'mission' and not he:  # the same profile from the API, and a Slice card shows it too
                    q = await page.evaluate("__grasp.teaser()")
                    check('__grasp.teaser(): the same pick (walls 4/6 beats fruit 10/40)', q['kind'] == 'mission' and q['id'] == 'walls' and q['n'] == 2, q)
                check('teaser (' + tag + '): no page errors', not errs, errs); await ctx.close()

        # ---- toasts at round end never touch the end card (phone EN / HE: Strike, Slice, the daily) ----
        for he in (False, True):
            for m in ('strike', 'slice', 'daily'):
                tag = 'phone ' + ('he' if he else 'en') + ' ' + m
                ctx, page, errs = await fresh(b, True, he, prof(coins=10, xp=45, missions=[('rounds', 2, 3), ('fruit', 0, 40), ('boss', 0, 1)]))
                if m == 'daily':
                    await page.evaluate("__grasp.setGameMode('strike')"); await page.tap('#dailyBtn'); await page.wait_for_timeout(300); await page.tap('#dailyMouse')
                    await page.wait_for_function("__grasp.daily.on && mode === 'mouse'", timeout=8000)
                else: await play(page, m, True)
                await page.wait_for_timeout(300)
                await page.evaluate("__grasp.toasts.length = 0")
                if m == 'slice': await end_slice(page, 60)
                else: await end_strike(page, 60)
                E = "() => " + ("__grasp.slice" if m == 'slice' else S)
                await page.wait_for_function("document.querySelector('#metaToast .mt:not(.wait)')", timeout=4000)
                await page.wait_for_timeout(150)
                await page.screenshot(path='tests/out/grippy_endcard_' + m + '_' + ('he' if he else 'en') + '.png')
                res = await page.evaluate(SAMPLER + "(" + E + ")")
                nt = len(await page.evaluate("__grasp.toasts"))
                want = 3 if m == 'daily' else 2  # level up + mission (+ the first daily's bonus)
                check(tag + ': ' + str(nt) + ' round-end toasts, all shown one at a time, one line each, inside the screen', nt >= want and len(res['texts']) >= want and res['maxAtOnce'] == 1 and res['oneLine'] and res['inside'], {k: res[k] for k in ('texts', 'maxAtOnce', 'oneLine', 'inside', 'frames', 'last')})
                check(tag + ': no toast pixel over the end card or the toolbar (every frame)', res['maxOver'] == 0 and res['maxBar'] == 0 and res['frames'] > 5, {k: res.get(k) for k in ('maxOver', 'maxBar', 'card', 'last')})
                check(tag + ': no page errors', not errs, errs); await ctx.close()

        # ---- toasts away from an end card are unchanged: stacked at the top, 3 s ----
        ctx, page, errs = await fresh(b, True)
        await play(page, 'strike', True)
        await page.evaluate("toast('claimedToast', { c: 5 }, 'coin'); toast('claimedToast', { c: 6 }, 'coin')")
        n = await page.evaluate("[...document.querySelectorAll('#metaToast .mt')].filter(e => e.getBoundingClientRect().height > 0).length")
        check('mid-round: two toasts stack as before (not compact)', n == 2 and not await page.evaluate("__grasp.toastCompact"), n)
        check('no page errors (mid-round toasts)', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
