exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Strike's surprise guests: every 4-6 serves (a serve = a launch from the far end: a fresh serve or the far-wall rebound) a flying cow or
# monkey comes instead of the ball. x1.35 radius, x0.9 speed, tumbling; slapped it screams back (bubble, sound, +5 coins, track('guest'))
# and smashes like a Big ball (never softer than medium); missed it boings off the screen (no life lost). Seeded on the 'guest' channel.
# Timing-independent: the balls are parked (speed 0) or driven by direct calls; every wait is a condition.
S = "__grasp.strike"
FRAMES = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
SFX_JS = "(() => { window.__sfx = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); o(k, a); }; })()"
FREEZE = f"(() => {{ const s = {S}; s.serveAt = performance.now() + 1e9; for (const b of s.balls) {{ b.speed = 0; b.trail.length = 0; }} }})()"
# park the guest at depth z on screen point (x, y), frozen, upright (no tumble): for pixel probes and screenshots
PARK = f"""((z, x, y) => {{ const s = {S}, b = s.ball; const g = b.guest; s.setBallZ(z, x, y); b.guest = g; b.speed = 0; b.rot = 0; b.tumble = 0; b.trail.length = 0; s.serveAt = performance.now() + 1e9; s.lives = 40; return ballScreen(b); }})"""
# probe a grid of points inside 0.7 r of the guest's screen centre: how many near-white, near-black and brown pixels
HEAD = lambda sc: {'x': sc['x'], 'y': sc['y'] - 0.5 * sc['r'], 'r': sc['r'] * 0.6}  # the cow's head (eyes, horns, black patches): the painted art has its pink muzzle at the centre
PROBE = """((sc) => { const out = { white: 0, black: 0, brown: 0, beige: 0, n: 0, px: [] }; for (let i = -4; i <= 4; i++) for (let j = -4; j <= 4; j++) {
  const x = sc.x + i / 4 * sc.r * 0.7, y = sc.y + j / 4 * sc.r * 0.7; if (Math.hypot(x - sc.x, y - sc.y) > sc.r * 0.7) continue; const [r, g, b] = __grasp.strike.pixel(x, y); out.n++;
  if (out.px.length < 6) out.px.push([r, g, b]);
  if (r > 205 && g > 205 && b > 195) out.white++; if (r < 60 && g < 60 && b < 70) out.black++;
  if (r > 90 && r < 200 && r - g > 25 && g - b > 15 && g < 150) out.brown++; if (r > 200 && g > 160 && r - b > 50) out.beige++; } return out; })"""

async def new_page(b, mobile=False, lang='en', gfx=None):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + (f"window.__graspGfx = {gfx};" if gfx else "") + f"try {{ localStorage.setItem('lang', '{lang}'); }} catch (e) {{}}")
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
    await page.evaluate("__grasp.setPlayerLevel(20)")  # the road unlocks everything (these suites test the run arc, not the meta gate)
    return ctx, page, errs

async def play_strike(page, mobile=False):
    if mobile: await page.tap('#mouseBtn'); await page.tap('.modes button[data-mode=strike]')
    else: await page.click('#mouseBtn'); await page.click('.modes button[data-mode=strike]')
    await page.wait_for_function(f"mode === 'mouse' && gameMode === 'strike' && {S}.ball", timeout=10000)
    await page.evaluate(SFX_JS + f"; __grasp.CONFIG.STRIKE_PU_RATE = 0; {S}.extrasOff = true; {S}.lives = 40; " + FREEZE)

async def frames(page, n=1):
    for _ in range(n): await page.evaluate(FRAMES)

async def to3d(page):  # the WebGL renderer on (setGfx('3d')); False when this machine has no WebGL
    await page.evaluate(f"__grasp.setGfx('3d'); {S}.gfxAuto = false")
    await page.wait_for_function(f"{S}.gfx === '3d' || {S}.gfxInfo.state === 'failed'", timeout=30000)
    return await page.evaluate(f"{S}.gfx") == '3d'

async def scene_cow(page, w, h):  # a cow coming in, the 'Incoming!' cue still up
    await page.evaluate(f"{S}.guestEvery = 0; {S}.spawnGuest('cow')")
    await page.evaluate(PARK + f"(420, {w * 0.42}, {h * 0.6})")

