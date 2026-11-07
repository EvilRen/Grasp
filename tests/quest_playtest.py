"""Let players loose on Quest: bots that tap the real buttons in the real page, for as long as you like.

They play through doors, fights, shops, camps, events, chests, the deck, the map and the menu, in both
languages and on two screen sizes, and they watch for the things a balance simulator cannot see:
  * any error the page throws, in any screen
  * a screen with nothing to press (a dead end)
  * a button drawn where a finger cannot reach it (off the screen, or under its bottom edge)
  * a button too small to hit
  * which screens were never reached at all
python3 playtest.py [actions-per-bot]
"""
import asyncio, sys, random, collections
from playwright.async_api import async_playwright

N = int(sys.argv[1]) if len(sys.argv) > 1 else 900
BOTS = [('en', 390, 844), ('he', 390, 844), ('en', 360, 640), ('he', 414, 896)]

SETUP = """(() => { const q = __grasp.quest, P = q.profile(); P.howto = 1; P.tut = 1; P.heroes = ['knight','wizard','robot'];
  q.quest.howto = null; return 1; })()"""

STATE = """(() => { const Q = __grasp.quest.quest, QC = __grasp.quest.QC, f = Q.f;
  return { scr: Q.scr, over: f ? f.over : null, run: !!Q.run, menu: !!Q.menuOpen, deck: !!Q.deckFor,
           map: !!Q.mapOpen, howto: !!Q.howto, sel: Q.sel, en: f ? f.en : 0,
           hand: f ? f.hand.map((id) => QC.cardOf(id).c) : [],
           mons: f ? f.mons.filter((m) => m.hp > 0 && m._x != null).map((m) => ({ x: m._x, y: m._y })) : [],
           btns: __grasp.quest.btns().map(b => ({ x: b.x, y: b.y, w: b.w, h: b.h, card: b.card == null ? null : b.card })) }; })()"""

async def run_bot(browser, lang, W, H, n, report):
    ctx = await browser.new_context(viewport={'width': W, 'height': H}, device_scale_factor=1, is_mobile=True, has_touch=True)
    page = await ctx.new_page()
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(f"localStorage.setItem('lang','{lang}');")
    await page.goto('http://localhost:8765/quest')
    await page.wait_for_timeout(1500)
    await page.evaluate(SETUP)
    rnd = random.Random(hash((lang, W, H)) & 0xffff)
    seen = collections.Counter()
    bad = []
    runs = 0
    last_key = None; stuck = 0
    for step in range(n):
        try:
            st = await page.evaluate(STATE)
        except Exception as e:
            bad.append(('state', str(e)[:120])); break
        key = 'menu' if st['menu'] else 'deck' if st['deck'] else 'map' if st['map'] else st['scr']
        seen[key] += 1
        bs = st['btns']
        if not bs:
            bad.append(('dead end: nothing to press', key, f"step {step}"))
            await page.evaluate("(()=>{const q=__grasp.quest; q.quest.run=null; q.quest.scr='pick';})()")
            continue
        for b in bs:                                   # a finger has to be able to reach it
            if b['x'] + b['w'] <= 0 or b['x'] >= W or b['y'] + b['h'] <= 4 or b['y'] >= H:
                bad.append(('button off the screen', key, {k: round(b[k]) for k in 'xywh'}))
            elif b['y'] + b['h'] > H + 1 and b['card'] is None:
                bad.append(('button runs past the bottom', key, {k: round(b[k]) for k in 'xywh'}))
            elif (b['w'] < 24 or b['h'] < 24) and b['card'] is None:
                bad.append(('button too small', key, {k: round(b[k]) for k in 'xywh'}))
        # who to tap. An overlay is looked at and then closed; a fight is actually played, card at monster,
        # so that runs finish and the screens past the first fight are reached at all.
        if key == last_key and key in ('menu', 'deck', 'map'):
            stuck += 1
        else:
            stuck = 0
        last_key = key
        pt = None
        if stuck > 3:
            await page.evaluate("(()=>{const Q=__grasp.quest.quest; Q.menuOpen=false; Q.deckFor=null; Q.mapOpen=false;})()")
            stuck = 0
            continue
        if key == 'fight' and st['mons'] and rnd.random() < 0.88:
            if st['sel'] is not None and st['sel'] >= 0:
                m = rnd.choice(st['mons']); pt = (m['x'], m['y'])
            else:
                cards = [b for b in bs if b['card'] is not None]
                ok = [b for b in cards if b['card'] < len(st['hand']) and st['hand'][b['card']] <= st['en']]
                if ok: tgt = rnd.choice(ok)
                else:
                    low = [b for b in bs if b['card'] is None and b['y'] > H * 0.78]
                    tgt = rnd.choice(low) if low else rnd.choice(bs)
        elif key == 'pick':
            tgt = bs[min(len(bs) - 1, rnd.randrange(len(bs)))]
        else:
            tgt = rnd.choice(bs[:-1] if len(bs) > 1 else bs)
        if pt is None:
            pt = (tgt['x'] + tgt['w'] / 2, tgt['y'] + tgt['h'] / 2)
        x = min(W - 2, max(2, pt[0])); y = min(H - 2, max(2, pt[1]))
        try:
            await page.mouse.click(x, y)
        except Exception as e:
            bad.append(('click', str(e)[:120]))
        await page.wait_for_timeout(45)
        # left the quest, or the run ended: start another one
        gm = await page.evaluate("gameMode + '|' + (__grasp.quest.quest.run ? 1 : 0) + '|' + __grasp.quest.quest.scr")
        mode, has_run, scr = gm.split('|')
        if mode != 'quest' or (scr == 'pick' and step % 7 == 0):
            runs += 1
            await page.goto('http://localhost:8765/quest'); await page.wait_for_timeout(900)
            await page.evaluate(SETUP)
            await page.evaluate("(()=>{const q=__grasp.quest; const h=['knight','wizard','robot'][%d]; q.newRun(h, ['short','normal','epic'][%d]); })()" % (rnd.randrange(3), rnd.randrange(3)))
            await page.wait_for_timeout(250)
    report.append({'bot': f'{lang} {W}x{H}', 'errors': errs, 'bad': bad, 'seen': dict(seen), 'restarts': runs})
    await ctx.close()

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--no-sandbox'])
        report = []
        await asyncio.gather(*[run_bot(b, l, w, h, N, report) for (l, w, h) in BOTS])
        await b.close()
    allseen = collections.Counter()
    print('=' * 70)
    for r in report:
        allseen.update(r['seen'])
        print(f"\n--- {r['bot']}  ({sum(r['seen'].values())} taps, {r['restarts']} fresh runs)")
        print('   screens:', ', '.join(f'{k}×{v}' for k, v in sorted(r['seen'].items(), key=lambda x: -x[1])))
        if r['errors']:
            print('   PAGE ERRORS:', len(r['errors']))
            for e in list(dict.fromkeys(r['errors']))[:5]: print('     !', e[:160])
        seenbad = collections.Counter(str(x[:2]) for x in r['bad'])
        if seenbad:
            print('   problems:')
            for k, v in seenbad.most_common(8): print(f'     × {v:4d}  {k}')
        if not r['errors'] and not r['bad']: print('   clean')
    want = {'pick', 'doors', 'fight', 'reward', 'rest', 'shop', 'event', 'chest', 'end', 'deck', 'map', 'menu'}
    print('\nnever reached:', ', '.join(sorted(want - set(allseen))) or 'nothing — every screen was played')
asyncio.run(main())
