exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Sand Lab's 500 generated challenges (10 worlds of 50; easy / normal / hard): every level is played by a bot with the level's own winning
# moves (pwBot: the real rules, no drawing) and must be won within 60 s of game time and within its bucket. LEVELS=a:b, DIFFS=easy,normal,hard.
import os
PWH = '__grasp.pw'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx, page, errs = await page_for(b, '/powder', True, init="window.__graspNoAutoFs = true;"); await wait(page, f"!!{PWH}.pw.g", 8000)
        n0, tot = await page.evaluate(f"[{PWH}.PW_N0, {PWH}.PW_TOTAL]")
        a, z = (os.environ.get('LEVELS') or '%d:%d' % (n0, tot)).split(':'); a, z = int(a), int(z)
        fails = []; only = [int(x) for x in (os.environ.get('ONLY') or '').split(',') if x]
        for diff in (os.environ.get('DIFFS') or 'normal').split(','):
            for k in (only or range(a, z)):
                r = await page.evaluate(f"{PWH}.bot({k}, '{diff}')")
                if not r['won']: fails.append((diff, r)); print('FAILED', diff, r, flush=True)
        check('every generated level (%d..%d) is won by its own moves' % (a, z - 1), not fails, fails[:12])
        check('levels: no page errors', not errs, errs); await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
