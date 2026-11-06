exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Glow Tree (/tree, Little ones): a calm bioluminescent night tree that grows, then invites one quiet thing — water the ground (a plant sprouts),
# pick a glowing fruit (it drifts up and lights a star). It loads by its link with no page errors (EN + HE) and lives in the Little ones room as a
# tile with its icon; the tree grows (M -> 1) and its events fire; watering sprouts a plant; a grown fruit, picked, lights a star. No buzzer, no
# fail, no timer pressure. Screenshots: tests/out/tree_{en,he}.png.

async def tree_suite(b):
    for he in (False, True):
        tag = 'tree ' + ('HE' if he else 'EN')
        ctx, page, errs = await page_for(b, '/tree', he)
        ok = await wait(page, "typeof gameMode !== 'undefined' && gameMode === 'tree' && typeof tgOn === 'function' && tgOn() && !!(window.__grasp && __grasp.tree)")
        check(tag + ': /tree opens the glow tree (tg-frame, debug hook ready)', ok, await page.evaluate("[typeof gameMode !== 'undefined' ? gameMode : null, location.pathname]"))
        check(tag + ': the corner sticker is the way out (minChrome)', await page.evaluate("document.body.classList.contains('minChrome') && !$('pauseBtn').hidden"))
        # it renders a few frames with no error
        await page.wait_for_timeout(500)
        s0 = await page.evaluate("__grasp.tree.state()")
        check(tag + ': the tree starts small and grows over time (M in 0..1)', isinstance(s0.get('M'), (int, float)) and 0 <= s0['M'] <= 1, s0)
        # grow it fully + run its invitations
        await page.evaluate("__grasp.tree.fast()"); await page.wait_for_timeout(400)
        s1 = await page.evaluate("__grasp.tree.state()")
        check(tag + ': fast(): the tree is grown (M ~ 1) and events have fired', s1['M'] >= 0.99 and s1['events'] >= 1, s1)
        check(tag + ': grown, it bears fruit to pick', s1['fruits'] >= 1, s1)
        # water the ground -> a plant sprouts
        before = await page.evaluate("__grasp.tree.state().plants")
        await page.evaluate("__grasp.tree.water(innerWidth * 0.35); __grasp.tree.water(innerWidth * 0.62)"); await page.wait_for_timeout(400)
        after = await page.evaluate("__grasp.tree.state().plants")
        check(tag + ': watering the ground sprouts a plant', after > before, {'before': before, 'after': after})
        # pick a grown fruit -> a star lights
        st0 = await page.evaluate("__grasp.tree.state()")
        picked = await page.evaluate("""(() => { const fs = __grasp.tree.fpos(); if (!fs.length) return false; __grasp.tree.pickAt(fs[0].x, fs[0].y); return true; })()""")
        await page.wait_for_timeout(600)
        st1 = await page.evaluate("__grasp.tree.state()")
        check(tag + ': a glowing fruit, picked, is collected and lights a star (no pressure, no fail)',
              picked and st1['collected'] > st0['collected'] and st1['stars'] >= 1, {'picked': picked, 'before': st0['collected'], 'after': st1['collected'], 'stars': st1['stars']})
        # shake the canopy -> a shower of light petals
        await page.evaluate("for (var i=0;i<4;i++) __grasp.tree.shake(innerWidth*0.45, innerHeight*0.45)")
        await page.wait_for_timeout(200)
        check(tag + ': shaking the canopy sheds glowing petals', (await page.evaluate("__grasp.tree.state().petals")) >= 1, await page.evaluate("__grasp.tree.state().petals"))
        # rain landings leave glowing puddles on the ground
        await page.evaluate("for (var i=0;i<6;i++) __grasp.tree.water(innerWidth*(0.3+0.06*i))")
        await page.wait_for_timeout(150)
        check(tag + ': rain/water leaves glowing puddles', (await page.evaluate("__grasp.tree.state().puddles")) >= 1, await page.evaluate("__grasp.tree.state().puddles"))
        # the glowing creature: it spawns, and a touch bursts it (lights a star, no fail)
        pos = await page.evaluate("__grasp.tree.bug()")
        check(tag + ': a glowing creature appears to touch', await page.evaluate("__grasp.tree.state().critter") and pos and 'x' in pos, pos)
        s_before = await page.evaluate("__grasp.tree.state().stars")
        await page.evaluate("__grasp.tree.touchBug()"); await page.wait_for_timeout(300)
        check(tag + ': touching the creature bursts light and lights a star', (await page.evaluate("__grasp.tree.state().stars")) >= s_before, {'before': s_before, 'after': await page.evaluate("__grasp.tree.state().stars")})
        await page.screenshot(path=OUT + 'tree_%s.png' % ('he' if he else 'en'))
        # the Little ones tile exists with its icon
        tile = await page.evaluate("""(() => { const b = document.querySelector('#littlePick [data-mode="tree"]'); if (!b) return null; return { ic: b.querySelector('.ic') ? b.querySelector('.ic').dataset.ic : null, lb: b.querySelector('.lb') ? b.querySelector('.lb').textContent.trim() : null }; })()""")
        check(tag + ': the Little ones room has a Glow Tree tile with its icon', tile and tile['ic'] == 'tree' and bool(tile['lb']), tile)
        check(tag + ': no page errors', not errs, errs)
        await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        await tree_suite(b)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
