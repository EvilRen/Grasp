exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
import os
# Less talking: the one speech gate (speakLine) and the parents' Voice setting (Names · All · Off). A real visitor is simulated with
# window.__graspVoice = 'names' (the suites otherwise keep the old talk: 'all', no timing rules). speechSynthesis is stubbed (window.__spoken;
# the voice list per context: EN + HE, or EN only). Checks: the default 'names' -> Strike / Slice / Smash say nothing at the round start,
# Animals says only names + questions, the same name not again within 6 s, one automatic re-ask then a boop; Hebrew with only an English
# voice = silence; 'off' silences everything (the toddler games, Shapes, the stickers) and cancels a line in progress; mute cancels too;
# 'all' lets the round start speak; the setting survives a reload (profile.grippy follows, an old grippy:false profile = Off); the 3-way
# row in the More sheet works in EN and HE (>= 44 px). Screenshots tests/out/voice_settings_{en,he}.png.
PORT = int(os.environ.get('GRASP_PORT', '8765')); BASE = 'http://localhost:%d' % PORT
if PORT != 8765: srv.terminate()
OUT = 'tests/out/'
results = []
def check(name, ok, detail=''):
    results.append((name, bool(ok))); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else '  | ' + str(detail)[:600]), flush=True)

def speech(voices):
    return ("window.__spoken = []; window.__cancels = 0; (() => { const ss = { speaking: false, speak(u) { __spoken.push({ text: u.text, lang: u.lang, rate: u.rate, pitch: u.pitch, voice: u.voice && u.voice.lang }); ss.speaking = true; }, cancel() { __cancels++; ss.speaking = false; }, getVoices: () => " + voices + ", addEventListener() {} };"
            " try { Object.defineProperty(window, 'speechSynthesis', { value: ss, configurable: true }); } catch (e) {} window.SpeechSynthesisUtterance = function (t) { this.text = t; }; })();")
BOTH = "[{ lang: 'en-US', name: 'E', localService: true }, { lang: 'he-IL', name: 'H', localService: true }]"
EN_ONLY = "[{ lang: 'en-US', name: 'E', localService: true }, { lang: 'en-GB', name: 'G' }]"

