# Strike Adventure's real bosses: each world's stage 8 (8, 16, 24, 32, 40) is a boss fight (Brick Golem, Glass Queen, Steel Robot, Jungle King
# Kong, Lava Dragon). Covers: the boss is the stage (no walls), it walks / flies in with a roar, its name banner and the voice; the health bar under
# the hearts pill (its name, the world's colour, the phase notches); damage by tier; the weak point (x3 while it glows); the phases at 66% / 33%
# (a roar, a heart back, an angry face); every attack of every boss fires and can be countered: projectiles slapped back hurt it (missed: a heart),
# the shield only a SUPER / PERFECT hit breaks, summoned mini-walls (in front of it, no stage progress), the charge (a hit knocks it back; else a
# heart and a slam), the spinning arm / tail (a ball meeting it is blocked; one past it hurts); a ball beside the body flies past; the victory (the
# explosion, 'Victory!', the stage clear, coins, the trip to the next world, the card) and the fail card (the boss's hp left, Try again); the time
# to beat each boss with a simulated careful child and a good player (in sane ranges); Endless keeps its boss wall; EN / HE names; 2D + 3D.
# Screenshots tests/out/boss_w{1..5}_{2d,2d_phase3,3d}.png, boss_w1_he.png, boss_victory.png, boss_fail.png, boss_wall.png, boss_charge.png.
exec(open('tests/test_challenge.py').read().split('async def main')[0])
B = "__grasp.boss"
BOSSES = {8: ('golem', 'Brick Golem', 'גולם הלבנים'), 16: ('queen', 'Glass Queen', 'מלכת הזכוכית'), 24: ('robot', 'Steel Robot', 'רובוט הפלדה'), 32: ('kong', 'Jungle King Kong', 'קינג קונג של הג׳ונגל'), 40: ('dragon', 'Lava Dragon', 'דרקון הלבה')}

async def frames(page, n=2):
    for _ in range(n): await page.evaluate("new Promise(r => requestAnimationFrame(() => r()))")

async def boss_stage(page, n, enter=True, click=False):  # Adventure stage n (all open) with the mouse; the boss up; calm (it attacks only when told) once it has walked in
    await page.evaluate("profile.adv.unlocked = 40; saveProfile(); setInputPref('mouse')")
    if await page.evaluate("mode === 'none'"):
        await page.evaluate("openAdvMap({ how: 'mouse' })"); await page.click(f'.anode[data-n="{n}"]')
    else: await page.evaluate(f"{A}.start({n})")
    await page.wait_for_function(f"{A}.on && {A}.stage === {n} && {A}.phase === 'play' && {B}.b && mode === 'mouse'", timeout=10000)
    await page.evaluate(f"{S}.noRally = true; {S}.noTiming = true; __grasp.CONFIG.STRIKE_PU_RATE = 0; {S}.guestEvery = 0")
    if enter: await page.evaluate(f"{B}.enter(); {B}.calm(true); park(); {B}.weak(false)")

