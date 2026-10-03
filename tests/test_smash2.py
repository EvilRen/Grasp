exec(open('tests/test_smash.py').read().split('async def main')[0])
# Smash stages and the rest: the stage plans (scene, clock, star times), a stage start (banner with the 3-star line, HUD = meter + clock + stars
# in reach), the clock (pauses with the sheet, 'Hurry!' at 10 s), the clear card (stars by time left, the line on how to get 3, coins: a first
# clear 3 + stars, a replay only the stars it adds; Next / Play again / Map) and the fail card (Try again / Map), progress and stars saved in the
# profile (validated on load), the map after play, the voice lines; screenshots of every scene before / mid-destruction, the map and the cards
# on a phone (EN / HE) and a desktop: tests/out/smash2_*.png.
def prof(smash):
    return "localStorage.setItem('grasp.profile', " + json.dumps(json.dumps({'v': 1, 'xpv': 2, 'smash': smash})) + ");"
async def card(page):  # a stage's card is up and its buttons take taps
    await page.wait_for_function(S + ".over && " + S + ".ui.buttons && performance.now() - " + S + ".overAt > 700", timeout=8000)
    return await page.evaluate(S + ".ui.buttons")
async def press(page, bt, key, tap=False):
    r = bt[key]; x, y = r['x'] + r['w'] / 2, r['y'] + r['h'] / 2
    if tap: await page.tap('#stage', position={'x': x, 'y': y})
    else: await page.mouse.click(x, y)
