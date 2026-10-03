exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Strike step 3: the difficulty curve. strikeTuning(level, diff) derives every per-level value; level 1 is the old constants exactly.
# Timing-independent: the ball is parked (speed 0) between checks; every wait is a condition.
S = "__grasp.strike"
FRAMES = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
PIX = "((x, y) => __grasp.strike.pixel(x, y))"  # the composited pixel: the WebGL layer (3D mode) under the 2D canvas; in 2D mode the 2D canvas pixel
SFX_JS = "(() => { window.__sfx = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); o(k, a); }; })()"
HELP_JS = """
window.park = (z = 2300, x = 30, y = 30) => { const s = __grasp.strike; s.setBallZ(z, x, y); s.ball.speed = 0; s.lives = 40; };
window.tun = (l, d) => __grasp.strike.tuning(l, d);
"""
EN_NEWS = {'nw_steel': 'New: steel walls!', 'nw_holed': 'New: walls with holes!', 'hd_curve': 'Curving balls!', 'hd_faster': 'Faster!', 'hd_tougher': 'Tougher walls!', 'nw_moving': 'New: moving walls!', 'nw_tnt': 'New: TNT walls!', 'hd_wobble': 'Wobbly balls!', 'hd_boss': 'Faster boss!'}
HE_NEWS = {'nw_steel': 'חדש: קירות פלדה!', 'nw_holed': 'חדש: קירות עם חור!', 'hd_curve': 'הכדור מתעקל!', 'hd_faster': 'מהר יותר!', 'hd_tougher': 'קירות קשים יותר!', 'nw_moving': 'חדש: קירות זזים!', 'nw_tnt': 'חדש: קירות TNT!', 'hd_wobble': 'הכדור מתפתל!', 'hd_boss': 'הבוס מהיר יותר!'}

async def new_page(b, mobile=False, lang='en'):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + f"try {{ localStorage.setItem('lang', '{lang}'); }} catch (e) {{}}")
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
    await page.evaluate("__grasp.setPlayerLevel(20)")  # the road unlocks everything (these suites test the run arc, not the meta gate)
    return ctx, page, errs

async def play_strike(page, tap=False):
    if tap: await page.tap('#mouseBtn'); await page.tap('.modes button[data-mode=strike]'); await page.tap('#advEndless')
    else: await page.click('#mouseBtn'); await page.click('.modes button[data-mode=strike]'); await page.click('#advEndless')
    await page.wait_for_function("mode === 'mouse' && gameMode === 'strike' && __grasp.strike.ball", timeout=8000)
    await page.evaluate(SFX_JS + ";\n" + HELP_JS + f"\n__grasp.CONFIG.STRIKE_PU_RATE = 0; {S}.extrasOff = true; park()")

async def frames(page, n=1):
    for _ in range(n): await page.evaluate(FRAMES)

