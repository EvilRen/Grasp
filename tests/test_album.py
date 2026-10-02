exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# The sticker album (a sticker for each Adventure stage's first 3-star clear; 8 to a world's page; a full page pays ECONOMY.album.page once; the
# stickers of a player from before the album; the peel onto the clear card with its sound; the album overlay on the map: header button, tabs,
# slots in colour / silhouettes with the stage, the page bonus with confetti; phone / desktop, EN / HE; the profile's validation), the world music
# (a loop per Adventure world on a lookahead timer: starts in a stage, stops on pause / hand lost / mute / the stage's end / the map, ducks
# under the banners, never in Endless) and the round-over card's title clear of the coin / XP pills. Hooks: __grasp.album, __grasp.music.
# Timing-independent: state is polled.
AL = "__grasp.album"; MU = "__grasp.music"; A = "__grasp.adventure"; S = "__grasp.strike"; P = "__grasp.profile"
TOASTS = "__grasp.toasts.map(t => t.text)"
SFX_JS = "(() => { if (window.__sfx) return; window.__sfx = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); o(k, a); }; })()"
OUT = 'tests/out/album_'

def rects_overlap(a, b, pad=0):
    return a['l'] < b['r'] - pad and b['l'] < a['r'] - pad and a['t'] < b['b'] - pad and b['t'] < a['b'] - pad
def box(r):  # {x, y, w, h} -> {l, r, t, b}
    return {'l': r['x'], 'r': r['x'] + r['w'], 't': r['y'], 'b': r['y'] + r['h']}

async def fresh(b, mobile=False, he=False, init='', date='2026-10-02'):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + "localStorage.setItem('lang','" + ('he' if he else 'en') + "');" + "sessionStorage.setItem('grasp.testDate','" + date + "');" + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_function("window.__grasp && __grasp.album", timeout=8000); await page.wait_for_timeout(300)
    await page.evaluate(SFX_JS)
    return ctx, page, errs

def prof(**kw):
    d = dict(v=1, coins=0, xp=0); d.update(kw)
    return "if (!sessionStorage.getItem('__seeded')) { localStorage.setItem('grasp.profile', " + json.dumps(json.dumps(d)) + "); sessionStorage.setItem('__seeded', '1'); }"
def stars(upto, v=3, extra=None):
    d = {str(n): v for n in range(1, upto + 1)}
    if extra: d.update({str(k): x for k, x in extra.items()})
    return d

async def tap(page, mobile, sel):
    if mobile: await page.tap(sel)
    else: await page.click(sel)

async def stage_play(page, n):
    await page.evaluate(f"{A}.start({n}, 'mouse')")
    await page.wait_for_function(f"{A}.on && {A}.stage === {n} && {A}.phase === 'play' && !{S}.over", timeout=8000)
