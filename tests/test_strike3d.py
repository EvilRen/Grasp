exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Strike in 3D: the WebGL renderer (three.js r128, loaded when Strike starts). The game logic is untouched; the camera reproduces proj(),
# so hit tests, ballScreen(), brickScreen() and the ui rects hold in both renderers. Headless Chromium's WebGL is SwiftShader (a CPU
# rasterizer): the checks run at a low fixed pixel ratio and the screenshots at full resolution. Without WebGL the suite checks the 2D fallback.
S = "__grasp.strike"
FRAMES = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
PIX2D = "((x, y) => { const d = ctx.getImageData(Math.round(x * DPR), Math.round(y * DPR), 1, 1).data; return [d[0], d[1], d[2], d[3]]; })"
FREEZE = f"(() => {{ const s = {S}; s.serveAt = performance.now() + 1e9; for (const b of s.balls) {{ b.speed = 0; b.trail.length = 0; }} }})()"  # the ball parked, no serve coming
def brickish(c): return c[0] > 120 and c[0] > c[1] + 35 and c[0] > c[2] + 50  # terracotta (lit, tone-mapped)
def coral(c): return c[0] > 170 and c[0] > c[2] + 40

async def frames(page, n=1):
    for _ in range(n): await page.evaluate(FRAMES)

async def open_page(b, mobile=False, query='', gfx="{ pr: 0.5, auto: false }", block_three=False, reqs=None):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); errs = []
    await routes(page)
    if block_three:  # the CDNs unreachable: every three.js request fails (registered after the harness routes, so it wins)
        async def abort(route): await route.abort()
        await page.route('**/three*.js', abort)
    if reqs is not None: page.on('request', lambda r: reqs.append(r.url) if 'three' in r.url else None)
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + (f"window.__graspGfx = {gfx};" if gfx else "window.__graspGfx = {};"))
    await page.goto('http://localhost:8765/index.html' + query); await page.wait_for_timeout(600)
    await page.evaluate(f"{S}.extrasOff = true; __grasp.CONFIG.STRIKE_PU_RATE = 0")
    return ctx, page, errs

async def start(page, mobile=False):
    if mobile: await page.tap('.modes button[data-mode=strike]'); await page.tap('#mouseBtn')
    else: await page.click('.modes button[data-mode=strike]'); await page.click('#mouseBtn')
    await page.wait_for_function(f"gameMode === 'strike' && {S}.ball", timeout=10000)


CLEAR = "(() => { G3.chunks.forEach(c => c.on = false); G3.pAdd.length = G3.pDust.length = 0; })()"
LIVE = "G3.chunks.filter(c => c.on)"

async def hold(page, ms):  # let the effects clock run ms, then hold the effects still
    t = await page.evaluate("G3.fxT")
    await page.wait_for_function(f"G3.fxT >= {t} + {ms}", timeout=30000, polling=40)
    await page.evaluate(f"{S}.gfxFreeze = true")

async def smash_kind(page, kind, power):  # a fresh wall of the kind at z 900 (others behind it), smashed by the ball at the given tier; resolves once chunks fly
    await page.evaluate(f"""(() => {{ const s = {S}; __grasp.CONFIG.STRIKE_BOSS_EVERY = 1000; {CLEAR}; s.boss = null; s.walls.length = 0; s.debris.length = 0; s.ui.tag = s.ui.levelBanner = null;
      s.spawnWall('{kind}', 900); s.spawnWall('brick', 1300); s.spawnWall('steel', 1700); const w = s.walls[0], t = '{kind}' === 'tnt' ? w.bricks.find(k => k.tnt) : null; if (t) s.smashTest('{power}', t.col, t.row); else s.smashTest('{power}'); }})()""")
    await page.wait_for_function(f"{S}.chunks3d > 0", timeout=15000, polling=30)

