exec(open('tests/test_challenge.py').read().split('async def main')[0])
# The 6-persona playtest fixes (see HANDOFF.md "Panel fixes").
# Batch 1 (bugs): 1 Slice: a bomb on the last heart shows the card and the frame loop keeps running (and one mode's exception never kills the
# loop); 2 Smash: a thing knocked off the screen is broken and credited (the wave completes), the speed clamp, the idle aid; 3 a canvas card's Home
# never taps through to the start screen; 4 the run-power title is its own i18n key; 5 the Replay pill's label clear of its thumb (HE); 6 touch
# wording under the cards (EN / HE) and the Daily panel's Play first; 7 no request for the missing monkey art; 8 toasts under an open sheet's
# header; 9 singular forms; 10 "Strike" translated in the HE Shop; 11 canvas bidi (+1, ×7 in Hebrew); 12 the sticker slot is no dark block;
# 13 the Frenzy card's Map; 14 the card's missions by the game played; 15 the meta pill's XP part opens the Road; 16 Tremorti: an 18 Hz rhythm
# is "unusual for tremor, possibly a measurement artefact".
# Batch 2 (feel): Strike's fingertip marker (touch) / ghost hand (camera) under the ball, labels off the ball, one serve instruction, Easy
# pacing (tests/strike_sim.js), Frenzy ramp, ranks; camera hand-loss (600 ms gap: no pause / no countdown in a free mode, a quiet chip in a timed
# one; the card's "More help"); the camera stays on at home and the hand dwells on tiles / map stops; drums (gentle strike, 2 samples, Harder!);
# paint's erase confirm; Busy Board (music on top, ~175 px cells, drag-scroll, a 3-word hint); Bubble Pop (the prompt once per device, no picker
# line, Calm keeps 5); Sandbox (mid-screen start, the toy box, the hint at the top); the pet (a starter snack, the Scarf at Baby); the economy
# (the welcome gift, a 150-coin theme, the map's next-purchase goal); Slice (2 s grace, 5 hearts in the first round, phone fruit, round length).
# Screenshots: tests/out/fix_*.png. State changes are polled (timing-independent).
import math
SIM = open('tests/strike_sim.js').read() + "\n;0"
SLSIM = open('tests/slice_sim.js').read() + "\n;0"
PF = "__grasp.panelfix"
CAMJS = open('tests/test_camgames.py').read().split('POINT_JS = """')[1].split('"""')[0]
FR = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
def overl(a, b): return a['x'] < b['x'] + b['w'] and b['x'] < a['x'] + a['w'] and a['y'] < b['y'] + b['h'] and b['y'] < a['y'] + a['h']