async def stage_clear(page, n, lost=0):  # play stage n and clear it at once; wait for its card
    await stage_play(page, n)
    r = await page.evaluate(f"{A}.finishTest({lost})")
    await page.wait_for_function(f"{S}.over && {A}.phase === 'card' && {S}.ui.buttons && {S}.ui.buttons.next", timeout=12000)
    return r

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--autoplay-policy=no-user-gesture-required'])

        # ---- the award rules: only a 3-star clear, only the first time; the peel onto the card with its sound ----
        ctx, page, errs = await fresh(b)
        check('a new player: no stickers, 40 in the list (8 a world), ECONOMY.album.page = 30', await page.evaluate(AL + ".got") == [] and len(await page.evaluate(AL + ".list")) == 40 and len(set(await page.evaluate(AL + ".list"))) == 40 and await page.evaluate(AL + ".economy.page") == 30)
        r = await stage_clear(page, 1, lost=1)
        check('stage 1 cleared with 2 stars: no sticker', r['stars'] == 2 and not r['sticker'] and await page.evaluate(AL + ".got") == [] and await page.evaluate(f"{S}.ui.advSticker") is None, r)
        c0 = await page.evaluate(P + ".coins")
        r = await stage_clear(page, 1, lost=0)
        check('...replayed with 3 stars: sticker 1 (new), no page yet', r['stars'] == 3 and r['sticker'] == 1 and r['page'] is None and await page.evaluate(AL + ".got") == [1] and await page.evaluate(AL + ".fresh") == [1], r)
        check('...the replay pays only the star it adds (the sticker is not coins)', await page.evaluate(P + ".coins") == c0 + 1)
        await page.wait_for_function(f"{S}.ui.advSticker && {S}.ui.advSticker.landed", timeout=8000)
        st = await page.evaluate(f"(() => {{ const u = {S}.ui; return {{ s: u.advSticker, card: u.card, next: u.buttons.next, pay: u.advPay, sfx: __sfx.slice() }}; }})()")
        sb, cd = box(st['s']), box(st['card'])
        check('the sticker lands on the card (after the stars) with the peel sound; inside the card, clear of the buttons and the pay pills',
              st['s']['n'] == 1 and 'peel' in st['sfx'] and sb['l'] >= cd['l'] and sb['r'] <= cd['r'] and sb['b'] <= box(st['next'])['t'] and not any(rects_overlap(sb, box(q)) for q in st['pay']) and st['sfx'].index('peel') > st['sfx'].index('xylo'), st)
        await page.screenshot(path=OUT + 'card_desktop_en.png')
        r = await stage_clear(page, 1, lost=0)
        check('3 stars again: no second sticker, no peel on the card', not r['sticker'] and await page.evaluate(AL + ".got") == [1] and await page.evaluate(f"{S}.ui.advSticker") is None, r)
        check('albumAward refuses a sticker already got / a bad stage', await page.evaluate(AL + ".award(1)") is None and await page.evaluate(AL + ".award(0)") is None and await page.evaluate(AL + ".award(41)") is None)
        await page.reload(); await page.wait_for_function("window.__grasp && __grasp.album", timeout=8000)
        check('the sticker survives a reload (still new)', await page.evaluate(AL + ".got") == [1] and await page.evaluate(AL + ".fresh") == [1])
        check('no page errors (award)', not errs, errs); await ctx.close()

        # ---- the page bonus on the card: the 8th sticker of world 1 (the boss stage) fills the page ----
        for mobile, he in ((True, False), (True, True)):
            tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en'); lt = 'he' if he else 'en'
            ctx, page, errs = await fresh(b, mobile, he, prof(adv={'stars': stars(7), 'unlocked': 8}))
            check(tag + ': a player from before the album: a sticker for each 3-star stage already, new, no page paid', await page.evaluate(AL + ".got") == list(range(1, 8)) and await page.evaluate(AL + ".fresh") == list(range(1, 8)) and await page.evaluate(AL + ".pages") == [] and await page.evaluate(P + ".coins") == 0)
            r = await stage_clear(page, 8, lost=0)
            check(tag + ': the boss stage with 3 stars: sticker 8, the page full: +30 coins once, on top of the clear', r['sticker'] == 8 and r['page'] == {'w': 1, 'coins': 30} and await page.evaluate(AL + ".pages") == [1] and await page.evaluate(P + ".coins") == r['coins'] + 30, [r, await page.evaluate(P + ".coins")])
            await page.wait_for_function(f"{S}.ui.advSticker && {S}.ui.advSticker.landed && __sfx.includes('fanfare')", timeout=8000)
            st = await page.evaluate(f"(() => {{ const u = {S}.ui; return {{ s: u.advSticker, card: u.card, btn: u.buttons, W: innerWidth, H: innerHeight }}; }})()")
            sb, cd = box(st['s']), box(st['card'])
            check(tag + ': the card says "Page complete! +30"; the sticker and every button inside the card, the card inside the screen', st['s']['page'] == 30 and sb['l'] >= cd['l'] and sb['r'] <= cd['r'] and all(box(q)['b'] <= cd['b'] + 1 for q in st['btn'].values()) and cd['l'] >= 0 and cd['r'] <= st['W'] and cd['b'] <= st['H'], st)
            check(tag + ': ' + ('the sticker at the right (RTL)' if he else 'the sticker at the left'), (sb['l'] > (cd['l'] + cd['r']) / 2) if he else (sb['r'] < (cd['l'] + cd['r']) / 2), [sb, cd])
            await page.wait_for_timeout(300); await page.screenshot(path=OUT + 'card_page_phone_' + lt + '.png')
            check(tag + ': claimPage again: nothing', await page.evaluate(AL + ".claimPage(1)") == 0 and await page.evaluate(P + ".coins") == r['coins'] + 30)
            check(tag + ': no page errors (page bonus)', not errs, errs); await ctx.close()

        # ---- the album: header button, tabs, slots, the unpaid page's bonus with confetti (phone + desktop, EN / HE) ----
        for mobile in (True, False):
            for he in (False, True):
                tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en'); lt = 'he' if he else 'en'; dev = 'phone' if mobile else 'desktop'
                ctx, page, errs = await fresh(b, mobile, he, prof(adv={'stars': stars(12, extra={13: 2}), 'unlocked': 14}))
                await page.evaluate(f"{A}.openMap()"); await page.wait_for_timeout(250)
                hd = await page.evaluate("""(() => { const r = (e) => { const q = e.getBoundingClientRect(); return { l: q.left, r: q.right, t: q.top, b: q.bottom, w: q.width, h: q.height }; }, h2 = $('advTitle'), ab = $('advAlbumBtn');
                  return { back: r($('advBack')), h2: r(h2), album: r(ab), day: r($('advDayChest')), stars: r($('advStarTotal')), full: h2.scrollWidth <= h2.clientWidth + 1, pr: ab.querySelector('.pr').textContent, dot: !ab.querySelector('.dot').hidden, W: innerWidth, noX: document.documentElement.scrollWidth <= innerWidth + 1 }; })()""")
                parts = [hd[k] for k in ('back', 'h2', 'album', 'day', 'stars')]
                check(tag + ': the map header holds back, title, Album (12/40, a dot for the new ones), the day chest and the stars: all inside, none overlapping, 40+ px targets, the title not cut',
                      all(x['l'] >= 0 and x['r'] <= hd['W'] + 0.5 for x in parts) and not any(rects_overlap(parts[i], parts[j], 1) for i in range(5) for j in range(i + 1, 5)) and all(hd[k]['h'] >= 40 and hd[k]['w'] >= 40 for k in ('back', 'album', 'day')) and hd['full'] and hd['pr'] == '12/40' and hd['dot'] and hd['noX'], hd)
                check(tag + ': ' + ('header runs right to left' if he else 'header runs left to right'), (hd['back']['l'] > hd['album']['l'] > hd['day']['l']) if he else (hd['back']['l'] < hd['album']['l'] < hd['day']['l']), hd)
                if mobile: await page.screenshot(path=OUT + 'map_header_phone_' + lt + '.png', clip={'x': 0, 'y': 0, 'width': 360, 'height': 120})
                c0 = await page.evaluate(P + ".coins")
                await tap(page, mobile, '#advAlbumBtn'); await page.wait_for_function(AL + ".shown", timeout=3000)
                check(tag + ': Album opens on the full page not paid yet (world 1)', await page.evaluate(AL + ".page") == 1)
                await page.wait_for_function(AL + ".pages.includes(1)", timeout=6000)
                await page.wait_for_function("document.querySelectorAll('#album .cf').length > 0 || " + AL + ".pages.length", timeout=2000)
                cf = await page.evaluate("document.querySelectorAll('#album .cf').length")
                check(tag + ': ...its bonus: +30 coins once, with confetti and a fanfare, the 8 new stickers peeled in (a peel sound)', await page.evaluate(P + ".coins") == c0 + 30 and cf > 0 and await page.evaluate("__sfx.includes('fanfare') && __sfx.includes('peel')") and await page.evaluate(AL + ".peeled") == list(range(1, 9)), [cf, await page.evaluate(AL + ".peeled")])
                await page.wait_for_function("!document.querySelector('#album .cf')", timeout=4000); await page.wait_for_timeout(300)
                pg = """(() => { const r = (e) => { const q = e.getBoundingClientRect(); return { l: q.left, r: q.right, t: q.top, b: q.bottom, w: q.width, h: q.height }; }, sh = document.querySelector('#album .sheet');
                  return { sheet: r(sh), tabs: [...document.querySelectorAll('.albTab')].map(t => ({ wd: +t.dataset.w, on: t.classList.contains('on'), ...r(t), dot: !!t.querySelector('.dot') })),
                    slots: [...document.querySelectorAll('.albSlot')].map(s => ({ n: +s.dataset.n, got: s.classList.contains('got'), lb: s.querySelector('.lb').textContent.trim(), stars: s.querySelectorAll('.lb svg').length, num: s.querySelector('.num') ? s.querySelector('.num').textContent : '', c: r(s.querySelector('canvas')), ...r(s) })),
                    title: $('albumPageTitle').textContent, count: $('albumCount').textContent, reward: $('albumReward').textContent.trim(), done: $('albumReward').classList.contains('done'), next: $('albumNext').textContent,
                    W: innerWidth, H: innerHeight, noX: document.documentElement.scrollWidth <= innerWidth + 1, fits: sh.scrollHeight <= sh.clientHeight + 1, fresh: __grasp.album.fresh }; })()"""
                a = await page.evaluate(pg)
                check(tag + ': page 1: 8 stickers in colour with their names, "8 / 8", "Page complete!" (done), the sheet inside the screen, nothing to scroll',
                      [s['n'] for s in a['slots']] == list(range(1, 9)) and all(s['got'] and s['lb'] for s in a['slots']) and a['count'] == '8 / 8' and a['done'] and a['reward'].startswith(await page.evaluate("t('albumDone')"))
                      and a['sheet']['l'] >= 0 and a['sheet']['r'] <= a['W'] + 0.5 and a['sheet']['t'] >= 0 and a['sheet']['b'] <= a['H'] + 0.5 and a['noX'] and a['fits'], a)
                check(tag + ': names in the language (Brick / לבנה); the page title "World 1 · ..."', a['slots'][0]['lb'] == ('לבנה' if he else 'Brick') and a['title'] == await page.evaluate("t('albumPage', { n: 1, w: t('wn_1') })"), a['slots'][0])
                check(tag + ': 5 world tabs (1 on), 40+ px targets; world 2 has a dot (new stickers there); big sticker slots (>= 52 px), no slot overlapping',
                      [t_['wd'] for t_ in a['tabs']] == [1, 2, 3, 4, 5] and a['tabs'][0]['on'] and all(t_['h'] >= 40 and t_['w'] >= 40 for t_ in a['tabs']) and a['tabs'][1]['dot'] and all(s['c']['w'] >= 52 for s in a['slots'])
                      and not any(rects_overlap(a['slots'][i], a['slots'][j], 1) for i in range(8) for j in range(i + 1, 8)), a['tabs'])
                check(tag + ': ' + ('tabs and slots run right to left' if he else 'tabs and slots run left to right'), (a['tabs'][0]['l'] > a['tabs'][1]['l'] and a['slots'][0]['l'] > a['slots'][1]['l']) if he else (a['tabs'][0]['l'] < a['tabs'][1]['l'] and a['slots'][0]['l'] < a['slots'][1]['l']))
                if not he or mobile: await page.screenshot(path=OUT + 'page1_' + dev + '_' + lt + '.png')
                await tap(page, mobile, '.albTab[data-w="2"]'); await page.wait_for_function(AL + ".page === 2", timeout=2000); await page.wait_for_timeout(700)
                a = await page.evaluate(pg)
                miss = [s for s in a['slots'] if not s['got']]
                check(tag + ': page 2: 4 in colour, 4 silhouettes with their stage number and 3 stars; "4 / 8"; the reward line; "Next sticker: get 3 ★ on stage 13"',
                      [s['n'] for s in a['slots'] if s['got']] == [9, 10, 11, 12] and [s['num'] for s in miss] == ['13', '14', '15', '16'] and all(s['stars'] == 3 for s in miss) and a['count'] == '4 / 8' and not a['done']
                      and a['reward'] == await page.evaluate("t('albumReward', { c: 30 })") and a['next'] == await page.evaluate("t('albumNext', { n: 13 })") and a['fresh'] == [], a)
                if mobile or not he: await page.screenshot(path=OUT + 'page2_' + dev + '_' + lt + '.png')
                await tap(page, mobile, '.albSlot[data-n="15"]'); await page.wait_for_timeout(150)
                check(tag + ': a tap on a silhouette: "Get 3 ★ on stage 15"', await page.evaluate("t('albumNeed', { n: 15 })") in await page.evaluate(TOASTS))
                check(tag + ': the album button: no dot once everything new was seen and paid', await page.evaluate("$('advAlbumBtn').querySelector('.dot').hidden"))
                if mobile: await tap(page, mobile, '#album .xBtn')
                else: await page.keyboard.press('Escape')
                await page.wait_for_function("!" + AL + ".shown", timeout=2000)
                check(tag + ': ' + ('X' if mobile else 'Escape') + ' closes the album; the map stays', await page.evaluate(A + ".mapOpen"))
                await tap(page, mobile, '#advAlbumBtn'); await page.wait_for_function(AL + ".shown", timeout=2000); await page.wait_for_timeout(600)
                check(tag + ': reopened: no bonus twice; it opens on the current stage\'s world (2)', await page.evaluate(P + ".coins") == c0 + 30 and await page.evaluate(AL + ".page") == 2)
                if not mobile and not he:
                    await page.click('#album', position={'x': 5, 'y': 5}); await page.wait_for_timeout(100)
                    check('a tap on the backdrop closes it', not await page.evaluate(AL + ".shown"))
                    await page.evaluate(f"(() => {{ for (let n = 1; n <= 40; n++) {P}.adv.stars[n] = 3; saveProfile(); }})()"); await page.reload(); await page.wait_for_function("window.__grasp && __grasp.album", timeout=8000)
                    await page.evaluate(SFX_JS)
                    check('all 40 three-starred (after a reload): 40 stickers', len(await page.evaluate(AL + ".got")) == 40)
                    await page.evaluate(f"{A}.openMap()"); await page.evaluate(AL + ".open(4)"); await page.wait_for_timeout(1900)
                    await page.screenshot(path=OUT + 'page4_desktop_en.png')
                    await page.evaluate(AL + ".setPage(5)"); await page.wait_for_function(AL + ".pages.includes(5)", timeout=4000); await page.wait_for_timeout(500)
                    await page.screenshot(path=OUT + 'page5_desktop_en.png')
                    check('every page shown pays once: 1, 4, 5 so far; "Every sticker found!"', await page.evaluate(AL + ".pages") == [1, 4, 5] and await page.evaluate("$('albumNext').textContent") == await page.evaluate("t('albumAllDone')"), await page.evaluate(AL + ".pages"))
                check(tag + ': no page errors (album)', not errs, errs); await ctx.close()

        # ---- the profile: bad album fields dropped ----
        ctx, page, errs = await fresh(b, init=prof(adv={'stars': {'3': 3}}, album={'got': [5, 5, 'x', 0, 41, 2.5, 9], 'fresh': [9, 7, 'a'], 'pages': [1, 2, 9, 'z']}))
        check('validation: stickers 1..40 unique and sorted (+ the 3-star stage 3 added, new), new ones only among those got, a page paid only when full',
              await page.evaluate(AL + ".got") == [3, 5, 9] and await page.evaluate(AL + ".fresh") == [9, 3] and await page.evaluate(AL + ".pages") == [], [await page.evaluate(AL + ".got"), await page.evaluate(AL + ".fresh"), await page.evaluate(AL + ".pages")])
        await ctx.close()
        ctx, page, errs = await fresh(b, init=prof(album='junk'))
        check('an album that is not an object: empty', await page.evaluate(AL + ".got") == [] and await page.evaluate(AL + ".pages") == [])
        keys = ['album', 'albumTitle', 'albumAria', 'albumPage', 'albumNeed', 'albumNext', 'albumStage', 'albumReward', 'albumDone', 'albumDoneToast', 'albumAllDone', 'newSticker', 'stickerToast', 'pageDoneCard', 'albumTab'] + ['st_' + s for s in await page.evaluate(AL + ".list")]
        miss = await page.evaluate("(ks => ['en', 'he'].flatMap(l => ks.filter(k => !I18N[l][k] || (l === 'he' && I18N.he[k] === I18N.en[k])).map(k => l + ':' + k)))(" + json.dumps(keys) + ")")
        check('I18N: every album string and sticker name in EN and HE (HE translated)', not miss, miss)
        check('no page errors (profile)', not errs, errs); await ctx.close()

        # ---- world music: starts in a stage, ducks under the banner, stops on pause / hand lost / mute / the end / the map; a track per world; never in Endless ----
        ctx, page, errs = await fresh(b, init=prof(adv={'stars': stars(16), 'unlocked': 40}))
        tr = await page.evaluate(MU + ".tracks")
        check('5 tracks, each its own tempo / key / lead voice (playful square, bells, mechanical saw, marimba, dramatic)', len(tr) == 5 and len({(t_['bpm'], t_['root']) for t_ in tr}) == 5 and [t_['lead'] for t_ in tr] == ['square', 'bell', 'saw', 'marimba', 'drama'], tr)
        check('on the start screen: no music', not await page.evaluate(MU + ".on"))
        await stage_play(page, 1)
        await page.wait_for_function(MU + ".audio === 'running'", timeout=5000)
        await page.wait_for_function(MU + ".on && " + MU + ".world === 1", timeout=3000)
        check('a stage of world 1: the loop starts (world 1), quiet (bus level <= 0.2, the sfx peak at 0.25)', await page.evaluate(MU + ".vol") <= 0.2 and await page.evaluate(MU + ".starts") == 1)
        bn = await page.evaluate(f"!!{S}.ui.levelBanner")
        check('...under the stage banner it is ducked', bn and await page.evaluate(MU + ".ducked") and abs(await page.evaluate(MU + ".target") - await page.evaluate(MU + ".vol * " + MU + ".duck")) < 1e-6, [bn, await page.evaluate(MU + ".target")])
        await page.wait_for_function("!" + MU + ".ducked && __grasp.music.target === __grasp.music.vol", timeout=6000)
        await page.wait_for_function(MU + ".gain > " + MU + ".vol * 0.7", timeout=4000)
        check('...the banner gone: back to full level (the bus gain follows)', True)
        n0 = await page.evaluate(MU + ".notes"); await page.wait_for_timeout(1000); n1 = await page.evaluate(MU + ".notes")
        check('notes keep coming from the lookahead timer, a handful a second (light on a phone)', 3 <= n1 - n0 <= 60, n1 - n0)
        await page.evaluate("pauseGame()"); await page.wait_for_function("!" + MU + ".on", timeout=2000)
        n0 = await page.evaluate(MU + ".notes"); await page.wait_for_timeout(600)
        check('paused (the hand lost pauses the game the same way): the music stops, no more notes', await page.evaluate(MU + ".notes") == n0 and await page.evaluate(MU + ".stops") == 1)
        await page.evaluate("unpauseGame()"); await page.wait_for_function(MU + ".on", timeout=2000)
        check('play goes on: the music again', await page.evaluate(MU + ".starts") == 2)
        await page.evaluate("simLost = () => { mode = 'camera'; cursor.present = false; hand.lastSeen = performance.now() - 2000; cameraStartedAt = performance.now() - 2000; updateNoHand(performance.now()); }; simLost()")
        await page.wait_for_function("!" + MU + ".on && __grasp.pause.on", timeout=2000)
        check('the hand lost (camera play): paused, no music', not await page.evaluate(MU + ".want"))
        await page.evaluate("mode = 'mouse'; noHandShown = false; $('status').hidden = true; unpauseGame()"); await page.wait_for_function(MU + ".on", timeout=2000)
        await page.evaluate("__grasp.muted = true")
        check('muted: stops at once', not await page.evaluate(MU + ".on"))
        n0 = await page.evaluate(MU + ".notes"); await page.wait_for_timeout(500)
        check('...and stays silent', not await page.evaluate(MU + ".on") and await page.evaluate(MU + ".notes") == n0)
        await page.evaluate("__grasp.muted = false"); await page.wait_for_function(MU + ".on", timeout=2000)
        check('unmuted: on again', True)
        await page.evaluate(f"{A}.finishTest(0)")
        check('the stage cleared: the music stops (the clear fanfare plays alone)', not await page.evaluate(MU + ".on") and not await page.evaluate(MU + ".want"))
        await page.wait_for_function(f"{A}.phase === 'card'", timeout=8000); await page.wait_for_timeout(300)
        check('...and stays off on the card', not await page.evaluate(MU + ".on"))
        await stage_play(page, 17); await page.wait_for_function(MU + ".on && " + MU + ".world === 3", timeout=3000)
        check('a stage of world 3: its own track', True)
        await page.evaluate(f"{A}.openMap()"); await page.wait_for_timeout(250)
        check('the map over the stage: no music', not await page.evaluate(MU + ".on"))
        await stage_play(page, 33); await page.wait_for_function(MU + ".on && " + MU + ".world === 5", timeout=3000)
        await page.evaluate(f"{A}.failTest()"); await page.wait_for_timeout(250)
        check('a stage of world 5, then failed: off on the fail card', not await page.evaluate(MU + ".on"))
        await page.evaluate("goHome()"); await page.wait_for_timeout(250)
        check('home: no music', not await page.evaluate(MU + ".on"))
        await page.evaluate("__grasp.setGameMode('strike'); strikeEndless('mouse')")
        await page.wait_for_function(f"gameMode === 'strike' && mode !== 'none' && {S}.walls.length && !{A}.on", timeout=8000)
        s0 = await page.evaluate(MU + ".starts"); await page.wait_for_timeout(900)
        check('Endless: no music', not await page.evaluate(MU + ".on") and await page.evaluate(MU + ".starts") == s0)
        check('no page errors (music)', not errs, errs); await ctx.close()

        # ---- the round-over card: the title clear of the coin / XP pills (phone + desktop, EN / HE; the daily too) ----
        for mobile in (True, False):
            for he in (False, True):
                tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en'); lt = 'he' if he else 'en'
                for daily in ((False, True) if not he else (False,)):
                    ctx, page, errs = await fresh(b, mobile, he)
                    if daily: await page.evaluate("__grasp.setGameMode('strike'); __grasp.startDaily('mouse')")
                    else: await page.evaluate("__grasp.setGameMode('strike'); strikeEndless('mouse')")
                    await page.wait_for_function(f"gameMode === 'strike' && mode !== 'none' && {S}.walls.length", timeout=8000)
                    await page.evaluate(f"{S}.lives = 1; cursor.history.length = 0; {S}.chest = null; {S}.setBallZ(-__grasp.CONFIG.STRIKE_HIT_Z * 0.7, innerWidth * 0.5, innerHeight * 0.1)")
                    await page.wait_for_function(f"{S}.over && {S}.ui.card && {S}.ui.titleBox && {S}.ui.coinBox", timeout=6000); await page.wait_for_timeout(600)
                    u = await page.evaluate(f"(() => {{ const u = {S}.ui; return {{ title: u.titleBox, coin: u.coinBox, xp: u.xpBox, streak: u.streakChip, card: u.card, btn: u.buttons, W: innerWidth, H: innerHeight }}; }})()")
                    T = box(u['title']); pills = [box(u[k]) for k in ('coin', 'xp', 'streak') if u.get(k)]
                    tg = tag + (' daily' if daily else '')
                    check(tg + ': the round-over title (' + ('daily' if daily else '"Round over"') + ') overlaps none of the pills (coins, +XP' + (', streak' if daily else '') + '); all inside the card; the buttons too',
                          u['xp'] and not any(rects_overlap(T, q) for q in pills) and T['l'] >= u['card']['x'] and T['r'] <= u['card']['x'] + u['card']['w'] and all(q['t'] >= u['card']['y'] for q in pills)
                          and all(box(q)['b'] <= u['card']['y'] + u['card']['h'] + 1 for q in u['btn'].values()), u)
                    check(tg + ': the title sits under the pills', all(T['t'] >= q['b'] for q in pills), [T, pills])
                    if not daily: await page.screenshot(path=OUT + 'roundover_' + ('phone' if mobile else 'desktop') + '_' + lt + '.png')
                    elif mobile: await page.screenshot(path=OUT + 'roundover_daily_phone_en.png')
                    check(tg + ': no page errors (round over)', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