async def step2(page):  # Strike 3D step 2: shatter chunks, glow, impact juice, the 3D boss, capsule shells, quality tiers
    S_ = S
    # quality tier rule (pure) and the tier switch
    qp = await page.evaluate(f"[[1, 8, 0], [2, 8, 0], [3, 8, 0], [1, 4, 0], [2, 2, 0], [1, 0, 0], [1, 8, 60], [1, 8, 45], [1, 8, 30], [3, 8, 60], [1, 2, 60]].map(a => {S}.gfxQualityPick(...a))")
    check('gfxQuality rule: 8 cores -> high (dpr 3 -> medium), 4 cores -> medium, 2 -> low, unknown -> medium; the first-3-s fps caps it (60 keeps, 45 -> medium, 30 -> low; never above the device tier)',
          qp == ['high', 'high', 'medium', 'medium', 'low', 'medium', 'high', 'medium', 'low', 'medium', 'low'], qp)
    q0 = await page.evaluate(f"{S}.gfxQuality"); print('INFO gfxQuality picked on SwiftShader:', q0, await page.evaluate(f"{S}.gfxInfo.qFps"))
    lo = await page.evaluate(f"(() => {{ const s = {S}; s.gfxQuality = 'low'; const r = {{ q: s.gfxQuality, lights: G3.flashes.length, inScene: G3.flashAll.filter(f => f.L.parent).length, shadow: G3.key.castShadow, cap: G3.qc.chunks }}; s.gfxQuality = 'high'; r.hi = {{ q: s.gfxQuality, lights: G3.flashes.length, cap: G3.qc.chunks, ball: !!G3.ballLight.parent }}; return r; }})()")
    check('strike.gfxQuality: low drops the flash lights, shadows and most of the chunk pool; high has 3 flash lights, a light on the SUPER ball and 160 chunks', q0 in ('high', 'medium', 'low') and lo['q'] == 'low' and lo['lights'] == 0 and lo['inScene'] == 0 and not lo['shadow'] and lo['cap'] < 80 and lo['hi'] == {'q': 'high', 'lights': 3, 'cap': 160, 'ball': True}, lo)
    await frames(page, 2)
    # a brick breaks: chunks that move, fall, bounce once on the floor and recycle
    await smash_kind(page, 'brick', 'hard')
    a = await page.evaluate(f"(() => {{ const L = {LIVE}; return {{ n: L.length, cls: [...new Set(L.map(c => c.cls))], kinds: [...new Set(L.map(c => c.kind))], pos: L.slice(0, 8).map(c => [c.x, c.y, c.z]), b0: G3.chBounces, d0: G3.chDone, geos: G3.chunkGeos.map(g => g.tris), sets: G3.chunkSets.map(t => t.length) }}; }})()")
    await hold(page, 300); await page.evaluate(f"{S}.gfxFreeze = false")
    b = await page.evaluate(f"(() => {{ const L = G3.chunks.slice(0, 8); return L.map(c => [c.x, c.y, c.z]); }})()")
    moved = sum(1 for p, q in zip(a['pos'], b) if abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) > 5)
    check(f"a brick breaks in 3D: {a['n']} convex chunks (patterns of {a['sets']} cells; every cell a closed polyhedron of >= 4 triangles), stone material, flying ({moved}/8 moved within 300 ms of effects time)",
          a['n'] >= 4 and a['cls'] == ['stone'] and a['sets'] == [4, 6, 8] and min(a['geos']) >= 4 and moved >= 6, a)
    await page.wait_for_function("G3.chBounces > " + str(a['b0']), timeout=40000, polling=60)
    fall = await page.evaluate(f"(() => {{ const {{ B }} = corridor(); return G3.chunks.filter(c => c.on && c.bounced).map(c => +(c.y + B).toFixed(1)).slice(0, 5); }})()")
    check('chunks fall under gravity and bounce once on the corridor floor (a bounced chunk sits just above the floor plane)', all(-1 <= v < 200 for v in fall) and len(fall) > 0, fall)
    await page.wait_for_function(f"{S}.chunks3d === 0", timeout=60000, polling=100)
    rc = await page.evaluate("({ done: G3.chDone, n: __grasp.strike.chunks3d })")
    check('the chunks fade, shrink and recycle: the live count goes back to 0', rc['n'] == 0 and rc['done'] - a['d0'] >= a['n'], rc)
    # the pool cap: a SUPER through a whole wall plus 60 more bricks never exceeds 160
    cap = await page.evaluate(f"(() => {{ const s = {S}; {CLEAR}; s.walls.length = 0; const w = s.spawnWall('brick', 900); for (const k of w.bricks) g3Shatter(w, k, {{ x: 0, y: 0 }}, 'super'); for (let i = 0; i < 60; i++) g3Shatter(w, w.bricks[i % w.bricks.length], {{ x: 0, y: 0 }}, 'hard'); return {{ n: s.chunks3d, bricks: w.bricks.length }}; }})()")
    check(f"chunk pool capped: {cap['bricks'] + 60} bricks shattered at once -> {cap['n']} live chunks (<= 160; the most faded recycle first)", 0 < cap['n'] <= 160, cap)
    await page.evaluate(CLEAR)
    # glass / steel / TNT variants
    await smash_kind(page, 'glass', 'medium'); await page.evaluate(f"{S}.gfxFreeze = true"); await frames(page, 1)
    gl = await page.evaluate(f"(() => {{ const L = {LIVE}; return {{ n: L.length, cls: [...new Set(L.map(c => c.cls))], thin: L.every(c => c.sz < c.sy * 0.25), mat: G3.chMats.glass.transparent && G3.chMats.glass.opacity < 0.6, glints: G3.fxAdd.count }}; }})()")
    check('glass breaks into thin translucent shards (8-cell pattern, transparent physical material) with sparkle glints', gl['n'] >= 8 and gl['cls'] == ['glass'] and gl['thin'] and gl['mat'] and gl['glints'] > 0, gl)
    await page.evaluate(f"{S}.gfxFreeze = false")
    await smash_kind(page, 'steel', 'hard'); await page.evaluate(f"{S}.gfxFreeze = true")
    st = await page.evaluate(f"(() => {{ const L = {LIVE}; return {{ n: L.length, cls: [...new Set(L.map(c => c.cls))], metal: G3.chMats.steel.metalness, sparks: G3.pAdd.filter(p => p.cell === 1).length, dark: L.every(c => c.col.r < 0.4) }}; }})()")
    check('steel breaks into darker metallic plates with sparks (streaks)', st['n'] >= 4 and st['cls'] == ['steel'] and st['metal'] > 0.8 and st['sparks'] >= 4 and st['dark'], st)
    await page.evaluate(f"{S}.gfxFreeze = false")
    t0 = await page.evaluate("G3.tnts || 0")
    await smash_kind(page, 'tnt', 'medium'); await page.evaluate(f"{S}.gfxFreeze = true"); await frames(page, 1)
    tn = await page.evaluate(f"(() => {{ const L = {LIVE}.filter(c => c.kind === 'tnt'); return {{ tnts: G3.tnts, charred: L.length, dark: L.every(c => c.col.r < 0.15 && c.col.g < 0.05), light: Math.max(...G3.flashes.map(f => f.L.intensity)), boom: G3.booms.some(b => b.on && b.shell.visible) }}; }})()")
    check(f"TNT: charred chunks, an expanding emissive fireball and a point-light flash (peak {tn['light']:.2f})", tn['tnts'] > t0 and tn['charred'] >= 4 and tn['dark'] and tn['light'] > 0.5 and tn['boom'], tn)
    await page.evaluate(f"{S}.gfxFreeze = false")
    await page.wait_for_function("G3.flashes.every(f => !f.on && f.L.intensity === 0) && G3.booms.every(b => !b.on && !b.shell.visible)", timeout=30000, polling=60)
    check('... and the flash light and the fireball fade out (intensity 0, hidden)', True)
    await page.evaluate(f"(() => {{ {CLEAR}; __grasp.strike.walls.length = 0; }})()")
    # the SUPER ball: glow sprite, bloom halo, light trail ribbon, a light riding it
    await page.evaluate(f"(() => {{ const s = {S}; s.setBallZ(500, innerWidth * 0.45, innerHeight * 0.5); const b = s.ball; b.super = true; b.tier = 'super'; b.dir = -1; b.speed = 0.4; }})()")
    await frames(page, 4)
    su = await page.evaluate(f"(() => {{ const o = G3.balls[0]; return {{ glow: o.glow.visible, halo: o.halo.visible, haloBig: o.halo.scale.x > o.glow.scale.x, rib: o.rib.visible, tris: o.rib.geometry.drawRange.count / 3, add: o.rib.material.blending === G3.T.AdditiveBlending, light: G3.ballLight.intensity }}; }})()")
    check('SUPER ball: glow sprite + a wider bloom halo + an additive trail ribbon through its recent positions + a light riding it', su['glow'] and su['halo'] and su['haloBig'] and su['rib'] and su['tris'] >= 2 and su['add'] and su['light'] > 0, su)
    await page.evaluate(f"{S}.ball.super = false; {S}.ball.tier = ''"); await frames(page, 2)
    nb = await page.evaluate("({ glow: G3.balls[0].glow.visible, rib: G3.balls[0].rib.visible, light: G3.ballLight.intensity })")
    check('a plain ball: no glow, no ribbon, no ball light', not nb['glow'] and not nb['rib'] and nb['light'] == 0, nb)
    # the boss in 3D: a body of real bricks (with depth) behind the face plane; a hit pops bricks off as chunks
    await page.evaluate(f"(() => {{ const s = {S}; {CLEAR}; __grasp.CONFIG.STRIKE_BOSS_EVERY = 8; const b = s.spawnBoss(1); b.z = 900; b.speed = 0; s.ui.tag = null; s.setBallZ(300, innerWidth * 0.45, innerHeight * 0.5); }})()"); await page.evaluate(FREEZE)
    await frames(page, 3)
    bo = await page.evaluate(f"(() => {{ const bb = G3.bossB; return {{ n: G3.bossBody.count, list: bb.list.length, depth: bb.d, body: G3.bossBody.visible, back: G3.bossBack.visible, face: G3.boss.visible, faceZ: G3.boss.position.z, bodyZ: new G3.T.Vector3().setFromMatrixPosition((() => {{ const m = new G3.T.Matrix4(); G3.bossBody.getMatrixAt(0, m); return m; }})()).z, bossZ: {S}.boss.z }}; }})()")
    check(f"boss in 3D: {bo['n']} instanced bricks with depth ({bo['depth']:.0f}) and a dark back plate; the face plane at the boss depth, just in front of the bricks", bo['n'] == bo['list'] and bo['n'] >= 40 and bo['depth'] > 10 and bo['body'] and bo['back'] and bo['face'] and abs(bo['faceZ'] + bo['bossZ']) < 0.01 and bo['bodyZ'] < bo['faceZ'], bo)
    await page.evaluate(f"{S}.bossHit('hard')"); await frames(page, 2)
    bh = await page.evaluate(f"({{ n: G3.bossBody.count, chunks: {LIVE}.filter(c => c.kind === 'boss').length, ui: !!{S}.ui.boss, bar: !!({S}.ui.boss && {S}.ui.boss.bar) }})")
    check(f"a boss hit pops bricks off its body as chunks ({bo['n']} -> {bh['n']} bricks, {bh['chunks']} chunks); the face boxes and health bar stay on the 2D overlay", bh['n'] < bo['n'] and bh['chunks'] >= 6 and bh['ui'] and bh['bar'], bh)
    await page.evaluate(f"(() => {{ const s = {S}; s.boss = null; {CLEAR}; s.walls.length = 0; }})()"); await frames(page, 2)
    # capsules: a glossy transparent shell, the icon inside, a glow
    await page.evaluate(f"{S}.spawnCapsule('multi', 700, 0, 0)"); await frames(page, 3)
    cp = await page.evaluate(f"(() => {{ const o = G3.capPool[0], c = {S}.capsules[0]; const r0 = o.shell.rotation.y; return {{ shell: o.shell.visible, tr: o.shell.material.transparent && o.shell.material.opacity < 1, gloss: o.shell.material.clearcoat, icon: o.icon.visible && !!o.icon.material.map, glow: o.glow.visible && o.glow.material.blending === G3.T.AdditiveBlending, at: [o.shell.position.x - c.x, o.shell.position.z + c.z], r0 }}; }})()")
    await frames(page, 2); r1 = await page.evaluate("G3.capPool[0].shell.rotation.y")
    check('power-up capsule in 3D: a glossy transparent shell (clearcoat) that spins, the icon sprite inside, an additive glow', cp['shell'] and cp['tr'] and cp['gloss'] >= 1 and cp['icon'] and cp['glow'] and abs(cp['at'][0]) < 0.5 and abs(cp['at'][1]) < 0.5 and r1 != cp['r0'], [cp, r1])
    await page.evaluate(f"{S}.capsules.length = 0"); await frames(page, 1)
    # parity still exact with every effect in the scene
    par = await page.evaluate(f"""(() => {{ const {{ L, R, T, B }} = corridor(); let worst = 0; for (const z of [0, 400, 1500]) for (const [x, y] of [[L, T], [R, B], [0, 0]]) {{ const a = proj(x, y, z), q = {S}.project3d(x, y, z); worst = Math.max(worst, Math.hypot(a.x - q.x, a.y - q.y)); }} return worst; }})()""")
    check(f'projection parity unchanged by step 2 (worst {par:.4f} px)', par < 1.5, par)
    await page.evaluate(f"(() => {{ const s = {S}; __grasp.CONFIG.STRIKE_BOSS_EVERY = 8; s.setLevel(1); s.walls.length = 0; s.spawnWall('brick', 900); }})()")

