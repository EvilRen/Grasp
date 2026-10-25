exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Grip + every finger (the owner, Oct 2026: "my daughter holds the phone in both hands, a finger of the holding hand rests on the screen's edge and
# the game is blocked"). In the Little ones games, Sand and Paint: a touch that starts in the edge band and stays is held back (it does nothing and
# blocks nothing); slid inward it becomes a finger; a quick tap in the band still taps; a palm-sized contact anywhere is held back; every other
# finger plays at once (two grooves in the sand, two strokes in Paint, two puzzle pieces carried). Big kids' games: untouched.
# Screenshots: tests/out/grip_*.png
S = '__grasp.sand'; GR = '__grasp.grip'; CG = '__grasp.cg'

async def down(page, pid, x, y, w=1):
    await page.evaluate(f"document.getElementById('stage').dispatchEvent(new PointerEvent('pointerdown', {{ pointerId: {pid}, pointerType: 'touch', clientX: {x}, clientY: {y}, isPrimary: {str(pid == 1).lower()}, bubbles: true, cancelable: true, button: 0, buttons: 1, width: {w}, height: {w} }}))")
async def move(page, pid, x, y): await page.evaluate(f"fing('pointermove', {pid}, {x}, {y})")
async def up(page, pid, x, y): await page.evaluate(f"fing('pointerup', {pid}, {x}, {y})")
async def drag1(page, pid, a, c, steps=12):
    await down(page, pid, *a); await page.wait_for_timeout(40)
    for k in range(1, steps + 1): await move(page, pid, a[0] + (c[0] - a[0]) * k / steps, a[1] + (c[1] - a[1]) * k / steps); await page.wait_for_timeout(18)
    await up(page, pid, *c); await page.wait_for_timeout(120)
async def drag2(page, a, c, steps=12):
    """fingers 2 and 3 drag at the same time"""
    await down(page, 2, *a[0]); await down(page, 3, *c[0]); await page.wait_for_timeout(50)
    for k in range(1, steps + 1):
        await move(page, 2, a[0][0] + (a[1][0] - a[0][0]) * k / steps, a[0][1] + (a[1][1] - a[0][1]) * k / steps)
        await move(page, 3, c[0][0] + (c[1][0] - c[0][0]) * k / steps, c[0][1] + (c[1][1] - c[0][1]) * k / steps); await page.wait_for_timeout(18)
    await up(page, 2, *a[1]); await up(page, 3, *c[1]); await page.wait_for_timeout(150)

async def sand(b, he):
    tag = 'sand ' + ('HE' if he else 'EN')
    ctx, page, errs = await page_for(b, '/sand', he); await wait(page, "gameMode === 'sand' && mode === 'mouse' && !!__grasp.sand.sa.L", 10000); await page.wait_for_timeout(500)
    B = await page.evaluate(f"{S}.sa.L.box"); cx = B['ix'] + B['iw'] / 2; cy = B['iy'] + B['ih'] / 2; base = await page.evaluate(f"{S}.SA.base"); band = await page.evaluate(f"{GR}.band()")
    at = lambda x, y: page.evaluate(f"{S}.at({x}, {y})")
    # the holding hand: a finger resting on the right edge (over the tray's rim and sand), for the whole time
    hx, hy = 390 - band * 0.4, cy + 60; await down(page, 1, hx, hy); await page.wait_for_timeout(400)
    check(tag + ': a finger resting on the edge (the band: %d px) is held back: no press, no fingerprint' % band, await page.evaluate("__grasp.tg.tg.presses.size") == 0 and await page.evaluate(f"{GR}.grip.pend.size") == 1 and await at(390 - B['rim'] - 4 - 25, hy) > base - 1.5)
    await drag1(page, 2, (cx - 100, cy - 150), (cx + 100, cy - 150))
    check(tag + ': ...and the other hand digs anyway (a groove %.1f px deep)' % (base - await at(cx, cy - 150)), await at(cx, cy - 150) < base - 4)
    await drag2(page, [(cx - 100, cy - 40), (cx + 60, cy - 40)], [(cx - 100, cy + 120), (cx + 60, cy + 120)])
    g1, g2 = await at(cx - 20, cy - 40), await at(cx - 20, cy + 120)
    check(tag + ': two fingers dig two grooves at once (%.1f and %.1f px deep), the edge finger still resting' % (base - g1, base - g2), g1 < base - 4 and g2 < base - 4 and await page.evaluate(f"{GR}.grip.pend.size") == 1, [g1, g2])
    await up(page, 1, hx, hy); await page.wait_for_timeout(150)
    check(tag + ': the resting finger lifted after a while: still nothing (no late tap)', await page.evaluate(f"{GR}.grip.pend.size") == 0 and await page.evaluate(f"{GR}.grip.log.slice(-1)[0]") == 'let go')
    # sliding in from the edge: a finger from where it leaves the band
    await drag1(page, 4, (B['ix'] + 4, cy + 230), (cx + 60, cy + 230), 16) if B['ix'] + 4 < band else None
    sx = B['ix'] + 4
    if sx < band: check(tag + ': a finger sliding in from the edge is a finger: it digs all the way (%.1f px deep in the middle)' % (base - await at(cx, cy + 230)), await at(cx, cy + 230) < base - 4 and await page.evaluate(f"{GR}.grip.slides") >= 1)
    else: check(tag + ': (the tray starts outside the edge band here)', True)
    # a quick tap in the band still taps: the colour dot's lower edge, near the bottom
    d = await page.evaluate(f"(() => {{ const b = {S}.sa.L.btns.find(q => q.id === 'night'); return [b.x, Math.max(3, b.y - b.r + 4)]; }})()")
    inband = d[1] < band
    await tap(page, d[0], d[1], hold=60, pid=5); await page.wait_for_timeout(300)
    check(tag + ': a quick tap in the edge band still taps (the moon button\'s upper rim, in the top band: glow on)' + ('' if inband else ' (not in the band here)'), await page.evaluate(f"{S}.sa.night") and (not inband or await page.evaluate(f"{GR}.grip.taps") >= 1))
    await page.evaluate(f"{S}.night(false)")
    # a palm anywhere: held back
    h0 = await at(cx, cy + 300)
    await down(page, 6, cx, cy + 300, w=110); await page.wait_for_timeout(100); await move(page, 6, cx + 40, cy + 300); await up(page, 6, cx + 40, cy + 300); await page.wait_for_timeout(150)
    check(tag + ': a palm-sized contact in the middle is held back (no dent)', abs(await at(cx, cy + 300) - h0) < 0.5)
    await page.screenshot(path=OUT + 'grip_sand_%s.png' % ('he' if he else 'en'))
    check(tag + ': no page errors', not errs, errs); await ctx.close()

async def paint(b):
    ctx, page, errs = await page_for(b, '/paint'); await wait(page, "gameMode === 'paint' && mode === 'mouse'", 10000)
    if await page.evaluate(f"{CG}.asking"): await page.click('#cgCamTouch')
    await page.evaluate("hideHint()"); await page.wait_for_timeout(400)
    await down(page, 1, 4, 500); await page.wait_for_timeout(300)  # (the holding hand on the left edge)
    await drag1(page, 2, (120, 220), (300, 300), 14)
    st = await page.evaluate(f"({{ s: {CG}.paint.strokes, ink: {CG}.paint.ink, t: ptr.touches.size }})")
    check('paint: a finger resting on the edge does not stop the other hand drawing (1 stroke, ink %d)' % st['ink'], st['s'] == 1 and st['ink'] > 120 and st['t'] == 0, st)
    i0 = await page.evaluate(f"{CG}.paint.ink"); await drag2(page, [(100, 380), (300, 380)], [(100, 560), (300, 600)])
    st = await page.evaluate(f"({{ s: {CG}.paint.strokes, ink: {CG}.paint.ink, mm: {CG}.paint.multiMax || 0, dr: {CG}.paint.drawing, a: {CG}.paintInk(90, 360, 310, 400), b: {CG}.paintInk(90, 540, 310, 620) }})")
    check('paint: two fingers draw two strokes at once (both on the drawing)', st['s'] == 3 and st['mm'] == 2 and st['a'] > 50 and st['b'] > 50 and not st['dr'], st)
    await up(page, 1, 4, 500); await page.screenshot(path=OUT + 'grip_paint.png')
    check('paint: no page errors', not errs, errs); await ctx.close()

async def toddlers(b):
    # Animals: the holding finger rests on the edge, a tap on an animal still plays it
    ctx, page, errs = await page_for(b, '/animals'); await wait(page, "gameMode === 'animals' && mode === 'mouse'", 10000); await page.wait_for_timeout(600)
    await down(page, 1, 386, 600); await page.wait_for_timeout(300)
    a = await page.evaluate("(() => { const A = __grasp.tg.an.list || __grasp.tg.an.animals || []; const q = A[0]; return q ? [q.x, q.y] : null; })()")
    if not a: a = [195, 420]
    n0 = len(await snd(page)); await tap(page, a[0], a[1], pid=2); await page.wait_for_timeout(300); s1 = await snd(page)
    check('animals: with a finger resting on the edge, a tap on an animal still plays (a sound)', len(s1) > n0, s1[-4:])
    await up(page, 1, 386, 600); check('animals: no page errors', not errs, errs); await ctx.close()
    # Puzzle: two pieces carried at once
    ctx, page, errs = await page_for(b, '/puzzle'); await wait(page, "gameMode === 'puzzle' && mode === 'mouse'", 10000); await page.wait_for_timeout(600)
    P = await page.evaluate("__grasp.tg.pz.pieces.filter(p => !p.placed).map(p => ({ i: p.i, x: p.x, y: p.y }))")
    if len(P) >= 2:
        a, c = P[0], P[1]
        await drag2(page, [(a['x'], a['y']), (a['x'] + 10, a['y'] - 120)], [(c['x'], c['y']), (c['x'] - 10, c['y'] - 120)], 10)
        Q = await page.evaluate("__grasp.tg.pz.pieces.map(p => ({ i: p.i, x: p.x, y: p.y, placed: p.placed }))")
        qa = next(q for q in Q if q['i'] == a['i']); qc = next(q for q in Q if q['i'] == c['i'])
        moved = lambda q, o: q['placed'] or abs(q['y'] - o['y']) > 60
        check('puzzle: two fingers carry two pieces at once (both moved or placed)', moved(qa, a) and moved(qc, c), [a, qa, c, qc])
    else: check('puzzle: (fewer than 2 pieces)', False, P)
    check('puzzle: no page errors', not errs, errs); await ctx.close()

async def bigkids(b):
    ctx, page, errs = await page_for(b, '/slice'); await wait(page, "gameMode === 'slice' && mode === 'mouse'", 10000); await page.wait_for_timeout(400)
    await down(page, 1, 4, 500); await page.wait_for_timeout(100)
    check('Big kids (Slice): the grip filter is off (an edge touch is a touch)', await page.evaluate(f"!{GR}.on()") and await page.evaluate("ptr.touches.size") == 1)
    await up(page, 1, 4, 500); check('slice: no page errors', not errs, errs); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for he in (False, True): await sand(b, he)
        await paint(b); await toddlers(b); await bigkids(b)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
