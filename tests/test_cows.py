exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Cow Stampede in an Adventure stage (the owner, Oct 2026: "I didn't have any cows"): the guests counted a serve only when the ball came back off the
# corridor's far end; in a stage it always comes back off a wall, so the count stayed at 1 and no cow ever came. A perfect player (every ball hit
# when it is close) through stage 1 in the event's week (live): cows come, every 2-3 balls.

LOOP = """new Promise((res) => { const seen = [], t0 = performance.now(); let lastP = -1;
  const tick = () => { const B = strike.balls[0];
    if (B && B.guest && strike.pitches !== lastP) { seen.push(strike.pitches); lastP = strike.pitches; }
    if (B && B.dir === -1 && B.z < 140 && !strike.waiting) strikeHit(B, performance.now(), 'medium');
    if (strike.over || adv.phase !== 'play' || performance.now() - t0 > 60000) return res({ seen, pitches: strike.pitches, kinds: strike.guestKinds.slice(), phase: adv.phase });
    requestAnimationFrame(tick); };
  tick(); })"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        ctx, page, errs = await page_for(b, '/', False, init="window.__graspNoAutoFs = true; sessionStorage.setItem('grasp.testDate', '2026-10-27');")
        await page.wait_for_timeout(800); await page.evaluate("__grasp.event.force('cows'); __grasp.event.live(true)")
        await page.tap('#heroPlay'); await wait(page, "mode !== 'none' && adv.on && adv.phase === 'play'", 8000); await page.evaluate("strike.autoServe = true")
        r = await page.evaluate(LOOP)
        check('Cow Stampede, Adventure stage 1, every ball hit: cows come (at least 3, every 2-3 balls; was none)', len(r['seen']) >= 3 and set(r['kinds']) == {'cow'} and all(1 < b2 - a <= 4 for a, b2 in zip(r['seen'], r['seen'][1:])), r)
        check('no page errors', not errs, errs)
        await ctx.close(); await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