async def shatter_shots(page, tag, pr):  # mid-shatter screenshots at full resolution: brick, glass, TNT, a SUPER smash, the boss
    await page.evaluate(f"{S}.gfxQuality = 'high'; {S}.setLevel(6)")
    for name, kind, power, ms in [('brick', 'brick', 'hard', 220), ('glass', 'glass', 'medium', 200), ('tnt', 'tnt', 'medium', 150), ('super', 'brick', 'super', 220)]:
        await smash_kind(page, kind, power); await hold(page, ms)
        if name == 'super':
            await page.evaluate(f"(() => {{ const b = {S}.ball; b.super = true; b.dir = -1; b.speed = 0; b.z = 520; b.x = -innerWidth * 0.12; b.y = innerHeight * 0.08; b.trail.length = 0; G3.balls[0].hist.length = 0; for (let i = 8; i >= 0; i--) G3.balls[0].hist.push({{ x: b.x + 40 * i, y: -b.y - 28 * i, z: -b.z + 60 * i, t: performance.now() - 25 * i }}); }})()")
        await page.evaluate(f"{S}.gfxPr = {pr}"); await frames(page, 2); await page.screenshot(path=f'tests/out/strike3d2_{tag}_{name}.png'); await page.evaluate(f"{S}.gfxPr = 0.5; {S}.gfxFreeze = false")
        await page.evaluate(f"{S}.ball = null; {S}.serve(); {S}.setBallZ(2300, 30, 30)")
    await page.evaluate(f"(() => {{ const s = {S}; __grasp.CONFIG.STRIKE_BOSS_EVERY = 8; {CLEAR}; s.walls.length = 0; const b = s.spawnBoss(1); b.z = 900; b.speed = 0; s.ui.tag = null; s.setBallZ(300, innerWidth * 0.45, innerHeight * 0.5); s.serveAt = performance.now() + 1e9; for (const q of s.balls) q.speed = 0; }})()")
    await frames(page, 2); await page.evaluate(f"{S}.bossHit('hard'); {S}.bossHit('super')"); await hold(page, 180)
    await page.evaluate(f"{S}.gfxPr = {pr}"); await frames(page, 2); await page.screenshot(path=f'tests/out/strike3d2_{tag}_boss.png'); await page.evaluate(f"{S}.gfxPr = 0.5; {S}.gfxFreeze = false")
    await page.evaluate(f"(() => {{ const s = {S}; s.boss = null; {CLEAR}; }})()")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ===== desktop: lazy load, 3D on, parity =====
        reqs = []
        ctx, page, errs = await open_page(b, reqs=reqs)
        pre = await page.evaluate("({ three: typeof THREE, hidden: $('stage3d').hidden, gfx: __grasp.strike.gfx })")
        check('before Strike starts: three.js not requested, the WebGL layer hidden, gfx 2d', pre['three'] == 'undefined' and not reqs and pre['hidden'] and pre['gfx'] == '2d', [pre, reqs])
        await start(page)
        await page.wait_for_function(f"{S}.gfx === '3d' || {S}.gfxInfo.state === 'failed'", timeout=20000)
        info = await page.evaluate(f"{S}.gfxInfo")
        webgl = info['state'] == 'ready'
        print('INFO renderer:', info)
        if not webgl:  # no WebGL here: the 2D renderer carries on
            await frames(page, 2); fl = await page.evaluate(PIX2D + "(640, 796)")
            check('no WebGL: strike.gfx stays 2d, the 2D corridor is drawn (opaque floor pixel)', await page.evaluate(f"{S}.gfx") == '2d' and fl[3] == 255 and fl[2] > fl[0], [info, fl])
        else:
            check('Strike starts: three.js r128 loads once (cdnjs URL), strike.gfx = 3d, the WebGL layer shown', await page.evaluate(f"{S}.gfx") == '3d' and await page.evaluate("THREE.REVISION") == '128' and len(reqs) == 1 and 'cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js' in reqs[0] and not await page.evaluate("$('stage3d').hidden"), [reqs, info])
            lay = await page.evaluate("(() => { const a = $('stage3d'), c = $('stage'), sa = getComputedStyle(a); return { under: !!(a.compareDocumentPosition(c) & Node.DOCUMENT_POSITION_FOLLOWING), pe: sa.pointerEvents, pos: sa.position, w: a.getBoundingClientRect().width, h: a.getBoundingClientRect().height }; })()")
            check('#stage3d sits under the 2D canvas (earlier in the DOM, both fixed full-screen), never takes pointer events', lay['under'] and lay['pe'] == 'none' and lay['pos'] == 'fixed' and lay['w'] == 1280 and lay['h'] == 800, lay)
            await page.mouse.move(1180, 700); await page.evaluate(FREEZE)
            await frames(page, 2)
            ov = await page.evaluate(PIX2D + "(640, 600)")
            check('3D mode: the 2D canvas is transparent over the corridor (it carries the overlays only)', ov[3] < 60, ov)
            # projection parity: the WebGL camera puts every world point where proj() does
            par = await page.evaluate(f"""(() => {{ const {{ L, R, T, B }} = corridor(), Z = __grasp.CONFIG.STRIKE_Z_FAR, pts = [];
              for (const z of [-200, 0, 150, 700, 1500, Z]) for (const [x, y] of [[L, T], [R, B], [0, 0], [L * 0.5, B * 0.7], [R * 0.9, T * 0.3]]) pts.push([x, y, z]);
              let worst = 0; for (const [x, y, z] of pts) {{ const a = proj(x, y, z), q = {S}.project3d(x, y, z); worst = Math.max(worst, Math.hypot(a.x - q.x, a.y - q.y)); }} return {{ n: pts.length, worst }}; }})()""")
            check(f"projection parity: {par['n']} world points, WebGL camera vs proj() within 1.5 px (worst {par['worst']:.4f} px)", par['worst'] < 1.5, par)
            sh = await page.evaluate(f"(() => {{ view.x = 9; view.y = -6; gfx3dCamera(); const a = proj(100, 50, 400), q = {S}.project3d(100, 50, 400); view.x = view.y = 0; gfx3dCamera(); return Math.hypot(a.x + 9 - q.x, a.y - 6 - q.y); }})()")
            check('the screen shake moves the 3D camera with the 2D drawing (parity under a shake offset)', sh < 1.5, sh)
            # a brick: its brickScreen() rect is where the 3D brick colour is
            await page.evaluate(f"{S}.setBallZ(2300, 30, 30)"); await page.evaluate(FREEZE); await frames(page, 2)
            bk = await page.evaluate(f"""(() => {{ const s = {S}, w = s.walls[0], r = s.brickScreen(w, 0, 1), px = (x, y) => s.pixel(x, y);
              return {{ kind: w.kind, z: w.z, r, c: px(r.x, r.y), inner: [[-0.3, -0.3], [0.3, -0.3], [-0.3, 0.3], [0.3, 0.3]].map(([a, b]) => px(r.x + a * r.w, r.y + b * r.h)), out: px(r.x - r.w * 0.5 - 6, r.y) }}; }})()""")
            check('brick probe: the brickScreen() rect of brick (0,1) shows the terracotta 3D brick at its centre and inner corners', bk['kind'] == 'brick' and brickish(bk['c']) and all(brickish(c) for c in bk['inner']), bk)
            check('just outside that rect (left of the wall): the corridor, not a brick', not brickish(bk['out']), bk['out'])
            # the ball at ballScreen()
            await page.evaluate(f"{S}.setBallZ(420, 760, 520)"); await page.evaluate(FREEZE); await frames(page, 2)
            bl = await page.evaluate(f"(() => {{ const s = {S}, q = s.ballScreen(); return {{ q, c: s.pixel(q.x, q.y), c3: s.pixel3d(q.x, q.y), e: s.pixel(q.x + q.r * 0.6, q.y + q.r * 0.2) }}; }})()")
            check('ball: the pixel at ballScreen() is the coral 3D ball (composited and in the WebGL layer)', coral(bl['c']) and coral(bl['c3']) and coral(bl['e']), bl)
            # holes: knocked-out bricks leave holes; behind them (walls behind removed) the dark corridor shows
            await page.evaluate(f"{S}.setBallZ(2300, 30, 30)"); await page.evaluate(FREEZE)
            ho = await page.evaluate(f"""(async () => {{ const s = {S}, w = s.walls[0]; s.walls.length = 1; const k = w.bricks.find(q => q.col === 1 && q.row === 1), r = s.brickScreen(w, 1, 1), before = s.pixel(r.x, r.y);
              k.alive = false; w.left--; await {FRAMES}; return {{ before, after: s.pixel(r.x, r.y), next: s.pixel(s.brickScreen(w, 2, 1).x, r.y), inst: G3.walls.get(w.id).ims.brick.count, alive: w.bricks.filter(q => q.alive).length }}; }})()""")
            check('a removed brick leaves a hole (no instance; the pixel goes dark), its neighbour stays a brick', brickish(ho['before']) and not brickish(ho['after']) and sum(ho['after']) < sum(ho['before']) - 120 and brickish(ho['next']) and ho['inst'] == ho['alive'], ho)
            # wall kinds and debris
            await page.evaluate(f"(() => {{ const s = {S}; s.walls.length = 0; s.spawnWall('glass', 700); s.spawnWall('steel', 1100); s.spawnWall('tnt', 1500); }})()"); await frames(page, 2)
            kd = await page.evaluate(f"(() => {{ const s = {S}, e = s.walls.map(w => ({{ kind: w.kind, ims: Object.fromEntries(Object.entries(G3.walls.get(w.id).ims).filter(([k, m]) => m.count).map(([k, m]) => [k, m.count])) }})); return e; }})()")
            check('glass / steel / TNT walls: instanced glass panes, steel plates, and TNT crates among the bricks', kd[0]['ims'].get('glass', 0) > 0 and kd[1]['ims'].get('steel', 0) > 0 and kd[2]['ims'].get('tnt', 0) >= 2, kd)
            gl = await page.evaluate(f"(() => {{ const s = {S}, w = s.walls[0], r = s.brickScreen(w, 1, 1); return {{ glass: s.pixel(r.x, r.y), mat: G3.mats.glass.transparent && G3.mats.glass.opacity < 1 }}; }})()")
            check('glass is translucent (a transparent material; the pane pixel is pale blue, not opaque brick)', gl['mat'] and gl['glass'][2] >= gl['glass'][0], gl)
            await step2(page)
            await page.evaluate(f"{S}.ball = null; {S}.serve(); {S}.setBallZ(2300, 30, 30)"); await page.evaluate(FREEZE)
            # one renderer, reused across rounds; pixel ratio
            r0 = await page.evaluate("G3.r"); await page.click('#resetBtn'); await page.wait_for_timeout(300)
            check('one WebGL renderer, reused across rounds (reset keeps it)', await page.evaluate("(() => { const r = G3.r; return !!r && G3.inits === 1 && document.querySelectorAll('canvas#stage3d').length === 1; })()"))
            # fps
            await page.evaluate(f"{S}.setBallZ(1800, 640, 400)"); await page.wait_for_timeout(2600)
            fps = await page.evaluate(f"{S}.gfxFps"); print(f'INFO gfxFps at pixel ratio 0.5, 1280x800, SwiftShader: {fps}')
            check('strike.gfxFps is measured while 3D draws', fps > 0, fps)
            # setGfx('2d') / ('3d') at runtime
            sw = await page.evaluate(f"(async () => {{ const s = {S}, a = await __grasp.setGfx('2d'); await {FRAMES}; const two = {{ gfx: s.gfx, hidden: $('stage3d').hidden, px: {PIX2D}(640, 796) }}; const c = await __grasp.setGfx('3d'); await {FRAMES}; return {{ a, two, c, hidden: $('stage3d').hidden }}; }})()")
            check("__grasp.setGfx('2d'): the 2D corridor at once (opaque floor), the WebGL layer hidden; setGfx('3d') brings it back", sw['a'] == '2d' and sw['two']['gfx'] == '2d' and sw['two']['hidden'] and sw['two']['px'][3] == 255 and sw['c'] == '3d' and not sw['hidden'], sw)
            # screenshots: level 1 (a broken wall, the ball incoming) and level 6 (glass, steel, TNT; a SUPER ball, debris)
            for lv in (1, 6):
                await stage(page, lv); await page.evaluate(f"{S}.gfxPr = 1"); await frames(page, 2)
                await page.screenshot(path=f'tests/out/strike3d_desktop_l{lv}.png'); await page.evaluate(f"{S}.gfxPr = 0.5")
            await shatter_shots(page, 'desktop', 1)
        check('desktop: no page errors', not errs, errs); await ctx.close()

        if webgl:
            # ===== phone: parity, default pixel ratio min(dpr, 2), screenshots =====
            ctx, page, errs = await open_page(b, mobile=True, gfx="{ auto: false }")
            await start(page, mobile=True); await page.wait_for_function(f"{S}.gfx === '3d'", timeout=20000)
            check('phone (dpr 3): the renderer pixel ratio is min(devicePixelRatio, 2) = 2', await page.evaluate(f"{S}.gfxPr") == 2 and await page.evaluate("G3.r.getPixelRatio()") == 2)
            await page.evaluate(f"{S}.gfxPr = 0.4")
            par = await page.evaluate(f"""(() => {{ const {{ L, R, T, B }} = corridor(), pts = []; for (const z of [0, 300, 1200, 2400]) for (const [x, y] of [[L, T], [R, B], [L * 0.3, B * 0.8]]) pts.push([x, y, z]);
              let worst = 0; for (const [x, y, z] of pts) {{ const a = proj(x, y, z), q = {S}.project3d(x, y, z); worst = Math.max(worst, Math.hypot(a.x - q.x, a.y - q.y)); }} return worst; }})()""")
            check(f'phone projection parity within 1.5 px (worst {par:.4f})', par < 1.5, par)
            await page.evaluate(f"{S}.setBallZ(420, 200, 470)"); await page.evaluate(FREEZE); await frames(page, 2)
            bl = await page.evaluate(f"(() => {{ const s = {S}, q = s.ballScreen(); return [[0, 0], [-0.45, 0.1], [0.4, -0.2]].map(([a, b]) => s.pixel(q.x + a * q.r, q.y + b * q.r)); }})()")
            check('phone: the pixels at ballScreen() are the coral ball (2 of 3 probes: the spinning seam may cross one)', sum(1 for c in bl if coral(c)) >= 2, bl)
            for lv in (1, 6):
                await stage(page, lv); await page.evaluate(f"{S}.gfxPr = 2"); await frames(page, 2)
                await page.screenshot(path=f'tests/out/strike3d_phone_l{lv}.png'); await page.evaluate(f"{S}.gfxPr = 0.4")
            await shatter_shots(page, 'phone', 2)
            check('phone: no page errors', not errs, errs); await ctx.close()

            # ===== the low-fps fallback: full resolution on a software GPU stays < 24 fps, so after 4 s Strike goes back to 2D =====
            ctx, page, errs = await open_page(b, gfx="{ pr: 1 }")
            await start(page); await page.wait_for_function(f"{S}.gfxInfo.state === 'ready'", timeout=20000)
            await page.wait_for_function(f"{S}.gfx === '2d'", timeout=30000)
            fb = await page.evaluate(f"({{ info: {S}.gfxInfo, fps: {S}.gfxFps, hidden: $('stage3d').hidden }})"); dt = fb['info']['fallbackAt'] - fb['info']['onAt']
            check(f'auto fallback: 3D fps stayed < 24 ({fb["fps"]} fps) for 4 s -> back to 2D {dt / 1000:.1f} s after 3D started (the pixel ratio stepped down first), the WebGL layer hidden', fb['info']['fallback'] == 'fps' and fb['fps'] < 24 and fb['hidden'] and 4000 <= dt < 15000 and fb['info']['pr'] < 1, fb)
            await frames(page, 2); fl = await page.evaluate(PIX2D + "(640, 796)")
            check('after the fallback the 2D corridor draws (opaque floor pixel)', fl[3] == 255 and fl[2] > fl[0], fl)
            check('fallback: no page errors', not errs, errs); await ctx.close()

        # ===== ?gfx=2d forces the 2D renderer: three.js never requested =====
        reqs = []
        ctx, page, errs = await open_page(b, query='?gfx=2d', gfx=None, reqs=reqs)
        await start(page); await page.wait_for_timeout(1200); await frames(page, 2)
        st = await page.evaluate(f"({{ gfx: {S}.gfx, three: typeof THREE, hidden: $('stage3d').hidden, info: {S}.gfxInfo, floor: {PIX2D}(640, 796) }})")
        check('?gfx=2d: strike.gfx 2d, three.js never requested, the WebGL layer hidden, the 2D corridor drawn', st['gfx'] == '2d' and st['three'] == 'undefined' and not reqs and st['hidden'] and st['floor'][3] == 255 and st['floor'][2] > st['floor'][0], [st, reqs])
        check('?gfx=2d: no page errors', not errs, errs); await ctx.close()

        # ===== three.js unreachable (both CDNs abort): Strike plays on in 2D =====
        ctx, page, errs = await open_page(b, block_three=True)
        await start(page); await page.wait_for_function(f"{S}.gfxInfo.state === 'failed'", timeout=20000); await frames(page, 2)
        st = await page.evaluate(f"({{ gfx: {S}.gfx, info: {S}.gfxInfo, hidden: $('stage3d').hidden, floor: {PIX2D}(640, 796), ball: !!{S}.ball }})")
        check('three.js failed to load (cdnjs and jsDelivr aborted): gfx 2d, the error kept, the 2D corridor drawn, the ball in play', st['gfx'] == '2d' and 'three.js failed to load' in st['info']['err'] and st['hidden'] and st['floor'][3] == 255 and st['ball'], st)
        await page.evaluate(f"{S}.setBallZ(900, 640, 380)"); await frames(page, 2)
        bp = await page.evaluate(PIX2D + "(640, 380)")
        check('fallback: the 2D ball is drawn', coral(bp), bp)
        check('load failure: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)

async def stage(page, lv):  # a staged scene for the screenshots: level 1 = a wall with a hole and the ball coming in; level 6 = glass, steel, TNT walls and a SUPER ball
    await page.evaluate(f"""(() => {{ const s = {S}; s.setLevel({lv}); s.walls.length = 0; s.debris.length = 0; s.ui.levelBanner = s.ui.levelUp = s.ui.tag = null; s.lives = s.maxLives;
      if ({lv} === 1) {{ const w = s.spawnWall('brick', 960); s.spawnWall('brick', 1360); s.spawnWall('brick', 1760); for (const k of w.bricks) if (k.col >= 1 && k.col <= 2 && k.row >= 1 && k.row <= 2) {{ k.alive = false; w.left--; }}
        w.hp = 2; for (const k of w.bricks) k.hp = 2; w.bricks[0].hp = 1; w.bricks[0].dent = 1; s.setBallZ(380, innerWidth * 0.56, innerHeight * 0.62); }}
      else {{ const g = s.spawnWall('glass', 700), st = s.spawnWall('steel', 1100); s.spawnWall('tnt', 1500); s.spawnWall('moving', 1900);
        for (const k of g.bricks) if ((k.col + k.row) % 3 === 0) {{ k.alive = false; g.left--; }}
        for (const k of st.bricks) if (k.row === 1 && k.col < 3) {{ k.alive = false; st.left--; }} st.bricks[st.cols * 2 + 1].dent = 1; st.bricks[st.cols * 2 + 1].hp = 2;
        s.setBallZ(300, innerWidth * 0.42, innerHeight * 0.6); const b = s.ball; b.super = true; b.tier = 'super'; b.dir = -1;
        for (let i = 6; i >= 1; i--) {{ const q = ballScreen({{ x: b.x - 30 * i, y: b.y + 18 * i, z: b.z - 28 * i }}); b.trail.push({{ x: q.x, y: q.y, r: q.r, t: performance.now() - 20 * i }}); }}
        for (let i = 0; i < 14; i++) s.debris.push({{ x: (Math.random() - 0.5) * 300, y: (Math.random() - 0.5) * 200, z: 600 + Math.random() * 300, vx: 0, vy: 0, vz: 0, rot: Math.random() * 6, vr: 0, k: 0.3 + Math.random() * 0.2, level: 6, kind: i % 3 ? 'glass' : 'brick', shard: i % 3 > 0, w: 220, h: 110, life: 1, decay: 0 }}); }}
      s.serveAt = performance.now() + 1e9; for (const b of s.balls) b.speed = 0; }})()""")

asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
