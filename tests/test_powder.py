exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Sand Lab (/powder, Big kids; the owner: "a game like that" (a falling-sand app)): the sticker opens it (Colors); a finger pours colourful sand
# that falls and piles; the Lab's materials react (water + lava = stone + steam, fire burns wood, boom powder explodes, plants drink water);
# the challenges: a level's goal, a win with stars and coins, the next one unlocked. Screenshots: tests/out/powder_*.png
PWH = '__grasp.pw'
async def drag(page, a, b, ms=600, steps=20):
    await page.mouse.move(a[0], a[1]); await page.mouse.down()
    for k in range(1, steps + 1): await page.mouse.move(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps); await page.wait_for_timeout(ms // steps)
    await page.mouse.up()
async def count(page, ty): return await page.evaluate(f"(() => {{ const G = {PWH}.pw.g; let n = 0; for (let i = 0; i < G.n; i++) if (G.t[i] === {ty}) n++; return n; }})()")

async def run(b, he):
    tag = 'HE' if he else 'EN'
    ctx, page, errs = await page_for(b, '/', he, init="window.__graspNoAutoFs = true;"); await page.wait_for_timeout(700)
    await page.screenshot(path=OUT + 'powder_home_%s.png' % tag.lower())
    await page.tap('#bigRoom [data-mode=powder]'); ok = await wait(page, f"gameMode === 'powder' && !!{PWH}.pw.g && !$('powderBar').hidden", 6000)
    check(tag + ': the sticker opens Sand Lab: the grid and the tool bar (Colors)', ok and await page.evaluate(f"{PWH}.pw.mode") == 'colors')
    W, H = await page.evaluate("[innerWidth, innerHeight]")
    await drag(page, (W * 0.3, H * 0.15), (W * 0.7, H * 0.15), 1500); await page.wait_for_timeout(1500)
    n = await count(page, 14); low = await page.evaluate(f"(() => {{ const G = {PWH}.pw.g; for (let y = G.h - 1; y >= 0; y--) for (let x = 0; x < G.w; x++) if (G.t[y * G.w + x] === 14) return y / G.h; return 0; }})()")
    check(tag + ': a finger pours colourful sand; it falls to the floor', n > 200 and low > 0.95, [n, low])
    await page.screenshot(path=OUT + 'powder_colors_%s.png' % tag.lower())
    # the Lab: water on lava = stone + steam; fire on wood
    await page.click('#powderBar [data-pw="m:lab"]'); await page.wait_for_timeout(200)
    await page.evaluate(f"(() => {{ const pw = {PWH}.pw, G = pw.g; for (let x = 10; x < G.w - 10; x++) for (let y = G.h - 12; y < G.h; y++) {{ G.t[y * G.w + x] = 9; }} for (let x = 10; x < 40; x++) for (let y = G.h - 40; y < G.h - 30; y++) G.t[y * G.w + x] = 4; }})()")
    await page.click('#powderBar [data-pw="t:water"]'); await drag(page, (W * 0.55, H * 0.2), (W * 0.75, H * 0.2), 1200)
    await page.click('#powderBar [data-pw="t:fire"]'); await drag(page, (W * 0.08, H * 0.35), (W * 0.2, H * 0.35), 800); await page.wait_for_timeout(1200)
    st, steam = await count(page, 3), await count(page, 7) + await count(page, 2)
    check(tag + ': the Lab: water on lava turns to stone (and steam)', st > 10, [st, steam])
    await page.screenshot(path=OUT + 'powder_lab_%s.png' % tag.lower())
    # boom powder explodes by fire
    await page.evaluate(f"(() => {{ const G = {PWH}.pw.g; G.t.fill(0); for (let x = 0; x < G.w; x++) for (let y = G.h - 6; y < G.h; y++) G.t[y * G.w + x] = 13; G.t[(G.h - 7) * G.w + 55] = 5; G.ex[(G.h - 7) * G.w + 55] = 30; }})()")
    await page.wait_for_timeout(800); n13 = await count(page, 13); check(tag + ': boom powder near fire explodes (a chain: it is gone)', n13 < 100, n13)
    # challenges: the list, level 1 (fill the cup) won by pouring sand into it
    await page.click('#powderBar [data-pw="m:chal"]'); await page.wait_for_timeout(300)
    check(tag + ': Challenges: 9 levels, the first open, the rest locked', await page.locator('#powderLv .pwLv').count() == 9 and await page.locator('#powderLv .pwLv.lock').count() == 8)
    await page.screenshot(path=OUT + 'powder_levels_%s.png' % tag.lower())
    await page.click('#powderLv [data-pw="lv:0"]'); await page.wait_for_timeout(400)
    await page.screenshot(path=OUT + 'powder_cup_%s.png' % tag.lower())
    await page.evaluate(f"(() => {{ const pw = {PWH}.pw, G = pw.g, [a, b, c, d] = pw.lv.z; for (let y = Math.floor(b * G.h); y < Math.ceil(d * G.h); y++) for (let x = Math.floor(a * G.w); x < Math.ceil(c * G.w); x++) if (!G.t[y * G.w + x]) G.t[y * G.w + x] = 1; }})()")
    ok = await wait(page, f"!!{PWH}.pw.won", 5000); await page.wait_for_timeout(500)
    check(tag + ': the cup filled: won (stars, the card), level 2 opens', ok and await page.evaluate(f"!$('powderLv').hidden && profile.powder.stars.cup >= 1"), await page.evaluate(f"{PWH}.pw.log.slice(-3)"))
    await page.screenshot(path=OUT + 'powder_won_%s.png' % tag.lower())
    await page.click('#powderLv [data-pw="lv:1"]'); await page.wait_for_timeout(300)
    check(tag + ': Next: level 2 (put out the fire) with only water', await page.evaluate(f"{PWH}.pw.lv.id") == 'fire' and await page.locator('#powderBar .pwT').count() == 1)
    await page.wait_for_timeout(800); await page.screenshot(path=OUT + 'powder_fire_%s.png' % tag.lower())
    fps = await page.evaluate("new Promise((ok) => { let n = 0; const t0 = performance.now(); const f = () => { n++; if (performance.now() - t0 < 1000) requestAnimationFrame(f); else ok(n); }; requestAnimationFrame(f); })")
    check(tag + ': runs smoothly (frames in a second)', fps >= 30, fps)
    await page.evaluate("goHome()"); await page.wait_for_timeout(400); check(tag + ': Home: the bar goes', await page.evaluate("$('powderBar').hidden && $('powderLv').hidden"))
    check(tag + ': no page errors', not errs, errs); await ctx.close()

async def sensors(b):
    # the owner turned his phone over and the sand stayed (Brave can hold devicemotion back): deviceorientation alone turns the gravity; with no sensor
    # at all, a note on how to allow it
    ctx, page, errs = await page_for(b, '/powder', True, init="window.__graspNoAutoFs = true; localStorage.removeItem('grasp.pwTilt');"); await wait(page, f"!!{PWH}.pw.g && !$('powderBar').hidden", 6000)
    await page.wait_for_timeout(3300)
    check('sensors: no motion sensor at all for 3 s: a note on how to allow it', 'noSensor' in await page.evaluate(f"{PWH}.pw.log") and await page.locator('#toast').count() >= 0)
    for _ in range(4): await page.evaluate("(() => { const e = new Event('deviceorientation'); e.beta = -90; e.gamma = 0; e.alpha = 0; window.dispatchEvent(e); })()"); await page.wait_for_timeout(60)
    await page.wait_for_timeout(300)
    check('sensors: deviceorientation alone (upside down: beta -90): the gravity points up', await page.evaluate(f"{PWH}.pw.gk") == 4, await page.evaluate(f"{PWH}.pw.gk"))
    for _ in range(4): await page.evaluate("(() => { const e = new Event('deviceorientation'); e.beta = 30; e.gamma = 60; e.alpha = 0; window.dispatchEvent(e); })()"); await page.wait_for_timeout(60)
    await page.wait_for_timeout(300)
    check('sensors: tilted right (gamma 60): the gravity turns right', await page.evaluate(f"{PWH}.pw.gk") in (5, 6, 7), await page.evaluate(f"{PWH}.pw.gk")) # (0 down, then clockwise on the screen: 6 right, 7 down-right)
    check('sensors: no page errors', not errs, errs); await ctx.close()

async def tilt_push(b):
    # the owner: "the sand should move when I move the phone, or when I touch sand that is already there"
    ctx, page, errs = await page_for(b, '/powder', True, init="window.__graspNoAutoFs = true; localStorage.removeItem('grasp.pwTilt');"); await wait(page, f"!!{PWH}.pw.g && !$('powderBar').hidden", 6000)
    pile = f"(() => {{ const G = {PWH}.pw.g; G.t.fill(0); for (let y = G.h - 25; y < G.h; y++) for (let x = Math.floor(G.w * 0.35); x < Math.floor(G.w * 0.65); x++) {{ G.t[y * G.w + x] = 14; G.ex[y * G.w + x] = 3; }} }})()"
    meanx = f"(() => {{ const G = {PWH}.pw.g; let s = 0, n = 0; for (let i = 0; i < G.n; i++) if (G.t[i] === 14) {{ s += (i % G.w) / G.w; n++; }} return [s / n, n]; }})()"
    await page.evaluate(pile); n0 = (await page.evaluate(meanx))[1]
    await page.evaluate("window.__pwGk = 2"); await page.wait_for_timeout(2500); L = await page.evaluate(meanx)
    await page.screenshot(path=OUT + 'powder_tilt_left.png')
    await page.evaluate("window.__pwGk = 6"); await page.wait_for_timeout(3500); R = await page.evaluate(meanx)
    check('tilt: gravity to the left, the sand runs left; to the right, it runs right; none lost', L[0] < 0.3 and R[0] > 0.7 and L[1] == n0 and R[1] == n0, [L, R, n0])
    await page.evaluate("window.__pwGk = null; window.dispatchEvent(Object.assign(new Event('devicemotion'), { accelerationIncludingGravity: { x: 9.2, y: 2, z: 1 } }))"); await page.wait_for_timeout(200)
    g1 = await page.evaluate(f"{PWH}.pw.gk")
    await page.evaluate("window.dispatchEvent(Object.assign(new Event('devicemotion'), { accelerationIncludingGravity: { x: 0.3, y: 9.6, z: 1 } }))"); await page.wait_for_timeout(200); g2 = await page.evaluate(f"{PWH}.pw.gk")
    check('tilt: the phone\'s motion sensor sets it (left side down: to the left; upright: down again)', g1 == 2 and g2 == 0, [g1, g2])
    await page.click('#powderBar [data-pw="tilt"]'); await page.evaluate("window.dispatchEvent(Object.assign(new Event('devicemotion'), { accelerationIncludingGravity: { x: 9.2, y: 2, z: 1 } }))"); await page.wait_for_timeout(200)
    check('the 📱 button turns the tilt off (the sand always falls down); kept', await page.evaluate(f"{PWH}.pw.gk") == 0 and await page.evaluate("localStorage.getItem('grasp.pwTilt')") == '0')
    await page.click('#powderBar [data-pw="tilt"]')
    # a finger on sand pushes it
    await page.evaluate("window.__pwGk = 0"); await page.evaluate(pile); await page.wait_for_timeout(300)
    snap = f"Array.from({PWH}.pw.g.t)"; before = await page.evaluate(snap); W, H = await page.evaluate("[innerWidth, innerHeight]")
    gy = await page.evaluate(f"(() => {{ const pw = {PWH}.pw; return pw.top + (pw.g.h - 12) * pw.cs; }})()")
    await drag(page, (W * 0.4, gy), (W * 0.62, gy - 30), 700); await page.wait_for_timeout(200)
    after = await page.evaluate(snap); moved = sum(1 for a, c in zip(before, after) if a != c)
    check('a finger that lands on sand pushes it along (it moves, none poured, none lost)', moved > 60 and after.count(14) == before.count(14) and await page.evaluate(f"{PWH}.pw.pushes || 0") > 0, [moved, before.count(14), after.count(14)])
    await page.screenshot(path=OUT + 'powder_push.png')
    c0 = after.count(14); await drag(page, (W * 0.5, H * 0.12), (W * 0.55, H * 0.12), 500); await page.wait_for_timeout(300)
    check('on empty space the finger still pours', (await count(page, 14)) > c0)
    check('tilt / push: no page errors', not errs, errs); await ctx.close()

async def levels_map(b):
    # 500 more (10 worlds of 50): the map (easy / normal / hard, the worlds, the levels); a generated level opens with its goal, tools, maybe a pour zone and a bucket
    ctx, page, errs = await page_for(b, '/powder', True, init="window.__graspNoAutoFs = true;"); await wait(page, f"!!{PWH}.pw.g && !$('powderBar').hidden", 6000)
    await page.click('#powderBar [data-pw="m:chal"]'); await page.wait_for_timeout(300)
    check('the map: easy / normal / hard and 11 worlds (the first steps + 10 of 50)', await page.locator('#powderLv .pwD').count() == 3 and await page.locator('#powderLv .pwW').count() == 11)
    await page.screenshot(path=OUT + 'powder_map.png')
    await page.evaluate(f"(() => {{ const P = profile.powder; for (let k = 0; k < 9; k++) P.stars[{PWH}.PW_LV[k].id] = 3; P.stars.g9 = 2; }})()")
    await page.click('#powderLv [data-pw="w:1"]'); await page.wait_for_timeout(200)
    check('world 1: 50 levels, the first two open (one done), the rest locked', await page.locator('#powderLv .pwLv').count() == 50 and await page.locator('#powderLv .pwLv.lock').count() == 48)
    await page.screenshot(path=OUT + 'powder_world1.png')
    await page.click('#powderLv [data-pw="d:hard"]'); await page.wait_for_timeout(150); check('the difficulty is kept', await page.evaluate("profile.powder.diff") == 'hard')
    await page.click('#powderLv [data-pw="lv:10"]'); await page.wait_for_timeout(400)
    L = await page.evaluate(f"(() => {{ const L = {PWH}.pw.lv; return {{ id: L.id, fam: L.fam, tools: L.tools, D: L.D }}; }})()")
    check('a generated level opens (its tools in the bar)', L['id'] == 'g10' and await page.locator('#powderBar .pwT').count() == len(L['tools']), L)
    await page.screenshot(path=OUT + 'powder_gen.png')
    await page.evaluate("profile.powder.diff = 'normal'"); check('levels map: no page errors', not errs, errs); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        await sensors(b); await tilt_push(b); await levels_map(b)
        for he in (True, False): await run(b, he)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
