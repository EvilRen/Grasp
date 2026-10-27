exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Menu B "Sticker Book" (the parent's pick, Oct 2026): the start screen as a sticker book. One sticker template for every game; the Big kids room
# (the Settings gear, the sound, full screen, the coins (Bubu hidden: the pet lives in the dock's Pet tab); the age switch; the Strike hero + Map; Smash, Slice, Arcade, Camera games; the dock: Shop, Pet, Events);
# the Little ones room (4 huge stickers a page, swiped sideways, dots, RTL-correct; a sticker says its name, then opens its game); the Arcade and
# Camera games sheets (stickers, 2 a row); the gear opens the settings in one tap (the owner removed the parents' gate on purpose);
# every press squashes + boings with a blip pitched per game, the idle wiggle, reduced motion, the Sound setting; the
# layout (no scroll at 360x740 / 390x844 / 1280x800, EN / HE; targets >= 44 px; labels >= 14 px); the camera's dwell on the stickers; the double-tap
# guard on the room switch; Pop It (another branch) only when its mode exists. Screenshots: tests/out/menub_*.png.
OUT = 'tests/out/'
M = '__grasp.menub'; A = '__grasp.adventure'

def prof(**kw):
    d = dict(v=1, coins=0, xp=0); d.update(kw)
    return "if (!sessionStorage.getItem('__seeded')) { localStorage.setItem('grasp.profile', " + json.dumps(json.dumps(d)) + "); sessionStorage.setItem('__seeded', '1'); }"

def stars(n): return {str(i): 3 for i in range(1, n + 1)}

async def fresh(b, he=False, w=390, h=844, mobile=True, init='', rm=None, camera=False):
    opts = dict(viewport={'width': w, 'height': h}, device_scale_factor=2, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': w, 'height': h})
    if rm: opts['reduced_motion'] = rm
    if camera: opts['permissions'] = ['camera']
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + HAND_JS + "localStorage.setItem('lang','" + ('he' if he else 'en') + "'); sessionStorage.setItem('grasp.testDate','2026-10-02');" + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_function("window.__grasp && __grasp.menub && document.readyState === 'complete'", timeout=10000)
    await page.wait_for_timeout(500)
    return ctx, page, errs

# every visible button on screen (the start screen, or an open sheet): its box, its text sizes; no page scroll
LAYOUT = """((sel) => { const root = sel ? document.querySelector(sel) : $('start'), r = (e) => { const q = e.getBoundingClientRect(); return { l: q.left, t: q.top, r: q.right, b: q.bottom, w: q.width, h: q.height }; };
  const pg = $('mbPager').getBoundingClientRect(), inView = (q, b) => b.closest('#mbPager') ? q.r > pg.left + 1 && q.l < pg.right - 1 : q.r > 1 && q.l < innerWidth - 1; // (the Little ones' other pages: scrolled out of the pager)
  const btns = [...root.querySelectorAll('button')].filter(b => b.offsetParent && !b.hidden && !b.closest('[hidden]') && !b.closest('[inert]') && inView(r(b), b)).map(b => ({ id: b.id || b.dataset.mode || b.dataset.cg || b.dataset.k || b.dataset.pg || b.dataset.ans || b.className, ...r(b),
    fs: Math.min(99, ...[...b.querySelectorAll('b, span, small')].filter(x => x.offsetParent && x.textContent.trim() && getComputedStyle(x).display !== 'none' && !x.classList.contains('bang')).map(x => parseFloat(getComputedStyle(x).fontSize))) }));
  const st = $('start');
  return { btns, W: innerWidth, H: innerHeight, dir: document.documentElement.dir,
    noScroll: document.documentElement.scrollHeight <= innerHeight + 1 && document.documentElement.scrollWidth <= innerWidth + 1 && document.body.scrollWidth <= innerWidth + 1 && st.scrollHeight <= st.clientHeight + 1 && st.scrollWidth <= st.clientWidth + 1 }; })"""

def layout_ok(tag, L, need=()):
    on = lambda q: q['l'] >= -0.5 and q['t'] >= -0.5 and q['r'] <= L['W'] + 0.5 and q['b'] <= L['H'] + 0.5
    small = [b for b in L['btns'] if b['w'] < 44 or b['h'] < 44]
    tiny = [b for b in L['btns'] if b['fs'] < 14]
    ids = [b['id'] for b in L['btns']]
    check(tag + ': no page scroll either way; every button fully on screen', L['noScroll'] and all(on(b) for b in L['btns']), [b for b in L['btns'] if not on(b)])
    check(tag + ': every tap target >= 44 x 44 px', not small, small)
    check(tag + ': every label >= 14 px', not tiny, tiny)
    if need: check(tag + ': shows ' + ', '.join(need), all(k in ids for k in need), ids)
    return L

BIG = ('settingsBtn', 'startSound', 'fullBtn', 'metaPill', 'bigBtn', 'littleBtn', 'heroPlay', 'heroAdv', 'strike', 'frenzyChip', 'dailyBtn', 'smash', 'slice', 'bigPopit', 'spot', 'drums', 'bubbles', 'paint', 'stars', 'collectionBtn', 'todayBtn')  # (navigation v2: no Arcade; Strike's mode chips; Pop It; the camera games' row)
# the rooms' swiper (#mbRooms): settled on the room mb.room names (the room off screen is inert)
SETTLED = f"(() => {{ const R = $('mbRooms'), r = {M}.mb.room; return !{M}.mb.swiping && Math.abs(Math.abs(R.scrollLeft) - (r === 'little' ? R.clientWidth : 0)) < 2 && $('start').dataset.room === r && $('bigRoom').inert === (r !== 'big') && $('littlePick').inert === (r !== 'little'); }})()"
def in_room(r): return f"{M}.mb.room === '{r}' && " + SETTLED
LITTLE = [['busy', 'shapes', 'sandbox', 'calmBtn'], ['animals', 'colors', 'peekaboo', 'feed'], ['puzzle', 'sand', 'lilPopit']]

async def page_of(page):
    return await page.evaluate(f"({{ i: {M}.pageNow(), mb: {M}.mb.page, on: [...document.querySelectorAll('#mbDots .mbDot')].findIndex(d => d.classList.contains('on')), sl: $('mbPager').scrollLeft,"
                               f" seen: [...document.querySelectorAll('#mbPager .stk')].filter(b => {{ const q = b.getBoundingClientRect(); return !b.hidden && q.left >= -1 && q.right <= innerWidth + 1; }}).map(b => b.dataset.mode || b.id) }})")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--autoplay-policy=no-user-gesture-required'])

        # ===== 1. the screens at 390x844 (EN / HE): the screenshots + the layout rules; then 360x740 and the desktop =====
        for he in (False, True):
            lg = 'he' if he else 'en'; tg = lg.upper()
            ctx, page, errs = await fresh(b, he)
            await page.wait_for_timeout(600)
            L = layout_ok(tg + ' main 390', await page.evaluate(LAYOUT + "()"), BIG)
            bx = {x['id']: x for x in L['btns']}
            check(tg + ': RTL in Hebrew, LTR in English', L['dir'] == ('rtl' if he else 'ltr'))
            lock, coins = bx['settingsBtn'], bx['metaPill']
            check(tg + ': the top bar: the gear at the ' + ('right (RTL)' if he else 'left') + ', the coins at the other end', ((lock['l'] > coins['l']) if he else (lock['l'] < coins['l'])), [lock, coins])
            check(tg + ': Bubu hidden (not in the top bar; the pet lives in the dock\'s Pet tab)', 'bubuBtn' not in bx and await page.evaluate("$('bubuBtn').hidden && $('bubuBtn').getBoundingClientRect().width === 0"), list(bx))
            hero = bx['heroPlay']; grid = [bx[k] for k in ('smash', 'slice', 'bigPopit')]; cams = [bx[k] for k in ('drums', 'bubbles', 'paint', 'stars')]
            check(tg + ': the Strike hero is the widest sticker, above the grid; Smash / Slice / Pop It / Spot it big (>= 70 x 150 px: four a row since spot the difference)', hero['w'] > 2.4 * max(g['w'] for g in grid) and hero['b'] <= min(g['t'] for g in grid) and all(g['w'] >= 70 and g['h'] >= 150 for g in grid), [hero, grid])
            check(tg + ': 3 a row: Smash / Slice / Pop It side by side, the 4 camera games in one row under them', max(g['t'] for g in grid) - min(g['t'] for g in grid) < 12 and max(c['t'] for c in cams) - min(c['t'] for c in cams) < 12 and min(c['t'] for c in cams) > max(g['b'] for g in grid), [grid, cams])
            st = await page.evaluate("""(() => { const s = [...document.querySelectorAll('#start .stk, .mbOv .stk')]; const cs = (e) => getComputedStyle(e); return { n: s.length,
              ink: s.every(e => cs(e).borderTopColor === 'rgb(42, 31, 61)'), edge: s.every(e => cs(e).boxShadow.startsWith('rgb(255, 255, 255)')), svg: s.every(e => e.querySelector('.ic svg.mbI')), canvas: document.querySelectorAll('#start .stk canvas, .mbOv .stk canvas').length,
              cols: new Set(s.map(e => cs(e).backgroundColor)).size, font: cs($('heroLbl')).fontFamily }; })()""")
            check(tg + ': one template: every game sticker (' + str(st['n']) + ') has the dark outline, the white die-cut edge and an SVG drawing (no live canvas previews), one colour per game', st['n'] >= 22 and st['ink'] and st['edge'] and st['svg'] and st['canvas'] == 0 and st['cols'] >= 17, st)  # (navigation v2: the Arcade sheet's stickers are gone: 17 colours)
            check(tg + ': the rounded type (Fredoka first, then a rounded stack)', st['font'].startswith('Fredoka'), st['font'])
            await page.screenshot(path=OUT + 'menub_main_%s.png' % lg)
            # Little ones: page 1, page 2
            await page.tap('#littleBtn'); await page.wait_for_function(in_room('little'), timeout=3000); await page.wait_for_timeout(500)
            L = layout_ok(tg + ' little p1', await page.evaluate(LAYOUT + "()"), ('busy', 'shapes', 'sandbox', 'calmBtn'))
            lb = {x['id']: x for x in L['btns']}
            check(tg + ': Little ones: 4 huge stickers (2 x 2, each >= 140 px), mint background, 3 dots', all(lb[k]['w'] >= 140 and lb[k]['h'] >= 180 for k in LITTLE[0]) and await page.evaluate("getComputedStyle($('start')).backgroundColor === 'rgb(166, 236, 208)' && document.querySelectorAll('#mbDots .mbDot').length === 3"), [lb.get(k) for k in LITTLE[0]])
            first = lb['busy']; check(tg + ': the first sticker sits at the ' + ('right (RTL)' if he else 'left'), (first['l'] > lb['shapes']['l']) if he else (first['l'] < lb['shapes']['l']), [first, lb['shapes']])
            DOTS = "[...document.querySelectorAll('#mbDots .mbDot')].map(d => ({ pg: +d.dataset.pg, x: d.getBoundingClientRect().left, on: d.classList.contains('on') })).sort((a, b) => a.x - b.x)"  # (left to right on screen)
            ds = await page.evaluate(DOTS); edge = ds[-1] if he else ds[0]
            check(tg + ': the dots run with the pages: page 1\'s dot is the ' + ('rightmost (RTL)' if he else 'leftmost') + ' and it is the lit one', edge['pg'] == 0 and edge['on'] and sum(d['on'] for d in ds) == 1 and [d['pg'] for d in ds] == ([2, 1, 0] if he else [0, 1, 2]), ds)
            await page.screenshot(path=OUT + 'menub_little_p1_%s.png' % lg)
            await page.tap('#mbDots .mbDot[data-pg="1"]'); await page.wait_for_function(f"{M}.pageNow() === 1", timeout=3000); await page.wait_for_timeout(600)
            ds = await page.evaluate(DOTS); p2 = await page_of(page)
            check(tg + ': tapping the middle dot goes to page 2 (its stickers on screen), the middle dot lit', [d['on'] for d in ds] == [False, True, False] and p2['seen'] == LITTLE[1], [ds, p2])
            layout_ok(tg + ' little p2', await page.evaluate(LAYOUT + "()"), ('animals', 'colors', 'peekaboo', 'feed'))
            await page.screenshot(path=OUT + 'menub_little_p2_%s.png' % lg)
            await page.tap('#bigBtn'); await page.wait_for_function(in_room('big'), timeout=3000); await page.wait_for_timeout(400)
            # (Strike is one card: its strip (Stage · Frenzy · Daily · Map) sits inside the hero's bottom, one row, in reading order; the camera games a row of stickers)
            seg = [bx[k] for k in ('heroAdv', 'frenzyChip', 'dailyBtn', 'strike')]
            inside = all(s['l'] >= hero['l'] - 0.5 and s['r'] <= hero['r'] + 0.5 and s['t'] >= hero['t'] + hero['h'] / 2 and s['b'] <= hero['b'] + 0.5 for s in seg)
            order = all((seg[i]['l'] > seg[i + 1]['l']) if he else (seg[i]['l'] < seg[i + 1]['l']) for i in range(3))
            check(tg + ': Strike is one card: its strip (Stage, Frenzy, Daily, Map) in one row inside the hero\'s bottom, in reading order', inside and order and max(s['t'] for s in seg) - min(s['t'] for s in seg) < 6, [hero, seg])
            # the settings: one tap on the gear
            await page.tap('#settingsBtn'); await page.wait_for_function("!$('moreSheet').hidden", timeout=1000); await page.wait_for_timeout(900)  # (after the sheet's spring-in)
            L = layout_ok(tg + ' settings', await page.evaluate(LAYOUT + "('#moreSheet')"), ('startLang', 'camBtn', 'mouseBtn', 'moreSound', 'voiceNames', 'voiceAll', 'voiceOff'))
            await page.screenshot(path=OUT + 'menub_settings_%s.png' % lg)
            check(tg + ' screens: no page errors', not errs, errs); await ctx.close()
        for (mobile, w, h, nm) in ((True, 360, 740, 'phone360'), (False, 1280, 800, 'desktop')):
            for he in (False, True):
                tg = nm + (' HE' if he else ' EN')
                ctx, page, errs = await fresh(b, he, w=w, h=h, mobile=mobile); await page.wait_for_timeout(700)  # (after the entrance)
                L = layout_ok(tg + ' main', await page.evaluate(LAYOUT + "()"), BIG)
                if nm == 'desktop':
                    col = await page.evaluate("(() => { const q = $('mbCol').getBoundingClientRect(); return { l: q.left, r: q.right, w: q.width }; })()")
                    check(tg + ': a centred phone-width column (the stickers stay big)', abs(col['l'] + col['r'] - w) < 4 and 340 <= col['w'] <= 480, col)
                    if not he: await page.screenshot(path=OUT + 'menub_main_desktop_en.png')
                await page.evaluate(f"{M}.room('little')"); await page.wait_for_function(in_room('little'), timeout=3000); await page.wait_for_timeout(200)
                for i in range(3):
                    await page.evaluate(f"{M}.page({i}, true)"); await page.wait_for_timeout(250)
                    layout_ok(tg + ' little p' + str(i + 1), await page.evaluate(LAYOUT + "()"), tuple(LITTLE[i]))
                check(tg + ': no page errors', not errs, errs); await ctx.close()

        # ===== 2. every sticker opens its game =====
        ctx, page, errs = await fresh(b, init=prof(adv={'stars': stars(9), 'unlocked': 10}, pet={'hatched': True, 'food': 3, 'pantry': 2, 'born': '2026-10-01', 'last': '2026-10-01', 'egg': True, 'eggSeen': True, 'asked': True}))
        async def home():
            await page.evaluate("if (mode !== 'none') goHome(); closeAdvMap(true); closeSmashMap(true); for (const o of document.querySelectorAll('.ov')) o.hidden = true; __grasp.home2.syncTabs()"); await page.wait_for_timeout(500)
        await page.tap('#heroPlay'); await page.wait_for_function(f"{A}.on && {A}.stage === 10 && mode === 'mouse' && $('start').hidden", timeout=10000)
        check('Strike hero: plays the current stage (10) at once', True); await home()
        await page.tap('#start button[data-mode=strike]'); await page.wait_for_function("!$('advMap').hidden", timeout=5000)
        check('Map: the Adventure map', await page.evaluate("advMapOpen() && mode === 'none'")); await home()
        await page.tap('#start button[data-mode=smash]'); await page.wait_for_function("gameMode === 'smash' && mode === 'mouse' && $('smashMap').hidden", timeout=8000)
        check('Smash: the Tower at once (Oct 2026: the tower is Smash; no map, no stages)', await page.evaluate("__grasp.smash.run === 'tower'")); await home()
        await page.tap('#start button[data-mode=slice]'); await page.wait_for_function("gameMode === 'slice' && mode === 'mouse'", timeout=8000)
        check('Slice: starts at once', True); await home()
        # Strike is one card: a mode in the strip only picks (pressed, remembered, the ribbon names it); the card's Play plays it
        PICKED = "(() => {{ const P = [...document.querySelectorAll('#heroModes .mbSeg:not(.heroMap)')].filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.id || b.dataset.k); return {{ P, mem: localStorage.getItem('grasp.heroMode'), sub: $('heroSub').textContent, lb: $('{0}').querySelector('.lb').textContent, mode, start: !$('start').hidden }}; }})()"
        for chip, m, want, nm in (('frenzyChip', 'frenzy', "__grasp.frenzy.on && mode === 'mouse'", 'Frenzy'), ('dailyBtn', 'daily', "__grasp.daily.on && mode === 'mouse' && $('daily').hidden", 'Daily (today\'s run, no panel)'),
                                  ('endlessChip', 'endless', "mode === 'mouse' && gameMode === 'strike' && !__grasp.adventure.on && !__grasp.frenzy.on", 'Endless (world 2: the old run)'), ('heroAdv', 'adv', f"{A}.on && {A}.stage === 10 && mode === 'mouse'", 'Stage 10')):
            await page.tap('#' + chip); await page.wait_for_timeout(300)
            pk = await page.evaluate(PICKED.format(chip))
            # (Stage N: the ribbon is checked back Home below: heroModeSet('adv') leaves the previous mode's name in the ribbon until h2Hero runs; reported)
            check('the strip: ' + nm + ' only picks (pressed alone, remembered, the ribbon names it; no game yet)', pk['P'] == [chip] and pk['mem'] == m and (pk['sub'] == pk['lb'] or (m == 'adv' and pk['sub'].startswith(pk['lb']))) and pk['mode'] == 'none' and pk['start'], pk)
            await page.tap('#heroPlay'); await page.wait_for_function(want + " && $('start').hidden", timeout=8000)
            check('... then the card\'s Play plays ' + nm, True); await home()
        pk = await page.evaluate(PICKED.format('heroAdv'))
        check('back Home: Stage 10 still picked, the ribbon names it', pk['P'] == ['heroAdv'] and pk['mem'] == 'adv' and pk['sub'] == pk['lb'] == 'Stage 10', pk)
        for cg in ('drums', 'bubbles', 'paint', 'stars'):
            await page.evaluate("localStorage.setItem('cgTouchOk', '1'); __grasp.cg.touchOk = true")
            await page.tap('#camGamesBtn [data-cg=%s]' % cg); await page.wait_for_function(f"gameMode === '{cg}' && mode === 'mouse' && $('cgPick').hidden", timeout=8000)
            check('Camera games > ' + cg + ': plays at once', True); await home()
        for tab, ov in (('collectionBtn', 'collection'), ('petTab', 'petRoom'), ('todayBtn', 'today')):
            await page.tap('#' + tab); await page.wait_for_timeout(450)
            o = await page.evaluate("[...document.querySelectorAll('.ov')].filter(o => !o.hidden).map(o => ({ id: o.id, b: o.querySelector('.sheet').getBoundingClientRect().bottom }))")
            dock = await page.evaluate("({ top: $('tabBar').getBoundingClientRect().top, on: [...document.querySelectorAll('#tabBar .tab.on')].map(b => b.id) })")
            check('dock ' + tab + ': opens ' + ov + ' above the dock (the dock stays), the sticker lit', [x['id'] for x in o] == [ov] and o[0]['b'] <= dock['top'] + 2 and dock['on'] == [tab], [o, dock])
            await home()
        await page.tap('#littleBtn'); await page.wait_for_timeout(500)
        for i, row in enumerate(LITTLE):
            for k in row:
                await page.evaluate(f"{M}.room('little'); {M}.page({i}, true)"); await page.wait_for_timeout(300)
                sel = '#calmBtn' if k == 'calmBtn' else '#lilPopit' if k == 'lilPopit' else '#littlePick button[data-mode=%s]' % k
                name = await page.evaluate(f"document.querySelector('{sel}').querySelector('.lb').textContent")
                await page.tap(sel)
                want = "gameMode === 'bubbles' && __grasp.cg.bubbles.calm" if k == 'calmBtn' else "gameMode === 'popit'" if k == 'lilPopit' else f"gameMode === '{k}'"
                await page.wait_for_function(f"{want} && mode === 'mouse' && $('start').hidden", timeout=8000)
                said = await page.evaluate(f"{M}.mb.said.map(x => x.text)")
                check('Little ones > ' + k + ': says "' + name + '", then plays', said and said[-1] == name, said[-3:])
                await home()
        await page.wait_for_function(SETTLED, timeout=3000)
        check('back home after a toddler game: still the Little ones room', await page.evaluate(f"$('start').dataset.room === 'little' && {M}.mb.room === 'little' && !$('littlePick').inert && $('bigRoom').inert"))
        await page.evaluate(f"{M}.room('big')"); await page.wait_for_timeout(300)
        bu = await page.evaluate("({ bubu: $('bubuBtn').hidden, w: $('bubuBtn').getBoundingClientRect().width, tab: !$('petTab').hidden })")
        check('Bubu hidden even with a hatched pet (the pet lives in the dock\'s Pet tab)', bu['bubu'] and bu['w'] == 0 and bu['tab'], bu)
        await page.evaluate(f"{M}.room('little')"); await page.wait_for_timeout(300)
        # Pop It (merged): its sticker shows in Little ones (page 3) and in Big kids
        await page.evaluate("window.routeOpen = (m) => { window.__opened = m; return true; }; __grasp.menub.page(2, true)"); await page.wait_for_timeout(300)
        pi = await page.evaluate(f"({{ lil: !$('lilPopit').hidden, big: !$('bigPopit').hidden, feat: {M}.feat('popit'), pages: {M}.mb.pages, seen: !!$('lilPopit').closest('.mbPg') }})")
        check('Pop It: its sticker shows in Little ones (page 3) and in Big kids', pi['lil'] and pi['big'] and pi['feat'] and pi['seen'] and pi['pages'] == 3, pi)
        await page.tap('#lilPopit'); await page.wait_for_function("window.__opened === 'popit'", timeout=4000)
        check('Pop It sticker: says its name and opens /popit (routeOpen)', await page.evaluate(f"{M}.mb.said.slice(-1)[0].text") == 'Pop It')
        check('stickers: no page errors', not errs, errs); await ctx.close()

        # ===== 3. Little ones' paging: both directions, EN / HE (RTL: the next page lies to the left) =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he, init="localStorage.setItem('grasp.room', 'little');")
            p0 = await page_of(page)
            check(tg + ': the room is remembered (Little ones on open); page 1, its dot lit', await page.evaluate("$('start').dataset.room") == 'little' and p0['i'] == 0 and p0['on'] == 0 and p0['seen'] == LITTLE[0], p0)
            sgn = -1 if he else 1
            await page.evaluate(f"$('mbPager').scrollBy({{ left: {sgn} * $('mbPager').clientWidth, behavior: 'instant' }})"); await page.wait_for_function(f"{M}.mb.page === 1", timeout=3000); await page.wait_for_timeout(300)
            p1 = await page_of(page)
            check(tg + ': a swipe ' + ('right (RTL)' if he else 'left') + ' = page 2 (its stickers on screen, its dot lit, a page blip)', p1['i'] == 1 and p1['on'] == 1 and p1['seen'] == LITTLE[1] and (p1['sl'] < 0 if he else p1['sl'] > 0) and await page.evaluate(f"{M}.mb.blips.some(x => x.kind === 'page')"), p1)
            await page.evaluate(f"$('mbPager').scrollBy({{ left: {sgn} * $('mbPager').clientWidth, behavior: 'instant' }})"); await page.wait_for_function(f"{M}.mb.page === 2", timeout=3000)
            p2 = await page_of(page)
            check(tg + ': ... page 3 (Puzzle, Sand, Pop It)', p2['i'] == 2 and p2['seen'] == LITTLE[2], p2)
            await page.evaluate(f"$('mbPager').scrollBy({{ left: {-sgn} * $('mbPager').clientWidth, behavior: 'instant' }})"); await page.wait_for_function(f"{M}.mb.page === 1", timeout=3000)
            check(tg + ': and back the other way to page 2', (await page_of(page))['seen'] == LITTLE[1])
            await page.tap('#mbDots .mbDot[data-pg="0"]'); await page.wait_for_function(f"{M}.mb.page === 0 && Math.abs($('mbPager').scrollLeft) < 2", timeout=4000)
            check(tg + ': the first dot: back to page 1', (await page_of(page))['seen'] == LITTLE[0])
            await page.mouse.move(200, 500); await page.mouse.wheel(sgn * 260, 0)  # (a sideways swipe on a trackpad: the browser's own scroll, snapped to a page)
            await page.wait_for_function(f"{M}.mb.page === 1 && Math.abs(Math.abs($('mbPager').scrollLeft) - $('mbPager').clientWidth) < 2", timeout=4000)
            check(tg + ': a sideways swipe snaps to the next page', (await page_of(page))['seen'] == LITTLE[1])
            await page.mouse.wheel(-sgn * 260, 0); await page.wait_for_function(f"{M}.mb.page === 0 && Math.abs($('mbPager').scrollLeft) < 2", timeout=4000)
            check(tg + ': ... and the other way back to page 1', (await page_of(page))['seen'] == LITTLE[0])
            await page.keyboard.press('Escape'); await page.wait_for_timeout(200)
            await page.wait_for_function(SETTLED, timeout=3000)
            check(tg + ': Escape: back to Big kids', await page.evaluate(f"$('start').dataset.room === 'big' && {M}.mb.room === 'big' && !$('bigRoom').inert && localStorage.getItem('grasp.room') === 'big'"))
            # the rooms swipe: #mbRooms holds both rooms side by side; a swipe to the Little ones side settles there (the switch follows); the switch slides back
            SW = f"({{ room: {M}.mb.room, data: $('start').dataset.room, big: $('bigBtn').getAttribute('aria-pressed'), little: $('littleBtn').getAttribute('aria-pressed'), bigInert: $('bigRoom').inert, lilInert: $('littlePick').inert, hidden: $('bigRoom').hidden || $('littlePick').hidden, sl: $('mbRooms').scrollLeft, w: $('mbRooms').clientWidth, mem: localStorage.getItem('grasp.room'), log: {M}.mb.log.slice(-3) }})"
            await page.evaluate(f"$('mbRooms').scrollBy({{ left: {sgn} * $('mbRooms').clientWidth, behavior: 'instant' }})"); await page.wait_for_function(in_room('little'), timeout=3000)
            sw = await page.evaluate(SW)
            check(tg + ': a swipe ' + ('right (RTL)' if he else 'left') + ' on the rooms = Little ones (the switch follows: Little ones pressed; Big kids inert, neither hidden; remembered)', sw['room'] == 'little' and sw['data'] == 'little' and sw['little'] == 'true' and sw['big'] == 'false' and sw['bigInert'] and not sw['lilInert'] and not sw['hidden'] and (sw['sl'] < 0 if he else sw['sl'] > 0) and sw['mem'] == 'little' and 'swipe:little' in sw['log'], sw)
            p0 = await page_of(page); check(tg + ': ... on its first page', p0['i'] == 0 and p0['seen'] == LITTLE[0], p0)
            await page.tap('#bigBtn'); await page.wait_for_function(in_room('big'), timeout=4000)
            sw = await page.evaluate(SW)
            check(tg + ': the switch slides back to Big kids (Big kids pressed, Little ones inert, the swiper at its start)', sw['room'] == 'big' and sw['big'] == 'true' and sw['little'] == 'false' and sw['lilInert'] and not sw['bigInert'] and not sw['hidden'] and abs(sw['sl']) < 2 and sw['mem'] == 'big', sw)
            await page.mouse.move(200, 600); await page.mouse.wheel(sgn * 300, 0)  # (a sideways trackpad swipe over Big kids: the swiper snaps to Little ones)
            await page.wait_for_function(in_room('little'), timeout=4000)
            check(tg + ': a sideways trackpad swipe over Big kids snaps to Little ones too', await page.evaluate("$('littleBtn').getAttribute('aria-pressed') === 'true'"))
            check(tg + ' paging: no page errors', not errs, errs); await ctx.close()

        # ===== 4. Settings: the gear opens it with one tap (the owner removed the parents' gate on purpose) =====
        ctx, page, errs = await fresh(b)
        check('no parents\' gate in the page (no #gate, no lock)', await page.evaluate("!document.getElementById('gate') && (!document.getElementById('lockBtn') || getComputedStyle($('lockBtn')).display === 'none') && !document.querySelector('[data-ic=\"lock\"], .gateHold, .gateOpts')"))
        await page.tap('#settingsBtn'); await page.wait_for_timeout(400)
        check('one tap on the gear: the settings sheet (language, touch / camera, sound, voice, install, Tremorti)', await page.evaluate("!$('moreSheet').hidden && !!$('tremortiLink') && $('settingsBtn').getAttribute('aria-expanded') === 'true'"))
        await page.keyboard.press('Escape'); await page.wait_for_timeout(200)
        check('Escape closes the settings', await page.evaluate("$('moreSheet').hidden && $('settingsBtn').getAttribute('aria-expanded') === 'false'"))
        await page.tap('#settingsBtn'); await page.wait_for_timeout(450); await page.evaluate("$('moreSheet').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }))"); await page.wait_for_timeout(200)
        check('a tap beside the settings closes them', await page.evaluate("$('moreSheet').hidden"))
        # the one-tap sound button stays on the start screen
        await page.tap('#startSound'); await page.wait_for_timeout(100)
        check('the sound sticker: one tap = muted (saved), its picture changes', await page.evaluate("muted === true && localStorage.getItem('muted') === '1' && $('startSound').getAttribute('aria-pressed') === 'false' && getComputedStyle($('startSound').querySelector('.off')).display !== 'none'"))
        await page.tap('#startSound'); await page.wait_for_timeout(100)
        check('... and back on', await page.evaluate("muted === false"))
        check('settings: no page errors', not errs, errs); await ctx.close()

        # ===== 5. motion and sound: squash + boing, pitched blips (and silence when muted), the idle wiggle, the background; reduced motion =====
        ctx, page, errs = await fresh(b)
        await page.tap('#bigBtn'); await page.wait_for_timeout(200)  # (a first gesture: the AudioContext runs)
        await page.evaluate("$('start').querySelector('[data-mode=smash]').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerId: 7, isPrimary: true }))")
        pr = await page.evaluate("({ pr: document.querySelector('#start [data-mode=smash]').classList.contains('mbPr'), tf: getComputedStyle(document.querySelector('#start [data-mode=smash]')).transform })")
        await page.evaluate("document.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 7 }))")
        bo = await page.evaluate("({ bo: document.querySelector('#start [data-mode=smash]').classList.contains('mbBo'), an: getComputedStyle(document.querySelector('#start [data-mode=smash]')).animationName })")
        check('a press squashes the sticker (scale .92); the release boings', pr['pr'] and bo['bo'] and bo['an'] == 'mbBoing', [pr, bo])
        keys = ['strike', 'smash', 'slice', 'arcade', 'camera', 'busy', 'shapes', 'sandbox', 'calm', 'animals', 'colors', 'peekaboo', 'feed', 'puzzle', 'drums', 'bubbles', 'paint', 'stars', 'frenzy', 'daily', 'endless']
        fs = await page.evaluate(f"{json.dumps(keys)}.map(k => Math.round({M}.pitch(k)))")
        check('the blips are pitched per game (a pentatonic note from its name: ' + str(len(set(fs))) + ' different notes for 21 games)', len(set(fs)) >= 6, fs)
        bl = await page.evaluate(f"{M}.mb.blips.slice(-2)")
        st = await page.evaluate("audio && audio.state")
        check('the press blip played (the Sound on, the audio running)', st != 'running' or (bl and bl[-1]['k'] == 'smash' and bl[-1]['kind'] == 'press' and bl[-1]['played']), [st, bl])
        await page.evaluate("setMuted(true)")
        await page.evaluate("$('start').querySelector('#bigPopit').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }))")
        check('muted: no blip plays (logged as silent)', await page.evaluate(f"{M}.mb.blips.slice(-1)[0].k === 'popit' && {M}.mb.blips.slice(-1)[0].played === false"))
        await page.evaluate("document.dispatchEvent(new PointerEvent('pointerup', { bubbles: true })); setMuted(false)")
        w0 = await page.evaluate(f"{M}.mb.wig"); await page.wait_for_timeout(4300)
        w1 = await page.evaluate(f"{M}.mb.wig")
        k = await page.evaluate(f"{M}.wiggle()")
        check('the idle wiggle: a random sticker every ~2 s (' + str(w1 - w0) + ' in 4.3 s)', 1 <= w1 - w0 <= 3 and k and await page.evaluate("!!document.querySelector('#start .stk.mbWiggle')"), [w0, w1, k])
        mo = await page.evaluate("({ bg: getComputedStyle($('start'), '::before').animationName, go: getComputedStyle($('heroPlay').querySelector('.go')).animationName })")
        check('the background drifts, the ▶ pulses', mo == {'bg': 'mbBg', 'go': 'mbPulse'}, mo)
        check('Bubu hidden', await page.evaluate("$('bubuBtn').hidden"))
        check('motion: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, rm='reduce')
        await page.wait_for_timeout(2300)
        rm = await page.evaluate(f"({{ wig: {M}.mb.wig, w: {M}.wiggle(), bg: getComputedStyle($('start'), '::before').animationName, go: getComputedStyle($('heroPlay').querySelector('.go')).animationName }})")
        check('reduced motion: no wiggle, no drifting background, no pulse', rm['wig'] == 0 and rm['w'] is None and rm['bg'] == 'none' and rm['go'] == 'none', rm)
        check('reduced motion: Bubu hidden', await page.evaluate("$('bubuBtn').hidden"))
        check('reduced motion: no page errors', not errs, errs); await ctx.close()

        # ===== 6. phase 1 guarantees on the new screen: the double-tap guard on the room switch; the camera's dwell selects stickers =====
        ctx, page, errs = await fresh(b, init="window.__graspTapGuard = true;")
        await page.wait_for_timeout(800)
        q = await page.evaluate("(() => { const r = $('littleBtn').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
        r2 = await page.evaluate(f"(() => {{ {M}.room('little', true); const r = document.querySelector('#littlePick [data-mode=busy]').getBoundingClientRect(); {M}.room('big', true); return [r.left + r.width / 2, r.top + 40]; }})()")  # (where the first sticker will be)
        await page.wait_for_timeout(700)  # (past the guard of that programmatic switch)
        await page.evaluate("window.__downs = []; document.addEventListener('pointerdown', (e) => __downs.push(performance.now()), true)")
        await page.touchscreen.tap(q[0], q[1]); await page.touchscreen.tap(r2[0], r2[1]); await page.wait_for_timeout(1300)  # (a quick double tap: the room switches under the finger)
        g = await page.evaluate("({ gap: __downs.length > 1 ? __downs[1] - __downs[0] : null, mode, start: !$('start').hidden, room: $('start').dataset.room, log: tapg.log.slice(-3) })")
        check('double-tap guard: a second tap right after the room switch (' + str(round(g['gap'] or 0)) + ' ms) lands on a sticker and is swallowed (no game starts)', g['room'] == 'little' and (g['gap'] is not None and g['gap'] >= 450 or (g['mode'] == 'none' and g['start'] and any(x.startswith('eat:') for x in g['log']))), g)
        check('guard: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, mobile=False, w=1280, h=800, camera=True, init="localStorage.setItem('inputPref','camera');")
        await page.click('#start button[data-mode=strike]'); await page.wait_for_function("!$('advMap').hidden", timeout=5000)
        await page.wait_for_function("__grasp.panelfix.homeCam.on", timeout=15000)
        await page.evaluate("$('advBack').click()"); await page.wait_for_timeout(300)
        r = await page.evaluate("(() => { const q = $('littleBtn').getBoundingClientRect(); return [q.left + q.width / 2, q.top + q.height / 2]; })()")
        await page.evaluate(f"window.__handFor = () => handAt({r[0]}, {r[1]}, 0.8)")
        await page.wait_for_function(in_room('little'), timeout=8000)
        check('camera: the hand held over "Little ones" switches the room', 'littleBtn' in await page.evaluate("__grasp.panelfix.homeCam.clicks"))
        r = await page.evaluate("(() => { const q = document.querySelector('#littlePick [data-mode=shapes]').getBoundingClientRect(); return [q.left + q.width / 2, q.top + q.height / 2]; })()")
        await page.evaluate(f"window.__handFor = () => handAt({r[0]}, {r[1]}, 0.8)")
        await page.wait_for_function("gameMode === 'shapes' && mode !== 'none'", timeout=12000)
        check('camera: ... and over a Little ones sticker it opens that game', 'shapes' in await page.evaluate("__grasp.panelfix.homeCam.clicks"))
        check('camera dwell: no page errors', not errs, errs); await ctx.close()

        # ===== full screen (the owner: Brave hides its own): a button on the start screen, one tap in, one tap out; it stays across a game and Home =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he, w=320, h=700); await page.wait_for_timeout(700)
            r = await page.evaluate("(() => { const a = $('fullBtn').getBoundingClientRect(); const gaps = ['settingsBtn', 'startSound', 'metaPill'].map(id => { const e = $(id).getBoundingClientRect(); return Math.max(e.left - a.right, a.left - e.right); }); return { hid: $('fullBtn').hidden, w: a.width, gap: Math.min(...gaps), bubu: $('bubuBtn').hidden, lbl: $('fullBtn').getAttribute('aria-label') }; })()")
            check(tg + ': the full screen button shows on the start screen (44 px, clear of the gear, the sound and the coins at 320 px; Bubu hidden), "' + r['lbl'] + '"', not r['hid'] and r['w'] >= 44 and r['gap'] >= 2 and r['bubu'] and r['lbl'] == ('מסך מלא' if he else 'Full screen'), r)
            await page.tap('#fullBtn'); await page.wait_for_timeout(500)
            r = await page.evaluate("({ fs: !!document.fullscreenElement, p: $('fullBtn').getAttribute('aria-pressed'), lbl: $('fullBtn').getAttribute('aria-label') })")
            check(tg + ': one tap: full screen, the button now says "' + r['lbl'] + '"', r['fs'] and r['p'] == 'true' and r['lbl'] == ('יציאה ממסך מלא' if he else 'Exit full screen'), r)
            await page.evaluate("routeOpen('popit')"); await page.wait_for_function("mode !== 'none'", timeout=8000); a1 = await page.evaluate("!!document.fullscreenElement")
            await page.evaluate("goHome()"); await page.wait_for_timeout(500); a2 = await page.evaluate("!!document.fullscreenElement")
            check(tg + ': ...it stays full screen in a game and back Home', a1 and a2, [a1, a2])
            await page.tap('#fullBtn'); await page.wait_for_timeout(500)
            check(tg + ': another tap: out of full screen', not await page.evaluate("!!document.fullscreenElement") and await page.evaluate("$('fullBtn').getAttribute('aria-pressed')") == 'false')
            check(tg + ' full screen: no page errors', not errs, errs); await ctx.close()

        # ===== full screen by itself when a game starts (touch devices; the owner: "full screen inside the games"); the button's exit keeps it off for the visit; not with a mouse =====
        ctx, page, errs = await fresh(b, False, w=390, h=844); await page.wait_for_timeout(700)
        await page.tap('#bigRoom [data-mode=slice]'); await page.wait_for_function("gameMode === 'slice' && mode !== 'none'", timeout=8000); await page.wait_for_timeout(400)
        a1 = await page.evaluate("!!document.fullscreenElement")
        await page.evaluate("goHome()"); await page.wait_for_timeout(500); a2 = await page.evaluate("!!document.fullscreenElement")
        check('a phone: a game starts in full screen by itself, and it stays back Home', a1 and a2, [a1, a2, await page.evaluate("__fsLog = fsA.log.slice()")])
        await page.tap('#fullBtn'); await page.wait_for_timeout(400); await page.tap('#bigRoom [data-mode=slice]'); await page.wait_for_function("gameMode === 'slice' && mode !== 'none'", timeout=8000); await page.wait_for_timeout(400)
        check('...the full screen button\'s exit: the next game stays as it is (not full screen) for this visit', not await page.evaluate("!!document.fullscreenElement") and await page.evaluate("sessionStorage.getItem('grasp.fsOff')") == '1')
        check('auto full screen: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, False, w=1280, h=800, mobile=False); await page.wait_for_timeout(700)
        await page.click('#bigRoom [data-mode=slice]'); await page.wait_for_function("gameMode === 'slice' && mode !== 'none'", timeout=8000); await page.wait_for_timeout(400)
        check('a computer (a mouse): no full screen by itself', not await page.evaluate("!!document.fullscreenElement"))
        check('desktop: no page errors', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