async def page_for(b, path='/', he=False, voices=BOTH, real='names', init=''):
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    pre = ("window.__graspVoice = '%s';" % real) if real else ''
    await page.add_init_script(INIT + pre + speech(voices) + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');") + init)
    await page.goto(BASE + path); await page.wait_for_function("typeof engine !== 'undefined' && !!engine", timeout=15000)
    return ctx, page, errs

async def wait(page, cond, timeout=8000):
    try: await page.wait_for_function(cond, timeout=timeout); return True
    except Exception: return False
async def spoken(page): return [s['text'] for s in await page.evaluate("__spoken")]

async def round_start(page, m):
    await page.evaluate("__spoken.length = 0; __grasp.voice.reset()")
    await page.evaluate("__grasp.setGameMode('" + m + "')"); await page.evaluate(START_MOUSE)
    ok = await wait(page, "mode === 'mouse' && gameMode === '" + m + "'")
    await page.wait_for_timeout(1500); return ok

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])

        # ===== 1. a real visitor's default: Names =====
        ctx, page, errs = await page_for(b, '/')
        st = await page.evaluate("({ set: __grasp.voice.set, legacy: __grasp.voice.legacy(), grippy: profile.grippy, ok: ['name','ask','hint','chatter'].map(l => __grasp.voice.ok(l)) })")
        check('a real visitor: the default is Names (names + asks only)', st['set'] == 'names' and not st['legacy'] and st['ok'] == [True, True, False, False], st)
        for m in ('strike', 'slice', 'smash'):
            ok = await round_start(page, m)
            sp = await spoken(page); log = await page.evaluate("__grasp.voice.log.filter(e => e.level === 'chatter').map(e => e.why)")
            check(m + ': the round starts and nothing is said (the start line is chatter)', ok and sp == [], [ok, sp, log])
            await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        bus = await page.evaluate("""(async () => { audioInit(); for (let i = 0; i < 20 && audio.state !== 'running'; i++) await new Promise(r => setTimeout(r, 50));
          sfx('click'); sfx('fanfare'); tgSfx('boop'); return { run: audio.state, bus: !!audio.__bus, ratio: audio.__limiter && audio.__limiter.ratio.value, thr: audio.__limiter && audio.__limiter.threshold.value, lv: [SFX_LEVEL.fanfare, SFX_LEVEL.click, SFX_LEVEL.boom], out: audioOut() === audio.__bus }; })()""")
        check('the master bus: one gain + a limiter (ratio 12, -10 dB); rewards +5 dB, click -4, booms -3', bus['run'] != 'running' or (bus['bus'] and bus['ratio'] == 12 and bus['thr'] == -10 and bus['lv'] == [5, -4, -3] and bus['out']), bus)
        check('no page errors (big kids)', not errs, errs); await ctx.close()

        # ===== 2. Animals under Names: only names and questions; the same name not again within 6 s; one auto re-ask =====
        ctx, page, errs = await page_for(b, '/animals')
        ok = await wait(page, "mode === 'mouse' && gameMode === 'animals' && an.list.length > 0")
        await page.evaluate("tgDemoDone(); an.ask = null; an.freeLeft = 99; an.lastTapAt = performance.now(); __spoken.length = 0; __grasp.voice.reset()")
        await page.evaluate("anPlay(an.list.find(a => a.kind === 'cow') || an.list[0], performance.now())"); await page.wait_for_timeout(1500)
        sp1 = await spoken(page); name = await page.evaluate("t('an_' + (an.list.find(a => a.kind === 'cow') || an.list[0]).kind) + '!'")
        check('animals: a tap says the name only ("' + name + '"), no "Moo!"', ok and sp1 == [name], [ok, sp1])
        await page.evaluate("anPlay(an.list.find(a => a.kind === 'cow') || an.list[0], performance.now())"); await page.wait_for_timeout(1500)
        sp2 = await spoken(page); why = await page.evaluate("__grasp.voice.log.filter(e => e.text === '%s').map(e => e.why)" % name)
        check('animals: the same name again 1.5 s later is not repeated (>= 6 s)', sp2 == [name] and 'same' in why, [sp2, why])
        await page.evaluate("an.freeLeft = 0; anAskStart(performance.now(), 'pig')"); await page.wait_for_timeout(300)
        q = await page.evaluate("t('anWhere', { a: tgName('an_pig', true) })"); sp3 = await spoken(page)
        check('animals: the question is asked ("' + q + '")', sp3[-1:] == [q], sp3)
        await page.evaluate("__grasp.voice.reset(); an.ask.last = performance.now() - 9000; an.lastTapAt = -1e9; anTick(performance.now())"); await page.wait_for_timeout(200)
        sp4 = await spoken(page)
        check('animals: one automatic re-ask', sp4.count(q) == 2, sp4)
        await page.evaluate("__grasp.voice.reset(); window.__nud = tg.nudges || 0; an.ask.last = performance.now() - 9000; an.lastTapAt = -1e9; anTick(performance.now())"); await page.wait_for_timeout(200)
        sp5 = await spoken(page); nud = await page.evaluate("(tg.nudges || 0) - __nud"); boop = await page.evaluate("tg.snd.slice(-3)")
        check('animals: no second automatic re-ask: a bounce + boop instead', sp5.count(q) == 2 and nud == 1 and 'boop' in boop, [sp5, nud, boop])
        await page.wait_for_timeout(3100)
        await page.evaluate("const b = an.bubble; if (b) anDown({ x: b.x, y: b.y }, performance.now())"); await page.wait_for_timeout(200)
        sp6 = await spoken(page)
        check('animals: tapping the question re-asks it (>= 3 s after the last)', sp6.count(q) == 3, sp6)
        lv = await page.evaluate("[...new Set(__grasp.voice.log.filter(e => e.why === 'ok').map(e => e.level))]")
        check('animals: everything said was a name or a question', set(lv) <= {'name', 'ask'} and lv, lv)
        await page.evaluate("const a = an.list.find(x => x.kind !== an.ask.kind); an.lastTapAt = 0; anDown({ x: a.x, y: a.y }, performance.now())"); await page.wait_for_timeout(1200)
        await page.evaluate("const a = an.list.find(x => x.kind === an.ask.kind); anDown({ x: a.x, y: a.y }, performance.now() + 500)"); await page.wait_for_timeout(1300)
        yes = await page.evaluate("t('tgYes')"); sp7 = await spoken(page)
        check('animals: the right animal: a party, no "Yes!" line', not any(yes in s for s in sp7) and await page.evaluate("an.found") >= 1, sp7)
        check('no page errors (animals)', not errs, errs); await ctx.close()

        # ===== 2b. a11y: the pause sheet and Home stop the voice; nothing from the last game under the start screen =====
        ctx, page, errs = await page_for(b, '/peekaboo')
        ok = await wait(page, "mode === 'mouse' && gameMode === 'peekaboo' && pk.ask")
        await page.evaluate("tgDemoDone(); __grasp.voice.reset(); pk.ask.last = -1e9"); ok2 = await wait(page, "__spoken.length > 0", 4000)
        c0 = await page.evaluate("__cancels"); await page.evaluate("openMenu(); __spoken.length = 0")
        check('peekaboo: the question is asked; the pause sheet cancels the line in progress', ok and ok2 and await page.evaluate("__cancels") > c0 and await page.evaluate("menu.open"))
        await page.evaluate("pk.ask.last = -1e9; __grasp.voice.reset()"); await page.wait_for_timeout(9000)
        check('peekaboo paused: no re-ask under the pause sheet (9 s)', await spoken(page) == [], await spoken(page))
        await page.evaluate("closeMenu(true)"); await page.wait_for_timeout(300)
        c1 = await page.evaluate("__cancels"); await page.evaluate("goHome(); __spoken.length = 0; __grasp.voice.reset()")
        check('Home cancels the voice', await page.evaluate("__cancels") > c1 and await page.evaluate("mode === 'none' && !$('start').hidden"))
        await page.wait_for_timeout(20000)
        sp = await spoken(page); ok_after = await page.evaluate("__grasp.voice.log.filter(e => e.why === 'ok').length")
        check('after leaving Peekaboo via Home: no speech in the next 20 s (the game no longer ticks under the start screen)', sp == [] and ok_after == 0, [sp, await page.evaluate("__grasp.voice.log.slice(-4)")])
        check('no page errors (pause / home)', not errs, errs); await ctx.close()

        # ===== 3. Hebrew with only an English voice: silence (never Hebrew read by an English voice) =====
        ctx, page, errs = await page_for(b, '/animals', he=True, voices=EN_ONLY)
        ok = await wait(page, "mode === 'mouse' && gameMode === 'animals' && an.list.length > 0")
        await page.evaluate("tgDemoDone(); an.freeLeft = 99; __spoken.length = 0; __grasp.voice.reset(); anPlay(an.list[0], performance.now()); anAskStart(performance.now() + 10, 'pig'); speakShape('circle'); mbSay('פאזל')")
        await page.wait_for_timeout(1500)
        sp = await spoken(page); why = await page.evaluate("__grasp.voice.log.map(e => e.why)")
        check('HE + only English voices: nothing is spoken (no he voice = silent)', ok and sp == [] and 'novoice' in why, [sp, why])
        check('HE: the voice pick is null, EN picks en-US (localService first)', await page.evaluate("__grasp.voice.pick('he') === null && __grasp.voice.pick('en').lang === 'en-US'"))
        await ctx.close()
        ctx, page, errs = await page_for(b, '/animals', he=True)
        await wait(page, "mode === 'mouse' && gameMode === 'animals' && an.list.length > 0")
        await page.evaluate("tgDemoDone(); an.freeLeft = 99; __spoken.length = 0; __grasp.voice.reset(); anPlay(an.list[0], performance.now())"); await page.wait_for_timeout(1500)
        u = await page.evaluate("__spoken[0] || null")
        check('HE with a he-IL voice: spoken with that voice, rate 0.9, pitch 1.0', u and u['voice'] == 'he-IL' and abs(u['rate'] - 0.9) < 1e-6 and u['pitch'] == 1, u)
        await page.evaluate("__spoken.length = 0; __grasp.voice.reset(); speakLine('חום!')");
        check('HE: a spoken-only spelling (חום -> חוּם), the screen text unchanged', await spoken(page) == ['חוּם!'], await spoken(page))
        await ctx.close()

        # ===== 4. Off: everything silent, the line in progress cancelled; mute cancels too =====
        ctx, page, errs = await page_for(b, '/animals')
        await wait(page, "mode === 'mouse' && gameMode === 'animals' && an.list.length > 0")
        await page.evaluate("tgDemoDone(); an.freeLeft = 99; __spoken.length = 0; __grasp.voice.reset(); anPlay(an.list[0], performance.now())"); await page.wait_for_timeout(1300)
        c0 = await page.evaluate("__cancels"); before = await spoken(page)
        await page.evaluate("__grasp.voice.set = 'off'"); c1 = await page.evaluate("__cancels")
        check('off: the line in progress is cancelled', len(before) == 1 and c1 > c0 and await page.evaluate("profile.grippy === false && localStorage.getItem('grasp.voice') === 'off'"), [before, c0, c1])
        await page.evaluate("__spoken.length = 0; __grasp.voice.reset(); anPlay(an.list[1], performance.now()); anAskStart(performance.now(), 'pig'); speakShape('circle'); mbSay('Puzzle'); grippySay('start')"); await page.wait_for_timeout(1300)
        check('off: names, questions, shapes, stickers: all silent', await spoken(page) == [], await spoken(page))
        await page.reload(); await wait(page, "mode === 'mouse' && gameMode === 'animals'")
        check('off survives a reload', await page.evaluate("__grasp.voice.set") == 'off')
        await page.evaluate("__grasp.voice.set = 'names'; tgDemoDone(); an.freeLeft = 99; __spoken.length = 0; __grasp.voice.reset(); anPlay(an.list[0], performance.now())"); await page.wait_for_timeout(1300)
        c0 = await page.evaluate("__cancels"); n = len(await spoken(page)); await page.evaluate("setMuted(true)")
        check('mute cancels the line in progress', n == 1 and await page.evaluate("__cancels") > c0)
        await page.evaluate("__spoken.length = 0; __grasp.voice.reset(); anPlay(an.list[2], performance.now())"); await page.wait_for_timeout(1300)
        check('muted: silent', await spoken(page) == []); await page.evaluate("setMuted(false)")
        await ctx.close()
        ctx, page, errs = await page_for(b, '/', init="localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, xpv: 2, coins: 0, xp: 0, grippy: false }));")
        check('an old profile with the voice off (grippy: false) = Off', await page.evaluate("__grasp.voice.set") == 'off')
        await ctx.close()

        # ===== 5. All: the round start speaks again (chatter, before the action) =====
        ctx, page, errs = await page_for(b, '/', init="localStorage.setItem('grasp.voice', 'all');")
        check('all: from storage', await page.evaluate("__grasp.voice.set") == 'all')
        ok = await round_start(page, 'slice'); sp = await spoken(page); lines = await page.evaluate("__grasp.grippy.lines.en.start")
        check('all: Slice\'s round start is said ("Let\'s go!" family)', ok and len(sp) == 1 and sp[0] in lines, [ok, sp])
        await page.evaluate("__grasp.voice.reset(); grippy.lastAt = -1e9; __spoken.length = 0; slice.fruits.push({ cut: false, x: 100, y: 100 }); grippySay('start')")
        check('all: never chatter during live action (fruit up)', await spoken(page) == [] and await page.evaluate("__grasp.voice.log.slice(-1)[0].why") == 'hot', await page.evaluate("__grasp.voice.log.slice(-2)"))
        await ctx.close()

        # ===== 6. the 3-way row in the More sheet, EN / HE =====
        for he in (False, True):
            lg = 'he' if he else 'en'
            ctx, page, errs = await page_for(b, '/', he=he)
            await page.evaluate("__grasp.home2.more(true)"); await page.wait_for_timeout(900)
            row = await page.evaluate("""(() => { const v = $('moreVoice'); return { label: v.querySelector('.mLb').textContent, btns: [...v.querySelectorAll('.segBtn')].map(b => { const r = b.getBoundingClientRect(); return { t: b.textContent.trim(), v: b.dataset.v, p: b.getAttribute('aria-pressed'), w: r.width, h: r.height, in: r.left >= 0 && r.right <= innerWidth }; }) }; })()""")
            want = ['שמות', 'הכול', 'כבוי'] if he else ['Names', 'All', 'Off']
            check(lg + ': the row "' + row['label'] + ': ' + ' · '.join(x['t'] for x in row['btns']) + '", Names pressed, each >= 44 px, on screen',
                  row['label'] == ('קול' if he else 'Voice') and [x['t'] for x in row['btns']] == want and [x['p'] for x in row['btns']] == ['true', 'false', 'false'] and all(x['w'] >= 44 and x['h'] >= 44 and x['in'] for x in row['btns']), row)
            await page.screenshot(path=OUT + 'voice_settings_%s.png' % lg)
            await page.tap('#voiceAll'); await page.wait_for_timeout(150)
            check(lg + ': tap All: pressed, stored, grippy on', await page.evaluate("__grasp.voice.set === 'all' && localStorage.getItem('grasp.voice') === 'all' && profile.grippy === true && $('voiceAll').getAttribute('aria-pressed') === 'true' && $('voiceNames').getAttribute('aria-pressed') === 'false'"))
            await page.tap('#voiceOff'); await page.wait_for_timeout(150)
            check(lg + ': tap Off: pressed, grippy off (the old code follows)', await page.evaluate("__grasp.voice.set === 'off' && profile.grippy === false && __grasp.grippy.on === false && $('voiceOff').getAttribute('aria-pressed') === 'true'"))
            await page.reload(); await page.wait_for_timeout(600); await page.evaluate("__grasp.home2.more(true)"); await page.wait_for_timeout(600)
            check(lg + ': Off survives a reload (the row shows it)', await page.evaluate("__grasp.voice.set === 'off' && $('voiceOff').getAttribute('aria-pressed') === 'true'"))
            await page.tap('#voiceNames'); await page.wait_for_timeout(150)
            check(lg + ': tap Names: back on', await page.evaluate("__grasp.voice.set === 'names' && profile.grippy === true && $('voiceNames').getAttribute('aria-pressed') === 'true'"))
            check(lg + ': no page errors', not errs, errs); await ctx.close()

        # ===== 7. the suites' default (no __graspVoice): the old talk =====
        ctx, page, errs = await page_for(b, '/', real=None)
        check('automation without __graspVoice: All, no timing rules (the older suites)', await page.evaluate("__grasp.voice.set === 'all' && __grasp.voice.legacy()"))
        await ctx.close()
        await b.close()
    srv.terminate()
    bad = [n for n, ok in results if not ok]
    print('\n%d checks, %d failed' % (len(results), len(bad)))
    if bad: print('FAILURES: %d' % len(bad)); sys.exit(1)
    print('ALL PASS')

asyncio.run(main())