def mono(xs, inc=True): return all((b > a) if inc else (b < a) for a, b in zip(xs, xs[1:]))

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ===== desktop, mouse, Easy (the default) =====
        ctx, page, errs = await new_page(b); await play_strike(page)
        await page.mouse.move(640, 300); await page.wait_for_timeout(100)
        t1 = await page.evaluate("({ e: tun(1, 'easy'), n: tun(1, 'normal'), cur: tun(), pace: __grasp.strike.pace, base: __grasp.strike.levelBase, params: __grasp.strikeParams(), gap: wallSlotZ(1) - wallSlotZ(0) })")
        e, n = t1['e'], t1['n']
        check('hooks: strike.tuning(level?) defaults to the current level (1, Easy); strike.levelBase = the level-1 pace', t1['cur'] == e and t1['cur']['level'] == 1 and t1['cur']['diff'] == 'easy' and t1['base'] == 0.65 and t1['pace'] == 0.65, t1['cur'])
        check('level 1 Easy = the previous constants: pace 0.65, max 2.2, grow 1.03, magnet 0.5, wall gap 400, brick hp 1, boss x1 / 40 s, reach x1, aim x1, no curve, brick-only mix',
              e['pace'] == 0.65 and e['maxSpeed'] == 2.2 and e['grow'] == 1.03 and e['magnet'] == 0.5 and e['wallGap'] == 400 and e['brickHp'] == 1 and e['bossHpMul'] == 1 and e['bossMs'] == 40000 and e['reach'] == 1 and e['drift'] == 1 and e['curve'] == 0 and e['kindWeights'] == {'brick': 3} and e['fog'] == 0 and e['edge'] == [120, 170, 255], e)
        check('level 1 Normal = the previous constants: pace 1.1, max 2.8, grow 1.05, magnet 0, gap 400, hp 1, boss x1 / 40 s, reach x1',
              n['pace'] == 1.1 and n['maxSpeed'] == 2.8 and n['grow'] == 1.05 and n['magnet'] == 0 and n['wallGap'] == 400 and n['brickHp'] == 1 and n['bossHpMul'] == 1 and n['bossMs'] == 40000 and n['reach'] == 1 and n['drift'] == 1 and n['curve'] == 0, n)
        pr = t1['params']
        check('strikeParams() unchanged (level-1 Easy values) and the level-1 wall slots are 400 apart', pr['speed'] == 0.65 and pr['max'] == 2.2 and pr['grow'] == 1.03 and pr['magnet'] == 0.5 and abs(t1['gap'] - 400) < 1e-9, [pr, t1['gap']])
        T = await page.evaluate("({ easy: [1,2,3,4,5,6,7,8].map(l => tun(l, 'easy')), normal: [1,2,3,4,5,6,7,8].map(l => tun(l, 'normal')), far: [9, 12, 20, 40].map(l => tun(l, 'easy')) })")
        for d in ('easy', 'normal'):
            col = lambda k: [x[k] for x in T[d]]
            check(f'{d}: pace, max speed, aim range, boss hp and boss advance rise at every level 1 -> 8', all(mono(col(k)) for k in ('pace', 'maxSpeed', 'drift', 'bossHpMul', 'bossSpeed')), {k: [round(v, 3) for v in col(k)] for k in ('pace', 'maxSpeed', 'drift', 'bossHpMul')})
            check(f'{d}: the wall gap and the heartbeat interval shrink at every level 1 -> 8', mono(col('wallGap'), False) and mono(col('beatMs'), False), [round(v) for v in col('wallGap')])
            check(f'{d}: no curve on levels 1-3, a curve from level 4 that grows; armored bricks\' hp = the level up to 3 (v4), their share 0 -> 40% by level 5', all(x['curve'] == 0 for x in T[d][:3]) and mono(col('curve')[3:]) and col('brickHp') == [1, 2, 3, 3, 3, 3, 3, 3] and [round(a, 2) for a in col('armor')] == [0, 0.1, 0.2, 0.3, 0.4, 0.4, 0.4, 0.4], [col('curve'), col('brickHp'), col('armor')])
            check(f'{d}: each level\'s pace cap sits between its base and the next level\'s base', all(x['pace'] < x['paceCap'] < y['pace'] for x, y in zip(T[d], T[d][1:])))
        es, ns = [x['speedMul'] for x in T['easy']], [x['speedMul'] for x in T['normal']]
        check('Normal ramps 12% per level, Easy 10% (level 8: x1.84 vs x1.70); Normal faster than Easy at every level from 2', abs(ns[1] - 1.12) < 1e-9 and abs(es[1] - 1.10) < 1e-9 and abs(ns[7] - 1.84) < 1e-9 and abs(es[7] - 1.70) < 1e-9 and all(a > b for a, b in zip(ns[1:], es[1:])), [ns, es])
        check('Normal tightens faster than Easy: smaller wall gap, wider aim at level 8; the boss level factor is the same (Easy\'s hp = 0.85 x Normal\'s)', T['normal'][7]['wallGap'] < T['easy'][7]['wallGap'] and T['normal'][7]['drift'] > T['easy'][7]['drift'] and all(abs(a['bossHpMul'] - b['bossHpMul']) < 1e-12 for a, b in zip(T['normal'], T['easy'])))
        ev = lambda k: [round(x[k], 6) for x in T['easy']]
        check('new Easy curve: max speed +4% a level, reach 1 / 0.95 / 0.90 / 0.85 then held, magnet 0.5 on levels 1-2 fading to 0.15 by level 6 (floor), gap 400 -8 a level',
              ev('maxSpeed') == [round(2.2 * (1 + 0.04 * i), 6) for i in range(8)] and ev('reach') == [1, 0.95, 0.9, 0.85, 0.85, 0.85, 0.85, 0.85] and ev('magnet') == [0.5, 0.5, 0.4125, 0.325, 0.2375, 0.15, 0.15, 0.15] and all(x['magnet'] >= 0.15 - 1e-9 for x in T['far']) and ev('wallGap') == [400 - 8 * i for i in range(8)] and all(x['wallGap'] >= 300 for x in T['far']),
              {k: ev(k) for k in ('maxSpeed', 'reach', 'magnet', 'wallGap')})
        check('levels 1-2 are the pure core, then every level-up brings one new thing in order: L3 glass, L4 steel, L5 curve, L6 holed, L7 moving, L8 TNT, L9 S-wobble + a faster boss (both difficulties)',
              [sorted(x['kindWeights']) for x in T['easy'][:8]] == [sorted(['brick', 'glass', 'steel', 'holed', 'moving', 'tnt'][:n]) for n in (1, 1, 2, 3, 3, 4, 5, 6)] and all(x['curve'] == 0 for x in T['easy'][:4]) and T['easy'][4]['curve'] > 0
              and [x['waves'] for x in T['easy']] == [1] * 8 and T['far'][0]['waves'] == 2 and [x['waves'] for x in T['normal']] == [1] * 8 and T['far'][0]['bossMs'] < T['easy'][7]['bossMs'] / 1.2, [x['waves'] for x in T['normal']])
        tint = [tuple(x['edge']) for x in T['normal']]
        check('corridor tint: a clearly different colour on each of levels 1-8 (blue, teal, green, gold, orange, red, purple, deep red), with fog from level 2', len(set(tint)) == 8 and all(sum(abs(a - b) for a, b in zip(p, q)) > 60 for p, q in zip(tint, tint[1:])) and T['normal'][0]['fog'] == 0 and all(x['fog'] >= 0.14 for x in T['normal'][1:]), tint)
        allE = T['easy'] + T['far']
        check('Easy floors: the reach never below 85% of level 1, the magnet never below 0.15, at any level', all(x['reach'] >= 0.85 - 1e-9 for x in allE) and all(x['magnet'] >= 0.15 - 1e-9 for x in allE) and T['easy'][7]['reach'] < 1 and T['easy'][7]['magnet'] < 0.5, [(x['level'], round(x['reach'], 3), round(x['magnet'], 3)) for x in allE])
        check('Normal: the magnet stays 0, the reach shrinks to a floor', all(x['magnet'] == 0 for x in T['normal']) and T['normal'][7]['reach'] < T['easy'][7]['reach'], [x['reach'] for x in T['normal']])
        check('past level 8 only the pace creeps up (no runaway): level 40 Easy under its max speed', T['far'][-1]['pace'] > T['easy'][7]['pace'] and T['far'][-1]['pace'] < T['far'][-1]['maxSpeed'] and T['far'][-1]['wallGap'] == T['easy'][7]['wallGap'])
        check('the wall-kind mix: level 8 has all six kinds; Normal level 8 favours steel / moving / TNT over plain brick', set(T['easy'][7]['kindWeights']) == {'brick', 'glass', 'steel', 'holed', 'moving', 'tnt'} and T['normal'][7]['kindWeights']['steel'] > T['normal'][7]['kindWeights']['brick'], T['normal'][7]['kindWeights'])

        # ===== the pace inside a level: grows per far-wall bounce, capped; reset to the new base on a level-up =====
        await page.evaluate(f"{S}.setLevel(3); park()")
        b3 = await page.evaluate(f"({{ pace: {S}.pace, base: {S}.levelBase, t: tun(3) }})")
        check('setLevel(3): the pace and levelBase are the level-3 base', b3['pace'] == b3['base'] == b3['t']['pace'], b3)
        paces = []
        for i in range(7):
            n0 = await page.evaluate(f"{S}.bounces")
            await page.evaluate(f"(() => {{ const s = {S}, b = s.ball; b.dir = -1; b.z = __grasp.CONFIG.STRIKE_Z_FAR - 1; b.speed = 1; b.tier = ''; b.super = false; b.vx = b.vy = 0; b.x = 0; b.y = 0; }})()")
            await page.wait_for_function(f"{S}.bounces > {n0}", timeout=5000); await page.evaluate("park()")
            paces.append(await page.evaluate(f"{S}.pace"))
        cap, nxt = b3['t']['paceCap'], await page.evaluate("tun(4).pace")
        check('far-wall bounces: the pace grows 3% at first, then holds at the level cap, below the next level\'s base', abs(paces[0] - b3['pace'] * 1.03) < 1e-9 and paces == sorted(paces) and abs(paces[-1] - cap) < 1e-9 and paces[-1] < nxt, [paces, cap, nxt])
        await page.evaluate(f"{S}.ui.newsBox = null; {S}.setCleared(clearedAtLevel(4)); park()")
        lu = await page.evaluate(f"({{ level: {S}.level, pace: {S}.pace, base: {S}.levelBase, news: {S}.ui.levelBanner && {S}.ui.levelBanner.news, text: levelNewsText({S}.ui.levelBanner.news) }})")
        check('level-up to 4: the pace resets to the level-4 base, above the old base and the old capped pace', lu['level'] == 4 and abs(lu['pace'] - nxt) < 1e-9 and lu['base'] == lu['pace'] and lu['pace'] > paces[-1] > b3['pace'], [lu, paces[-1]])
        check('level 4 banner sub-line: "New: steel walls!  ·  Faster!  ·  Tougher walls!"', lu['news'] == ['nw_steel', 'hd_faster', 'hd_tougher'] and lu['text'] == '  ·  '.join(EN_NEWS[k] for k in lu['news']), lu)
        await page.wait_for_function(f"{S}.ui.newsBox && performance.now() > {S}.ui.levelBanner.t + 450", timeout=6000)
        nb = await page.evaluate(f"{S}.ui.newsBox")
        check('the banner draws the sub-line inside the screen', nb['text'] == lu['text'] and nb['x'] >= 0 and nb['x'] + nb['w'] <= 1280, nb)
        await page.screenshot(path='tests/out/strike7_banner_desktop.png')
        allnews = await page.evaluate("[2,3,4,5,6,7,8,9,10].map(l => levelNews(l))")
        check('every level-up 2 -> 10 names what got harder, "Faster!" every time; from 3 the new thing first: glass, steel, curve, holed, moving, TNT, wobble + faster boss', all(len(x) >= 1 and 'hd_faster' in x for x in allnews) and allnews[0][0] == 'hd_faster' and [x[0] for x in allnews[1:8]] == ['nw_glass', 'nw_steel', 'hd_curve', 'nw_holed', 'nw_moving', 'nw_tnt', 'hd_wobble'] and allnews[7][1] == 'hd_boss', allnews)
        he = await page.evaluate("(() => { setLang('he'); const r = ['nw_holed', 'hd_curve', 'hd_faster', 'hd_tougher', 'nw_moving'].map(k => t(k)); const all = ['glass', 'steel', 'holed', 'moving', 'tnt'].every(k => I18N.he['nw_' + k] && I18N.en['nw_' + k]) && ['faster', 'tougher', 'curve', 'wobble', 'boss'].every(k => I18N.he['hd_' + k] && I18N.en['hd_' + k]); setLang('en'); return { r, all }; })()")
        check('Hebrew sub-lines (and every news string in EN + HE)', he['r'] == [HE_NEWS[k] for k in ['nw_holed', 'hd_curve', 'hd_faster', 'hd_tougher', 'nw_moving']] and he['all'], he)

        # ===== curve, drift, gap, brick hp, boss, magnet, trail, heartbeat at a level =====
        cv = await page.evaluate(f"""(() => {{ const s = {S}, out = {{}}; const W0 = corridor().R - corridor().L;
          s.setLevel(4); s.serve(); out.c3 = s.ball.curve; park();
          s.setLevel(5); s.serve(); const b = s.ball; out.c4 = b.curve; out.want4 = tun(5).curve * W0; b.z = __grasp.CONFIG.STRIKE_Z_FAR * 0.5; b.speed = 0.0001; return out; }})()""")
        await frames(page, 2)
        mid = await page.evaluate(f"(() => {{ const b = {S}.ball, k = 1 - b.z / __grasp.CONFIG.STRIKE_Z_FAR; return {{ off: b.x - (b.x0 + (b.tx - b.x0) * k), c: b.curve }}; }})()")
        check('level 4 serves fly straight; level 5 serves bow sideways (curve = the tuned share of the corridor), mid-flight off the straight line', cv['c3'] == 0 and abs(abs(cv['c4']) - cv['want4']) < 1e-6 and abs(mid['off']) > 0.9 * abs(cv['c4']) and mid['off'] * cv['c4'] > 0, [cv, mid])
        await page.evaluate("park()")
        lv = await page.evaluate(f"""(() => {{ const s = {S}, r = {{}}; s.setLevel(6);
          const w = s.spawnWall('brick', 9000); r.hp = w.hp; s.walls.splice(s.walls.indexOf(w), 1);
          r.gap = wallSlotZ(1) - wallSlotZ(0); r.t = tun(6); r.trail6 = s.trailMs({{}}); r.magnet = magnetVal();
          s.boss = null; const bs = s.spawnBoss(1); r.boss = {{ hp: bs.maxHp, speed: bs.speed, z: bs.z }}; s.boss = null; s.setLevel(6);
          s.setLevel(1); r.trail1 = s.trailMs({{}}); r.gap1 = wallSlotZ(1) - wallSlotZ(0); s.setLevel(6); return r; }})()""")
        t6 = lv['t']
        check('level 6 (Easy): armored brick hp 3 (v4: the cap), wall slots closer (tuned gap), magnet faded to its 0.15 floor (full on levels 1-2)', lv['hp'] == 3 and abs(lv['gap'] - t6['wallGap']) < 1e-9 and lv['gap'] < lv['gap1'] and abs(lv['magnet'] - t6['magnet']) < 1e-9 and abs(lv['magnet'] - 0.15) < 1e-9, lv)
        check('level 6 boss: hp 16 x 0.85 x the level factor, advancing faster (tuned crossing time)', lv['boss']['hp'] == round(16 * 0.85 * t6['bossHpMul']) and lv['boss']['hp'] > 10 and abs(lv['boss']['speed'] - (lv['boss']['z'] - 450) / t6['bossMs']) < 1e-12 and t6['bossMs'] < 40000, lv['boss'])
        check('the ball trail is longer at the faster level-6 pace (160 ms at level 1)', lv['trail1'] == 160 and lv['trail6'] > 160 * 1.2, [lv['trail1'], lv['trail6']])
        # heartbeat: none on level 1, a soft beat from level 2, quicker each level
        await page.evaluate(f"{S}.setLevel(1); park(); __sfx.length = 0; {S}.beats = 0")
        await frames(page, 30); b1 = await page.evaluate(f"({{ beats: {S}.beats, sfx: __sfx.filter(k => k === 'beat').length }})")
        await page.evaluate(f"{S}.setLevel(5); park(); __sfx.length = 0; {S}.beats = 0; {S}.beatAt = 0")
        await page.wait_for_function(f"{S}.beats >= 2", timeout=10000)
        b5 = await page.evaluate(f"({{ beats: {S}.beats, sfx: __sfx.filter(k => k === 'beat').length, ms: {S}.beatMs, ms2: tun(2).beatMs }})")
        check('heartbeat: silent on level 1; on level 5 a soft "beat" sfx at the level\'s (shorter) interval', b1['beats'] == 0 and b1['sfx'] == 0 and b5['sfx'] >= 2 and b5['ms'] < b5['ms2'] < 1000, [b1, b5])

        # ===== edge lights: colour per level (pixel probe) =====
        async def edge(level):
            await page.evaluate(f"{S}.setLevel({level}); park(2300, 300, -200); {S}.debris.length = 0; particles.length = 0"); await frames(page, 3)
            return await page.evaluate("(() => { const { L, B } = corridor(), out = []; for (const z of [30, 60, 90, 120, 150, 180]) { const p = proj(L, B, z); for (const dx of [-1, 0, 1]) out.push(" + PIX + "(p.x + dx, p.y)); } return { px: out, col: __grasp.strike.ui.edgeCol }; })()")
        e1 = await edge(1); e6 = await edge(6)
        rb = lambda e: sum(p[0] - p[2] for p in e['px'])
        check('edge-light strips: cool blue on level 1, red-pink on level 6 (pixel probe along the floor edge)', rb(e1) < 0 and rb(e6) > 0 and e1['col'] != e6['col'] and e6['col'][0] > e6['col'][2], [rb(e1), rb(e6), e1['col'], e6['col']])
        await page.screenshot(path='tests/out/strike7_level6_desktop.png')
        FOG = "(async () => { const s = __grasp.strike, keep = s.walls.splice(0); await " + FRAMES + "; const v = vanish(), r = " + PIX + "(v.x + 30, v.y + 30); s.walls.push(...keep); return r; })()"  # the walls set aside for the probe: they stand in front of the vanishing point
        fog = await page.evaluate(FOG); await edge(1); fog1 = await page.evaluate(FOG)
        check('the far fog takes the level\'s colour on level 6 (redder than level 1)', fog[0] - fog[2] > fog1[0] - fog1[2], [fog1, fog])

        # ===== speed-up inside a level: every 5 returns in a row (no miss) the pace steps up 5%, within the level cap; 'Faster!' + a whoosh =====
        RET = "(() => { const s = __grasp.strike; s.setBallZ(__grasp.CONFIG.STRIKE_HIT_Z, innerWidth / 2, innerHeight / 2); strikeHit(s.ball, performance.now()); park(); return s.pace; })()"
        await page.evaluate(f"{S}.setLevel(2); park(); __sfx.length = 0"); p0 = await page.evaluate(f"{S}.pace")
        ps = [await page.evaluate(RET) for _ in range(5)]
        fu = await page.evaluate(f"({{ ui: {S}.ui.faster, ups: {S}.paceUps, sfx: __sfx.filter(k => k === 'faster').length, run: {S}.runReturns }})")
        check('4 returns: same pace; the 5th: pace x1.05, "Faster!" pulse + a whoosh', ps[:4] == [p0] * 4 and abs(ps[4] - p0 * 1.05) < 1e-9 and fu['ui'] and fu['sfx'] == 1 and fu['run'] == 5, [p0, ps, fu])
        await frames(page, 2); fb = await page.evaluate(f"{S}.ui.fasterBox"); hud = await page.evaluate(f"{S}.ui.hud")
        check('"Faster!" is drawn just under the top HUD row (at the start edge), inside the screen', fb and fb['text'] == 'Faster!' and hud['y'] + hud['h'] <= fb['y'] < hud['y'] + hud['h'] + 70 and fb['x'] >= 0 and fb['x'] + fb['w'] <= 1280, [fb, hud])
        await page.screenshot(path='tests/out/strike7_faster_desktop.png')
        ps2 = [await page.evaluate(RET) for _ in range(4)]
        await page.evaluate(f"(() => {{ const s = {S}; s.setBallZ(-__grasp.CONFIG.STRIKE_HIT_Z * 2, 30, 30); strikeMiss(s.ball, performance.now()); s.serve(); park(); }})()")
        ps3 = [await page.evaluate(RET) for _ in range(4)]
        check('a miss breaks the run: 4 returns + a miss + 4 returns = no speed-up', ps2 == [ps[4]] * 4 and ps3 == [ps[4]] * 4, [ps[4], ps2, ps3])
        cp = await page.evaluate(f"(() => {{ const s = {S}, T = tun(), cap = Math.min(T.maxSpeed, T.paceCap); s.pace = cap * 0.99; for (let i = 0; i < 20; i++) {{ s.setBallZ(150, innerWidth / 2, innerHeight / 2); strikeHit(s.ball, performance.now()); park(); }} return {{ pace: s.pace, cap, next: tun(3).pace }}; }})()")
        check('the speed-ups stop at the level cap (base + 75% of the step), below the next level\'s base', abs(cp['pace'] - cp['cap']) < 1e-9 and cp['pace'] < cp['next'], cp)
        await page.evaluate(f"{S}.ui.newsBox = null; {S}.setCleared(clearedAtLevel(3)); park()")
        lr = await page.evaluate(f"({{ run: {S}.runReturns, pace: {S}.pace, base: tun(3).pace }})")
        check('a level-up resets the run and the pace to the new level\'s base', lr['run'] == 0 and abs(lr['pace'] - lr['base']) < 1e-9, lr)
        he2 = await page.evaluate("I18N.he.hd_faster")
        check('"Faster!" in Hebrew: מהר יותר!', he2 == 'מהר יותר!', he2)

        # ===== perks multiply on top =====
        pk = await page.evaluate(f"""(() => {{ const s = {S}, r = {{}}; s.setLevel(5); park();
          s.offerPerks(); s.perkOffer = ['wide']; s.pickPerk(0); s.offerPerks(); s.perkOffer = ['magnet']; s.pickPerk(0); s.offerPerks(); s.perkOffer = ['slow']; s.pickPerk(0);
          r.t = tun(5); r.reach = s.perkStats().reach; r.magnet = magnetVal(); s.ball = null; s.serve(); r.serve = s.ball.speed; r.pace = s.pace; park(); return r; }})()""")
        check('perks on top of level 5: Wider Hands x1.2 reach (x the level reach), Magnet +0.15 on the faded base, Slow Start serves at 85% of the level-5 pace',
              abs(pk['reach'] - 1.2) < 1e-9 and abs(pk['magnet'] - (pk['t']['magnet'] + 0.15)) < 1e-9 and abs(pk['pace'] - pk['t']['pace']) < 1e-9 and abs(pk['serve'] - pk['t']['pace'] * 0.85) < 1e-9, pk)
        check('desktop: no page errors', not errs, errs); await ctx.close()

        # ===== Normal + the daily modifiers on top =====
        ctx, page, errs = await new_page(b); await page.evaluate("__grasp.setStrikeDiff('normal')"); await play_strike(page)
        await page.mouse.move(640, 300)
        nm = await page.evaluate(f"(() => {{ const s = {S}; s.setLevel(5); park(); return {{ t: s.tuning(), pace: s.pace, curve: tun(5).curve }}; }})()")
        check('Normal level 5: pace = 1.1 x 1.48, tuning diff normal', nm['t']['diff'] == 'normal' and abs(nm['pace'] - 1.1 * 1.48) < 1e-9, nm)
        dm = await page.evaluate(f"""(() => {{ const g = __grasp, s = {S}, r = {{}};
          g.daily.forceModifier = 'speedy'; g.startDaily(); r.l1 = s.pace; s.setLevel(5); r.diff = s.tuning().diff; r.pace = s.pace; r.base = s.levelBase; r.t = tun(5, 'normal');
          g.daily.forceModifier = 'bighands'; g.startDaily(); s.setLevel(5); r.reach = s.perkStats().reach; r.lreach = s.tuning().reach; r.pace2 = s.pace;
          g.daily.forceModifier = null; return r; }})()""")
        check('daily (always Normal) + "Speedy": the level-5 pace and levelBase are the Normal level-5 base x1.25; level 1 is 1.1 x1.25', dm['diff'] == 'normal' and abs(dm['pace'] - dm['t']['pace'] * 1.25) < 1e-9 and dm['base'] == dm['pace'] and abs(dm['l1'] - 1.375) < 1e-9, dm)
        check('daily "Big hands": reach x1.4 on top of the level reach; no Speedy = the plain level-5 base', abs(dm['reach'] - 1.4) < 1e-9 and dm['lreach'] < 1 and abs(dm['pace2'] - dm['t']['pace']) < 1e-9, dm)
        await page.evaluate("__grasp.setStrikeDiff('easy')")
        check('normal/daily: no page errors', not errs, errs); await ctx.close()

        # ===== phone screenshots: levels 1, 4, 8 in EN and HE =====
        for lang in ('en', 'he'):
            ctx, page, errs = await new_page(b, mobile=True, lang=lang); await play_strike(page, tap=True)
            await page.evaluate(f"(() => {{ const s = {S}; s.ui.levelBanner = {{ t: performance.now(), level: 1, goal: s.ui.levelBanner ? s.ui.levelBanner.goal : 5 }}; }})()")  # re-arm (a slow 3D start can outlive the first slide-in)
            await page.wait_for_function(f"{S}.ui.levelBanner && performance.now() > {S}.ui.levelBanner.t + 500", timeout=6000)
            await page.screenshot(path=f'tests/out/strike7_level1_{lang}.png')
            for lvl in (4, 8):  # (level 7 comes after world 1's boss now)
                await page.evaluate(f"(() => {{ const s = {S}; s.ui.newsBox = null; s.ui.levelBanner = null; s.setLevel({lvl - 1}); s.setCleared(clearedAtLevel({lvl})); park(); s.lives = s.maxLives; }})()")
                await page.wait_for_function(f"{S}.ui.newsBox && performance.now() > {S}.ui.levelBanner.t + 450", timeout=6000)
                nb = await page.evaluate(f"({{ box: {S}.ui.newsBox, news: {S}.ui.levelBanner.news, level: {S}.level }})")
                want = '  ·  '.join((HE_NEWS if lang == 'he' else EN_NEWS).get(k, '?') for k in nb['news'])
                ok = nb['level'] == lvl and nb['box']['scale'] > 0.85 and nb['box']['x'] >= 0 and nb['box']['x'] + nb['box']['w'] <= 360 and 'hd_faster' in nb['news'] and (lvl != 4 or nb['box']['text'] == want)
                check(f'{lang} phone: level {lvl} banner names what got harder, inside 360 px, legible (wraps to two lines rather than shrink)', ok, nb)
                await page.screenshot(path=f'tests/out/strike7_level{lvl}_{lang}.png')
            check(f'{lang} phone: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
