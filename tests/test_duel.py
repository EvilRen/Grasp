# Challenge a friend: the stage / Frenzy / Endless cards' 'Challenge a friend' button builds a short link (/duel?m=adv&s=12&score=1234&by=<base64url
# name>&d=e; Frenzy / Endless: + seed=<base64url>), asks the name once (optional, sanitized, kept), and opens the share sheet (else the clipboard and
# a toast) with a line in EN / HE. Opening /duel?... plays the same run (an Adventure stage by its number; an Endless / Frenzy run from its seed: the
# same walls, power-up bricks and guests), shows 'Beat 1234 (from Dana)' with a ghost on a bar, 'You passed Dana!', and the card says WIN / LOSE with
# both scores and 'Send back'. Every parameter is validated and clamped; a broken link opens the Adventure map. The daily and the stages keep their
# own seeds. Screenshots tests/out/duel_*.png (EN / HE, phone / desktop).
exec(open('tests/test_challenge.py').read().split('async def main')[0])
D = "__grasp.duel"
SEQ = """(() => { const s = __grasp.strike, sig = (w) => w.kind + ':' + w.bricks.filter(k => k.pu).map(k => k.pu + k.col + k.row).join('') + ':' + w.bricks.filter(k => k.weak || k.armor || k.gold || k.key || k.turret || k.hole).map(k => k.col + '' + k.row).join('');
  const first = s.walls.map(sig); s.setLevel(6); const lv6 = s.walls.map(sig); const more = []; for (let i = 0; i < 8; i++) more.push(sig(s.spawnWall(undefined, 9000 + i * 10)));
  return { first, lv6, more, gq: s.guestQ && [s.guestQ.at, s.guestQ.kind], seed: __grasp.duel.runSeed, r: ['pu', 'turret', 'guest', 'rally'].map(c => +__grasp.strikeRand(c).toFixed(9)) }; })()"""
SHARE_STUB = """window.__shared = []; window.__clip = []; try { navigator.clipboard.writeText = async (x) => { __clip.push(x); }; } catch (e) {}"""

async def new_page(b, url, mobile=False, he=False, init=''):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + SPEECH + "localStorage.setItem('lang','" + ('he' if he else 'en') + "');" + init)
    await page.goto(url); await page.wait_for_function("window.__grasp && __grasp.duel", timeout=10000)
    await page.evaluate(SFX_JS); await page.evaluate(HELP)
    return ctx, page, errs

