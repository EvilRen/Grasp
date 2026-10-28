exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# home2 (parent-approved, from the 6-persona playtest): the start screen's new hierarchy, the simple end cards, gentler for parents.
# The hero continues the Adventure at the right stage (its world's colour; a new player: "Play"); the Little ones picker (Busy Board, Shapes,
# Sandbox, Calm bubbles) and the Arcade picker (Frenzy, the daily, Endless from world 2); the bottom tab bar (Play / Shop / Pet / Events: the sheets
# open above it, the tab lit, switching, Play / Escape close); the More sheet behind ⋯ (Tremorti, language, install, sound, voice, camera | touch);
# hidden until earned (the album, the pet's tab with its '!', the Road, the run powers, Endless); one popup a session (the gift calendar, else the
# pet's hatch, else the name sheet: never two at once); tips only after the first serve; the cards (<= 3 buttons + Share; no missions / XP / upsell;
# the toddler card); the Share sheet (the replay clip, Challenge a friend, Copy link); the gift calendar pauses on a missed day; no streak nags; no red
# dots but new rewards (cleared once seen); 44 px targets; no scroll at 360x740 / 390x844 / 1280x800, EN / HE; the camera dwell on the new screen;
# direct links. Screenshots: tests/out/home2_after_*.png (the before shots: tests/out/home2_before_*.png, taken from the previous start screen).
# Menu B (the Sticker Book, Oct 2026) moved things: the hero is a "Strike" sticker with a "Stage N" ribbon, Little ones is a room (the age switch),
# the tab bar is a dock (Shop, Pet, Events; no Play tab: nothing lit on the start screen), the More sheet sits behind the parents' gate (the lock;
# here opened through its hook), the Arcade / Little ones tiles are stickers. tests/test_menub.py covers the new screen itself.
A = "__grasp.adventure"; S = "__grasp.strike"; H = "__grasp.home2"; P = "__grasp.profile"; G = "__grasp.gifts"
OUT = 'tests/out/'
TOASTS = "__grasp.toasts.map(t => t.text)"

def prof(**kw):  # a stored profile (merged over the defaults by the game), seeded once a context
    d = dict(v=1, coins=0, xp=0); d.update(kw)
    return "if (!sessionStorage.getItem('__seeded')) { localStorage.setItem('grasp.profile', " + json.dumps(json.dumps(d)) + "); sessionStorage.setItem('__seeded', '1'); }"

def stars(n):  # stages 1..n cleared with 3 stars
    return {str(i): 3 for i in range(1, n + 1)}

