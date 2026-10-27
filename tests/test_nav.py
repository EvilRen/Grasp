exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Navigation v2 (the owner's "one way home" pass, Oct 2026): the Arcade dissolved (Strike's modes: since Oct 2026 a strip inside its one card: a mode only picks, the card's Play plays it, the Map opens at once;
# Pop It has its own sticker; the camera games are a row of stickers); "a sticker plays" (Smash's sticker = its current stage; nothing pops up
# after Home: what waits glows); one way home (the corner control = pause + house; the sheet: Resume, Home, Restart, Map (Strike / Smash), at most
# 4 rows; every end card: the big button, then Home, then Map / Share: at most 3); Home = the room the game belongs to; one tap everywhere (the
# owner removed the parental controls on purpose: the corner control, the Big kids switch and Settings are plain taps; the browser's Back in any
# game: the pause sheet first, then Home; window.__graspNavGuard opts the suites in to the Back handling); Back on the start screen closes the
# sheet on top. Screenshots: tests/out/nav_{main,strike_chips,pause,card_strike,card_smash,toddler_pause}_{en,he}.png at 390x844.
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
                chips: [...$('heroModes').querySelectorAll('button')].filter(b => !b.hidden).map(b => { const q = r(b), lb = b.querySelector('.lb'), ic = b.querySelector('.ic svg'); return { id: b.id || b.dataset.k, lb: lb.offsetParent ? lb.textContent.trim() : '', ic: !!(ic && ic.getBoundingClientRect().width > 12), on: b.getAttribute('aria-pressed'),
                  fs: Math.min(99, ...[...b.querySelectorAll('.lb')].filter(x => x.offsetParent && x.textContent.trim()).map(x => parseFloat(getComputedStyle(x).fontSize))), w: q.width, h: q.height, l: q.left, rr: q.right, t: q.top, bb: q.bottom }; }),
                hero: (() => { const q = r($('heroPlay')); return { l: q.left, rr: q.right, t: q.top, bb: q.bottom }; })(), sub: $('heroSub').textContent }; })()""")
            ids = [x['id'] for x in L['vis']]
            check(tg + ': no Arcade (no sticker, no sheet)', not L['arcade'], ids)
            check(tg + ': Big kids: the hero + its strip (Stage, Frenzy, Daily, Endless, Map), Smash, Slice, Pop It, 4 camera games, the dock', all(k in ids for k in ('heroPlay', 'heroAdv', 'strike', 'frenzyChip', 'dailyBtn', 'endlessChip', 'smash', 'slice', 'bigPopit', 'drums', 'bubbles', 'paint', 'stars', 'collectionBtn', 'todayBtn')), ids)
            ch = L['chips']; cid = [c['id'] for c in ch]; stage = ('שלב' if he else 'Stage')
            check(tg + ': Strike is one card: its strip = Stage N, then 3 modes (Frenzy, Daily, Endless), then the Map; Stage N picked (the ribbon says it)', cid == ['heroAdv', 'frenzyChip', 'dailyBtn', 'endlessChip', 'map'] and [c['on'] for c in ch[:4]] == ['true', 'false', 'false', 'false'] and L['sub'] == stage + ' 10', [cid, L['sub']])
            check(tg + ': the strip: one word a mode, "' + stage + '" (+ its number when it fits), the Map\'s icon (+ its word when it fits)', ch[0]['lb'] in (stage + ' 10', stage) and all(len(c['lb'].split()) == 1 for c in ch[1:4]) and ch[4]['ic'] and len(ch[4]['lb'].split()) <= 1, ch)
            bad = [c for c in ch if c['w'] < 44 or c['h'] < 44 or c['fs'] < 14 or c['l'] < -0.5 or c['rr'] > L['W'] + 0.5 or c['bb'] > L['H'] + 0.5]
            inside = all(c['l'] >= L['hero']['l'] - 0.5 and c['rr'] <= L['hero']['rr'] + 0.5 and c['t'] >= L['hero']['t'] and c['bb'] <= L['hero']['bb'] + 0.5 for c in ch) and max(c['t'] for c in ch) - min(c['t'] for c in ch) < 6
            check(tg + ': the strip\'s buttons: each >= 44 x 44 px, text >= 14 px, on screen, in one row inside the hero card', not bad and inside, (bad, ch, L['hero']))
            small = [x for x in L['vis'] if x['w'] < 44 or x['h'] < 44]; off = [x for x in L['vis'] if x['l'] < -0.5 or x['rr'] > L['W'] + 0.5 or x['bb'] > L['H'] + 0.5]
            check(tg + ': every button >= 44 px and on screen, no page scroll', not small and not off and L['noScroll'], (small, off))
            await page.screenshot(path=OUT + 'nav_main_' + tg.lower() + '.png')
            await page.screenshot(path=OUT + 'nav_strike_chips_' + tg.lower() + '.png', clip=await page.evaluate("(() => { const q = $('hero').getBoundingClientRect(); return { x: 0, y: Math.max(0, q.top - 20), width: innerWidth, height: q.height + 40 }; })()"))
            check(tg + ': no page errors', not errs, errs); await ctx.close()

        # ===== 2. the chips and the stickers play at once =====
        ctx, page, errs = await fresh(b, init=prof(adv={'stars': stars(9), 'unlocked': 10}, worlds={'unlocked': 2, 'last': 1}))
        PICK = "({ mode, start: !$('start').hidden, ov: [...document.querySelectorAll('.ov')].filter(o => !o.hidden).map(o => o.id), map: !$('advMap').hidden, on: [...document.querySelectorAll('#heroModes .mbSeg:not(.heroMap)')].filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.id), mem: localStorage.getItem('grasp.heroMode'), route: __grasp.route.of(location.pathname) || null })"
        await page.tap('#frenzyChip'); await page.wait_for_timeout(300); pk = await page.evaluate(PICK)
        check('Frenzy in the strip: only picked (no game, no sheet, no map, no new route)', pk['mode'] == 'none' and pk['start'] and pk['ov'] == [] and not pk['map'] and pk['on'] == ['frenzyChip'] and pk['mem'] == 'frenzy' and pk['route'] is None, pk)
        await page.tap('#heroPlay'); await page.wait_for_function("__grasp.frenzy.on && mode === 'mouse'", timeout=8000)
        check('...the card\'s Play: Frenzy plays at once (no sheet, no map)', await page.evaluate("$('advMap').hidden && !document.querySelector('.ov:not([hidden])') && location.pathname === '/frenzy'"))
        await home(page)
        await page.tap('#dailyBtn'); await page.wait_for_timeout(300); pk = await page.evaluate(PICK)
        check('Daily in the strip: only picked', pk['mode'] == 'none' and pk['ov'] == [] and pk['on'] == ['dailyBtn'] and pk['mem'] == 'daily', pk)
        await page.tap('#heroPlay'); await page.wait_for_function("__grasp.daily.on && mode === 'mouse'", timeout=8000)
        check('...the card\'s Play: today\'s run plays at once (no #daily panel)', await page.evaluate("$('daily').hidden && $('advMap').hidden"))
        await home(page)
        await page.tap('#endlessChip'); await page.wait_for_timeout(300); pk = await page.evaluate(PICK)
        check('Endless in the strip: only picked (no world map yet)', pk['mode'] == 'none' and pk['ov'] == [] and pk['on'] == ['endlessChip'] and pk['mem'] == 'endless' and await page.evaluate("$('worldMap').hidden"), pk)
        await page.tap('#heroPlay'); await page.wait_for_function("!$('worldMap').hidden", timeout=5000)
        check('...the card\'s Play with Endless (world 2): the world map; its own history entry', await page.evaluate("history.state && history.state.grasp === 'ov'"))
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
        check('the hero\'s Map: the Adventure map at once (the picked mode stays Endless)', await page.evaluate("mode === 'none' && localStorage.getItem('grasp.heroMode') === 'endless' && $('endlessChip').getAttribute('aria-pressed') === 'true'"))
        await page.evaluate("closeAdvMap()"); await page.wait_for_timeout(400)
        check('chips / stickers: no page errors', not errs, errs); await ctx.close()

        # ===== 3. the pause sheet in every game: Resume, Home first (both big); Restart; Map only for Strike / Smash; at most 4 rows =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he)
            bad = []
            for m in ['strike', 'smash', 'slice', 'sandbox', 'busy', 'shapes', 'drums', 'bubbles', 'paint', 'stars', 'animals', 'colors', 'peekaboo', 'feed', 'puzzle', 'sand', 'popit', 'spot']:
                if m == 'strike': await page.evaluate(f"{A}.start(1, 'mouse')")
                elif m == 'smash': await page.evaluate("__grasp.setGameMode('smash'); smashStageStart(1, 'mouse')")
                else: await page.evaluate(f"__grasp.setGameMode('{m}'); strikeStart('mouse')")
                await page.wait_for_function("mode !== 'none'", timeout=8000); await page.wait_for_timeout(250)
                if m == 'spot': await page.wait_for_function("__grasp.spot.spot.ready", timeout=15000)
                await page.evaluate("openMenu()"); await page.wait_for_timeout(120)
                sh = await page.evaluate(SHEET)
                want = ['resumeBtn', 'homeBtn'] if m in ('sandbox', 'busy', 'shapes', 'animals', 'colors', 'peekaboo', 'feed', 'puzzle', 'sand', 'popit') else ['resumeBtn', 'homeBtn', 'resetBtn'] + (['menuMap'] if m in ('strike', 'smash') else [])  # (Little ones: Resume + Home only)
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

        # ===== 5. one tap everywhere (the owner removed the parental controls); Back in a toddler game = the pause sheet first (opted in: window.__graspNavGuard) =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he, init="window.__graspNavGuard = true; localStorage.setItem('grasp.room', 'little');")
            await page.tap('#start .stk[data-mode="busy"]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'busy'", timeout=8000); await page.wait_for_timeout(600)
            check(tg + ': no hold ring / hint left on the corner control or the Big kids switch', await page.evaluate("!document.querySelector('.navRing, .navHint')"))
            await page.screenshot(path=OUT + 'nav_toddler_pause_' + tg.lower() + '.png')
            hb = await page.evaluate("({ cls: document.body.classList.contains('homeOnly'), lbl: $('pauseBtn').getAttribute('aria-label'), vis: [...$('pauseBtn').querySelectorAll('svg')].filter(e => getComputedStyle(e).display !== 'none').map(e => e.getAttribute('class')) })")
            check(tg + ': Busy Board (nothing to pause): the corner sticker is the house alone, labelled Home', hb['cls'] and hb['lbl'] == ('בית' if he else 'Home') and hb['vis'] == ['pbHome'], hb)
            await page.tap('#pauseBtn'); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=3000)
            check(tg + ': ...one tap on it: home at once (no sheet)', await page.evaluate("!menu.open && !__grasp.route.of(location.pathname)")); await page.wait_for_timeout(450)
            await page.tap('#start .stk[data-mode="busy"]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'busy'", timeout=8000); await page.wait_for_timeout(600)
            # the browser's Back inside a toddler game: home at once, like its corner sticker (the QA sweep: nothing to pause there, no sheet)
            await page.evaluate("history.back()"); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=4000); await page.wait_for_timeout(200)
            check(tg + ': Back inside Busy Board: home at once (Little ones; no pause sheet)', await page.evaluate(f"!menu.open && !__grasp.route.of(location.pathname) && {M}.mb.room === 'little'")); await page.wait_for_timeout(450)
            # the coin pill hidden in Little ones; Big kids is one tap
            check(tg + ': Little ones: the coin pill is out of reach', await page.evaluate("getComputedStyle($('metaPill')).visibility === 'hidden'"))
            await page.tap('#bigBtn'); await page.wait_for_function(f"{M}.mb.room === 'big'", timeout=1000)
            check(tg + ': Little ones -> Big kids: one tap', await page.evaluate(f"{M}.mb.room") == 'big')
            # a Big kids game: the corner control is a plain tap too
            await page.evaluate(f"{A}.start(1, 'mouse')"); await page.wait_for_function(f"{A}.on && mode === 'mouse'", timeout=8000); await page.wait_for_timeout(500)
            check(tg + ': a Big kids game: the sticker keeps pause (not home-only), labelled Pause', await page.evaluate("!document.body.classList.contains('homeOnly') && $('pauseBtn').getAttribute('aria-label') === t('pauseMenu')"))
            await page.tap('#pauseBtn'); await page.wait_for_function("menu.open", timeout=3000)
            check(tg + ': a Big kids game: one tap pauses', True)
            await page.evaluate("closeMenu(false); goHome()"); await page.wait_for_timeout(300)
            check(tg + ': one tap: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, init="localStorage.setItem('grasp.room', 'little');")
        await page.tap('#start .stk[data-mode="busy"]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'busy'", timeout=8000); await page.wait_for_timeout(500)
        await page.evaluate("history.back()"); await page.wait_for_function("mode === 'none'", timeout=4000)
        check('no opt-in (the old suites): Back leaves a Little ones game at once', await page.evaluate("!menu.open")); await page.wait_for_timeout(450)
        await page.tap('#start .stk[data-mode="busy"]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'busy'", timeout=8000); await page.wait_for_timeout(500)
        await page.tap('#pauseBtn'); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=3000)
        check('...and the house sticker is one plain tap home too', await page.evaluate("!menu.open")); await ctx.close()

        # ===== 6. Back with a sheet open on the start screen closes the sheet =====
        ctx, page, errs = await fresh(b)
        n0 = await page.evaluate("history.length")
        await page.tap('#collectionBtn'); await page.wait_for_function("!$('collection').hidden", timeout=3000); await page.wait_for_timeout(200)
        check('a sheet opened on the start screen: one history entry', await page.evaluate("history.state && history.state.grasp === 'ov'") and await page.evaluate("history.length") == n0 + 1)
        await page.evaluate("history.back()"); await page.wait_for_function("$('collection').hidden", timeout=3000)
        check('Back: the sheet closes, the start screen stays', await page.evaluate("mode === 'none' && !$('start').hidden && !__grasp.route.of(location.pathname)"))
        await page.wait_for_timeout(450)
        await page.tap('#settingsBtn'); await page.wait_for_function("!$('moreSheet').hidden", timeout=3000); await page.evaluate("history.back()"); await page.wait_for_function("$('moreSheet').hidden", timeout=3000)
        check('Back closes the Settings sheet too', True); await page.wait_for_timeout(450)
        await page.tap('#collectionBtn'); await page.wait_for_function("!$('collection').hidden", timeout=3000); await page.wait_for_timeout(450)
        await page.evaluate("closePanel('collection')"); await page.wait_for_timeout(450)
        await page.tap('#start .stk[data-mode="slice"]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'slice'", timeout=8000)
        check('a game started after a sheet: its entry replaces the sheet\'s', await page.evaluate("history.state && history.state.grasp === 'slice' && history.state.fromHome"))
        await page.evaluate("history.back()"); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=4000)
        check('...Back from the game: the start screen', await page.evaluate("!__grasp.route.of(location.pathname)"))
        check('Back: no page errors', not errs, errs); await ctx.close()

        # ===== 7. nothing pops up after Home: the waiting egg glows on the Pet tab (Bubu hidden); a tap opens it =====
        ctx, page, errs = await fresh(b, init="window.__graspPopups = true; window.__graspGiftAuto = true;" + prof(pet={'egg': True, 'pantry': 1}))
        await page.wait_for_timeout(500)
        o = await page.evaluate("({ open: [...document.querySelectorAll('.ov')].filter(o => !o.hidden).map(o => o.id), popup: __grasp.home2.h2.popup, call: $('petTab').dataset.call, glow: $('petTab').classList.contains('mbCall'), bubu: $('bubuBtn').hidden })")
        check('an egg waiting: no sheet opens by itself; the Pet tab glows instead (Bubu hidden)', o['open'] == [] and o['popup'] == 'hatch' and o['call'] == 'hatch' and o['glow'] and o['bubu'], o)
        await page.tap('#petTab'); await page.wait_for_function("!$('petRoom').hidden", timeout=3000)
        check('...a tap on the Pet tab opens the egg\'s room', await page.evaluate("!$('petTab').classList.contains('mbCall')"))
        await page.evaluate("__grasp.home2.tab('play')"); await page.wait_for_timeout(300)
        await page.evaluate("window.__graspGiftAuto = false; __grasp.home2.reset(); h2.rounds = 1; profile.pet.asked = false; profile.pet.hatched = true; saveProfile(); goHome()"); await page.wait_for_timeout(800)
        o = await page.evaluate("({ open: [...document.querySelectorAll('.ov')].filter(o => !o.hidden).map(o => o.id), call: $('petTab').dataset.call, popup: __grasp.home2.h2.popup })")
        check('back home with the pet\'s name not asked yet: no name sheet pops up; the Pet tab glows', o['open'] == [] and o['call'] == 'name', o)
        await page.tap('#petTab'); await page.wait_for_function("!$('petName').hidden", timeout=3000)
        check('...a tap on the Pet tab: the name sheet', await page.evaluate("!$('petTab').classList.contains('mbCall')"))
        check('popups: no page errors', not errs, errs); await ctx.close()

        # ===== 8. Settings: the top bar's gear opens it with one tap (no parents' gate) =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he)
            g = await page.evaluate("({ gate: !!document.getElementById('gate'), lock: !!document.getElementById('lockBtn') && getComputedStyle($('lockBtn')).display !== 'none', aria: $('settingsBtn').getAttribute('aria-label'), ico: !!$('settingsBtn').querySelector('svg[data-ico=\"gear\"]') })")
            check(tg + ': the gear (labelled Settings), no gate sheet; the Little ones lock (the owner, Oct 2026) not shown in Big kids', not g['gate'] and not g['lock'] and g['ico'] and g['aria'] == ('הגדרות' if he else 'Settings'), g)
            await page.tap('#settingsBtn'); await page.wait_for_function("!$('moreSheet').hidden", timeout=1000)
            check(tg + ': one tap: the settings (Stats lives there)', await page.evaluate("!!$('moreHud').offsetParent && $('settingsBtn').getAttribute('aria-expanded') === 'true'"))
            await page.tap('#moreSheet .xBtn'); await page.wait_for_timeout(300)
            check(tg + ': its X closes it', await page.evaluate("$('moreSheet').hidden && $('settingsBtn').getAttribute('aria-expanded') === 'false'"))
            check(tg + ': settings: no page errors', not errs, errs); await ctx.close()

        # ===== 9. the QA pass: Back for a real visitor (opted in), Forward under a sheet, Calm bubbles per start =====
        HOLD = "window.__graspNavGuard = true;"
        ctx, page, errs = await fresh(b, init=HOLD)
        await page.tap('#start .stk[data-mode="slice"]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'slice'", timeout=8000); await page.wait_for_timeout(400)
        await page.evaluate("history.back()"); await page.wait_for_function("menu.open", timeout=4000)
        check('a Big kids game, Back: the pause sheet (still in the game, its entry pushed again)', await page.evaluate("mode === 'mouse' && location.pathname === '/slice'"))
        await page.evaluate("history.back()"); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=4000)
        check('...Back again (the sheet open): Home', True); await page.wait_for_timeout(450)
        await page.tap('#littleBtn'); await page.wait_for_function(f"{M}.mb.room === 'little' && !{M}.mb.swiping && Math.abs(Math.abs($('mbRooms').scrollLeft) - $('mbRooms').clientWidth) < 2 && $('bigRoom').inert && !$('littlePick').inert", timeout=3000); await page.wait_for_timeout(200)
        check('the Little ones room (a real visitor): its own history entry', await page.evaluate("history.state && history.state.grasp === 'room'"))
        await page.evaluate("history.back()"); await page.wait_for_timeout(500)
        await page.wait_for_function(f"!{M}.mb.swiping && Math.abs($('mbRooms').scrollLeft) < 2", timeout=3000)
        check('Back in the Little ones room: to Big kids (like Escape; no trap; the swiper back on Big kids, Little ones inert)', await page.evaluate(f"{M}.mb.room === 'big' && mode === 'none' && !$('start').hidden && $('littlePick').inert && !$('bigRoom').inert"))
        check('QA Back: no page errors', not errs, errs); await ctx.close()
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
