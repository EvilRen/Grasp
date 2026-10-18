exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Navigation v2 (the owner's "one way home" pass, Oct 2026): the Arcade dissolved (Strike's modes are chips under its hero, each plays at once;
# Pop It has its own sticker; the camera games are a row of stickers); "a sticker plays" (Smash's sticker = its current stage; nothing pops up
# after Home: what waits glows); one way home (the corner control = pause + house; the sheet: Resume, Home, Restart, Map (Strike / Smash), at most
# 4 rows; every end card: the big button, then Home, then Map / Share: at most 3); Home = the room the game belongs to; toddler-safe exits (a hold
# on the corner control and the Big kids switch, the browser's Back re-pushed with a hint; window.__graspHomeHold opts the suites in); Back on
# the start screen closes the sheet on top; the parents' gate (a random sum, shuffled answers, 400 ms arming, a cool-down after a wrong answer).
# Screenshots: tests/out/nav_{main,strike_chips,pause,card_strike,card_smash,toddler_hold}_{en,he}.png at 390x844.
OUT = 'tests/out/'
A = '__grasp.adventure'; S = '__grasp.strike'; N = '__grasp.nav'; M = '__grasp.menub'; H = '__grasp.home2'

def prof(**kw):
    d = dict(v=1, coins=0, xp=0); d.update(kw)
    return "if (!sessionStorage.getItem('__seeded')) { localStorage.setItem('grasp.profile', " + json.dumps(json.dumps(d)) + "); sessionStorage.setItem('__seeded', '1'); }"

def stars(n): return {str(i): 3 for i in range(1, n + 1)}

async def fresh(b, he=False, init='', w=390, h=844):
    ctx = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + HAND_JS + "localStorage.setItem('lang','" + ('he' if he else 'en') + "'); sessionStorage.setItem('grasp.testDate','2026-10-02');" + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_function(f"window.__grasp && {N} && document.readyState === 'complete'", timeout=10000)
    await page.wait_for_timeout(500)
    return ctx, page, errs

async def home(page):
    await page.evaluate("if (mode !== 'none' || anyMapOpen()) goHome()"); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=5000); await page.wait_for_timeout(450)

async def card_tap(page, E, key):
    await page.wait_for_function(f"{E}.over && {E}.ui.buttons && {E}.ui.buttons.{key} && performance.now() - {E}.overAt > 700", timeout=10000)
    r = await page.evaluate(f"{E}.ui.buttons.{key}")
    await page.tap('#stage', position={'x': r['x'] + r['w'] / 2, 'y': r['y'] + r['h'] / 2})

# the pause sheet's visible rows, top to bottom
SHEET = """(() => { const c = document.querySelector('.chrome'); const rows = [...c.querySelectorAll('button')].filter(b => getComputedStyle(b).display !== 'none' && b.offsetParent).map(b => ({ id: b.id || b.className, t: b.getBoundingClientRect().top, h: b.getBoundingClientRect().height, lb: (b.querySelector('.lb') || b).textContent.trim() })).sort((a, b) => a.t - b.t);
  return { open: menu.open && c.classList.contains('open'), ids: rows.map(r => r.id).filter(id => id !== 'pauseBtn'), rows }; })()"""
