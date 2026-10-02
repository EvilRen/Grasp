exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Meta progression: the profile (coins, XP, level, missions, collection) in localStorage, coins earned per event in Slice / Smash / Strike,
# the XP / level formula and its toast, date-seeded daily missions, the collection (buy / equip / skinned sprites) and the start-screen panels.
P = "__grasp.profile"
SFX_JS = "(() => { window.__sfx = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); o(k, a); }; })()"  # every sound asked for, in order
PARK_JS = """
window.parkFruit = (xs, y) => { __grasp.CONFIG.SLICE_GRAVITY = 0; const f = __grasp.slice; f.fruits.length = 0; f.halves.length = 0; f.nextSpawn = 1e12;
  for (const x of [].concat(xs)) f.fruits.push({ x, y, vx: 0, vy: 0, r: 40, rot: 0, vr: 0, kind: {rind:'#ffc24b', flesh:'#ffe3a1', seed:null}, born: 0 }); };
window.dropFruit = () => { __grasp.CONFIG.SLICE_GRAVITY = 0; const f = __grasp.slice; f.nextSpawn = 1e12;
  f.fruits.push({ x: 300, y: innerHeight + 100, vx: 0, vy: 0.5, r: 40, rot: 0, vr: 0, kind: {rind:'#ffc24b', flesh:'#ffe3a1', seed:null}, born: 0 }); };
"""
PILL = "(() => { const b = __grasp.coinUi.box; return b && { x: b.x, y: b.y, w: b.w, h: b.h, inside: b.x >= 0 && b.y >= 0 && b.x + b.w <= innerWidth && b.y + b.h <= innerHeight, W: innerWidth }; })()"
TOASTS = "[...document.querySelectorAll('#metaToast .mt .tx')].map(e => e.textContent)"
KEYS = "(k => [...SPRITES.keys()].filter(q => q.startsWith(k)))"
SHEET = """(id => { const ov = $(id), sh = ov.querySelector('.sheet'), r = sh.getBoundingClientRect(), h2 = sh.querySelector('h2').getBoundingClientRect(), x = sh.querySelector('.xBtn').getBoundingClientRect();
  return { hidden: ov.hidden, inside: r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight, w: r.width, h: r.height, scrolls: sh.scrollHeight > sh.clientHeight + 1, bodyScroll: document.documentElement.scrollHeight > innerHeight + 1,
    xEnd: x.left > h2.left, xIn: x.right <= innerWidth && x.left >= 0 }; })"""
START_FIT = "(() => { const st = $('start'), p = $('metaPill').getBoundingClientRect(), l = $('startLang').getBoundingClientRect(), r = document.querySelector('.metaRow').getBoundingClientRect(), a = document.querySelector('#start a.link').getBoundingClientRect(); return { noScroll: st.scrollHeight <= st.clientHeight + 1 && document.documentElement.scrollHeight <= innerHeight + 1, pillIn: p.left >= 0 && p.right <= innerWidth && p.top >= 0, pillLeftOfLang: p.left < l.left, pillOverlap: p.right > l.left && p.left < l.right, row: [r.left, r.right, r.top, r.bottom], rowIn: r.left >= 0 && r.right <= innerWidth && r.bottom <= innerHeight, linkIn: a.bottom <= innerHeight, btns: [...document.querySelectorAll('.metaBtn')].map(b => b.querySelector('[data-i18n]').textContent.trim()), W: innerWidth, H: innerHeight }; })()"

async def fresh(b, mobile=False, he=False, init=''):
    opts = dict(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width':1280,'height':800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + PARK_JS + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');") + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(700)
    return ctx, page, errs
async def play(page, m, mobile=False):
    if mobile: await page.tap('.modes button[data-mode=' + m + ']'); await page.tap('#mouseBtn')
    else: await page.click('.modes button[data-mode=' + m + ']'); await page.click('#mouseBtn')
    await page.wait_for_timeout(500); await page.evaluate(SFX_JS)
async def drag(page, x0, x1, y, step=40, wait=16):
    await page.mouse.move(x0, y); await page.mouse.down()
    n = max(1, int(abs(x1 - x0) / step))
    for i in range(1, n + 1): await page.mouse.move(x0 + (x1 - x0) * i / n, y); await page.wait_for_timeout(wait)
    await page.mouse.up(); await page.wait_for_timeout(120)