HITS = """((tier, x, y, perf) => { const r = __grasp.boss.ball(tier, x, y, perf); park(); return r; })"""
CENTER = "(() => { const s = __grasp.boss.state(); return [s.x, s.y + s.hh * 0.45]; })()"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ===== B1: the entrance (world 1, the natural walk-in): no walls, the roar, the banner, the voice, the bar =====
        ctx, page, errs = await fresh(b)
        await boss_stage(page, 8, enter=False)
        pl = await page.evaluate(f"(() => {{ const P = {A}.plan(8); return {{ boss: P.boss, walls: P.walls, kinds: P.kinds }}; }})()")
        check('stage 8 is a boss stage with no walls of its own (the fight is the stage)', pl['boss'] and pl['walls'] == 0 and pl['kinds'] == [], pl)
        st0 = await page.evaluate(f"({{ s: {B}.state(), walls: {S}.walls.length, goal: {S}.goal, banner: {S}.ui.levelBanner && {S}.ui.levelBanner.boss }})")
        check('the Brick Golem is there from the start, beyond the far end (it walks in after the stage banner); full hp; no walls', st0['s']['kind'] == 'golem' and st0['s']['hp'] == st0['s']['maxHp'] == st0['s']['def']['hp'] and st0['s']['z'] > 2400 and st0['walls'] == 0 and st0['banner'], st0)
        check('the stage banner says "Beat the boss!"', await page.evaluate("t('stageGoalBoss')") == 'Beat the boss!' and await page.evaluate("I18N.he.stageGoalBoss") == 'נצחו את הבוס!')
        await page.evaluate("__sfx.length = 0; __grasp.grippy.cool()")
        await page.wait_for_function(f"{B}.state().entered", timeout=8000)
        await page.wait_for_function(f"{S}.ui.rbIntroBox", timeout=4000)
        en = await page.evaluate(f"({{ s: {B}.state(), sfx: __sfx.slice(), intro: {S}.ui.rbIntroBox, voice: __grasp.grippy.last && __grasp.grippy.last.event, bar: {S}.ui.bossBar, hud: {S}.ui.hud, accent: WORLDS[0].accent }})")
        check('it walks in to its spot (z ~ 0.32 of the corridor) with a roar', abs(en['s']['z'] - en['s']['zHome']) < 2 and abs(en['s']['zHome'] - 768) < 1 and 'roar' in en['sfx'], [en['s']['z'], en['sfx'][:6]])
        check('its name drops in: "Brick Golem" (the banner), and the voice line for a boss', en['intro'] and en['intro']['name'] == 'Brick Golem' and en['voice'] == 'boss', [en['intro'], en['voice']])
        bar = en['bar']; hud = en['hud']
        check('the health bar: thin, at the top under the hearts pill, its name, the world\'s colour, full, inside the screen', bar and bar['name'] == 'Brick Golem' and bar['col'] == en['accent'] and bar['frac'] == 1 and bar['y'] >= hud['y'] + hud['h'] and bar['y'] < hud['y'] + hud['h'] + 20 and bar['barH'] <= 10 and bar['x'] >= 0 and bar['x'] + bar['w'] <= 1280, [bar, hud])
        await page.wait_for_timeout(600); await page.screenshot(path='tests/out/boss_intro.png')
        check('B1: no page errors', not errs, errs); await ctx.close()

        # ===== B2: every boss: damage, the weak point, every attack countered, the phases (desktop EN) =====
        ctx, page, errs = await fresh(b)
        for n, (kind, name, name_he) in BOSSES.items():
            w = n // 8
            await boss_stage(page, n)
            s = await page.evaluate(f"{B}.state()")
            check(f'W{w}: stage {n} brings the {name} ({kind}), {s["maxHp"]} hp (Easy), a {"flying" if s["def"]["fly"] else "ground"} boss', s['kind'] == kind and s['name'] == name and s['hp'] == s['maxHp'] and s['phase'] == 1 and s['def']['fly'] == (kind == 'dragon'), s['kind'])
            c = await page.evaluate(CENTER)
            r1 = await page.evaluate(f"{HITS}('medium', {c[0]}, {c[1]})")
            r2 = await page.evaluate(f"{HITS}('super', {c[0]}, {c[1]})")
            check(f'W{w}: a ball on its body hurts it by tier (medium 2, SUPER 4) and comes back', r1['hit'] and r1['dmg'] == 2 and r1['dir'] == 1 and r2['dmg'] == 4, [r1, r2])
            wk = await page.evaluate(f"(() => {{ const p = {B}.weak(true), r = {HITS}('medium', p.x, p.y); const st = {B}.state(); return {{ r, on: st.weakOn, n: st.weakHits }}; }})()")
            check(f'W{w}: the weak point while it glows: x3 (a medium hit does 6), then it dims', wk['r']['dmg'] == 6 and not wk['on'] and wk['n'] == 1, wk)
            wo = await page.evaluate(f"(() => {{ const p = {B}.weakPos(); return {HITS}('medium', p.x, p.y); }})()")
            check(f'W{w}: the same spot while it is dim: x1', wo['dmg'] == 2, wo)
            if kind != 'dragon':
                ms = await page.evaluate(f"(() => {{ const s = {B}.state(), L = corridor().L; return {HITS}('hard', L + ballR() * 1.05, s.y - s.hh * 0.9); }})()")
                check(f'W{w}: a ball beside its body flies past (no damage, on to the far wall)', not ms['hit'] and ms['dmg'] == 0 and ms['passed'], ms)
            atks = s['def']['atk'][2]
            for a in atks:
                await page.evaluate(f"(() => {{ const b = {B}.b; b.shield = null; b.arm = null; b.charge = null; b.z = b.zHome; {S}.shots.length = 0; for (const w of {S}.walls.slice()) if (w.summon) wallDown(w, performance.now()); }})()")
                if a == 'shot':
                    f = await page.evaluate(f"(() => {{ __sfx.length = 0; {B}.fire('shot'); const q = {S}.shots.find(q => q.boss); return q && {{ kind: q.kind, z: q.z, dir: q.dir, sfx: __sfx.slice() }}; }})()")
                    hp0 = await page.evaluate(f"{B}.state().hp")
                    await page.evaluate(f"(() => {{ const q = {S}.shots.find(q => q.boss); deflectShot(q, performance.now()); }})()")
                    await page.wait_for_function(f"{B}.state().returned >= 1", timeout=6000)
                    rt = await page.evaluate(f"{B}.state()")
                    check(f'W{w} shot: it throws its {f and f["kind"]} at the player; slapped back, it flies home and hurts it (-3)', f and f['dir'] == 1 and f['kind'] == {'golem': 'rock', 'queen': 'shard', 'robot': 'rocket', 'kong': 'barrel', 'dragon': 'fire'}[kind] and rt['hp'] == hp0 - 3 and rt['countered'].get('shot') == 1, [f, hp0, rt['hp']])
                    await page.evaluate(f"(() => {{ {S}.lives = 3; const n0 = {A}.lost; {B}.fire('shot'); const q = {S}.shots.find(q => q.boss && !q.dead && q.dir > 0); q.z = -200; window.__lost0 = n0; }})()")
                    await page.mouse.move(5, 790); await page.wait_for_timeout(150)
                    await page.wait_for_function(f"{A}.lost > window.__lost0", timeout=4000)
                    check(f'W{w} shot: missed, it costs a heart', await page.evaluate(f"{S}.lives") == 2)
                    await page.evaluate("park()")
                elif a == 'shield':
                    sh = await page.evaluate(f"""(() => {{ {B}.fire('shield'); const on = {B}.state().shield, c = {CENTER}, a = {HITS}('medium', c[0], c[1]), b2 = {HITS}('hard', c[0], c[1]), still = {B}.state().shield, s = {HITS}('super', c[0], c[1]), st = {B}.state();
                      {B}.fire('shield'); const p = {HITS}('medium', c[0], c[1], true), st2 = {B}.state(); return {{ on, a, b2, still, s, off: !st.shield, blocked: st.blocked, p, off2: !st2.shield, n: st2.countered.shield }}; }})()""")
                    check(f'W{w} shield: it raises a shield; medium and hard hits are blocked (no damage); a SUPER breaks it and hurts; a PERFECT one breaks it too', sh['on'] and sh['a']['dmg'] == 0 and sh['b2']['dmg'] == 0 and sh['still'] and sh['blocked'] == 2 and sh['s']['dmg'] == 4 and sh['off'] and sh['p']['dmg'] == 2 and sh['off2'] and sh['n'] == 2, sh)
                elif a == 'wall':
                    wl = await page.evaluate(f"""(() => {{ const p0 = {S}.progress; {B}.fire('wall'); const s = {B}.state(), ws = {S}.walls.filter(w => w.summon && w.left > 0); return {{ n: ws.length, z: ws.map(w => w.z), bz: s.z, left: ws.map(w => w.left), p0 }}; }})()""")
                    check(f'W{w} wall: it summons mini-walls in front of itself (a few bricks over its body)', wl['n'] >= 1 and all(z < wl['bz'] for z in wl['z']) and all(0 < l < 30 for l in wl['left']), wl)
                    if n == 32: await frames(page, 3); await page.screenshot(path='tests/out/boss_wall.png')
                    aw = await page.evaluate(f"(() => {{ const c = {CENTER}, bl = {S}.ball; bl.x = c[0]; bl.y = c[1]; bl.z = 10; bl.dir = -1; bl.speed = {S}.pace; const t = aimWall(bl); park(); return t; }})()")
                    check(f'W{w} wall: a ball hit at the boss meets the mini-wall first', aw['id'] != 'boss' and aw['id'] != 'far', aw)
                    br = await page.evaluate(f"""(() => {{ for (const w of {S}.walls.filter(w => w.summon)) {{ for (const k of w.bricks) if (k.alive) {{ k.alive = false; k.hp = 0; w.left--; }} wallDown(w, performance.now()); }} return {{ left: {S}.walls.filter(w => w.summon).length, c: {B}.state().countered.wall, p: {S}.progress, phase: {A}.phase }}; }})()""")
                    check(f'W{w} wall: broken, the mini-walls are gone (no stage progress, the fight goes on)', br['left'] == 0 and br['c'] >= 1 and br['p'] == wl['p0'] and br['phase'] == 'play', br)
                elif a == 'charge':
                    await page.evaluate(f"{B}.fire('charge')"); z0 = await page.evaluate(f"{B}.state().z"); await page.wait_for_timeout(400); z1 = await page.evaluate(f"{B}.state().z")
                    if n == 24: await page.screenshot(path='tests/out/boss_charge.png')
                    kb = await page.evaluate(f"(() => {{ const c = {CENTER}, r = {HITS}('medium', c[0], c[1]), s = {B}.state(); return {{ r, charge: s.charge, knocks: s.knocks, z: s.z, n: s.countered.charge }}; }})()")
                    check(f'W{w} charge: it charges at the player; a hit knocks it back', z1 < z0 - 5 and kb['r']['dmg'] > 0 and not kb['charge'] and kb['knocks'] == 1 and kb['z'] > z1 and kb['n'] == 1, [z0, z1, kb])
                    await page.evaluate(f"(() => {{ {S}.lives = 3; window.__lost0 = {A}.lost; {B}.fire('charge'); {B}.b.charge.v = 1.5; }})()")
                    await page.wait_for_function(f"{B}.state().slams >= 1", timeout=5000)
                    sl = await page.evaluate(f"({{ lives: {S}.lives, lost: {A}.lost - window.__lost0, s: {B}.state() }})")
                    check(f'W{w} charge: not stopped, it slams into the player: a heart, and it backs off', sl['lives'] == 2 and sl['lost'] == 1 and not sl['s']['charge'], sl)
                    await page.evaluate("park()")
                elif a == 'arm':
                    ar = await page.evaluate(f"""(() => {{ const b = {B}.b; {B}.fire('arm'); b.arm.w = 0; b.arm.a = Math.PI / 2 + 0.3; const segs = {B}.arm(), s0 = segs[0], q = 0.62, x = s0.x0 + (s0.x1 - s0.x0) * q, y = s0.y0 + (s0.y1 - s0.y0) * q;
                      const blk = {HITS}('hard', x, y); const s = {B}.state(); let best = null; for (let i = -6; i <= 6; i++) for (let j = -6; j <= 6; j++) {{ const px = s.x + i * s.hw / 7, py = s.y + j * s.hh / 7; if (!rbInBody(b, px, py, 0)) continue; const d = Math.min(...{B}.arm().map(g => segDist(px, py, g) - g.w / 2)); if (!best || d > best.d) best = {{ x: px, y: py, d }}; }}
                      const ok = {HITS}('hard', best.x, best.y); return {{ n: segs.length, blk, ok, armBlocks: {B}.state().armBlocks, d: best.d }}; }})()""")
                    check(f'W{w} arm: a spinning {"tail" if kind == "dragon" else "arm"} at its depth blocks a ball that meets it (no damage); a ball past it hurts', ar['n'] >= 1 and ar['blk']['hit'] and ar['blk']['dmg'] == 0 and ar['armBlocks'] == 1 and ar['ok']['dmg'] == 3, ar)
                    await page.evaluate(f"{B}.b.arm.w = 0.002")
            fired = await page.evaluate(f"{B}.state().fired")
            check(f'W{w}: every attack of its last phase fired ({", ".join(atks)})', all(fired.get(a, 0) >= 1 for a in atks), fired)
            # the phases: 66% and 33% (a roar, a heart back, more attacks); the art: cracks, then pieces off, sparks and an angry face
            await page.evaluate(f"(() => {{ const b = {B}.b; b.shield = null; b.arm = null; b.charge = null; b.z = b.zHome; {S}.shots.length = 0; for (const w of {S}.walls.slice()) if (w.summon) wallDown(w, performance.now()); }})()")
            ph = await page.evaluate(f"""(() => {{ const b = {B}.b, c = {CENTER}; {S}.lives = 1; __sfx.length = 0; b.hp = Math.floor(b.maxHp * 2 / 3) + 1; {B}.ball('medium', c[0], c[1]); const p2 = {{ ph: b.phase, lives: {S}.lives, roar: __sfx.includes('roar'), fl: {S}.floaters.map(f => f.text) }};
              b.hp = Math.floor(b.maxHp / 3) + 1; {S}.lives = 2; {B}.ball('medium', c[0], c[1]); const r = {{ p2, p3: b.phase, angry: b.angry, lives: {S}.lives, atk: [b.def.atk[0].length, b.def.atk[1].length, b.def.atk[2].length], ms: b.def.atkMs }}; park(); return r; }})()""")
            check(f'W{w} phases: under 66% phase 2 (a roar, "It\'s angry!", the hearts back: "+2 ❤"), under 33% phase 3 (angry, the hearts back again); more attacks and faster each phase',
                  ph['p2']['ph'] == 2 and ph['p2']['roar'] and ph['p2']['lives'] == 3 and "It's angry!" in ph['p2']['fl'] and '+2 ❤' in ph['p2']['fl'] and ph['p3'] == 3 and ph['angry'] and ph['lives'] == 3 and ph['atk'][0] < ph['atk'][2] and ph['ms'][0] > ph['ms'][1] > ph['ms'][2], ph)
            await page.evaluate(f"(() => {{ {B}.weak(true); {S}.lives = 40; }})()"); await frames(page, 3); await page.wait_for_timeout(120)
            ub = await page.evaluate(f"({{ ui: {S}.ui.boss, bar: {S}.ui.bossBar }})")
            check(f'W{w}: drawn in phase 3 (its body box inside the corridor, the weak point marked on it), the bar at a third', ub['ui'] and ub['ui']['kind'] == kind and ub['ui']['w'] > 100 and ub['ui']['weak']['on'] and ub['ui']['x'] < ub['ui']['weak']['x'] < ub['ui']['x'] + ub['ui']['w'] and ub['bar']['phase'] == 3 and ub['bar']['frac'] < 0.34, ub)
            await page.screenshot(path=f'tests/out/boss_w{w}_2d_phase3.png')
            await page.evaluate(f"(() => {{ const b = {B}.b; b.hp = b.maxHp; b.phase = 1; b.angry = false; {B}.weak(true); if (b.def.arm) {{ {B}.fire('arm'); b.arm.w = 0; b.arm.a = 0.6; }} if (b.def.atk[2].includes('shield') && b.n % 2 === 0) {B}.fire('shield'); }})()")
            await frames(page, 3); await page.wait_for_timeout(300); await page.screenshot(path=f'tests/out/boss_w{w}_2d.png')
            check(f'W{w}: no page errors', not errs, errs)
        check('B2: no page errors', not errs, errs); await ctx.close()

        # ===== B3: the victory (world 1): the explosion, 'Victory!', the stage clear, coins, the trip to world 2, the card =====
        ctx, page, errs = await fresh(b)
        await boss_stage(page, 8)
        c0 = await page.evaluate("profile.coins")
        await page.evaluate("__sfx.length = 0")
        vi = await page.evaluate(f"(() => {{ const b = {B}.b, c = {CENTER}; b.hp = 3; const r = {B}.ball('super', c[0], c[1]); return {{ r, boss: !!{S}.boss, last: {S}.lastBoss, down: !!{S}.ui.rbDown, sfx: __sfx.slice(), phase: {A}.phase, res: {A}.result, travel: {A}.travel, bosses: {S}.bosses }}; }})()")
        check('the last hit: it blows up (boom, the boss-down blast), the stage clears, the trip to world 2 starts', vi['r']['dmg'] >= 3 and not vi['boss'] and vi['down'] and 'bossdown' in vi['sfx'] and 'boom' in vi['sfx'] and vi['phase'] == 'clear' and vi['travel'] and vi['travel']['to'] == 2 and vi['bosses'] == 1, vi)
        check('the clear: 3 stars (no heart lost), the boss in the result, a first clear pays 3 + 3 stars + 5 for a boss', vi['res']['clear'] and vi['res']['boss'] and vi['res']['rb']['kind'] == 'golem' and vi['res']['stars'] == 3 and vi['res']['coins'] == 11, vi['res'])
        await page.wait_for_function(f"{S}.ui.victoryBox && {S}.ui.victoryBox.a > 0.9", timeout=4000)
        await page.screenshot(path='tests/out/boss_victory.png')
        check('"Victory!" and "Brick Golem defeated!" over the burst', await page.evaluate("t('bossVictory')") == 'Victory!' and await page.evaluate("t('bossDefeated', { b: t('bn_golem') })") == 'Brick Golem defeated!')
        await page.wait_for_function(f"{S}.over && {A}.phase === 'card' && {S}.ui.buttons && {S}.ui.buttons.next", timeout=12000); await page.wait_for_timeout(1400)
        cd = await page.evaluate(f"({{ btn: Object.keys({S}.ui.buttons), card: {S}.ui.card, labels: {S}.ui.advLabels, world: {S}.world, coins: profile.coins - {c0} }})")
        check('the card: "World 1 done!", Next / Play again / Map / Challenge a friend, inside the screen; world 2 now', set(cd['btn']) == {'next', 'retry', 'map', 'duel'} and cd['card']['y'] + cd['card']['h'] <= 800 and cd['world'] == 2 and cd['coins'] >= 11, cd)
        await page.screenshot(path='tests/out/boss_victory_card.png')
        check('B3: no page errors', not errs, errs); await ctx.close()

        # ===== B4: the fail (world 2): the card shows how much of the boss was left; Try again brings it back at full hp =====
        ctx, page, errs = await fresh(b, mobile=True)
        await boss_stage(page, 16)
        await page.evaluate(f"(() => {{ const b = {B}.b; b.hp = Math.round(b.maxHp * 0.4); {S}.lives = 3; }})()")
        await page.evaluate(f"{A}.failTest()")
        await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.retry && {S}.ui.advBoss", timeout=8000); await page.wait_for_timeout(600)
        fl = await page.evaluate(f"({{ r: {A}.result, ab: {S}.ui.advBoss, btn: Object.keys({S}.ui.buttons), labels: {S}.ui.advLabels, card: {S}.ui.card }})")
        check('fail: "So close!" with "Glass Queen: 40% left" and its bar; Try again / Map / Challenge a friend; the card fits the phone', not fl['r']['clear'] and fl['r']['rb']['left'] == 40 and fl['ab']['left'] == 40 and fl['labels']['retry'] == 'Try again' and set(fl['btn']) == {'retry', 'map', 'duel'} and fl['card']['y'] + fl['card']['h'] <= 740, fl)
        await page.screenshot(path='tests/out/boss_fail.png')
        await page.evaluate(f"endCardAction('retry', performance.now())")
        await page.wait_for_function(f"{A}.phase === 'play' && {B}.b", timeout=6000)
        rt = await page.evaluate(f"({{ s: {B}.state(), over: {S}.over, lives: {S}.lives }})")
        check('Try again: the Glass Queen back at full hp, a fresh stage', rt['s']['hp'] == rt['s']['maxHp'] and rt['s']['kind'] == 'queen' and not rt['over'] and rt['lives'] == 3, rt)
        check('B4: no page errors', not errs, errs); await ctx.close()

        # ===== B5: the time to beat each boss (a simulated careful child and a good player, phone, Easy) =====
        ctx, page, errs = await fresh(b, mobile=True)
        await boss_stage(page, 8, enter=False)
        await page.evaluate(f"{S}.noRally = false; {S}.noTiming = false")  # (the real game: the rally on)
        times = {}
        for n in (8, 16, 24, 32, 40):
            for pl, seeds in (('kid', (1, 2, 3, 4)), ('good', (1, 2, 3))):
                if pl == 'kid' and n in (24, 32): continue
                ts, segs = [], []
                for sd in seeds:
                    await page.evaluate(f"{A}.start({n})"); await page.wait_for_function(f"{A}.stage === {n} && {A}.phase === 'play' && {B}.b", timeout=10000)
                    r = await page.evaluate(f"{B}.sim({{ player: '{pl}', seed: {sd}, maxS: 600 }})")
                    ts.append(r['t'] if r['t'] else 999); segs.append(r['segLost'])
                med = sorted(ts)[len(ts) // 2] if len(ts) % 2 else sum(sorted(ts)[len(ts) // 2 - 1:len(ts) // 2 + 1]) / 2
                times[(n, pl)] = (med, segs)
                print(f'  measured: stage {n} {pl}: {ts} s (median {med}), hearts lost per phase {segs}')
        k1, g1, g5, k5 = times[(8, 'kid')][0], times[(8, 'good')][0], times[(40, 'good')][0], times[(40, 'kid')][0]
        kseg = times[(8, 'kid')][1]; survive = sum(1 for sg in kseg if all(x < 3 for x in sg))
        check(f'world 1: a careful child beats the Brick Golem in ~45-75 s (median {k1} s) and usually survives it (hearts lost per phase {kseg}: 3 hearts, all back at each phase)', 38 <= k1 <= 80 and survive >= 2, times[(8, 'kid')])
        check(f'world 1: a good player is quicker (median {g1} s)', 15 <= g1 < k1, [g1, k1])
        check(f'each world takes longer for a good player (W1..W5: {[times[(n, "good")][0] for n in (8, 16, 24, 32, 40)]} s)', all(times[(a, 'good')][0] <= times[(b2, 'good')][0] + 8 for a, b2 in ((8, 16), (16, 24), (24, 32), (32, 40))))
        check(f'world 5: the Lava Dragon is hard: ~90-150 s for a good player (median {g5} s), longer for a child ({k5} s)', 75 <= g5 <= 165 and k5 > g5, [g5, k5])
        check('B5: no page errors', not errs, errs); await ctx.close()

        # ===== B6: Endless keeps its boss wall; EN / HE names; HE phone screenshot =====
        ctx, page, errs = await fresh(b); await endless(page)
        eb = await page.evaluate(f"(() => {{ const s = {S}; s.spawnBoss(1); return {{ real: !!s.boss.real, hp: s.boss.hp, bb: !!{B}.b }}; }})()")
        await frames(page, 3)
        check('Endless keeps its boss wall (a face on a brick wall every world), not a real boss', not eb['real'] and not eb['bb'] and eb['hp'] > 0 and await page.evaluate(f"!!({S}.ui.boss && {S}.ui.boss.eyes)"), eb)
        nm = await page.evaluate("(() => ['golem', 'queen', 'robot', 'kong', 'dragon'].map(k => [I18N.en['bn_' + k], I18N.he['bn_' + k]]))()")
        check('every boss has its name in EN and HE', [tuple(x) for x in nm] == [(v[1], v[2]) for v in BOSSES.values()], nm)
        keys = ['bossOfWorld', 'bossBlocked', 'bossShield', 'bossShieldBroken', 'bossWeak', 'bossReturned', 'bossKnock', 'bossCharge', 'bossPhase2', 'bossPhase3', 'bossVictory', 'bossDefeated', 'bossLeft', 'bossWall', 'bossShieldTip', 'bossWeakTip', 'bossShotTip']
        miss = await page.evaluate("(ks => ['en', 'he'].flatMap(l => ks.filter(k => !I18N[l][k] || (l === 'he' && I18N.he[k] === I18N.en[k])).map(k => l + ':' + k)))(" + json.dumps(keys) + ")")
        check('I18N: every boss line in EN and HE', not miss, miss)
        check('B6: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, mobile=True, he=True)
        await boss_stage(page, 8, enter=False)
        await page.wait_for_function(f"{S}.ui.rbIntroBox && {S}.ui.rbIntroBox.a > 0.9", timeout=8000)
        he = await page.evaluate(f"({{ intro: {S}.ui.rbIntroBox.name, bar: {S}.ui.bossBar && {S}.ui.bossBar.name, W: innerWidth, b: {S}.ui.bossBar }})")
        check('HE phone: "גולם הלבנים" on the banner and the bar; the bar inside the screen', he['intro'] == 'גולם הלבנים' and he['bar'] == 'גולם הלבנים' and he['b']['x'] >= 0 and he['b']['x'] + he['b']['w'] <= he['W'], he)
        await page.screenshot(path='tests/out/boss_w1_he.png')
        check('HE: no page errors', not errs, errs); await ctx.close()

        # ===== B7: 3D: each boss on a textured plane at its depth (the WebGL renderer) =====
        ctx, page, errs = await fresh(b, mobile=True, gfx="{ pr: 0.35, shadows: false, auto: false }")
        for n, (kind, name, _) in BOSSES.items():
            w = n // 8
            await boss_stage(page, n)
            try: await page.wait_for_function(f"{S}.gfx === '3d'", timeout=30000); g3 = True
            except Exception: g3 = False
            check(f'3D W{w}: the WebGL renderer is up', g3, await page.evaluate(f"{S}.gfxInfo"))
            if not g3: break
            await page.evaluate(f"(() => {{ const b = {B}.b; {B}.weak(true); if (b.def.arm) {{ {B}.fire('arm'); b.arm.w = 0; b.arm.a = 0.6; }} }})()")
            await page.wait_for_timeout(500)
            v = await page.evaluate(f"(() => {{ const u = {S}.ui.boss; return {{ vis: !!(G3.rb && G3.rb.visible), u, px: {S}.pixel(Math.round(u.cx), Math.round(u.cy)) }}; }})()")
            await page.evaluate(f"window.__bb = {S}.boss; {S}.boss = null"); await page.wait_for_timeout(250)
            v2 = await page.evaluate(f"(() => {{ const u = {json.dumps(v['u'])}; return {{ vis: !!(G3.rb && G3.rb.visible), px: {S}.pixel(Math.round(u.cx), Math.round(u.cy)) }}; }})()")
            await page.evaluate(f"{S}.boss = window.__bb"); await page.wait_for_timeout(300)
            check(f'3D W{w}: the {name} drawn on a plane at its depth (its pixels on screen; gone when it is away)', v['vis'] and not v2['vis'] and sum(abs(a - c) for a, c in zip(v['px'], v2['px'])) > 40, [v['px'], v2['px']])
            await page.screenshot(path=f'tests/out/boss_w{w}_3d.png')
        check('B7: no page errors', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
