exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Smash (v3): five scenes of breakable Matter things (the revealing brick wall, a room, a city, toy towers, a fruit market); the Smash tile opens
# its map (Free play + 20 stages); mouse / touch: a tap is a punch at that point, a swipe a sweeping hit (strength by speed); the camera: any contact.
# v3 ("it ends far too fast"): things take 2-5 hits with cracks that grow, a wobble and a deeper knock each hit; weak chain reactions (a fall is one
# hit's worth, never the end of a thing not yet cracked); a swipe hits each thing once; waves: the scene scrolls on when most of a wave is smashed;
# hairline cracks ahead; a boss with a health bar at the end. This suite: the map, each scene's build, multi-hit + cracks, weak chains, waves, the
# boss, sounds, debris, free play, the pause sheet, mouse / touch / camera. Stages, clocks, stars, the stage-length simulation, voice, screenshots: test_smash2.py.
FIST_JS = """
window.mkFist = (cx, cy) => { // all four fingertips curled back toward the wrist, thumb away from the index tip (no pinch)
  const L = Array.from({length:21}, () => ({x: cx, y: cy + 0.10, z: 0}));
  L[0] = {x: cx, y: cy + 0.30, z:0}; L[9] = {x: cx, y: cy + 0.10, z:0}; L[4] = {x: cx - 0.14, y: cy + 0.16, z:0};
  for (const [tip, pip] of [[8,6],[12,10],[16,14],[20,18]]) { L[pip] = {x: cx + 0.02, y: cy + 0.02, z:0}; L[tip] = {x: cx + 0.02, y: cy + 0.14, z:0}; }
  return L;
};
window.fistAt = (X, Y) => { const B = __grasp.CONFIG.MAP_BOX, m = (1 - B) / 2; return mkFist(1 - (m + X / innerWidth * B), m + Y / innerHeight * B); };
window.sweep = (fn, x0, y0, x1, y1, ms) => { const t0 = performance.now(); window.__handFor = () => { const k = Math.min(1, (performance.now() - t0) / ms); return fn(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k); }; };
"""
GEST_JS = """window.__gest = (keys, o) => new Promise(res => { o = o || {}; const type = o.type || 'mouse', id = type === 'touch' ? 11 : 1; let t0 = null, k = 0;
  const fire = (kind, x, y, tg) => (tg || window).dispatchEvent(new PointerEvent(kind, { clientX: x, clientY: y, pointerType: type, pointerId: id, isPrimary: true, bubbles: true, cancelable: true, button: kind === 'pointermove' ? -1 : 0, buttons: o.down ? 1 : 0 }));
  if (o.down) fire('pointerdown', keys[0][1], keys[0][2], canvas);
  const step = (ts) => { if (t0 === null) t0 = ts; const t = ts - t0; while (k < keys.length - 1 && keys[k + 1][0] <= t) k++;
    let x, y; if (k >= keys.length - 1) { x = keys[keys.length - 1][1]; y = keys[keys.length - 1][2]; } else { const a = keys[k], b = keys[k + 1], q = (t - a[0]) / (b[0] - a[0]); x = a[1] + (b[1] - a[1]) * q; y = a[2] + (b[2] - a[2]) * q; }
    fire('pointermove', x, y);
    if (t >= keys[keys.length - 1][0]) { if (o.up) fire('pointerup', x, y, canvas); res(); return; } requestAnimationFrame(step); };
  requestAnimationFrame(step); });"""
# the speech stub (as in test_grippy): records every utterance
SPEECH = ("window.__spoken = []; try { const ss = { speaking: false, speak(u) { __spoken.push({ text: u.text, lang: u.lang }); setTimeout(() => { try { u.onend && u.onend(); } catch (e) {} }, 300); }, cancel() {}, getVoices() { return [{ lang: 'en-US', name: 'E' }, { lang: 'he-IL', name: 'H' }]; } };"
          " Object.defineProperty(window, 'speechSynthesis', { configurable: true, get: () => ss }); } catch (e) {}")
S = "__grasp.smash"; SM = "__grasp.sm"
# the front tile wall's cell at a screen point (index, alive) and how many cells are out
TOTAL = "(() => { let n = 0; for (const T of __grasp.sm.tiles) n += T.total - T.alive; return n + __grasp.sm.objs.filter(o => !o.alive).length; })()"  # everything smashed so far (tiles + things)
OUT0 = "(() => { const T = __grasp.sm.tiles.find(q => q.layer === 0); return T ? T.total - T.alive : -1; })()"
CELL = "((x, y) => { const T = __grasp.sm.tiles.find(q => q.layer === 0); const r = Math.floor((y - T.y0) / T.ch), off = T.stagger && r % 2 ? T.cw / 2 : 0, c = Math.floor((x - T.x0 + off) / T.cw), i = r * T.nc + c; return { i, alive: T.cells[i] === 1, hp: T.hp[i], chp: T.chp, out: T.total - T.alive }; })"
# the front wall's cells hit at all (cracked or out)
DMG0 = "(() => { const T = __grasp.sm.tiles.find(q => q.layer === 0); if (!T) return -1; let n = T.total - T.alive; for (let i = 0; i < T.cells.length; i++) if (T.cells[i] && T.hp[i] < T.chp) n++; return n; })()"
DMGALL = "(() => { let n = 0; for (const T of __grasp.sm.tiles) { n += T.total - T.alive; for (let i = 0; i < T.cells.length; i++) if (T.cells[i] && T.hp[i] < T.chp) n++; } return n + __grasp.sm.objs.reduce((a, o) => a + o.hits + (o.alive ? 0 : 1), 0); })()"
SOUNDS = {'window': 'glass', 'frame': 'glass', 'jar': 'glass', 'bottle': 'glass', 'plate': 'clink', 'cup': 'clink', 'vase': 'clink', 'clock': 'clink', 'plant': 'clink', 'tv': 'spark', 'ceilLamp': 'pop', 'floorLamp': 'pop',
          'shelf': 'wood', 'table': 'wood', 'cabinet': 'wood', 'book': 'swish', 'floor': 'crunch', 'car': 'car', 'streetLamp': 'pop', 'tree': 'wood', 'towerLegs': 'clang', 'tank': 'splash', 'hydrant': 'splash',
          'block': 'clack', 'balloon': 'pop', 'gift': 'confetti', 'watermelon': 'splat', 'tomato': 'splat', 'egg': 'splat', 'pumpkin': 'splat', 'orange': 'splat', 'apple': 'splat', 'crate': 'wood',
          'chest': 'confetti', 'gem': 'clink', 'trophy': 'clang'}