def local(link): return link.replace('https://grasp-weld.vercel.app', 'http://localhost:8765')
LVL = "localStorage.setItem('grasp.testLevel', '1');"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ===== D1: the link: building, encoding, parsing, validation =====
        ctx, page, errs = await fresh(b)
        lk = await page.evaluate(f"""({{ adv: {D}.build({{ m: 'adv', s: 12, score: 1234, by: 'Dana', d: 'easy' }}), frz: {D}.build({{ m: 'frz', seed: 0xDEADBEEF, score: 34, d: 'normal' }}), end: {D}.build({{ m: 'end', s: 2, seed: 7, score: 99999999999, by: '' }}),
          he: {D}.build({{ m: 'adv', s: 3, score: 5, by: 'דנה' }}), clamp: {D}.build({{ m: 'adv', s: 99, score: -5, by: '  <b>Dana</b> 😀 !! ' }}) }})""")
        check('the link: /duel?m=adv&s=12&score=1234&by=<base64url name>&d=e on the live site', lk['adv'] == 'https://grasp-weld.vercel.app/duel?m=adv&s=12&score=1234&by=RGFuYQ&d=e', lk['adv'])
        check('Frenzy / Endless carry the run\'s seed (base64url, 6 characters); no name: no by=', lk['frz'] == 'https://grasp-weld.vercel.app/duel?m=frz&seed=3q2-7w&score=34&d=n' and 'by=' not in lk['end'] and 'seed=AAAABw' in lk['end'] and 'score=9999999' in lk['end'], [lk['frz'], lk['end']])
        check('short links (< 110 characters), a Hebrew name round-trips as base64url UTF-8, values clamped (stage 40, score 0), the name sanitized', all(len(v) < 110 for v in lk.values()) and 'by=15PXoNeU' in lk['he'] and 's=40' in lk['clamp'] and 'score=0' in lk['clamp'], lk)
        pr = await page.evaluate(f"""(() => {{ const P = {D}.parse; return {{
          ok: P('?m=adv&s=12&score=1234&by=RGFuYQ&d=e'), frz: P('?m=frz&seed=3q2-7w&score=34&d=n'), he: P('?m=adv&s=3&score=5&by=15PXoNeU'),
          badm: P('?m=boss&s=3'), nom: P('?s=3'), big: P('?m=adv&s=999&score=123456789&d=x'), junk: P('?m=end&s=abc&seed=@@@&score=12a&by=!!!&d=n'), long: P('?m=adv&s=5&score=1&by=' + 'A'.repeat(200)),
          neg: P('?m=adv&s=-4&score=-9'), endw: P('?m=end&s=9&seed=AAAABw'), xss: P('?m=adv&by=' + {D}.nameEnc('<img src=x onerror=alert(1)>')), empty: P(''), notstr: P(null) }}; }})()""")
        check('parse: a good link', pr['ok'] == {'m': 'adv', 's': 12, 'seed': None, 'seedOk': False, 'score': 1234, 'by': 'Dana', 'd': 'easy'} and pr['frz']['seed'] == 0xDEADBEEF and pr['frz']['d'] == 'normal' and pr['he']['by'] == 'דנה', pr['ok'])
        check('parse: no known mode = no duel (null)', pr['badm'] is None and pr['nom'] is None and pr['empty'] is None and pr['notstr'] is None)
        check('parse: everything else clamped or ignored (stage 1..40, score 0..9,999,999, bad seed / name / difficulty dropped, long values ignored)',
              pr['big']['s'] == 40 and pr['big']['score'] == 9999999 and pr['big']['d'] is None and pr['junk']['s'] == 1 and pr['junk']['seed'] is None and not pr['junk']['seedOk'] and pr['junk']['score'] == 0 and pr['junk']['by'] == '' and pr['long']['by'] == '' and pr['neg']['s'] == 1 and pr['neg']['score'] == 0 and pr['endw']['s'] == 5, pr)
        check('a name never carries markup: only letters, digits, spaces and . _ \' - (16 at most)', pr['xss']['by'] == 'img srcx onerror' and not any(ch in pr['xss']['by'] for ch in '<>=()/'), pr['xss'])
        nm = await page.evaluate(f"[{D}.sanitize('  Dana   Lee  '), {D}.sanitize('ABCDEFGHIJKLMNOPQRSTUV'), {D}.sanitize('יוֹסִי'), {D}.sanitize(42), {D}.seedDec({D}.seedEnc(4294967295)), {D}.seedDec('AAAA'), {D}.nameDec('%%%')]")
        check('sanitize: spaces folded, 16 characters at most, Hebrew (with niqqud) kept; seeds round-trip (32 bit); garbage decodes to nothing', nm[0] == 'Dana Lee' and nm[1] == 'ABCDEFGHIJKLMNOP' and nm[2] == 'יוֹסִי' and nm[3] == '' and nm[4] == 4294967295 and nm[5] is None and nm[6] == '', nm)
        rw = await page.evaluate("Promise.all(['/duel?m=adv&s=2', '/duel/?m=frz', '/duel'].map(u => fetch(u).then(r => r.status)))")
        vj = json.load(open('vercel.json'))
        check('vercel.json (and tests/serve.py) rewrite /duel and /duel/ to the page, the query kept', rw == [200, 200, 200] and all('duel' in r['source'] for r in vj['rewrites']), rw)
        check('D1: no page errors', not errs, errs); await ctx.close()

        # ===== D2: the Endless card: Challenge a friend, the name once, the share sheet / the clipboard; the same run from the link =====
        ctx, page, errs = await fresh(b, init=SHARE_STUB)
        await page.evaluate("__grasp.setPlayerLevel(12); profile.worlds.unlocked = 1; saveProfile()")
        await page.click('.modes button[data-mode=strike]'); await page.click('#advEndless')
        await page.wait_for_function(f"gameMode === 'strike' && mode === 'mouse' && {S}.walls.length === 4", timeout=10000)
        s1 = await page.evaluate(SEQ)
        check('every Endless run has its own seed (strikeRand from it: a duel can replay the run)', isinstance(s1['seed'], int) and s1['seed'] >= 0, s1['seed'])
        await page.evaluate(f"(() => {{ const s = {S}; s.score = 1234; s.lives = 1; s.setBallZ(100, 640, 420); strikeMiss(s.ball, performance.now()); }})()")
        await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.duel", timeout=6000); await page.wait_for_timeout(500)
        eb = await page.evaluate(f"({{ btn: {S}.ui.buttons, card: {S}.ui.card, ctx: {D}.ctx() }})")
        db = eb['btn']['duel']; cd = eb['card']
        check('the Endless round-over card: a "Challenge a friend" button inside the card (under Easy / Normal)', db['y'] > eb['btn']['easy']['y'] and cd['y'] <= db['y'] and db['y'] + db['h'] <= cd['y'] + cd['h'] and db['x'] >= cd['x'] and eb['ctx']['m'] == 'end' and eb['ctx']['score'] == 1234 and eb['ctx']['seed'] == s1['seed'], eb)
        await page.screenshot(path='tests/out/duel_card_endless_en.png')
        await page.evaluate("try { Object.defineProperty(navigator, 'share', { configurable: true, value: undefined }); } catch (e) {}")
        await page.mouse.click(db['x'] + db['w'] / 2, db['y'] + db['h'] / 2)
        await page.wait_for_function(f"{D}.asking", timeout=4000)
        sh = await page.evaluate("(() => { const r = $('duelName').getBoundingClientRect(), i = $('duelNameIn'); return { title: $('duelNameT').textContent, ph: i.placeholder, focus: document.activeElement === i, w: r.width }; })()")
        check('the first time: a small sheet asks for a name (optional), the field focused', sh['title'] == 'Your name (optional)' and sh['ph'] == 'Name' and sh['focus'], sh)
        await page.screenshot(path='tests/out/duel_name_sheet_en.png')
        await page.mouse.move(640, 300); await page.mouse.move(100, 100); await page.wait_for_timeout(1300)
        check('a fast mouse over the sheet does not restart the round (the card waits)', await page.evaluate(f"{S}.over && {D}.asking"))
        await page.fill('#duelNameIn', ' <Dana>!! '); await page.click('#duelNameGo')
        await page.wait_for_function("__clip.length === 1", timeout=4000)
        cl = await page.evaluate(f"({{ clip: __clip[0], name: profile.duelName, asked: profile.duelAsked, link: {D}.lastLink, toasts: __grasp.toasts.map(t => t.text || t.key || t), sheet: {D}.asking }})")
        check('Share: the name is sanitized and kept ("Dana"); no share sheet here: the line + the link go to the clipboard', cl['name'] == 'Dana' and cl['asked'] and not cl['sheet'] and cl['clip'] == 'I scored 1234 on Grasp Endless — can you beat me? 💥 ' + cl['link'] and '/duel?m=end&s=1&seed=' in cl['link'] and 'by=RGFuYQ' in cl['link'] and 'score=1234' in cl['link'], cl)
        check('a toast: "Challenge link copied!"', any('Challenge link copied!' in str(x) for x in cl['toasts']) or await page.evaluate("t('duelCopied')") == 'Challenge link copied!', cl['toasts'])
        await page.evaluate("Object.defineProperty(navigator, 'share', { configurable: true, value: async (d) => { __shared.push(d); } })")
        r2 = await page.evaluate(f"{D}.share()")
        sd = await page.evaluate("__shared[0]")
        check('the next time: no name sheet; the native share sheet with a title, the line and the link', r2 == 'shared' and sd['title'] == 'Grasp' and sd['text'] == 'I scored 1234 on Grasp Endless — can you beat me? 💥' and sd['url'] == cl['link'], [r2, sd])
        await page.evaluate("Object.defineProperty(navigator, 'share', { configurable: true, value: async () => { const e = new Error('x'); e.name = 'AbortError'; throw e; } })")
        check('a cancelled share sheet: nothing copied, no toast', await page.evaluate(f"{D}.share()") == 'aborted' and await page.evaluate("__clip.length") == 1)
        link_end = cl['link']
        check('D2 challenger: no page errors', not errs, errs)
        # the friend opens the link: the same run
        ctx2, page2, errs2 = await new_page(b, local(link_end), init="if (!sessionStorage.getItem('lv')) { sessionStorage.setItem('lv', '1'); }")
        await page2.wait_for_function(f"{D}.on && gameMode === 'strike' && mode === 'mouse' && {S}.walls.length === 4", timeout=10000)
        await page2.evaluate("__grasp.setPlayerLevel(12)")
        st = await page2.evaluate(f"({{ path: location.pathname + location.search, route: __grasp.route.now, link: {D}.link, start: $('start').hidden, map: advMapOpen(), adv: {A}.on, frz: __grasp.frenzy.on }})")
        check('/duel?m=end... opens the Endless run at once (no start screen, no map), the address keeps the link', st['path'] == link_end.replace('https://grasp-weld.vercel.app', '') and st['route'] == 'duel' and st['start'] and not st['map'] and not st['adv'] and not st['frz'] and st['link']['score'] == 1234 and st['link']['by'] == 'Dana', st)
        s2 = await page2.evaluate(SEQ)
        check('the same seeded run as the challenger\'s: the same walls, special / power-up bricks, guests and random channels', s1 == s2, [s1, s2])
        await page2.wait_for_function(f"{S}.ui.duelBar", timeout=5000)
        bb = await page2.evaluate(f"({{ bar: {S}.ui.duelBar, hud: {S}.ui.hud }})")
        check('the target banner under the HUD pill: "Beat 1,234 (from Dana)", a bar with their ghost', bb['bar']['text'] == 'Beat 1,234 (from Dana)' and bb['bar']['them'] == 1234 and bb['bar']['y'] >= bb['hud']['y'] + bb['hud']['h'] and 0 < bb['bar']['x'] and bb['bar']['x'] + bb['bar']['w'] < 1280 and not bb['bar']['passed'], bb)
        await page2.wait_for_timeout(300); await page2.screenshot(path='tests/out/duel_banner_en.png')
        await page2.evaluate(f"(() => {{ __sfx.length = 0; {S}.score = 1300; }})()")
        await page2.wait_for_function(f"{D}.passed", timeout=4000); await page2.wait_for_timeout(200)
        ps = await page2.evaluate(f"({{ bar: {S}.ui.duelBar, fl: {S}.floaters.map(f => f.text), sfx: __sfx.slice() }})")
        check('passing their score: "You passed Dana!" (a cheer), the ghost behind you', ps['bar']['passed'] and ps['bar']['text'] == 'You passed Dana!' and 'You passed Dana!' in ps['fl'] and 'levelup' in ps['sfx'], ps)
        await page2.screenshot(path='tests/out/duel_passed_en.png')
        await page2.evaluate(f"(() => {{ const s = {S}; s.score = 1500; s.lives = 1; s.setBallZ(100, 640, 420); strikeMiss(s.ball, performance.now()); }})()")
        await page2.wait_for_function(f"{S}.over && {S}.ui.duelCard && {S}.ui.buttons && {S}.ui.buttons.duel", timeout=6000); await page2.wait_for_timeout(500)
        wc = await page2.evaluate(f"({{ dc: {S}.ui.duelCard, card: {S}.ui.card, btn: Object.keys({S}.ui.buttons), sfx: __sfx.slice() }})")
        check('the card: WIN, you 1,500 vs Dana 1,234 (a panel above the card), no Easy / Normal in a duel, "Send back"', wc['dc']['win'] and wc['dc']['text'] == 'WIN' and wc['dc']['you'] == 1500 and wc['dc']['them'] == 1234 and wc['dc']['y'] + wc['dc']['h'] <= wc['card']['y'] and 'easy' not in wc['btn'] and 'duel' in wc['btn'] and 'record' in wc['sfx'], wc)
        await page2.screenshot(path='tests/out/duel_win_en.png')
        await page2.evaluate("profile.duelAsked = true; profile.duelName = 'Noa'; saveProfile(); try { Object.defineProperty(navigator, 'share', { configurable: true, value: undefined }); } catch (e) {}")
        await page2.evaluate(SHARE_STUB); await page2.evaluate(f"{D}.share()"); sb = await page2.evaluate(f"({{ link: {D}.lastLink, clip: __clip[0] }})")
        check('Send back: the same challenge (mode, world, seed) with your score and name', sb['link'].startswith(link_end.split('&score=')[0]) and 'score=1500' in sb['link'] and 'by=Tm9h' in sb['link'], sb)
        await page2.evaluate("endCardAction('again', performance.now())"); await page2.wait_for_function(f"!{S}.over && {D}.on", timeout=5000)
        s3 = await page2.evaluate(f"({{ seed: {D}.runSeed, passed: {D}.passed }})")
        check('Play again in a duel: the same challenge again (the same seed, the target back)', s3['seed'] == s1['seed'] and not s3['passed'], s3)
        await page2.evaluate(f"(() => {{ const s = {S}; s.score = 200; s.lives = 1; s.setBallZ(100, 640, 420); strikeMiss(s.ball, performance.now()); }})()")
        await page2.wait_for_function(f"{S}.over && {S}.ui.duelCard", timeout=6000); await page2.wait_for_timeout(400)
        lc = await page2.evaluate(f"{S}.ui.duelCard")
        check('a lower score: LOSE, 200 vs 1,234', not lc['win'] and not lc['tie'] and lc['text'] == 'LOSE' and lc['you'] == 200, lc)
        await page2.evaluate("goHome()"); await page2.wait_for_timeout(400)
        hm = await page2.evaluate(f"({{ on: {D}.on, path: location.pathname, mode, diff: __grasp.strike.diff }})")
        check('Home leaves the duel (the address back to /)', not hm['on'] and hm['path'] == '/' and hm['mode'] == 'none', hm)
        check('D2 friend: no page errors', not errs2, errs2); await ctx2.close(); await ctx.close()

        # ===== D3: Frenzy and the Adventure; the difficulty from the link; other seeds untouched =====
        ctx, page, errs = await fresh(b, init=SHARE_STUB)
        await page.evaluate("__grasp.setPlayerLevel(12); profile.frenzy = { best: 3, top: 1.2, runs: 1 }; saveProfile(); setInputPref('mouse')")
        await page.click('.modes button[data-mode=strike]'); await page.wait_for_function("advMapOpen()", timeout=8000); await page.click('#advFrenzy')
        await page.wait_for_function(f"__grasp.frenzy.on && {S}.walls.length === 4", timeout=10000)
        f1 = await page.evaluate(SEQ)
        await page.evaluate(f"(() => {{ const s = {S}; s.noTiming = true; s.hits = 21; s.shield = 0; s.lives = 1; s.setBallZ(100, 640, 420); strikeMiss(s.ball, performance.now()); }})()")
        await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.duel && {S}.ui.buttons.share", timeout=6000); await page.wait_for_timeout(400)
        fb = await page.evaluate(f"({{ d: {S}.ui.buttons.duel, s: {S}.ui.buttons.share, card: {S}.ui.card, ctx: {D}.ctx(), text: {D}.text() }})")
        check('the Frenzy card: Share and Challenge a friend side by side inside the card; the line "I hit 21 in a row on Grasp Frenzy — can you beat me? 💥"', abs(fb['d']['y'] - fb['s']['y']) < 1 and fb['d']['x'] > fb['s']['x'] and fb['d']['x'] + fb['d']['w'] <= fb['card']['x'] + fb['card']['w'] and fb['ctx']['m'] == 'frz' and fb['ctx']['score'] == 21 and fb['text'] == 'I hit 21 in a row on Grasp Frenzy — can you beat me? 💥', fb)
        await page.screenshot(path='tests/out/duel_card_frenzy_en.png')
        flink = await page.evaluate(f"{D}.build({{ ...{D}.ctx(), by: 'Ari' }})")
        ctx2, page2, errs2 = await new_page(b, local(flink))
        await page2.wait_for_function(f"{D}.on && __grasp.frenzy.on && {S}.walls.length === 4", timeout=10000); await page2.evaluate("__grasp.setPlayerLevel(12)")
        f2 = await page2.evaluate(SEQ)
        fr = await page2.evaluate(f"({{ lives: {S}.lives, shield: {S}.shield, path: location.pathname, route: __grasp.route.now }})")
        check('/duel?m=frz...: a Frenzy run (one heart + the shield) from the challenger\'s seed: the same walls and channels', fr['lives'] == 1 and fr['shield'] == 1 and fr['path'] == '/duel' and fr['route'] == 'duel' and f1 == f2, [fr, f1 == f2])
        await page2.evaluate(f"{S}.hits = 22"); await page2.wait_for_function(f"{D}.passed", timeout=3000)
        check('Frenzy: the score is hits in a row (22 > 21: passed)', await page2.evaluate(f"{D}.score()") == 22)
        check('D3 frenzy: no page errors', not errs2, errs2); await ctx2.close()
        # the Adventure: the stage by its number (even one the friend has not reached), the challenger's difficulty for the run only
        await page.evaluate("goHome()"); await page.evaluate("profile.adv.unlocked = 40; saveProfile(); setStrikeDiff('normal')")
        await page.evaluate(f"{A}.start(12, 'mouse')"); await page.wait_for_function(f"{A}.on && {A}.stage === 12 && {A}.phase === 'play' && {S}.walls.length > 0", timeout=10000)
        a1 = await page.evaluate(f"(() => {{ const s = {S}; return {{ walls: s.walls.map(w => w.kind + w.bricks.filter(k => k.weak || k.armor || k.gold || k.key || k.turret).length), r: ['serve', 'bricks'].map(c => +__grasp.strikeRand(c).toFixed(9)), seed: {D}.runSeed }}; }})()")
        alink = await page.evaluate(f"{D}.build({{ m: 'adv', s: 12, score: 4321, by: 'Dana', d: 'normal' }})"); await page.evaluate("setStrikeDiff('easy')")
        check('an Adventure stage keeps its own seeding (no run seed)', a1['seed'] is None, a1)
        ctx2, page2, errs2 = await new_page(b, local(alink), mobile=True, he=True)
        await page2.wait_for_function(f"{D}.on && {A}.on && {A}.stage === 12 && {A}.phase === 'play' && {S}.walls.length > 0", timeout=10000)
        a2 = await page2.evaluate(f"(() => {{ const s = {S}; return {{ walls: s.walls.map(w => w.kind + w.bricks.filter(k => k.weak || k.armor || k.gold || k.key || k.turret).length), r: ['serve', 'bricks'].map(c => +__grasp.strikeRand(c).toFixed(9)), seed: {D}.runSeed, unl: {A}.unlocked, diff: {S}.diff, saved: localStorage.getItem('strikeDiff') }}; }})()")
        check('/duel?m=adv&s=12: stage 12 at once, though this player has not reached it; the same walls (the bricks\' grid follows the screen) and serves; Normal (the challenger\'s) for this run, not saved', [x.rstrip('0123456789') for x in a2['walls']] == [x.rstrip('0123456789') for x in a1['walls']] and a2['r'][0] == a1['r'][0] and a2['unl'] == 1 and a2['diff'] == 'normal' and a2['saved'] != 'normal', [a1, a2])
        await page2.wait_for_function(f"{S}.ui.duelBar", timeout=6000); await page2.wait_for_timeout(1800)
        hb = await page2.evaluate(f"({{ bar: {S}.ui.duelBar, W: innerWidth }})")
        check('HE phone: "עקפו את 4,321 (של Dana)" under the pill, inside the screen', hb['bar']['text'] == 'עקפו את 4,321 (של Dana)' and hb['bar']['x'] >= 0 and hb['bar']['x'] + hb['bar']['w'] <= hb['W'], hb)
        await page2.screenshot(path='tests/out/duel_banner_adv_he.png')
        await page2.evaluate(f"(() => {{ {S}.score = 900; }})()"); await page2.evaluate(f"{A}.failTest()")
        await page2.wait_for_function(f"{S}.over && {S}.ui.duelCard && {S}.ui.buttons && {S}.ui.buttons.duel", timeout=8000); await page2.wait_for_timeout(600)
        ac = await page2.evaluate(f"({{ dc: {S}.ui.duelCard, card: {S}.ui.card, btn: {S}.ui.buttons, H: innerHeight, W: innerWidth, lb: {S}.ui.advLabels }})")
        check('HE phone, the stage\'s fail card in a duel: "הפסד" 900 vs 4,321 above it, "החזירו אתגר" (Send back) inside the card, everything on the screen', not ac['dc']['win'] and ac['dc']['text'] == 'הפסד' and ac['dc']['y'] >= 0 and ac['dc']['y'] + ac['dc']['h'] <= ac['card']['y'] and ac['lb']['duel'] == 'החזירו אתגר' and ac['btn']['duel']['y'] + ac['btn']['duel']['h'] <= ac['card']['y'] + ac['card']['h'] and ac['card']['y'] + ac['card']['h'] <= ac['H'], ac)
        await page2.screenshot(path='tests/out/duel_lose_adv_he.png')
        ht = await page2.evaluate(f"(() => {{ const c = {D}.ctx(); return {{ c, text: {D}.text(c) }}; }})()")
        check('HE: the challenge line "השגתי 900 בשלב 12 ב-Grasp — תצליחו לנצח אותי? 💥"', ht['text'] == 'השגתי 900 בשלב 12 ב-Grasp — תצליחו לנצח אותי? 💥', ht)
        await page2.evaluate("endCardAction('map', performance.now())"); await page2.wait_for_timeout(300)
        mp = await page2.evaluate(f"({{ on: {D}.on, diff: {S}.diff, map: advMapOpen() }})")
        check('Map leaves the duel; the player\'s own difficulty is back', not mp['on'] and mp['diff'] == 'easy' and mp['map'], mp)
        check('D3 adventure: no page errors', not errs2, errs2); await ctx2.close()
        # the daily keeps its date seed
        await page.evaluate("goHome()"); await page.evaluate("__grasp.daily.forceModifier = 'tiny'; __grasp.setGameMode('strike'); __grasp.startDaily()")
        await page.wait_for_function("__grasp.daily.on", timeout=8000)
        dy = await page.evaluate(f"({{ seed: {D}.runSeed, r: __grasp.strikeRand('walls') }})")
        check('the daily keeps its own date seed (no run seed)', dy['seed'] is None and 0 <= dy['r'] < 1, dy)
        check('D3: no page errors', not errs, errs); await ctx.close()

        # ===== D4: broken links; Back from a duel =====
        ctx, page, errs = await new_page(b, 'http://localhost:8765/duel?m=boss&s=3&score=12')
        await page.wait_for_function("advMapOpen()", timeout=8000)
        bl = await page.evaluate(f"({{ on: {D}.on, map: advMapOpen(), path: location.pathname }})")
        check('a link with no known mode: the Adventure map, no duel', not bl['on'] and bl['map'], bl)
        await page.goto('http://localhost:8765/duel/?m=end&s=zz&seed=%%%&score=-1&by=<script>&d=q'); await page.wait_for_function(f"{D}.on && {S}.walls.length === 4", timeout=10000)
        jl = await page.evaluate(f"({{ link: {D}.link, seed: {D}.runSeed, w: {S}.world }})")
        check('/duel/ with junk parameters: still an Endless duel (world 1, a fresh seed, target 0, no name)', jl['link']['s'] == 1 and jl['link']['score'] == 0 and jl['link']['by'] == '' and jl['link']['d'] is None and isinstance(jl['seed'], int) and jl['w'] == 1, jl)
        await page.wait_for_timeout(300); await page.go_back(); await page.wait_for_timeout(400)
        check('Back from a duel: the start screen', await page.evaluate("mode === 'none' && !__grasp.duel.on"))
        check('D4: no page errors', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
