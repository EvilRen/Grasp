# Strike v4 ("challenge"): hard hits are no 'break everything' button any more, aim matters, the Adventure ramps up and there is a score to chase.
# Covers: the bounded blast (soft 1 / medium 2 / hard a plus / SUPER the 3x3 / fireball a radius-2 diamond) and the bounce back off the wall
# it hit (never through it, never a second wall in a flight); the aim (the landing point follows the hit's direction); armored bricks (cracks
# per hit), weak spots (a row + a column), keystones (what rests on them falls), gold (a bonus); the overheat (heats up, forced soft, cools
# down); turret shots (slapped away vs a heart lost); two-ball stages; walls closing in; the difficulty ramp (world 1 gentle vs world 2+); the
# combo (x2 .. x8, reset on a miss, a pop by the pill); the score on the clear card, the stage's best, NEW RECORD!, ranks (Bronze .. Legend)
# on the card and the map; the profile's validation. EN / HE, desktop / phone, 2D / 3D screenshots in tests/out/challenge_*.png.
exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
S = "__grasp.strike"; A = "__grasp.adventure"
SFX_JS = "(() => { window.__sfx = []; window.__sfxa = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); __sfxa.push([k, a]); o(k, a); }; })()"
SPEECH = ("window.__spoken = []; try { const ss = { speaking: false, speak(u) { __spoken.push({ text: u.text, lang: u.lang }); setTimeout(() => { try { u.onend && u.onend(); } catch (e) {} }, 300); }, cancel() {}, getVoices() { return [{ lang: 'en-US', name: 'E' }, { lang: 'he-IL', name: 'H' }]; } };"
          " Object.defineProperty(window, 'speechSynthesis', { configurable: true, get: () => ss }); } catch (e) {}")
HELP = """
window.park = (z = 2300, x = 30, y = 30) => { const s = __grasp.strike; s.setBallZ(z, x, y); s.ball.speed = 0; s.lives = 40; };
window.plainWall = (z = 900) => { const s = __grasp.strike; s.walls.length = 0; const w = s.spawnWall('brick', z); for (const k of w.bricks) { k.weak = k.key = k.gold = k.turret = k.armor = false; k.pu = null; k.hp = k.max = 1; } return w; };
window.ballAt = (w, col, row, tier, fire) => { const s = __grasp.strike, c = brickCell(w, col, row), b = s.ball; b.dir = -1; b.x = b.lx = c.x; b.y = b.ly = c.y; b.z = w.z - 1; b.vx = b.vy = 0; b.spin = 0; b.tier = tier; b.super = tier === 'super'; b.fire = !!fire; b.guest = null; return b; };
window.blast = (tier, col, row, fire) => { const s = __grasp.strike, w = plainWall(), b = ballAt(w, col, row, tier, fire), n0 = w.left; const out = smashWall(w, b, performance.now()); if (out === 'bounce') bounceOffWall(b, w); b.fire = false; // (as ballTick does)
  return { out, n: n0 - w.left, dir: b.dir, bz: b.z, wz: w.z, gone: w.bricks.filter(k => !k.alive).map(k => [k.col, k.row]), cols: w.cols, rows: w.rows }; };
0;
"""

async def fresh(b, mobile=False, he=False, init='', gfx=None):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + SPEECH + "localStorage.setItem('lang','" + ('he' if he else 'en') + "');" + (f"window.__graspGfx = {gfx};" if gfx else '') + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(700)
    await page.evaluate(HELP); await page.evaluate(SFX_JS)
    return ctx, page, errs

async def endless(page):  # the Endless run with the mouse, the ball parked far away
    await page.click('.modes button[data-mode=strike]'); await page.click('#advEndless')
    await page.wait_for_function(f"gameMode === 'strike' && mode === 'mouse' && {S}.walls.length === 4", timeout=10000)
    await page.evaluate(f"__grasp.CONFIG.STRIKE_PU_RATE = 0; {S}.guestEvery = 0; park()")

async def stage(page, n):  # Adventure stage n with the mouse (all stages open), waiting for its walls
    await page.evaluate(f"profile.adv.unlocked = 40; saveProfile(); setInputPref('mouse')")
    if await page.evaluate("mode === 'none'"):
        await page.evaluate(f"openAdvMap({{ how: 'mouse' }})"); await page.click(f'.anode[data-n="{n}"]')
    else: await page.evaluate(f"{A}.start({n})")
    await page.wait_for_function(f"{A}.on && {A}.stage === {n} && {A}.phase === 'play' && {S}.walls.length > 0 && mode === 'mouse'", timeout=10000)

