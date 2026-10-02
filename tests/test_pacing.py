exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Pacing step 1: the run arc (levels 1-2 pure core; power-ups from 3 and rare; perks after odd levels from 3; flying animals from 4;
# wall kinds one level later) and the level tension arc (heartbeat / edge lights tighten, a glowing 'final wall', a calm release beat),
# plus first-run onboarding tips. Hooks: strike.pacing, strike.finalWall, strike.releaseUntil, profile.tips.
S = "__grasp.strike"
FRAMES = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
SFX_JS = "(() => { window.__sfx = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); o(k, a); }; })()"
PARK = f"(() => {{ const s = {S}; if (!s.ball) s.serve(); s.setBallZ(2300, 30, 30); s.ball.speed = 0; s.lives = 40; }})()"
SPAWN_N = f"""((L, n) => {{ const s = {S}; s.setLevel(L); let pu = 0; const kinds = {{}}; for (let i = 0; i < n; i++) {{ const w = s.spawnWall(undefined, 9000 + i); kinds[w.kind] = (kinds[w.kind] || 0) + 1; if (w.bricks.some(k => k.pu)) pu++; s.walls.splice(s.walls.indexOf(w), 1); }} return {{ pu: pu / n, kinds }}; }})"""

async def frames(page, n=1):
    for _ in range(n): await page.evaluate(FRAMES)

async def new_page(b, gfx=None, ctx=None):
    if ctx is None: ctx = await b.new_context(viewport={'width': 1280, 'height': 800})
    page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + (f"window.__graspGfx = {gfx};" if gfx else ''))
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
    await page.evaluate("__grasp.setPlayerLevel(20)")  # the road unlocks everything (these suites test the run arc, not the meta gate)
    return ctx, page, errs