CARD = "(E) => ({ keys: Object.keys(E.ui.buttons || {}), b: E.ui.buttons })"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])

        # ===== 1. no Arcade; the screenshots of the start screen, the Strike chips =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he, init=prof(adv={'stars': stars(9), 'unlocked': 10}, worlds={'unlocked': 2, 'last': 1}))
            L = await page.evaluate("""(() => { const r = (e) => e.getBoundingClientRect(); const vis = [...$('bigRoom').querySelectorAll('button')].filter(b => b.offsetParent && !b.hidden).map(b => ({ id: b.id || b.dataset.mode || b.dataset.cg, w: r(b).width, h: r(b).height, l: r(b).left, rr: r(b).right, t: r(b).top, bb: r(b).bottom }));
              return { arcade: !!document.getElementById('arcadeBtn') || !!document.getElementById('arcadePick'), vis, W: innerWidth, H: innerHeight, noScroll: document.documentElement.scrollHeight <= innerHeight + 1 && document.documentElement.scrollWidth <= innerWidth + 1,
                chips: [...$('heroModes').querySelectorAll('button')].filter(b => !b.hidden).map(b => ({ id: b.id, lb: b.querySelector('.lb').textContent.trim(), ic: !!b.querySelector('.ic svg') })) }; })()""")
            ids = [x['id'] for x in L['vis']]
            check(tg + ': no Arcade (no sticker, no sheet)', not L['arcade'], ids)
            check(tg + ': Big kids: the hero + Map, 3 mode chips (Frenzy, Daily, Endless), Smash, Slice, Pop It, 4 camera games, the dock', all(k in ids for k in ('heroPlay', 'strike', 'frenzyChip', 'dailyBtn', 'endlessChip', 'smash', 'slice', 'bigPopit', 'drums', 'bubbles', 'paint', 'stars', 'collectionBtn', 'todayBtn')), ids)
            check(tg + ': the chips: icon + one word each, at most 3', len(L['chips']) == 3 and all(c['ic'] and len(c['lb'].split()) == 1 for c in L['chips']), L['chips'])
            small = [x for x in L['vis'] if x['w'] < 44 or x['h'] < 44]; off = [x for x in L['vis'] if x['l'] < -0.5 or x['rr'] > L['W'] + 0.5 or x['bb'] > L['H'] + 0.5]
            check(tg + ': every button >= 44 px and on screen, no page scroll', not small and not off and L['noScroll'], (small, off))
            await page.screenshot(path=OUT + 'nav_main_' + tg.lower() + '.png')
            await page.screenshot(path=OUT + 'nav_strike_chips_' + tg.lower() + '.png', clip=await page.evaluate("(() => { const q = $('hero').getBoundingClientRect(); return { x: 0, y: Math.max(0, q.top - 20), width: innerWidth, height: q.height + 40 }; })()"))
            check(tg + ': no page errors', not errs, errs); await ctx.close()

        # ===== 2. the chips and the stickers play at once =====
        ctx, page, errs = await fresh(b, init=prof(adv={'stars': stars(9), 'unlocked': 10}, worlds={'unlocked': 2, 'last': 1}))
        await page.tap('#frenzyChip'); await page.wait_for_function("__grasp.frenzy.on && mode === 'mouse'", timeout=8000)
        check('Frenzy chip: Frenzy plays at once (no sheet, no map)', await page.evaluate("$('advMap').hidden && !document.querySelector('.ov:not([hidden])') && location.pathname === '/frenzy'"))
        await home(page)
        await page.tap('#dailyBtn'); await page.wait_for_function("__grasp.daily.on && mode === 'mouse'", timeout=8000)
        check('Daily chip: today\'s run plays at once (no #daily panel)', await page.evaluate("$('daily').hidden && $('advMap').hidden"))
        await home(page)
        await page.tap('#endlessChip'); await page.wait_for_function("!$('worldMap').hidden", timeout=5000)
        check('Endless chip (world 2): the world map; its own history entry', await page.evaluate("history.state && history.state.grasp === 'ov'"))
        await page.evaluate("history.back()"); await page.wait_for_function("$('worldMap').hidden", timeout=4000)
        check('Back on the world map: it closes, the start screen stays', await page.evaluate("mode === 'none' && !$('start').hidden && !__grasp.route.of(location.pathname)"))
        await page.wait_for_timeout(450)
        await page.tap('#bigPopit'); await page.wait_for_function("mode !== 'none' && gameMode === 'popit'", timeout=8000); await page.wait_for_timeout(400)
        pi = await page.evaluate("({ over: __grasp.popit.pi.over && __grasp.popit.pi.over.kind, mode: __grasp.popit.pi.mode, flow: __grasp.popit.pi.flow })")
        check('Pop It sticker (Big kids): straight into Free play (no picker first), the kid flow', pi == {'over': None, 'mode': 'free', 'flow': 'kid'}, pi)
        await page.evaluate("__grasp.popit.act('corner')"); await page.wait_for_timeout(250)
        check('...its corner button still opens the 5 modes (with Race)', await page.evaluate("__grasp.popit.pi.over && __grasp.popit.pi.over.kind === 'picker' && piModes().length === 5"))
        await home(page)
        check('Home from Pop It (Big kids): back in Big kids', await page.evaluate(f"{M}.mb.room") == 'big')
        await page.tap('#start .stk[data-mode="smash"]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'smash'", timeout=8000)
        check('Smash sticker: its current stage at once (no map)', await page.evaluate("$('smashMap').hidden && __grasp.smash.run === 'stage'"))
        await home(page)
        await page.tap('#camGamesBtn [data-cg="paint"]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'paint'", timeout=8000)
        check('a camera game\'s sticker: plays at once (no picker sheet)', await page.evaluate("$('cgPick').hidden"))
        await home(page)
        await page.tap('.heroMap'); await page.wait_for_function("!$('advMap').hidden", timeout=5000)
        check('the hero\'s Map chip: the Adventure map', True)
        await page.evaluate("closeAdvMap()"); await page.wait_for_timeout(400)
        check('chips / stickers: no page errors', not errs, errs); await ctx.close()

        # ===== 3. the pause sheet in every game: Resume, Home first (both big); Restart; Map only for Strike / Smash; at most 4 rows =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he)
            bad = []
            for m in ['strike', 'smash', 'slice', 'sandbox', 'busy', 'shapes', 'drums', 'bubbles', 'paint', 'stars', 'animals', 'colors', 'peekaboo', 'feed', 'puzzle', 'popit']:
                if m == 'strike': await page.evaluate(f"{A}.start(1, 'mouse')")
                elif m == 'smash': await page.evaluate("__grasp.setGameMode('smash'); smashStageStart(1, 'mouse')")
                else: await page.evaluate(f"__grasp.setGameMode('{m}'); strikeStart('mouse')")
                await page.wait_for_function("mode !== 'none'", timeout=8000); await page.wait_for_timeout(250)
                await page.evaluate("openMenu()"); await page.wait_for_timeout(120)
                sh = await page.evaluate(SHEET)
                want = ['resumeBtn', 'homeBtn'] if m in ('sandbox', 'busy', 'shapes', 'animals', 'colors', 'peekaboo', 'feed', 'puzzle', 'popit') else ['resumeBtn', 'homeBtn', 'resetBtn'] + (['menuMap'] if m in ('strike', 'smash') else [])  # (Little ones: Resume + Home only)
                if not (sh['open'] and sh['ids'] == want and all(r['h'] >= 54 for r in sh['rows'][:2])): bad.append((m, sh['ids']))
                if m == 'strike':
                    await page.screenshot(path=OUT + 'nav_pause_' + tg.lower() + '.png')
                    lb = [r['lb'] for r in sh['rows'] if r['id'] in ('resumeBtn', 'homeBtn')]
                    check(tg + ': the first two rows read Resume, Home', lb == (['המשך', 'בית'] if he else ['Resume', 'Home']), lb)
                await page.evaluate("closeMenu(false); goHome()"); await page.wait_for_timeout(300)
            check(tg + ': every game\'s pause sheet: Resume, Home (big), Restart (Big kids; + Map for Strike / Smash); no Sound / Language / Stats / Install', not bad, bad)
            check(tg + ': no page errors', not errs, errs); await ctx.close()

        # the Map row: Strike -> the Adventure map over the game; its Back = Home
        ctx, page, errs = await fresh(b)
        await page.evaluate(f"{A}.start(1, 'mouse')"); await page.wait_for_function(f"{A}.on && mode === 'mouse'", timeout=8000); await page.wait_for_timeout(300)
        await page.tap('#pauseBtn'); await page.wait_for_function("menu.open", timeout=3000); await page.tap('#menuMap'); await page.wait_for_function("!$('advMap').hidden", timeout=4000)
        check('pause > Map (Strike): the Adventure map', await page.evaluate("!menu.open"))
        await page.tap('#advBack'); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=5000)
        check('...its Back: home', True); await page.wait_for_timeout(400)
        await page.evaluate("__grasp.setGameMode('smash'); smashStageStart(1, 'mouse')"); await page.wait_for_function("mode === 'mouse'", timeout=8000); await page.wait_for_timeout(300)
        await page.tap('#pauseBtn'); await page.wait_for_function("menu.open", timeout=3000); await page.tap('#menuMap'); await page.wait_for_function("!$('smashMap').hidden", timeout=4000)
        check('pause > Map (Smash): the Smash map', True)
        await page.evaluate("closeSmashMap()"); await page.wait_for_timeout(300)
        check('pause Map: no page errors', not errs, errs); await ctx.close()

        # ===== 4. every end card: the big one, then Home (+ Map / Share), at most 3; Home -> the room the game belongs to =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he, init=prof(adv={'stars': stars(2), 'unlocked': 3}))
            await page.evaluate(f"{A}.start(3, 'mouse')"); await page.wait_for_function(f"{A}.on && {A}.phase === 'play'", timeout=8000)
            await page.evaluate(f"{A}.finishTest(1)"); await page.wait_for_function(f"{S}.over && {S}.ui.buttons && performance.now() - {S}.overAt > 1600", timeout=10000)
            c = await page.evaluate(f"({CARD})({S})"); lb = await page.evaluate(f"{S}.ui.advLabels")
            check(tg + ': the Strike clear card: Next (big), Home, Map; nothing else', c['keys'] == ['next', 'home', 'map'] and c['b']['next']['h'] > c['b']['home']['h'] and lb['home'] == ('בית' if he else 'Home'), (c['keys'], lb))
            rtl = c['b']['home']['x'] > c['b']['map']['x']
            check(tg + ': Home on the start side, Map on the end side', rtl == he, c['b'])
            await page.screenshot(path=OUT + 'nav_card_strike_' + tg.lower() + '.png')
            await card_tap(page, S, 'home'); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=5000)
            check(tg + ': the card\'s Home: the start screen, Big kids', await page.evaluate(f"{M}.mb.room") == 'big'); await page.wait_for_timeout(400)
            await page.evaluate(f"{A}.start(3, 'mouse')"); await page.wait_for_function(f"{A}.on && {A}.phase === 'play'", timeout=8000)
            await page.evaluate(f"{A}.failTest()"); await page.wait_for_function(f"{S}.over && {S}.ui.buttons", timeout=8000)
            c = await page.evaluate(f"({CARD})({S})")
            check(tg + ': the Strike fail card: Try again (big), Home, Map', c['keys'] == ['retry', 'home', 'map'], c['keys'])
            await page.evaluate("goHome()"); await page.wait_for_timeout(400)
            await page.evaluate("__grasp.setGameMode('smash'); smashStageStart(1, 'mouse')"); await page.wait_for_function("mode === 'mouse' && __grasp.smash.phase === 'play'", timeout=10000)
            await page.evaluate("__grasp.smash.endAt = performance.now() + 200"); await page.wait_for_function("__grasp.smash.over && __grasp.smash.ui.buttons && performance.now() - __grasp.smash.overAt > 900", timeout=10000)
            c = await page.evaluate("(" + CARD + ")(__grasp.smash)")
            check(tg + ': the Smash card: the big one, Home, Map', len(c['keys']) == 3 and c['keys'][1:] == ['home', 'map'] and c['keys'][0] in ('next', 'retry'), c['keys'])
            await page.screenshot(path=OUT + 'nav_card_smash_' + tg.lower() + '.png')
            await page.evaluate("goHome()"); await page.wait_for_timeout(400)
            await page.evaluate("__grasp.setGameMode('slice'); strikeStart('mouse')"); await page.wait_for_function("mode === 'mouse' && gameMode === 'slice'", timeout=8000); await page.wait_for_timeout(300)
            await page.evaluate("for (let i = 0; i < 8 && !__grasp.slice.over; i++) sliceLoseLife(performance.now())"); await page.wait_for_function("__grasp.slice.over && __grasp.slice.ui.buttons", timeout=6000)
            c = await page.evaluate("(" + CARD + ")(__grasp.slice)")
            check(tg + ': the generic card (Slice): Play again (big), Home', c['keys'][:2] == ['again', 'home'] and len(c['keys']) <= 3, c['keys'])
            await page.evaluate("goHome()"); await page.wait_for_timeout(400)
            await page.evaluate(f"{M}.room('little'); __grasp.setGameMode('popit'); strikeStart('mouse')"); await page.wait_for_function("mode !== 'none' && gameMode === 'popit'", timeout=8000); await page.wait_for_timeout(400)
            await page.evaluate("__grasp.popit.open('race', { ms: 9000, best: 9000, stars: 2, record: false })"); await page.wait_for_timeout(500)
            ui = await page.evaluate("__grasp.popit.pi.ui.map(u => u.id)")
            check(tg + ': Pop It\'s card: Again, Home', ui[-2:] == ['again', 'home'], ui)
            await page.evaluate("__grasp.popit.act('home')"); await page.wait_for_function("mode === 'none'", timeout=5000)
            check(tg + ': Pop It (Little ones) Home: back in Little ones', await page.evaluate(f"{M}.mb.room") == 'little')
            await page.evaluate(f"{M}.room('big'); __grasp.setGameMode('animals'); strikeStart('mouse')"); await page.wait_for_function("mode !== 'none'", timeout=8000); await page.wait_for_timeout(300)
            await page.evaluate("goHome()"); await page.wait_for_timeout(300)
            check(tg + ': a Little ones game left by Home: the Little ones room (the room the game belongs to)', await page.evaluate(f"{M}.mb.room") == 'little')
            await page.evaluate(f"{M}.room('big')")
            check(tg + ': cards: no page errors', not errs, errs); await ctx.close()

        # ===== 5. toddler-safe exits (opted in: window.__graspHomeHold) =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he, init="window.__graspHomeHold = true; localStorage.setItem('grasp.room', 'little');")
            await page.tap('#start .stk[data-mode="busy"]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'busy'", timeout=8000); await page.wait_for_timeout(600)
            await page.tap('#pauseBtn'); await page.wait_for_timeout(350)
            st = await page.evaluate(f"({{ open: menu.open, hint: document.querySelector('#pauseBtn .navHint').classList.contains('show'), txt: document.querySelector('#pauseBtn .navHint').textContent, log: {N}.nav.log.slice(-3) }})")
            check(tg + ': Busy Board: a short tap on the corner control does not pause; it wiggles + "Hold to pause"', not st['open'] and st['hint'] and st['txt'] == ('להחזיק כדי לעצור' if he else 'Hold to pause'), st)
            r = await page.evaluate("(() => { const q = $('pauseBtn').getBoundingClientRect(); return { x: q.left + q.width / 2, y: q.top + q.height / 2 }; })()")
            await page.wait_for_timeout(1800)
            await page.mouse.move(r['x'], r['y']); await page.mouse.down(); await page.wait_for_timeout(650)
            mid = await page.evaluate("({ holding: $('pauseBtn').classList.contains('holding'), off: +document.querySelector('#pauseBtn .navRing rect').getAttribute('stroke-dashoffset'), open: menu.open })")
            await page.screenshot(path=OUT + 'nav_toddler_hold_' + tg.lower() + '.png')
            check(tg + ': holding: the ring fills, not paused yet', mid['holding'] and 10 < mid['off'] < 90 and not mid['open'], mid)
            await page.wait_for_timeout(1000); await page.mouse.up(); await page.wait_for_timeout(200)
            sh = await page.evaluate(SHEET)
            check(tg + ': after ~1.3 s: the pause sheet (Resume, Home first)', sh['open'] and sh['ids'][:2] == ['resumeBtn', 'homeBtn'], sh['ids'])
            await page.evaluate("closeMenu(true)"); await page.wait_for_timeout(300)
            # the browser's Back inside a toddler game: stays, the hint; a second Back within 2 s leaves
            await page.evaluate("history.back()"); await page.wait_for_timeout(600)
            bk = await page.evaluate(f"({{ mode, path: location.pathname, log: __grasp.route.log.slice(-3), hint: {N}.nav.log.slice(-1)[0] }})")
            check(tg + ': Back inside Busy Board: still playing (the entry pushed again), the hint', bk['mode'] == 'mouse' and bk['path'] == '/busy' and 'guard:busy' in bk['log'] and bk['hint'] == 'hint:navBackHold', bk)
            await page.evaluate("history.back()"); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=4000)
            check(tg + ': a second Back within 2 s: home (Little ones)', await page.evaluate(f"!__grasp.route.of(location.pathname) && {M}.mb.room === 'little'")); await page.wait_for_timeout(450)
            # the coin pill hidden in Little ones; Big kids needs the hold
            check(tg + ': Little ones: the coin pill is out of reach', await page.evaluate("getComputedStyle($('metaPill')).visibility === 'hidden'"))
            await page.tap('#bigBtn'); await page.wait_for_timeout(400)
            check(tg + ': Little ones -> Big kids: a tap stays (the hint)', await page.evaluate(f"{M}.mb.room === 'little' && document.querySelector('#bigBtn .navHint').classList.contains('show')"))
            q = await page.evaluate("(() => { const q = $('bigBtn').getBoundingClientRect(); return { x: q.left + q.width / 2, y: q.top + q.height / 2 }; })()")
            await page.wait_for_timeout(1800)  # (after the hint)
            await page.mouse.move(q['x'], q['y']); await page.mouse.down()
            try: await page.wait_for_function(f"{M}.mb.room === 'big'", timeout=5000)
            except Exception: pass
            await page.mouse.up(); await page.wait_for_timeout(300)
            check(tg + ': ...held ~1.3 s: Big kids', await page.evaluate(f"{M}.mb.room") == 'big', await page.evaluate(f"{N}.nav.log.slice(-4)"))
            # a Big kids game: the corner control is a plain tap
            await page.evaluate(f"{A}.start(1, 'mouse')"); await page.wait_for_function(f"{A}.on && mode === 'mouse'", timeout=8000); await page.wait_for_timeout(500)
            await page.tap('#pauseBtn'); await page.wait_for_function("menu.open", timeout=3000)
            check(tg + ': a Big kids game: one tap pauses', True)
            await page.evaluate("closeMenu(false); goHome()"); await page.wait_for_timeout(300)
            check(tg + ': toddler: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, init="localStorage.setItem('grasp.room', 'little');")
        await page.tap('#start .stk[data-mode="busy"]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'busy'", timeout=8000); await page.wait_for_timeout(500)
        await page.tap('#pauseBtn'); await page.wait_for_function("menu.open", timeout=3000)
        check('no opt-in (the old suites): the corner control is a plain tap in Little ones too', True)
        await page.evaluate("closeMenu(false); history.back()"); await page.wait_for_function("mode === 'none'", timeout=4000)
        check('...and Back leaves the game at once', True); await ctx.close()

        # ===== 6. Back with a sheet open on the start screen closes the sheet =====
        ctx, page, errs = await fresh(b)
        n0 = await page.evaluate("history.length")
        await page.tap('#collectionBtn'); await page.wait_for_function("!$('collection').hidden", timeout=3000); await page.wait_for_timeout(200)
        check('a sheet opened on the start screen: one history entry', await page.evaluate("history.state && history.state.grasp === 'ov'") and await page.evaluate("history.length") == n0 + 1)
        await page.evaluate("history.back()"); await page.wait_for_function("$('collection').hidden", timeout=3000)
        check('Back: the sheet closes, the start screen stays', await page.evaluate("mode === 'none' && !$('start').hidden && !__grasp.route.of(location.pathname)"))
        await page.wait_for_timeout(450)
        await page.tap('#lockBtn'); await page.wait_for_function("!$('gate').hidden", timeout=3000); await page.evaluate("history.back()"); await page.wait_for_function("$('gate').hidden", timeout=3000)
        check('Back closes the parents\' gate too', True); await page.wait_for_timeout(450)
        await page.tap('#collectionBtn'); await page.wait_for_function("!$('collection').hidden", timeout=3000); await page.wait_for_timeout(450)
        await page.evaluate("closePanel('collection')"); await page.wait_for_timeout(450)
        await page.tap('#start .stk[data-mode="slice"]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'slice'", timeout=8000)
        check('a game started after a sheet: its entry replaces the sheet\'s', await page.evaluate("history.state && history.state.grasp === 'slice' && history.state.fromHome"))
        await page.evaluate("history.back()"); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=4000)
        check('...Back from the game: the start screen', await page.evaluate("!__grasp.route.of(location.pathname)"))
        check('Back: no page errors', not errs, errs); await ctx.close()

        # ===== 7. nothing pops up after Home: the waiting egg glows on Bubu; a tap opens it =====
        ctx, page, errs = await fresh(b, init="window.__graspPopups = true; window.__graspGiftAuto = true;" + prof(pet={'egg': True, 'pantry': 1}))
        await page.wait_for_timeout(500)
        o = await page.evaluate("({ open: [...document.querySelectorAll('.ov')].filter(o => !o.hidden).map(o => o.id), popup: __grasp.home2.h2.popup, call: $('bubuBtn').dataset.call })")
        check('an egg waiting: no sheet opens by itself; Bubu glows instead', o['open'] == [] and o['popup'] == 'hatch' and o['call'] == 'hatch', o)
        await page.tap('#bubuBtn'); await page.wait_for_function("!$('petRoom').hidden", timeout=3000)
        check('...a tap on Bubu opens the egg\'s room', await page.evaluate("!$('bubuBtn').classList.contains('mbCall')"))
        await page.evaluate("__grasp.home2.tab('play')"); await page.wait_for_timeout(300)
        await page.evaluate("window.__graspGiftAuto = false; __grasp.home2.reset(); h2.rounds = 1; profile.pet.asked = false; profile.pet.hatched = true; saveProfile(); goHome()"); await page.wait_for_timeout(800)
        o = await page.evaluate("({ open: [...document.querySelectorAll('.ov')].filter(o => !o.hidden).map(o => o.id), call: $('bubuBtn').dataset.call, popup: __grasp.home2.h2.popup })")
        check('back home with the pet\'s name not asked yet: no name sheet pops up; Bubu glows', o['open'] == [] and o['call'] == 'name', o)
        check('popups: no page errors', not errs, errs); await ctx.close()

        # ===== 8. the parents' gate: a random small sum, shuffled answers, 400 ms arming, a cool-down after a wrong answer =====
        ctx, page, errs = await fresh(b, init="window.__graspGateCoolMs = 1500;")
        qs = []
        for i in range(12):
            q = await page.evaluate(f"(() => {{ const g = {M}.gate.question(); return {{ a: g.a, b: g.b, ans: g.ans, opts: [...$('gateOpts').querySelectorAll('button')].map(b => b.dataset.ans), q: $('gateQTx').textContent }}; }})()")
            qs.append(q)
        check('the gate: a + b with a, b in 3..9; 3 different answers, the right one among them', all(3 <= q['a'] <= 9 and 3 <= q['b'] <= 9 and len(set(q['opts'])) == 3 and q['ans'] in q['opts'] and int(q['ans']) == q['a'] + q['b'] for q in qs), qs[:3])
        check('...not always the same sum, not always in the same place', len({(q['a'], q['b']) for q in qs}) > 3 and len({q['opts'].index(q['ans']) for q in qs}) > 1, [(q['a'], q['b'], q['opts'].index(q['ans'])) for q in qs])
        await page.evaluate(f"{M}.gate.open(); {M}.gate.step(2)")
        early = await page.evaluate(f"{M}.gate.answer({M}.mb.gate.ans)")
        check('an answer within 400 ms of the question is ignored', early is None and not await page.evaluate("$('gate').hidden"))
        await page.wait_for_timeout(450)
        wrong = await page.evaluate(f"{M}.mb.gate.opts.find(v => v !== {M}.mb.gate.ans)")
        await page.evaluate(f"{M}.gate.answer('{wrong}')"); await page.wait_for_function(f"{M}.mb.gate.step === 1", timeout=3000)
        cool = await page.evaluate(f"({{ step: {M}.mb.gate.step, held: {M}.gate.hold(), txt: $('gateHoldTx').textContent }})")
        check('a wrong answer: back to the hold, which rests (the hold refused, "Try again in N s")', cool['step'] == 1 and cool['held'] is False and 'Try again in' in cool['txt'], cool)
        await page.wait_for_function("!mbGateCooling()", timeout=4000)
        check('...after the rest the hold works again', await page.evaluate(f"(() => {{ const ok = {M}.gate.hold(); {M}.gate.stop(); return ok; }})()"))
        await page.evaluate(f"{M}.gate.step(2)"); await page.wait_for_timeout(450); await page.evaluate(f"{M}.gate.answer({M}.mb.gate.ans)"); await page.wait_for_timeout(200)
        check('the right answer: the settings (Stats lives there now)', await page.evaluate("!$('moreSheet').hidden && !!$('moreHud').offsetParent"))
        check('gate: no page errors', not errs, errs); await ctx.close()

        # ===== 9. the QA pass: Back traps for a real visitor (opted in), Forward under a sheet, Calm bubbles per start =====
        HOLD = "window.__graspHomeHold = true;"
        ctx, page, errs = await fresh(b, init=HOLD)
        await page.tap('#start .stk[data-mode="slice"]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'slice'", timeout=8000); await page.wait_for_timeout(400)
        await page.evaluate("history.back()"); await page.wait_for_function("menu.open", timeout=4000)
        check('a Big kids game, Back: the pause sheet (still in the game, its entry pushed again)', await page.evaluate("mode === 'mouse' && location.pathname === '/slice'"))
        await page.evaluate("history.back()"); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=4000)
        check('...Back again (the sheet open): Home', True); await page.wait_for_timeout(450)
        await page.tap('#littleBtn'); await page.wait_for_timeout(500)
        check('the Little ones room (a real visitor): its own history entry', await page.evaluate("history.state && history.state.grasp === 'room'"))
        await page.evaluate("history.back()"); await page.wait_for_timeout(500)
        check('Back in the Little ones room: stays there, the hold hint on Big kids', await page.evaluate(f"{M}.mb.room === 'little' && document.querySelector('#bigBtn .navHint').classList.contains('show') && history.state && history.state.grasp === 'room'"))
        check('QA Back traps: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b)
        await page.tap('#start .stk[data-mode="slice"]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'slice'", timeout=8000); await page.wait_for_timeout(300)
        await page.evaluate("history.back()"); await page.wait_for_function("mode === 'none'", timeout=4000); await page.wait_for_timeout(450)
        await page.evaluate("__grasp.home2.tab('shop')"); await page.wait_for_timeout(300)  # (the Shop's own entry replaces the forward one; routeOpen is what Forward would run)
        await page.evaluate("routeOpen('slice')"); await page.wait_for_function("mode === 'mouse' && gameMode === 'slice'", timeout=5000); await page.wait_for_timeout(300)
        check('a game opened by its route (Forward) with the Shop open: the Shop closes (never a game under a sheet)', await page.evaluate("[...document.querySelectorAll('.ov')].filter(o => !o.hidden).map(o => o.id)") == [])
        await page.evaluate("goHome()"); await page.wait_for_timeout(400)
        await page.evaluate(f"{M}.room('little')"); await page.wait_for_timeout(300)
        await page.tap('#calmBtn'); await page.wait_for_function("gameMode === 'bubbles' && mode === 'mouse'", timeout=8000); await page.wait_for_timeout(300)
        cb = await page.evaluate("({ calm: __grasp.cg.bubbles.calm, ask: !$('cgCam').hidden })")
        await page.evaluate("goHome()"); await page.wait_for_timeout(400); await page.evaluate(f"{M}.room('big')"); await page.wait_for_timeout(300)
        await page.tap('#camGamesBtn [data-cg="bubbles"]'); await page.wait_for_function("gameMode === 'bubbles' && mode === 'mouse'", timeout=8000)
        check('Calm bubbles (Little ones): calm, no camera question; the big kids\' Bubble Pop afterwards: timed again', cb == {'calm': True, 'ask': False} and await page.evaluate("__grasp.cg.bubbles.calm") is False, cb)
        check('QA Forward / Calm: no page errors', not errs, errs); await ctx.close()
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs = []
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + HOLD + "localStorage.setItem('grasp.room', 'big');")
        await page.goto('http://localhost:8765/animals'); await page.wait_for_function("window.__grasp && mode === 'mouse' && gameMode === 'animals'", timeout=10000); await page.wait_for_timeout(500)
        check('a direct link (a real visitor): the start screen under it in history', await page.evaluate("history.length") >= 2 and await page.evaluate("history.state && history.state.fromHome"))
        await page.evaluate("openMenu()"); await page.wait_for_timeout(200); await page.tap('#homeBtn'); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=4000); await page.wait_for_timeout(400)
        check('...its Home: the start screen, in Little ones (the room of the game)', await page.evaluate(f"{M}.mb.room") == 'little' and not await page.evaluate("__grasp.route.of(location.pathname)"))
        check('direct link: no page errors', not errs, errs); await ctx.close()

        await b.close()
    srv.terminate()
    print('\nRESULT:', 'ALL PASS' if not check.fails else f'{check.fails} FAILED')
    sys.exit(1 if check.fails else 0)

asyncio.run(main())
