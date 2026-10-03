exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Pacing step 2: progress across days. The road (Strike unlocks by player level, persisted in the profile, gating the in-run pacing; the daily
# ignores it with 'Preview!' tags), the NEW UNLOCKED card and the next run's spotlight, the Road panel, the pill's next unlock, worlds (a boss
# closes each world of 6 levels, beating it unlocks a checkpoint start on the world map), per-world corridor palettes in 2D and 3D, the boss
# chest and its prize table, the Golden ticket, and the XP a run earns. Hooks: __grasp.road, __grasp.worlds, __grasp.setPlayerLevel,
# __grasp.runXp, strike.world, strike.chest (open()), strike.chestPrize(seed), strike.lastSpot, strike.ui.spot / chest.
S = "__grasp.strike"
P = "__grasp.profile"
SFX_JS = "(() => { window.__sfx = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); o(k, a); }; })()"
FRAMES = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
PARK = f"(() => {{ const s = {S}; if (!s.ball) s.serve(); s.setBallZ(2300, 30, 30); s.ball.speed = 0; s.lives = 40; }})()"
PIX = "((x, y) => __grasp.strike.pixel(x, y))"
TOASTS = "[...document.querySelectorAll('#metaToast .mt .tx')].map(e => e.textContent)"
LADDER = [('brick', 1), ('cow', 1), ('glass', 2), ('pu_big', 3), ('perks1', 4), ('steel', 5), ('pu_slow', 6), ('monkey', 7), ('curve', 8), ('pu_multi', 9), ('perks2', 10),
          ('holed', 11), ('pu_fire', 12), ('moving', 14), ('perks3', 15), ('tnt', 16), ('pu_life', 17), ('wobble', 18), ('w5set', 19), ('legend', 20)]
# a low-level player's run at a high run level: what the walls, power-up bricks, serves and perk offers bring (many walls simulated)
GATE_SIM = f"""((plv, L) => {{ const s = {S}; __grasp.setPlayerLevel(plv); s.setLevel(L); const lv0 = s.lives; s.lives = 1; const kinds = {{}}, pus = {{}}, guests = {{}};
  for (let i = 0; i < 300; i++) {{ const w = s.spawnWall(undefined, 9000 + i); kinds[w.kind] = (kinds[w.kind] || 0) + 1; for (const k of w.bricks) if (k.pu) pus[k.pu] = (pus[k.pu] || 0) + 1; s.walls.splice(s.walls.indexOf(w), 1); }}
  let curved = 0, waves = 0, plain = 0; for (let i = 0; i < 240; i++) {{ s.serve(); const b = s.ball; if (b.guest) guests[b.guest] = (guests[b.guest] || 0) + 1; else {{ plain++; if (b.curve) curved++; if (b.waves > 1 && b.curve) waves++; }} }}
  s.ball.guest = null; s.lives = lv0; const offers = []; for (let i = 0; i < 30; i++) {{ s.perks = {{}}; if (s.offerPerks()) offers.push(...s.perkOffer); s.perkOffer = null; }}
  const pc = s.pacing; return {{ kinds, pus, guests, curved, waves, plain, offers: [...new Set(offers)].sort(), puRate: pc.puRate, perksOpen: pc.perks, guestsOn: pc.guestsOn }}; }})"""
START_FIT = "(() => { const st = $('start'), p = $('metaPill').getBoundingClientRect(), l = $('startLang').getBoundingClientRect(), r = document.querySelector('.metaRow').getBoundingClientRect(); return { noScroll: st.scrollHeight <= st.clientHeight + 1 && document.documentElement.scrollHeight <= innerHeight + 1, pillIn: p.left >= 0 && p.right <= innerWidth, pillOverlap: p.right > l.left && p.left < l.right && p.bottom > l.top && p.top < l.bottom, rowIn: r.left >= 0 && r.right <= innerWidth && r.bottom <= innerHeight, nx: $('nextUnlock').textContent, nxFits: $('nextUnlock').getBoundingClientRect().right <= p.right + 1 && $('nextUnlock').getBoundingClientRect().left >= p.left - 1, btns: [...document.querySelectorAll('.metaBtn')].map(b => b.querySelector('[data-i18n]').textContent.trim()) }; })()"

async def frames(page, n=1):
    for _ in range(n): await page.evaluate(FRAMES)

async def new_page(b, mobile=False, he=False, init='', gfx=None):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');") + (f"window.__graspGfx = {gfx};" if gfx else '') + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(700)
    return ctx, page, errs

async def play(page):
    await page.click('#mouseBtn'); await page.click('.modes button[data-mode=strike]'); await page.click('#advEndless')
    await page.wait_for_function("gameMode === 'strike' && __grasp.strike.walls.length", timeout=8000)
    await page.evaluate(SFX_JS); await page.mouse.move(640, 760)

async def end_run(page):
    await page.evaluate(f"{S}.lives = 1; cursor.history.length = 0; {S}.chest = null; {S}.setBallZ(-__grasp.CONFIG.STRIKE_HIT_Z * 0.7, innerWidth * 0.5, innerHeight * 0.1)")
    await page.wait_for_function(f"{S}.over", timeout=4000)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ---- the ladder: one unlock per player level 1..20; setPlayerLevel(n) earns exactly the ones up to n ----
        ctx, page, errs = await new_page(b)
        lad = await page.evaluate("__grasp.road.ladder.map(r => [r.id, r.lv])")
        check('the road: 20 unlocks over player levels 1-20 (the cow from the start), in the designed order', [tuple(x) for x in lad] == LADDER, lad)
        fresh = await page.evaluate(f"({{ got: {P}.road.got, level: {P}.level, next: __grasp.road.next.id, nx: $('nextUnlock').textContent }})")
        check('a fresh profile: level 1 with brick walls + the ball only; next: glass walls (180 XP to go, on the pill)', fresh['got'] == ['brick', 'cow'] and fresh['level'] == 1 and fresh['next'] == 'glass' and fresh['nx'] == '180 XP to: Glass walls', fresh)
        per = {}
        for n in (1, 2, 3, 4, 5, 8, 10, 12, 15, 16, 19, 20):
            per[n] = await page.evaluate(f"(() => {{ __grasp.setPlayerLevel({n}); return {{ got: __grasp.road.ladder.filter(r => __grasp.road.unlocked(r.id)).map(r => r.id), level: {P}.level, xp: {P}.xp, x0: __grasp.xpForLevel({n}), cards: {P}.road.cards.length, fresh: {P}.road.fresh.length, lv: __grasp.levelOf({P}.xp) }}; }})()")
        check('setPlayerLevel(n): level n at its xp, exactly the ladder items with lv <= n unlocked (no cards, no spotlights)', all(per[n]['got'] == [i for i, lv in LADDER if lv <= n] and per[n]['level'] == n and per[n]['lv'] == n and per[n]['xp'] == per[n]['x0'] and not per[n]['cards'] and not per[n]['fresh'] for n in per), {n: per[n]['got'][-1] for n in per})
        sk = await page.evaluate(f"({{ lava: {P}.unlocked.includes('ball_lava') && {P}.unlocked.includes('trail_lava'), legend: {P}.unlocked.includes('hand_legend'), items: __grasp.collection.items.filter(i => ['ball_lava', 'trail_lava', 'hand_legend'].includes(i.id)).map(i => [i.id, i.level]) }})")
        check('level 19: the Volcano skins (lava ball + lava trail), level 20: the Legend hand, in the collection', sk['lava'] and sk['legend'] and sorted(map(tuple, sk['items'])) == [('ball_lava', 19), ('hand_legend', 20), ('trail_lava', 19)], sk)
        perks = await page.evaluate(f"[4, 10, 15].map(n => {{ __grasp.setPlayerLevel(n); return {S}.pacing.perks; }})")
        check('perks unlock in three packs: Lv4 Wider Hands / Thick Skin / Slow Start, Lv10 + Heavy Ball / Sticky Magnet / Lucky, Lv15 + Spark Trail / Coin Magnet',
              perks == [['wide', 'skin', 'slow'], ['wide', 'heavy', 'magnet', 'skin', 'lucky', 'slow'], ['wide', 'heavy', 'magnet', 'skin', 'lucky', 'spark', 'slow', 'coins']], perks)
        xpc = await page.evaluate("[1, 2, 3, 4, 5, 6, 10, 20].map(n => __grasp.xpForLevel(n))")
        lv = await page.evaluate("[0, 179, 180, 379, 380, 599, 600, 840, 6839, 6840].map(x => __grasp.levelOf(x))")
        check('XP curve: level L begins at 10 (L-1)^2 + 170 (L-1) (0, 180, 380, 600, 840, 1100 ...); levelOf inverts it exactly', xpc == [0, 180, 380, 600, 840, 1100, 2340, 6840] and lv == [1, 1, 2, 2, 3, 3, 4, 5, 19, 20], [xpc, lv])
        check('ladder: no page errors', not errs, errs); await ctx.close()

        # an existing player (a profile from before the road, on the old XP curve): same level, everything that level earns, no cards
        ctx, page, errs = await new_page(b, init="if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded', '1'); localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, coins: 40, xp: 1300, unlocked: ['ball_classic', 'hand_classic', 'blade_steel', 'trail_none', 'ball_planet', 'trail_rainbow', 'hand_cat'] })); }")
        ex = await page.evaluate(f"({{ level: {P}.level, xp: {P}.xp, got: {P}.road.got, cards: {P}.road.cards, fresh: {P}.road.fresh, worlds: {P}.worlds, nx: $('nextUnlock').textContent, card: __grasp.road.card }})")
        check('an existing level-6 profile (old curve, 1300 xp): still level 6 (its xp moved onto the new curve), the six level unlocks already its own, no NEW cards',
              ex['level'] == 6 and 1100 <= ex['xp'] < 1380 and ex['got'] == [i for i, l in LADDER if l <= 6] and not ex['cards'] and not ex['fresh'] and ex['card'] is None and ex['worlds'] == {'unlocked': 1, 'last': 1}, ex)
        await page.reload(); await page.wait_for_timeout(500)
        check('...and the converted profile is stable across a reload', await page.evaluate(f"{P}.level") == 6 and await page.evaluate(f"{P}.xp") == ex['xp'])
        check('existing profile: no page errors', not errs, errs); await ctx.close()

        # ---- the gate: a low-level player's run never brings what is still locked, even at high run levels ----
        ctx, page, errs = await new_page(b)
        await play(page); await page.evaluate(PARK)
        g1 = await page.evaluate(GATE_SIM + "(1, 12)")
        check('a level-1 player at run level 12: 300 walls all brick, no power-up bricks, the cow only, straight serves, no perk offers', list(g1['kinds']) == ['brick'] and not g1['pus'] and list(g1['guests']) == ['cow'] and g1['curved'] == 0 and not g1['offers'] and g1['puRate'] == 0 and g1['guestsOn'], g1)
        g3 = await page.evaluate(GATE_SIM + "(3, 12)")
        check('a level-3 player at run level 12: only brick + glass walls and the Big ball power-up; the cow only, no curves, no perks', set(g3['kinds']) == {'brick', 'glass'} and set(g3['pus']) == {'big'} and list(g3['guests']) == ['cow'] and g3['curved'] == 0 and not g3['offers'], g3)
        g6 = await page.evaluate(GATE_SIM + "(3, 6)")
        check('the example: a level-6 run of a level-3 player has only brick + glass walls and Big ball', set(g6['kinds']) == {'brick', 'glass'} and set(g6['pus']) == {'big'}, g6)
        g8 = await page.evaluate(GATE_SIM + "(8, 12)")
        check('a level-8 player at run level 12: brick / glass / steel walls, Big ball + Slow-mo, the cow and the monkey, curving (never wobbling) serves, the first perk pack only',
              set(g8['kinds']) == {'brick', 'glass', 'steel'} and set(g8['pus']) == {'big', 'slow'} and set(g8['guests']) == {'cow', 'monkey'} and g8['guests']['cow'] >= 12 and g8['curved'] == g8['plain'] and g8['waves'] == 0 and g8['offers'] == ['skin', 'slow', 'wide'], g8)
        g20 = await page.evaluate(GATE_SIM + "(20, 12)")
        check('a level-20 player at run level 12: every wall kind, every power-up, both animals, the S-wobble, every perk', set(g20['kinds']) == {'brick', 'glass', 'steel', 'holed', 'moving', 'tnt'} and set(g20['pus']) == {'multi', 'big', 'slow', 'fire', 'life'} and set(g20['guests']) == {'cow', 'monkey'} and g20['waves'] == g20['plain'] and len(g20['offers']) == 8, g20)
        g20b = await page.evaluate(GATE_SIM + "(20, 1)")
        check('...but the run arc still holds: at run level 1 even a level-20 player gets brick walls only, no power-ups, no animals', list(g20b['kinds']) == ['brick'] and not g20b['pus'] and not g20b['guests'], g20b)
        # in play: completing level 5 as a level-3 player brings no perk pick (none unlocked); the level-up's new kind is skipped when locked
        await page.evaluate(f"__grasp.setPlayerLevel(3); {S}.setLevel(5); {PARK}")
        await page.evaluate(f"{S}.setCleared({S}.cleared + 7)"); await frames(page, 2)
        pk = await page.evaluate(f"({{ level: {S}.level, perkAt: {S}.perkAt, offer: !!{S}.perkOffer, next: {S}.walls.map(w => w.kind) }})")
        check('a level-3 player completing run level 5: no perk pick (no perk unlocked yet); level 6 brings no holed wall', pk['level'] == 6 and pk['perkAt'] == 0 and not pk['offer'] and 'holed' not in pk['next'], pk)
        check('gate: no page errors', not errs, errs); await ctx.close()

        # ---- a level-up at the end of a run: the NEW UNLOCKED card over the end card; the next run's spotlight ('New! Glass walls') ----
        ctx, page, errs = await new_page(b)
        await page.evaluate("__grasp.addXp(170)")
        await play(page); await page.evaluate(PARK)
        await page.evaluate(f"{S}.setCleared({S}.cleared + 5)"); await frames(page, 2)  # 5 walls, run level 2
        st = await page.evaluate(f"({{ walls: {S}.cleared - {S}.cleared0, levels: {S}.level - 1, bosses: {S}.bosses, xp: {S}.runXp, xp0: {P}.xp }})")
        await end_run(page)
        await page.wait_for_function("__grasp.road.card === 'glass'", timeout=6000)
        nc = await page.evaluate(f"""(() => {{ const P = $('newCard'), r = P.querySelector('.sheet').getBoundingClientRect(), cv = P.querySelector('.nuArt canvas'), d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data; let lit = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 40) lit++;
          return {{ shown: !P.hidden, kick: P.querySelector('.nuKick').textContent, name: $('nuName').textContent, line: P.querySelector('.nuLine').textContent, grip: !!P.querySelector('.nuGrip, .bub'), art: lit / (d.length / 4), inside: r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight,
            xp: {P}.xp, level: {P}.level, fresh: {P}.road.fresh.slice(), xpBox: {S}.ui.xpBox && {S}.ui.xpBox.n, sfx: __sfx.slice(-12) }}; }})()""")
        check('the run earned runXp(walls, levels, bosses) = 20 + 4 x 5 + 10 x 1 = 50 XP; the end card shows +50 XP', st['xp'] == 50 and nc['xp'] - st['xp0'] == 50 and nc['xpBox'] == 50, [st, nc['xp'], nc['xpBox']])
        check('level 2 reached: the NEW UNLOCKED card over the end card (Glass walls, its art, a short line, no Grippy hand / bubble), inside the viewport, an unlock sound',
              nc['shown'] and nc['kick'] == 'NEW UNLOCKED!' and nc['name'] == 'Glass walls' and nc['line'] and not nc['grip'] and nc['art'] > 0.15 and nc['inside'] and nc['level'] == 2 and 'unlock' in nc['sfx'], nc)
        await page.screenshot(path='tests/out/road_newcard_endcard.png')
        await page.mouse.move(640, 300); await page.mouse.move(900, 600, steps=3); await page.wait_for_timeout(300)
        check('while the card is up, a wave does not restart the round', await page.evaluate(f"{S}.over"))
        await page.click('#nuOk'); await page.wait_for_timeout(450)
        cl = await page.evaluate(f"({{ shown: !$('newCard').hidden, cards: {P}.road.cards, fresh: {P}.road.fresh }})")
        check('"Awesome!" closes it; glass stays marked fresh for its first appearance in a run', not cl['shown'] and cl['cards'] == [] and cl['fresh'] == ['glass'], cl)
        await page.evaluate("endCardAction('again', performance.now())"); await page.wait_for_timeout(300)
        await page.evaluate(f"{PARK}; __grasp.grippy.cool(); {S}.setLevel(3)")  # run level 3 brings glass (the first wall of the level is it)
        await page.wait_for_function(f"{S}.lastSpot && {S}.ui.spot", timeout=4000)
        sp = await page.evaluate(f"({{ last: {S}.lastSpot, ui: {S}.ui.spot, fresh: {P}.road.fresh, kinds: {S}.walls.map(w => w.kind) }})")
        check("next run: the first glass wall gets the spotlight 'New! Glass walls' (a big tag under the HUD), and glass is no longer fresh",
              sp['last']['id'] == 'glass' and not sp['last']['preview'] and sp['ui']['text'] == 'New! Glass walls' and sp['ui']['w'] > 150 and 0 <= sp['ui']['x'] and sp['ui']['x'] + sp['ui']['w'] <= 1280 and sp['fresh'] == [], sp)
        await page.screenshot(path='tests/out/road_spotlight.png')
        await page.evaluate("resetStrike(performance.now())"); await page.evaluate(f"{PARK}; {S}.setLevel(3)"); await page.wait_for_timeout(600)
        check('the run after that: no spotlight again for glass', await page.evaluate(f"{S}.lastSpot") is None)
        check('NEW card + spotlight: no page errors', not errs, errs); await ctx.close()

        # ---- the Road panel and the pill on a phone, EN and HE: colour / silhouette / hidden rows that fit; the card on the start screen ----
        for he in (False, True):
            tag = 'phone ' + ('he' if he else 'en')
            ctx, page, errs = await new_page(b, True, he)
            await page.evaluate("__grasp.setPlayerLevel(5)"); await page.wait_for_timeout(200)
            f = await page.evaluate(START_FIT)
            check(tag + ': the pill shows the XP to the next unlock (260 XP to Slow-mo) inside it; the start screen still fits with the Road button',
                  f['noScroll'] and f['pillIn'] and not f['pillOverlap'] and f['rowIn'] and f['nxFits'] and f['nx'] == ('עוד 260 XP: הילוך איטי' if he else '260 XP to: Slow-mo') and f['btns'] == (['משימות', 'הדרך', 'חנות'] if he else ['Missions', 'Road', 'Shop']), f)
            await page.screenshot(path='tests/out/road_' + tag.replace(' ', '_') + '_start.png')
            # the shop: a labelled button (bag icon, 'Shop' + the coin balance) even on a phone, a red dot once something new is affordable
            SHOP = "(() => { const b = $('collectionBtn'), l = b.querySelector('[data-i18n]').getBoundingClientRect(), r = b.getBoundingClientRect(), row = document.querySelector('.metaRow').getBoundingClientRect(); return { label: b.querySelector('[data-i18n]').textContent, lw: l.width, sc: b.querySelector('.sc').textContent, dot: !b.querySelector('.dot').hidden, inRow: r.left >= row.left - 0.5 && r.right <= row.right + 0.5, labelIn: l.left >= r.left && l.right <= r.right, title: $('collectionTitle').textContent }; })()"
            sh = await page.evaluate(SHOP)
            check(tag + ': the Shop button is labelled on the phone (' + sh['label'] + ' ' + sh['sc'] + '), inside the row; no dot with 0 coins', sh['label'] == ('חנות' if he else 'Shop') and sh['lw'] > 20 and sh['labelIn'] and sh['sc'] == '0' and sh['inRow'] and not sh['dot'] and sh['title'] == sh['label'], sh)
            await page.evaluate("__grasp.addCoins(150)"); await page.wait_for_timeout(100)
            sh2 = await page.evaluate(SHOP); f2 = await page.evaluate(START_FIT)
            check(tag + ': 150 coins: the balance on the button, a red dot (something new is affordable), the start screen still fits', sh2['sc'] == '150' and sh2['dot'] and f2['noScroll'] and f2['rowIn'], [sh2, f2['noScroll']])
            await page.screenshot(path='tests/out/road_' + tag.replace(' ', '_') + '_shop_dot.png')
            await page.evaluate("__grasp.addCoins(-150)"); await page.wait_for_timeout(50)
            await page.tap('#roadBtn'); await page.wait_for_timeout(400)
            rp = await page.evaluate("""(() => { const ov = $('road'), sh = ov.querySelector('.sheet'), r = sh.getBoundingClientRect(), x = sh.querySelector('.xBtn').getBoundingClientRect(), h2 = sh.querySelector('h2').getBoundingClientRect();
              const px = (cv) => { const d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data, c = new Set(); for (let i = 0; i < d.length; i += 4) if (d[i + 3] > 200) c.add(d[i] >> 3 << 10 | d[i + 1] >> 3 << 5 | d[i + 2] >> 3); return c.size; };
              return { hidden: ov.hidden, inside: r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight, scrolls: sh.scrollHeight > sh.clientHeight + 1, bodyScroll: document.documentElement.scrollHeight > innerHeight + 1, xEnd: x.left > h2.left,
                rows: [...document.querySelectorAll('#rlist .rrow')].map(li => { const b = li.getBoundingClientRect(), nm = li.querySelector('.nm'), cv = li.querySelector('canvas'), lv = li.querySelector('.lv');
                  return { id: li.dataset.id, st: li.dataset.st, inSheet: b.left >= r.left - 0.5 && b.right <= r.right + 0.5, nmFits: nm.scrollWidth <= nm.clientWidth + 1, lvIn: lv.getBoundingClientRect().right <= b.right + 0.5 && lv.getBoundingClientRect().left >= b.left - 0.5, name: nm.firstChild ? nm.firstChild.textContent : '', lv: lv.textContent, cols: cv ? px(cv) : 0, q: li.querySelector('.q') ? li.querySelector('.q').textContent : null }; }) }; })()""")
            sts = [r['st'] for r in rp['rows']]
            check(tag + ': the Road panel: levels 1-5 unlocked (in colour, the cow too), the next 3 (6-8) as silhouettes, the rest hidden', sts == ['got'] * 6 + ['next'] * 3 + ['hide'] * 11, sts)
            got, nxt, hid = [r for r in rp['rows'] if r['st'] == 'got'], [r for r in rp['rows'] if r['st'] == 'next'], [r for r in rp['rows'] if r['st'] == 'hide']
            check(tag + ': unlocked rows show the art in colour (many colours) and their level; silhouettes are one flat colour (edge rounding aside) with "Lv 6/7/8"; hidden rows are just "?"',
                  all(r['cols'] >= 6 for r in got) and all(1 <= r['cols'] <= 3 for r in nxt) and [r['lv'] for r in nxt] == (['רמה 6', 'רמה 7', 'רמה 8'] if he else ['Lv 6', 'Lv 7', 'Lv 8']) and all(r['q'] == '?' and r['name'] == '???' and r['lv'] == '?' for r in hid), [[r['cols'], r['lv']] for r in got + nxt])
            check(tag + ': the panel fits the phone (scrolls inside, no page scroll), every row and its name inside the sheet, close button at the inline end',
                  not rp['hidden'] and rp['inside'] and rp['scrolls'] and not rp['bodyScroll'] and rp['xEnd'] == (not he) and all(r['inSheet'] and r['nmFits'] and r['lvIn'] for r in rp['rows']), [r for r in rp['rows'] if not (r['inSheet'] and r['nmFits'] and r['lvIn'])])
            heb = [r['name'] for r in got + nxt if not re.search('[֐-׿]', r['name'])] if he else [r['name'] for r in got + nxt if not re.match('[A-Z]', r['name'])]
            check(tag + ': names translated', not heb, heb)
            await page.screenshot(path='tests/out/road_' + tag.replace(' ', '_') + '_panel.png')
            await page.keyboard.press('Escape'); await page.wait_for_timeout(100)
            check(tag + ': Escape closes the panel', await page.evaluate("$('road').hidden"))
            await page.evaluate("__grasp.addXp(300)"); await page.wait_for_timeout(500)  # 840 + 260 -> level 6: Slow-mo
            cd = await page.evaluate("(() => { const P = $('newCard'), r = P.querySelector('.sheet').getBoundingClientRect(), ok = $('nuOk').getBoundingClientRect(); return { shown: !P.hidden, name: $('nuName').textContent, kick: P.querySelector('.nuKick').textContent, inside: r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight && ok.bottom <= r.bottom }; })()")
            check(tag + ': a level-up on the start screen: the NEW UNLOCKED card (Slow-mo) fits the phone', cd['shown'] and cd['name'] == ('הילוך איטי' if he else 'Slow-mo') and cd['kick'] == ('נפתח משהו חדש!' if he else 'NEW UNLOCKED!') and cd['inside'], cd)
            await page.screenshot(path='tests/out/road_' + tag.replace(' ', '_') + '_newcard.png')
            await page.tap('#nuOk'); await page.wait_for_timeout(450)
            check(tag + ': closed with a tap', await page.evaluate("$('newCard').hidden"))
            await page.evaluate("__grasp.worlds.unlocked = 3; __grasp.setGameMode('strike')"); await page.wait_for_timeout(200)
            await page.evaluate(START_MOUSE); await page.wait_for_timeout(400)
            wm = await page.evaluate("(() => { const ov = $('worldMap'), r = ov.querySelector('.sheet').getBoundingClientRect(), n = [...ov.querySelectorAll('.wnode')].map(b => { const q = b.getBoundingClientRect(); return { w: +b.dataset.world, locked: b.classList.contains('locked'), cur: b.classList.contains('cur'), x: q.left + q.width / 2, inside: q.left >= r.left && q.right <= r.right, name: b.querySelector('.nm').textContent }; }); return { shown: !ov.hidden, inside: r.left >= 0 && r.right <= innerWidth && r.top >= 0 && r.bottom <= innerHeight, n }; })()")
            xs = [q['x'] for q in wm['n']]
            check(tag + ': with world 3 open, Strike start shows the world map first: 5 nodes on a path, 1-3 open (1 the current one, pulsing), 4-5 grey and locked, all inside; RTL runs right to left',
                  wm['shown'] and wm['inside'] and [q['locked'] for q in wm['n']] == [False] * 3 + [True] * 2 and [q['cur'] for q in wm['n']] == [True] + [False] * 4 and all(q['inside'] for q in wm['n']) and (xs == sorted(xs, reverse=True) if he else xs == sorted(xs)), wm)
            await page.screenshot(path='tests/out/road_' + tag.replace(' ', '_') + '_worldmap.png')
            check(tag + ': no page errors', not errs, errs); await ctx.close()

        # ---- the end card's Shop button (beside Home, only while something new is affordable); the collection hooks still work ----
        ctx, page, errs = await new_page(b)
        await play(page); await page.evaluate(PARK); await end_run(page); await page.wait_for_function(f"{S}.ui.buttons", timeout=4000); await frames(page, 2)
        nb = await page.evaluate(f"Object.keys({S}.ui.buttons)")
        check('end card with too few coins: no Shop button', 'shop' not in nb, nb)
        await page.evaluate(f"{P}.coins = 150; endCardAction('again', performance.now())"); await page.evaluate(PARK); await end_run(page)
        await page.wait_for_function(f"{S}.ui.buttons && {S}.ui.buttons.shop", timeout=4000); await frames(page, 2)
        bt = await page.evaluate(f"({{ b: {S}.ui.buttons, card: {S}.ui.card }})"); sb, hb, cd = bt['b']['shop'], bt['b']['home'], bt['card']
        check('end card with an affordable item: a Shop button beside Home, inside the card, as tall as it', sb['y'] == hb['y'] and sb['h'] == hb['h'] and sb['x'] >= cd['x'] and sb['x'] + sb['w'] <= cd['x'] + cd['w'] and (sb['x'] >= hb['x'] + hb['w'] or sb['x'] + sb['w'] <= hb['x']), bt)
        await page.screenshot(path='tests/out/road_endcard_shop.png')
        await page.wait_for_timeout(600); await page.mouse.click(sb['x'] + sb['w'] / 2, sb['y'] + sb['h'] / 2); await page.wait_for_timeout(400)
        st = await page.evaluate("({ mode, start: !$('start').hidden, shop: !$('collection').hidden, title: $('collectionTitle').textContent })")
        check('tapping it: the start screen with the Shop open', st == {'mode': 'none', 'start': True, 'shop': True, 'title': 'Shop'}, st)
        ok = await page.evaluate("__grasp.collection.buy('ball_beach') && __grasp.collection.equip('ball_beach') && __grasp.collection.state(__grasp.collection.items.find(i => i.id === 'ball_beach')) === 'equipped'")
        check('__grasp.collection hooks still work (buy, equip, state)', ok)
        check('shop: no page errors', not errs, errs); await ctx.close()

        # ---- worlds: the boss closes world 1 (level 6); beating it unlocks world 2 and the map starts there ----
        ctx, page, errs = await new_page(b)
        await page.evaluate("__grasp.setPlayerLevel(20)")
        await play(page); await page.evaluate(f"{PARK}; __grasp.grippy.on = false")
        early = await page.evaluate(f"(() => {{ const s = {S}, out = []; for (let n = 1; n <= 35; n++) {{ s.setCleared(n); out.push([n, s.level, !!s.boss]); }} s.perkAt = 0; s.perkOffer = null; return {{ out, next: s.next, level: s.level, progress: s.progress, goal: s.goal, world: s.world }}; }})()")
        check('walls 1-35 (levels 1-5 and the first six of level 6): never a boss; the NEXT card says the boss comes after the final wall', not any(x[2] for x in early['out']) and early['level'] == 6 and early['progress'] == 6 and early['next'] == 'boss' and early['world'] == 1, early['out'][-3:] + [early['next']])
        await page.evaluate(f"{PARK}; {S}.setCleared(36)"); await frames(page, 2)
        bo = await page.evaluate(f"({{ boss: {S}.boss && {{ n: {S}.boss.n, gate: {S}.boss.gate, hp: {S}.boss.hp }}, level: {S}.level, progress: {S}.progress, gate: {S}.gate }})")
        check("wall 36 (level 6's last): the world's boss (#1) comes; the level holds at 6 (bar full) until it is beaten", bo['boss'] and bo['boss']['n'] == 1 and bo['boss']['gate'] and bo['level'] == 6 and bo['progress'] == 7 and bo['gate'] == 6, bo)
        await page.evaluate(f"{S}.setCleared(37); {S}.perkAt = 0; {S}.perkOffer = null"); await frames(page, 1)
        check('no level-up past the gate while the boss lives', await page.evaluate(f"{S}.level") == 6)
        await page.evaluate(f"(() => {{ const s = {S}; while (s.boss) s.bossHit('super'); }})()"); await frames(page, 2)
        bd = await page.evaluate(f"({{ level: {S}.level, world: {S}.world, gate: {S}.gate, unlocked: __grasp.worlds.unlocked, worldUp: {S}.worldUp, chest: !!{S}.chest, toasts: {TOASTS}, banner: {S}.ui.levelBanner && {S}.ui.levelBanner.world, rel: {S}.releaseUntil > performance.now() }})")
        check('boss #1 beaten: level 7 = world 2 (the release beat, a banner naming the world), world 2 unlocked and saved, a toast, the chest drops',
              bd['level'] == 7 and bd['world'] == 2 and bd['gate'] == 12 and bd['unlocked'] == 2 and bd['worldUp'] == 2 and bd['chest'] and bd['banner'] == 2 and bd['rel'] and any('World 2 unlocked: Glass Garden!' in x for x in bd['toasts']), bd)
        await page.wait_for_function(f"{S}.chest && {S}.chest.state === 'ready' && {S}.ui.chest", timeout=4000)
        ch = await page.evaluate(f"({{ box: {S}.ui.chest, serveIn: {S}.serveAt - performance.now(), balls: {S}.balls.length, coins: {P}.coins, tickets: {P}.tickets, unl: {P}.unlocked.length, grippy: __sfx.includes('whoosh') }})")
        await page.screenshot(path='tests/out/road_chest.png')
        check('the chest waits on the screen (inside it), the run holds (no ball, no serve) until it is opened', ch['box']['x'] > 0 and ch['box']['x'] + ch['box']['w'] < 1280 and ch['box']['y'] > 0 and ch['box']['y'] + ch['box']['h'] < 800 and ch['balls'] == 0 and ch['serveIn'] > 500, ch)
        await page.mouse.click(ch['box']['x'] + ch['box']['w'] / 2, ch['box']['y'] + ch['box']['h'] / 2); await frames(page, 1)
        op = await page.evaluate(f"({{ state: {S}.chest && {S}.chest.state, prize: {S}.lastChest, coins: {P}.coins, tickets: {P}.tickets, unl: {P}.unlocked.slice(), parts: particles.length, sfx: __sfx.slice(-6) }})")
        pz = op['prize'] or {}
        applied = (pz.get('kind') == 'coins' and 25 <= pz.get('n', 0) <= 60 and op['coins'] == ch['coins'] + pz['n']) or (pz.get('kind') == 'skin' and pz.get('item') in op['unl'] and len(op['unl']) == ch['unl'] + 1) or (pz.get('kind') == 'ticket' and op['tickets'] == ch['tickets'] + 1)
        check('a tap on the chest opens it: lid pops with confetti and a sound; the prize (from the table) is applied', op['state'] == 'open' and applied and op['parts'] > 40 and 'unlock' in op['sfx'], op)
        await page.wait_for_timeout(900); await page.screenshot(path='tests/out/road_chest_open.png')
        await page.wait_for_function(f"!{S}.chest", timeout=5000); await page.wait_for_function(f"{S}.balls.length > 0", timeout=6000)
        check('after the prize: the chest goes and play resumes in world 2 (a serve)', await page.evaluate(f"{S}.world") == 2)
        await page.evaluate(f"{P}.tickets = 0"); await menu_click(page, '#homeBtn'); await page.wait_for_timeout(300)
        await page.click('#mouseBtn'); await page.click('.modes button[data-mode=strike]'); await page.click('#advEndless'); await page.wait_for_timeout(300)
        mp = await page.evaluate("({ shown: !$('worldMap').hidden, n: [...document.querySelectorAll('#wmap .wnode')].map(b => [b.classList.contains('locked'), b.classList.contains('cur')]), mode })")
        check('home, Strike, Play: the world map first (world 2 open, 3-5 locked), no game yet', mp['shown'] and [x[0] for x in mp['n']] == [False, False, True, True, True] and mp['mode'] == 'none', mp)
        await page.click('#wmap .wnode[data-world="3"]', force=True); await page.wait_for_timeout(200)
        check('a locked world: a toast, the map stays', not await page.evaluate("$('worldMap').hidden") and any('Beat the boss of world 2 first' in x for x in await page.evaluate(TOASTS)))
        await page.click('#wmap .wnode[data-world="2"]')
        await page.wait_for_function("mode === 'mouse' && gameMode === 'strike' && __grasp.strike.walls.length", timeout=8000)
        w2 = await page.evaluate(f"({{ level: {S}.level, world: {S}.world, score: {S}.score, perks: {S}.perks, lives: {S}.lives, maxLives: {S}.maxLives, base: sd('STRIKE_LIVES'), cleared0: {S}.cleared0, c7: clearedAtLevel(7), last: __grasp.worlds.last, gate: {S}.gate, banner: {S}.ui.levelBanner }})")
        check('world 2 picked: the run starts at level 7 (world 2) with base stats (score 0, no perks, base lives); the choice is remembered', w2['level'] == 7 and w2['world'] == 2 and w2['score'] == 0 and w2['perks'] == {} and w2['lives'] == w2['base'] == w2['maxLives'] and w2['cleared0'] == w2['c7'] and w2['last'] == 2 and w2['gate'] == 12 and w2['banner']['world'] == 2, w2)
        await page.evaluate(f"{PARK}; {S}.setCleared(clearedAtLevel(13))"); await frames(page, 1)
        check("world 2's boss (#2) closes it at level 12", await page.evaluate(f"{S}.boss && {S}.boss.n === 2 && {S}.boss.gate && {S}.level === 12"))
        await page.evaluate(f"{S}.boss = null; endCardAction('again', performance.now())"); await page.wait_for_timeout(100)
        check('Play again restarts in the same world (level 7)', await page.evaluate(f"{S}.level") == 7)
        # the world palettes: a clearly different corridor in each world (2D pixel probes)
        await page.evaluate("__grasp.worlds.unlocked = 5")
        pal = {}
        for n in range(1, 6):
            await page.evaluate(f"__grasp.worlds.start({n}); {PARK}; {S}.walls.length = 0"); await frames(page, 3)
            pal[n] = await page.evaluate(f"({{ world: {S}.world, floor: {PIX}(1150, 700), wall: {PIX}(6, 420), ceil: {PIX}(250, 30) }})")
        print('INFO 2D palettes:', pal)
        d = lambda a, b: sum(abs(x - y) for x, y in zip(a, b))
        check('2D: each world draws its own corridor palette (floor, side wall and ceiling pixels differ between every pair of worlds)', [pal[n]['world'] for n in pal] == [1, 2, 3, 4, 5] and all(d(pal[i][k], pal[j][k]) > 12 for i in pal for j in pal if i < j for k in ('floor', 'wall')), pal)
        check('2D world tints: Glass Garden teal-green, Steel Factory grey, Jungle green, Volcano red', pal[2]['floor'][1] > pal[2]['floor'][0] and pal[4]['floor'][1] > pal[4]['floor'][0] + 8 and pal[4]['floor'][1] > pal[4]['floor'][2] and pal[5]['floor'][0] > pal[5]['floor'][2] + 15 and max(pal[3]['floor']) - min(pal[3]['floor']) < 40, pal)
        await page.screenshot(path='tests/out/road_world5.png')
        check('worlds: no page errors', not errs, errs); await ctx.close()

        # 3D: the WebGL corridor takes on each world's palette too
        ctx, page, errs = await new_page(b, gfx="{ pr: 0.25, shadows: false, auto: false }")
        await page.evaluate("__grasp.setPlayerLevel(20); __grasp.worlds.unlocked = 5")
        await page.click('#mouseBtn'); await page.click('.modes button[data-mode=strike]'); await page.click('#advEndless'); await page.wait_for_timeout(300)
        await page.click('#wmap .wnode[data-world="1"]'); await page.wait_for_function("gameMode === 'strike' && mode === 'mouse'", timeout=8000)
        g = await page.evaluate("__grasp.setGfx('3d')")
        await page.wait_for_function(f"{S}.gfx === '3d'", timeout=20000)
        p3 = {}
        for n in range(1, 6):
            await page.evaluate(f"__grasp.worlds.start({n}); {PARK}; {S}.walls.length = 0"); await frames(page, 3)
            p3[n] = await page.evaluate(f"({{ world: {S}.world, floor: {S}.pixel3d(640, 770), wall: {S}.pixel3d(30, 420) }})")
        print('INFO 3D palettes:', p3)
        check('3D (setGfx): each world gives the WebGL corridor its own palette (floor and wall pixels differ between every pair)', g == '3d' and all(d(p3[i][k], p3[j][k]) > 8 for i in p3 for j in p3 if i < j for k in ('floor', 'wall')), p3)
        await page.screenshot(path='tests/out/road_world5_3d.png')
        check('3D worlds: no page errors', not errs, errs); await ctx.close()

        # ---- the chest's prize table over many seeded opens; auto-open; the Golden ticket ----
        ctx, page, errs = await new_page(b)
        await play(page); await page.evaluate(PARK)
        dist = await page.evaluate(f"""(() => {{ const s = {S}, n = 4000, c = {{ coins: 0, skin: 0, ticket: 0 }}, items = new Set(); let lo = 1e9, hi = 0, bad = 0;
          for (let i = 1; i <= n; i++) {{ const p = s.chestPrize(i * 7919); c[p.kind]++; if (p.kind === 'coins') {{ lo = Math.min(lo, p.n); hi = Math.max(hi, p.n); }} if (p.kind === 'skin') {{ items.add(p.item); const it = __grasp.collection.items.find(q => q.id === p.item); if (!it || it.level || {P}.unlocked.includes(p.item)) bad++; }} }}
          const all = __grasp.collection.items.filter(i => !i.level).map(i => i.id); const keep = {P}.unlocked.slice(); {P}.unlocked = [...new Set(keep.concat(all))]; const c2 = {{ coins: 0, skin: 0, ticket: 0 }}; for (let i = 1; i <= 2000; i++) c2[s.chestPrize(i * 104729).kind]++; {P}.unlocked = keep;
          return {{ share: {{ coins: c.coins / n, skin: c.skin / n, ticket: c.ticket / n }}, lo, hi, bad, items: items.size, owned: c2, same: JSON.stringify(s.chestPrize(42)) === JSON.stringify(s.chestPrize(42)) }}; }})()""")
        print('INFO chest prizes:', dist)
        sh = dist['share']
        check('4000 seeded chest opens: mostly coins (~70%), sometimes a skin (~22%), rarely a Golden ticket (~8%); coins 25-60 (the economy); skins only ones not owned yet',
              0.64 <= sh['coins'] <= 0.76 and 0.17 <= sh['skin'] <= 0.27 and 0.05 <= sh['ticket'] <= 0.11 and 25 <= dist['lo'] <= 28 and 57 <= dist['hi'] <= 60 and dist['bad'] == 0 and dist['items'] >= 8 and dist['same'], dist)
        check('with every skin owned, a skin roll pays coins instead', dist['owned']['skin'] == 0 and dist['owned']['coins'] > 1700, dist['owned'])
        await page.evaluate(f"window.__sr0 = strikeRand; strikeRand = (ch) => ch === 'chest' ? 0.5 : __sr0(ch); {S}.chestAutoMs = 500; {S}.dropChest()")  # (a coins prize: a random 8% ticket here would upset the ticket count below)
        await page.wait_for_function(f"{S}.chest && {S}.chest.state === 'open'", timeout=4000); await page.evaluate("strikeRand = __sr0")
        check('no tap: the chest opens by itself after its wait (camera-friendly)', await page.evaluate(f"!!{S}.lastChest"))
        await page.wait_for_function(f"!{S}.chest", timeout=5000)
        await page.evaluate(f"(() => {{ window.__sr = strikeRand; strikeRand = (ch) => ch === 'chest' ? 0.01 : __sr(ch); {S}.chestAutoMs = null; {S}.dropChest().open(); strikeRand = __sr; }})()")
        tk = await page.evaluate(f"({{ prize: {S}.lastChest, tickets: {P}.tickets, toasts: {TOASTS} }})")
        check('a Golden ticket from the chest: saved in the profile, a toast', tk['prize'] == {'kind': 'ticket'} and tk['tickets'] == 1 and any('Golden ticket' in x for x in tk['toasts']), tk)
        await page.wait_for_timeout(500); await page.screenshot(path='tests/out/road_ticket.png')
        await page.evaluate(f"{S}.chest = null; resetStrike(performance.now())"); await frames(page, 1)
        gt = await page.evaluate(f"({{ lives: {S}.lives, max: {S}.maxLives, tickets: {P}.tickets, used: {S}.ticket, toasts: {TOASTS} }})")
        check('the next run starts with +1 life (the ticket used up, a toast)', gt['lives'] == gt['max'] + 1 and gt['tickets'] == 0 and gt['used'] and any('+1 life this run' in x for x in gt['toasts']), gt)
        await page.evaluate(f"{P}.tickets = 1; __grasp.daily.forceModifier = 'tiny'; __grasp.startDaily()"); await frames(page, 1)
        check('the daily never uses a ticket (the same run for everyone)', await page.evaluate(f"{S}.lives === 3 && {P}.tickets === 1"))
        check('chest: no page errors', not errs, errs); await ctx.close()

        # ---- the daily ignores the road: a level-1 player gets the full seeded run, with 'Preview!' on what is still locked ----
        ctx, page, errs = await new_page(b)
        await page.evaluate("__grasp.daily.forceModifier = 'tiny'; __grasp.setGameMode('strike'); __grasp.startDaily()")
        await page.wait_for_function("__grasp.daily.on && __grasp.strike.walls.length", timeout=8000)
        await page.evaluate(SFX_JS + "; " + PARK)
        dy = await page.evaluate(GATE_SIM.replace('__grasp.setPlayerLevel(plv);', '') + "(1, 12)")
        check('daily, level-1 player at run level 12: every wall kind, every power-up, both animals, wobbling serves and every perk (the road does not apply)',
              set(dy['kinds']) == {'brick', 'glass', 'steel', 'holed', 'moving', 'tnt'} and set(dy['pus']) == {'multi', 'big', 'slow', 'fire', 'life'} and set(dy['guests']) == {'cow', 'monkey'} and dy['waves'] > 0 and len(dy['offers']) == 8, dy)
        await page.evaluate(f"{PARK}; __grasp.CONFIG.STRIKE_PU_RATE = 0; {S}.spots.length = 0; {S}.previewed.clear(); {S}.seenKinds.clear(); {S}.lastSpot = null; {S}.walls.length = 0; {S}.spawnWall('steel')")
        await page.wait_for_function(f"{S}.ui.spot", timeout=3000)
        pv = await page.evaluate(f"({{ last: {S}.lastSpot, ui: {S}.ui.spot, got: {P}.road.got, fresh: {P}.road.fresh }})")
        check("a locked thing in the daily gets 'Preview! Steel walls' (the profile's road unchanged)", pv['last']['id'] == 'steel' and pv['last']['preview'] and pv['ui']['text'] == 'Preview! Steel walls' and pv['got'] == ['brick', 'cow'] and pv['fresh'] == [], pv)
        await page.screenshot(path='tests/out/road_daily_preview.png')
        await page.evaluate(f"{S}.lastSpot = null; {S}.seenKinds.clear(); {S}.walls.length = 0; {S}.spawnWall('steel')"); await frames(page, 2)
        check('...once a run', await page.evaluate(f"{S}.lastSpot") is None)
        check('daily: no page errors', not errs, errs); await ctx.close()

        # ---- the economy: a scripted typical Easy run (9 walls = 2 levels completed, a guest slapped, 2 power-ups) earns 15-35 coins; the cheapest look is >= 4 such runs ----
        ctx, page, errs = await new_page(b)
        await play(page); await page.evaluate(f"{PARK}; __grasp.CONFIG.STRIKE_PU_RATE = 0; {S}.guestEvery = 0")
        c0 = await page.evaluate(f"{P}.coins")
        for i in range(9):
            await page.wait_for_function(f"{S}.walls.some(w => w.left > 0 && w.z < __grasp.CONFIG.STRIKE_Z_FAR) && !{S}.chest", timeout=8000)
            await page.evaluate(f"(() => {{ const s = {S}; s.perkAt = 0; s.perkOffer = null; s.balls.length = 0; const w = s.walls.filter(q => q.left > 0 && q.z < __grasp.CONFIG.STRIKE_Z_FAR).sort((a, b) => a.z - b.z)[0]; wallDown(w, performance.now()); }})()")  # (v4: a wall takes several hits now: the scripted run knocks the nearest one out)
            await page.wait_for_function(f"{S}.cleared >= {i + 1}", timeout=8000); await page.evaluate(f"{S}.balls.length = 0")
        await page.evaluate(f"(() => {{ const s = {S}, b = s.spawnGuest('cow'); s.setBallZ(30, 640, 420); b.guest = 'cow'; strikeHit(s.ball, performance.now()); s.catchTest('big'); s.catchTest('slow'); }})()")
        ec = await page.evaluate(f"({{ coins: {P}.coins - {c0}, cleared: {S}.cleared, level: {S}.level, cheapest: Math.min(...__grasp.collection.items.filter(i => i.cost > 0).map(i => i.cost)), table: ECONOMY.strike, prices: ECONOMY.prices }})")
        print('INFO economy:', ec)
        check(f"economy: a typical Easy run ({ec['cleared']} walls, level {ec['level']}, a guest, 2 power-ups) earns {ec['coins']} coins (15-35); the cheapest look ({ec['cheapest']}) takes >= 4 such runs",
              ec['cleared'] >= 9 and ec['level'] >= 3 and 15 <= ec['coins'] <= 35 and ec['cheapest'] / ec['coins'] >= 4, ec)
        pr = ec['prices']
        check('prices: cheapest looks 120-150, mid 300-450, premium 700-900, the disco ball / robot hand ~1000; the road items are not for sale', all(120 <= pr[k] <= 150 for k in ('ball_beach', 'hand_mint', 'hand_sky', 'hand_lilac')) and all(300 <= pr[k] <= 450 for k in ('blade_neon', 'ball_soccer', 'trail_sparkle')) and all(700 <= pr[k] <= 900 for k in ('trail_fire', 'blade_rainbow')) and pr['ball_disco'] == pr['hand_robot'] == 1000 and await page.evaluate("['ball_lava', 'trail_lava', 'hand_legend', 'ball_planet', 'hand_cat', 'trail_rainbow'].every(id => { const it = __grasp.collection.items.find(i => i.id === id); return it.level && !it.cost; }) && !__grasp.collection.buy('hand_legend')"), pr)
        check('economy: no page errors', not errs, errs); await ctx.close()

        # ---- XP per run: a typical 3-minute run is a third to a half of a player level early on (levels 1-5), less later ----
        ctx, page, errs = await new_page(b)
        xp = await page.evaluate("""(() => { const X = __grasp.runXp, F = __grasp.xpForLevel, gap = (L) => F(L + 1) - F(L), typ = X({ walls: 12, levels: 2, bosses: 0 });
          const band = []; for (const w of [10, 12, 14]) for (const l of [2, 3]) band.push(X({ walls: w, levels: l, bosses: 0 }));
          const early = [1, 2, 3, 4, 5].map(L => typ / gap(L)), lo = [1, 2, 3, 4, 5].map(L => Math.min(...band) / gap(L)), hi = [1, 2, 3, 4, 5].map(L => Math.max(...band) / gap(L));
          let xp = 0, runs = 0; const per = []; for (let d = 1; d <= 3; d++) { for (let r = 0; r < 6; r++) { xp += typ; runs++; } per.push(__grasp.levelOf(xp)); }
          return { typ, band, early, lo, hi, late: typ / gap(15), strong: X({ walls: 40, levels: 6, bosses: 1 }), days: per, to20: Math.ceil(F(20) / typ) }; })()""")
        print('INFO XP per run:', xp)
        check('a typical 3-minute run (12 walls, 2 levels): 88 XP = between a third and a half of each of player levels 1-5', xp['typ'] == 88 and all(1 / 3 - 0.005 <= k <= 0.5 for k in xp['early']), xp['early'])
        check('typical runs (10-14 walls, 2-3 levels): roughly 0.3-0.6 of a level early on; later levels take longer (level 15: under a quarter); a strong run earns ~3x', all(0.29 <= k for k in xp['lo']) and all(k <= 0.62 for k in xp['hi']) and xp['late'] < 0.25 and xp['strong'] > 2.5 * xp['typ'], xp)
        check('six typical runs a day: about 2-3 levels on day 1; the 20-level ladder takes many sessions (over 60 typical runs)', 3 <= xp['days'][0] <= 4 and xp['days'][2] - xp['days'][0] >= 2 and xp['to20'] > 60, xp['days'])
        check('XP: no page errors', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