async def end_slice(page):
    for _ in range(3): await page.evaluate("dropFruit()"); await page.wait_for_timeout(120)
    await page.wait_for_function("__grasp.slice.over && __grasp.slice.ui.buttons", timeout=3000); await page.wait_for_timeout(650)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])

        # ---- profile: defaults, persistence, broken storage, reset, the level formula, the start-screen pill ----
        ctx, page, errs = await fresh(b)
        pr = await page.evaluate(P); today = await page.evaluate("localDate()")
        check('fresh profile: 0 coins, 0 xp, level 1, the four default items owned and worn', pr['coins'] == 0 and pr['xp'] == 0 and pr['level'] == 1 and sorted(pr['unlocked']) == ['ball_classic', 'blade_steel', 'hand_classic', 'trail_none'] and pr['equipped'] == {'ball': 'classic', 'hand': 'classic', 'blade': 'steel', 'trail': 'none'}, pr)
        check('fresh profile: 3 missions for today, stats at zero', pr['missions']['date'] == today and len(pr['missions']['list']) == 3 and all(m['progress'] == 0 and not m['done'] and not m['claimed'] and m['goal'] > 0 and m['reward'] > 0 for m in pr['missions']['list']) and all(v == 0 for v in pr['stats'].values()) and set(pr['stats']) == {'bricks', 'fruit', 'cars', 'bosses', 'rounds', 'powerups', 'walls'}, pr)
        raw = await page.evaluate("JSON.parse(localStorage.getItem('grasp.profile'))")
        check("saved under 'grasp.profile' with a schema version", raw and raw['v'] == 1 and raw['missions']['date'] == today, raw)
        lv = await page.evaluate("[0, 49, 50, 199, 200, 449, 450, 800].map(x => __grasp.levelOf(x))")
        check('level = floor(sqrt(xp / 50)) + 1', lv == [1, 1, 2, 2, 3, 3, 4, 5], lv)
        pill = await page.evaluate("({ c: $('metaPill').querySelector('.coins').textContent, l: $('metaPill').querySelector('.lvl').textContent, xp: $('metaPill').querySelector('.xp i').style.width })")
        check('start screen pill: 0 coins, Lv 1, empty XP bar', pill == {'c': '0', 'l': 'Lv 1', 'xp': '0%'}, pill)
        await page.evaluate("__grasp.addCoins(37); __grasp.addXp(25)")
        pill = await page.evaluate("({ c: $('metaPill').querySelector('.coins').textContent, l: $('metaPill').querySelector('.lvl').textContent, xp: $('metaPill').querySelector('.xp i').style.width })")
        check('addCoins / addXp update the pill: 37 coins, half way to level 2', pill == {'c': '37', 'l': 'Lv 1', 'xp': '50%'}, pill)
        await page.reload(); await page.wait_for_timeout(600)
        pr = await page.evaluate(P)
        check('reload: coins and xp persist', pr['coins'] == 37 and pr['xp'] == 25 and pr['missions']['date'] == today, pr)
        await page.evaluate("__grasp.addXp(200)")
        check('level 3 at 225 xp: two level-ups rewarded (+40, +60 coins) and the level-3 item unlocked', await page.evaluate(P + ".level") == 3 and await page.evaluate(P + ".coins") == 137 and 'ball_planet' in await page.evaluate(P + ".unlocked"))
        ts = await page.evaluate(TOASTS)
        check('level-up toasts with the reward, and an unlock toast', any('Level up! Level 2' in x and '+40' in x for x in ts) and any('Level up! Level 3' in x and '+60' in x for x in ts) and any('Unlocked: Planet' in x for x in ts), ts)
        await page.evaluate("__grasp.profileReset()")
        pr = await page.evaluate(P)
        check('profileReset: back to the defaults (missions for today regenerated)', pr['coins'] == 0 and pr['xp'] == 0 and pr['level'] == 1 and len(pr['unlocked']) == 4 and len(pr['missions']['list']) == 3, pr)
        for bad, what in [("'{bad'", 'broken JSON'), ('\'{"v":99,"coins":500}\'', 'another schema version'), ('\'{"v":1,"coins":12,"xp":"x","equipped":{"ball":"disco"},"unlocked":["nope","ball_beach"],"stats":{"fruit":-3}}\'', 'a partial, partly wrong object')]:
            await page.evaluate("localStorage.setItem('grasp.profile', " + bad + ")"); await page.reload(); await page.wait_for_timeout(600)
            pr = await page.evaluate(P)
            exp = pr['coins'] == (12 if 'partial' in what else 0) and pr['xp'] == 0 and pr['equipped']['ball'] == 'classic' and 'nope' not in pr['unlocked'] and pr['stats']['fruit'] == 0 and len(pr['missions']['list']) == 3
            check('storage holds ' + what + ': safe defaults, the valid fields kept', exp and ('ball_beach' in pr['unlocked']) == ('partial' in what), pr)
        check('profile: no page errors', not errs, errs); await ctx.close()

        # ---- coins per event: Slice ----
        ctx, page, errs = await fresh(b)
        await play(page, 'slice'); await page.mouse.move(100, 700); await page.wait_for_timeout(100)
        await page.evaluate("parkFruit(640, 400)"); await drag(page, 400, 880, 400)
        pr = await page.evaluate(P); ev = await page.evaluate("__grasp.events")
        check('slice: a fruit cut = +1 coin, fruit stat, track(fruit)', pr['coins'] == 1 and pr['stats']['fruit'] == 1 and ['fruit', 1] in ev, [pr['coins'], pr['stats'], ev])
        check('slice: coin chime played, a +1 floater rises over the pill', 'coin' in await page.evaluate("__sfx") and await page.evaluate("__grasp.coinUi.floaters.some(f => f.n === 1 && f.text.endsWith('+1'))"))
        pl = await page.evaluate(PILL)
        check('slice: coin pill on the HUD row, at the start edge beside the score', pl and pl['inside'] and pl['x'] == 16 and pl['y'] < await page.evaluate("scoreY()"), pl)
        await page.evaluate("parkFruit([500, 600, 700], 400)"); await drag(page, 380, 900, 400, step=60)
        pr = await page.evaluate(P); ev = await page.evaluate("__grasp.events")
        check('slice: three fruit in one swipe = +3 coins, a ×3 combo tracked once', pr['coins'] == 4 and pr['stats']['fruit'] == 4 and await page.evaluate("__grasp.slice.bestCombo") >= 3 and ev.count(['combo', 1]) == 1, [pr['coins'], ev])
        await page.evaluate("__grasp.addXp(45); __grasp.slice.score = 63"); await page.evaluate("__sfx.length = 0"); await end_slice(page)
        pr = await page.evaluate(P); ts = await page.evaluate(TOASTS)
        check('round over: xp += score / 10 (6) -> level 2, +40 reward coins, rounds stat, track(round)', pr['xp'] == 51 and pr['level'] == 2 and pr['coins'] == 44 and pr['stats']['rounds'] == 1 and ['round', 1] in await page.evaluate("__grasp.events"), pr)
        check('level-up toast over the end card + levelup sound', any('Level up! Level 2' in x and '+40' in x for x in ts) and 'levelup' in await page.evaluate("__sfx"), ts)
        card = await page.evaluate("(() => { const ui = __grasp.slice.ui, bt = ui.buttons.again; return { rows: ui.missionRow, coin: ui.coinBox, bt }; })()")
        check('end card: a compact row of the 3 missions above the buttons, and the coins earned this round', len(card['rows']) == 3 and all(r['y'] < card['bt']['y'] and r['w'] > 60 for r in card['rows']) and card['coin'] and card['coin']['n'] == 44, card)
        await page.screenshot(path='tests/out/meta_endcard_slice.png')
        check('slice coins: no page errors', not errs, errs); await ctx.close()

        # ---- coins per event: Smash ----
        ctx, page, errs = await fresh(b)
        await play(page, 'smash')
        tgt = await page.evaluate("(() => { const bs = __grasp.smash.bricks.filter(b => b.plugin.wall.id === 0); const top = Math.min(...bs.map(b => b.position.y)); return { x: __grasp.smash.walls[0].x, y: top + 10 }; })()")
        await page.mouse.move(tgt['x'] - 260, tgt['y']); await page.wait_for_timeout(120); await drag(page, tgt['x'] - 260, tgt['x'] + 260, tgt['y'], step=64)
        st = await page.evaluate("({ out: __grasp.smash.bricksOut, coins: " + P + ".coins, bricks: " + P + ".stats.bricks, walls: __grasp.events.filter(e => e[0] === 'wall').length, ev: __grasp.events })")
        check('smash: a coin per brick knocked loose (+5 per wall down)', st['out'] > 0 and st['coins'] == st['out'] + 5 * st['walls'] and st['bricks'] == st['out'], st)
        pl = await page.evaluate(PILL)
        check('smash: coin pill on the HUD row', pl and pl['inside'] and pl['x'] == 16, pl)
        last = await page.evaluate("(() => { const w = __grasp.smash.walls[1], bs = __grasp.smash.bricks.filter(b => b.plugin.wall === w), keep = bs[0]; for (const b of bs.slice(1)) { M.Composite.remove(world, b); __grasp.smash.bricks.splice(__grasp.smash.bricks.indexOf(b), 1); w.left--; } return { x: keep.position.x, y: keep.position.y, left: w.left }; })()")
        c0, e0 = await page.evaluate("[" + P + ".coins, __grasp.events.length]")
        await page.mouse.move(last['x'] - 260, last['y']); await page.wait_for_timeout(120); await drag(page, last['x'] - 260, last['x'] + 260, last['y'], step=64)
        st = await page.evaluate("({ coins: " + P + ".coins, walls: " + P + ".stats.walls, ev: __grasp.events.slice(" + str(e0) + ") })")
        paid = sum(n for e, n in st['ev'] if e == 'brick') + 5 * sum(1 for e, n in st['ev'] if e == 'wall')  # the swing may clip the other wall too (smash radius): every brick paid once, the wall down once
        check('smash: the last brick of a wall = +1 +5, track(wall); coins match the events exactly', last['left'] == 1 and st['coins'] == c0 + paid and st['walls'] == 1 and st['ev'].count(['wall', 1]) == 1 and st['ev'].count(['brick', 1]) >= 1, [last, c0, st])
        await page.evaluate("__grasp.smash.nextCar = 0"); await page.wait_for_timeout(300)
        await page.evaluate("(() => { const c = __grasp.smash.cars[0]; M.Body.setPosition(c, { x: innerWidth * 0.5, y: c.plugin.y }); })()"); await page.wait_for_timeout(50)
        cy = await page.evaluate("__grasp.smash.cars[0].parts[1].position.y"); c0 = await page.evaluate(P + ".coins"); n0 = await page.evaluate("__grasp.smash.pieces.length")
        await page.mouse.move(340, cy); await page.wait_for_timeout(120); await drag(page, 340, 940, cy, step=64)
        st = await page.evaluate("({ coins: " + P + ".coins, cars: " + P + ".stats.cars, out: __grasp.smash.carsOut, pieces: __grasp.smash.pieces.length })")
        check('smash: a coin per car part, track(car)', st['out'] == 1 and st['cars'] == 1 and st['coins'] - c0 >= 12 and ['car', 1] in await page.evaluate("__grasp.events"), [c0, st, n0])
        await page.evaluate("__grasp.smash.score = 128; __grasp.setRoundEnd(performance.now())"); await page.wait_for_function("__grasp.smash.over", timeout=2000); await page.wait_for_timeout(700)
        pr = await page.evaluate(P)
        check('smash round over: xp = score / 10, rounds stat', pr['xp'] == 12 and pr['stats']['rounds'] == 1, pr)
        check('smash end card lists the missions', len(await page.evaluate("__grasp.smash.ui.missionRow")) == 3)
        check('smash coins: no page errors', not errs, errs); await ctx.close()

        # ---- coins per event: Strike ----
        ctx, page, errs = await fresh(b)
        await play(page, 'strike'); await page.mouse.move(640, 700); await page.wait_for_timeout(300)
        n = await page.evaluate("__grasp.strike.walls[0].bricks.filter(k => k.alive).length"); c0 = await page.evaluate(P + ".coins")
        await page.evaluate("__grasp.strike.smashTest('super')"); await page.wait_for_timeout(200)
        st = await page.evaluate("({ coins: " + P + ".coins, bricks: " + P + ".stats.bricks, walls: " + P + ".stats.walls, ev: __grasp.events })")
        check('strike: SUPER through a wall = a coin per brick + 5 for the wall, track(brick n) + track(wall)', st['coins'] == c0 + n + 5 and st['bricks'] == n and st['walls'] == 1 and ['brick', n] in st['ev'] and ['wall', 1] in st['ev'], [n, c0, st])
        pl = await page.evaluate(PILL); hud = await page.evaluate("__grasp.strike.ui.hud")
        check('strike: coin pill under the HUD card at the end edge', pl and pl['inside'] and pl['y'] >= hud['y'] + hud['h'] and pl['x'] + pl['w'] <= hud['x'] + hud['w'] and pl['x'] > hud['x'] + hud['w'] / 2, [pl, hud])
        await page.evaluate("__grasp.strike.balls.length = 0; __grasp.strike.serveAt = performance.now() + 1e9")  # the SUPER ball would go on through the queue: no more coins from it
        c0 = await page.evaluate(P + ".coins"); await page.evaluate("__grasp.strike.catchTest('big')"); await page.wait_for_timeout(100)
        check('strike: a power-up caught = +3, track(powerup)', await page.evaluate(P + ".coins") == c0 + 3 and await page.evaluate(P + ".stats.powerups") == 1 and ['powerup', 1] in await page.evaluate("__grasp.events"))
        c0 = await page.evaluate(P + ".coins"); await page.evaluate("__grasp.strike.spawnBoss(1); for (let i = 0; i < 20 && __grasp.strike.boss; i++) __grasp.strike.bossHit('super')"); await page.wait_for_timeout(150)
        check('strike: a boss beaten = +25, track(boss)', await page.evaluate("!__grasp.strike.boss && __grasp.strike.bosses === 1") and await page.evaluate(P + ".coins") == c0 + 25 and await page.evaluate(P + ".stats.bosses") == 1 and ['boss', 1] in await page.evaluate("__grasp.events"))
        await page.evaluate("__grasp.strike.setCleared(5)"); await page.wait_for_timeout(50)
        check('strike: reaching level 2 tracks strikeLevel 2', await page.evaluate("__grasp.strike.level") == 2 and ['strikeLevel', 2] in await page.evaluate("__grasp.events"))
        await page.evaluate("__grasp.strike.score = 95; __grasp.strike.lives = 1; cursor.history.length = 0; __grasp.strike.setBallZ(-__grasp.CONFIG.STRIKE_HIT_Z * 0.7, innerWidth * 0.5, innerHeight * 0.1)"); await page.wait_for_function("__grasp.strike.over", timeout=3000); await page.wait_for_timeout(700)
        pr = await page.evaluate(P)
        check('strike round over: xp = score / 10 (9), rounds stat', pr['xp'] == 9 and pr['stats']['rounds'] == 1, pr)
        check('strike end card lists the missions and the round coins', len(await page.evaluate("__grasp.strike.ui.missionRow")) == 3 and (await page.evaluate("__grasp.strike.ui.coinBox.n")) == pr['coins'])
        await page.screenshot(path='tests/out/meta_endcard_strike.png')
        check('strike coins: no page errors', not errs, errs); await ctx.close()

        # ---- daily missions: seeded by the date, progress through track, completion toast + reward, claim ----
        ctx, page, errs = await fresh(b, init="sessionStorage.setItem('grasp.testDate', '2026-03-01');")
        await page.evaluate(SFX_JS)
        a = await page.evaluate("__grasp.missions")
        check('a set date gives 3 distinct missions from the pool', len(a) == 3 and len({m['id'] for m in a}) == 3 and all(m['id'] in ['fruit', 'bricks', 'cars', 'walls', 'powerups', 'boss', 'strikeLevel', 'rounds', 'combo'] for m in a) and await page.evaluate(P + ".missions.date") == '2026-03-01', a)
        ev0 = await page.evaluate("__grasp.missionPool.find(q => q.id === '" + a[0]['id'] + "').ev")
        await page.evaluate("__grasp.track('" + ev0 + "', 1)")
        await page.reload(); await page.wait_for_timeout(600); await page.evaluate(SFX_JS)
        a2 = await page.evaluate("__grasp.missions")
        check('reload on the same date: the same missions, progress kept', [(m['id'], m['goal'], m['reward']) for m in a2] == [(m['id'], m['goal'], m['reward']) for m in a] and a2[0]['progress'] == 1, [a, a2])
        lists = {}
        for d in ['2026-03-02', '2026-03-05', '2026-04-11']:
            await page.evaluate("__grasp.setDate('" + d + "')"); lists[d] = [(m['id'], m['goal']) for m in await page.evaluate("__grasp.missions")]
        ids = [tuple(m['id'] for m in a)] + [tuple(x[0] for x in v) for v in lists.values()]
        check('other dates: different lists, fresh progress', len(set(ids)) >= 3 and await page.evaluate(P + ".missions.date") == '2026-04-11' and all(m['progress'] == 0 for m in await page.evaluate("__grasp.missions")), ids)
        await page.evaluate("__grasp.setDate('2026-03-01')"); m0 = (await page.evaluate("__grasp.missions"))[0]
        check('back to the first date: its list again (regenerated from the seed)', m0['id'] == a[0]['id'] and m0['goal'] == a[0]['goal'], [a[0], m0])
        c0 = await page.evaluate(P + ".coins"); mx = await page.evaluate("!!__grasp.missionPool.find(q => q.id === '" + m0['id'] + "').max")
        await page.evaluate("__sfx.length = 0; __grasp.track('" + ev0 + "', " + str(m0['goal'] - 1) + ")")
        m = (await page.evaluate("__grasp.missions"))[0]
        check('track(event, n) adds to the mission (or reports the best value)', m['progress'] == m0['goal'] - 1 and not m['done'] and 'mission' not in await page.evaluate("__sfx"), m)
        await page.evaluate("__grasp.track('" + ev0 + "', " + str(m0['goal'] if mx else 1) + ")")
        m = (await page.evaluate("__grasp.missions"))[0]; ts = await page.evaluate(TOASTS)
        check('goal reached: done (progress capped), toast with a check and the reward, mission sound, coins not yet paid', m['done'] and m['progress'] == m['goal'] and not m['claimed'] and any('Mission complete' in x and '+' + str(m['reward']) in x for x in ts) and 'mission' in await page.evaluate("__sfx") and await page.evaluate(P + ".coins") == c0, [m, ts])
        check('toast card has the check icon', await page.evaluate("!!document.querySelector('#metaToast .mt.ok .ic svg')"))
        await page.evaluate("__grasp.track('" + ev0 + "', 5)")
        check('a done mission does not count further', (await page.evaluate("__grasp.missions"))[0]['progress'] == m['goal'])
        nb = await page.evaluate("({ hidden: $('missionsBtn').querySelector('.nb').hidden, n: $('missionsBtn').querySelector('.nb').textContent })")
        check('Missions button shows 1 claimable', nb == {'hidden': False, 'n': '1'}, nb)
        await page.click('#missionsBtn'); await page.wait_for_timeout(200)
        rows = await page.evaluate("[...document.querySelectorAll('#mlist .mrow')].map(r => ({ id: r.dataset.id, done: r.classList.contains('done'), claim: !!r.querySelector('.claim'), ok: !!r.querySelector('.ok'), bar: r.querySelector('.bar i').style.width, pr: r.querySelector('.pr').textContent, nm: r.querySelector('.nm').textContent }))")
        check('Missions panel: 3 rows with name, progress bar and count; the done one offers Claim', len(rows) == 3 and rows[0]['done'] and rows[0]['claim'] and rows[0]['bar'] == '100%' and rows[0]['pr'] == str(m['goal']) + ' / ' + str(m['goal']) and all(r['nm'] and not r['ok'] for r in rows) and not rows[1]['claim'], rows)
        await page.click('#mlist .mrow .claim'); await page.wait_for_timeout(150)
        m = (await page.evaluate("__grasp.missions"))[0]; rows = await page.evaluate("[...document.querySelectorAll('#mlist .mrow')].map(r => ({ claim: !!r.querySelector('.claim'), ok: !!r.querySelector('.ok') }))")
        check('Claim: reward paid, row shows a check, badge gone', m['claimed'] and await page.evaluate(P + ".coins") == c0 + m['reward'] and rows[0] == {'claim': False, 'ok': True} and await page.evaluate("$('missionsBtn').querySelector('.nb').hidden"), [m, rows])
        check('claiming twice pays once', not await page.evaluate("__grasp.claimMission('" + m['id'] + "')") and await page.evaluate(P + ".coins") == c0 + m['reward'])
        await page.reload(); await page.wait_for_timeout(600)
        check('claimed state persists', (await page.evaluate("__grasp.missions"))[0]['claimed'])
        await page.evaluate("__grasp.setDate('2026-03-09'); __grasp.track('fruit', 1)")
        check('a new day: a fresh list', await page.evaluate(P + ".missions.date") == '2026-03-09' and all(not x['done'] and not x['claimed'] for x in await page.evaluate("__grasp.missions")))
        check('missions: no page errors', not errs, errs); await ctx.close()

        # ---- collection: items, buy, equip, level unlocks, the sprites the modes draw ----
        ctx, page, errs = await fresh(b)
        await page.evaluate(SFX_JS)
        items = await page.evaluate("__grasp.collection.items")
        check('18 items: 5 balls, 6 hands, 3 blades, 4 trails, each with a cost or a level', len(items) == 18 and [sum(1 for i in items if i['type'] == ty) for ty in ['ball', 'hand', 'blade', 'trail']] == [5, 6, 3, 4] and all(('cost' in i) != ('level' in i) for i in items), items)
        check('buy while poor fails: nothing deducted, still locked', not await page.evaluate("__grasp.collection.buy('ball_beach')") and await page.evaluate(P + ".coins") == 0 and 'ball_beach' not in await page.evaluate(P + ".unlocked"))
        check('equip a locked item fails', not await page.evaluate("__grasp.collection.equip('ball_beach')") and await page.evaluate(P + ".equipped.ball") == 'classic')
        await page.evaluate("__grasp.addCoins(100); __sfx.length = 0")
        ok = await page.evaluate("__grasp.collection.buy('ball_beach')"); pr = await page.evaluate(P)
        check('buy with coins: 100 - 60 = 40, unlocked, unlock sound + toast', ok and pr['coins'] == 40 and 'ball_beach' in pr['unlocked'] and 'unlock' in await page.evaluate("__sfx") and any('Unlocked: Beach ball' in x for x in await page.evaluate(TOASTS)), pr)
        check('buying again fails (already owned)', not await page.evaluate("__grasp.collection.buy('ball_beach')") and await page.evaluate(P + ".coins") == 40)
        check('equip: the ball skin changes and persists', await page.evaluate("__grasp.collection.equip('ball_beach')") and await page.evaluate(P + ".equipped.ball") == 'beach' and await page.evaluate("JSON.parse(localStorage.getItem('grasp.profile')).equipped.ball") == 'beach')
        check('a level item cannot be bought early', not await page.evaluate("__grasp.collection.buy('hand_cat')") and 'hand_cat' not in await page.evaluate(P + ".unlocked"))
        await page.evaluate("__grasp.addCoins(1000); __grasp.collection.buy('hand_mint'); __grasp.collection.equip('hand_mint'); __grasp.collection.buy('blade_neon'); __grasp.collection.equip('blade_neon'); __grasp.collection.buy('trail_fire'); __grasp.collection.equip('trail_fire')")
        await play(page, 'strike'); await page.mouse.move(640, 500); await page.wait_for_timeout(400)
        ks = await page.evaluate(KEYS + "('strikeBall|')"); hk = await page.evaluate(KEYS + "('strikeHand|')")
        check('strike draws the beach ball and the mint hand (sprites keyed by skin)', any(k.startswith('strikeBall|beach|') for k in ks) and not any(k.startswith('strikeBall|classic') for k in ks) and hk == ['strikeHand|mint'], [ks, hk])
        await page.evaluate("__grasp.collection.equip('ball_classic')"); await page.wait_for_timeout(150)
        check('equipping mid-game switches the sprite', any(k.startswith('strikeBall|classic|') for k in await page.evaluate(KEYS + "('strikeBall|')")))
        await page.evaluate("__grasp.strike.smashTest('hard')"); await page.wait_for_timeout(200)
        check('fire trail sheds embers behind the returning ball', await page.evaluate("particles.some(p => p.color === '#ff8a3d' || p.color === '#ffe07a')"))
        await page.click('#homeBtn'); await page.wait_for_timeout(200); await play(page, 'smash'); await page.mouse.move(640, 500); await page.mouse.down(); await page.wait_for_timeout(150); await page.mouse.up()
        check('smash draws the mint glove', await page.evaluate(KEYS + "('glove|')") == ['glove|mint'])
        await page.click('#homeBtn'); await page.wait_for_timeout(200); await play(page, 'slice'); await page.evaluate("parkFruit(640, 400)"); await drag(page, 400, 880, 400)
        check('slice draws the neon katana', await page.evaluate(KEYS + "('katana|')") == ['katana|neon'])
        await page.click('#homeBtn'); await page.wait_for_timeout(300)
        # the panel
        await page.click('#collectionBtn'); await page.wait_for_timeout(250)
        tl = await page.evaluate("[...document.querySelectorAll('#collection .tile')].map(b => ({ id: b.dataset.id, locked: b.classList.contains('locked'), eq: b.classList.contains('equipped'), lk: !!b.querySelector('.lk'), st: b.querySelector('.st').textContent.trim(), nm: b.querySelector('.nm').textContent, drawn: (() => { const c = b.querySelector('canvas'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++; return n > 200; })() }))")
        unl = await page.evaluate(P + ".unlocked"); eq = await page.evaluate(P + ".equipped")
        check('Collection panel: 18 tiles, each with a drawn preview and a name', len(tl) == 18 and all(x['drawn'] and x['nm'] for x in tl), tl)
        check('locked tiles dim with a lock and the cost / level; owned say Equip; the worn ones say Equipped', all(x['locked'] == (x['id'] not in unl) and x['lk'] == x['locked'] for x in tl) and all((x['st'] == '300') for x in tl if x['id'] == 'ball_disco') and all(x['st'] == 'Lv 5' for x in tl if x['id'] == 'hand_cat') and sum(1 for x in tl if x['eq']) == 4 and all(x['eq'] == (eq[x['id'].split('_')[0]] == x['id'].split('_', 1)[1]) for x in tl) and all(x['st'] == ('Equipped' if x['eq'] else 'Equip') for x in tl if not x['locked']), tl)
        c0 = await page.evaluate(P + ".coins"); await page.evaluate("__sfx.length = 0")
        await page.click('#collection .tile[data-id=hand_sky]'); await page.wait_for_timeout(100)
        st = await page.evaluate("({ coins: " + P + ".coins, eq: " + P + ".equipped.hand, cls: document.querySelector('#collection .tile[data-id=hand_sky]').className, cf: document.querySelectorAll('#collection .cf').length })")
        check('tap a locked, affordable tile: bought (-50), worn, confetti, unlock sound', st['coins'] == c0 - 50 and st['eq'] == 'sky' and 'equipped' in st['cls'] and st['cf'] > 10 and 'unlock' in await page.evaluate("__sfx"), st)
        await page.evaluate(P + ".coins = 10; __grasp.addCoins(0); syncMeta()"); await page.click('#collection .tile[data-id=ball_disco]'); await page.wait_for_timeout(100)
        st = await page.evaluate("({ coins: " + P + ".coins, cls: document.querySelector('#collection .tile[data-id=ball_disco]').className })")
        check('tap a locked tile you cannot afford: still locked, shakes, "more coins" toast', st['coins'] == 10 and 'locked' in st['cls'] and 'shake' in st['cls'] and any('290 more coins' in x for x in await page.evaluate(TOASTS)), st)
        await page.click('#collection .tile[data-id=hand_cat]'); await page.wait_for_timeout(100)
        check('tap a level-locked tile: "reach level" toast', any('Reach level 5' in x for x in await page.evaluate(TOASTS)) and 'hand_cat' not in await page.evaluate(P + ".unlocked"))
        await page.click('#collection .tile[data-id=hand_mint]'); await page.wait_for_timeout(100)
        check('tap an owned tile: worn', await page.evaluate(P + ".equipped.hand") == 'mint' and 'equipped' in await page.evaluate("document.querySelector('#collection .tile[data-id=hand_mint]').className"))
        await page.screenshot(path='tests/out/meta_desktop_collection.png')
        check('collection: no page errors', not errs, errs); await ctx.close()

        # ---- start screen + panels on a phone, EN and HE; the HUD pill in every mode ----
        for he in (False, True):
            tag = 'phone ' + ('he' if he else 'en')
            ctx, page, errs = await fresh(b, True, he, "localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, coins: 123, xp: 60 }));")
            await page.wait_for_timeout(1300)
            f = await page.evaluate(START_FIT)
            check(tag + ': coins + level pill at the top opposite the language button, no overlap, start screen fits', f['noScroll'] and f['pillIn'] and f['pillLeftOfLang'] == (not he) and not f['pillOverlap'] and f['rowIn'] and f['linkIn'], f)
            check(tag + ': pill reads 123 coins, Lv 2; Missions + Collection buttons', await page.evaluate("$('metaPill').querySelector('.coins').textContent") == '123' and await page.evaluate("$('metaPill').querySelector('.lvl').textContent") == ('רמה 2' if he else 'Lv 2') and f['btns'] == (['משימות', 'אוסף'] if he else ['Missions', 'Collection']), f)
            await page.tap('.modes button[data-mode=strike]'); await page.wait_for_timeout(500)
            check(tag + ': strike selected (with its pill) still fits', (await page.evaluate(START_FIT))['noScroll'])
            await page.screenshot(path='tests/out/meta_' + tag.replace(' ', '_') + '_start.png')
            await page.tap('#missionsBtn'); await page.wait_for_timeout(350)
            s = await page.evaluate(SHEET + "('missions')")
            check(tag + ': Missions panel opens inside the viewport, no page scroll, close button at the inline end', not s['hidden'] and s['inside'] and not s['bodyScroll'] and s['xIn'] and s['xEnd'] == (not he), s)
            check(tag + ': mission names in ' + ('Hebrew' if he else 'English'), await page.evaluate("[...document.querySelectorAll('#mlist .nm')].every(e => " + ("/[\\u0590-\\u05ff]/" if he else "/^[A-Za-z]/") + ".test(e.textContent))"))
            await page.screenshot(path='tests/out/meta_' + tag.replace(' ', '_') + '_missions.png')
            await page.tap('#missions .xBtn'); await page.wait_for_timeout(100)
            check(tag + ': close button closes it', await page.evaluate("$('missions').hidden"))
            await page.tap('#collectionBtn'); await page.wait_for_timeout(350)
            s = await page.evaluate(SHEET + "('collection')")
            tiles = await page.evaluate("(() => { const sh = $('collection').querySelector('.sheet').getBoundingClientRect(); return [...document.querySelectorAll('#collection .tile')].map(b => { const r = b.getBoundingClientRect(); return r.width >= 80 && r.left >= sh.left && r.right <= sh.right && b.querySelector('.nm').scrollWidth <= b.querySelector('.nm').clientWidth + 1; }); })()")
            check(tag + ': Collection panel fits the phone and scrolls inside; every tile inside the sheet with its name fitting', not s['hidden'] and s['inside'] and s['scrolls'] and not s['bodyScroll'] and s['xEnd'] == (not he) and len(tiles) == 18 and all(tiles), [s, tiles])
            await page.screenshot(path='tests/out/meta_' + tag.replace(' ', '_') + '_collection.png')
            await page.evaluate("$('collection').querySelector('.sheet').scrollTop = 400"); await page.wait_for_timeout(100)
            await page.screenshot(path='tests/out/meta_' + tag.replace(' ', '_') + '_collection_scrolled.png')
            await page.keyboard.press('Escape'); await page.wait_for_timeout(100)
            check(tag + ': Escape closes the panel', await page.evaluate("$('collection').hidden"))
            await page.tap('#collectionBtn'); await page.wait_for_timeout(200); await page.evaluate("$('collection').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }))"); await page.wait_for_timeout(100)
            check(tag + ': a tap on the backdrop closes the panel', await page.evaluate("$('collection').hidden"))
            await page.tap('#metaPill'); await page.wait_for_timeout(200)
            check(tag + ': the coins pill opens the collection', not await page.evaluate("$('collection').hidden")); await page.keyboard.press('Escape')
            for m in ['slice', 'smash', 'strike']:
                await page.tap('.modes button[data-mode=' + m + ']'); await page.tap('#mouseBtn'); await page.wait_for_timeout(600)
                await page.evaluate("__grasp.addCoins(7)"); await page.wait_for_timeout(100)
                pl = await page.evaluate(PILL)
                if m == 'strike':
                    hud = await page.evaluate("__grasp.strike.ui.hud")
                    ok = pl['inside'] and pl['y'] >= hud['y'] + hud['h'] and (pl['x'] >= hud['x'] + hud['w'] / 2 if not he else pl['x'] + pl['w'] <= hud['x'] + hud['w'] / 2)
                else: ok = pl['inside'] and (pl['x'] == 16 if not he else pl['x'] + pl['w'] == pl['W'] - 16) and pl['y'] + pl['h'] <= await page.evaluate("scoreY()") + 30
                check(tag + ': ' + m + ' HUD coin pill inside the screen at the start edge (Strike: end edge under the card)', ok, [pl, m])
                if m == 'strike': await page.screenshot(path='tests/out/meta_' + tag.replace(' ', '_') + '_hud_strike.png')
                if m == 'slice': await page.screenshot(path='tests/out/meta_' + tag.replace(' ', '_') + '_hud_slice.png')
                await page.tap('#homeBtn'); await page.wait_for_timeout(300)
            check(tag + ': home refreshes the pill', await page.evaluate("$('metaPill').querySelector('.coins').textContent") == '144')
            check(tag + ': no page errors', not errs, errs); await ctx.close()

        # ---- toasts fade ----
        ctx, page, errs = await fresh(b)
        await page.evaluate("__grasp.addXp(60)"); await page.wait_for_timeout(100)
        check('toast shows at the top, inside the viewport', await page.evaluate("(() => { const r = document.querySelector('#metaToast .mt').getBoundingClientRect(); return r.top > 0 && r.top < 160 && r.left >= 0 && r.right <= innerWidth; })()"))
        await page.wait_for_timeout(3700)
        check('toast gone after ~3.5 s', await page.evaluate("document.querySelectorAll('#metaToast .mt').length") == 0)
        check('toasts: no page errors', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