async def fresh(b, mobile=True, he=False, init='', w=360, h=740, date='2026-10-02', camera=False):
    opts = dict(viewport={'width': w, 'height': h}, device_scale_factor=2, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': w if w != 360 else 1280, 'height': h if h != 740 else 800})
    if camera: opts['permissions'] = ['camera']
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + HAND_JS + "localStorage.setItem('lang','" + ('he' if he else 'en') + "');" + ("sessionStorage.setItem('grasp.testDate','" + date + "');" if date else '') + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_function("window.__grasp && __grasp.home2 && document.readyState === 'complete'", timeout=10000)
    await page.wait_for_timeout(400)
    return ctx, page, errs

async def tap(page, mobile, sel):
    if mobile: await page.tap(sel)
    else: await page.click(sel)

async def card_tap(page, E, key, mobile=True):  # a card button: a tap on the canvas at its centre, once the card is armed
    await page.wait_for_function(f"{E}.over && {E}.ui.buttons && {E}.ui.buttons.{key} && performance.now() - {E}.overAt > 700", timeout=10000)
    r = await page.evaluate(f"{E}.ui.buttons.{key}")
    if mobile: await page.tap('#stage', position={'x': r['x'] + r['w'] / 2, 'y': r['y'] + r['h'] / 2})
    else: await page.mouse.click(r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)

# the start screen: every button on it (>= 44 px, text >= 14 px), the tab bar, no scroll
SCREEN = """(() => { const r = (e) => { const q = e.getBoundingClientRect(); return { l: q.left, t: q.top, r: q.right, b: q.bottom, w: q.width, h: q.height }; }, st = $('start');
  const btns = [...st.querySelectorAll('button')].filter(b => b.offsetParent && !b.hidden && !b.closest('[inert]')).map(b => ({ id: b.id || b.dataset.mode || b.dataset.cg || b.className, ...r(b),
    fs: Math.min(99, ...[...b.querySelectorAll('b, span, small')].filter(x => x.offsetParent && x.textContent.trim() && !x.closest('.pv') && getComputedStyle(x).display !== 'none' && !x.classList.contains('bang') && !x.classList.contains('dot')).map(x => parseFloat(getComputedStyle(x).fontSize))) }));
  return { btns, noScroll: document.documentElement.scrollHeight <= innerHeight + 1 && document.documentElement.scrollWidth <= innerWidth + 1 && st.scrollHeight <= st.clientHeight + 1 && st.scrollWidth <= st.clientWidth + 1,
    W: innerWidth, H: innerHeight, hero: $('heroLbl').textContent, sub: $('heroSub').textContent, aria: $('heroPlay').getAttribute('aria-label'), dir: document.documentElement.dir, tabs: [...document.querySelectorAll('#tabBar .tab')].filter(b => !b.hidden).map(b => b.dataset.tab) }; })()"""

# the rooms' swiper (#mbRooms): settled on the room menub's mb.room names (the room off screen is inert, never hidden)
SETTLED = "(() => { const R = $('mbRooms'), m = __grasp.menub.mb, r = m.room; return !m.swiping && Math.abs(Math.abs(R.scrollLeft) - (r === 'little' ? R.clientWidth : 0)) < 2 && $('start').dataset.room === r && $('bigRoom').inert === (r !== 'big') && $('littlePick').inert === (r !== 'little') && !$('bigRoom').hidden && !$('littlePick').hidden; })()"
def in_room(r): return "__grasp.menub.mb.room === '" + r + "' && " + SETTLED

def screen_ok(tag, L, ntabs=2):
    on = lambda q: q['l'] >= -0.5 and q['t'] >= -0.5 and q['r'] <= L['W'] + 0.5 and q['b'] <= L['H'] + 0.5
    small = [b for b in L['btns'] if b['w'] < 44 or b['h'] < 44]
    tiny = [b for b in L['btns'] if b['fs'] < 14]
    check(tag + ': no scrolling either way; every button on screen', L['noScroll'] and all(on(b) for b in L['btns']), [b for b in L['btns'] if not on(b)])
    check(tag + ': every tap target >= 44 x 44 px', not small, small)
    check(tag + ': every label >= 14 px', not tiny, tiny)
    check(tag + ': the tab bar: ' + ', '.join(L['tabs']), len(L['tabs']) == ntabs, L['tabs'])

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ===== 1. the start screen: one screen at 360x740 / 390x844 / 1280x800, EN / HE; 44 px targets; the after screenshots =====
        for (mobile, w, h, nm) in ((True, 360, 740, 'phone'), (True, 390, 844, 'phone390'), (False, 1280, 800, 'desktop')):
            for he in (False, True):
                tag = nm + (' he' if he else ' en')
                ctx, page, errs = await fresh(b, mobile, he, w=w, h=h); await page.wait_for_timeout(1300)
                L = await page.evaluate(SCREEN)
                screen_ok(tag, L)
                ids = [x['id'] for x in L['btns']]
                check(tag + ': the hierarchy: the top bar (the gear, sound, full screen, the coins; Bubu hidden), the age switch, the hero (Play + its strip: Stage / Frenzy / Daily / Map), Smash, Slice, Pop It, Spot it, Mix it, Quest, the 4 camera games, the dock (Shop, Events)',
                      'bubuBtn' not in ids and all(k in ids for k in ('settingsBtn', 'startSound', 'fullBtn', 'metaPill', 'bigBtn', 'littleBtn', 'heroPlay', 'heroAdv', 'strike', 'frenzyChip', 'dailyBtn', 'smash', 'slice', 'bigPopit', 'spot', 'mix', 'quest', 'drums', 'bubbles', 'paint', 'stars', 'collectionBtn', 'todayBtn')) and len(ids) == 23, ids)  # (navigation v2: no Arcade, no Camera games sheet)  # (phase 1: the sound button; menu B: the gear (was the lock) instead of ⋯)
                hero = next(x for x in L['btns'] if x['id'] == 'heroPlay'); seg = [x for x in L['btns'] if x['id'] in ('heroAdv', 'frenzyChip', 'dailyBtn', 'strike')]
                check(tag + ': Strike is one card: its strip (Stage, Frenzy, Daily, Map) sits in one row inside the hero\'s bottom', len(seg) == 4 and all(s['l'] >= hero['l'] - 0.5 and s['r'] <= hero['r'] + 0.5 and s['t'] >= hero['t'] + hero['h'] / 2 and s['b'] <= hero['b'] + 0.5 for s in seg) and max(s['t'] for s in seg) - min(s['t'] for s in seg) < 6, [hero, seg])
                others = [x for x in L['btns'] if x['id'] in ('smash', 'slice', 'bigPopit', 'drums', 'stars')]
                check(tag + ': the hero is clearly the main thing: the widest button, above the grid', hero['w'] > 1.6 * max(o['w'] for o in others) and hero['b'] <= min(o['t'] for o in others), [hero, others])
                check(tag + ': a new player: the hero says "' + ('סטרייק' if he else 'Strike') + '" with "' + ('שלב 1' if he else 'Stage 1') + '" (aria: "' + L['aria'] + '")', L['hero'] == ('סטרייק' if he else 'Strike') and L['sub'] == ('שלב 1' if he else 'Stage 1') and L['aria'].startswith('לשחק' if he else 'Play'), L)
                check(tag + ': RTL in Hebrew', L['dir'] == ('rtl' if he else 'ltr'))
                check(tag + ': Bubu hidden (the pet lives only in the dock\'s Pet tab)', await page.evaluate("$('bubuBtn').hidden && $('bubuBtn').getBoundingClientRect().width === 0"))
                await page.screenshot(path=OUT + 'home2_after_start_%s_%s.png' % (nm, 'he' if he else 'en'))
                check(tag + ': no page errors', not errs, errs); await ctx.close()

        # ===== 2. the hero continues the Adventure at the right stage, in its world's colour =====
        ctx, page, errs = await fresh(b)
        await page.tap('#heroPlay')
        await page.wait_for_function(f"{A}.on && {A}.stage === 1 && mode === 'mouse' && $('start').hidden", timeout=10000)
        check('a new player: the hero plays stage 1 at once (touch)', await page.evaluate(f"[{A}.stage, gameMode, location.pathname]") == [1, 'strike', '/strike'])
        check('hero: no page errors', not errs, errs); await ctx.close()
        for he in (False, True):
            ctx, page, errs = await fresh(b, he=he, init=prof(adv={'stars': stars(4), 'unlocked': 5}))
            hh = await page.evaluate(f"({{ h: {H}.hero(), wc: getComputedStyle($('heroPlay')).getPropertyValue('--wc').trim(), want: WORLDS[0].accent }})")
            check(('HE' if he else 'EN') + ': stages 1-4 cleared: "' + hh['h']['label'] + '" + "' + hh['h']['sub'] + '"; its label says "' + hh['h']['aria'] + '", world 1\'s name; its colour', hh['h']['n'] == 5 and hh['h']['label'] == ('סטרייק' if he else 'Strike') and hh['h']['sub'] == ('שלב 5' if he else 'Stage 5') and hh['h']['aria'].startswith('לשחק בסטרייק — שלב 5' if he else 'Play Strike — Stage 5') and hh['h']['aria'].endswith(('סמטת הלבנים' if he else 'Brick Alley')) and hh['wc'].lower() == hh['want'].lower(), hh)
            await page.tap('#heroPlay')
            await page.wait_for_function(f"{A}.on && {A}.stage === 5 && mode === 'mouse'", timeout=10000)
            check(('HE' if he else 'EN') + ': the hero plays stage 5', True)
            check('hero 5: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, init=prof(adv={'stars': stars(11), 'unlocked': 12}))
        hh = await page.evaluate(f"({{ h: {H}.hero(), wc: getComputedStyle($('heroPlay')).getPropertyValue('--wc').trim(), want: WORLDS[1].accent }})")
        check('world 2: "Strike" + "Stage 12", World 2 (in its label) and its colour', hh['h']['n'] == 12 and hh['h']['w'] == 2 and hh['h']['sub'] == 'Stage 12' and 'Play Strike — Stage 12, World 2' in hh['h']['aria'] and hh['wc'].lower() == hh['want'].lower(), hh)
        await page.screenshot(path=OUT + 'home2_after_hero_world2.png')
        await page.tap('#start button[data-mode=strike]'); await page.wait_for_function("!$('advMap').hidden", timeout=5000)
        check("the hero's Map opens the Adventure map (choose any stage there)", await page.evaluate("advMapOpen() && mode === 'none'"))
        check('hero world 2: no page errors', not errs, errs); await ctx.close()

        # ===== 3. the Little ones picker; the Arcade picker; direct links =====
        for he in (False, True):
            ctx, page, errs = await fresh(b, he=he)
            await page.tap('#littleBtn'); await page.wait_for_function(in_room('little'), timeout=3000); await page.wait_for_timeout(500)
            lp = await page.evaluate("""(() => { const P = $('littlePick'); return { items: [...P.querySelectorAll('.mbPg .stk:not(.tgTile)')].map(b => { const q = b.getBoundingClientRect(); return [b.dataset.mode || b.id, b.querySelector('.lb').textContent.trim(), q.width >= 120 && q.height >= 120 && q.left >= 0 && q.right <= innerWidth + 0.5 && q.bottom <= innerHeight]; }), x: $('bigBtn').getBoundingClientRect().height }; })()""")
            names = ['לוח פעילות', 'צורות', 'ארגז חול', 'בועות רגועות'] if he else ['Busy Board', 'Shapes', 'Sandbox', 'Calm bubbles']
            check(('HE' if he else 'EN') + ': Little ones (menu B: a room, its first page): Busy Board, Shapes, Sandbox, Calm bubbles; big, on screen; the way back (Big kids) >= 44 px', [i[0] for i in lp['items']] == ['busy', 'shapes', 'sandbox', 'calmBtn'] and [i[1] for i in lp['items']] == names and all(i[2] for i in lp['items']) and lp['x'] >= 44, lp)
            await page.screenshot(path=OUT + 'home2_after_little_%s.png' % ('he' if he else 'en'))
            if not he:
                for m in ('busy', 'shapes', 'sandbox'):
                    if await page.evaluate("__grasp.menub.mb.room !== 'little'"): await page.tap('#littleBtn')
                    await page.wait_for_function(in_room('little'), timeout=3000); await page.wait_for_timeout(400)
                    await page.tap('#littlePick button[data-mode=%s]' % m)
                    await page.wait_for_function(f"gameMode === '{m}' && mode === 'mouse' && $('start').hidden", timeout=8000)
                    check('Little ones: ' + m + ' starts (after its name; menu B: the room stays for the way back)', True)
                    await page.evaluate("goHome()"); await page.wait_for_timeout(250)
                await page.tap('#littleBtn'); await page.wait_for_function(in_room('little'), timeout=3000); await page.wait_for_timeout(400); await page.tap('#calmBtn')
                await page.wait_for_function("gameMode === 'bubbles' && mode === 'mouse'", timeout=8000)
                check('Little ones: Calm bubbles = Bubble Pop with Calm on (no timer; navigation v2: not stored for the big kids\' Bubble Pop)', await page.evaluate("__grasp.cg.bubbles.calm === true && localStorage.getItem('bubblesCalm') !== '1'"))
                await page.evaluate("goHome()"); await page.wait_for_timeout(250)
                await page.tap('#littleBtn'); await page.wait_for_function(in_room('little'), timeout=3000); await page.wait_for_timeout(400); await page.keyboard.press('Escape'); await page.wait_for_timeout(150)
                await page.wait_for_function(SETTLED, timeout=3000)
                check('Little ones: Escape goes back to Big kids (Little ones inert, off screen)', await page.evaluate("__grasp.menub.mb.room === 'big' && $('littlePick').inert && !$('bigRoom').inert && $('bigBtn').getAttribute('aria-pressed') === 'true'"))
            check('little: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, init=prof(frenzy={'best': 12, 'top': 1.4, 'runs': 2}))
        ar = await page.evaluate("({ frz: !$('frenzyChip').hidden, daily: !$('dailyBtn').hidden && !!$('dailyBtn').closest('#heroModes'), endless: !$('endlessChip').hidden, mapEndless: $('advEndless').hidden })")
        check('Strike\'s chips (navigation v2: the Arcade dissolved): Frenzy and the daily; Endless hidden until world 2 (on the map too)', ar['frz'] and ar['daily'] and not ar['endless'] and ar['mapEndless'], ar)
        PK = "({ mode, start: !$('start').hidden, on: [...document.querySelectorAll('#heroModes .mbSeg:not(.heroMap)')].filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.id), sub: $('heroSub').textContent, mem: localStorage.getItem('grasp.heroMode') })"
        await page.tap('#frenzyChip'); await page.wait_for_timeout(300); pk = await page.evaluate(PK)
        check('the Frenzy chip only picks Frenzy (pressed, the ribbon says Frenzy, remembered; no game yet)', pk['mode'] == 'none' and pk['start'] and pk['on'] == ['frenzyChip'] and pk['sub'] == 'Frenzy' and pk['mem'] == 'frenzy', pk)
        pl = await page.evaluate("(() => { const g = document.querySelector('#heroPlay .go'); return { picked: $('hero').classList.contains('picked'), anim: getComputedStyle(g).animationName, ring: getComputedStyle(g, '::after').animationName }; })()")
        check('...and the Play button calls (it jumps, rings go out of it; the owner: \"why don\'t Frenzy and Daily work?\")', pl['picked'] and 'heroGoJump' in pl['anim'] and pl['ring'] == 'heroGoPing', pl)
        await page.tap('#heroPlay'); await page.wait_for_function("__grasp.frenzy.on && mode === 'mouse'", timeout=8000)
        check('...the card\'s Play: Frenzy starts (the call stops)', not await page.evaluate("$('hero').classList.contains('picked')"))
        check('...the card\'s Play: Frenzy starts', await page.evaluate("location.pathname") == '/frenzy')
        await page.evaluate("goHome()"); await page.wait_for_timeout(450)
        check('back Home: Frenzy still picked', (await page.evaluate(PK))['on'] == ['frenzyChip'])
        await page.tap('#dailyBtn'); await page.wait_for_timeout(300); pk = await page.evaluate(PK)
        check('the Daily chip only picks the daily (no game, no panel yet)', pk['mode'] == 'none' and pk['on'] == ['dailyBtn'] and pk['mem'] == 'daily' and await page.evaluate("[...document.querySelectorAll('.ov')].filter(o => !o.hidden).map(o => o.id)") == [], pk)
        await page.tap('#heroPlay'); await page.wait_for_function("__grasp.daily.on && mode === 'mouse'", timeout=8000)
        check('...the card\'s Play: today\'s run at once (no panel first)', await page.evaluate("[...document.querySelectorAll('.ov')].filter(o => !o.hidden).map(o => o.id)") == [])
        check('chips: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, init=prof(adv={'stars': stars(8), 'unlocked': 9}))
        check('world 2 reached: the Endless chip shows (and Endless on the map)', await page.evaluate("!$('endlessChip').hidden && (renderAdvMap(), !$('advEndless').hidden)"))
        await page.tap('#endlessChip'); await page.wait_for_timeout(300)
        check('the Endless chip only picks Endless', await page.evaluate("mode === 'none' && $('endlessChip').getAttribute('aria-pressed') === 'true' && $('heroSub').textContent === 'Endless'"))
        await page.tap('#heroPlay'); await page.wait_for_function("mode === 'mouse' && gameMode === 'strike' && !__grasp.adventure.on && !__grasp.frenzy.on", timeout=8000)
        check('...the card\'s Play: the old run', True)
        await ctx.close()
        for path, m in (('/busy', 'busy'), ('/shapes', 'shapes'), ('/sandbox', 'sandbox'), ('/slice', 'slice')):
            ctx = await b.new_context(viewport={'width': 360, 'height': 740}, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs = []
            page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT)
            await page.goto('http://localhost:8765' + path)
            await page.wait_for_function(f"window.__grasp && gameMode === '{m}' && mode === 'mouse' && $('start').hidden", timeout=10000)
            check('the direct link ' + path + ' still starts ' + m, not errs, errs); await ctx.close()

        # ===== 4. the tab bar: Play / Shop / Pet / Events; the sheets above it; switching; Play / Escape close =====
        ctx, page, errs = await fresh(b, init=prof(pet={'hatched': True, 'food': 3, 'pantry': 2, 'born': '2026-10-01', 'last': '2026-10-01'}))
        TB = """(() => { const bar = $('tabBar').getBoundingClientRect(), open = [...document.querySelectorAll('.ov')].filter(o => !o.hidden).map(o => ({ id: o.id, tabbed: o.classList.contains('tabbed'), b: o.querySelector('.sheet').getBoundingClientRect().bottom }));
          return { on: [...document.querySelectorAll('#tabBar .tab.on')].map(b => b.dataset.tab), cur: [...document.querySelectorAll('#tabBar .tab[aria-current=page]')].map(b => b.dataset.tab), open, barTop: bar.top, tab: __grasp.home2.h2.tab }; })()"""
        for tab, ov in (('collectionBtn', 'collection'), ('petTab', 'petRoom'), ('todayBtn', 'today')):
            await page.tap('#' + tab); await page.wait_for_timeout(450)
            t = await page.evaluate(TB)
            want = {'collectionBtn': 'shop', 'petTab': 'pet', 'todayBtn': 'today'}[tab]
            check('tab ' + want + ': its sheet opens above the bar (the bar stays), the tab lit (aria-current), the other sheets closed', t['on'] == [want] and t['cur'] == [want] and [o['id'] for o in t['open']] == [ov] and t['open'][0]['tabbed'] and t['open'][0]['b'] <= t['barTop'] + 1, t)
            await page.screenshot(path=OUT + 'home2_after_tab_%s.png' % want)
        await page.evaluate("__grasp.home2.tab('play')"); await page.wait_for_timeout(250)
        t = await page.evaluate(TB)
        check('back to the start screen (no sheet; menu B: no Play tab, so nothing lit)', t['on'] == [] and not t['open'] and t['tab'] == 'play', t)
        await page.tap('#todayBtn'); await page.wait_for_timeout(400); await page.keyboard.press('Escape'); await page.wait_for_timeout(200)
        t = await page.evaluate(TB)
        check('Escape closes the tab\'s sheet; nothing lit again', t['on'] == [] and not t['open'], t)
        await page.tap('#collectionBtn'); await page.wait_for_timeout(400); await page.evaluate("$('collection').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }))"); await page.wait_for_timeout(200)
        check('a tap beside the sheet closes it too', (await page.evaluate(TB))['on'] == [] and not (await page.evaluate(TB))['open'])
        check('tabs: no page errors', not errs, errs); await ctx.close()

        # ===== 5. the More sheet: Tremorti, language, install, sound, voice, camera | touch =====
        for he in (False, True):
            ctx, page, errs = await fresh(b, he=he)
            await page.evaluate("window.dispatchEvent(Object.assign(new Event('beforeinstallprompt', { cancelable: true }), { prompt: () => { window.__prompted = (window.__prompted || 0) + 1; return Promise.resolve(); }, userChoice: Promise.resolve({ outcome: 'accepted' }) }))")
            await page.tap('#settingsBtn'); await page.wait_for_function("!$('moreSheet').hidden", timeout=1000); await page.wait_for_timeout(450)
            check(('HE' if he else 'EN') + ': the gear opens the settings in one tap (no parents\' gate)', await page.evaluate("!document.getElementById('gate') && $('settingsBtn').getAttribute('aria-expanded') === 'true'"))
            mo = await page.evaluate("""(() => { const S = $('moreSheet'), sh = S.querySelector('.sheet').getBoundingClientRect(), rows = [...S.querySelectorAll('.moreRow')].filter(r => !r.hidden && r.offsetParent).map(r => { const q = r.getBoundingClientRect(); return { id: r.id || r.className, h: q.height, in: q.left >= sh.left && q.right <= sh.right + 0.5 && q.bottom <= innerHeight }; });
              return { rows, link: $('tremortiLink').getAttribute('href'), linkTx: $('tremortiLink').textContent.trim(), lang: $('startLang').textContent.trim(), install: !$('installBtn').hidden, cam: $('camBtn').textContent.trim(), touch: $('mouseBtn').getAttribute('aria-pressed'),
                sound: $('moreSound').getAttribute('aria-pressed'), voice: String($('voiceOff').getAttribute('aria-pressed') !== 'true'), small: [...S.querySelectorAll('button, a')].filter(e => e.offsetParent).map(e => e.getBoundingClientRect()).filter(q => q.height < 44 || q.width < 44).length, expanded: $('settingsBtn').getAttribute('aria-expanded') }; })()""")
            tg = 'HE' if he else 'EN'
            check(tg + ': More (the gear): the language, Camera | Touch, Sound, Voice, Stats (navigation v2: from the pause sheet), Install app, the Tremorti link; every row inside, >= 44 px', len(mo['rows']) == 7 and all(r['in'] and r['h'] >= 44 for r in mo['rows']) and mo['small'] == 0 and mo['expanded'] == 'true', mo)
            check(tg + ': the Tremorti link goes to /tremorti/ (' + mo['linkTx'] + ')', mo['link'] == '/tremorti/' and mo['linkTx'] == ('טרמורטי · מד רעד' if he else 'Tremorti · tremor meter'), mo)
            check(tg + ': Touch is the default way to play; sound and voice on; Install offered (the browser offered it)', mo['touch'] == 'true' and mo['sound'] == 'true' and mo['voice'] == 'true' and mo['install'], mo)
            await page.screenshot(path=OUT + 'home2_after_more_%s.png' % ('he' if he else 'en'))
            if not he:
                await page.tap('#moreSound'); await page.wait_for_timeout(100)
                check('Sound: off (muted, saved)', await page.evaluate("muted === true && localStorage.getItem('muted') === '1' && $('moreSound').getAttribute('aria-pressed') === 'false'"))
                await page.tap('#moreSound'); await page.tap('#voiceOff'); await page.wait_for_timeout(100)
                check('Voice: Off (Names · All · Off; profile.grippy follows); Sound back on', await page.evaluate("profile.grippy === false && muted === false && $('voiceOff').getAttribute('aria-pressed') === 'true'"))
                await page.tap('#voiceAll'); await page.tap('#camBtn'); await page.wait_for_timeout(150)
                check('Camera | Touch: Camera chosen and remembered (the existing pref)', await page.evaluate("inputPref() === 'camera' && localStorage.getItem('inputPref') === 'camera'"))
                await page.tap('#mouseBtn'); await page.wait_for_timeout(100)
                check('...Touch again', await page.evaluate("inputPref() === 'mouse'"))
                await page.tap('#installBtn'); await page.wait_for_function("__grasp.pwa.state.log.includes('choice:accepted')", timeout=5000)
                check('Install app: the browser\'s prompt (once); the More sheet closes', await page.evaluate("window.__prompted === 1 && $('moreSheet').hidden"))
                await page.evaluate("__grasp.home2.more(true)"); await page.wait_for_timeout(400); await page.tap('#startLang'); await page.wait_for_timeout(200)
                check('the language row switches to Hebrew (RTL) and back', await page.evaluate("document.documentElement.dir === 'rtl' && lang === 'he'"))
                await page.tap('#startLang'); await page.wait_for_timeout(150)
                check('...English again', await page.evaluate("lang === 'en'"))
                await page.keyboard.press('Escape'); await page.wait_for_timeout(150)
                check('Escape closes the More sheet', await page.evaluate("$('moreSheet').hidden && $('settingsBtn').getAttribute('aria-expanded') === 'false'"))
            check('more: no page errors', not errs, errs); await ctx.close()

        # ===== 6. hidden until earned: the pet (the first round finished, not a failed stage), the album, the Road, the run powers, Endless =====
        ctx, page, errs = await fresh(b, init="localStorage.setItem('inputPref','mouse');")
        e0 = await page.evaluate("({ tab: !$('petTab').hidden, lv: getComputedStyle($('metaPill').querySelector('.lvl')).display, xp: getComputedStyle($('metaPill').querySelector('.xp')).display, egg: profile.pet.egg })")
        check('a new player: no Pet tab, no level / XP on the pill (the Road not earned), no egg', not e0['tab'] and e0['lv'] == 'none' and e0['xp'] == 'none' and not e0['egg'], e0)
        await page.evaluate(f"{A}.start(1, 'mouse')"); await page.wait_for_function(f"{A}.on && {A}.phase === 'play'", timeout=8000)
        await page.evaluate(f"{A}.failTest()"); await page.wait_for_function(f"{S}.over && {S}.ui.buttons", timeout=8000)
        check('a failed stage does not earn the egg', not await page.evaluate("profile.pet.egg"))
        await page.evaluate("goHome()"); await page.wait_for_timeout(200)
        check('...no Pet tab yet', await page.evaluate("$('petTab').hidden"))
        await page.evaluate("__grasp.setGameMode('slice')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse' && gameMode === 'slice'", timeout=5000)
        await page.evaluate("sliceLoseLife(performance.now()); sliceLoseLife(performance.now()); sliceLoseLife(performance.now())")
        await page.wait_for_function("__grasp.slice.over && __grasp.slice.ui.buttons", timeout=5000)
        check('the first round finished (Slice): the egg is earned', await page.evaluate("profile.pet.egg === true && !profile.pet.hatched"))
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        pt = await page.evaluate("({ tab: !$('petTab').hidden, bang: !$('petTab').querySelector('.bang').hidden, tabs: [...document.querySelectorAll('#tabBar .tab')].filter(b => !b.hidden).map(b => b.dataset.tab), h: $('petTab').getBoundingClientRect().height })")
        check('home: the Pet sticker appears in the dock with a "!" (Shop, Pet, Events)', pt['tab'] and pt['bang'] and pt['tabs'] == ['shop', 'pet', 'today'] and pt['h'] >= 44, pt)
        await page.screenshot(path=OUT + 'home2_after_pet_tab.png')
        await page.tap('#petTab'); await page.wait_for_timeout(400)
        check('the room seen: the "!" goes away (and stays away after a reload)', await page.evaluate("$('petTab').querySelector('.bang').hidden && profile.pet.eggSeen === true"))
        await page.evaluate("__grasp.addXp(200)"); await page.wait_for_timeout(100)
        check('the first level-up: the pill shows the level + XP bar; it opens the Road', await page.evaluate("getComputedStyle($('metaPill').querySelector('.lvl')).display !== 'none'"))
        await page.evaluate("__grasp.road.closeCard && __grasp.road.closeCard(); __grasp.home2.tab('play')"); await page.wait_for_timeout(500)
        await page.evaluate("for (const o of document.querySelectorAll('.ov')) o.hidden = true"); await page.tap('#metaPill'); await page.wait_for_timeout(200)
        check('...the pill opens the Road', await page.evaluate("!$('road').hidden"))
        check('earned: no page errors', not errs, errs); await ctx.close()
        # the run powers: not in world 1, from world 2
        ctx, page, errs = await fresh(b, init=prof(adv={'stars': stars(2), 'unlocked': 3}))
        await page.evaluate(f"{A}.start(3, 'mouse')"); await page.wait_for_function(f"{A}.on && {A}.stage === 3 && {A}.phase === 'play'", timeout=8000)
        await page.evaluate(f"{A}.finishTest(0)"); await card_tap(page, S, 'next')
        await page.wait_for_function(f"{A}.stage === 4 && {A}.phase === 'play'", timeout=8000)
        check('world 1: Next plays the next stage at once (no run-power cards)', not await page.evaluate(f"{S}.perkOffer"))
        await ctx.close()
        ctx, page, errs = await fresh(b, init=prof(adv={'stars': stars(9), 'unlocked': 10}))
        await page.evaluate(f"{A}.start(10, 'mouse')"); await page.wait_for_function(f"{A}.on && {A}.stage === 10 && {A}.phase === 'play'", timeout=8000)
        await page.evaluate(f"{A}.finishTest(0)"); await card_tap(page, S, 'next')
        await page.wait_for_function(f"{S}.perkOffer && {S}.perkMode === 'run'", timeout=8000)
        check('world 2: Next offers the run powers', True)
        check('run powers: no page errors', not errs, errs); await ctx.close()

        # ===== 7. one popup a session: on open the pet's hatch, else the name sheet; the gift calendar only after a round (phase 1); never two at once =====
        OPEN = "[...document.querySelectorAll('.ov, #newCard')].filter(o => !o.hidden).map(o => o.id)"
        ctx, page, errs = await fresh(b, init="window.__graspPopups = true; window.__graspGiftAuto = true;" + prof(pet={'egg': True, 'pantry': 1}))
        await page.wait_for_function(H + ".h2.popup", timeout=4000); await page.wait_for_timeout(600)
        o1 = await page.evaluate(OPEN)
        check('session start, a gift due and an egg earned: nothing pops up (navigation v2): the Pet tab glows for the hatch (Bubu hidden); phase 1: the calendar never on open', o1 == [] and await page.evaluate(H + ".h2.popup") == 'hatch' and await page.evaluate("$('petTab').dataset.call") == 'hatch' and await page.evaluate("$('petTab').classList.contains('mbCall') && $('bubuBtn').hidden") and await page.evaluate("__grasp.pet.state.stage") == 0, o1)
        await page.screenshot(path=OUT + 'home2_after_popup_hatch.png')
        await page.tap('#petTab'); await page.wait_for_function("!$('petRoom').hidden", timeout=3000)
        check('...a tap on the glowing Pet tab: the room with the egg (the glow cleared)', await page.evaluate(OPEN) == ['petRoom'] and await page.evaluate("!$('petTab').classList.contains('mbCall')"))
        for i in range(5): await page.tap('#petRoomCv'); await page.wait_for_timeout(80)
        await page.wait_for_function("__grasp.pet.state.nameOpen", timeout=4000)
        await page.tap('#petNameSkip'); await page.wait_for_timeout(200)
        await page.evaluate("__grasp.home2.tab('play')"); await page.wait_for_timeout(200)
        await page.evaluate("h2.rounds = 1; goHome()"); await page.wait_for_timeout(500)
        check('a round later, back home: no second popup in this session (the gift waits)', await page.evaluate(OPEN) == [] and not await page.evaluate(G + ".shown"))
        await page.evaluate("profile.pet.asked = false; saveProfile()")
        await page.reload(); await page.wait_for_function("window.__grasp && __grasp.home2", timeout=8000); await page.wait_for_timeout(900)
        o4 = await page.evaluate(OPEN)
        check('a hatched pet never named (the sheet missed): the session\'s one call is the name (the Pet tab glows; nothing pops up)', o4 == [] and await page.evaluate(H + ".h2.popup") == 'name' and await page.evaluate("$('petTab').dataset.call") == 'name' and await page.evaluate("$('petTab').classList.contains('mbCall')"), o4)
        await page.tap('#petTab'); await page.wait_for_function("!$('petName').hidden", timeout=3000)
        check('...a tap on the glowing Pet tab: the name sheet', await page.evaluate("!$('petName').hidden && !$('petTab').classList.contains('mbCall')"))
        await page.tap('#petNameSkip'); await page.wait_for_timeout(200)
        await page.reload(); await page.wait_for_function("window.__grasp && __grasp.home2", timeout=8000); await page.wait_for_timeout(900)
        check('nothing due on open: no popup at all (the gift calendar waits for a round)', await page.evaluate(OPEN) == [] and await page.evaluate(H + ".h2.popup") is None)
        await page.evaluate("h2.rounds = 1; goHome()"); await page.wait_for_function(G + ".shown", timeout=4000); await page.wait_for_timeout(400)
        check('...a round finished, back home: the gift calendar, alone', await page.evaluate(OPEN) == ['gifts'] and await page.evaluate(H + ".h2.popup") == 'gift')
        await page.screenshot(path=OUT + 'home2_after_popup_gift.png')
        await page.tap('#giftOk'); await page.wait_for_function("document.querySelector('.gbox.today.opened')", timeout=3000); await page.wait_for_timeout(500); await page.tap('#giftOk'); await page.wait_for_timeout(500)
        check('the calendar closed: no second popup in this session', await page.evaluate(OPEN) == [])
        check('under automation (no opt-in) the suites never see a popup', await page.evaluate(H + ".popupOk()"))
        check('popups: no page errors', not errs, errs); await ctx.close()

        # ===== 8. tips only after the first serve =====
        ctx, page, errs = await fresh(b)
        await page.evaluate("setInputPref('mouse'); __grasp.setGameMode('strike'); strikeEndless('mouse')"); await page.wait_for_function(f"mode === 'mouse' && {S}.waiting", timeout=8000)
        tp = await page.evaluate("(() => { const a = tipOnce('weak'); return { a, show: $('hint').classList.contains('show') && $('hint').querySelector('.tx').textContent === t('tipWeak'), q: __grasp.home2.h2.tipQ }; })()")
        check('a tip before the first serve: held back (not over the start of the round)', tp['a'] and not tp['show'] and tp['q'] == await page.evaluate("t('tipWeak')"), tp)
        await page.evaluate(f"{S}.playerServe('medium')")
        await page.wait_for_function("$('hint').classList.contains('show') && $('hint').querySelector('.tx').textContent === t('tipWeak')", timeout=3000)
        check('...the first serve: it shows', True)
        check('tips: no page errors', not errs, errs); await ctx.close()

        # ===== 9. the cards: <= 3 buttons + Share; no missions / XP / upsell; the toddler card =====
        CARD = """((E) => { const u = E.ui; return { keys: Object.keys(u.buttons || {}), labels: u.labels || u.advLabels, missions: (u.missionRow || []).length, xp: !!u.xpBox, teaser: !!u.teaser, rp: !!u.rpBtn, coin: u.coinBox ? u.coinBox.n : null, card: u.card, best: u.bestChip || u.advBestChip || null, rank: u.advScore ? u.advScore.rank : null,
          inside: Object.values(u.buttons || {}).every(r => r.x >= u.card.x - 1 && r.x + r.w <= u.card.x + u.card.w + 1 && r.y + r.h <= u.card.y + u.card.h + 1 && r.h >= 44) }; })"""
        def card_ok(tag, c, keys):
            check(tag + ': buttons ' + ' / '.join(keys) + ' (<= 3 with Share), inside the card, >= 44 px', c['keys'] == keys and len(c['keys']) <= 3 and c['inside'], c)
            check(tag + ': no missions, no XP pill, no coin upsell, no Replay pill (merged into Share)', c['missions'] == 0 and not c['xp'] and not c['teaser'] and not c['rp'], c)
        ctx, page, errs = await fresh(b, init="localStorage.setItem('inputPref','mouse');" + prof(coins=40, adv={'stars': {'1': 3, '2': 3, '3': 3}, 'unlocked': 4, 'best': {'4': 100}}, missions={'date': '2026-10-02', 'list': [{'id': 'walls', 'goal': 6, 'progress': 1, 'reward': 22, 'done': False, 'claimed': False}, {'id': 'fruit', 'goal': 15, 'progress': 0, 'reward': 15, 'done': False, 'claimed': False}, {'id': 'rounds', 'goal': 3, 'progress': 0, 'reward': 10, 'done': False, 'claimed': False}]}))
        await page.evaluate(f"{A}.start(4, 'mouse')"); await page.wait_for_function(f"{A}.on && {A}.phase === 'play' && {S}.walls.length", timeout=8000)  # (phase 1: a stage 4 record: Share, and its sheet's challenge (none on stages 1-3))
        await page.evaluate(f"{S}.score = 640"); await page.evaluate(f"{A}.finishTest(1)")
        await page.wait_for_function(f"{S}.over && {S}.ui.advScore && {S}.ui.advScore.a >= 1 && {S}.ui.advStars.shown === 2", timeout=10000); await page.wait_for_timeout(500)
        c = await page.evaluate(CARD + f"({S})")
        card_ok('Adventure clear', c, ['next', 'home', 'share'])  # (navigation v2: the big one, Home, then Share on a record (else Map))
        check('Adventure clear: Next is the big one; stars + the score with NEW RECORD! (phase 1: a record, hence Share), no rank badge', c['labels']['next'] == 'Next' and c['rank'] is None and await page.evaluate(f"!!{S}.ui.advRecord"), c)
        await page.screenshot(path=OUT + 'home2_after_card_adv.png')
        # the Share sheet: Replay clip (when made), Challenge a friend, Copy link
        await page.evaluate("Object.defineProperty(navigator, 'share', { configurable: true, value: undefined }); window.__clip = []; navigator.clipboard.writeText = async (t) => { __clip.push(t); }; profile.duelAsked = true; profile.duelName = 'Noa'")
        await card_tap(page, S, 'share')
        await page.wait_for_function("!$('shareSheet').hidden", timeout=3000); await page.wait_for_timeout(500)
        sh = await page.evaluate("""(() => { const S = $('shareSheet'), sh = S.querySelector('.sheet').getBoundingClientRect(); return { rows: [...S.querySelectorAll('.shRow')].filter(r => !r.hidden).map(r => [r.id, r.querySelector('b').textContent, r.getBoundingClientRect().height]), inside: sh.top >= 0 && sh.bottom <= innerHeight, over: __grasp.strike.over }; })()""")
        check('Share: a small sheet over the card: Challenge a friend, Copy link (+ Replay clip once made); big rows', [r[0] for r in sh['rows'] if r[0] != 'shReplay'] == ['shDuel', 'shCopy'] and all(r[2] >= 44 for r in sh['rows']) and sh['inside'] and sh['over'], sh)
        await page.screenshot(path=OUT + 'home2_after_share_sheet.png')
        await page.mouse.move(100, 100); await page.mouse.move(300, 600, steps=3); await page.wait_for_timeout(1100)
        check('while the sheet is up the card waits (a wave does not play on)', await page.evaluate(f"{S}.over && {A}.stage === 4"))
        await page.tap('#shCopy'); await page.wait_for_function("__clip.length === 1", timeout=3000)
        cp = await page.evaluate("({ clip: __clip[0], toast: __grasp.toasts.some(x => x.key === 'linkCopied'), hidden: $('shareSheet').hidden })")
        check('Copy link: the challenge link (stage 4, the score, the name) to the clipboard, "Link copied!", the sheet closes', '/duel?m=adv&s=4&score=640' in cp['clip'] and 'by=Tm9h' in cp['clip'] and cp['toast'] and cp['hidden'], cp)
        await card_tap(page, S, 'share'); await page.wait_for_function("!$('shareSheet').hidden", timeout=3000); await page.wait_for_timeout(500)
        await page.tap('#shDuel'); await page.wait_for_function("__clip.length === 2", timeout=3000)
        check('Challenge a friend: the challenge line + link shared (here: the clipboard)', await page.evaluate("__clip[1].startsWith('I scored 640 on Grasp stage 4') && __clip[1].includes('/duel?m=adv&s=4')"), await page.evaluate("__clip"))
        await page.wait_for_function("__grasp.replay.ready()", timeout=15000)
        await card_tap(page, S, 'share'); await page.wait_for_function("!$('shareSheet').hidden && !$('shReplay').hidden && !$('shReplay').disabled", timeout=5000); await page.wait_for_timeout(500)
        await page.tap('#shReplay'); await page.wait_for_function("__grasp.replay.rp.open && $('shareSheet').hidden", timeout=6000)
        check('Replay clip: the replay sheet plays the round\'s best moment (and only it is open)', await page.evaluate("[...document.querySelectorAll('.ov')].filter(o => !o.hidden).map(o => o.id)") == ['replay'])
        await page.evaluate("__grasp.replay.close()"); await page.wait_for_timeout(300)
        check('cards / share: no page errors', not errs, errs); await ctx.close()
        # Endless (HE phone), Slice, Smash: the shared round-over card
        ctx, page, errs = await fresh(b, he=True, init="localStorage.setItem('inputPref','mouse');" + prof(coins=900))
        await page.evaluate("setInputPref('mouse'); __grasp.setGameMode('strike'); strikeEndless('mouse')"); await page.wait_for_function(f"mode === 'mouse' && {S}.walls.length", timeout=8000)
        await page.evaluate(f"(() => {{ const s = {S}; s.score = 321; s.lives = 1; s.setBallZ(100, 180, 420); strikeMiss(s.ball, performance.now()); }})()")
        await page.wait_for_function(f"{S}.over && {S}.ui.buttons && performance.now() - {S}.overAt > 800", timeout=8000)
        c = await page.evaluate(CARD + f"({S})")
        card_ok('Endless (HE)', c, ['again', 'home', 'share'])
        check('Endless (HE): a first run: no best chip that only repeats the score, no "+0" (game feel); +coins only', c['best'] is None and (c['coin'] is None or c['coin'] > 0) and c['labels'] == {'again': 'לשחק שוב', 'home': 'בית', 'share': 'שיתוף ⤴'}, c)
        await page.screenshot(path=OUT + 'home2_after_card_endless_he.png')
        await page.evaluate("goHome()"); await page.wait_for_timeout(200)
        await page.evaluate("__grasp.setGameMode('slice')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse' && gameMode === 'slice'", timeout=5000)
        await page.evaluate("__grasp.slice.score = 9; sliceLoseLife(performance.now()); sliceLoseLife(performance.now()); sliceLoseLife(performance.now())")
        await page.wait_for_function("__grasp.slice.over && __grasp.slice.ui.buttons && performance.now() - __grasp.slice.overAt > 800", timeout=5000)
        c = await page.evaluate(CARD + "(__grasp.slice)")
        card_ok('Slice (HE, 900 coins: nothing to upsell)', c, ['again', 'home', 'share'])
        await page.screenshot(path=OUT + 'home2_after_card_slice.png')
        await page.evaluate("Object.defineProperty(navigator, 'share', { configurable: true, value: undefined }); window.__clip = []; navigator.clipboard.writeText = async (t) => { __clip.push(t); }; 0")  # (the trailing 0: an expression ending in a function would be called by evaluate)
        await card_tap(page, "__grasp.slice", 'share'); await page.wait_for_function("!$('shareSheet').hidden", timeout=3000); await page.wait_for_timeout(500)
        check('Slice\'s Share: no challenge (Strike only); Copy link', await page.evaluate("$('shDuel').hidden && !$('shCopy').hidden"))
        await page.tap('#shCopy'); await page.wait_for_function("__clip.length === 1", timeout=3000)
        check('Copy link: the game\'s own page (/slice)', (await page.evaluate("__clip[0]")).endswith('/slice'), await page.evaluate("__clip"))
        check('shared card: no page errors', not errs, errs); await ctx.close()
        # the toddler card (Shapes) and a camera game's card (Bubble Pop: stars, no Share)
        ctx, page, errs = await fresh(b, init="localStorage.setItem('inputPref','mouse');")
        await page.evaluate("document.querySelector('#littlePick [data-mode=shapes]').click()"); await page.wait_for_function("mode === 'mouse' && gameMode === 'shapes' && shapes.mat", timeout=8000)
        await page.evaluate("__grasp.shapes.placeTest && (() => { for (let i = 0; i < 12; i++) try { __grasp.shapes.placeTest(0); } catch (e) {} })()"); await page.wait_for_timeout(400)
        await page.evaluate("shapesHome()"); await page.wait_for_function("shapes.over && shapes.ui.buttons", timeout=5000); await page.wait_for_timeout(1500)
        c = await page.evaluate(CARD + "(shapes)")
        check('the toddler card (Shapes): big stars, confetti, Play again (big) + Home only; no score, coins or Share', c['keys'] == ['again', 'home'] and c['coin'] is None and await page.evaluate("shapes.ui.starsRow >= 1 && shapes.ui.toddlerFx > 0 && shapes.ui.buttons.again.h >= 60"), c)
        await page.screenshot(path=OUT + 'home2_after_card_toddler.png')
        await card_tap(page, "shapes", 'again')
        await page.wait_for_function("!shapes.over && mode === 'mouse'", timeout=5000)
        check('the toddler card\'s Play again: a new round', await page.evaluate("shapes.level === 1"))
        await page.evaluate("goHome()"); await page.wait_for_timeout(200)
        await page.evaluate("localStorage.setItem('cgTouchOk', '1'); __grasp.cg.touchOk = true; __grasp.cg.start('bubbles', 'mouse')"); await page.wait_for_function("gameMode === 'bubbles' && mode === 'mouse' && !__grasp.cg.asking", timeout=8000)  # (no camera prompt: asked once per device)
        await page.evaluate("__grasp.cg.calm(false); __grasp.cg.end()"); await page.wait_for_function("__grasp.cg.bubbles.over && __grasp.cg.bubbles.ui.buttons", timeout=5000)
        c = await page.evaluate(CARD + "(__grasp.cg.bubbles)")
        check('a camera game\'s card (Bubble Pop): stars + Play again / Home, no Share', c['keys'] == ['again', 'home'], c)
        check('toddler card: no page errors', not errs, errs); await ctx.close()

        # ===== 10. gentler: the gift pauses on a missed day; no streak nags; no upsell outside the Shop; red dots only for new rewards, cleared once seen =====
        ctx, page, errs = await fresh(b, init=prof(coins=5000, habit={'gift': {'day': 3, 'date': '2026-09-27'}, 'play': ['2026-09-29', '2026-09-30', '2026-10-01']}))
        st = await page.evaluate(G + ".state")
        check('the gift calendar after days away: paused at day 4 (the next box), not back to day 1', st['day'] == 4 and st['missed'] and not st['opened'], st)
        gentle = await page.evaluate("""(() => { const txt = $('start').innerText, nags = ['keepFlame', 'flameZero', 'flameToast'].map(k => t(k, { n: 3 })); return { nag: nags.some(n => txt.includes(n)) || __grasp.toasts.some(x => nags.includes(x.text)), flame: !!document.getElementById('flameBtn'), shopDot: !$('collectionBtn').querySelector('.dot').hidden, nx: getComputedStyle($('nextUnlock')).display, upsell: /coins to|מטבעות ל/.test(txt) }; })()""")
        check('no streak nag on the start screen or in toasts; no flame chip', not gentle['nag'] and not gentle['flame'], gentle)
        check('5000 coins: no "you can afford" dot on the Shop tab, no "N more coins" anywhere on the start screen', not gentle['shopDot'] and gentle['nx'] == 'none' and not gentle['upsell'], gentle)
        await page.evaluate("openAdvMap({ how: 'mouse' })"); await page.wait_for_timeout(300)
        check('no coin goal on the Adventure map', await page.evaluate("$('advGoal').hidden"))
        await page.evaluate("closeAdvMap()"); await page.wait_for_timeout(200)
        d0 = await page.evaluate(H + ".todayDot()")
        check('the Events tab: a red dot for the new gift', d0 >= 1 and await page.evaluate("!$('todayBtn').querySelector('.dot').hidden"))
        await page.tap('#todayBtn'); await page.wait_for_timeout(450)
        tdy = await page.evaluate("({ dot: !$('todayBtn').querySelector('.dot').hidden, streak: $('todayStreak').hidden ? null : $('todayStreak').textContent.replace(/[^0-9]/g, ''), gift: $('todayGiftLine').textContent, ms: document.querySelectorAll('#today #mlist .mrow').length, ev: !!$('eventBtn').closest('#today') })")
        check('the Today panel: the weekly event, the gift (day 4 waiting), the missions, the streak (3, quietly); seen: the dot cleared', not tdy['dot'] and tdy['streak'] == '3' and tdy['gift'] == 'Day 4 gift is waiting' and tdy['ms'] == 3 and tdy['ev'], tdy)
        await page.screenshot(path=OUT + 'home2_after_today.png')
        await page.evaluate("__grasp.home2.tab('play')"); await page.wait_for_timeout(150)
        check('...and it stays cleared (seen) after closing', await page.evaluate("$('todayBtn').querySelector('.dot').hidden"))
        await page.evaluate("profile.missions.list[0].progress = profile.missions.list[0].goal; profile.missions.list[0].done = true; saveProfile(); syncMeta()")
        check('a mission done since: the dot again (something new to claim)', await page.evaluate("!$('todayBtn').querySelector('.dot').hidden"))
        check('gentle: no page errors', not errs, errs); await ctx.close()

        # ===== 11. the camera: the hand's dwell works on the new start screen (the camera chosen) =====
        ctx, page, errs = await fresh(b, mobile=False, camera=True, init="localStorage.setItem('inputPref','camera');")
        await page.click('#start button[data-mode=strike]'); await page.wait_for_function("!$('advMap').hidden", timeout=5000)
        await page.wait_for_function("__grasp.panelfix.homeCam.on", timeout=15000)
        await page.evaluate("$('advBack').click()"); await page.wait_for_timeout(300)
        r = await page.evaluate("(() => { const q = $('littleBtn').getBoundingClientRect(); return [q.left + q.width / 2, q.top + q.height / 2]; })()")
        await page.evaluate(f"window.__handFor = () => handAt({r[0]}, {r[1]}, 0.8)")
        await page.wait_for_function(in_room('little'), timeout=8000)
        check('camera on: holding the hand over Little ones opens it (the start screen dwell)', 'littleBtn' in await page.evaluate("__grasp.panelfix.homeCam.clicks"))
        await page.evaluate("__grasp.home2.pick('littlePick', false)"); await page.wait_for_timeout(200)
        r = await page.evaluate("(() => { const q = $('heroPlay').getBoundingClientRect(); return [q.left + q.width / 2, q.top + q.height / 2]; })()")
        await page.evaluate(f"window.__handFor = () => handAt({r[0]}, {r[1]}, 0.8)")
        await page.wait_for_function(f"{A}.on && mode === 'camera'", timeout=10000)
        check('...and over the hero it starts the stage with the camera', True)
        check('camera dwell: no page errors', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