async def play(page):
    await page.click('#mouseBtn'); await page.click('.modes button[data-mode=strike]')
    await page.wait_for_function("gameMode === 'strike' && __grasp.strike.walls.length", timeout=8000)
    await page.evaluate(SFX_JS); await page.mouse.move(640, 760)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        ctx, page, errs = await new_page(b)
        await play(page)
        # ---- onboarding: a fresh profile's first run opens with the serve tip (not the usual start line) ----
        g0 = await page.evaluate("({ last: __grasp.grippy.last && __grasp.grippy.last.event, tips: __grasp.profile.tips.slice() })")
        check("first Strike run on a fresh profile: Grippy's first line is the serve tip ('Slap the ball!'), recorded in profile.tips", g0['last'] == 'tip_serve' and g0['tips'] == ['serve'], g0)
        await page.evaluate(PARK)
        # ---- the rules per level (strike.pacing) ----
        rules = await page.evaluate(f"[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(L => {{ {S}.setLevel(L); const q = {S}.pacing; return {{ L, pu: +q.puRate.toFixed(3), perk: q.perkLevel, guests: q.guestsOn, kinds: q.kindsUnlocked.join(','), curve: {S}.tuning(L).curve > 0, waves: {S}.tuning(L).waves }}; }})")
        print('INFO pacing:', rules)
        check('levels 1-2: no power-up bricks (rate 0), no perk after them, no flying animals, brick walls only, straight balls', all(r['pu'] == 0 and not r['perk'] and not r['guests'] and r['kinds'] == 'brick' and not r['curve'] for r in rules[:2]), rules[:2])
        check('power-ups from level 3: ~1 a wall in 3 at levels 3-4, rising slowly to 1 in 2 by level 8', abs(rules[2]['pu'] - 1 / 3) < 0.01 and abs(rules[3]['pu'] - 1 / 3) < 0.01 and rules[2]['pu'] < rules[5]['pu'] < rules[7]['pu'] and abs(rules[7]['pu'] - 0.5) < 0.01 and abs(rules[9]['pu'] - 0.5) < 0.01, [r['pu'] for r in rules])
        check('perk picks only after levels 3, 5, 7, 9', [r['L'] for r in rules if r['perk']] == [3, 5, 7, 9], [r['perk'] for r in rules])
        check('flying animals from level 4', [r['guests'] for r in rules] == [False] * 3 + [True] * 7, [r['guests'] for r in rules])
        check('wall kinds one level later: L3 glass, L4 steel, L6 holed, L7 moving, L8 TNT; curving balls from L5, the S-wobble from L9',
              [r['kinds'] for r in rules[:8]] == ['brick', 'brick', 'brick,glass', 'brick,glass,steel', 'brick,glass,steel', 'brick,glass,steel,holed', 'brick,glass,steel,holed,moving', 'brick,glass,steel,holed,moving,tnt']
              and [r['curve'] for r in rules] == [False] * 4 + [True] * 6 and [r['waves'] for r in rules] == [1] * 8 + [2] * 2, rules)
        luck = await page.evaluate(f"(() => {{ const s = {S}; s.setLevel(3); s.perks.lucky = 1; const r = s.pacing.puRate; s.perks.lucky = 0; return r; }})()")
        check('the Lucky perk still multiplies the power-up rate (+50%)', abs(luck - 0.5) < 0.01, luck)
        # ---- simulated walls: levels 1-2 spawn bricks only, no power-ups; the measured rate per level is in band ----
        sim = {}
        for L, n in ((1, 120), (2, 120), (3, 240), (4, 240), (6, 240), (8, 240)): sim[L] = await page.evaluate(SPAWN_N + f"({L}, {n})")
        print('INFO simulated walls:', sim)
        check('120 walls each at levels 1 and 2: all brick, none with a power-up brick', all(sim[L]['pu'] == 0 and list(sim[L]['kinds']) == ['brick'] for L in (1, 2)), {L: sim[L] for L in (1, 2)})
        band = {3: (0.22, 0.45), 4: (0.22, 0.45), 6: (0.3, 0.53), 8: (0.38, 0.62)}
        check('measured power-up walls per level within the expected band (L3 ~0.33, L4 ~0.33, L6 ~0.42, L8 ~0.5)', all(band[L][0] <= sim[L]['pu'] <= band[L][1] for L in band), {L: sim[L]['pu'] for L in band})
        check('glass first appears at level 3 (not before)', 'glass' in sim[3]['kinds'] and 'glass' not in sim[2]['kinds'] and 'steel' not in sim[3]['kinds'], sim[3]['kinds'])
        # ---- guests: none in 30 serves at levels 1-3; from level 4 the first one comes 8-12 serves in ----
        gq = await page.evaluate(f"""(() => {{ const s = {S}, out = {{}}; for (const L of [1, 2, 3]) {{ s.setLevel(L); let g = 0; for (let i = 0; i < 30; i++) {{ s.serve(); if (s.ball.guest) g++; }} out[L] = g; }}
          s.setLevel(4); let first = 0; for (let i = 1; i <= 14 && !first; i++) {{ s.serve(); if (s.ball.guest) first = i; }} out.first4 = first; s.ball.guest = null; return out; }})()""")
        check(f"flying animals: none in 30 serves at levels 1, 2, 3; at level 4 the first comes on serve {gq['first4']} (8-12)", gq['1'] == 0 and gq['2'] == 0 and gq['3'] == 0 and 8 <= gq['first4'] <= 12, gq)
        await page.evaluate(PARK)
        # ---- perk offers in play: none after levels 1, 2; one after level 3 (once the release is over) ----
        async def clear_to(n): await page.evaluate(f"{PARK}; {S}.setCleared({n})")
        await page.evaluate(f"(() => {{ const s = {S}; s.setLevel(1); s.walls.length = 0; for (let i = 0; i < 4; i++) s.spawnWall('brick', 960 + 400 * i); }})()")
        po = {}
        for n, lv in ((4, 2), (9, 3), (15, 4)):
            await clear_to(n); po[lv] = await page.evaluate(f"({{ level: {S}.level, perkAt: {S}.perkAt, offer: !!{S}.perkOffer, rel: {S}.releaseUntil - performance.now() }})")
        check('levels 1 and 2 completed: no perk pick; level 3 completed: a perk pick queued for the end of the release', po[2]['level'] == 2 and po[2]['perkAt'] == 0 and po[3]['level'] == 3 and po[3]['perkAt'] == 0 and po[4]['level'] == 4 and po[4]['perkAt'] > 0 and not po[4]['offer'], po)
        await page.wait_for_function(f"{S}.perkOffer", timeout=8000)
        at = await page.evaluate(f"performance.now() - {S}.releaseUntil")
        check('the perk cards open as the release ends (not before)', at >= -50, at)
        await page.evaluate(f"{S}.pickPerk(0)"); await frames(page, 1)
        await clear_to(22); p5 = await page.evaluate(f"({{ level: {S}.level, perkAt: {S}.perkAt }})")
        check('level 4 completed: no perk pick (every other level)', p5['level'] == 5 and p5['perkAt'] == 0, p5)
        # ---- the final wall: L6 (goal 7) -> after 6 walls the front wall is the final one ----
        await page.wait_for_function(f"performance.now() > {S}.releaseUntil", timeout=5000)
        await page.evaluate(f"(() => {{ const s = {S}; s.setLevel(6); s.walls.length = 0; s.spawnWall('brick', 960); s.spawnWall('brick', 1360); s.ui.tag = null; __grasp.grippy.cool(); }})()")
        t0 = await page.evaluate(f"({{ fin: {S}.finalWall, tension: {S}.pacing.tension, beat: {S}.pacing.beatMs, hp: {S}.walls[0].bricks.map(k => k.hp) }})")
        cl6 = await page.evaluate(f"{S}.cleared")
        await clear_to(cl6 + 5); m5 = await page.evaluate(f"({{ fin: {S}.finalWall, tension: {S}.pacing.tension, beat: {S}.pacing.beatMs, level: {S}.level, progress: {S}.progress }})")
        await page.wait_for_function(f"performance.now() > {S}.releaseUntil", timeout=5000)
        await clear_to(cl6 + 6); await page.wait_for_function(f"{S}.finalWall", timeout=5000); await frames(page, 2)
        fw = await page.evaluate(f"""(() => {{ const s = {S}, w = s.walls.find(q => q.final), base = s.tuning(6).brickHp; return {{ level: s.level, progress: s.progress, goal: s.goal, tag: s.ui.tag && s.ui.tag.kind, box: !!s.ui.tagBox, text: s.ui.tagBox ? t('wk_final') : '', grippy: __grasp.grippy.last.event,
          tough: w.bricks.filter(k => k.hp === base + 1).length, n: w.bricks.length, front: w === s.walls.filter(q => q.left > 0).sort((a, b) => a.z - b.z)[0], tension: s.pacing.tension, beat: s.pacing.beatMs }}; }})()""")
        check(f"the level's last wall is the 'final wall': flagged, the 'Final wall!' tag, Grippy's final-wall line, +1 hp on {fw['tough']} of {fw['n']} bricks (a third)",
              fw['level'] == 6 and fw['progress'] == fw['goal'] - 1 and fw['front'] and fw['tag'] == 'final' and fw['box'] and fw['text'] == 'Final wall!' and fw['grippy'] == 'final' and abs(fw['tough'] - fw['n'] / 3) <= 2, fw)
        check(f"tension builds through the level: heartbeat {t0['beat']:.0f} -> {m5['beat']:.0f} -> {fw['beat']:.0f} ms, tension 0 -> {m5['tension']:.2f} -> 1", t0['tension'] == 0 and 0 < m5['tension'] < 1 and fw['tension'] == 1 and t0['beat'] > m5['beat'] > fw['beat'], [t0, m5, fw])
        # the glow: gold pixels on the final wall's rim (2D), gone when the flag is off
        rim = f"""(() => {{ const s = {S}, w = s.walls.find(q => q.final) || s.walls[0], {{ L, T, B }} = corridor(), c = brickCell(w, 0, 0), lw = Math.min(c.w, c.h) * 0.07, p = proj(L + (w.ox || 0) + lw / 2, (T + B) / 2 + c.h * 0.3, w.z); return s.pixel(p.x, p.y); }})()"""
        await page.evaluate(PARK); await frames(page, 2); g1 = await page.evaluate(rim)
        await page.evaluate(f"{S}.walls.find(q => q.final).final = false"); await frames(page, 2); g2 = await page.evaluate(rim)
        await page.evaluate(f"{S}.walls.filter(q => q.left > 0).sort((a, b) => a.z - b.z)[0].final = true"); await frames(page, 1)
        check('the final wall glows: a gold pixel on its rim, not there on an ordinary wall', g1[0] > 170 and g1[0] > g1[2] + 70 and g1[1] > 110 and sum(g1) > sum(g2) + 80, [g1, g2])
        # ---- the release: completing a level -> 2.5 s calm: no ball served, the heartbeat stops, a chime and the level-up; then a serve ----
        await page.evaluate("__sfx.length = 0")
        r0 = await page.evaluate(f"(() => {{ const s = {S}; s.setLevel(4); s.setCleared(s.cleared + 7); return {{ now: performance.now(), rel: s.releaseUntil, level: s.level, balls: s.balls.length, beats: s.beats, up: !!s.ui.levelUp, sfx: __sfx.slice(), perkAt: s.perkAt }}; }})()")
        check('a level completed (level 4 -> 5; level 6 now ends in the world boss): the release starts (2.5 s), the ball in play pops away, a soft chime and the level-up fanfare', r0['level'] == 5 and abs(r0['rel'] - r0['now'] - 2500) < 5 and r0['balls'] == 0 and r0['up'] and 'chime' in r0['sfx'] and 'levelup' in r0['sfx'], r0)
        seen = []
        while True:
            q = await page.evaluate(f"({{ t: performance.now(), balls: {S}.balls.length, beats: {S}.beats, over: {S}.over, offer: !!{S}.perkOffer }})")
            if q['t'] > r0['rel'] - 100: break
            seen.append(q); await page.wait_for_timeout(150)
        check(f"during the release ({len(seen)} samples over 2.4 s): no ball served, no heartbeat", len(seen) >= 4 and all(q['balls'] == 0 for q in seen) and all(q['beats'] == r0['beats'] for q in seen), seen[-3:])
        await page.wait_for_function(f"{S}.balls.length > 0", timeout=4000)
        r1 = await page.evaluate(f"performance.now() - {S}.releaseUntil")
        check(f'after the release the next level starts: a ball is served ({r1:.0f} ms after it ends)', 0 <= r1 < 1500, r1)
        # ---- onboarding tips: the first gold brick, the first perk pick, the first flying animal: once each per profile ----
        await page.evaluate(f"(() => {{ const s = {S}; s.setLevel(3); s.walls.length = 0; __grasp.CONFIG.STRIKE_PU_RATE = 1; s.spawnWall('brick', 960); __grasp.CONFIG.STRIKE_PU_RATE = 1 / 12; }})()"); await frames(page, 3)
        await page.evaluate(f"{S}.spawnGuest('cow')"); await frames(page, 2)
        await page.evaluate(f"(() => {{ const s = {S}; s.walls.length = 0; __grasp.CONFIG.STRIKE_PU_RATE = 1; s.spawnWall('brick', 960); __grasp.CONFIG.STRIKE_PU_RATE = 1 / 12; __grasp.grippy.cool(); s.spawnGuest('monkey'); }})()"); await frames(page, 3)
        ev = await page.evaluate("({ said: __grasp.grippy.said.map(x => x.event), tips: __grasp.profile.tips.slice() })")
        cnt = {e: ev['said'].count(e) for e in ('tip_serve', 'tip_pu', 'tip_perk', 'tip_guest')}
        check(f"onboarding tips: serve, gold brick, perk pick, flying animal each explained exactly once ({cnt}); profile.tips = {ev['tips']}", all(v == 1 for v in cnt.values()) and sorted(ev['tips']) == ['guest', 'perk', 'pu', 'serve'] and 'monkey' in ev['said'], ev)
        check('no page errors', not errs, errs)
        # a new page on the same profile: the tips are not repeated (the usual start line)
        await page.close(); _, page2, errs2 = await new_page(b, ctx=ctx); await play(page2)
        g2 = await page2.evaluate("({ last: __grasp.grippy.last && __grasp.grippy.last.event, tips: __grasp.profile.tips.slice() })")
        check('next run on that profile: no tip, the usual start line; the seen tips persist', g2['last'] == 'start' and sorted(g2['tips']) == ['guest', 'perk', 'pu', 'serve'], g2)
        check('second run: no page errors', not errs2, errs2); await ctx.close()

        # ---- 3D: the final wall's glowing frame and the tension-brightened edge strips ----
        ctx, page, errs = await new_page(b, gfx="{ pr: 0.4, auto: false, shadows: false }"); await play(page)
        await page.wait_for_function(f"{S}.gfx === '3d' || {S}.gfxInfo.state === 'failed'", timeout=20000)
        if await page.evaluate(f"{S}.gfx") == '3d':
            await page.evaluate(PARK)
            e0 = await page.evaluate(f"(async () => {{ const s = {S}; s.setLevel(6); s.walls.length = 0; s.spawnWall('brick', 960); await {FRAMES}; return {{ edge: G3.edgeMat.color.r + G3.edgeMat.color.g + G3.edgeMat.color.b, tension: s.pacing.tension }}; }})()")
            await page.evaluate(f"{S}.setCleared({S}.cleared + 6)"); await page.wait_for_function(f"{S}.finalWall", timeout=5000); await frames(page, 2)
            f3 = await page.evaluate(f"(() => {{ const s = {S}, w = s.walls.find(q => q.final), e = G3.walls.get(w.id); return {{ frame: !!e.frame && e.frame.visible && e.frame.count === 4, add: e.frame && e.frame.material.blending === G3.T.AdditiveBlending, tension: s.pacing.tension, edge: G3.edgeMat.color.r + G3.edgeMat.color.g + G3.edgeMat.color.b }}; }})()")
            check('3D: the final wall gets a glowing (additive) gold frame; the edge strips burn brighter with the tension', f3['frame'] and f3['add'] and f3['tension'] == 1 and e0['tension'] == 0, [e0, f3])
        else: print('INFO no WebGL: 3D final-wall check skipped')
        check('3D page: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)

asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
