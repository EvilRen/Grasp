exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Sand (/sand, the Little ones): a tray of kinetic sand, touch only, finger only (v2: the owner, "too pixelated, only the finger, glow in the dark"). Its link and sticker open it (EN / HE, no page errors, the demo finger + <= 3
# words, the house in the corner is the way out: one tap, home); the finger digs a groove and the sand piles up on its sides (the volume stays); a touch leaves a
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
    flat = f"(() => {{ const a = {S}.sa; let m = 0; for (let k = 0; k < a.h.length; k++) m = Math.max(m, Math.abs(a.h[k] - a.h0[k])); return m < 0.01; }})()"
    check('the tray: fresh soft sand, ~2 px a cell on a phone (%d cells)' % await page.evaluate(f"{S}.sa.GW * {S}.sa.GH"), await page.evaluate(flat) and await page.evaluate(f"{S}.sa.cs") < 2.5 and await page.evaluate(f"{S}.sa.GW * {S}.sa.GH") > 50000)
    check('finger only: two buttons (smooth, moon), no tools, no colours', sorted((await page.evaluate(f"{S}.sa.L.btns.map(b => b.id).join()")).split(',')) == ['night', 'smooth'] and await page.evaluate(f"!{S}.sa.L.tools && !{S}.sa.L.cols"))
    # the finger: a groove, the sand piled on its sides, the volume kept
    s0 = await page.evaluate(f"{S}.sum()"); await page.evaluate(f"window.__lv = 0; window.__lvT = setInterval(() => {{ __lv = Math.max(__lv, {S}.snd.lv); }}, 20)")
    await stroke(page, [(cx - 110, cy - 150), (cx + 110, cy - 150)], 14)
    g = await hat(page, cx, cy - 150); rim = max([await hat(page, cx, cy - 150 - d) for d in range(14, 40, 2)]); s1 = await page.evaluate(f"{S}.sum()")
    check('the finger digs a groove (%.1f px under the base) and the sand piles up beside it (%.1f px over)' % (base - g, rim - base), g < base - 4 and rim > base + 1.5, [g, rim])
    check('...the sand is pushed, not lost: the volume changes < 2%% (%.2f%%)' % (abs(s1 - s0) / s0 * 100), abs(s1 - s0) / s0 < 0.02, [s0, s1])
    rough = await page.evaluate(f"""(() => {{ const a = {S}.sa, j = Math.round(({cy} - 150 - 26 - a.L.box.iy) / a.csy); let m = 0; for (let i = Math.round(({cx} - 60 - a.L.box.ix) / a.cs); i < Math.round(({cx} + 60 - a.L.box.ix) / a.cs); i++) {{ const k = j * a.GW + i; m = Math.max(m, Math.abs(a.h[k] - (a.h[k - 1] + a.h[k + 1]) / 2)); }} return m; }})()""")
    check('...its rim is smooth along the stroke (no teeth: %.2f px from the neighbours\' mean)' % rough, rough < 0.6, rough)
    lv = await page.evaluate("clearInterval(__lvT), __lv"); await page.wait_for_timeout(400); lv2 = await page.evaluate(f"{S}.snd.lv")
    check('the sand hisses while the finger moves (level %.2f) and goes quiet when it stops (%.2f)' % (lv, lv2), lv > 0.03 and lv2 < 0.01, [lv, lv2])
    check('...and every touch answers with a sound (the crunch)', 'crunch' in await snd(page))
    await tap(page, cx + 90, cy + 40); fp = await hat(page, cx + 90, cy + 40)
    check('a touch leaves a fingerprint (%.1f px deep)' % (base - fp), fp < base - 1.5, fp)
    for k in range(5): await stroke(page, [(cx - 80, cy - 60), (cx + 80, cy - 60)], 10)
    fl = await page.evaluate(f"{S}.SA.floorAt"); g2 = await hat(page, cx, cy - 60)
    check('retracing a groove digs deeper, down to the tray\'s floor (%.1f px left, the floor shows under %.1f)' % (g2, fl), g2 < fl, g2)
    # two fingers at once
    await page.evaluate(f"fing('pointerdown', 1, {cx - 60}, {cy + 200})"); await page.evaluate(f"fing('pointerdown', 2, {cx + 60}, {cy + 120})")
    for k in range(1, 9): await page.evaluate(f"fing('pointermove', 2, {cx + 60 + k * 8}, {cy + 120})"); await page.wait_for_timeout(16)
    await page.evaluate(f"fing('pointerup', 2, {cx + 124}, {cy + 120})"); await page.evaluate(f"fing('pointerup', 1, {cx - 60}, {cy + 200})"); await page.wait_for_timeout(150)
    check('two fingers at once: each digs (every finger plays)', await hat(page, cx + 90, cy + 120) < base - 3 and await hat(page, cx - 60, cy + 200) < base - 1.5)
    await page.screenshot(path=OUT + 'sand_finger.png')
    # the moon: glow in the dark; the grooves glow, the glow fades to a faint rest glow
    nb = await page.evaluate(f"(() => {{ const b = {S}.sa.L.btns.find(q => q.id === 'night'); return [b.x, b.y]; }})()")
    await tap(page, *nb); await page.wait_for_timeout(300)
    check('the moon button: glow in the dark on (remembered)', await page.evaluate(f"{S}.sa.night") and await page.evaluate("localStorage.getItem('grasp.sandNight')") == '1')
    await stroke(page, [(cx - 100, cy + 280), (cx + 100, cy + 280)], 14); await page.wait_for_timeout(100)
    g1 = await page.evaluate(f"{S}.glowAt({cx}, {cy + 280})"); col = await page.evaluate(f"{S}.colAt({cx}, {cy + 280})"); off = await page.evaluate(f"{S}.glowAt({cx}, {cy + 330})")
    px = await page.evaluate(f"(() => {{ const a = {S}.sa, k = (Math.floor(({cy} + 280 - a.L.box.iy) / a.csy) * a.GW + Math.floor(({cx} - a.L.box.ix) / a.cs)) * 4; return [a.img.data[k], a.img.data[k + 1], a.img.data[k + 2], a.lit[k], a.lit[k + 1], a.lit[k + 2]]; }})()")
    check('...a new groove glows (%.2f) in a neon colour, the untouched sand beside it does not (%.2f); the picture is brighter there' % (g1, off), g1 > 0.8 and max(col) > 0.6 and off < 0.05 and sum(px[:3]) > sum(px[3:]) + 150, [g1, col, off, px])
    await page.screenshot(path=OUT + 'sand_night.png')
    await page.evaluate(f"(() => {{ for (let i = 0; i < 60; i++) saGlowFrame(500); }})()"); g3 = await page.evaluate(f"{S}.glowAt({cx}, {cy + 280})")
    check('...the glow fades with time to a faint rest glow in the groove (%.2f after 30 s)' % g3, 0.03 < g3 < 0.3, g3)
    await tap(page, *nb); await page.wait_for_timeout(300)
    check('...the sun button: back to day', not await page.evaluate(f"{S}.sa.night") and await page.evaluate("localStorage.getItem('grasp.sandNight')") == '0')
    # the smoother: a bar sweeps it flat again
    sb = await page.evaluate(f"(() => {{ const b = {S}.sa.L.btns.find(q => q.id === 'smooth'); return [b.x, b.y]; }})()")
    await tap(page, *sb); await page.wait_for_timeout(350); mid = await page.evaluate(f"!!{S}.sa.sweep")
    await page.screenshot(path=OUT + 'sand_sweep.png'); await page.wait_for_timeout(900)
    check('the smooth button: a bar sweeps down the tray (under way after 0.35 s) and the sand is fresh again, no glow left', mid and await page.evaluate(flat) and await page.evaluate(f"{S}.sa.glow.every(v => v === 0)") and 'whoosh' in await snd(page))
    # Home and back: a fresh tray
    await stroke(page, [(cx - 60, cy), (cx + 60, cy)], 8)
    await page.tap('#pauseBtn'); home = await wait(page, "mode === 'none' && !$('start').hidden", 4000)
    await page.evaluate("__grasp.setGameMode('sand'); strikeStart('mouse')"); await wait(page, "gameMode === 'sand' && mode === 'mouse'", 8000); await page.wait_for_timeout(300)
    check('Home (one tap on the house in the corner) and back: a fresh tray', home and await page.evaluate(flat))
    # cheap: only the changed part is shaded; at night only what glows is redrawn
    await stroke(page, [(cx - 30, cy), (cx + 30, cy)], 6); cells = await page.evaluate(f"{S}.sa.lastCells || 0"); allc = await page.evaluate(f"{S}.sa.GW * {S}.sa.GH"); ms = await page.evaluate(f"{S}.sa.shadeMs")
    check('the shading is cheap: only the changed part is redrawn (%d of %d cells), %.1f ms' % (cells, allc, ms), 0 < cells < allc * 0.4 and ms < 25, [cells, allc, ms])
    await page.evaluate(f"{S}.night(true)"); await page.wait_for_timeout(300); await stroke(page, [(cx - 30, cy + 100), (cx + 30, cy + 100)], 6); await page.wait_for_timeout(100)
    gc = await page.evaluate(f"{S}.sa.glowCells || 0")
    check('...and at night only the glowing part is recomposed each frame (%d of %d cells)' % (gc, allc), 0 < gc < allc * 0.5, gc)
    await page.evaluate(f"{S}.night(false)")
    check('mechanics: no page errors', not errs, errs); await ctx.close()

async def layouts(b):
    for he, (w, h) in ((False, (320, 568)), (True, (390, 844)), (False, (844, 390)), (True, (1280, 800))):
        tag = ('HE' if he else 'EN') + ' %dx%d' % (w, h); ctx, page, errs = await sand_page(b, he, w, h)
        r = await page.evaluate(f"""(() => {{ const L = {S}.sa.L, B = L.box, bs = L.btns, pb = document.querySelector('.chrome').getBoundingClientRect();
          const inside = bs.every((b) => b.x - b.r >= 0 && b.x + b.r <= innerWidth && b.y - b.r >= 0);
          const above = bs.every((b) => b.y + b.r <= B.y + 2); const apart = Math.hypot(bs[0].x - bs[1].x, bs[0].y - bs[1].y) >= bs[0].r + bs[1].r + 8;
          const clearPill = bs.every((b) => b.x + b.r <= pb.left - 6 || b.x - b.r >= pb.right + 6);
          return {{ inside, above, apart, clearPill, d: Math.min(...bs.map((b) => b.r * 2)), bh: B.h, bottomGap: innerHeight - (B.y + B.h), under: B.y >= pb.bottom - 2, order: bs.map((b) => b.id).join() }}; }})()""")
        check(tag + ': no dead space: the two buttons (%d px) in the top row beside the pause pill (clear of it), the tray from under that row to %d px from the bottom' % (r['d'], r['bottomGap']),
              r['inside'] and r['above'] and r['apart'] and r['clearPill'] and r['d'] >= 50 and r['bh'] >= 150 and r['under'] and r['bottomGap'] <= 12, r)
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