def shape_n(col, row, cols, rows, shape):  # bricks of a blast shape that fit on the grid
    n = 0
    for c in range(cols):
        for r in range(rows):
            dc, dr = abs(c - col), abs(r - row)
            if (shape == 2 and dc + dr <= 1) or (shape == 3 and dc <= 1 and dr <= 1) or (shape == 4 and (dc + dr <= 2 or (dc <= 1 and dr <= 1))) or (shape == 0 and dc + dr == 0): n += 1
    return n

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ===== A1: the bounded blast and the bounce =====
        ctx, page, errs = await fresh(b); await endless(page)
        await page.evaluate(f"{S}.noSpecials = true")
        r = {t: await page.evaluate(f"blast('{t}', 1, 2)") for t in ('soft', 'medium', 'hard', 'super')}; r['fire'] = await page.evaluate("blast('soft', 1, 2, true)")
        cols, rows = r['soft']['cols'], r['soft']['rows']
        check('soft: a chip, just the brick it hits (1)', r['soft']['n'] == 1 and r['soft']['gone'] == [[1, 2]], r['soft'])
        check('medium: the brick + one neighbour (2)', r['medium']['n'] == 2 and [1, 2] in r['medium']['gone'] and all(abs(c - 1) + abs(rr - 2) <= 1 for c, rr in r['medium']['gone']), r['medium'])
        check('hard: a plus round the impact (5)', r['hard']['n'] == shape_n(1, 2, cols, rows, 2) == 5, r['hard'])
        check('SUPER: the 3x3 round the impact (9), nothing outside it', r['super']['n'] == 9 and all(abs(c - 1) <= 1 and abs(rr - 2) <= 1 for c, rr in r['super']['gone']), r['super'])
        check('fireball: bounded too, a radius-2 diamond (' + str(shape_n(1, 2, cols, rows, 4)) + ' here)', r['fire']['n'] == shape_n(1, 2, cols, rows, 4) and r['fire']['n'] < cols * rows, r['fire'])
        check('every tier bounces back off the wall it hit (never through it), a ball\'s depth in front of it', all(q['out'] == 'bounce' and q['dir'] == 1 and q['bz'] < q['wz'] for q in r.values()), {k: (q['out'], q['dir']) for k, q in r.items()})
        # a real SUPER flight: one wall, never two
        await page.evaluate(f"(() => {{ const s = {S}; s.walls.length = 0; [0, 1, 2, 3].forEach(i => s.spawnWall('brick', wallSlotZ(i))); s.heat = 0; }})()")
        await page.mouse.move(640, 420); await page.wait_for_timeout(150)
        await page.evaluate(f"(() => {{ const s = {S}; s.setBallZ(140, 640, 420); cursor.history.length = 0; strikeHit(s.ball, performance.now(), 'super'); }})()")
        await page.wait_for_function(f"{S}.ball && {S}.ball.dir === 1", timeout=6000)
        fl = await page.evaluate(f"{S}.walls.slice().sort((a, b) => a.z - b.z).map(w => w.bricks.length - w.left)")
        check('a SUPER slap in play: the first wall loses at most the 3x3, the ball comes back, the 3 walls behind are untouched', 1 <= fl[0] <= 9 and fl[1:] == [0, 0, 0], fl)
        # aim: the landing point follows the hit's direction
        await page.evaluate(f"(() => {{ const s = {S}; s.walls.length = 0; [0, 1, 2, 3].forEach(i => s.spawnWall('brick', wallSlotZ(i))); s.heat = 0; }})()")
        lands = []
        for dx in (-160, 160):
            await page.mouse.move(640, 420); await page.wait_for_timeout(80)
            a = await page.evaluate(f"(() => {{ const s = {S}, now = performance.now(); s.setBallZ(140, 640, 420); cursor.history.length = 0; cursor.history.push({{ t: now - 80, x: 640 - {dx} * 0.5, y: 420 }}, {{ t: now, x: 640, y: 420 }}); cursor.x = 640; cursor.y = 420; strikeHit(s.ball, now, 'medium'); s.heat = 0; const A = s.ball.aim; return {{ ax: A.x, x0: s.ball.x, wall: A.wall }}; }})()")
            await page.wait_for_function(f"{S}.ball && {S}.ball.dir === 1", timeout=6000)
            ls = await page.evaluate(f"{S}.lastSmash"); lands.append((a, ls))
            await page.evaluate(f"(() => {{ const s = {S}; s.walls.length = 0; [0, 1, 2, 3].forEach(i => s.spawnWall('brick', wallSlotZ(i))); }})()")
        (al, ll), (ar, lr) = lands
        cw = await page.evaluate("(corridor().R - corridor().L) / wallGrid().cols")
        check('aim: a slap with the hand moving left lands left of the hit point, moving right lands right', al['ax'] < al['x0'] - 40 and ar['ax'] > ar['x0'] + 40 and ll['x'] < lr['x'] - 80, [al, ar, ll['x'], lr['x']])
        check('aim: the ball lands where it was aimed (within a third of a brick, curve included)', abs(ll['x'] - al['ax']) < cw / 3 and abs(lr['x'] - ar['ax']) < cw / 3, [ll['x'], al['ax'], lr['x'], ar['ax'], cw])
        await page.evaluate(f"{S}.setBallZ(400, 640, 420); {S}.ball.dir = -1; {S}.ball.aim = {{ x: 100, y: 0, z: wallSlotZ(0), wall: {S}.walls[0].id, t: performance.now() - 300 }}; {S}.ball.speed = 0")
        await page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
        am = await page.evaluate(f"{S}.ui.aimMarks")
        check('the landing point is marked on the wall ahead (a reticle on the overlay)', len(am) == 1 and am[0]['r'] > 4, am)
        await page.screenshot(path='tests/out/challenge_aim_en.png')

        # ===== A2: armor, weak spots, keystones, gold =====
        await page.evaluate("park()")
        ar = await page.evaluate("""(() => { const s = __grasp.strike, w = plainWall(), k = w.bricks.find(q => q.col === 1 && q.row === 2); k.armor = true; k.hp = k.max = 3; const out = [];
          for (let i = 0; i < 3; i++) { __sfxa.length = 0; const b = ballAt(w, 1, 2, 'soft'); smashWall(w, b, performance.now()); out.push({ hp: k.hp, alive: k.alive, cl: crackLevel(k, w), armor: (__sfxa.find(q => q[0] === 'armor') || [0, 0])[1] }); } return out; })()""")
        check('an armored brick (3 hp) takes three chips: cracked, badly cracked, out', [q['hp'] for q in ar] == [2, 1, 0] and [q['cl'] for q in ar[:2]] == [1, 2] and not ar[2]['alive'] and ar[0]['alive'], ar)
        check('a crack per armor level: a stony "tock" that is lower with more hp left (arg 2, then 1)', [q['armor'] for q in ar[:2]] == [2, 1], ar)
        wk = await page.evaluate("""(() => { const s = __grasp.strike, w = plainWall(), k = w.bricks.find(q => q.col === 2 && q.row === 1); k.weak = true; __sfx.length = 0; const b = ballAt(w, 2, 1, 'soft'), n0 = w.left; smashWall(w, b, performance.now());
          return { n: n0 - w.left, line: w.bricks.filter(q => q.col === 2 || q.row === 1).every(q => !q.alive), other: w.bricks.filter(q => q.col !== 2 && q.row !== 1).every(q => q.alive), sfx: __sfx.slice(), cracks: s.cracks.length, weakHits: s.weakHits, cols: w.cols, rows: w.rows }; })()""")
        check('a weak spot (glowing): even a soft hit on it cracks its whole row and column, nothing else; sfx weak, a crack line', wk['line'] and wk['other'] and wk['n'] == wk['cols'] + wk['rows'] - 1 and 'weak' in wk['sfx'] and wk['cracks'] >= 1 and wk['weakHits'] == 1, wk)
        ky = await page.evaluate("""(() => { const s = __grasp.strike, w = plainWall(), R = w.rows - 1, k = w.bricks.find(q => q.col === 1 && q.row === R); k.key = true; __sfx.length = 0; const b = ballAt(w, 1, R, 'soft'), n0 = w.left; smashWall(w, b, performance.now());
          return { n: n0 - w.left, fell: w.bricks.filter(q => q.row < R && Math.abs(q.col - 1) <= 1).every(q => !q.alive), kept: w.bricks.filter(q => Math.abs(q.col - 1) > 1).every(q => q.alive), sfx: __sfx.slice(), rows: w.rows }; })()""")
        check('a keystone: knocked out, everything resting on it (above it, one column each side) comes down; the rest stands; sfx keystone', ky['fell'] and ky['kept'] and ky['n'] == 1 + 3 * (ky['rows'] - 1) and 'keystone' in ky['sfx'], ky)
        gd = await page.evaluate("""(() => { const s = __grasp.strike, w = plainWall(), k = w.bricks.find(q => q.col === 0 && q.row === 0); k.gold = true; s.streak = 0; __sfx.length = 0; const s0 = s.score; const b = ballAt(w, 0, 0, 'soft'); smashWall(w, b, performance.now());
          return { ds: s.score - s0, sfx: __sfx.slice(), fl: s.floaters.map(f => f.text), golds: s.golds }; })()""")
        check('a gold brick: +25 bonus (x the combo) on top of its point, a GOLD floater and a ching', gd['ds'] == 26 and 'gold' in gd['sfx'] and any('GOLD' in f for f in gd['fl']) and gd['golds'] == 1, gd)
        await page.evaluate(f"{S}.noSpecials = false; {S}.setLevel(5)")
        sp = await page.evaluate("""(() => { const s = __grasp.strike, out = { armor: 0, weak: 0, gold: 0, key: 0, turret: 0, n: 0 }; for (let i = 0; i < 24; i++) { const w = s.spawnWall('brick', 9000 + i); for (const k of w.bricks) { out.n++; for (const t of ['armor', 'weak', 'gold', 'key', 'turret']) if (k[t]) out[t]++; } s.walls.splice(s.walls.indexOf(w), 1); }
          s.setLevel(1); const o1 = { weak: 0, armor: 0 }; for (let i = 0; i < 12; i++) { const w = s.spawnWall('brick', 9000 + i); for (const k of w.bricks) { if (k.weak) o1.weak++; if (k.armor) o1.armor++; } s.walls.splice(s.walls.indexOf(w), 1); } out.l1 = o1; return out; })()""")
        check('Endless spawns special bricks by level: level 5 has armored (~30%), weak spots, gold, keystones; level 1: a weak spot a wall, no armor', sp['armor'] > sp['n'] * 0.2 and sp['weak'] >= 20 and sp['gold'] > 0 and sp['key'] > 0 and sp['turret'] == 0 and sp['l1']['weak'] == 12 and sp['l1']['armor'] == 0, sp)
        check('A: no page errors', not errs, errs); await ctx.close()

        # ===== A3: the overheat =====
        ctx, page, errs = await fresh(b); await endless(page)
        await page.mouse.move(640, 420); await page.wait_for_timeout(100)
        HIT = lambda tier: f"(() => {{ const s = {S}; s.setBallZ(140, 640, 420); strikeHit(s.ball, performance.now(), '{tier}'); const r = {{ heat: s.heat, hot: overheated(), tier: s.lastHit.tier }}; park(); return r; }})()"
        await page.evaluate("__sfx.length = 0")
        h1 = await page.evaluate(HIT('super')); h2 = await page.evaluate(HIT('hard'))
        check('hard and SUPER hits heat the hand (SUPER +0.45, hard +0.28), not overheated yet', abs(h1['heat'] - 0.45) < 0.02 and abs(h2['heat'] - 0.73) < 0.02 and not h2['hot'], [h1, h2])
        await page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
        hb = await page.evaluate(f"{S}.ui.heatBar")
        check('a slim heat bar shows under the HUD pill while the hand is warm (minimal HUD: hearts + walls pill stay the row)', hb and hb['h'] <= 6 and 0.6 < hb['val'] < 0.8 and await page.evaluate(f"{S}.ui.hudParts.join()") == 'hearts,walls' and hb['y'] >= await page.evaluate(f"{S}.ui.hud.y + {S}.ui.hud.h"), hb)
        h3 = await page.evaluate(HIT('super'))
        t0 = await page.evaluate("performance.now()")
        ho = await page.evaluate(f"({{ sfx: __sfx.slice(), fl: {S}.floaters.map(f => f.text), left: {S}.hotUntil - performance.now() }})")
        check('full heat: OVERHEAT for ~3 s, a sizzle, an "Overheat!" floater', h3['hot'] and h3['heat'] == 1 and 'sizzle' in ho['sfx'] and 'Overheat!' in ho['fl'] and 2500 < ho['left'] <= 3000, [h3, ho])
        h4 = await page.evaluate(HIT('super'))
        check('overheated: a SUPER slap comes out soft', h4['tier'] == 'soft' and h4['hot'], h4)
        await page.wait_for_timeout(300); await page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
        hb = await page.evaluate(f"{S}.ui.heatBar"); steam = await page.evaluate("particles.filter(p => p.steam).length")
        check('overheated: the bar is full and red ("Too hot!"), steam rises off the hand', hb and hb['hot'] and hb['val'] == 1 and steam > 0, [hb, steam])
        await page.screenshot(path='tests/out/challenge_overheat_en.png')
        await page.evaluate(f"{S}.hotUntil = performance.now() + 30"); await page.wait_for_function(f"!overheated() && {S}.hotUntil === 0", timeout=3000)
        c0 = await page.evaluate(f"{S}.heat")
        check('the overheat ends: the hand is warm (0.35), hits are real again', abs(c0 - 0.35) < 0.02 and (await page.evaluate(HIT('hard')))['tier'] == 'hard', c0)
        m1 = await page.evaluate(HIT('medium')); m2 = await page.evaluate(HIT('soft'))
        check('medium and soft hits cool it (-0.12, -0.3)', abs(m1['heat'] - (0.35 + 0.28 - 0.12)) < 0.03 and abs(m2['heat'] - (0.35 + 0.28 - 0.12 - 0.3)) < 0.03, [m1, m2])
        k0 = await page.evaluate(f"{S}.heat"); await page.wait_for_timeout(1500); k1 = await page.evaluate(f"{S}.heat")
        check('and it cools with time too (~0.06 a second)', 0.04 < k0 - k1 < 0.14, [k0, k1])
        check('overheat: no page errors', not errs, errs); await ctx.close()

        # ===== B: turrets, walls closing in, two balls, the ramp =====
        ctx, page, errs = await fresh(b); await endless(page)
        await page.evaluate(f"{S}.noSpecials = true")
        tw = await page.evaluate("""(() => { const s = __grasp.strike, w = plainWall(), k = w.bricks.find(q => q.col === 1 && q.row === 0); k.turret = true; k.hp = k.max = 2; __sfx.length = 0;
          const q = fireShot(w, k, performance.now(), challengeCfg()); q.speed = 1.6; const t = proj(q.tx, q.ty, 0); return { t, sfx: __sfx.slice(), n: s.shots.length, id: w.id }; })()""")
        check('a turret brick fires a slow glowing shot at the player (sfx pew)', tw['n'] == 1 and 'pew' in tw['sfx'], tw)
        await page.mouse.move(tw['t']['x'], tw['t']['y']); await page.wait_for_timeout(50)
        await page.wait_for_function(f"{S}.deflects >= 1", timeout=6000)
        d = await page.evaluate(f"({{ dir: {S}.shots[0] && {S}.shots[0].dir, lives: {S}.lives, sfx: __sfx.slice(), streak: {S}.streak }})")
        check('a hand on the shot at the plane slaps it away: no heart lost, a ping, it flies back, the combo grows', d['dir'] == -1 and d['lives'] == 40 and 'deflect' in d['sfx'] and d['streak'] >= 1, d)
        await page.wait_for_function(f"{S}.shots.every(q => q.dead)", timeout=6000)
        tk = await page.evaluate(f"(() => {{ const w = {S}.walls.find(q => q.id === {tw['id']}), k = w.bricks.find(q => q.turret); return {{ hp: k.hp, alive: k.alive }}; }})()")
        check('...and back at its turret it chips it (2 hp -> 1)', tk['hp'] == 1 and tk['alive'], tk)
        await page.mouse.move(1270, 790); await page.evaluate("cursor.history.length = 0"); await page.wait_for_timeout(60)
        await page.evaluate(f"(() => {{ const s = {S}, w = s.walls.find(q => q.id === {tw['id']}), k = w.bricks.find(q => q.turret); __sfx.length = 0; const q = fireShot(w, k, performance.now(), challengeCfg()); q.speed = 1.6; s.streak = 7; }})()")
        await page.wait_for_function(f"{S}.shotHits >= 1", timeout=6000)
        h = await page.evaluate(f"({{ lives: {S}.lives, sfx: __sfx.slice(), streak: {S}.streak, fl: {S}.floaters.map(f => f.text) }})")
        check('a shot nobody slaps costs a heart: a buzz, "Ouch!", the combo is gone', h['lives'] == 39 and 'hurt' in h['sfx'] and h['streak'] == 0 and 'Ouch!' in h['fl'], h)
        await page.screenshot(path='tests/out/challenge_turret_en.png')
        check('turrets: no page errors', not errs, errs); await ctx.close()

        # the ramp: plans
        ctx, page, errs = await fresh(b)
        plans = await page.evaluate(f"Array.from({{ length: 40 }}, (_, i) => {A}.plan(i + 1))")
        w1 = plans[:4]; later = plans[8:]
        check('world 1 stages 1-4 are the gentle on-ramp: slower (x0.9), more reach (x1.08), 2 weak spots a wall, no armor / turrets / closing walls / two balls', all(q['paceK'] == 0.9 and q['reachK'] > 1 and q['weak'] == 2 and q['armor'] == 0 and q['turret'] == 0 and q['creep'] == 0 and q['balls'] == 1 for q in w1), w1[0])
        check('from world 2: faster (x1.1+), less reach, walls closer, turrets from stage 10, walls closing in from stage 12, more armor each world', all(q['paceK'] > 1.1 and q['reachK'] < 1 and q['gapK'] < 1 for q in later) and plans[9]['turret'] > 0 and plans[8]['turret'] == 0 and plans[11]['creep'] > 0 and plans[10]['creep'] == 0 and [plans[i]['armor'] for i in (4, 12, 20, 28, 36)] == sorted([plans[i]['armor'] for i in (4, 12, 20, 28, 36)]), [plans[9]['turret'], plans[11]['creep']])
        two = [q['n'] for q in plans if q['balls'] == 2]
        check('two balls at once on some world 3+ stages (never a boss stage)', len(two) >= 4 and min(two) >= 17 and not any(plans[n - 1]['boss'] for n in two), two)
        await stage(page, 1); p1 = await page.evaluate(f"{S}.pace"); r1 = await page.evaluate("advK('reachK')")
        await stage(page, 9); p9 = await page.evaluate(f"{S}.pace"); r9 = await page.evaluate("advK('reachK')")
        check('the pace in world 2 is far above world 1\'s first stage (x1.6+), the reach smaller', p9 / p1 > 1.6 and r9 < 1 < r1, [p1, p9, r1, r9])
        # walls closing in (stage 12)
        await stage(page, 12)
        await page.evaluate(f"{S}.playerServe('medium'); park(2300)")
        z0 = await page.evaluate(f"{S}.walls.slice().sort((a, b) => a.z - b.z)[0].z"); await page.wait_for_timeout(1200); z1 = await page.evaluate(f"{S}.walls.slice().sort((a, b) => a.z - b.z)[0].z")
        check('stage 12: the front wall closes in while the ball is in play (~25 depth units a second)', 15 < z0 - z1 < 60, [z0, z1])
        await page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
        await page.evaluate(f"(() => {{ const w = {S}.walls.slice().sort((a, b) => a.z - b.z)[0]; w.cz = wallSlotZ(0) - 420; }})()")
        try: await page.wait_for_function(f"{S}.ui.danger > 0.6", timeout=5000)  # (it slides there at the queue's slide speed)
        except Exception: pass
        dg = await page.evaluate(f"{S}.ui.danger")
        check('near the player it glows red (the danger rises)', dg > 0.6, dg)
        await page.screenshot(path='tests/out/challenge_closing_en.png')
        l0 = await page.evaluate(f"{S}.lives"); await page.evaluate("__sfx.length = 0")
        await page.evaluate(f"(() => {{ const w = {S}.walls.slice().sort((a, b) => a.z - b.z)[0]; w.cz = wallSlotZ(0); }})()")
        await page.wait_for_function(f"{S}.crushes >= 1", timeout=4000)
        cr = await page.evaluate(f"({{ lives: {S}.lives, lost: {A}.lost, z: {S}.walls.slice().sort((a, b) => a.z - b.z)[0].z, sfx: __sfx.slice() }})")
        check('if it gets to the player it slams in: a heart lost (the stage\'s star count drops), the wall shoved back to its slot', cr['lives'] == l0 - 1 and cr['lost'] == 1 and abs(cr['z'] - await page.evaluate("wallSlotZ(0)")) < 30 and 'hurt' in cr['sfx'], cr)
        # two balls (the first two-ball stage)
        await stage(page, two[0]); await page.wait_for_function(f"{S}.waiting", timeout=6000)
        await page.evaluate(f"{S}.playerServe('medium')"); nb = await page.evaluate(f"{S}.balls.length")
        check(f'stage {two[0]}: the serve sends two balls', nb == 2, nb)
        l0 = await page.evaluate(f"{S}.lives"); await page.mouse.move(1270, 790)
        await page.evaluate(f"(() => {{ const s = {S}; cursor.history.length = 0; s.balls[1].dir = 1; s.balls[1].z = -__grasp.CONFIG.STRIKE_HIT_Z * 0.9; s.balls[0].dir = 1; s.balls[0].z = 2300; s.balls[0].speed = 0; }})()")
        await page.wait_for_function(f"{S}.balls.length === 1", timeout=4000)
        check('a two-ball stage: each ball missed costs a heart, even with the other still in play', await page.evaluate(f"{S}.lives") == l0 - 1, [l0, await page.evaluate(f"{S}.lives")])
        await page.screenshot(path='tests/out/challenge_twoballs_en.png')
        check('ramp: no page errors', not errs, errs); await ctx.close()

        # ===== C: the combo =====
        ctx, page, errs = await fresh(b); await endless(page)
        await page.mouse.move(640, 420); await page.wait_for_timeout(100)
        HITM = f"(() => {{ const s = {S}; s.setBallZ(140, 640, 420); strikeHit(s.ball, performance.now(), 'medium'); park(); return {{ mul: comboMul(), pop: s.ui.comboPop }}; }})()"
        ms = [await page.evaluate(HITM) for _ in range(7)]
        check('the combo grows with returns in a row: x1, x1, x2 (3 hits), x2, x2, x3 (6), x3', [q['mul'] for q in ms] == [1, 1, 2, 2, 2, 3, 3], [q['mul'] for q in ms])
        check('...and pops ("x3 COMBO") only when it changes', ms[2]['pop']['n'] == 2 and ms[5]['pop']['n'] == 3 and ms[6]['pop']['t'] == ms[5]['pop']['t'], [ms[2]['pop'], ms[5]['pop']])
        await page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
        cb = await page.evaluate(f"({{ box: {S}.ui.comboBox, hud: {S}.ui.hud, pill: {S}.ui.wallsPill }})")
        bx = cb['box']['x'] + cb['box']['w'] / 2 if cb['box'] else 0; hr = cb['hud']['x'] + cb['hud']['w']
        check('the pop sits by the walls pill (beside the HUD row on a laptop)', cb['box'] and cb['box']['n'] == 3 and hr < bx < hr + 100 and abs(cb['box']['y'] + cb['box']['h'] / 2 - (cb['hud']['y'] + cb['hud']['h'] / 2)) < 45, cb)
        await page.screenshot(path='tests/out/challenge_combo_en.png')
        await page.evaluate(f"{S}.streak = 40"); check('it caps at x8', await page.evaluate("comboMul()") == 8)
        await page.mouse.move(1270, 790); await page.evaluate(f"cursor.history.length = 0; {S}.setBallZ(-__grasp.CONFIG.STRIKE_HIT_Z * 0.9, 640, 420)")
        await page.wait_for_function(f"{S}.streak === 0", timeout=4000)
        lp = await page.evaluate(f"({{ mul: comboMul(), pop: {S}.ui.comboPop }})")
        check('a miss drops it back to x1 (a grey "x1" sinks by the pill)', lp['mul'] == 1 and lp['pop']['lost'] == 8 and lp['pop']['n'] == 1, lp)
        check('combo: no page errors', not errs, errs); await ctx.close()

        # ===== C: score, best, NEW RECORD!, ranks (EN desktop, HE phone) =====
        for he, mob in ((False, False), (True, True)):
            tag = 'he' if he else 'en'
            ctx, page, errs = await fresh(b, mobile=mob, he=he); await stage(page, 1)
            th = await page.evaluate("rankThresholds(1)")
            check(tag + ': rank thresholds by the stage\'s par: Bronze 0 < Silver < Gold < Diamond < Legend', th[0] == 0 and th == sorted(th) and len(set(th)) == 5 and th[1] == await page.evaluate("stagePar(1)"), th)
            await page.evaluate(f"{S}.score = {th[3] + 20}"); r1 = await page.evaluate(f"{A}.finishTest(0)")
            check(tag + ': a first clear keeps its score as the stage\'s best, ranks it (Diamond), no NEW RECORD on a first clear', r1['score'] == th[3] + 20 and r1['bestScore'] == r1['score'] and not r1['record'] and r1['rank'] == 3 and await page.evaluate("profile.adv.best[1]") == r1['score'], r1)
            await page.wait_for_function(f"{S}.over && {S}.ui.advScore && {S}.ui.advScore.a >= 1", timeout=10000)
            sc = await page.evaluate(f"{S}.ui.advScore")
            check(tag + ': the clear card shows the score with its rank pill', sc['score'] == r1['score'] and sc['rank'] == 'diamond' and not sc['record'] and sc['x'] >= 0 and sc['x'] + sc['w'] <= await page.evaluate("innerWidth"), sc)
            await page.evaluate(f"{A}.start(1)"); await page.wait_for_function(f"{A}.phase === 'play' && {A}.stage === 1", timeout=8000)
            await page.evaluate("__sfx.length = 0; __spoken.length = 0; __grasp.grippy.cool && __grasp.grippy.cool()")
            await page.evaluate(f"{S}.score = {th[4] + 50}"); r2 = await page.evaluate(f"{A}.finishTest(0)")
            check(tag + ': a better score: NEW RECORD (the old best kept for the card), Legend, the profile\'s best updated', r2['record'] and r2['prevScore'] == r1['score'] and r2['rank'] == 4 and await page.evaluate("profile.adv.best[1]") == th[4] + 50, r2)
            await page.wait_for_function(f"{S}.over && {S}.ui.advRecord && {S}.ui.advRecord.a >= 1", timeout=10000)
            rec = await page.evaluate(f"({{ sfx: __sfx.slice(), said: __grasp.grippy.said.map(s => s.event || s.ev || s), spoken: __spoken.map(s => s.text) }})")
            check(tag + ': the record moment: a fanfare and the voice says it', 'record' in rec['sfx'] and any(('record' in str(s)) for s in rec['said']), rec)
            await page.wait_for_timeout(300); await page.screenshot(path=f'tests/out/challenge_record_{tag}.png')
            await page.evaluate(f"{A}.start(1)"); await page.wait_for_function(f"{A}.phase === 'play' && {A}.stage === 1", timeout=8000)
            await page.evaluate(f"{S}.score = {th[1] + 5}"); r3 = await page.evaluate(f"{A}.finishTest(1)")
            check(tag + ': a lower score: no record, the best stays, its own rank (Silver), the next rank\'s score named', not r3['record'] and r3['bestScore'] == th[4] + 50 and r3['rank'] == 1 and r3['next']['rank'] == 2 and r3['next']['at'] == th[2], r3)
            await page.wait_for_function(f"{S}.over && {S}.ui.advScore && {S}.ui.advScore.a >= 1", timeout=10000)
            await page.screenshot(path=f'tests/out/challenge_card_{tag}.png')
            await page.evaluate("openAdvMap()"); await page.wait_for_timeout(300)
            mp = await page.evaluate("""({ rk: (document.querySelector('.anode[data-n="1"] .rk') || {}).dataset, node: document.querySelector('.anode[data-n="1"]').dataset.rank, none: !document.querySelector('.anode[data-n="2"] .rk'), chip: !$('advRank').hidden && $('advRank').textContent, aria: document.querySelector('.anode[data-n="1"]').getAttribute('aria-label') })""")
            want = 'אגדה' if he else 'Legend'
            check(tag + ': the map shows the stage\'s best rank as a gem on its stop, none on an uncleared stop; the overall rank chip in the footer', mp['rk'] and mp['rk']['rank'] == 'legend' and mp['node'] == 'legend' and mp['none'] and want in mp['chip'] and want in mp['aria'], mp)
            for _ in range(6):  # (the XP from the clears may have opened NEW UNLOCKED sheets: dismissed)
                if await page.evaluate("$('newCard').hidden"): break
                await page.evaluate("$('nuOk').click()"); await page.wait_for_timeout(400)
            await page.evaluate("advScrollTo(1, false)"); await page.wait_for_timeout(200)  # (the XP from the clears may have opened a NEW UNLOCKED sheet; the view on stage 1)
            await page.screenshot(path=f'tests/out/challenge_map_{tag}.png')
            check(tag + ': no page errors', not errs, errs); await ctx.close()

        # profile validation
        ctx, page, errs = await fresh(b)
        await page.evaluate("(() => { const p = JSON.parse(localStorage.getItem(PROFILE_KEY) || '{}'); p.adv = p.adv || {}; p.adv.stars = { 1: 3 }; p.adv.best = { 1: 900.4, 2: -5, 99: 100, 3: 'x', 4: 1e12, 0: 50 }; localStorage.setItem(PROFILE_KEY, JSON.stringify(p)); })()")
        await page.reload(); await page.wait_for_timeout(600)
        bst = await page.evaluate("profile.adv.best")
        check('profile: the best scores are validated on load (stage 1..40, a positive number, rounded, capped)', bst == {'1': 900, '4': 9999999}, bst)
        ov = await page.evaluate("[overallRank(), advBestRank(1), advBestRank(2)]")
        check('the overall rank: the average of the cleared stages\' best ranks; an uncleared stage has none', ov[0] == ov[1] and ov[2] == -1, ov)
        check('profile: no page errors', not errs, errs); await ctx.close()

        # ===== screenshots: special bricks in play, EN desktop 2D, HE phone 2D, 3D =====
        for he, mob, g3 in ((False, False, False), (True, True, False), (False, False, True)):
            tag = ('he' if he else 'en') + ('_phone' if mob else '') + ('_3d' if g3 else '')
            ctx, page, errs = await fresh(b, mobile=mob, he=he, gfx="{ pr: 0.2, shadows: false, auto: false }" if g3 else None)
            await stage(page, 22)
            if g3: await page.wait_for_function(f"{S}.gfx === '3d'", timeout=30000)
            await page.evaluate(f"{S}.playerServe('medium'); park(2300); {S}.walls.forEach(w => w.turretAt = 1e12)")
            await page.evaluate(f"(() => {{ const s = {S}; s.streak = 8; streakUp(performance.now()); s.heat = 0.6; s.ui.heatAt = performance.now(); }})()")
            await page.wait_for_timeout(250)
            sp = await page.evaluate(f"(() => {{ const w = {S}.walls.slice().sort((a, b) => a.z - b.z)[0]; return {{ sp: w.bricks.filter(k => k.alive && brickSpecial(k)).map(brickSpecial), hb: {S}.ui.heatBar, cb: {S}.ui.comboBox, W: innerWidth }}; }})()")
            check(tag + ': stage 22\'s front wall carries special bricks; the heat bar and the combo pop sit inside the screen', len(sp['sp']) >= 3 and sp['hb'] and 0 <= sp['hb']['x'] and sp['hb']['x'] + sp['hb']['w'] <= sp['W'] and sp['cb'] and 0 <= sp['cb']['x'] and sp['cb']['x'] + sp['cb']['w'] <= sp['W'], sp)
            if g3:
                ic = await page.evaluate("(() => { let n = 0; for (const [, e] of G3.walls) n += e.icons.filter(p => p.visible).length; return n; })()")
                check('3D: the special bricks wear their faces (icon planes in front of them)', ic >= 3, ic)
            await page.screenshot(path=f'tests/out/challenge_specials_{tag}.png')
            check(tag + ': no page errors', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