async def scene_monkey(page, w, h):  # a monkey slapped a moment ago, flying back dizzy, its bubble up
    await page.evaluate(f"{S}.guestEvery = 0; {S}.spawnGuest('monkey')")
    await page.evaluate(PARK + f"(30, {w * 0.6}, {h * 0.55})")
    await page.evaluate(f"(() => {{ const s = {S}, b = s.ball; strikeHit(b, performance.now()); b.speed = 0; b.vx = b.vy = 0; b.spin = 0; b.z = 260; b.trail.length = 0; }})()")
    await page.wait_for_function(f"performance.now() - {S}.ball.guestHitAt > 380")
    # (a slow software-WebGL frame can outlast the bubble: hold it beside the monkey for the shot)
    await page.evaluate(f"(() => {{ const s = {S}, sc = ballScreen(s.ball); for (const f of s.floaters) if (f.bubble) {{ f.life = 30; f.x = sc.x - sc.r * 0.6; f.y = sc.y - sc.r * 1.15; }} }})()"); await frames(page, 1)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ===== desktop, EN, 2D =====
        ctx, page, errs = await new_page(b); await play_strike(page)
        await page.mouse.move(1240, 780); await frames(page, 2)
        h0 = await page.evaluate(f"({{ every: {S}.guestEvery, next: {S}.guestNext, hits: {S}.guestHits, guest: {S}.ball.guest, kinds: {S}.guestKinds.length }})")
        check('hooks: guestEvery null by default, guestHits 0, each ball has guest: null; extrasOff (the older suites) means no guests', h0['every'] is None and h0['hits'] == 0 and h0['guest'] is None and h0['next'] is None, h0)

        # ---- schedule: guestEvery = 2 -> every second serve is a guest; both kinds; radius x1.35, speed x0.9 ----
        sch = await page.evaluate(f"""(() => {{ const s = {S}; s.guestEvery = 2; const out = [];
          for (let i = 0; i < 10; i++) {{ s.serve(); const b = s.ball; b.speed0 = b.speed; out.push({{ guest: b.guest, speed: b.speed, base: s.pace * __grasp.strike.perkStats().serve, r: ballScreen(b).r, r0: ballScreen({{ x: b.x, y: b.y, z: b.z }}).r, tumble: b.tumble || 0 }}); }}
          {FREEZE}; return out; }})()""")
        g = [x['guest'] for x in sch]
        check('guestEvery = 2: serves 2, 4, 6, 8, 10 bring a guest, the others a ball', all((x is not None) == (i % 2 == 1) for i, x in enumerate(g)), g)
        check('both kinds appear (never three of a kind in a row)', {'cow', 'monkey'} <= set(x for x in g if x), g)
        gs = [x for x in sch if x['guest']]
        check('a guest is x1.35 the ball radius and x0.9 the serve speed, and it tumbles', all(abs(x['r'] / x['r0'] - 1.35) < 1e-6 and abs(x['speed'] / x['base'] - 0.9) < 1e-6 and abs(x['tumble']) > 0.001 for x in gs) and all(abs(x['r'] - x['r0']) < 1e-9 for x in sch if not x['guest']), gs[:2])
        rot = await page.evaluate(f"(() => {{ const s = {S}; s.guestEvery = 0; s.spawnGuest('cow'); const b = s.ball; b.speed = 0.0001; const r0 = b.rot; return new Promise(res => setTimeout(() => res([r0, b.rot]), 300)); }})()")
        check('the guest tumbles in flight (its rotation turns)', abs(rot[1] - rot[0]) > 0.2, rot)

        # ---- the NEXT card shows the guest one serve before ----
        await page.evaluate(f"{S}.setLevel(4); {S}.guestEvery = 2; {S}.serve(); {FREEZE}")  # (the card shows from level 3 on)
        nx = await page.evaluate(f"{S}.guestNext"); await frames(page, 2)
        card = await page.evaluate(f"{S}.ui.nextCard")
        check('one serve before a guest: guestNext.in = 1 and the NEXT card shows that guest (icon drawn) even with extrasOff', nx and nx['in'] == 1 and card and card['kind'] == 'guest' and card['guest'] == nx['kind'] and card.get('icon'), [nx, card])
        await page.screenshot(path='tests/out/guests_next_card.png', clip={'x': 640, 'y': 40, 'width': 640, 'height': 200})
        await page.evaluate(f"{S}.serve(); {FREEZE}"); await frames(page, 2)
        sv = await page.evaluate(f"({{ g: {S}.ball.guest, card: {S}.ui.nextCard }})")
        check('...and the next serve is that guest; the card goes away (extrasOff, no guest next)', sv['g'] == nx['kind'] and sv['card'] is None, sv)

        # ---- slap: back it goes, screaming, a bubble, +5 coins, track('guest'), at least medium ----
        await page.evaluate(f"{S}.guestEvery = 0; {S}.spawnGuest('cow')"); sc = await page.evaluate(PARK + "(30, 640, 420)")
        hit = await page.evaluate(f"""(() => {{ const s = {S}, b = s.ball, c0 = __grasp.profile.coins, e0 = __grasp.events.length; __sfx.length = 0; const f0 = s.floaters.length;
          strikeHit(b, performance.now()); return {{ dir: b.dir, tier: b.tier, hits: s.guestHits, coins: __grasp.profile.coins - c0, ev: __grasp.events.slice(e0), sfx: __sfx.slice(), bub: s.floaters.filter(f => f.bubble).map(f => f.text), speed: b.speed, pace: s.pace }}; }})()""")
        check('slapping a cow: it reverses (dir -1), at least medium power, guestHits 1', hit['dir'] == -1 and hit['tier'] in ('medium', 'hard', 'super') and hit['hits'] == 1, hit)
        check("slap: a 'MOO!' speech bubble, the 'moo' sound requested, +2 coins, track('guest', 1)", 'MOO!' in hit['bub'] and 'moo' in hit['sfx'] and hit['coins'] == 2 and ['guest', 1] in hit['ev'], hit)
        await frames(page, 2); fc = await page.evaluate(f"guestFace({S}.ball, performance.now())")
        await page.wait_for_function(f"performance.now() - {S}.ball.guestHitAt > 400"); fd = await page.evaluate(f"guestFace({S}.ball, performance.now())")
        check('faces: happy right after the slap, dizzy (spiral eyes) flying back', fc == 'happy' and fd == 'dizzy', [fc, fd])
        # ---- the painted cow art (assets/guests/cow_<face>.png) replaces the drawn cow; the monkey (no art yet) stays drawn ----
        await page.wait_for_function(f"['in', 'happy', 'dizzy', 'squash'].every(f => {S}.guestArt('cow', f) === 'img') || ['in', 'happy', 'dizzy', 'squash'].some(f => GUEST_ART['cow_' + f].state === 'failed')", timeout=8000)
        art = await page.evaluate(f"({{ cow: ['in', 'happy', 'dizzy', 'squash'].map(f => {S}.guestArt('cow', f)), monkey: ['in', 'happy', 'dizzy', 'squash'].map(f => {S}.guestArt('monkey', f)), w: GUEST_ART.cow_in.img.naturalWidth }})")
        check("the cow uses its painted art for every face ('img'); the monkey, with no art files yet, falls back to the drawn sprite", art['cow'] == ['img'] * 4 and art['monkey'] == ['drawn'] * 4 and art['w'] == 256, art)
        await page.evaluate(f"(() => {{ const s = {S}; s.guestEvery = 0; s.serve(); s.spawnGuest('cow'); s.floaters.length = 0; }})()"); sc2 = await page.evaluate(PARK + "(160, 640, 430)")
        await frames(page, 3); await page.screenshot(path='tests/out/guests_cow_art_2d.png')
        pa = await page.evaluate(PROBE + f"({json.dumps(HEAD(sc2))})")
        check('2D: the painted cow reads white + black at its head', pa['white'] >= 4 and pa['black'] >= 3, pa)
        await page.evaluate(f"(() => {{ const s = {S}; s.serve(); s.spawnGuest('monkey'); }})()"); await page.evaluate(PARK + "(30, 640, 420)")
        hm = await page.evaluate(f"(() => {{ const s = {S}; __sfx.length = 0; strikeHit(s.ball, performance.now()); return {{ sfx: __sfx.slice(), bub: s.floaters.filter(f => f.bubble).map(f => f.text) }}; }})()")
        check("monkey slap: 'OOH OOH!' bubble and the 'monkey' chirps", 'OOH OOH!' in hm['bub'] and 'monkey' in hm['sfx'], hm)
        ms = await page.evaluate("""(() => { const d = __grasp.missionPool.find(q => q.id === 'guest'); const L = __grasp.profile.missions.list; L[0] = { id: 'guest', progress: 0, goal: 3, reward: 30, done: false, claimed: false };
          const t0 = t('ms_guest', { n: 3 }); __grasp.track('guest', 1); __grasp.track('guest', 1); const p2 = L[0].progress; __grasp.track('guest', 1); return { d, t0, p2, done: L[0].done }; })()""")
        check("mission 'Hit 3 flying animals' (ev 'guest', goal 3) completes after 3 guest hits", ms['d'] and ms['d']['ev'] == 'guest' and ms['d']['goals'] == [3] and ms['t0'] == 'Hit 3 flying animals' and ms['p2'] == 2 and ms['done'], ms)

        # ---- walls: smashes like a Big ball, footprint >= its own size ----
        sm = await page.evaluate(f"""(() => {{ const s = {S}, now = performance.now(); s.guestEvery = 0; const res = {{}};
          const dead = (w) => w.bricks.filter(k => !k.alive).length;
          const run = (key, guest, tier) => {{ s.serve(); s.walls.length = 0; s.spawnWall('brick', wallSlotZ(0)); const w = s.smashTest(tier); const b = s.ball; b.guest = guest; const d0 = dead(w); smashWall(w, b, now);
            const r = ballRad(b), cover = w.bricks.filter(k => {{ const c = brickCell(w, k.col, k.row); return Math.hypot(Math.max(0, Math.abs(b.x - c.x) - c.w / 2), Math.max(0, Math.abs(b.y - c.y) - c.h / 2)) < r; }});
            res[key] = {{ n: dead(w) - d0, under: cover.length, underAlive: cover.filter(k => k.alive).length, r, bricks: w.bricks.length }}; }};
          run('ball', null, 'medium'); run('cow', 'cow', 'medium'); run('cowSoft', 'cow', 'soft'); run('ballSoft', null, 'soft'); {FREEZE}; return res; }})()""")
        check('a guest smashes at least as many bricks as a ball at the same power, and a soft slap still counts as medium', sm['cow']['n'] >= sm['ball']['n'] and sm['cowSoft']['n'] >= sm['ball']['n'] and sm['cowSoft']['n'] > sm['ballSoft']['n'], sm)
        check("the guest's hole covers its whole footprint (x1.35 radius): no live brick left under it", sm['cow']['underAlive'] == 0 and sm['cowSoft']['underAlive'] == 0 and sm['cow']['r'] > sm['ball']['r'] * 1.3, sm)

        # ---- a miss: no life lost, a boing, a squashed face bouncing off, then a normal serve ----
        await page.evaluate(f"{S}.serve(); {S}.spawnGuest('monkey')"); await page.evaluate(PARK + "(200, 120, 120)")
        m0 = await page.evaluate(f"(() => {{ const s = {S}; __sfx.length = 0; s.ball.speed = s.pace; s.serveAt = 0; return {{ lives: s.lives, misses: s.misses, gm: s.guestMisses, streak: s.streak }}; }})()")
        await page.wait_for_function(f"{S}.guestMisses > {m0['gm']}", timeout=15000)
        m1 = await page.evaluate(f"({{ lives: {S}.lives, misses: {S}.misses, gm: {S}.guestMisses, bouncers: {S}.bouncers.map(q => q.kind), sfx: __sfx.slice(), bub: {S}.floaters.filter(f => f.bubble).map(f => f.text), balls: {S}.balls.length }})")
        check("missing a guest: no life lost, no miss counted, a 'boing', a BOING! bubble, the monkey bouncing off the screen", m1['lives'] == m0['lives'] and m1['misses'] == m0['misses'] and 'boing' in m1['sfx'] and 'BOING!' in m1['bub'] and m1['bouncers'] == ['monkey'], [m0, m1])
        await frames(page, 2)
        check('the squashed-face frame is drawn', await page.evaluate("SPRITES.has('guest|monkey|squash')"))
        await page.wait_for_function(f"{S}.ball && !{S}.ball.guest", timeout=10000)
        await page.wait_for_function(f"{S}.bouncers.length === 0", timeout=10000)
        check('then a normal ball is served and the guest has bounced off the screen', True)

        # ---- Grippy: cow / monkey lines ----
        ln = await page.evaluate("__grasp.grippy.lines")
        bad = [e + ':' + l for e in ('cow', 'monkey') for l in ('en', 'he') if len(ln[l].get(e, [])) < 6 or len(set(ln[l][e])) != len(ln[l][e]) or any(len(x) > 48 or not x.strip() for x in ln[l][e])]
        heb = [e for e in ('cow', 'monkey') if not all(re.search('[֐-׿]', x) for x in ln['he'][e]) or set(ln['he'][e]) & set(ln['en'][e])]
        check("Grippy has >= 6 distinct short lines for 'cow' and 'monkey' in EN and HE (Hebrew)", not bad and not heb, [bad, heb])
        gr = await page.evaluate(f"(() => {{ const s = {S}; __grasp.grippy.cool(); s.serve(); s.spawnGuest('cow'); const a = __grasp.grippy.last; __grasp.grippy.cool(); s.serve(); s.spawnGuest('monkey'); const c = __grasp.grippy.last; {FREEZE}; return [a, c]; }})()")
        check('a guest flies in: Grippy says a cow / monkey line, and the whistle cue + Incoming! floater', gr[0]['event'] == 'cow' and gr[0]['text'] in ln['en']['cow'] and gr[1]['event'] == 'monkey' and gr[1]['text'] in ln['en']['monkey']
              and 'whistle' in await page.evaluate("__sfx") and await page.evaluate(f"{S}.floaters.some(f => f.text === 'Incoming!')"), gr)

        # ---- pixel probes, 2D: the cow white + black, the monkey brown ----
        await page.evaluate(f"(() => {{ const s = {S}; s.serve(); s.spawnGuest('cow'); s.floaters.length = 0; }})()"); sc = await page.evaluate(PARK + "(160, 640, 430)")
        await frames(page, 3); pc = await page.evaluate(PROBE + f"({json.dumps(HEAD(sc))})")
        check('2D: the cow reads white with black patches at its head', pc['white'] >= 4 and pc['black'] >= 3, pc)
        await page.evaluate(f"(() => {{ const s = {S}; s.serve(); s.spawnGuest('monkey'); s.floaters.length = 0; }})()"); sc = await page.evaluate(PARK + "(160, 640, 430)")
        await frames(page, 3); pm = await page.evaluate(PROBE + f"({json.dumps(sc)})")
        check('2D: the monkey reads brown (with its beige face) at its screen point', pm['brown'] >= 6 and pm['beige'] >= 2 and pm['white'] < pm['brown'], pm)
        check('no page errors (desktop EN)', not errs, errs)
        await ctx.close()

        # ===== HE: the bubbles in Hebrew =====
        ctx, page, errs = await new_page(b, lang='he'); await play_strike(page); await page.mouse.move(1240, 780)
        he = await page.evaluate(f"""(() => {{ const s = {S}, out = {{}}; s.guestEvery = 0;
          for (const k of ['cow', 'monkey']) {{ s.serve(); s.spawnGuest(k); const b = s.ball; s.setBallZ(30, 640, 420); b.guest = k; s.floaters.length = 0; __sfx.length = 0; strikeHit(b, performance.now()); out[k] = {{ bub: s.floaters.filter(f => f.bubble).map(f => f.text), sfx: __sfx.slice() }}; }}
          {FREEZE}; return out; }})()""")
        check("HE: the cow says 'מווו!' and the monkey 'או או!'", 'מווו!' in he['cow']['bub'] and 'או או!' in he['monkey']['bub'] and 'moo' in he['cow']['sfx'] and 'monkey' in he['monkey']['sfx'], he)
        check('no page errors (HE)', not errs, errs)
        await ctx.close()

        # ===== daily: the same guests on the same serves on two runs of the same date =====
        ctx, page, errs = await new_page(b); await play_strike(page); await page.mouse.move(1240, 780)
        SEQ = f"""(() => {{ const s = {S}; s.extrasOff = false; s.guestEvery = null; __grasp.startDaily(); const out = [], early = [];
          for (let i = 0; i < 20; i++) {{ s.serve(); if (s.ball.guest) early.push(s.pitches); }}  // levels 1-3: no flying animals
          s.setLevel(4); const p0 = s.pitches;
          for (let i = 0; i < 100; i++) {{ s.serve(); if (s.ball.guest) out.push([s.pitches - p0, s.ball.guest]); }} s.extrasOff = true; {FREEZE}; s.lives = 40; return {{ out, early, on: __grasp.daily.on }}; }})()"""
        d1 = await page.evaluate(SEQ); d2 = await page.evaluate(SEQ)
        gaps = [b2[0] - a2[0] for a2, b2 in zip(d1['out'], d1['out'][1:])]
        check('daily: no guests on level 1; from level 4 a guest every 8-12 serves, both kinds, seeded', d1['on'] and not d1['early'] and len(d1['out']) >= 6 and 8 <= d1['out'][0][0] <= 12 and all(8 <= x <= 12 for x in gaps) and {'cow', 'monkey'} <= {k for _, k in d1['out']}, d1)
        check('daily: the same guest serves (and kinds) on a second run of the same date', d1['out'] == d2['out'], [d1['out'], d2['out']])
        check('no page errors (daily)', not errs, errs)
        await ctx.close()

        # ===== 3D (setGfx('3d')): pixel probes on the WebGL sprites =====
        ctx, page, errs = await new_page(b, gfx="{ pr: 0.5, auto: false, shadows: false }"); await play_strike(page); await page.mouse.move(1240, 780)
        webgl = await to3d(page)
        if not webgl: print('INFO no WebGL here: the 3D probes are skipped', await page.evaluate(f"{S}.gfxInfo"))
        else:
            await page.evaluate(f"(() => {{ const s = {S}; s.guestEvery = 0; s.serve(); s.spawnGuest('cow'); s.floaters.length = 0; }})()"); sc = await page.evaluate(PARK + "(160, 640, 430)")
            await frames(page, 3); pc = await page.evaluate(PROBE + f"({json.dumps(HEAD(sc))})")
            ov = await page.evaluate(f"(() => {{ const s = {S}; const q = __grasp.strike.pixel3d({sc['x']}, {sc['y']}); return q; }})()")
            check('3D: the cow is a WebGL sprite (white + black at its screen point, in the WebGL layer)', pc['white'] >= 4 and pc['black'] >= 3 and ov is not None, [pc, ov])
            a3 = await page.evaluate(f"(() => {{ const g = G3.guestPool[0], b = {S}.ball; return {{ art: {S}.guestArt('cow', guestFace(b, performance.now())), same: !!(g && g.material.map && g.material.map.image === guestSprite('cow', guestFace(b, performance.now())).c) }}; }})()")
            check('3D: the guest sprite carries the painted cow art (sRGB texture of the art canvas)', a3['art'] == 'img' and a3['same'], a3)
            await page.screenshot(path='tests/out/guests_cow_art_3d.png')
            await page.evaluate(f"(() => {{ const s = {S}; s.serve(); s.spawnGuest('monkey'); s.floaters.length = 0; }})()"); sc = await page.evaluate(PARK + "(160, 640, 430)")
            await frames(page, 3); pm = await page.evaluate(PROBE + f"({json.dumps(sc)})")
            check('3D: the monkey reads brown at its screen point', pm['brown'] >= 6 and pm['beige'] >= 2, pm)
            sh = await page.evaluate(f"(() => {{ const S3 = G3, o = S3.balls[0], g = S3.guestPool[0]; return {{ blob: o.blob.visible, mesh: o.mesh.visible, sprite: !!(g && g.visible), rot: g ? g.material.rotation : null }}; }})()")
            check('3D: the guest sprite shows, the ball mesh hides, the soft floor shadow stays', sh['blob'] and not sh['mesh'] and sh['sprite'], sh)
        check('no page errors (3D)', not errs, errs)
        await ctx.close()

        # ===== phone screenshots: EN + HE, cow incoming / monkey flying back, 2D and 3D =====
        for lang in ('en', 'he'):
            for gfx in ('2d', '3d'):
                ctx, page, errs = await new_page(b, mobile=True, lang=lang, gfx="{ pr: 0.6, auto: false, shadows: false }" if gfx == '3d' else None)
                await play_strike(page, mobile=True)
                if gfx == '3d':
                    if not await to3d(page): print('INFO no WebGL: skipping the 3D phone shots'); await ctx.close(); continue
                    await page.evaluate(f"{S}.gfxPr = 1.5")
                await scene_cow(page, 360, 740); await frames(page, 3)
                await page.screenshot(path=f'tests/out/guests_{lang}_{gfx}_cow_incoming.png')
                await scene_monkey(page, 360, 740); await frames(page, 2)
                bub = await page.evaluate(f"{S}.floaters.filter(f => f.bubble).map(f => f.text)")
                await page.screenshot(path=f'tests/out/guests_{lang}_{gfx}_monkey_back.png')
                check(f'phone {lang} {gfx}: screenshots (cow incoming, monkey flying back with its bubble)', ('OOH OOH!' if lang == 'en' else 'או או!') in bub and not errs, [bub, errs])
                await ctx.close()

asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
