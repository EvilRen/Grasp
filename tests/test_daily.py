exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Daily challenge: a date-seeded Strike run (strikeRand), the modifier of the day, the record per date, the 7-day strip, the streak and its
# bonuses, sharing (clipboard fallback), the start-screen Daily button and its panel (EN / HE), the 'Play today's daily' mission.
# Timing-independent: runs are ended by parking the ball behind the player and polling for the round-over state.
D = "__grasp.daily"; S = "__grasp.strike"
TOASTS = "__grasp.toasts.map(t => t.text)"
# the first 12 wall kinds (level 6: every kind unlocked), each wall's brick layout, and the first perk offer of a fresh daily run
SEQ = """(() => { const g = __grasp, s = g.strike; g.startDaily(); s.setLevel(6); const kinds = s.walls.map(w => w.kind), lay = [];
  while (kinds.length < 12) kinds.push(s.spawnWall().kind);
  for (const w of s.walls) lay.push(w.kind + ':' + w.bricks.map(k => k.tnt ? 't' : k.hole ? 'h' : k.pu ? 'p' : '.').join(''));
  s.offerPerks(); const perks = s.perkOffer.slice(); s.pickPerk(0);
  return { kinds: kinds.slice(0, 12), lay, perks, mod: g.daily.modifier, date: g.daily.date, on: g.daily.on }; })()"""
BTN = """(() => { const b = $('dailyBtn'), r = b.getBoundingClientRect(), m = $('missionsBtn').getBoundingClientRect(), n = b.querySelector('.dNew');
  return { label: b.querySelector('.dTx b').textContent, date: b.querySelector('.dDate').textContent, mod: b.querySelector('.dMod').textContent, modId: b.dataset.mod, streak: b.querySelector('.dStreak b').textContent,
    zero: b.querySelector('.dStreak').classList.contains('zero'), newShown: !n.hidden && n.getBoundingClientRect().width > 0, newText: n.textContent, played: b.dataset.played,
    inside: r.left >= 0 && r.right <= innerWidth && r.bottom <= innerHeight, overlap: r.right > m.left && r.left < m.right, wider: r.width > m.width,
    fits: (() => { const st = $('start'); return st.scrollHeight <= st.clientHeight + 1 && document.documentElement.scrollHeight <= innerHeight + 1; })() }; })()"""

