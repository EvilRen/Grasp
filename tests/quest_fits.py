"""Every screen in Quest, on every phone shape, measured: does anything a finger needs fall off the edge?"""
import asyncio, sys
from playwright.async_api import async_playwright

SIZES = [(320, 568), (360, 560), (360, 640), (375, 667), (390, 844), (414, 896), (430, 932)]
SET = {
 'pick':   "(()=>{const q=__grasp.quest; q.quest.run=null; q.quest.scr='pick';})()",
 'doors':  "(()=>{const q=__grasp.quest; q.newRun('knight','epic');})()",
 'fight':  "(()=>{const q=__grasp.quest; q.newRun('wizard','epic'); q.enter('fight');})()",
 'boss':   "(()=>{const q=__grasp.quest; q.newRun('robot','epic'); q.enter('boss');})()",
 'shop':   "(()=>{const q=__grasp.quest; q.newRun('knight','epic'); q.quest.run.gold=999; q.enter('shop');})()",
 'rest':   "(()=>{const q=__grasp.quest; q.newRun('knight','epic'); q.enter('rest');})()",
 'event':  "(()=>{const q=__grasp.quest; q.newRun('knight','epic'); q.enter('event');})()",
 'chest':  "(()=>{const q=__grasp.quest; q.newRun('knight','epic'); q.enter('chest');})()",
 'reward': "(()=>{const q=__grasp.quest; q.newRun('knight','epic'); q.quest.scr='reward'; q.quest.data={gold:30, relic:'heart', cards:['strike','bash','cleave']};})()",
 'end':    "(()=>{const q=__grasp.quest; q.newRun('knight','epic'); const Q=q.quest; Q.f=null; Q.scr='end'; Q.end={won:true,fights:12,bosses:3,coins:148,hero:'knight'}; Q.newHero=1;})()",
 'deck':   "(()=>{const q=__grasp.quest; q.newRun('knight','epic'); for(let i=0;i<14;i++) q.quest.run.deck.push('strike'); q.quest.deckFor={k:'view'};})()",
 'map':    "(()=>{const q=__grasp.quest; q.newRun('knight','epic'); q.quest.mapOpen=true;})()",
 'menu':   "(()=>{const q=__grasp.quest; q.newRun('knight','epic'); q.quest.menuOpen=true;})()",
 'howto':  "(()=>{const q=__grasp.quest; q.quest.howto={p:0};})()",
}
async def main():
    async with async_playwright() as pw:
        br = await pw.chromium.launch(args=['--no-sandbox'])
        bad = 0
        for lang in ('en', 'he'):
            for (W, H) in SIZES:
                ctx = await br.new_context(viewport={'width': W, 'height': H}, device_scale_factor=1, is_mobile=True, has_touch=True)
                page = await ctx.new_page(); errs = []
                page.on('pageerror', lambda e: errs.append(str(e)))
                await page.add_init_script(f"localStorage.setItem('lang','{lang}');")
                await page.goto('http://localhost:8765/quest'); await page.wait_for_timeout(1300)
                await page.evaluate("(()=>{const P=__grasp.quest.profile(); P.howto=1; P.tut=1; P.heroes=['knight','wizard','robot']; __grasp.quest.quest.howto=null;})()")
                for name, js in SET.items():
                    await page.evaluate("(()=>{const Q=__grasp.quest.quest; Q.menuOpen=false; Q.deckFor=null; Q.mapOpen=false; Q.howto=null;})()")
                    await page.evaluate(js); await page.wait_for_timeout(260)
                    st = await page.evaluate("(()=>({b:__grasp.quest.btns().map(b=>[Math.round(b.x),Math.round(b.y),Math.round(b.w),Math.round(b.h),b.card==null?0:1])}))()")
                    bs = st['b']
                    if not bs:
                        print(f'  {lang} {W}x{H} {name:7s} NOTHING TO PRESS'); bad += 1; continue
                    out = [b for b in bs if not b[4] and (b[1] + b[3] > H + 1 or b[1] < -1 or b[0] < -1 or b[0] + b[2] > W + 1)]
                    tiny = [b for b in bs if not b[4] and (b[2] < 24 or b[3] < 24)]
                    if out or tiny:
                        bad += 1
                        print(f'  {lang} {W}x{H} {name:7s} off:{len(out)} tiny:{len(tiny)}  {(out + tiny)[:3]}')
                if errs: print(f'  {lang} {W}x{H} PAGE ERRORS {errs[:2]}'); bad += 1
                await ctx.close()
        print('\n' + ('all clean: every screen fits every phone' if not bad else f'{bad} screens with something out of reach'))
        await br.close()
asyncio.run(main())