NEED = {'wall': ['table', 'plate', 'cup', 'tv', 'cabinet', 'vase', 'floorLamp'],
        'room': ['window', 'frame', 'clock', 'ceilLamp', 'shelf', 'jar', 'plant', 'book', 'table', 'plate', 'cup', 'vase', 'tv', 'cabinet', 'floorLamp'],
        'city': ['floor', 'car', 'tree', 'towerLegs', 'tank', 'streetLamp', 'hydrant'], 'blocks': ['block', 'balloon', 'gift'],
        'food': ['watermelon', 'tomato', 'egg', 'pumpkin', 'crate', 'shelf', 'bottle', 'orange', 'apple']}
# v3: hits each kind takes (glass 1-2, china 2, furniture 3-4, building floors 4-5, ...)
HP = {'window': 2, 'frame': 2, 'jar': 2, 'bottle': 2, 'plate': 2, 'cup': 2, 'vase': 2, 'table': 4, 'cabinet': 4, 'tv': 4, 'shelf': 4, 'car': 4, 'block': 4, 'watermelon': 5, 'pumpkin': 5, 'crate': 4, 'egg': 1, 'balloon': 1}
REST = "(() => { const o = __grasp.sm.objs; return { n: o.length, alive: o.every(q => q.alive), moving: o.filter(q => q.alive && !q.stat && q.body.speed > 0.6).map(q => q.kind + ':' + q.body.speed.toFixed(2)) }; })()"