async def fresh(b, mobile=False, he=False, init='', date='2026-10-02'):
    opts = dict(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width':1280,'height':800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + "localStorage.setItem('lang','" + ('he' if he else 'en') + "');" + ("sessionStorage.setItem('grasp.testDate','" + date + "');" if date else '') + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(700)
    return ctx, page, errs
async def end_run(page, score, level=1):  # finish the running daily with this score at this level: the last life goes on a missed ball
    await page.evaluate(f"(() => {{ const s = {S}; if ({level} > 1) s.setLevel({level}); s.score = {score}; s.lives = 1; s.setBallZ(-500); }})()")
    await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.share && performance.now() - {S}.overAt > 450", timeout=8000)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])

        # ---- the seed: same date = the same run (even with Math.random poisoned), another date = another run ----
        ctx, page, errs = await fresh(b)
        await page.evaluate(D + ".forceModifier = 'speedy'")
        a = await page.evaluate(SEQ)
        check('startDaily: daily mode on, today\'s date, the forced modifier', a['on'] and a['date'] == '2026-10-02' and a['mod'] == 'speedy', a)
        await page.evaluate("window.__mr = Math.random; Math.random = () => 0.5")
        a2 = await page.evaluate(SEQ)
        await page.evaluate("Math.random = window.__mr")
        check('same date, second attempt: identical first 12 wall kinds', a2['kinds'] == a['kinds'], [a['kinds'], a2['kinds']])
        check('same date: identical brick layouts (TNT / holes / power-up bricks) and the same first perk offer', a2['lay'] == a['lay'] and a2['perks'] == a['perks'] and len(a['perks']) == 3, [a['perks'], a2['perks']])
        check('the wall kinds vary within the run (a real mix, not one kind)', len(set(a['kinds'])) >= 3, a['kinds'])
        await page.evaluate("__grasp.setDate('2026-10-03')")
        c = await page.evaluate(SEQ)
        check('another date: another run (wall kinds / layouts / perk offer differ)', c['date'] == '2026-10-03' and (c['kinds'], c['lay'], c['perks']) != (a['kinds'], a['lay'], a['perks']), [a['kinds'], c['kinds'], a['perks'], c['perks']])
        check('another date: wall kinds differ', c['kinds'] != a['kinds'], [a['kinds'], c['kinds']])
        check('no page errors (seed)', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b)  # a reload on the same date: still the same run
        await page.evaluate(D + ".forceModifier = 'speedy'")
        r = await page.evaluate(SEQ)
        check('same date after a reload: identical kinds, layouts and perk offer', (r['kinds'], r['lay'], r['perks']) == (a['kinds'], a['lay'], a['perks']), [a['kinds'], r['kinds']])
        await page.evaluate("__grasp.setGameMode('strike')")  # out of the daily: the hooks follow the (test) date
        seed = await page.evaluate(D + ".seed"); seed2 = await page.evaluate("(() => { __grasp.setDate('2026-10-03'); const s = " + D + ".seed; __grasp.setDate('2026-10-02'); return s; })()")
        check('__grasp.daily.seed: a number keyed by the date', isinstance(seed, int) and seed != seed2, [seed, seed2])

        # ---- Normal Strike is untouched: Math.random path; the daily is always Normal with 3 lives ----
        await page.evaluate("__grasp.setGameMode('strike')")
        nr = await page.evaluate("(() => { const o = Math.random; Math.random = () => 0.123; const v = [__grasp.strikeRand('walls'), __grasp.strikeRand('perks'), __grasp.strikeRand()]; Math.random = o; return { v, on: __grasp.daily.on }; })()")
        check('normal Strike (daily off): strikeRand is Math.random', not nr['on'] and nr['v'] == [0.123, 0.123, 0.123], nr)
        await page.evaluate("__grasp.setStrikeDiff('easy'); __grasp.setGameMode('strike')")
        ez = await page.evaluate("({ p: __grasp.strikeParams(), lives: " + S + ".lives, rate: " + S + ".perkStats().puRate })")
        await page.evaluate(D + ".forceModifier = 'tiny'; __grasp.startDaily()")
        dy = await page.evaluate("(() => { const o = Math.random; Math.random = () => 0.123; const v = __grasp.strikeRand('walls'); Math.random = o; return { v, lives: " + S + ".lives, max: " + S + ".maxLives, radius: sd('STRIKE_HIT_RADIUS'), speed: sd('STRIKE_BASE_SPEED'), easyPill: !!(" + S + ".ui.buttons && " + S + ".ui.buttons.easy), rate: " + S + ".perkStats().puRate, diff: " + S + ".diff }; })()")
        check('daily mode: strikeRand is the seeded generator, not Math.random', dy['v'] != 0.123 and 0 <= dy['v'] < 1, dy)
        check('normal Strike on Easy: the Easy lives (5), for contrast', ez['lives'] == 5, ez)
        check('daily: 3 lives, Normal hit radius / speed / power-up rate', dy['lives'] == 3 and dy['max'] == 3 and dy['radius'] == 1.3 and abs(dy['speed'] - 1.1) < 1e-9 and dy['rate'] < ez['rate'] and dy['diff'] == 'easy', [dy, ez])
        sv = await page.evaluate("({ d: " + S + ".serveAt - performance.now(), b: !!" + S + ".ui.dailyBanner, mod: " + S + ".ui.dailyBanner && " + S + ".ui.dailyBanner.mod })")
        check('daily: the pre-run banner (modifier) is up and the first serve waits for it', sv['b'] and sv['mod'] == 'tiny' and sv['d'] > 1500, sv)
        await page.evaluate("__grasp.setGameMode('strike')")
        check('picking Strike again leaves the daily; normal first serve after 600 ms', not await page.evaluate(D + ".on") and await page.evaluate(S + ".serveAt - performance.now()") < 700)
        check('no page errors (normal Strike)', not errs, errs); await ctx.close()

        # ---- the modifiers ----
        ctx, page, errs = await fresh(b)
        mods = await page.evaluate("(() => { const out = []; for (let i = 0; i < 90; i++) { const d = new Date(2026, 0, 1 + i); out.push(__grasp.daily.modifierFor(localDate(d))); } return out; })()")
        check('modifierFor: deterministic, all 7 modifiers over 90 days', set(mods) == {'glass', 'steel', 'tnt', 'tiny', 'bighands', 'speedy', 'rain'} and mods == await page.evaluate("(() => { const out = []; for (let i = 0; i < 90; i++) out.push(__grasp.daily.modifierFor(localDate(new Date(2026, 0, 1 + i)))); return out; })()"), sorted(set(mods)))
        glass_date = await page.evaluate("(() => { for (let i = 0; i < 90; i++) { const d = localDate(new Date(2026, 9, 2 + i)); if (__grasp.daily.modifierFor(d) === 'glass') return d; } })()")
        await page.evaluate("__grasp.setDate('" + glass_date + "')")
        g = await page.evaluate("(() => { __grasp.startDaily(); const s = __grasp.strike, k = s.walls.map(w => w.kind); s.setLevel(4); for (let i = 0; i < 6; i++) k.push(s.spawnWall().kind); return { k, mod: __grasp.daily.modifier }; })()")
        check('a "Glass day" date (' + str(glass_date) + '): every wall is glass, at level 1 and level 4', g['mod'] == 'glass' and len(g['k']) == 10 and all(x == 'glass' for x in g['k']), g)
        await page.evaluate("__grasp.setDate('2026-10-02')")
        for mod, kind in (('steel', 'steel'), ('tnt', 'tnt')):
            k = await page.evaluate("(() => { __grasp.daily.forceModifier = '" + mod + "'; __grasp.startDaily(); const s = __grasp.strike, k = s.walls.map(w => w.kind); for (let i = 0; i < 16; i++) k.push(s.spawnWall().kind); return { k, lv: s.level, crates: s.walls.filter(w => w.kind === 'tnt').map(w => w.bricks.filter(q => q.tnt).length) }; })()")
            ok = k['lv'] == 1 and kind in k['k'] and set(k['k']) <= {'brick', kind} and (mod != 'tnt' or all(n >= 3 for n in k['crates']))
            check('forceModifier ' + mod + ': ' + kind + ' walls from level 1' + (' (3-4 crates each)' if mod == 'tnt' else ''), ok, k)
        m = await page.evaluate("""(() => { const g = __grasp, s = g.strike, r = {};
          g.daily.forceModifier = 'speedy'; g.startDaily(); r.speedy = s.pace;
          g.daily.forceModifier = 'bighands'; g.startDaily(); r.reach = s.perkStats().reach;
          g.daily.forceModifier = 'tiny'; g.startDaily(); r.tiny = ballR();
          g.daily.forceModifier = 'rain'; g.startDaily(); r.rate = s.perkStats().puRate; r.pu = 0; for (let i = 0; i < 8; i++) r.pu += s.spawnWall().bricks.filter(k => k.pu).length; r.lv = s.level;
          g.daily.forceModifier = 'glass'; g.startDaily(); r.ball = ballR(); r.base = s.pace; r.reach0 = s.perkStats().reach; r.rate0 = s.perkStats().puRate; return r; })()""")
        check('Speedy: pace x1.25', abs(m['speedy'] - m['base'] * 1.25) < 1e-9, m)
        check('Big hands: reach x1.4', abs(m['reach'] - 1.4) < 1e-9 and m['reach0'] == 1, m)
        check('Tiny ball: ball x0.7', abs(m['tiny'] - m['ball'] * 0.7) < 1e-6, m)
        check('Power-up rain: x3 power-up rate, power-up bricks already on level 1', abs(m['rate'] - m['rate0'] * 3) < 1e-9 and m['lv'] == 1 and m['pu'] > 0, m)
        await page.evaluate(D + ".forceModifier = null")
        check('no page errors (modifiers)', not errs, errs); await ctx.close()

        # ---- results: best / attempts / level per date, first-play bonus once a day, streak, milestones, a gap breaks it ----
        ctx, page, errs = await fresh(b, date='2026-10-01')
        c0 = await page.evaluate("__grasp.profile.coins")
        await page.evaluate("__grasp.startDaily()"); await end_run(page, 30, 2)
        c1 = await page.evaluate("__grasp.profile.coins"); rec = await page.evaluate("__grasp.profile.daily")
        check('first daily of the day: +50 coins and a toast', c1 - c0 == 50 and sum('First daily today' in x for x in await page.evaluate(TOASTS)) == 1, [c0, c1])
        check('the record: best, 1 attempt, level', rec.get('2026-10-01') == {'best': 30, 'attempts': 1, 'level': 2}, rec)
        await page.evaluate("__grasp.startDaily()"); await end_run(page, 20)
        c2 = await page.evaluate("__grasp.profile.coins"); rec = await page.evaluate("__grasp.profile.daily")
        check('second attempt the same day: no bonus again; best kept, 2 attempts', c2 == c1 and sum('First daily today' in x for x in await page.evaluate(TOASTS)) == 1 and rec['2026-10-01'] == {'best': 30, 'attempts': 2, 'level': 2}, [c1, c2, rec])
        await page.evaluate("__grasp.startDaily()"); await end_run(page, 45)
        info = await page.evaluate("({ d: { best: " + D + ".best, attempts: " + D + ".attempts, streak: " + D + ".streak }, nb: " + S + ".ui.newBest })")
        check('a higher score: new best for today (ribbon), 3 attempts', info['d'] == {'best': 45, 'attempts': 3, 'streak': 1} and info['nb'], info)
        check('the end card in daily mode: Share, no Easy / Normal pill; the streak chip', await page.evaluate("(() => { const b = " + S + ".ui.buttons; return !!b.share && !b.easy && !b.normal && " + S + ".ui.streakChip.n === 1; })()"))
        streaks = []
        for d in ('2026-10-02', '2026-10-03'):
            await page.evaluate("__grasp.setDate('" + d + "'); __grasp.startDaily()"); await end_run(page, 10)
            streaks.append(await page.evaluate(D + ".streak"))
        ts = await page.evaluate(TOASTS)
        check('consecutive days: the streak counts 2, 3', streaks == [2, 3], streaks)
        check('3-day streak milestone: +100 coins and a toast', any('3-day streak! +100' in x for x in ts) and await page.evaluate("__grasp.profile.coins") - c2 == 50 * 2 + 100, [ts, await page.evaluate("__grasp.profile.coins"), c2])
        rec = await page.evaluate("__grasp.profile.daily")
        check('best / attempts saved per date', rec['2026-10-01']['best'] == 45 and rec['2026-10-02'] == {'best': 10, 'attempts': 1, 'level': 1} and rec['2026-10-03']['attempts'] == 1, rec)
        await page.evaluate("__grasp.setGameMode('strike'); __grasp.setDate('2026-10-04')")  # (during a daily the hooks report the run's date)
        check('the next day, not played yet: the streak is still alive (3)', await page.evaluate(D + ".streak") == 3 and await page.evaluate(D + ".attempts") == 0)
        await page.evaluate("__grasp.setDate('2026-10-06')")
        check('a day skipped: the streak is broken (0)', await page.evaluate(D + ".streak") == 0)
        await page.evaluate("__grasp.startDaily()"); await end_run(page, 5)
        check('playing after the gap: a new streak of 1', await page.evaluate(D + ".streak") == 1)
        await page.reload(); await page.wait_for_timeout(600)
        check('the records survive a reload', await page.evaluate("Object.keys(__grasp.profile.daily).sort().join()") == '2026-10-01,2026-10-02,2026-10-03,2026-10-06')
        check('no page errors (results)', not errs, errs); await ctx.close()

        # ---- the 7-day strip, share (clipboard fallback + toast), end card screenshots (phone, EN / HE) ----
        prof = "localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, coins: 0, xp: 0, daily: { '2026-09-27': { best: 210, attempts: 2, level: 3 }, '2026-09-29': { best: 95, attempts: 1, level: 2 }, '2026-09-30': { best: 400, attempts: 3, level: 4 }, '2026-10-01': { best: 12345, attempts: 1, level: 6 }, 'junk': { best: 1, attempts: 1 } } }));"
        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx, page, errs = await fresh(b, True, he, prof + "Object.defineProperty(navigator, 'share', { value: undefined, configurable: true });")
            check(tag + ': stored records loaded (a bad key dropped); the streak is alive from yesterday (3)', await page.evaluate(D + ".streak") == 3 and 'junk' not in await page.evaluate("__grasp.profile.daily"))
            await page.evaluate("navigator.clipboard.writeText = async (t) => { window.__clip = t; }; 0")
            await page.evaluate(D + ".forceModifier = 'tnt'; __grasp.startDaily()"); await end_run(page, 1234, 5)
            st = await page.evaluate(S + ".ui.strip")
            check(tag + ': end card strip: 7 tiles, the last 7 dates oldest first, bests or empty, today last and highlighted', [x['date'] for x in st] == ['2026-09-26', '2026-09-27', '2026-09-28', '2026-09-29', '2026-09-30', '2026-10-01', '2026-10-02'] and [x['best'] for x in st] == [None, 210, None, 95, 400, 12345, 1234] and [x['today'] for x in st] == [False] * 6 + [True], st)
            inside = all(x['x'] >= 0 and x['x'] + x['w'] <= 360 and x['w'] > 20 for x in st)
            order = (st[0]['x'] > st[-1]['x']) if he else (st[0]['x'] < st[-1]['x'])
            check(tag + ': strip tiles inside the card, ' + ('right to left' if he else 'left to right'), inside and order, [(x['x'], x['w']) for x in st])
            check(tag + ': streak 4 on the end card after today\'s run', await page.evaluate(S + ".ui.streakChip.n") == 4)
            await page.wait_for_timeout(250)
            await page.screenshot(path='tests/out/daily_endcard_' + tag + '.png')
            bt = await page.evaluate(S + ".ui.buttons.share")
            await page.mouse.click(bt['x'] + bt['w'] / 2, bt['y'] + bt['h'] / 2)
            await page.wait_for_function("window.__clip", timeout=3000)
            clip = await page.evaluate("window.__clip")
            exp = ('Grasp אתגר יומי' if he else 'Grasp daily') + ' 2026-10-02: 🧱 1234 · L5 · 🔥4'
            check(tag + ': Share with no navigator.share: the text goes to the clipboard', clip == exp, clip)
            await page.wait_for_function("__grasp.toasts.some(t => t.key === 'copied')", timeout=3000)
            check(tag + ': a "Copied" toast', any(x == ('הועתק' if he else 'Copied') for x in await page.evaluate(TOASTS)) and await page.evaluate(S + ".over"), await page.evaluate(TOASTS))
            await page.evaluate("window.__shared = null; Object.defineProperty(navigator, 'share', { value: async (d) => { window.__shared = d.text; }, configurable: true }); 0")
            r = await page.evaluate(D + ".share()")
            check(tag + ': with navigator.share: the share sheet gets the same text', r == 'shared' and await page.evaluate("window.__shared") == exp, r)
            # the panel strip on the start screen
            await page.tap('#homeBtn'); await page.wait_for_timeout(300); await page.tap('#dailyBtn'); await page.wait_for_timeout(400)
            ps = await page.evaluate("[...document.querySelectorAll('#dStrip .st')].map(e => ({ d: e.dataset.date, v: e.querySelector('b').textContent, today: e.classList.contains('today'), played: e.classList.contains('played') }))")
            check(tag + ': Daily panel strip matches (7 tiles, today highlighted)', [x['d'] for x in ps] == [x['date'] for x in st] and [x['v'] for x in ps] == ['–', '210', '–', '95', '400', '12345', '1234'] and ps[-1]['today'] and ps[-1]['played'] and not ps[0]['played'], ps)
            check(tag + ': no page errors (strip / share)', not errs, errs); await ctx.close()

        # ---- the Daily button on the start screen (phone + desktop, EN / HE), the panel, the in-game banner ----
        for mobile in (True, False):
            for he in (False, True):
                tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en')
                ctx, page, errs = await fresh(b, mobile, he)
                await page.wait_for_timeout(1300)  # entrance done
                exp_mod = await page.evaluate(D + ".modifierFor('2026-10-02')")
                bt = await page.evaluate(BTN)
                mod_txt = await page.evaluate("t('mod_" + exp_mod + "')")
                check(tag + ': Daily button: label, today\'s date, the modifier of the day', bt['label'] == ('אתגר יומי' if he else 'Daily') and bt['modId'] == exp_mod and bt['mod'] == mod_txt and bt['date'] and bt['date'] == await page.evaluate("shortDate('2026-10-02')"), bt)
                check(tag + ': not played today: NEW dot, streak 0 (dim flame)', bt['newShown'] and bt['newText'] == ('חדש' if he else 'NEW') and bt['streak'] == '0' and bt['zero'] and bt['played'] == 'false', bt)
                check(tag + ': Daily button inside the screen, beside Missions, the widest of the row; the start screen still fits', bt['inside'] and not bt['overlap'] and bt['wider'] and bt['fits'], bt)
                if mobile:
                    await page.screenshot(path='tests/out/daily_button_' + ('he' if he else 'en') + '.png')
                    await page.tap('.modes button[data-mode=strike]'); await page.wait_for_timeout(500)
                    check(tag + ': Strike selected (with its Easy / Normal pill) still fits', (await page.evaluate(BTN))['fits'])
                if mobile: await page.tap('#dailyBtn')
                else: await page.click('#dailyBtn')
                await page.wait_for_timeout(400)
                pn = await page.evaluate("(() => { const ov = $('daily'), sh = ov.querySelector('.sheet').getBoundingClientRect(); return { hidden: ov.hidden, inside: sh.left >= 0 && sh.right <= innerWidth && sh.top >= 0 && sh.bottom <= innerHeight, mod: ov.querySelector('.dmod .nm').textContent, desc: ov.querySelector('.dmod .ds').textContent, tiles: ov.querySelectorAll('#dStrip .st').length, title: $('dailyTitle').textContent, gm: gameMode, cam: $('dailyCam').textContent }; })()")
                check(tag + ': Daily panel: title, the modifier and its line, 7 tiles, inside the screen; Strike selected', not pn['hidden'] and pn['inside'] and pn['mod'] == mod_txt and pn['desc'] and pn['tiles'] == 7 and pn['title'] == ('אתגר יומי' if he else 'Daily challenge') and pn['gm'] == 'strike', pn)
                if mobile: await page.screenshot(path='tests/out/daily_panel_' + ('he' if he else 'en') + '.png')
                await page.keyboard.press('Escape'); await page.wait_for_timeout(150)
                check(tag + ': Escape closes the panel', await page.evaluate("$('daily').hidden"))
                if mobile: await page.tap('#dailyBtn')
                else: await page.click('#dailyBtn')
                await page.wait_for_timeout(300)
                if mobile: await page.tap('#dailyMouse')
                else: await page.click('#dailyMouse')
                await page.wait_for_function(D + ".on && " + S + ".ui.dailyBannerBox && " + S + ".ui.dailyBannerBox.a === 1 && Math.abs(" + S + ".ui.dailyBannerBox.x + " + S + ".ui.dailyBannerBox.w / 2 - innerWidth / 2) < 1", timeout=5000)  # slid in
                bb = await page.evaluate(S + ".ui.dailyBannerBox")
                check(tag + ': "Play with mouse or touch" in the panel starts the daily; the pre-run banner shows inside the screen', await page.evaluate("mode") == 'mouse' and bb['x'] >= 0 and bb['x'] + bb['w'] <= await page.evaluate("innerWidth") + 1, bb)
                if mobile:
                    await page.wait_for_timeout(500)
                    await page.screenshot(path='tests/out/daily_banner_' + ('he' if he else 'en') + '.png')
                await end_run(page, 77)
                await page.wait_for_timeout(200)
                if mobile: await page.tap('#homeBtn')
                else: await page.click('#homeBtn')
                await page.wait_for_timeout(400)
                bt = await page.evaluate(BTN)
                check(tag + ': home after a daily: no NEW dot, streak 1, daily mode off', not bt['newShown'] and bt['streak'] == '1' and not bt['zero'] and bt['played'] == 'true' and not await page.evaluate(D + ".on"), bt)
                if mobile: await page.screenshot(path='tests/out/daily_button_played_' + ('he' if he else 'en') + '.png')
                if mobile: await page.tap('#mouseBtn')
                else: await page.click('#mouseBtn')
                await page.wait_for_timeout(300)
                check(tag + ': the plain Play button afterwards is normal Strike, not the daily', not await page.evaluate(D + ".on") and await page.evaluate("gameMode") == 'strike')
                check(tag + ': no page errors (button / panel)', not errs, errs); await ctx.close()

        # ---- the mission, I18N ----
        ctx, page, errs = await fresh(b)
        pool = await page.evaluate("__grasp.missionPool.find(q => q.id === 'daily')")
        check('"Play today\'s daily" is in the mission pool (event daily, goal 1)', pool and pool['ev'] == 'daily' and pool['goals'] == [1], pool)
        day = await page.evaluate("(() => { for (let i = 0; i < 120; i++) { const d = localDate(new Date(2026, 9, 2 + i)); __grasp.setDate(d); if (__grasp.missions.some(m => m.id === 'daily')) return d; } })()")
        check('the daily mission comes up on some days', bool(day), day)
        await page.evaluate("__grasp.startDaily()"); await end_run(page, 3)
        mm = await page.evaluate("__grasp.missions.find(m => m.id === 'daily')")
        check('a finished daily run completes it', mm and mm['done'] and mm['progress'] == 1, mm)
        keys = ['daily', 'dailyTitle', 'dailySub', 'dailyNew', 'dailyBest', 'attemptsN', 'dailyStreak', 'dailyBanner', 'dailyModLabel', 'last7', 'dStreakL', 'dBestL', 'dAttL', 'dailyBonus', 'streakBonus', 'share', 'copied', 'shareFail', 'shareText', 'ms_daily'] + ['mod_' + x for x in ['glass', 'steel', 'tnt', 'tiny', 'bighands', 'speedy', 'rain']] + ['modd_' + x for x in ['glass', 'steel', 'tnt', 'tiny', 'bighands', 'speedy', 'rain']]
        miss = await page.evaluate("(ks => ['en', 'he'].flatMap(l => ks.filter(k => !I18N[l][k] || (l === 'he' && I18N.he[k] === I18N.en[k] && !/^(copied|share)$/.test(k))).map(k => l + ':' + k)))(" + str(keys) + ")")
        check('I18N: every new string in EN and HE (HE translated)', not miss, miss)
        he = await page.evaluate("[I18N.he.daily, I18N.he.mod_glass, I18N.he.ms_daily, I18N.en.ms_daily]")
        check('HE: Daily = "אתגר יומי"; modifier names; mission text', he[0] == 'אתגר יומי' and he[1] == 'יום זכוכית' and he[2] and he[3] == "Play today's daily", he)
        check('no page errors (mission)', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
