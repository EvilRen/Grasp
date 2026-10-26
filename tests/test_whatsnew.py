exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# The version, the copyright line and What's New (the owner, Oct 2026: "my copyright and what's new with each version, like in all my other
# games"; copied from Greedy Paws): "(c) <year> Benny Ankri · v<APP_VERSION>" faint at the bottom of the start screen; after an update, once a
# version, a sheet with the release's notes. A first visit: none. The notes are gated: a feature release (x.Y.0) cannot ship with the last one's.
# Screenshots: tests/out/whatsnew_*.png

WN = "window.__graspWhatsNew = true;"
SEED = "if (!sessionStorage.getItem('wnSeeded')) { sessionStorage.setItem('wnSeeded', '1'); %s }"
ST = "({ open: !$('wnSheet').hidden, n: $('wnList').children.length, v: $('wnV').textContent, ver: localStorage.getItem('grasp.ver'), seen: localStorage.getItem('grasp.wn'), log: __grasp.wn.wn.log.slice() })"

async def notes(b):
    ctx, page, errs = await page_for(b, '/', True, init="window.__graspNoAutoFs = true;")
    cur = await page.evaluate("APP_VERSION"); minor = lambda v: '.'.join(v.split('.')[:2])
    he, en = await page.evaluate("I18N.he.wnFor"), await page.evaluate("I18N.en.wnFor")
    check('the What\'s New notes describe this release (notes for %s, the app is %s)' % (he, cur), minor(he) == minor(cur))
    check('both languages describe the same release', he == en, (he, en))
    nh, ne = await page.evaluate("I18N.he.wn.length"), await page.evaluate("I18N.en.wn.length")
    check('the notes are not empty, and as many in both languages', nh > 0 and nh == ne, (nh, ne))
    check('the version is x.y.z', bool(re.match(r'^\d+\.\d+\.\d+$', cur)), cur)
    await ctx.close()

async def foot(b, he):
    tag = 'HE' if he else 'EN'
    ctx, page, errs = await page_for(b, '/', he, init="window.__graspNoAutoFs = true;"); await page.wait_for_timeout(1200)
    f = await page.evaluate("""(() => { const e = $('menuFoot'), r = e.getBoundingClientRect(), s = getComputedStyle(e);
      const dl = [...document.querySelectorAll('#tabBar .mbDockB:not([hidden]) .dl')].map((q) => q.getBoundingClientRect()).filter((q) => q.width);
      return { text: e.textContent.trim(), dir: s.direction, op: +s.opacity, top: r.top, bot: r.bottom, h: innerHeight, labelsBot: Math.max(...dl.map((q) => q.bottom)), pe: s.pointerEvents }; })()""")
    year = await page.evaluate("new Date().getFullYear()"); ver = await page.evaluate("APP_VERSION")
    check(tag + ': the copyright line: "© %d Benny Ankri · v%s"' % (year, ver), f['text'] == '© %d Benny Ankri · v%s' % (year, ver), f['text'])
    check(tag + ': it reads left to right, faint, never takes a tap', f['dir'] == 'ltr' and 0.2 < f['op'] < 0.8 and f['pe'] == 'none', f)
    check(tag + ': on the screen, under the dock\'s labels (no overlap)', f['bot'] <= f['h'] and f['top'] >= f['labelsBot'] - 1, f)
    await page.screenshot(path=OUT + 'whatsnew_foot_%s.png' % tag.lower())
    await page.evaluate(START_MOUSE); await wait(page, "mode !== 'none'", 6000); await page.wait_for_timeout(300)
    check(tag + ': in a game the line is gone', await page.evaluate("!$('menuFoot').checkVisibility()"))
    check(tag + ': foot: no page errors', not errs, errs); await ctx.close()

async def flow(b, he):
    tag = 'HE' if he else 'EN'
    # a first visit: no sheet, the version remembered
    ctx, page, errs = await page_for(b, '/', he, init=WN + "window.__graspNoAutoFs = true;"); await page.wait_for_timeout(1500)
    s = await page.evaluate(ST)
    check(tag + ': a first visit: no What\'s New (the version is remembered)', not s['open'] and s['ver'] == await page.evaluate("APP_VERSION"), s)
    await ctx.close()
    # an update since the last visit: the sheet once
    ctx, page, errs = await page_for(b, '/', he, init=WN + "window.__graspNoAutoFs = true;" + SEED % "localStorage.setItem('grasp.ver', '0.9.0');")
    ok = await wait(page, "!$('wnSheet').hidden", 5000); s = await page.evaluate(ST)
    check(tag + ': after an update: What\'s New opens with the notes and the version', ok and s['n'] == await page.evaluate("wnNotes().length") and s['v'] == 'v' + await page.evaluate("APP_VERSION"), s)
    t = await page.evaluate("$('wnT').textContent")
    check(tag + ': its title', t == ('מה חדש?' if he else 'What’s new?'), t)
    fit = await page.evaluate("(() => { const r = document.querySelector('#wnSheet .sheet').getBoundingClientRect(), b = $('wnBtn').getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight && b.height >= 44 && b.width >= 44; })()")
    check(tag + ': the sheet fits the phone; its button is a big target', fit)
    await page.screenshot(path=OUT + 'whatsnew_sheet_%s.png' % tag.lower())
    await page.tap('#wnBtn'); await page.wait_for_timeout(300)
    check(tag + ': its button closes it', not (await page.evaluate(ST))['open'])
    await page.reload(); await page.wait_for_function("typeof engine !== 'undefined' && !!engine", timeout=15000); await page.wait_for_timeout(1500)
    check(tag + ': once a version: not again after a reload', not (await page.evaluate(ST))['open'], await page.evaluate(ST))
    check(tag + ': flow: no page errors', not errs, errs); await ctx.close()
    # a player from before the versions (a stored profile, no version): their first update shows it
    ctx, page, errs = await page_for(b, '/', he, init=WN + "window.__graspNoAutoFs = true;" + SEED % "localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, coins: 12 }));")
    ok = await wait(page, "!$('wnSheet').hidden", 5000)
    check(tag + ': an old player (a profile, no version yet): What\'s New shows', ok, await page.evaluate(ST))
    await page.keyboard.press('Escape'); await page.wait_for_timeout(200)
    check(tag + ': Escape closes it', not (await page.evaluate(ST))['open'])
    await ctx.close()
    # a direct link to a game: not over the game; it waits for the start screen
    ctx, page, errs = await page_for(b, '/animals', he, init=WN + "window.__graspNoAutoFs = true;" + SEED % "localStorage.setItem('grasp.ver', '0.9.0');")
    await wait(page, "gameMode === 'animals' && mode !== 'none'", 8000); await page.wait_for_timeout(800)
    check(tag + ': a game\'s link: no sheet over the game', not (await page.evaluate(ST))['open'])
    await page.evaluate("goHome()"); ok = await wait(page, "!$('wnSheet').hidden", 4000)
    check(tag + ': Home: then it shows', ok, await page.evaluate(ST))
    check(tag + ': link: no page errors', not errs, errs); await ctx.close()

async def suites(b):  # the other suites never see it (no opt-in): an old version stored does not open it
    ctx, page, errs = await page_for(b, '/', False, init="window.__graspNoAutoFs = true;" + SEED % "localStorage.setItem('grasp.ver', '0.9.0');"); await page.wait_for_timeout(1500)
    check('without the opt-in (the other suites): no What\'s New', not (await page.evaluate(ST))['open'])
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        await notes(b)
        for he in (True, False): await foot(b, he); await flow(b, he)
        await suites(b)
        await b.close()
    print('FAILURES:', check.fails)
import re
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
