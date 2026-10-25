exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Sand (/sand, the Little ones): a tray of kinetic sand, touch only. Its link and sticker open it (EN / HE, no page errors, the demo finger + <= 3
# words, the pause menu is the way out); the finger digs a groove and the sand piles up on its sides (the volume stays); a touch leaves a
# fingerprint; retracing a groove digs to the tray's floor; a mold turns out a raised shape and its button again picks the next shape (its name
# said); the rake leaves four grooves; the roller evens a mound; the knife cuts thin and deep; a colour pours a mound of that colour and the
# finger smears it; two fingers dig at once; Home and back = a fresh flat tray; the sand's hiss plays only while the finger moves;
# the layout fits a small phone and a landscape one; the shading stays cheap (only the changed part is redrawn).
# Screenshots: tests/out/sand_*.png
S = '__grasp.sand'

async def sand_page(b, he=False, w=390, h=844):
    ctx, page, errs = await page_for(b, '/sand', he)
    if (w, h) != (390, 844): await page.set_viewport_size({'width': w, 'height': h})
    await wait(page, "gameMode === 'sand' && mode === 'mouse' && !!__grasp.sand.sa.L", 10000); await page.wait_for_timeout(500)
    return ctx, page, errs

async def box(page): return await page.evaluate(f"{S}.sa.L.box")
async def btn(page, kind, i):
    x, y = await page.evaluate(f"(() => {{ const b = {S}.sa.L.{kind}[{i}]; return [b.x, b.y]; }})()")
    await tap(page, x, y); await page.wait_for_timeout(380)
async def hat(page, x, y): return await page.evaluate(f"{S}.at({x}, {y})")
async def stroke(page, pts, steps=8, pid=1):
    await page.evaluate(f"fing('pointerdown', {pid}, {pts[0][0]}, {pts[0][1]})"); await page.wait_for_timeout(60)
    for a, c in zip(pts, pts[1:]):
        for k in range(1, steps + 1): await page.evaluate(f"fing('pointermove', {pid}, {a[0] + (c[0] - a[0]) * k / steps}, {a[1] + (c[1] - a[1]) * k / steps})"); await page.wait_for_timeout(16)
    await page.evaluate(f"fing('pointerup', {pid}, {pts[-1][0]}, {pts[-1][1]})"); await page.wait_for_timeout(120)
async def fresh(page): await page.evaluate("tgReset('sand')"); await page.wait_for_timeout(150)

async def mechanics(b):
    ctx, page, errs = await sand_page(b)
    B = await box(page); cx = B['ix'] + B['iw'] / 2; cy = B['iy'] + B['ih'] / 2; base = await page.evaluate(f"{S}.SA.base")
    check('the tray: the sand starts flat and natural (every cell within 3 px of the base level, one colour)', await page.evaluate(f"(() => {{ const a = {S}.sa; let m = 0; for (let k = 0; k < a.h.length; k++) m = Math.max(m, Math.abs(a.h[k] - {base})); return m < 3 && a.c.every((v) => v === 0); }})()"))
    # the finger: a groove, the sand piled on its sides, the volume kept
    s0 = await page.evaluate(f"{S}.sum()"); await page.evaluate(f"{S}.sa.sndMax = 0; window.__lv = 0; window.__lvT = setInterval(() => {{ __lv = Math.max(__lv, {S}.snd.lv); }}, 20)")
    await stroke(page, [(cx - 110, cy - 150), (cx + 110, cy - 150)], 14)
    g = await hat(page, cx, cy - 150); rim = max([await hat(page, cx, cy - 150 - d) for d in range(14, 40, 2)]); s1 = await page.evaluate(f"{S}.sum()")
    check('the finger digs a groove (%.1f px under the base) and the sand piles up beside it (%.1f px over)' % (base - g, rim - base), g < base - 4 and rim > base + 1.5, [g, rim])
    check('...the sand is pushed, not lost: the volume changes < 2%% (%.2f%%)' % (abs(s1 - s0) / s0 * 100), abs(s1 - s0) / s0 < 0.02, [s0, s1])
    lv = await page.evaluate("clearInterval(__lvT), __lv"); await page.wait_for_timeout(400); lv2 = await page.evaluate(f"{S}.snd.lv")
    check('the sand hisses while the finger moves (level %.2f) and goes quiet when it stops (%.2f)' % (lv, lv2), lv > 0.03 and lv2 < 0.01, [lv, lv2])
    check('...and every touch answers with a sound (the crunch)', 'crunch' in await snd(page))
    # a touch: a fingerprint
    await tap(page, cx + 90, cy + 40); fp = await hat(page, cx + 90, cy + 40)
    check('a touch leaves a fingerprint (%.1f px deep)' % (base - fp), fp < base - 1.5, fp)
    # retracing a groove digs down to the floor
    for k in range(5): await stroke(page, [(cx - 80, cy - 60), (cx + 80, cy - 60)], 10)
    fl = await page.evaluate(f"{S}.SA.floorAt"); g2 = await hat(page, cx, cy - 60)
    check('retracing a groove digs deeper, down to the tray\'s floor (%.1f px left, the floor shows under %.1f)' % (g2, fl), g2 < fl, g2)
    await page.screenshot(path=OUT + 'sand_finger.png')
    # the mold: a raised shape; its button again = the next shape, named
    await fresh(page); await btn(page, 'tools', 1)
    check('the mold button picks the mold (its shape said: "Star!")', await page.evaluate(f"{S}.sa.tool") == 'mold' and 'Star!' in await said(page), await said(page))
    await tap(page, cx, cy); await page.wait_for_timeout(850); top = await hat(page, cx + 2, cy + 6); out = await hat(page, cx + 90, cy + 90)
    check('a tap with the mold turns out a raised star (%.1f px over the sand around it)' % (top - out), top > out + 10 and await page.evaluate(f"{S}.sa.n.mold") == 1, [top, out])
    await btn(page, 'tools', 1)
    check('the mold button again: the next shape (the heart), named', await page.evaluate(f"{S}.SA.shapes[{S}.sa.shape]") == 'heart' and 'Heart!' in await said(page), await said(page))
    for i, (dx, dy) in enumerate([(-90, 170), (90, 170)]):
        if i: await btn(page, 'tools', 1)
        await tap(page, cx + dx, cy + dy); await page.wait_for_timeout(800)
    hearts = await hat(page, cx - 90, cy + 170 - 4); fish = await hat(page, cx + 90 + 10, cy + 170)
    check('...the heart and the fish stand in the sand too', hearts > base + 8 and fish > base + 8, [hearts, fish])
    await page.screenshot(path=OUT + 'sand_molds.png')
    # the roller evens the star out
    await btn(page, 'tools', 3)
    for k in range(4): await stroke(page, [(cx - 70, cy), (cx + 70, cy)], 12)
    top2 = await hat(page, cx + 2, cy + 6)
    check('the roller evens the star out (%.1f -> %.1f px)' % (top, top2), top2 < top - 4, [top, top2])
    # the rake: four grooves side by side
    await fresh(page); await btn(page, 'tools', 2); await stroke(page, [(cx - 120, cy), (cx + 120, cy)], 20)
    prof = await page.evaluate(f"[...Array(81).keys()].map((d) => {S}.at({cx}, {cy} - 40 + d))")
    mins = sum(1 for i in range(len(prof)) if prof[i] < base - 2.5 and (i == 0 or prof[i - 1] >= base - 2.5))  # (the runs under the surface)
    check('the rake leaves four grooves side by side (%d found)' % mins, mins == 4, [round(v, 1) for v in prof])
    # the knife: thin and deep
    await fresh(page); await btn(page, 'tools', 4); await stroke(page, [(cx, cy - 100), (cx, cy + 100)], 20)
    k0 = await hat(page, cx, cy); k1 = await hat(page, cx + 16, cy)
    check('the knife cuts thin and deep (%.1f px deep in the cut, %.1f px beside it)' % (base - k0, base - k1), k0 < base - 8 and k1 > base - 3, [k0, k1])
    # colours: a mound of pink, smeared by the finger
    await fresh(page); await btn(page, 'cols', 1)
    check('a colour: picked (named "Pink!"), the finger now pours it', await page.evaluate(f"{S}.sa.tool") == 'pour' and 'Pink!' in await said(page), await said(page))
    await page.evaluate(f"fing('pointerdown', 1, {cx - 40}, {cy})"); await page.wait_for_timeout(1300); await page.evaluate(f"fing('pointerup', 1, {cx - 40}, {cy})"); await page.wait_for_timeout(200)
    ph = await hat(page, cx - 40, cy); pc = await page.evaluate(f"{S}.colAt({cx - 40}, {cy})")
    check('holding: pink sand falls into a mound (%.1f px over the base) and it is pink' % (ph - base), ph > base + 6 and pc == 1, [ph, pc])
    def pinks(): return page.evaluate(f"(() => {{ const a = {S}.sa, B = a.L.box; let n = 0; for (let j = 0; j < a.GH; j++) for (let i = 0; i < a.GW; i++) {{ const x = B.ix + (i + 0.5) * a.cs; if (x > {cx} + 10 && a.c[j * a.GW + i] === 1) n++; }} return n; }})()")
    p0 = await pinks(); await btn(page, 'tools', 0); await stroke(page, [(cx - 70, cy), (cx + 80, cy)], 16); p1 = await pinks()
    check('the finger drags pink into the plain sand (pink cells right of the mound: %d -> %d)' % (p0, p1), p1 > p0 + 5, [p0, p1])
    await page.screenshot(path=OUT + 'sand_colours.png')
    # one finger: a second never steals the first
    await fresh(page); await page.evaluate(f"fing('pointerdown', 1, {cx - 60}, {cy})"); await page.evaluate(f"fing('pointerdown', 2, {cx + 60}, {cy + 120})")
    for k in range(1, 9): await page.evaluate(f"fing('pointermove', 2, {cx + 60 + k * 8}, {cy + 120})"); await page.wait_for_timeout(16)
    await page.evaluate(f"fing('pointerup', 2, {cx + 124}, {cy + 120})"); await page.evaluate(f"fing('pointerup', 1, {cx - 60}, {cy})"); await page.wait_for_timeout(150)
    check('two fingers at once: each digs its own groove (every finger plays)', await hat(page, cx + 90, cy + 120) < base - 3 and await hat(page, cx - 60, cy) < base - 1.5)
    # Restart: a fresh flat tray
    await btn(page, 'cols', 2); await page.evaluate(f"fing('pointerdown', 1, {cx}, {cy})"); await page.wait_for_timeout(500); await page.evaluate(f"fing('pointerup', 1, {cx}, {cy})")
    await page.evaluate("goHome()"); await page.wait_for_timeout(400); await page.evaluate("__grasp.setGameMode('sand'); strikeStart('mouse')"); await wait(page, "gameMode === 'sand' && mode === 'mouse'", 8000); await page.wait_for_timeout(300)
    check('Home and back (the Little ones pause sheet has no Restart): a fresh flat tray of plain sand, the finger again', await page.evaluate(f"(() => {{ const a = {S}.sa; let m = 0; for (let k = 0; k < a.h.length; k++) m = Math.max(m, Math.abs(a.h[k] - {base})); return m < 3 && a.c.every((v) => v === 0) && a.tool === 'finger'; }})()"))
    # cheap: only the changed part is shaded
    ms = await page.evaluate(f"{S}.sa.shadeMs"); await stroke(page, [(cx - 30, cy), (cx + 30, cy)], 6); cells = await page.evaluate(f"{S}.sa.lastCells || 0"); allc = await page.evaluate(f"{S}.sa.GW * {S}.sa.GH")
    check('the shading is cheap: only the changed part is redrawn (%d of %d cells), %.1f ms a frame' % (cells, allc, ms), 0 < cells < allc * 0.5 and ms < 12, [cells, allc, ms])
    check('mechanics: no page errors', not errs, errs); await ctx.close()

async def layouts(b):
    for he, (w, h) in ((False, (320, 568)), (True, (390, 844)), (False, (844, 390)), (True, (1280, 800))):
        tag = ('HE' if he else 'EN') + ' %dx%d' % (w, h); ctx, page, errs = await sand_page(b, he, w, h)
        r = await page.evaluate(f"""(() => {{ const L = {S}.sa.L, B = L.box, bs = [...L.tools, ...L.cols];
          const inside = bs.every((b) => b.x - b.r >= 0 && b.x + b.r <= innerWidth && b.y - b.r >= 0 && b.y + b.r <= innerHeight);
          const clear = bs.every((b) => b.y - b.r >= B.y + B.h); let apart = true; for (const a of bs) for (const c of bs) if (a !== c && Math.hypot(a.x - c.x, a.y - c.y) < a.r + c.r) apart = false;
          const pb = $('pauseBtn').getBoundingClientRect();
          return {{ inside, clear, apart, tool: Math.min(...L.tools.map((b) => b.r * 2)), col: Math.min(...L.cols.map((b) => b.r * 2)), bh: B.h, under: B.y >= pb.bottom - 2, rtl: L.tools[0].x > L.tools[4].x }}; }})()""")
        check(tag + ': the tray, then the tools (%d px) and the colours (%d px): all on screen, apart, under the pause button; RTL mirrors the row' % (r['tool'], r['col']),
              r['inside'] and r['clear'] and r['apart'] and r['tool'] >= 54 and r['col'] >= 40 and r['bh'] >= 140 and r['under'] and r['rtl'] == he, r)
        await page.screenshot(path=OUT + 'sand_%s_%dx%d.png' % ('he' if he else 'en', w, h))
        check(tag + ': no page errors', not errs, errs); await ctx.close()

async def sticker(b):
    ctx, page, errs = await page_for(b, '/', True)
    await page.tap('#littleBtn'); await wait(page, "!$('littlePick').hidden", 3000); await page.wait_for_timeout(500)
    await page.evaluate("(() => { const b = document.querySelector('#littlePick button[data-mode=sand]'); __grasp.menub.page([...$('mbPager').querySelectorAll('.mbPg')].indexOf(b.closest('.mbPg')), true); })()"); await page.wait_for_timeout(400)
    lb = await page.evaluate("document.querySelector('#littlePick button[data-mode=sand] .lb').textContent")
    await page.tap('#littlePick button[data-mode=sand]'); ok = await wait(page, "gameMode === 'sand' && mode === 'mouse'", 8000)
    check('HE: the Little ones sticker "' + lb + '" opens the sand in one tap', ok and lb == 'חול קינטי', lb)
    check('sticker: no page errors', not errs, errs); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for he in (False, True): await link_tests(b, 'sand', he)
        await mechanics(b); await layouts(b); await sticker(b)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