async def fresh(b, mobile=False, he=False, init='', camera=False):
    opts = dict(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width':1280,'height':800})
    ctx = await b.new_context(**({'permissions': ['camera']} if camera else {}), **opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + HAND_JS + FIST_JS + GEST_JS + SPEECH + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');") + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_function("typeof __grasp !== 'undefined' && !!engine", timeout=15000); await page.wait_for_timeout(300)
    return ctx, page, errs
async def free(page, tap=False):  # the Smash tile, then the map's Free play
    await (page.tap if tap else page.click)('.modes button[data-mode=smash]'); await page.wait_for_function("__grasp.sm.mapOpen", timeout=5000)
    await (page.tap if tap else page.click)('#smashFree'); await page.wait_for_function("mode !== 'none' && __grasp.smash.run === 'free' && __grasp.sm.objs.length > 0", timeout=15000)
async def settle(page, ms=1300): await page.wait_for_timeout(ms)
async def drag(page, x0, x1, y, step=64, wait=16):
    await page.mouse.move(x0, y); await page.wait_for_timeout(120); await page.mouse.down()
    n = max(1, int(abs(x1 - x0) / step))
    for i in range(1, n + 1): await page.mouse.move(x0 + (x1 - x0) * i / n, y); await page.wait_for_timeout(wait)
    await page.mouse.up(); await page.wait_for_timeout(150)
async def play_phase(page, timeout=6000): await page.wait_for_function(S + ".phase === 'play'", timeout=timeout)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
        # ---------------- desktop, mouse ----------------
        ctx, page, errs = await fresh(b)
        await page.click('.modes button[data-mode=smash]'); await page.wait_for_function("__grasp.sm.mapOpen", timeout=5000)
        mp = await page.evaluate("""(() => { const n = [...document.querySelectorAll('#smList .smNode')]; return { path: location.pathname, mode, title: $('smTitle').textContent, free: $('smashFree').getBoundingClientRect().height > 60, nodes: n.length,
          cur: n.filter(b => b.classList.contains('cur')).map(b => b.dataset.n), locked: n.filter(b => b.classList.contains('locked')).length, scenes: [...document.querySelectorAll('#smList .smScene')].map(s => s.dataset.scene), total: $('smStarTotal').textContent.trim() }; })()""")
        check('the Smash tile opens its map at /smash: Free play on top, 20 stages in 5 scene groups (stage 1 current, the rest locked), no game running yet', mp['path'] == '/smash' and mp['mode'] == 'none' and mp['title'] == 'Smash' and mp['free'] and mp['nodes'] == 20 and mp['cur'] == ['1'] and mp['locked'] == 19 and mp['scenes'] == ['wall', 'room', 'city', 'blocks', 'food'] and mp['total'].startswith('0'), mp)
        await page.click('#smList .smNode[data-n="5"]', force=True); await page.wait_for_timeout(300)
        check('a locked stage does not start (the map stays)', await page.evaluate("__grasp.sm.mapOpen && mode === 'none'"))
        await page.keyboard.press('Escape'); await page.wait_for_function("!__grasp.sm.mapOpen && !location.pathname.startsWith('/smash')", timeout=4000)
        check('Escape closes the map back to the start screen at /', await page.evaluate("!__grasp.sm.mapOpen && !$('start').hidden && !location.pathname.startsWith('/smash')"))
        await free(page)
        st = await page.evaluate("""(() => { const v = [...document.querySelectorAll('.chrome > *')].filter(e => e.getBoundingClientRect().width > 0); return { run: __grasp.smash.run, scene: __grasp.smash.scene, phase: __grasp.smash.phase, path: location.pathname, chrome: v.map(e => e.id), tiles: __grasp.sm.tiles.map(t => [t.kind, t.layer, t.alive, t.chp]), bodies: bodies.length, sleeping: engine.enableSleeping, waves: __grasp.smash.waves, wave: __grasp.smash.wave, boss: __grasp.smash.bossHp }; })()""")
        check('Free play starts on the brick wall (a full-screen brick wall in front of a tiled room wall), sandbox objects gone, resting bodies sleep', st['run'] == 'free' and st['scene'] == 'wall' and st['phase'] == 'play' and st['path'] == '/smash' and [t[:2] for t in st['tiles']] == [['tile', 1], ['brick', 0]] and st['tiles'][1][2] > 40 and st['bodies'] == 0 and st['sleeping'], st)
        check('v3: a free-play scene is 3 waves and then a 50-hp boss; bricks take 2 hits, glazed tiles 1', st['waves'] == 3 and st['wave'] == 0 and st['boss'] == 50 and st['tiles'][1][3] == 2 and st['tiles'][0][3] == 1, st)
        check('in play the toolbar is one pause button', st['chrome'] == ['pauseBtn'], st)
        await page.wait_for_function(S + ".ui.hud && " + S + ".ui.trackBox", timeout=3000); hud = await page.evaluate(S + ".ui.hud"); tb = await page.evaluate(S + ".ui.trackBox")
        check('the HUD is one slim pill: the progress track through the scene (a dot where each wave ends, the boss\'s crown at the end); free play: no clock, no coin pill', hud and hud['parts'] == ['track'] and hud['h'] <= 32 and tb['marks'] == 3 and tb['h'] <= 8 and tb['prog'] < 0.05 and await page.evaluate("__grasp.coinUi.box") is None, [hud, tb])
        wall = await page.evaluate("(() => { const T = __grasp.sm.tiles.find(q => q.layer === 0); return { x0: T.x0, y0: T.y0, w: T.w, h: T.h }; })()")
        check('the brick wall covers the whole screen', wall['x0'] == 0 and wall['y0'] == 0 and wall['w'] == 1280 and wall['h'] == 800, wall)
        # a click is a punch right there: v3 the brick cracks first, the next click knocks it out
        await page.wait_for_timeout(500)
        c0 = await page.evaluate(CELL + "(640, 420)")
        await page.mouse.click(640, 420); await page.wait_for_function(f"{CELL}(640, 420).hp < 2", timeout=3000)
        c1 = await page.evaluate(CELL + "(640, 420)")
        check('mouse: a click cracks the brick under it (and its neighbours) but knocks nothing out yet', c0['alive'] and c0['hp'] == 2 and c1['alive'] and c1['hp'] == 1 and c1['out'] == 0 and await page.evaluate(DMG0) >= 2, [c0, c1])
        check('...a crack: its own knock (smcrack), no crunch yet', any(s['k'] == 'smcrack' and s['o'] == 'brick' for s in await page.evaluate(SM + ".snd")) and not any(s['k'] == 'crunch' for s in await page.evaluate(SM + ".snd")))
        await page.wait_for_timeout(120); await page.mouse.click(640, 420); await page.wait_for_function(f"!{CELL}(640, 420).alive", timeout=3000)
        check('mouse: the second click knocks the cracked bricks out, with the crunch', (await page.evaluate(CELL + "(640, 420)"))['out'] >= 2 and any(s['o'] == 'brick' and s['k'] == 'crunch' for s in await page.evaluate(SM + ".snd")))
        o0 = await page.evaluate(DMG0); await drag(page, 200, 1080, 250, step=8, wait=60)
        check('mouse: a slow drag smashes nothing along its way (only the press itself punches where it lands)', await page.evaluate(DMG0) - o0 <= 6 and (await page.evaluate(CELL + "(640, 250)"))['hp'] == 2 and (await page.evaluate(CELL + "(1000, 250)"))['hp'] == 2, [o0, await page.evaluate(DMG0)])
        out0 = await page.evaluate(OUT0); await drag(page, 100, 1180, 250)
        c2 = [await page.evaluate(CELL + f"({x}, 250)") for x in (400, 900)]
        check('mouse: a fast swipe cracks a band of bricks along its path, each once (a swipe is one hit on each thing: no mass clear)', all(c['alive'] and c['hp'] == 1 for c in c2) and await page.evaluate(OUT0) - out0 <= 8, [c2, out0, await page.evaluate(OUT0)])
        await drag(page, 100, 1180, 250)
        o1 = await page.evaluate(OUT0)
        check('mouse: a second fast swipe there knocks the cracked band out', o1 - out0 >= 8 and not (await page.evaluate(CELL + "(400, 250)"))['alive'] and not (await page.evaluate(CELL + "(900, 250)"))['alive'], [out0, o1])
        pc = await page.evaluate("({ n: __grasp.smash.pieces.length, dyn: __grasp.smash.pieces.every(p => !p.isStatic), moving: __grasp.smash.pieces.some(p => p.speed > 0.5), meter: __grasp.sm.meter })")
        check('knocked-out bricks fly as dynamic debris; the wave\'s meter rises', pc['n'] > 0 and pc['dyn'] and pc['moving'] and 0 < pc['meter'] < 0.5, pc)
        # ---- each scene builds, rests, and holds what it should ----
        for sc in ['wall', 'room', 'city', 'blocks', 'food']:
            n = await page.evaluate(f"{SM}.build('{sc}', 2)"); await settle(page)
            k = await page.evaluate(SM + ".kinds()"); r = await page.evaluate(REST)
            miss = [q for q in NEED[sc] if not k.get(q)]
            check(f'desktop {sc}: builds with {n} things of every kind it should have', n >= (8 if sc == 'wall' else 16) and not miss, [n, miss, k])
            check(f'desktop {sc}: everything rests after the build (nothing breaks or cracks by itself, nothing still moving)', r['alive'] and not r['moving'] and await page.evaluate(f"{SM}.objs.every(o => !o.hits)"), r)
        lay = await page.evaluate(f"(() => {{ {S}.waves = 1; {SM}.build('wall', 1); return [...new Set({SM}.objs.map(o => o.kind + ':' + o.layer))]; }})()")
        check('the wall scene: the room\'s things behind the bricks (layer 1); on its last wave the treasure behind the room\'s wall (layer 2)', 'chest:2' in lay and 'gem:2' in lay and 'trophy:2' in lay and 'tv:1' in lay and 'table:1' in lay, lay)
        # the front-most first: a punch on the wall breaks bricks, not the TV behind them
        tv = await page.evaluate(f"(() => {{ const o = {SM}.alive('tv')[0]; return {{ x: o.body.position.x, y: o.body.position.y }}; }})()")
        await page.evaluate(f"{SM}.punch({tv['x']}, {tv['y']}, 0.4)")
        check('front first: a punch where the TV stands behind the wall cracks bricks, the TV is untouched', await page.evaluate(f"{SM}.alive('tv')[0].hits === 0") and await page.evaluate(DMG0) > 0)
        for _ in range(12):
            if not await page.evaluate(f"{SM}.alive('tv').length"): break
            await page.evaluate(f"{SM}.punch({tv['x']}, {tv['y']}, 1)")
        check('...and once the bricks there are gone, the TV takes the hits and breaks', await page.evaluate(f"{SM}.alive('tv').length") == 0, await page.evaluate(f"{SM}.alive('tv').map(o => o.hp)"))
        # ---- v3: tougher things: hits by size / material, cracks that grow, a wobble and a deeper knock each hit, only the last hit breaks ----
        tough, bad = {}, []
        for sc in ['room', 'city', 'blocks', 'food']:
            await page.evaluate(f"{SM}.build('{sc}', 1)"); await settle(page, 700)
            for kind, want in HP.items():
                r = await page.evaluate(f"""(() => {{ const o = {SM}.alive('{kind}')[0]; if (!o) return null; {SM}.snd.length = 0; const lv = [], ar = [], alive = [], wob = [];
                  for (let i = 0; i < 9 && o.alive; i++) {{ {SM}.hit(o, 0.3); lv.push({SM}.crackLv(o)); alive.push(o.alive); wob.push(performance.now() - o.hitAt < 50); const s = {SM}.snd.filter(q => q.k === 'smcrack' && q.o === '{kind}').pop(); ar.push(s ? s.a : null); }}
                  return {{ hits: alive.length, lv, ar, alive, wob, max: o.maxHp }}; }})()""")
                if r is None or kind in tough: continue
                tough[kind] = r['hits']
                ok = r['hits'] == want and r['max'] == want and all(r['alive'][:-1]) and not r['alive'][-1] and all(r['wob'][:-1]) and r['lv'][:-1] == sorted(r['lv'][:-1]) and (want < 2 or (r['lv'][0] >= 1 and r['ar'][0] is not None)) and all(r['ar'][i] <= r['ar'][i + 1] for i in range(len(r['ar']) - 2))
                if not ok: bad.append((kind, r))
        check('v3: every thing takes its hits (glass and china 2, furniture 4, floors 4+, melons 5...) - cracks grow each hit (stage 1..4), it wobbles, the knock gets deeper, only the last hit breaks it', not bad and set(tough) >= set(HP) - {'window', 'frame'}, [bad, tough, sorted(set(HP) - set(tough))])
        await page.evaluate(f"{SM}.build('room', 1)"); await settle(page, 700)
        w2 = await page.evaluate(f"(() => {{ const o = {SM}.alive('window')[0]; {SM}.hit(o, 0.3); const a = [o.alive, {SM}.crackLv(o)]; {SM}.hit(o, 0.3); return a.concat([o.alive]); }})()")
        check('a window (glass, static on the wall) cracks on the first hit and shatters on the second', w2 == [True, 2, False], w2)
        # a swipe across a row of things hits each once: a shelf of jars all cracked, none broken
        sw = await page.evaluate(f"""(() => {{ const s = {SM}.alive('shelf')[0], b = s.body.bounds, on = {SM}.objs.filter(o => o.alive && o !== s && o.body.position.y < s.body.position.y && o.body.position.x > b.min.x && o.body.position.x < b.max.x && s.body.position.y - o.body.position.y < 80 && o.maxHp >= 2);
          const y = on[0].body.position.y; {SM}.sweep(b.min.x - 10, y, b.max.x + 10, y, 1); return {{ n: on.length, hit: on.filter(o => o.hits === 1).length, alive: on.filter(o => o.alive).length }}; }})()""")
        check('v3: a hard swipe across a shelf of jars hits each jar exactly once: all cracked, none broken (no mass clear)', sw['n'] >= 3 and sw['hit'] == sw['n'] and sw['alive'] == sw['n'], sw)
        # ---- every thing breaks with its own sound ----
        heard, bad = {}, []
        for sc in ['wall', 'room', 'city', 'blocks', 'food']:
            await page.evaluate(f"{S}.waves = 1; {SM}.build('{sc}', 3)"); await settle(page, 900)
            for kind, want in SOUNDS.items():
                got = await page.evaluate(f"(() => {{ const o = {SM}.alive('{kind}')[0]; if (!o) return null; {SM}.snd.length = 0; {SM}.breakObj(o); const s = {SM}.snd.find(q => q.o === '{kind}' && q.k !== 'smcrack'); return s ? s.k : 'none'; }})()")
                if got is None: continue
                heard[kind] = got
                if got != want: bad.append((kind, got, want))
        check('every kind of thing breaks with its own sound (glass shatter, china clink, TV spark, bulb / balloon pop, splat, confetti, crunch...)', not bad and set(heard) >= set(SOUNDS), [bad, sorted(set(SOUNDS) - set(heard))])
        # ---- v3: weak chain reactions ----
        await page.evaluate(f"{SM}.build('room', 1)"); await settle(page)
        jar0 = await page.evaluate(f"(() => {{ const s = {SM}.alive('shelf')[0], b = s.body.bounds, on = {SM}.objs.filter(o => o.alive && o !== s && o.body.position.y < s.body.position.y && o.body.position.x > b.min.x && o.body.position.x < b.max.x && s.body.position.y - o.body.position.y < 80); window.__on = on; window.__flr = {SM}.objs.filter(o => o.alive && (o.kind === 'plate' || o.kind === 'cup')).map(o => o.hp); {SM}.breakObj(s); return on.length; }})()")
        await page.wait_for_function("__on.some(o => o.hits > 0)", timeout=6000); await page.wait_for_timeout(1500)
        ch = await page.evaluate("({ hit: __on.filter(o => o.hits > 0).length, down: __on.filter(o => !o.alive).length, n: __on.length, list: __on.map(o => o.kind + ':' + o.hp + '/' + o.maxHp + (o.alive ? '' : '!')) })")
        check('chain (weak): a broken shelf drops its jars - they crack on the floor (a fall is one hit\'s worth) but do not shatter', jar0 >= 3 and ch['hit'] >= 2 and ch['down'] == 0, [jar0, ch])
        await page.evaluate(f"(() => {{ const s = {SM}.alive('shelf')[0], b = s.body.bounds, on = {SM}.objs.filter(o => o.alive && o !== s && o.body.position.y < s.body.position.y && o.body.position.x > b.min.x && o.body.position.x < b.max.x && s.body.position.y - o.body.position.y < 80); window.__on2 = on; for (const o of on) {{ {SM}.hit(o, 0.3); }} {SM}.breakObj(s); }})()")
        await page.wait_for_function("__on2.filter(o => !o.alive).length >= 2", timeout=6000)
        check('...but things already cracked do shatter when they fall', await page.evaluate("__on2.filter(o => !o.alive).length") >= 2, await page.evaluate("__on2.map(o => o.kind + (o.alive ? '' : '!'))"))
        dm = await page.evaluate("engine.world.bodies.filter(b => b.label === 'debris').every(b => !(b.collisionFilter.mask & 2))")
        flr = await page.evaluate(f"{SM}.objs.filter(o => o.alive && (o.kind === 'plate' || o.kind === 'cup')).map(o => o.hp)")
        check('debris never hurts things (it does not even touch them): the plates and cups under the falling shelves are whole', dm and flr == await page.evaluate("__flr"), [dm, flr])
        await page.evaluate(f"{SM}.build('city', 2)"); await settle(page)
        g = await page.evaluate(f"(() => {{ const fl = {SM}.alive('floor'), by = {{}}; for (const o of fl) (by[o.group] = by[o.group] || []).push(o); const g = Object.keys(by).sort((a, b) => by[b].length - by[a].length)[0]; window.__bl = by[g]; const low = by[g].reduce((a, o) => o.body.position.y > a.body.position.y ? o : a); {SM}.breakObj(low); return by[g].length; }})()")
        await page.wait_for_timeout(2500)
        cl = await page.evaluate("({ down: __bl.filter(o => !o.alive).length, hit: __bl.filter(o => o.alive && o.hits).length, n: __bl.length })")
        check('chain (weak): knock out a building\'s ground floor - the floors above drop and crack, the building does not collapse', g >= 5 and cl['down'] == 1, [g, cl])
        await page.evaluate(f"(() => {{ window.__tank = {SM}.alive('tank')[0]; {SM}.breakObj({SM}.alive('towerLegs')[0]); }})()")
        await page.wait_for_function("__tank.hits > 0", timeout=5000)
        check('chain (weak): the water tower\'s legs go - the tank falls and cracks, it does not burst', await page.evaluate("__tank.alive && __tank.hp === __tank.maxHp - 1"), await page.evaluate("[__tank.alive, __tank.hp]"))
        # ---- debris: capped, faded, pooled ----
        await page.evaluate(f"(() => {{ {SM}.build('food', 4); window.__pmax = 0; window.__pOn = true; (function r() {{ if (!__pOn) return; __pmax = Math.max(__pmax, __grasp.smash.pieces.length); requestAnimationFrame(r); }})(); }})()"); await settle(page, 800)
        for sc in ['food', 'blocks', 'room']:
            await page.evaluate(f"(() => {{ {SM}.build('{sc}', 4); for (const o of {SM}.alive()) {SM}.breakObj(o, 1); }})()"); await page.wait_for_timeout(250)
        await page.wait_for_timeout(400); cap = await page.evaluate(SM + ".cap"); pm = await page.evaluate("__pOn = false; __pmax"); now_n = await page.evaluate(SM + ".pieces")
        check('debris is capped (140 on a desktop; never far over it, back under it within a moment)', cap == 140 and pm <= cap * 1.25 + 1 and now_n <= cap, [cap, pm, now_n])
        await page.evaluate("__grasp.CONFIG.SMASH_PIECE_MS = 150")
        await page.wait_for_function("__grasp.sm.pieces === 0", timeout=5000)
        pool = await page.evaluate(SM + ".pool")
        check('debris fades out and goes back to its pool (no bodies left in the world)', pool > 20 and await page.evaluate("engine.world.bodies.filter(b => b.label === 'debris').length") == 0, pool)
        await page.evaluate("__grasp.CONFIG.SMASH_PIECE_MS = 3500"); await page.evaluate(f"(() => {{ {SM}.build('blocks', 1); for (const o of {SM}.alive('block').slice(0, 6)) {SM}.breakObj(o); }})()")
        check('new debris reuses pooled bodies', await page.evaluate(SM + ".pool") < pool and await page.evaluate(SM + ".pieces") > 0, [pool, await page.evaluate(SM + ".pool")])
        # ---- v3 waves: most of a wave smashed -> the scene scrolls on, the next wave slides in (leftovers slide away), later waves come in a little cracked ----
        await page.evaluate(f"{S}.waves = 3; {S}.bossHp = 50; {SM}.build('room', 1)"); await settle(page, 600)
        ids0 = await page.evaluate(f"{SM}.objs.map(o => o.id)")
        await page.evaluate(f"{SM}.breakTo(0.7)"); await page.wait_for_timeout(200)
        check('below 85% of the wave: still the first wave', await page.evaluate(f"{S}.phase === 'play' && {S}.wave === 0") and 0.65 <= await page.evaluate(SM + ".meter") < 0.85, await page.evaluate(SM + '.meter'))
        await page.evaluate(f"{SM}.breakTo(0.86)"); await page.wait_for_function(S + ".phase === 'scroll'", timeout=3000)
        try: await page.wait_for_function(f"Math.abs({SM}.progress - 0.25) < 0.01", timeout=1500)  # (a loaded container: the wave's meter resets a frame later)
        except Exception: pass
        sc0 = await page.evaluate(f"({{ wave: {S}.wave, newX: Math.min(...{SM}.objs.filter(o => o.alive && o.wave === 1).map(o => o.body.position.x - o.w / 2)), n: {SM}.objs.filter(o => o.wave === 1).length, prog: {SM}.progress, log: {SM}.waveLog.length }})")
        await page.wait_for_timeout(450)
        mid = await page.evaluate(f"({{ x: Math.min(...{SM}.objs.filter(o => o.alive && o.wave === 1).map(o => o.body.position.x - o.w / 2)), bg: {S}.bgX }})")
        await play_phase(page)
        sc1 = await page.evaluate(f"({{ wave: {S}.wave, meter: {SM}.meter, old: {SM}.objs.filter(o => {S}.wave !== o.wave).length, inside: {SM}.objs.every(o => o.body.position.x > -5 && o.body.position.x < innerWidth + 5), ids: {SM}.objs.map(o => o.id), tag: {S}.tag && {S}.tag.text, hair: {SM}.objs.filter(o => o.hair).length, n: {SM}.objs.length, tb: {S}.ui.trackBox }})")
        check('85% of the wave: the scene scrolls on - wave 2 built off to the right slides in (the backdrop pans along)', sc0['wave'] == 1 and sc0['newX'] >= 1280 * 0.7 and sc0['n'] >= 10 and 0 < mid['x'] < sc0['newX'] and mid['bg'] < 0 and abs(sc0['prog'] - 1 / 4) < 0.01, [sc0, mid])
        check('...then wave 2 is on screen, the leftovers of wave 1 slid away and are gone, the meter starts again, a small tag says "Onward! 2/3"', sc1['wave'] == 1 and sc1['meter'] < 0.02 and sc1['old'] == 0 and sc1['inside'] and not set(sc1['ids']) & set(ids0) and sc1['tag'] == 'Onward! 2/3', sc1)
        check('tension: the waves ahead come in with hairline cracks already (no damage)', sc1['hair'] >= 1 and await page.evaluate(f"{SM}.objs.filter(o => o.hair).every(o => o.hp === o.maxHp)"), sc1)
        await page.evaluate(f"(() => {{ for (const o of {SM}.objs) o.hair = 0; {S}.hairAt = performance.now(); }})()"); await page.wait_for_function(f"{SM}.objs.some(o => o.hair)", timeout=3000)
        check('...and as a wave goes on, things not yet hit start to crack and tremble by themselves', await page.evaluate(f"(() => {{ const o = {SM}.objs.find(q => q.hair); return o.hp === o.maxHp && performance.now() - o.tremAt < 1500; }})()"))
        await page.wait_for_function(f"{S}.ui.trackBox && {S}.ui.trackBox.wave === 1", timeout=3000); tb = await page.evaluate(S + ".ui.trackBox")
        check('the progress track shows how far through the scene (a quarter: 1 of 3 waves + the boss)', 0.2 <= tb['prog'] <= 0.3 and tb['waves'] == 3, tb)
        # ---- v3 the boss: after the last wave, the scene's boss with a health bar; harder hits hurt more; cracks -> pieces fall off -> shakes; the big one ----
        await page.evaluate("__grasp.grippy.cool()"); await page.evaluate(f"{SM}.toBoss()"); await play_phase(page)
        bs = await page.evaluate(f"(() => {{ const o = {SM}.boss; return {{ seg: {S}.seg, kind: o && o.extra.kind, hp: o && o.hp, max: o && o.maxHp, cx: o && o.body.position.x, said: __grasp.grippy.last && __grasp.grippy.last.event, tag: {S}.tag && {S}.tag.text, w: o && o.w, h: o && o.h }}; }})()")
        await page.wait_for_function(S + ".ui.bossBar", timeout=3000); bar = await page.evaluate(S + ".ui.bossBar")
        check('the boss rolls in after the last wave: the room\'s giant TV, 50 hp, "Boss!", the voice says so (smashBoss)', bs['seg'] == 'boss' and bs['kind'] == 'tv' and bs['hp'] == 50 and bs['max'] == 50 and abs(bs['cx'] - 640) < 2 and bs['tag'] == 'Boss!' and bs['said'] == 'smashBoss' and bs['w'] > 250, bs)
        check('its health bar sits under the HUD pill, full', bar and bar['f'] == 1 and bar['y'] > (await page.evaluate(S + ".ui.hud"))['y'] and bar['w'] >= 200, bar)
        dm = await page.evaluate(f"[{SM}.hit({SM}.boss, 0.3), {SM}.hit({SM}.boss, 0.7), {SM}.hit({SM}.boss, 0.95)]")
        check('harder hits hurt the boss more: a tap 1, a fast swipe 2, a very fast one 3', dm == [49, 47, 44], dm)
        p1 = await page.evaluate(f"(() => {{ const o = {SM}.boss; while (o.hp > 30) {SM}.hit(o, 0.3); return {{ ph: o.extra.ph, pieces: {SM}.pieces }}; }})()")
        await page.wait_for_function(S + ".ui.bossBar && " + S + ".ui.bossBar.ph === 2", timeout=3000)
        p2 = await page.evaluate(f"(() => {{ const o = {SM}.boss, n0 = {SM}.pieces; {SM}.hit(o, 0.3); return {{ more: {SM}.pieces > n0 }}; }})()")
        check('boss phase 2 (under 2/3): pieces fall off with every hit', p1['ph'] == 2 and p2['more'], [p1, p2])
        p3 = await page.evaluate(f"(() => {{ const o = {SM}.boss; while (o.hp > 14) {SM}.hit(o, 0.3); return o.extra.ph; }})()")
        check('boss phase 3 (under 1/3): it shakes and glows', p3 == 3)
        await page.screenshot(path='tests/out/smash3_boss_phase3_desktop_en.png')
        c0 = await page.evaluate("__grasp.profile.coins"); await page.evaluate("__grasp.grippy.cool()")
        await page.evaluate(f"(() => {{ const o = {SM}.boss; while (o.alive) {SM}.hit(o, 0.3); }})()")
        bm = await page.evaluate(f"({{ phase: {S}.phase, boss: {SM}.boss.alive, pieces: {SM}.pieces, snd: {SM}.snd.some(s => s.k === 'bossdown') }})")
        check('the last hit: the boss blows up (its pieces fly, the boss-down blast)', bm['phase'] == 'boom' and not bm['boss'] and bm['pieces'] >= 10 and bm['snd'], bm)
        await page.wait_for_function(S + ".phase === 'clear'", timeout=4000)
        await page.wait_for_function(S + ".ui.clearBox", timeout=3000)
        cl = await page.evaluate(f"({{ coins: __grasp.profile.coins, box: {S}.ui.clearBox, said: __grasp.grippy.last && __grasp.grippy.last.event, prog: {SM}.progress }})")
        check('then the victory: "Smashed!", confetti, +6 coins, the voice cheers (smashClear), the track full', cl['box']['text'] == 'Smashed!' and cl['coins'] - c0 == 6 and cl['said'] == 'smashClear' and cl['prog'] == 1, [c0, cl])
        await page.screenshot(path='tests/out/smash3_victory_desktop_en.png')
        await page.wait_for_function(S + ".phase === 'in'", timeout=5000)
        sl = await page.evaluate(f"({{ scene: {S}.scene, slide: {S}.slide, tag: {S}.ui.tagBox }})")
        await page.wait_for_function(S + ".phase === 'play'", timeout=5000)
        nx = await page.evaluate(f"({{ scene: {S}.scene, meter: {SM}.meter, slide: {S}.slide, wave: {S}.wave, seg: {S}.seg, said: __grasp.grippy.said.map(s => s.event).slice(-2) }})")
        check('then the next scene (the city) slides in with its name, wave 1 of it, and the voice says so (smashScene)', sl['scene'] == 'city' and sl['slide'] > 0 and nx['scene'] == 'city' and nx['meter'] < 0.05 and nx['slide'] == 0 and nx['wave'] == 0 and nx['seg'] == 'wave' and nx['said'] == ['smashClear', 'smashScene'], [sl, nx])
        check('free play order: wall, room, city, blocks, food, then round again', await page.evaluate("(() => { const out = []; for (let i = 0; i < 6; i++) { smFreeNext(performance.now()); out.push(__grasp.smash.scene); } return out; })()") == ['blocks', 'food', 'wall', 'room', 'city', 'blocks'])
        try: await page.wait_for_function("['brick', 'car', 'wall', 'smash'].every(k => __grasp.events.some(e => e[0] === k))", timeout=5000)  # (the stats are flushed to track() once a second: polled)
        except Exception: pass
        ev = await page.evaluate("__grasp.events.map(e => e[0])"); pr = await page.evaluate("__grasp.profile.stats")
        check('smashing counts for the stats and missions: bricks (bricks, tiles, blocks, floors), cars, walls (a wall, a building or a boss all the way down), things smashed', all(k in ev for k in ['brick', 'car', 'wall', 'smash']) and pr['smashed'] > 0 and pr['bricks'] > 0 and pr['cars'] > 0 and pr['walls'] > 0, [sorted(set(ev)), pr])
        # ---- the pause sheet: everything waits ----
        await page.evaluate(f"{SM}.build('blocks', 1)"); await settle(page, 600)
        await page.click('#pauseBtn'); await page.wait_for_function("menu.open && __grasp.pause.on", timeout=3000)
        sh = await page.evaluate("[...document.querySelectorAll('.chrome.open button')].filter(b => b.getBoundingClientRect().width > 0).map(b => b.id)")
        check('the pause button opens the sheet: Resume, Restart, Sound, Language, Stats, Home', all(i in sh for i in ['resumeBtn', 'resetBtn', 'muteBtn', 'hudBtn', 'homeBtn']) and len(sh) >= 6, sh)
        await page.evaluate(f"(() => {{ for (const o of {SM}.alive('block').slice(0, 3)) {SM}.breakObj(o); }})()")
        y0 = await page.evaluate("__grasp.smash.pieces.map(p => p.position.y).join()"); await page.wait_for_timeout(400); y1 = await page.evaluate("__grasp.smash.pieces.map(p => p.position.y).join()")
        check('paused: the debris hangs still (physics waits)', y0 == y1 and len(y0) > 0)
        await page.screenshot(path='tests/out/smash2_pause_desktop_en.png')
        await page.click('#resumeBtn'); await page.wait_for_function("!menu.open && !__grasp.pause.on", timeout=3000)
        await page.wait_for_function(f"__grasp.smash.pieces.map(p => p.position.y).join() !== '{y1}'", timeout=3000)
        check('Resume: play goes on (the debris falls again)', True)
        await page.keyboard.press('Escape'); await page.wait_for_timeout(150)
        check('Escape opens the sheet too (and again closes it)', await page.evaluate("menu.open") and (await page.keyboard.press('Escape') or True) and not await page.evaluate("menu.open"))
        await page.evaluate(f"{SM}.breakTo(0.3)"); await menu_click(page, '#resetBtn'); await page.wait_for_timeout(300)
        check('Restart (free play): the same scene afresh', await page.evaluate(f"!menu.open && {S}.scene === 'blocks' && {SM}.meter < 0.05 && {S}.run === 'free' && {S}.wave === 0"))
        await menu_click(page, '#homeBtn'); await page.wait_for_function("mode === 'none' && !location.pathname.startsWith('/smash')", timeout=4000)
        check('Home: the start screen at /', await page.evaluate("mode === 'none' && !$('start').hidden && !location.pathname.startsWith('/smash')"))
        await page.evaluate("__grasp.setGameMode('sandbox')"); await page.wait_for_timeout(200)
        check('leaving Smash for another game clears its things and stops the sleeping', await page.evaluate("__grasp.sm.objs.length === 0 && !engine.enableSleeping && document.body.classList.contains('minChrome')"))  # (every game keeps the corner pause button)
        check('desktop: no page errors', not errs, errs); await ctx.close()

        # ---------------- camera ----------------
        ctx, page, errs = await fresh(b, camera=True)
        await page.click('#camBtn'); await page.click('.modes button[data-mode=smash]'); await page.wait_for_function("__grasp.sm.mapOpen", timeout=5000)
        await page.click('#smashFree'); await page.wait_for_function("mode === 'camera' && __grasp.sm.objs.length > 0", timeout=15000)
        await page.evaluate("window.__handFor = () => fistAt(200, 300)"); await page.wait_for_timeout(700)
        check('camera: a closed fist is recognised', await page.evaluate("gesture") == 'fist', await page.evaluate("[gesture, hand.pinchD]"))
        await page.wait_for_function("!__grasp.pause.on", timeout=8000)
        o0 = await page.evaluate(DMG0); cy = await page.evaluate("cursor.y")
        await page.evaluate("sweep(fistAt, 150, 300, 1130, 300, 260)"); await page.wait_for_timeout(700)
        o1 = await page.evaluate(DMG0)
        check('camera: a fist swept across the wall cracks a band of bricks', o1 - o0 >= 8 and (await page.evaluate(CELL + f"(640, {cy})"))['hp'] < 2, [o0, o1, cy])
        await page.evaluate("window.__handFor = () => handAt(150, 680, 0.8)"); await page.wait_for_timeout(600)
        check('camera: an open hand punches too (kid-friendly)', await page.evaluate("gesture === 'open' && __grasp.punchGesture()"))
        o2 = await page.evaluate(DMGALL); await page.evaluate("sweep((x, y) => handAt(x, y, 0.8), 150, 680, 1130, 680, 260)"); await page.wait_for_timeout(700)
        check('camera: a fast open-hand wave smashes too', await page.evaluate(DMGALL) - o2 >= 8, [o2, await page.evaluate(DMGALL)])
        await page.evaluate("window.__handFor = () => handAt(640, 120, 0.8)"); await page.wait_for_timeout(500)
        kn = await page.evaluate("new Promise(res => { const seen = new Set(), t0 = performance.now(); let fr = 0; (function r() { fr++; seen.add(__grasp.smash.camAt); if (performance.now() - t0 < 1000) requestAnimationFrame(r); else res({ knocks: seen.size - 1, frames: fr }); })(); })")
        check('camera: a hand resting on things keeps knocking, a few times a second (not every frame)', 2 <= kn['knocks'] <= 6 and kn['frames'] > kn['knocks'] * 2, kn)
        await page.evaluate("window.__handFor = () => handAt(1000, 120, 0.1)"); await page.wait_for_timeout(500)
        o5 = await page.evaluate(DMGALL); await page.wait_for_timeout(800)
        check('camera: a pinch does not punch', await page.evaluate("gesture") == 'pinch' and await page.evaluate(DMGALL) == o5, [o5, await page.evaluate(DMGALL)])
        hint = await page.evaluate("hintText()"); hhe = await page.evaluate("(() => { setLang('he'); const h = hintText(); setLang('en'); return h; })()")
        check('camera hint (EN + HE): punch or touch things, smash your way to the boss', hint.startswith('Punch or touch things with your hand to smash them') and 'boss' in hint and hhe.startswith('תנו אגרוף או געו בדברים') and 'הבוס' in hhe, [hint, hhe])
        check('smash constants: PUNCH_SPEED 0.55 (touch 0.35), FIST_RADIUS 40, a wave moves on at 85%', await page.evaluate("__grasp.CONFIG.PUNCH_SPEED === 0.55 && __grasp.CONFIG.PUNCH_SPEED_TOUCH === 0.35 && __grasp.CONFIG.FIST_RADIUS === 40 && __grasp.CONFIG.SMASH_CLEAR === 0.85"))
        check('camera: no page errors', not errs, errs); await ctx.close()

        # ---------------- phone, touch (EN + HE) ----------------
        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx, page, errs = await fresh(b, mobile=True, he=he)
            await free(page, tap=True)
            check(tag + ' phone: Free play on touch', await page.evaluate("mode === 'mouse' && __grasp.smash.scene === 'wall'"))
            await page.wait_for_timeout(400)
            c0 = await page.evaluate(CELL + "(180, 420)")
            await page.tap('#stage', position={'x': 180, 'y': 420}); await page.wait_for_function(f"{CELL}(180, 420).hp < 2", timeout=3000)
            await page.wait_for_timeout(100); await page.tap('#stage', position={'x': 180, 'y': 420}); await page.wait_for_function(f"!{CELL}(180, 420).alive", timeout=3000)
            check(tag + ' phone: a tap is a punch right where the finger lands (a crack, then the next tap knocks it out)', c0['alive'] and not (await page.evaluate(CELL + "(180, 420)"))['alive'])
            o0 = await page.evaluate(DMG0)
            await page.evaluate("__gest([[0, 20, 600], [60, 20, 600], [260, 340, 600], [300, 340, 600]], { type: 'touch', down: true, up: true })"); await page.wait_for_timeout(250)
            o1 = await page.evaluate(DMG0)
            check(tag + ' phone: a fast touch swipe cracks the bricks along it', o1 - o0 >= 3 and (await page.evaluate(CELL + "(100, 600)"))['hp'] < 2 and (await page.evaluate(CELL + "(260, 600)"))['hp'] < 2, [o0, o1])
            await page.evaluate("__gest([[0, 30, 250], [100, 30, 250], [3600, 330, 250], [3700, 330, 250]], { type: 'touch', down: true, up: true })"); await page.wait_for_timeout(200)
            o2 = await page.evaluate(DMG0)
            check(tag + ' phone: a slow finger drag smashes nothing along its way (only where it first lands)', o2 - o1 <= 6 and (await page.evaluate(CELL + "(200, 250)"))['hp'] == 2 and (await page.evaluate(CELL + "(310, 250)"))['hp'] == 2, [o1, o2])
            check(tag + ' phone: debris capped lower on a phone (80)', await page.evaluate(SM + ".cap") == 80)
            hud = await page.evaluate(S + ".ui.hud"); pb = await page.evaluate("(() => { const r = $('pauseBtn').getBoundingClientRect(); return { l: r.left, r: r.right, t: r.top, b: r.bottom }; })()")
            check(tag + ' phone: the track pill sits beside the pause button on the top row, on screen', hud and hud['x'] >= 0 and hud['x'] + hud['w'] <= pb['l'] and hud['y'] < pb['b'] and hud['y'] + hud['h'] > pb['t'], [hud, pb])
            await page.evaluate(f"{SM}.toBoss()"); await play_phase(page); await page.wait_for_function(S + ".ui.bossBar", timeout=3000)
            bb = await page.evaluate(S + ".ui.bossBar"); bo = await page.evaluate(f"(() => {{ const o = {SM}.boss; return {{ kind: o.extra.kind, l: o.body.bounds.min.x, r: o.body.bounds.max.x, t: o.body.bounds.min.y }}; }})()")
            check(tag + ' phone: the wall\'s boss (the treasure safe) fits the screen under its health bar', bo['kind'] == 'safe' and bo['l'] >= 0 and bo['r'] <= 360 and bo['t'] > bb['y'] + bb['h'] and bb['x'] >= 0 and bb['x'] + bb['w'] <= 360, [bo, bb])
            for _ in range(8):
                bx = await page.evaluate(f"{SM}.boss.body.position.x"); by = await page.evaluate(f"{SM}.boss.body.position.y")
                await page.tap('#stage', position={'x': bx, 'y': by}); await page.wait_for_timeout(60)
            check(tag + ' phone: taps on the boss hurt it (one each)', 40 <= await page.evaluate(f"{SM}.boss.hp") <= 44, await page.evaluate(f"{SM}.boss.hp"))
            await menu_click(page, '#homeBtn', tap=True); await page.wait_for_timeout(300)
            check(tag + ' phone: Home from the sheet', await page.evaluate("mode === 'none' && !$('start').hidden"))
            check(tag + ' phone: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
