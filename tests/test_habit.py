exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# The daily habit: the 7-day gift calendar (day progression across mocked dates, the restart after a missed day, the cycle after day 7, each prize
# credited once, the look prizes and their coin fallbacks, the once-a-day pop-up for a real visitor, never under automation unless asked), the
# play-streak flame (counting, the pulse when it grows today, the 'play today' hint), the '3 stages today' chest on the Adventure map, the star chests
# beside its path (thresholds, one claim each, the 100-star look), the 'Tomorrow: day N gift' line on the stage card and the round-over card,
# the profile's validation, EN / HE, phone / desktop. Hooks: __grasp.gifts, __grasp.habit (+ __grasp.setDate). Timing-independent: state is polled.
G = "__grasp.gifts"; HB = "__grasp.habit"; A = "__grasp.adventure"; S = "__grasp.strike"; P = "__grasp.profile"
TOASTS = "__grasp.toasts.map(t => t.text)"
CHEAP = {'ball_beach', 'hand_mint', 'hand_sky', 'hand_lilac'}  # the looks at <= 150 coins
ALL_COIN_ITEMS = "__grasp.collection.items.filter(it => !it.level && it.cost > 0).map(it => it.id)"
START = """(() => { const st = $('start'), r = (e) => { const q = e.getBoundingClientRect(); return { l: q.left, r: q.right, t: q.top, b: q.bottom, w: q.width, h: q.height }; }, f = $('flameBtn'), g = $('giftBtn'), h = $('flameHint');
  return { flame: r(f), gift: r(g), h1: r(document.querySelector('#start .panel h1')), lang: r($('startLang')), pill: r($('metaPill')), hint: h.hidden ? null : r(h), hintText: h.hidden ? '' : h.textContent.trim(),
    n: f.querySelector('b').textContent, zero: f.classList.contains('zero'), today: f.classList.contains('today'), grow: f.classList.contains('grow'), giftDot: !g.querySelector('.dot').hidden, giftReady: g.classList.contains('ready'),
    W: innerWidth, noX: document.documentElement.scrollWidth <= innerWidth + 1 && st.scrollWidth <= st.clientWidth + 1, fits: st.scrollHeight <= st.clientHeight + 1, dir: document.documentElement.dir }; })()"""
BOXES = """(() => { const ov = $('gifts'), sh = ov.querySelector('.sheet').getBoundingClientRect(), bs = [...ov.querySelectorAll('.gbox')].map(b => { const q = b.getBoundingClientRect(); return { day: +b.dataset.day, st: b.dataset.st, opened: b.classList.contains('opened'), x: q.left + q.width / 2, y: q.top, w: q.width, h: q.height, pz: b.querySelector('.pz').textContent.trim(), dn: b.querySelector('.dn').textContent, ck: !!b.querySelector('.ck') }; });
  const ok = $('giftOk').getBoundingClientRect();
  return { shown: !ov.hidden, boxes: bs, inside: sh.left >= 0 && sh.right <= innerWidth + 0.5 && sh.top >= 0 && sh.bottom <= innerHeight + 0.5, noX: document.documentElement.scrollWidth <= innerWidth + 1, sub: $('giftSub').textContent, missed: $('giftSub').classList.contains('missed'),
    ok: $('giftOk').textContent, okH: ok.height, title: $('giftTitle').textContent, bub: ov.querySelector('.nuGrip .bub').textContent }; })()"""

def rects_overlap(a, b, pad=0):
    return a['l'] < b['r'] - pad and b['l'] < a['r'] - pad and a['t'] < b['b'] - pad and b['t'] < a['b'] - pad

async def fresh(b, mobile=False, he=False, init='', date='2026-10-02', auto=False):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + "localStorage.setItem('lang','" + ('he' if he else 'en') + "');" + ("sessionStorage.setItem('grasp.testDate','" + date + "');" if date else '') + ("window.__graspGiftAuto = true;" if auto else '') + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(700)
    return ctx, page, errs

def prof(**kw):  # a stored profile (merged over the defaults by the game)
    d = dict(v=1, coins=0, xp=0); d.update(kw)
    return "if (!sessionStorage.getItem('__seeded')) { localStorage.setItem('grasp.profile', " + json.dumps(json.dumps(d)) + "); sessionStorage.setItem('__seeded', '1'); }"

async def tap(page, mobile, sel):
    if mobile: await page.tap(sel)
    else: await page.click(sel)