async def mid(page):  # a few real swipes and punches across the scene, then a moment for the debris to fly
    for f in (0.3, 0.45, 0.6, 0.72, 0.86):
        await page.evaluate(f"{SM}.sweep(innerWidth * 0.05, innerHeight * {f}, innerWidth * 0.95, innerHeight * {f + 0.03}, 0.9)"); await page.wait_for_timeout(60)
    if await page.evaluate(SM + ".meter") < 0.3: await page.evaluate(SM + ".breakTo(0.35)")
    await page.wait_for_timeout(350)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
        # ---------------- the stage plans ----------------
        ctx, page, errs = await fresh(b)
        pl = await page.evaluate(f"Array.from({{length: 20}}, (_, i) => {SM}.plan(i + 1))")
        scenes = [q['scene'] for q in pl]
        check('20 stages: 4 per scene in the map\'s order (wall, room, city, blocks, food), each scene\'s layout fuller stage by stage', scenes == [s for s in ['wall', 'room', 'city', 'blocks', 'food'] for _ in range(4)] and [q['v'] for q in pl[:4]] == [1, 2, 3, 4], scenes)
        check('the clock: shorter stage by stage within a scene; ★★★ = 45% of it left, ★★ = 20%', all(pl[i]['time'] > pl[i + 1]['time'] for i in range(19) if i % 4 != 3) and all(q['star3'] == int(q['time'] * 0.45 + 0.5) and q['star2'] == int(q['time'] * 0.2 + 0.5) for q in pl) and pl[0]['time'] == 120, [(q['time'], q['star3'], q['star2']) for q in pl[:8]])
        sf = await page.evaluate(f"(() => {{ const P = {SM}.plan(1); return [P.star3, P.star3 - 1, P.star2, P.star2 - 1, 0].map(s => {SM}.starsFor(P, s)); }})()")
        check('stars by the time left at the clear: >= the ★★★ time: 3; >= the ★★ time: 2; else 1 (a clear never gets 0)', sf == [3, 2, 2, 1, 1], sf)
        check('the economy: a Smash stage pays a first clear 3 + its stars, a replay the stars it adds; free play 6 a scene', await page.evaluate("ECONOMY.smashStage.first === 3 && ECONOMY.smashStage.star === 1 && ECONOMY.smash.scene === 6"))
        ln = await page.evaluate("__grasp.grippy.lines")
        bad = [e + ':' + l for e in ['smashClear', 'smashScene', 'smashHurry'] for l in ('en', 'he') if len(set(ln[l][e])) < 3 or any(not (1 <= len(x.split()) <= 3) or len(x) > 16 for x in ln[l][e]) or (l == 'he' and not all(re.search('[֐-׿]', x) for x in ln[l][e]))]
        check('voice lines for Smash\'s big moments (scene smashed, a new scene, hurry), 3 short lines each in EN and HE', not bad, bad)
        # ---------------- a stage from the map ----------------
        await page.click('.modes button[data-mode=smash]'); await page.wait_for_function(SM + ".mapOpen", timeout=5000)
        await page.screenshot(path='tests/out/smash2_map_desktop_en.png')
        await page.click('#smList .smNode.cur'); await page.wait_for_function(f"mode === 'mouse' && {S}.run === 'stage' && {S}.n === 1 && {SM}.objs.length > 0", timeout=15000)
        await page.wait_for_timeout(400)
        st = await page.evaluate(f"({{ scene: {S}.scene, left: {S}.endAt - performance.now(), banner: {S}.ui.bannerBox, hud: {S}.ui.hud, stars: {S}.ui.starsBox, timer: {S}.ui.timerBox, path: location.pathname, spoken: __spoken.map(s => s.text) }})")
        check('stage 1 from the map: the brick wall, a 2:00 clock running, the path /smash', st['scene'] == 'wall' and 117000 < st['left'] <= 120000 and st['path'] == '/smash', st)
        check('the start banner: "Stage 1", the scene and its clock, and the ★★★ line (finish with 54 s left)', st['banner'] and st['banner']['title'] == 'Stage 1' and 'The Brick Wall' in st['banner']['sub'] and st['banner']['line'] == '★★★ = finish with 54 s left', st['banner'])
        check('the HUD in a stage: the meter, the clock and the stars still in reach (3), one slim pill', st['hud']['parts'] == ['meter', 'timer', 'stars'] and st['stars']['n'] == 3 and st['timer']['text'] in ('2:00', '1:59') and st['hud']['h'] <= 32, st)
        check('the voice says go at the stage start', len(st['spoken']) >= 1 and st['spoken'][-1] in ln['en']['start'], st['spoken'])
        await page.screenshot(path='tests/out/smash2_stage_banner_desktop_en.png')
        l0 = await page.evaluate(f"{S}.endAt - performance.now()"); await page.wait_for_timeout(600); l1 = await page.evaluate(f"{S}.endAt - performance.now()")
        check('the clock counts down', 450 < l0 - l1 < 2000, [l0, l1])
        await page.click('#pauseBtn'); await page.wait_for_function("menu.open", timeout=3000)
        l2 = await page.evaluate(f"{S}.endAt - performance.now()"); await page.wait_for_timeout(700); l3 = await page.evaluate(f"{S}.endAt - performance.now()")
        check('the pause sheet stops the clock', abs(l2 - l3) < 100, [l2, l3])
        await page.click('#resumeBtn'); await page.wait_for_function("!menu.open && !__grasp.pause.on", timeout=3000)
        await page.evaluate(f"{S}.endAt = performance.now() + 50000"); await page.wait_for_function(f"{S}.ui.starsBox && {S}.ui.starsBox.n === 2", timeout=3000)
        check('under the ★★★ time the HUD shows 2 stars in reach', True)
        # a clear with 2 stars (40 s left)
        c0 = await page.evaluate("__grasp.profile.coins"); await page.evaluate("__grasp.grippy.cool(); __grasp.smash.endAt = performance.now() + 40500")
        await page.evaluate(SM + ".breakTo(0.95)"); bt = await card(page)
        r = await page.evaluate(f"({{ r: {S}.result, labels: {S}.ui.labels, hint: {S}.ui.starHint, stars: {S}.ui.stars, prof: __grasp.profile.smash, coins: __grasp.profile.coins, said: __grasp.grippy.last && __grasp.grippy.last.event }})")
        check('cleared with 40 s left: 2 stars, a first clear pays 3 + 2 coins', r['r']['clear'] and r['r']['stars'] == 2 and r['r']['first'] and r['r']['coins'] == 5 and r['coins'] - c0 == 5, [c0, r])
        check('the clear card: Next / Play again / Map (success says "Play again")', set(bt) == {'next', 'retry', 'map'} and r['labels'] == {'next': 'Next', 'retry': 'Play again', 'map': 'Map'} and bt['next']['w'] > bt['retry']['w'], r['labels'])
        await page.wait_for_function(f"{S}.ui.starHint && {S}.ui.starHint.a >= 1", timeout=4000)
        hint = await page.evaluate(f"{S}.ui.starHint.text")
        check('the line under the stars says how to get 3 ("40 s left. Finish with 54 s left for ★★★")', hint in ('40 s left. Finish with 54 s left for ★★★', '41 s left. Finish with 54 s left for ★★★'), hint)
        check('saved: stage 1 has 2 stars, stage 2 is open; the voice cheers', r['prof'] == {'stars': {'1': 2}, 'unlocked': 2} and r['said'] == 'advClear', r)
        await page.screenshot(path='tests/out/smash2_card_clear_desktop_en.png')
        await press(page, bt, 'retry'); await page.wait_for_function(f"!{S}.over && {S}.n === 1 && {S}.phase === 'play'", timeout=5000)
        check('Play again: the same stage afresh (a full clock, the meter at 0)', await page.evaluate(f"{S}.endAt - performance.now()") > 117000 and await page.evaluate(SM + ".meter") < 0.02)
        c1 = await page.evaluate("__grasp.profile.coins"); await page.evaluate("__grasp.grippy.cool()"); await page.evaluate(SM + ".breakTo(0.95)"); bt = await card(page)
        r = await page.evaluate(f"({{ r: {S}.result, prof: __grasp.profile.smash, coins: __grasp.profile.coins, said: __grasp.grippy.last && __grasp.grippy.last.event }})")
        check('a fast replay: 3 stars; the replay pays only the star it adds (1 coin); "Perfect" from the voice', r['r']['stars'] == 3 and not r['r']['first'] and r['r']['coins'] == 1 and r['coins'] - c1 == 1 and r['prof']['stars'] == {'1': 3} and r['said'] == 'advPerfect', [c1, r])
        await page.wait_for_function(f"{S}.ui.starHint && {S}.ui.starHint.a >= 1", timeout=4000)
        check('3 stars: the line says how fast it was', (await page.evaluate(f"{S}.ui.starHint.text")).startswith('Super fast'))
        await press(page, bt, 'next'); await page.wait_for_function(f"!{S}.over && {S}.n === 2", timeout=5000)
        check('Next: stage 2 at once (the same scene, fuller)', await page.evaluate(f"{S}.scene === 'wall' && {S}.variant === 2"))
        # the last seconds: 'Hurry!' once; then the clock runs out: the fail card
        await page.evaluate("__grasp.grippy.cool(); __grasp.smash.endAt = performance.now() + 9500"); await page.wait_for_function("__grasp.grippy.last && __grasp.grippy.last.event === 'smashHurry'", timeout=4000)
        check('10 s left: the voice says hurry (once), the clock turns red', await page.evaluate(f"{S}.hurry && {S}.ui.timerBox.left <= 10"))
        await page.evaluate("__grasp.grippy.cool(); __grasp.smash.endAt = performance.now() + 300"); bt = await card(page)
        r = await page.evaluate(f"({{ r: {S}.result, labels: {S}.ui.labels, fail: {S}.ui.failBar, said: __grasp.grippy.last.event, prof: __grasp.profile.smash }})")
        check('the clock ran out: the fail card ("So close!", how far it got) with Try again / Map, no coins, nothing saved for stage 2', not r['r']['clear'] and r['labels'] == {'retry': 'Try again', 'map': 'Map'} and set(bt) == {'retry', 'map'} and r['fail'] is not None and r['r']['coins'] == 0 and '2' not in r['prof']['stars'] and r['said'] == 'advFail', r)
        await page.screenshot(path='tests/out/smash2_card_fail_desktop_en.png')
        await page.mouse.click(300, 120); await page.wait_for_function(f"!{S}.over && {S}.n === 2 && {S}.phase === 'play'", timeout=5000)
        check('a tap away from the card buttons: try again (as Strike\'s wave)', await page.evaluate(f"{S}.endAt - performance.now()") > 90000)
        await page.evaluate(f"{S}.endAt = performance.now() + 300"); bt = await card(page)
        await press(page, bt, 'map'); await page.wait_for_function(SM + ".mapOpen", timeout=4000)
        mp = await page.evaluate("({ s1: document.querySelector('#smList .smNode[data-n=\"1\"]').dataset.stars, cur: document.querySelector('#smList .smNode.cur').dataset.n, locked3: document.querySelector('#smList .smNode[data-n=\"3\"]').classList.contains('locked'), total: $('smStarTotal').querySelector('b').textContent, path: location.pathname })")
        check('Map from the card: stage 1 shows its 3 stars, stage 2 is the current one, stage 3 still locked, 3 stars in all', mp['s1'] == '3' and mp['cur'] == '2' and mp['locked3'] and mp['total'] == '3' and mp['path'] == '/smash', mp)
        await page.click('#smList .smNode.cur'); await page.wait_for_function(f"!{SM}.mapOpen && !{S}.over && {S}.n === 2", timeout=5000)
        check('a stop on the map over a game starts it at once', await page.evaluate("mode === 'mouse' && __grasp.smash.phase === 'play'"))
        await page.evaluate(f"(() => {{ __grasp.profile.smash.unlocked = 20; }})()"); await page.evaluate(SM + ".stage(20)"); await page.wait_for_function(f"{S}.n === 20 && {S}.scene === 'food'", timeout=5000)
        await page.evaluate(SM + ".breakTo(0.95)"); bt = await card(page)
        check('the last stage\'s clear: its main button goes to the map', (await page.evaluate(f"{S}.ui.labels.next")) == 'Map')
        await press(page, bt, 'next'); await page.wait_for_function(SM + ".mapOpen", timeout=4000)
        await page.click('#smBack'); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=4000)
        check('Back on the map over a game: home', await page.evaluate("!__grasp.sm.mapOpen"))
        await page.evaluate("syncBests()")
        check('the Smash tile shows the stars won in its stages', await page.evaluate("document.querySelector('.modes button[data-mode=smash] .best').textContent") == '★ ' + str(await page.evaluate(SM + ".total")))
        await page.reload(); await page.wait_for_timeout(600)
        check('progress and stars survive a reload', await page.evaluate("__grasp.profile.smash.stars['1'] === 3 && __grasp.profile.smash.stars['20'] >= 1 && __grasp.profile.smash.unlocked === 20"))
        check('stages desktop: no page errors', not errs, errs); await ctx.close()

        # ---------------- the profile: Smash progress validated on load ----------------
        for data, want, what in [({'stars': {'1': 3, '2': 9, 'x': 2, '30': 1, '3': 2.5, '4': 1, '5': '2'}, 'unlocked': 99}, {'stars': {'1': 3, '4': 1}, 'unlocked': 20}, 'bad stars dropped, the frontier clamped to 20'),
                                 ({'stars': {'6': 2}, 'unlocked': -5}, {'stars': {'6': 2}, 'unlocked': 7}, 'a negative frontier: at least past the last starred stage'),
                                 ('junk', {'stars': {}, 'unlocked': 1}, 'not an object: the defaults')]:
            ctx, page, errs = await fresh(b, init=prof(data))
            got = await page.evaluate("__grasp.profile.smash")
            check('profile.smash validated on load: ' + what, got == want, [data, got])
            await ctx.close()

        # ---------------- free play + screenshots: phone EN / HE, desktop EN; stage cards on the phone ----------------
        for mobile, he in [(True, False), (True, True), (False, False)]:
            tag = ('phone_' if mobile else 'desktop_') + ('he' if he else 'en')
            ctx, page, errs = await fresh(b, mobile=mobile, he=he, init=prof({'stars': {'1': 3, '2': 2, '3': 1}, 'unlocked': 4}))
            await (page.tap if mobile else page.click)('.modes button[data-mode=smash]'); await page.wait_for_function(SM + ".mapOpen", timeout=5000)
            await page.wait_for_timeout(200)
            mp = await page.evaluate("(() => { const f = $('smashFree').getBoundingClientRect(), n = [...document.querySelectorAll('#smList .smNode')].map(b => b.getBoundingClientRect()); return { title: $('smTitle').textContent, free: $('smashFree').textContent, in: f.left >= 0 && f.right <= innerWidth, nodes: n.every(r => r.left >= 0 && r.right <= innerWidth && r.width >= 44 && r.height >= 44), scene: document.querySelector('#smList .smScene b').textContent, dir: document.documentElement.dir, stars: document.querySelector('#smList .smScene small').textContent }; })()")
            check(tag + ': the map in the UI language, everything on screen, big tap targets', mp['in'] and mp['nodes'] and ((mp['title'] == 'ניפוץ' and 'משחק חופשי' in mp['free'] and mp['scene'] == 'קיר הלבנים' and mp['dir'] == 'rtl') if he else (mp['title'] == 'Smash' and 'Free play' in mp['free'] and mp['scene'] == 'The Brick Wall')) and mp['stars'] == '★ 6/12', mp)
            await page.screenshot(path=f'tests/out/smash2_map_{tag}.png')
            await (page.tap if mobile else page.click)('#smashFree'); await page.wait_for_function(f"mode === 'mouse' && {S}.run === 'free' && {SM}.objs.length > 0", timeout=15000)
            for sc in ['wall', 'room', 'city', 'blocks', 'food']:
                await page.evaluate(f"{SM}.build('{sc}', 2)"); await page.wait_for_timeout(1100)
                await page.screenshot(path=f'tests/out/smash2_{sc}_{tag}.png')
                await mid(page); await page.screenshot(path=f'tests/out/smash2_{sc}_{tag}_mid.png')
                check(f'{tag} {sc}: mid-destruction (meter up, debris flying, within the cap)', 0.2 < await page.evaluate(SM + ".meter") and 0 < await page.evaluate(SM + ".pieces") <= await page.evaluate(SM + ".cap") * 1.25)
            if mobile:
                await page.evaluate(SM + ".stage(4)"); await page.wait_for_function(f"{S}.n === 4 && {S}.phase === 'play'", timeout=5000); await page.wait_for_timeout(500)
                await page.screenshot(path=f'tests/out/smash2_stage_banner_{tag}.png')
                bn = await page.evaluate(f"{S}.ui.bannerBox")
                check(tag + ': the stage banner in the UI language', bn and (bn['title'] == 'שלב 4' and 'לסיים' in bn['line'] if he else bn['title'] == 'Stage 4' and 'finish with' in bn['line']), bn)
                await page.evaluate(f"{S}.endAt = performance.now() + 30000; {SM}.breakTo(0.95)"); bt = await card(page); await page.wait_for_timeout(1200)
                lb = await page.evaluate(f"{S}.ui.labels")
                check(tag + ': clear card labels' + (' (HE: הבא / לשחק שוב / מפה; Play again on the right)' if he else ''), lb == ({'next': 'הבא', 'retry': 'לשחק שוב', 'map': 'מפה'} if he else {'next': 'Next', 'retry': 'Play again', 'map': 'Map'}) and ((bt['retry']['x'] > bt['map']['x']) == he) and all(q['x'] >= 8 and q['x'] + q['w'] <= 352 and q['h'] >= 44 for q in bt.values()), [lb, bt])
                await page.screenshot(path=f'tests/out/smash2_card_clear_{tag}.png')
                await press(page, bt, 'next', tap=True); await page.wait_for_function(f"!{S}.over && {S}.n === 5 && {S}.scene === 'room'", timeout=5000)
                check(tag + ': tap Next: stage 5, the room', True)
                await page.evaluate(f"{S}.endAt = performance.now() + 300"); bt = await card(page); await page.wait_for_timeout(300)
                lb = await page.evaluate(f"{S}.ui.labels")
                check(tag + ': fail card labels: ' + ('שוב / מפה' if he else 'Try again / Map'), lb == ({'retry': 'שוב', 'map': 'מפה'} if he else {'retry': 'Try again', 'map': 'Map'}), lb)
                await page.screenshot(path=f'tests/out/smash2_card_fail_{tag}.png')
                await press(page, bt, 'retry', tap=True); await page.wait_for_function(f"!{S}.over && {S}.n === 5", timeout=5000)
                check(tag + ': tap Try again: the stage afresh', await page.evaluate(f"{S}.phase === 'play' && {SM}.meter < 0.02"))
            check(tag + ': no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