async def camfresh(b, mobile=False, he=False, init=''):  # a page with the camera stub, the camera chosen
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(permissions=['camera'], **opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + HAND_JS + CAMJS + "localStorage.setItem('lang','" + ('he' if he else 'en') + "');localStorage.setItem('inputPref','camera');" + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_function("typeof __grasp !== 'undefined' && !!__grasp.panelfix", timeout=10000); await page.wait_for_timeout(500)
    await page.evaluate(SFX_JS)
    return ctx, page, errs

async def tap_at(page, mobile, x, y):
    if mobile: await page.touchscreen.tap(x, y)
    else: await page.mouse.click(x, y)

async def slice_start(page, mobile):
    await (page.tap if mobile else page.click)('#start button[data-mode=slice]')
    await page.wait_for_function("gameMode === 'slice' && mode === 'mouse'", timeout=10000)

async def slice_end(page):  # three misses (the suites' 3-heart rounds)
    for _ in range(8):
        if await page.evaluate("__grasp.slice.over"): break
        await page.evaluate("(() => { __grasp.CONFIG.SLICE_GRAVITY = 0; const f = __grasp.slice; f.nextSpawn = 1e12; f.fruits.push({ x: 300, y: innerHeight + 100, vx: 0, vy: 0.5, r: 40, rot: 0, vr: 0, kind: {rind:'#ffc24b', flesh:'#ffe3a1', seed:null}, born: 0 }); })()")
        await page.wait_for_timeout(120)
    await page.wait_for_function("__grasp.slice.over && __grasp.slice.ui.buttons", timeout=4000); await page.wait_for_timeout(650)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ================= 1. Slice: a bomb on the last heart: the card, and the frame loop goes on =================
        ctx, page, errs = await fresh(b)
        await slice_start(page, False)
        await page.evaluate("(() => { __grasp.CONFIG.SLICE_GRAVITY = 0; const s = __grasp.slice; s.lives = 1; s.fruits.length = 0; s.nextSpawn = 1e12; s.fruits.push({ x: 640, y: 400, vx: 0, vy: 0, r: 40, rot: 0, vr: 0, kind: BOMB, bomb: true, born: 0 }); })()")
        await page.mouse.move(380, 400); await page.mouse.down()
        for i in range(1, 13): await page.mouse.move(380 + i * 45, 400); await page.wait_for_timeout(16)
        await page.mouse.up()
        await page.wait_for_function("__grasp.slice.over", timeout=3000)
        await page.wait_for_function("__grasp.slice.ui.buttons", timeout=4000); f0 = await page.evaluate("__grasp.gfx.fxp.frame")
        try: await page.wait_for_function(f"__grasp.gfx.fxp.frame > {f0} + 5", timeout=4000)
        except Exception: pass
        f1 = await page.evaluate("__grasp.gfx.fxp.frame")
        st = await page.evaluate(f"({{ over: __grasp.slice.over, lives: __grasp.slice.lives, bombs: __grasp.slice.bombsHit, btn: Object.keys(__grasp.slice.ui.buttons || {{}}), err: {PF}.frameErr.n }})")
        check('1 Slice: slicing a bomb on the last heart ends the round: the round-over card (Play again / Home), no exception', st['over'] and st['lives'] == 0 and st['bombs'] == 1 and 'again' in st['btn'] and 'home' in st['btn'] and st['err'] == 0 and not errs, [st, errs])
        check('1 Slice: the frame loop keeps running after it (frames advance)', f1 > f0 + 5, [f0, f1])
        await page.evaluate("window.__boom = 1; window.__rs = renderSlice; renderSlice = (n) => { if (window.__boom) { window.__boom = 0; throw new Error('panelfix boom'); } window.__rs(n); }; 0")
        g0 = await page.evaluate("__grasp.gfx.fxp.frame"); await page.wait_for_function(f"{PF}.frameErr.n >= 1 && __grasp.gfx.fxp.frame > {g0} + 10", timeout=4000)
        await page.evaluate("renderSlice = window.__rs; 0")
        check('1 the frame loop survives an exception in a mode (caught, reported once as a page error, frames go on)', await page.evaluate(f"{PF}.frameErr.n") == 1 and sum('panelfix boom' in e for e in errs) == 1, errs)
        await ctx.close()

        # ================= 2. Smash: a thing knocked off the screen is credited; the wave completes =================
        ctx, page, errs = await fresh(b)
        await page.click('#start button[data-mode=smash]'); await page.wait_for_function("!$('smashMap').hidden", timeout=6000); await page.click('#smashFree')
        await page.wait_for_function("gameMode === 'smash' && mode === 'mouse' && __grasp.smash.phase === 'play'", timeout=10000)
        await page.evaluate("__grasp.sm.build('room')"); await page.wait_for_timeout(200)
        r = await page.evaluate("""(() => { const S = __grasp.smash, dyn = S.objs.filter(o => o.alive && !o.stat && o.kind !== 'boss' && o.wave === S.wave).sort((a, b) => b.value - a.value), a = dyn[0], c = dyn[1], now = performance.now();
          M.Body.setPosition(a.body, { x: innerWidth / 2, y: innerHeight + 5000 }); M.Body.setPosition(c.body, { x: -300, y: innerHeight / 2 });
          for (const T of S.tiles) for (let i = 0; i < T.cells.length; i++) if (T.cells[i]) smTileKnock(T, i, Math.floor(i / T.nc), i % T.nc, 0, 0, 1, now, false);
          for (const o of S.objs) if (o.alive && o !== a && o !== c && o.kind !== 'boss') smBreak(o, o.body.position.x, o.body.position.y, 0, 0, 0.4, now);
          return { meter: smMeter(), lost0: S.lost || 0, wave: S.wave, kinds: [a.kind, c.kind] }; })()""")
        await page.wait_for_function(f"(__grasp.smash.lost || 0) >= {r['lost0'] + 2}", timeout=4000)
        await page.wait_for_function(f"__grasp.smash.phase === 'scroll' || __grasp.smash.wave > {r['wave']}", timeout=5000)
        q = await page.evaluate("({ lost: __grasp.smash.lost, wave: __grasp.smash.wave, phase: __grasp.smash.phase })")
        check('2 Smash: things knocked out of the screen (below the floor, past the side) are broken and credited, so the wave completes (it stalled at 70-80%)', q['lost'] >= r['lost0'] + 2 and (q['phase'] == 'scroll' or q['wave'] > r['wave']), [r, q])
        await page.wait_for_function("__grasp.smash.phase === 'play'", timeout=6000)
        v = await page.evaluate("(() => { const o = __grasp.smash.objs.find(o => o.alive && !o.stat && o.kind !== 'boss'); if (!o) return null; M.Body.setVelocity(o.body, { x: 400, y: 300 }); return o.id; })()")
        await page.evaluate(FR)
        sp = await page.evaluate(f"(() => {{ const o = __grasp.smash.objs.find(o => o.id === {v or 0}); return o ? Math.hypot(o.body.velocity.x, o.body.velocity.y) : 0; }})()")
        check('2 Smash: a thing hit very hard is clamped (no tunnelling through the 400 px walls)', v is not None and sp <= 38.5, [v, sp])
        await page.evaluate("__grasp.sm.build('room')"); await page.wait_for_timeout(200)
        mt = await page.evaluate("(() => { const m = __grasp.sm.breakTo(0.66); const S = __grasp.smash; S.lastHitAt = performance.now() - 9000; S.phaseAt = performance.now() - 9000; S.aidAt = -1e9; return { m, seg: S.seg, phase: S.phase, run: S.run }; })()")
        await page.wait_for_function("(__grasp.smash.autoNext || 0) >= 1", timeout=4000)
        check('2 Smash: nothing hit for 8 s: the things left tremble, and free play rolls on with most of the wave smashed', 0.6 <= mt['m'] < 0.85 and await page.evaluate("__grasp.smash.aids >= 1 && __grasp.smash.autoNext >= 1"), mt)
        check('2 Smash: no page errors', not errs, errs); await ctx.close()

        # ================= 3. tap-through: a card's Home on the phone never lands on the start screen under it =================
        for he in (False, True):
            ctx, page, errs = await fresh(b, mobile=True, he=he, init="localStorage.setItem('inputPref','mouse');")
            await slice_start(page, True); await slice_end(page)
            h = await page.evaluate("__grasp.slice.ui.buttons.home"); x, y = h['x'] + h['w'] / 2, h['y'] + h['h'] / 2
            await page.evaluate("window.__clicks = []; document.addEventListener('click', (e) => { if (e.isTrusted) __clicks.push(e.target.id || e.target.className || e.target.tagName); });")
            await page.touchscreen.tap(x, y)
            await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=4000); await page.wait_for_timeout(600)
            o = await page.evaluate(f"(() => {{ const el = document.elementFromPoint({x}, {y}), btn = el && el.closest && el.closest('button'); return {{ under: btn ? (btn.id || btn.dataset.mode || btn.className) : (el && el.id), clicks: __clicks, room: !$('petRoom').hidden, ov: [...document.querySelectorAll('.ov')].filter(e => !e.hidden).map(e => e.id), pick: !$('cgPick').hidden, mode, gm: gameMode, guard: {PF}.cguard.until > 0 }}; }})()")
            check(f'3 tap-through ({"HE" if he else "EN"} phone): the card\'s Home goes home and its tap reaches nothing under it (was: the pet room opened)', not o['clicks'] and not o['room'] and not o['ov'] and not o['pick'] and o['mode'] == 'none' and o['gm'] == 'slice' and o['guard'], o)
            await page.wait_for_timeout(200); await page.evaluate("__grasp.home2.more(true)"); await page.wait_for_timeout(300)
            check(f'3 ...a real tap afterwards still works (home2: the More sheet opens)', await page.evaluate("!$('moreSheet').hidden"))
            check('3 no page errors', not errs, errs); await ctx.close()

        # ================= 4 + 5. the run-power title's own key; the Replay pill (HE) =================
        ctx, page, errs = await fresh(b, mobile=True)
        k = await page.evaluate("({ rp: t('rpTitle'), run: t('runPowTitle'), rpHe: I18N.he.rpTitle, runHe: I18N.he.runPowTitle })")
        check('4 i18n: the replay title and the run-power title are separate keys (EN / HE)', k == {'rp': 'Your best moment', 'run': 'Power for the next stage!', 'rpHe': 'הרגע הכי טוב שלכם', 'runHe': 'כוח לשלב הבא!'}, k)
        await stage(page, 3); await page.evaluate(f"{A}.finishTest(0)")
        await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.next && performance.now() - {S}.overAt > 600", timeout=10000)
        r = await page.evaluate(f"{S}.ui.buttons.next"); await page.touchscreen.tap(r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)
        await page.wait_for_function(f"{S}.perkOffer && {S}.ui.perkCards && {S}.ui.perkCards.length === 3 && {S}.ui.perkTitle", timeout=6000); await page.wait_for_timeout(400)
        check('4 the run-power cards say "Power for the next stage!" (not the replay\'s "Your best moment")', await page.evaluate(f"{S}.ui.perkTitle") == 'Power for the next stage!')
        await page.screenshot(path='tests/out/fix_runpower_title.png')
        check('4 no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, he=True)
        await slice_start(page, False)
        await page.evaluate("__grasp.replay.rp.noGate = true"); c0 = await page.evaluate("__grasp.replay.state.caps"); await page.wait_for_function(f"__grasp.replay.state.caps >= {c0 + 70}", timeout=30000)
        await page.evaluate("(() => { const c = __grasp.slice.combo; c.n = 5; c.t = performance.now(); slice.score = 5; })()"); await page.wait_for_timeout(1800)  # (phase 1: Share only on a record: a first round's score is one)
        await slice_end(page)
        await page.wait_for_function("__grasp.slice.ui.buttons && __grasp.slice.ui.buttons.share && __grasp.replay.ready() && performance.now() - __grasp.slice.overAt > 900", timeout=15000)
        bs = await page.evaluate("__grasp.slice.ui.buttons.share"); await page.mouse.click(bs['x'] + bs['w'] / 2, bs['y'] + bs['h'] / 2)
        await page.wait_for_function("!$('shareSheet').hidden", timeout=4000); await page.wait_for_timeout(500)
        q = await page.evaluate("(() => { const r = $('shReplay').getBoundingClientRect(), l = $('shReplay').querySelector('b'), lr = l.getBoundingClientRect(), ic = $('shReplay').querySelector('.aIc').getBoundingClientRect(); return { label: l.textContent, on: !$('shReplay').hidden && !$('shReplay').disabled, inside: r.left >= 0 && r.right <= innerWidth, clear: lr.right <= ic.left + 1 || lr.left >= ic.right - 1, fits: l.scrollWidth <= l.clientWidth + 1 }; })()")
        check('5 (home2) the replay in Hebrew: Share opens the sheet; its "הילוך חוזר" row, ready, the label clear of its icon', q['label'] == 'הילוך חוזר' and q['on'] and q['inside'] and q['clear'] and q['fits'], q)
        await page.screenshot(path='tests/out/fix_replay_pill_he.png')
        check('5 no page errors', not errs, errs); await ctx.close()

        # ================= 6. the cards' lines in touch wording (EN / HE); the Daily panel's Play first =================
        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx, page, errs = await fresh(b, mobile=True, he=he)
            await stage(page, 1); await page.evaluate(f"{A}.finishTest(0)")
            await page.wait_for_function(f"{S}.over && {S}.ui.againLine && performance.now() - {S}.overAt > 1100", timeout=10000)
            ln = await page.evaluate(f"{S}.ui.againLine")
            check(f'6 {tag}: a stage clear by touch says "Tap Next…", not "Wave…"', ln == ('הקישו על „הבא” לשלב הבא' if he else 'Tap Next for the next stage'), ln)
            await page.wait_for_timeout(300); await page.screenshot(path=f'tests/out/fix_card_touch_{tag}.png')
            await page.evaluate(f"{A}.start(1)"); await page.wait_for_function(f"{A}.phase === 'play'", timeout=8000); await page.evaluate(f"{A}.failTest()")
            await page.wait_for_function(f"{S}.over && {S}.ui.againLine && performance.now() - {S}.overAt > 1100 && {A}.result && !{A}.result.clear", timeout=10000)
            ln2 = await page.evaluate(f"{S}.ui.againLine")
            check(f'6 {tag}: a fail by touch says "Tap Try again"', ln2 == ('הקישו על „שוב” כדי לנסות שוב' if he else 'Tap Try again'), ln2)
            ks = await page.evaluate("(() => { const m0 = mode; const a = againKey('playAgainWave'); mode = 'camera'; const c = [againKey('playAgainWave'), againKey('advWaveNext')]; mode = m0; return [a, ...c]; })()")
            check(f'6 {tag}: Endless / camera games by touch "Tap Play again"; with the camera "Wave…" stays', ks == ['playAgainTap', 'playAgainCam', 'advWaveNext'], ks)
            check(f'6 {tag}: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, mobile=True)
        await page.tap('#arcadeBtn'); await page.wait_for_function("!$('arcadePick').hidden", timeout=4000); await page.wait_for_timeout(400)
        await page.tap('#dailyBtn'); await page.wait_for_function("!$('daily').hidden", timeout=4000)
        d = await page.evaluate("(() => { const a = $('daily').querySelector('.dActs'), bs = [...a.children]; return { ids: bs.map(x => x.id), cls: bs.map(x => x.className), txt: bs.map(x => x.textContent) }; })()")
        check('6 the Daily panel: "Play" (touch) is the primary button, the camera the secondary one', d['ids'] == ['dailyMouse', 'dailyCam'] and d['cls'] == ['primary', 'secondary'] and d['txt'][0] == 'Play', d)
        await ctx.close()

        # ================= 7. no request for the missing monkey art =================
        ctx, page, errs = await fresh(b)
        bad = []; page.on('response', lambda r: bad.append(r.url + ' ' + str(r.status)) if '/assets/guests/' in r.url and r.status >= 400 else None)
        reqs = []; page.on('request', lambda r: reqs.append(r.url) if '/assets/guests/' in r.url else None)
        await endless(page); await page.wait_for_function("['in', 'happy', 'dizzy', 'squash'].every(f => GUEST_ART['cow_' + f] && GUEST_ART['cow_' + f].state !== 'loading')", timeout=10000)
        ms = await page.evaluate("['in', 'happy', 'dizzy', 'squash'].map(f => GUEST_ART['monkey_' + f].state)")
        check('7 Strike loads the cow art but never asks for monkey_*.png (no 404s); the monkey is drawn', not bad and not any('monkey_' in u for u in reqs) and any('cow_in' in u for u in reqs) and ms == ['none'] * 4, [bad, reqs, ms])
        await ctx.close()

        # ================= 8. a toast never covers an open sheet's header (the pet room's title and X) =================
        ctx, page, errs = await fresh(b, mobile=True, init="localStorage.setItem('grasp.profile.pet', '1');")
        await page.evaluate("__grasp.pet.set({ hatched: true, food: 3, pantry: 2, born: '2026-10-01', last: '2026-10-01' }); __grasp.pet.open(true)"); await page.wait_for_timeout(400)
        await page.evaluate("toast('unlockedToast', { n: 'Beach ball' }, 'star')"); await page.wait_for_timeout(500)
        o = await page.evaluate("(() => { const h = $('petRoom').querySelector('header').getBoundingClientRect(), x = $('petRoom').querySelector('.xBtn').getBoundingClientRect(), t = $('metaToast').querySelector('.mt').getBoundingClientRect(); return { h: [h.top, h.bottom], x: [x.top, x.bottom, x.left, x.right], t: [t.top, t.bottom, t.left, t.right] }; })()")
        check('8 a toast while the pet room is open sits under its header (the title and the X stay clear)', o['t'][0] >= o['h'][1] and (o['t'][0] >= o['x'][1] or o['t'][3] <= o['x'][2] or o['t'][2] >= o['x'][3]), o)
        await page.screenshot(path='tests/out/fix_toast_petroom.png')
        await ctx.close()

        # ================= 9-11. singular forms; "Strike" in the HE Shop; canvas bidi in Hebrew =================
        ctx, page, errs = await fresh(b, he=True)
        tx = await page.evaluate("(() => { const L = lang, r = {}; lang = 'en'; r.en1 = t('dayChestNeed', { n: 1 }); r.en2 = t('dayChestNeed', { n: 2 }); r.coins1 = t('coinsN', { n: 1 }); lang = 'he'; r.he1 = t('dayChestNeed', { n: 1 }); r.he2 = t('dayChestNeed', { n: 2 }); r.sub = t('themesSub'); lang = L; return r; })()")
        check('9 plurals: "Clear 1 more stage today…" (not "1 more stages"), 2 = plural; Hebrew too', tx['en1'] == 'Clear 1 more stage today to open the chest' and tx['en2'] == 'Clear 2 more stages today to open the chest' and tx['coins1'] == '1 coin' and tx['he1'] == 'סיימו עוד שלב אחד היום כדי לפתוח את התיבה' and 'שלבים' in tx['he2'], tx)
        check('10 the HE Shop\'s Themes subtitle has no English "Strike"', 'Strike' not in tx['sub'] and 'מכה' in tx['sub'], tx['sub'])
        bd = await page.evaluate(f"""(() => {{ const P = {PF}, a = P.bidiDir('+1'), b = P.bidiDir('רצף ×7!'), c = P.bidiText('רצף ‎×7!'), d = P.bidiText('+5');
          const sp = (txt) => {{ TEXTS.clear(); return textSprite(txt, 20, '#ffffff', null).c.toDataURL(); }}; const he = sp('+1'); const L = lang; lang = 'en'; const en = sp('+1'); lang = L;
          return {{ a, b, c, d, same: he === en }}; }})()""")
        check('11 canvas bidi (HE): "+1" is drawn left-to-right (the same pixels as in English, not "1+"); "×7" in "רצף ×7!" is an LTR isolate', bd['a'] == 'ltr' and bd['b'] == 'rtl' and '⁦×7⁩' in bd['c'] and bd['d'] == '+5' and bd['same'], bd)
        await ctx.close()

        # ================= 12. the sticker slot on the card is no dark block =================
        ctx, page, errs = await fresh(b, mobile=True)
        await stage(page, 1)
        await page.evaluate("window.__sil = 0; const o = stickerSprite; stickerSprite = (n, sil, R) => { if (sil) __sil++; return o(n, sil, R); }; 0")
        await page.evaluate(f"{A}.finishTest(0)")
        await page.wait_for_function(f"{S}.over && {S}.ui.advSticker", timeout=10000); await page.wait_for_timeout(300)
        await page.screenshot(path='tests/out/fix_sticker_slot.png')
        await page.wait_for_function(f"{S}.ui.advSticker && {S}.ui.advSticker.landed", timeout=8000)
        check('12 the new sticker\'s slot on the card is a faint ring (the dark silhouette, a black block while the card came in, is not drawn)', await page.evaluate("__sil") == 0)
        await ctx.close()

        # ================= 13 + 14. the Frenzy card's Map; the card's missions by the game =================
        ctx, page, errs = await fresh(b, init="localStorage.setItem('inputPref','mouse');")
        await page.evaluate("(() => { profile.missions = { date: missionDay(), list: [{ id: 'cars', goal: 2, progress: 0, reward: 15, done: false, claimed: false }, { id: 'walls', goal: 6, progress: 1, reward: 22, done: false, claimed: false }, { id: 'fruit', goal: 15, progress: 0, reward: 15, done: false, claimed: false }] }; saveProfile(); })()")
        await page.click('#start button[data-mode=strike]'); await page.wait_for_function(A + ".mapOpen", timeout=8000); await page.click('#advFrenzy')
        await page.wait_for_function("__grasp.frenzy.on && mode === 'mouse'", timeout=10000)
        await page.evaluate(f"(() => {{ const s = {S}; s.lives = 1; s.shield = 0; s.serve(); s.setBallZ(-__grasp.CONFIG.STRIKE_HIT_Z * 0.9, 30, 30); }})()")
        await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.map && performance.now() - {S}.overAt > 600", timeout=8000)
        fc = await page.evaluate(f"({{ btn: Object.keys({S}.ui.buttons), rows: {S}.ui.missionRow.map(r => r.id), tz: {S}.ui.teaser && {S}.ui.teaser.kind }})")
        check('13 the Frenzy card has a Map button beside Home', 'map' in fc['btn'] and 'home' in fc['btn'] and 'again' in fc['btn'], fc)
        check('14 (home2) the Frenzy card lists no missions and no upsell (missions live in the Today panel)', fc['rows'] == [] and not fc['tz'], fc)
        await page.screenshot(path='tests/out/fix_frenzy_card.png')
        r = await page.evaluate(f"{S}.ui.buttons.map"); await page.mouse.click(r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)
        await page.wait_for_function(A + ".mapOpen", timeout=4000)
        check('13 its Map opens the Adventure map', await page.evaluate(A + ".mapOpen"))
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        await page.click('#start button[data-mode=slice]'); await page.wait_for_function("gameMode === 'slice' && mode === 'mouse'", timeout=8000); await slice_end(page)
        sr = await page.evaluate("__grasp.slice.ui.missionRow.map(r => r.id)")
        check('14 (home2) a Slice card lists no missions either', sr == [], [sr, await page.evaluate("profile.missions")])
        check('13/14 no page errors', not errs, errs); await ctx.close()

        # ================= 15. the meta pill (home2): before the first level-up it opens the Shop (the Road is not earned yet); after it, the Road =================
        ctx, page, errs = await fresh(b)
        lv0 = await page.evaluate("({ lv: getComputedStyle($('metaPill').querySelector('.lvl')).display, nx: getComputedStyle($('metaPill').querySelector('.nx')).display })")
        await page.click('#metaPill'); await page.wait_for_timeout(200)
        a1 = await page.evaluate("({ road: !$('road').hidden, shop: !$('collection').hidden })"); await page.keyboard.press('Escape'); await page.wait_for_timeout(150)
        await page.evaluate("__grasp.addXp(200); __grasp.road.closeCard && __grasp.road.closeCard()"); await page.wait_for_timeout(500); await page.evaluate("for (const o of document.querySelectorAll('.ov')) o.hidden = true")
        lv1 = await page.evaluate("getComputedStyle($('metaPill').querySelector('.lvl')).display")
        await page.click('#metaPill'); await page.wait_for_timeout(200)
        a3 = await page.evaluate("({ road: !$('road').hidden, shop: !$('collection').hidden })")
        check('15 the meta pill: level 1: coins only, a tap opens the Shop; after the first level-up the level shows and the pill opens the Road (no "… XP to: …" upsell text)', lv0 == {'lv': 'none', 'nx': 'none'} and a1 == {'road': False, 'shop': True} and lv1 != 'none' and a3 == {'road': True, 'shop': False}, [lv0, a1, lv1, a3])
        await ctx.close()

        # ---- the economy: the welcome gift, a 150-coin theme, the map's next-purchase goal ----
        ctx, page, errs = await fresh(b, mobile=True, init="window.__graspStarter = true; localStorage.setItem('inputPref','mouse');")
        await slice_start(page, True); await slice_end(page)
        ec = await page.evaluate("({ coins: profile.coins, starter: profile.starter, toast: __grasp.toasts.some(x => x.key === 'starterGift'), gym: __grasp.themes.prices.gym })")
        await page.evaluate("__grasp.slice && endCardAction('again', performance.now())"); await slice_end(page)
        c2 = await page.evaluate("profile.coins")
        check('economy: the first finished round brings a welcome gift of 80 coins (once); the first theme costs 150', ec['coins'] >= 80 and ec['starter'] and ec['toast'] and ec['gym'] == 150 and c2 - ec['coins'] < 80, [ec, c2])
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        await page.evaluate("profile.coins = 50; saveProfile(); openAdvMap({ how: 'mouse' })"); await page.wait_for_timeout(400)
        g1 = await page.evaluate("({ hid: $('advGoal').hidden, txt: $('advGoal').textContent, q: __grasp.panelfix.nextPurchase() })")
        await page.evaluate("profile.coins = 85; saveProfile(); renderAdvMap()"); await page.wait_for_timeout(100)
        g2 = await page.evaluate("$('advGoal').textContent")
        check('economy (home2): no coin goal on the map (no upsell outside the Shop); the next purchase is still known to the Shop', g1['hid'] and await page.evaluate("$('advGoal').hidden") and g1['q'] and g1['q']['name'] == 'Cool hands', [g1, g2])
        await page.screenshot(path='tests/out/fix_map_goal.png')
        check('economy: no page errors', not errs, errs); await ctx.close()

        await b.close()
    srv.terminate()
    print('ALL PASSED' if check.fails == 0 else f'{check.fails} FAILED'); sys.exit(1 if check.fails else 0)

asyncio.run(main())