async def stage_clear(page, n, lost=0):  # play stage n (from the start screen or a card) and clear it at once; wait for its card
    await page.evaluate(f"{A}.start({n}, 'mouse')")
    await page.wait_for_function(f"{A}.on && {A}.stage === {n} && {A}.phase === 'play' && !{S}.over", timeout=8000)
    await page.evaluate(f"{A}.finishTest({lost})")
    await page.wait_for_function(f"{S}.over && {A}.phase === 'card' && {S}.ui.buttons && {S}.ui.buttons.next", timeout=10000)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ---- the calendar across mocked dates: days 1..7, each prize once, the cycle, a missed day, a clock that went back ----
        ctx, page, errs = await fresh(b)
        check('under automation the calendar never pops up by itself (the other suites see the plain start screen)', not await page.evaluate(G + ".shown") and not await page.evaluate(G + ".auto") and await page.evaluate(G + ".shownCount") == 0)
        st = await page.evaluate(G + ".state")
        check('a new player: today is day 1, not opened, nothing missed', st['day'] == 1 and not st['opened'] and not st['missed'] and st['tomorrow'] == 2, st)
        check('ECONOMY.gifts: 5, 8, 10, a look, 15, 20, the chest (40 coins + a look)', await page.evaluate(G + ".economy.days") == [5, 8, 10, 'skin', 15, 20, 'chest'] and await page.evaluate(G + ".economy.chest") == 40)
        got = []
        for i in range(7):
            d = '2026-10-%02d' % (2 + i)
            await page.evaluate(f"__grasp.setDate('{d}')")
            pre = await page.evaluate(G + ".state"); c0 = await page.evaluate(P + ".coins"); u0 = await page.evaluate(P + ".unlocked.length")
            r = await page.evaluate(G + ".claim()")
            again = await page.evaluate(G + ".claim()")
            got.append({'day': pre['day'], 'r': r, 'dc': await page.evaluate(P + ".coins") - c0, 'du': await page.evaluate(P + ".unlocked.length") - u0, 'again': again, 'state': await page.evaluate(G + ".state")})
        check('consecutive days: the boxes go 1, 2, ... 7', [g['day'] for g in got] == [1, 2, 3, 4, 5, 6, 7], [g['day'] for g in got])
        check('coin days credit exactly their coins (5, 8, 10, 15, 20)', [got[i]['dc'] for i in (0, 1, 2, 4, 5)] == [5, 8, 10, 15, 20], [g['dc'] for g in got])
        check('day 4: a cheap look not owned yet (no coins), now in the collection', got[3]['r']['item'] in CHEAP and got[3]['dc'] == 0 and got[3]['du'] == 1, got[3])
        check('day 7: the big chest: 40 coins + a look not owned yet (<= 420)', got[6]['r']['chest'] and got[6]['dc'] == 40 and got[6]['du'] == 1 and got[6]['r']['item'] in await page.evaluate(ALL_COIN_ITEMS) and got[6]['r']['item'] != got[3]['r']['item'], got[6])
        check('a second open the same day: nothing (null), nothing credited', all(g['again'] is None for g in got) and all(g['state']['opened'] for g in got))
        check('after an open: tomorrow is the next box (2..7, then 1)', [g['state']['tomorrow'] for g in got] == [2, 3, 4, 5, 6, 7, 1], [g['state']['tomorrow'] for g in got])
        await page.evaluate("__grasp.setDate('2026-10-09')")
        st = await page.evaluate(G + ".state")
        check('after day 7 the calendar cycles: day 1 again (not "missed")', st['day'] == 1 and not st['opened'] and not st['missed'], st)
        c0 = await page.evaluate(P + ".coins"); await page.evaluate(G + ".claim()")
        check('...and its day 1 pays 5', await page.evaluate(P + ".coins") - c0 == 5)
        await page.evaluate("__grasp.setDate('2026-10-10')"); await page.evaluate(G + ".claim()")  # day 2
        await page.evaluate("__grasp.setDate('2026-10-12')")  # 10-11 skipped
        st = await page.evaluate(G + ".state")
        check('a missed day: the calendar restarts at day 1 (missed flag for the gentle line)', st['day'] == 1 and st['missed'] and not st['opened'], st)
        await page.evaluate("__grasp.setDate('2026-10-05')")
        st = await page.evaluate(G + ".state"); c0 = await page.evaluate(P + ".coins")
        check('a clock that went back: no second gift', st['opened'] and await page.evaluate(G + ".claim()") is None and await page.evaluate(P + ".coins") == c0, st)
        await page.reload(); await page.wait_for_timeout(500); await page.evaluate("__grasp.setDate('2026-10-12')")  # (the init script sets the test date again on a reload)
        check('the calendar survives a reload (stored in the profile)', await page.evaluate(P + ".habit.gift") == {'day': 2, 'date': '2026-10-10'} and (await page.evaluate(G + ".state"))['missed'], await page.evaluate(P + ".habit.gift"))
        check('no page errors (calendar)', not errs, errs); await ctx.close()

        # ---- look prizes when every look is owned: coins instead ----
        ctx, page, errs = await fresh(b)
        await page.evaluate(f"(() => {{ for (const id of {ALL_COIN_ITEMS}) if (!{P}.unlocked.includes(id)) {P}.unlocked.push(id); }})()")
        pz = await page.evaluate(f"[{G}.prize(4), {G}.prize(7), {G}.prize(1)]")
        check('nothing left to win: day 4 pays 12 coins, day 7 pays 40 + 30', pz[0] == {'coins': 12, 'item': None} and pz[1]['coins'] == 70 and pz[1]['item'] is None and pz[2] == {'coins': 5, 'item': None}, pz)
        check('no page errors (fallbacks)', not errs, errs); await ctx.close()

        # ---- the once-a-day pop-up for a real visitor; tap to open (phone + desktop, EN / HE): burst, coins fly, the line for tomorrow ----
        for mobile in (True, False):
            for he in (False, True):
                tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en'); lt = 'he' if he else 'en'
                ctx, page, errs = await fresh(b, mobile, he, auto=True)
                await page.wait_for_function(G + ".shown", timeout=4000)
                await page.wait_for_timeout(600)  # the pop-in done
                bx = await page.evaluate(BOXES)
                check(tag + ': the first open of the day: the calendar pops up (7 boxes, day 1 today, the rest to come), inside the screen, no sideways scroll',
                      bx['shown'] and [x['day'] for x in bx['boxes']] == list(range(1, 8)) and [x['st'] for x in bx['boxes']] == ['today'] + ['future'] * 6 and bx['inside'] and bx['noX'], bx)
                check(tag + ': big kid-sized boxes (>= 60 x 80), day 7 the widest; a big Open button', all(x['w'] >= 60 and x['h'] >= 80 for x in bx['boxes']) and bx['boxes'][6]['w'] > bx['boxes'][0]['w'] * 1.6 and bx['okH'] >= 48, [(x['w'], x['h']) for x in bx['boxes']])
                exp = {'title': 'מתנה יומית' if he else 'Daily gift', 'ok': 'לפתוח!' if he else 'Open it!', 'd1': 'יום 1' if he else 'Day 1'}
                check(tag + ': texts (title, Open, Day 1, the coin prizes, the look, the chest)', bx['title'] == exp['title'] and bx['ok'] == exp['ok'] and bx['boxes'][0]['dn'] == exp['d1'] and bx['boxes'][0]['pz'].endswith('+5') and bx['boxes'][5]['pz'].endswith('+20')
                      and bx['boxes'][3]['pz'] == ('מראה חדש' if he else 'New look') and bx['boxes'][6]['pz'] == ('תיבה גדולה' if he else 'Big chest'), bx['boxes'])
                d1, d2 = bx['boxes'][0], bx['boxes'][1]
                check(tag + ': boxes run ' + ('right to left' if he else 'left to right'), (d1['x'] > d2['x']) if he else (d1['x'] < d2['x']), [d1['x'], d2['x']])
                check(tag + ': the start screen behind: the gift chip has its dot; once-a-day mark stored', (await page.evaluate(START))['giftDot'] and await page.evaluate(P + ".habit.seen") == '2026-10-02')
                if mobile: await page.screenshot(path='tests/out/habit_gift_phone_' + lt + '.png')
                elif not he: await page.screenshot(path='tests/out/habit_gift_desktop_en.png')
                c0 = await page.evaluate(P + ".coins")
                if he: await tap(page, mobile, '#giftSub')  # a tap anywhere on the calendar opens today's box
                else: await tap(page, mobile, '.gbox.today')
                await page.wait_for_function("document.querySelector('.gbox.today.opened')", timeout=3000)
                await page.wait_for_timeout(250)
                bx = await page.evaluate(BOXES)
                check(tag + ': ' + ('a tap on the sheet' if he else 'a tap on the glowing box') + ' opens it: +5 coins once, a toast, the box opened with a check, "tomorrow: day 2"',
                      await page.evaluate(P + ".coins") == c0 + 5 and bx['boxes'][0]['opened'] and bx['boxes'][0]['ck'] and '2' in bx['sub'] and bx['ok'] == ('יש!' if he else 'Yay!') and any(('מתנה יומית' if he else 'Daily gift') in x for x in await page.evaluate(TOASTS)), bx)
                await page.wait_for_function("document.querySelectorAll('.gfly').length > 0", timeout=3000)
                check(tag + ': coins fly to the pill', True)
                if mobile:
                    await page.wait_for_timeout(500); await page.screenshot(path='tests/out/habit_gift_open_phone_' + lt + '.png')
                await tap(page, mobile, '#giftSub'); await page.wait_for_timeout(100)
                check(tag + ': another tap does not pay again', await page.evaluate(P + ".coins") == c0 + 5)
                await tap(page, mobile, '#giftOk'); await page.wait_for_function("!" + G + ".shown", timeout=3000)
                s = await page.evaluate(START)
                check(tag + ': Yay closes it; the gift chip: no dot, no bounce', not s['giftDot'] and not s['giftReady'], s)
                await page.reload(); await page.wait_for_timeout(1200)
                check(tag + ': a reload the same day: no pop-up', not await page.evaluate(G + ".shown"))
                if not mobile and not he:
                    await page.evaluate("__grasp.setDate('2026-10-03'); goHome()")
                    await page.wait_for_function(G + ".shown", timeout=3000)
                    check(tag + ': the next day (back on the start screen): it pops up again, day 2 today, day 1 done', [x['st'] for x in (await page.evaluate(BOXES))['boxes']][:3] == ['past', 'today', 'future'])
                    await page.keyboard.press('Escape'); await page.wait_for_timeout(100)
                    check(tag + ': Escape closes it unopened; the chip keeps its dot; no second pop-up today', not await page.evaluate(G + ".shown") and (await page.evaluate(START))['giftDot'] and not await page.evaluate(G + ".maybe()"))
                    await page.click('#giftBtn'); await page.wait_for_function(G + ".shown", timeout=3000)
                    check(tag + ': the gift chip opens it any time', (await page.evaluate(G + ".state"))['day'] == 2)
                    await page.click('#giftOk'); await page.wait_for_function("document.querySelector('.gbox.today.opened')", timeout=3000)
                    check(tag + ': ...and day 2 pays 8', await page.evaluate(P + ".coins") == c0 + 13)
                    await page.click('#gifts', position={'x': 5, 'y': 5}); await page.wait_for_timeout(100)
                    check(tag + ': a tap on the backdrop closes it', not await page.evaluate(G + ".shown"))
                    await page.evaluate("__grasp.setDate('2026-10-06'); goHome()")
                    await page.wait_for_function(G + ".shown", timeout=3000)
                    bx = await page.evaluate(BOXES)
                    check(tag + ': back after missed days: day 1 again with the gentle line', bx['missed'] and bx['boxes'][0]['st'] == 'today' and 'new week' in bx['sub'].lower(), bx['sub'])
                    await page.keyboard.press('Escape')
                check(tag + ': no page errors (pop-up)', not errs, errs); await ctx.close()

        # the pop-up waits for a NEW UNLOCKED card, and never shows over a game
        ctx, page, errs = await fresh(b, auto=True, init=prof(road={'got': ['brick', 'cow', 'glass'], 'fresh': [], 'cards': ['glass']}, xp=200))
        await page.wait_for_timeout(500)
        check('a NEW UNLOCKED card waiting: it shows first, the calendar waits', await page.evaluate("__grasp.road.card") == 'glass' and not await page.evaluate(G + ".shown"))
        await page.evaluate("__grasp.road.closeCard()"); await page.wait_for_function(G + ".shown", timeout=3000)
        check('...and the calendar comes once the card is closed', await page.evaluate(G + ".shown"))
        await page.keyboard.press('Escape')
        await page.evaluate(START_MOUSE.replace("if (!$('advMap').hidden) $('advEndless').click();", '')); await page.wait_for_timeout(300)
        await page.evaluate("__grasp.setDate('2026-10-03')")
        check('in a game: no pop-up (maybe() refuses)', await page.evaluate("mode") != 'none' and not await page.evaluate(G + ".maybe()") and not await page.evaluate(G + ".shown"))
        check('no page errors (order)', not errs, errs); await ctx.close()

        # ---- the play-streak flame: counting, the pulse when it grows today, the 'play today' hint (phone + desktop, EN / HE) ----
        for mobile in (True, False):
            for he in (False, True):
                tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en'); lt = 'he' if he else 'en'
                ctx, page, errs = await fresh(b, mobile, he, prof(habit={'play': ['2026-09-29', '2026-09-30', '2026-10-01']}))
                await page.wait_for_timeout(1300)
                s = await page.evaluate(START)
                check(tag + ': 3 days in a row up to yesterday: the flame shows 3 (not lit for today); the hint "play today to keep your 3-day streak"',
                      s['n'] == '3' and not s['zero'] and not s['today'] and s['hint'] and '3' in s['hintText'] and s['hintText'] == await page.evaluate("t('keepFlame', { n: 3 })"), s)
                check(tag + ': the flame and the gift chip sit in the top bar: inside the screen, clear of the wordmark, the language button and the pill; 40+ px targets; no sideways scroll; the start screen still fits',
                      all(r['l'] >= 0 and r['r'] <= s['W'] and r['h'] >= 40 for r in (s['flame'], s['gift'])) and not any(rects_overlap(a, x, 3) for a in (s['flame'], s['gift']) for x in (s['h1'], s['lang'], s['pill'])) and not rects_overlap(s['flame'], s['gift'])
                      and s['noX'] and s['fits'], s)
                if mobile: await page.screenshot(path='tests/out/habit_start_hint_phone_' + lt + '.png')
                await stage_clear(page, 1)
                check(tag + ': a finished round (an Adventure stage) counts today', await page.evaluate(HB + ".playedToday") and await page.evaluate(HB + ".streak") == 4)
                await page.evaluate("goHome()"); await page.wait_for_timeout(150)
                s = await page.evaluate(START)
                check(tag + ': home: the flame grows to 4 with a pulse, lit; the hint gone', s['n'] == '4' and s['today'] and s['grow'] and not s['hint'] and await page.evaluate(HB + ".pulses") == 1, s)
                if mobile:
                    await page.wait_for_timeout(1100); await page.screenshot(path='tests/out/habit_start_streak_phone_' + lt + '.png')
                await page.evaluate("goHome()"); await page.wait_for_timeout(50)
                check(tag + ': home again: no second pulse today', await page.evaluate(HB + ".pulses") == 1)
                if not mobile and not he:
                    await page.reload(); await page.wait_for_timeout(500)
                    check('a reload: still 4, no pulse again', await page.evaluate(HB + ".pulses") == 0 and (await page.evaluate(START))['n'] == '4')
                    await page.evaluate("__grasp.setDate('2026-10-03')")
                    s = await page.evaluate(START)
                    check('the next day: 4 still alive, the hint back', s['n'] == '4' and s['hint'] and not s['today'], s)
                    await page.evaluate("__grasp.setDate('2026-10-04')")
                    s = await page.evaluate(START)
                    check('a day skipped: the flame goes out (0, dim, no hint)', s['n'] == '0' and s['zero'] and not s['hint'], s)
                    await page.click('#flameBtn'); await page.wait_for_timeout(100)
                    check('the flame tapped: a toast that tells what it is', any('flame' in x.lower() for x in await page.evaluate(TOASTS)))
                    check('the daily challenge streak is its own (untouched)', await page.evaluate("__grasp.daily.streak") == 0)
                check(tag + ': no page errors (flame)', not errs, errs); await ctx.close()

        # ---- the '3 stages today' chest on the map; the 'Tomorrow' line on the stage card and the round-over card ----
        for mobile, he in ((True, False), (True, True), (False, False)):
            tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en'); lt = 'he' if he else 'en'
            ctx, page, errs = await fresh(b, mobile, he, prof(adv={'stars': {}, 'unlocked': 5}, xp=6850))
            await page.evaluate(f"{A}.openMap()"); await page.wait_for_timeout(200)
            dc = await page.evaluate("(() => { const b = $('advDayChest'), r = b.getBoundingClientRect(), h = $('advTitle').getBoundingClientRect(), st = $('advStarTotal').getBoundingClientRect(), bk = $('advBack').getBoundingClientRect(); return { st: b.dataset.state, pr: b.querySelector('.pr').textContent, w: r.width, h: r.height, in: r.left >= 0 && r.right <= innerWidth, clear: r.right <= Math.max(st.left, h.left) + 1 || r.left >= Math.min(st.right, h.right) - 1, starsIn: st.right <= innerWidth + 0.5 && st.left >= 0 && bk.left >= 0, noX: document.documentElement.scrollWidth <= innerWidth + 1 }; })()")
            check(tag + ': the map header: the stage chest 0/3 (filling), 44+ px, inside, the header still fits', dc['st'] == 'filling' and dc['pr'] == '0/3' and dc['w'] >= 44 and dc['h'] >= 44 and dc['in'] and dc['starsIn'] and dc['noX'], dc)
            c0 = await page.evaluate(P + ".coins")
            await tap(page, mobile, '#advDayChest'); await page.wait_for_timeout(100)
            check(tag + ': tapped before 3: a toast saying how many more, no coins', await page.evaluate(P + ".coins") == c0 and (lambda _e, _ts: any(x == _e for x in _ts))(await page.evaluate("t('dayChestNeed', { n: 3 })"), await page.evaluate(TOASTS)))
            await stage_clear(page, 1)
            card = await page.evaluate(S + ".ui.tomorrow")
            check(tag + ': stage card, today\'s gift not opened: no "Tomorrow" line', card is None)
            await page.evaluate(G + ".claim()")
            await page.wait_for_timeout(100)
            tm = await page.evaluate(f"({{ t: {S}.ui.tomorrow, card: {S}.ui.card, W: innerWidth, H: innerHeight }})")
            check(tag + ': gift opened: the clear card shows "Tomorrow: day 2 gift" under the card, inside the screen', tm['t'] and tm['t']['day'] == 2 and tm['t']['text'] == await page.evaluate("t('tomorrowGift', { n: 2 })") and tm['t']['y'] > tm['card']['y'] + tm['card']['h'] and tm['t']['x'] >= 0 and tm['t']['x'] + tm['t']['w'] <= tm['W'] and tm['t']['y'] + tm['t']['h'] <= tm['H'], tm)
            if mobile:
                await page.wait_for_timeout(1200); await page.screenshot(path='tests/out/habit_advcard_tomorrow_' + lt + '.png')
            await stage_clear(page, 2)  # replays and new stages both count
            await stage_clear(page, 1)
            check(tag + ': 3 stages cleared today (a replay counts)', await page.evaluate(HB + ".stages") == {'n': 3, 'claimed': False, 'goal': 3})
            await page.evaluate(f"{A}.openMap()"); await page.wait_for_timeout(250)
            check(tag + ': the chest is ready (3/3, shaking)', await page.evaluate("[$('advDayChest').dataset.state, $('advDayChest').querySelector('.pr').textContent, getComputedStyle($('advDayChest')).animationName]") == ['ready', '3/3', 'cshake'])
            if mobile: await page.screenshot(path='tests/out/habit_map_daychest_' + lt + '.png')
            c0 = await page.evaluate(P + ".coins")
            await tap(page, mobile, '#advDayChest'); await page.wait_for_timeout(150)
            check(tag + ': tapped at 3: +10 coins, opened (done)', await page.evaluate(P + ".coins") == c0 + 10 and await page.evaluate("$('advDayChest').dataset.state") == 'done' and await page.evaluate(HB + ".stages.claimed"))
            await tap(page, mobile, '#advDayChest'); await page.wait_for_timeout(100)
            check(tag + ': tapped again: nothing more', await page.evaluate(P + ".coins") == c0 + 10 and await page.evaluate(HB + ".claimStages()") == 0)
            if not mobile:
                await page.evaluate("__grasp.setDate('2026-10-03')")
                check('the next day: the stage chest starts again at 0', await page.evaluate(HB + ".stages") == {'n': 0, 'claimed': False, 'goal': 3})
                await page.evaluate("__grasp.setDate('2026-10-02')")
                # the fail card
                await page.evaluate(f"{A}.start(3, 'mouse')"); await page.wait_for_function(f"{A}.on && {A}.stage === 3 && {A}.phase === 'play'", timeout=8000)
                await page.evaluate(f"{A}.failTest()"); await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.retry && {S}.ui.tomorrow", timeout=8000)
                check('the fail card shows the Tomorrow line too (and a fail does not count for the chest)', (await page.evaluate(S + ".ui.tomorrow"))['day'] == 2 and await page.evaluate(HB + ".stages.n") == 3)
            # the shared round-over card (Endless Strike)
            await page.evaluate("goHome()"); await page.wait_for_timeout(100)
            await page.evaluate(f"{A}.endless('mouse')"); await page.wait_for_function(f"mode === 'mouse' && !{A}.on && !{S}.over", timeout=8000)
            await page.evaluate(f"(() => {{ const s = {S}; s.lives = 1; s.setBallZ(-500); }})()")
            await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.again && {S}.ui.tomorrow && performance.now() - {S}.overAt > 1100", timeout=10000)
            tm = await page.evaluate(f"({{ t: {S}.ui.tomorrow, card: {S}.ui.card, W: innerWidth, H: innerHeight }})")
            check(tag + ': the round-over card: "Tomorrow: day 2 gift" under the card, inside the screen', tm['t']['day'] == 2 and tm['t']['y'] > tm['card']['y'] + tm['card']['h'] and tm['t']['x'] >= 0 and tm['t']['x'] + tm['t']['w'] <= tm['W'] and tm['t']['y'] + tm['t']['h'] <= tm['H'], tm)
            if mobile: await page.screenshot(path='tests/out/habit_endcard_tomorrow_' + lt + '.png')
            check(tag + ': no page errors (stage chest / tomorrow)', not errs, errs); await ctx.close()

        # Slice's round-over card has the line too (and none before the gift is opened)
        ctx, page, errs = await fresh(b)
        await page.evaluate("__grasp.setGameMode('slice')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse'", timeout=5000)
        await page.evaluate("sliceLoseLife(performance.now()); sliceLoseLife(performance.now()); sliceLoseLife(performance.now())")
        await page.wait_for_function("__grasp.slice.over && __grasp.slice.ui.buttons", timeout=5000)
        check('Slice: no Tomorrow line before the gift is opened', await page.evaluate("__grasp.slice.ui.tomorrow") is None)
        await page.evaluate(G + ".claim()")
        await page.wait_for_function("__grasp.slice.ui.tomorrow", timeout=3000)
        check('Slice: the round-over card shows "Tomorrow: day 2 gift" once it is', (await page.evaluate("__grasp.slice.ui.tomorrow"))['day'] == 2)
        check('no page errors (slice card)', not errs, errs); await ctx.close()

        # ---- the star chests beside the map's path ----
        stars26 = {str(n): 3 for n in range(1, 9)}; stars26['9'] = 2
        for mobile, he in ((True, False), (True, True), (False, False)):
            tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en'); lt = 'he' if he else 'en'
            ctx, page, errs = await fresh(b, mobile, he, prof(adv={'stars': stars26, 'unlocked': 10}))
            await page.evaluate(f"{A}.openMap()"); await page.wait_for_timeout(250)
            lst = await page.evaluate(HB + ".starChests")
            check(tag + ': 5 star chests at 10 / 25 / 45 / 70 / 100 stars paying 15 / 25 / 35 / 50 / 80; with 26 stars the first two reached', [c['stars'] for c in lst] == [10, 25, 45, 70, 100] and [c['coins'] for c in lst] == [15, 25, 35, 50, 80] and [c['reached'] for c in lst] == [True, True, False, False, False] and not any(c['claimed'] for c in lst), lst)
            ch = await page.evaluate("""(() => { const nodes = [...document.querySelectorAll('.anode .disc')].map(d => { const q = d.getBoundingClientRect(); return { l: q.left, r: q.right, t: q.top, b: q.bottom }; }), sc = $('advScroll');
              return { nodes, sw: sc.scrollWidth <= sc.clientWidth + 1, chests: [...document.querySelectorAll('.achest')].map(b => { const q = b.querySelector('.cbox').getBoundingClientRect(), l = b.querySelector('.lb').getBoundingClientRect(); return { i: +b.dataset.i, st: b.dataset.state, next: b.classList.contains('next'), lb: b.querySelector('.lb').textContent.trim(), box: { l: q.left, r: q.right, t: q.top, b: q.bottom }, lab: { l: l.left, r: l.right, t: l.top, b: l.bottom }, w: q.width, h: q.height }; }) }; })()""")
            cs = ch['chests']
            check(tag + ': on the map: 2 ready (Claim), the next one shows its progress "26 / 45", the rest locked', [c['st'] for c in cs] == ['reached', 'reached', 'locked', 'locked', 'locked'] and cs[2]['next'] and cs[2]['lb'] == '26 / 45' and cs[3]['lb'] == '70' and cs[0]['lb'] == await page.evaluate("t('claim')"), [(c['st'], c['lb']) for c in cs])
            check(tag + ': beside the path: no chest on a stop, all inside the map width, big targets', all(not rects_overlap(c[k], n, 2) for c in cs for k in ('box', 'lab') for n in ch['nodes']) and ch['sw'] and all(c['box']['l'] >= 0 and c['box']['r'] <= (360 if mobile else 1280) and c['w'] >= 50 and c['h'] >= 44 for c in cs), cs)
            await page.evaluate("document.querySelector('.achest[data-i=\"1\"]').scrollIntoView({ block: 'center' })"); await page.wait_for_timeout(200)
            if mobile: await page.screenshot(path='tests/out/habit_map_chests_phone_' + lt + '.png')
            elif not he: await page.screenshot(path='tests/out/habit_map_chests_desktop_en.png')
            c0 = await page.evaluate(P + ".coins")
            await tap(page, mobile, '.achest[data-i="1"]'); await page.wait_for_timeout(200)
            check(tag + ': the 25-star chest tapped: +25 coins, opened', await page.evaluate(P + ".coins") == c0 + 25 and await page.evaluate("document.querySelector('.achest[data-i=\"1\"]').dataset.state") == 'claimed' and await page.evaluate(P + ".habit.starChests") == [25])
            await tap(page, mobile, '.achest[data-i="1"]'); await page.wait_for_timeout(100)
            check(tag + ': tapped again: nothing more ("already opened")', await page.evaluate(P + ".coins") == c0 + 25 and (lambda _e, _ts: any(x == _e for x in _ts))(await page.evaluate("t('starChestDone')"), await page.evaluate(TOASTS)))
            await page.evaluate("document.querySelector('.achest[data-i=\"2\"]').scrollIntoView({ block: 'center' })"); await page.wait_for_timeout(150)
            await tap(page, mobile, '.achest[data-i="2"]'); await page.wait_for_timeout(100)
            check(tag + ': a locked chest: "19 more stars", no coins', await page.evaluate(P + ".coins") == c0 + 25 and (lambda _e, _ts: any(x == _e for x in _ts))(await page.evaluate("t('starChestNeed', { n: 19 })"), await page.evaluate(TOASTS)))
            check(tag + ': hooks: a claimed / unreached chest gives nothing', await page.evaluate(HB + ".claimStar(1)") is None and await page.evaluate(HB + ".claimStar(2)") is None)
            if not mobile:
                await page.evaluate(f"(() => {{ for (let n = 1; n <= 40; n++) {P}.adv.stars[n] = 3; }})()")
                c1 = await page.evaluate(P + ".coins"); u1 = await page.evaluate(P + ".unlocked.length")
                r = await page.evaluate(HB + ".claimStar(4)")
                check('100 stars: +80 coins and a look not owned yet', r['coins'] == 80 and r['item'] in await page.evaluate(ALL_COIN_ITEMS) and await page.evaluate(P + ".coins") == c1 + 80 and await page.evaluate(P + ".unlocked.length") == u1 + 1, r)
                await page.evaluate(f"(() => {{ for (const id of {ALL_COIN_ITEMS}) if (!{P}.unlocked.includes(id)) {P}.unlocked.push(id); }})()")
                r = await page.evaluate(f"(() => {{ {P}.habit.starChests = {P}.habit.starChests.filter(s => s !== 100); return {HB}.claimStar(4); }})()")
                check('...with every look owned: 80 + 60 coins instead', r == {'coins': 140, 'item': None}, r)
                await page.reload(); await page.wait_for_timeout(400)
                check('claims survive a reload', await page.evaluate(P + ".habit.starChests") == [25, 100])
            check(tag + ': no page errors (star chests)', not errs, errs); await ctx.close()

        # ---- the profile: bad habit fields are dropped, good ones kept; an old profile gets the defaults ----
        bad = {'gift': {'day': 9, 'date': '2026-10-01'}, 'play': ['2026-10-01', 'bad', 5, '2026-09-30', '2026-10-01'], 'flame': {'date': 'zz', 'n': 2}, 'stages': {'date': '2026-10-02', 'n': '7', 'claimed': 'yes'}, 'starChests': [10, 11, 'a', 25, 10], 'seen': 5}
        ctx, page, errs = await fresh(b, init=prof(habit=bad))
        h = await page.evaluate(P + ".habit")
        check('validation: a bad gift day dropped, play dates filtered / unique / sorted, a bad flame dropped, stages n coerced (claimed only if true), unknown star chests dropped, a bad seen dropped',
              h['gift'] == {'day': 0, 'date': ''} and h['play'] == ['2026-09-30', '2026-10-01'] and h['flame'] == {'date': '', 'n': 0} and h['stages'] == {'date': '2026-10-02', 'n': 7, 'claimed': False} and h['starChests'] == [10, 25] and h['seen'] == '', h)
        await ctx.close()
        ctx, page, errs = await fresh(b, init=prof(habit='junk'))
        h = await page.evaluate(P + ".habit")
        check('a habit that is not an object: the defaults', h['gift'] == {'day': 0, 'date': ''} and h['play'] == [] and h['starChests'] == [] and await page.evaluate(G + ".state.day") == 1, h)
        await ctx.close()
        ctx, page, errs = await fresh(b, init=prof(habit={'gift': {'day': 7, 'date': '2026-10-01'}, 'stages': {'date': '2026-10-02', 'n': 2, 'claimed': False}}))
        check('good values kept: after a stored day 7 yesterday, today is day 1; 2 stages today', await page.evaluate(G + ".state.day") == 1 and not await page.evaluate(G + ".state.missed") and await page.evaluate(HB + ".stages.n") == 2)
        keys = ['giftTitle', 'giftDayN', 'giftSub', 'giftMissed', 'giftOpen', 'giftYay', 'giftTomorrow', 'giftTap', 'giftGot', 'giftToast', 'giftMystery', 'giftChest', 'giftOpened', 'tomorrowGift', 'flameN', 'flameZero', 'keepFlame', 'flameToast',
                'dayChest', 'dayChestToast', 'dayChestNeed', 'dayChestDone', 'starChest', 'starChestToast', 'starChestNeed', 'starChestDone']
        miss = await page.evaluate("(ks => ['en', 'he'].flatMap(l => ks.filter(k => !I18N[l][k] || (l === 'he' && I18N.he[k] === I18N.en[k])).map(k => l + ':' + k)))(" + json.dumps(keys) + ")")
        check('I18N: every habit string in EN and HE (HE translated)', not miss, miss)
        check('no page errors (profile)', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
