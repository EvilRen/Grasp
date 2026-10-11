## Panel E report: Ronit (casual mobile player) and Omer (core player)

Both personas played the frozen snapshot on port 8796. The server is now stopped and no project files or git were touched. Scripts and screenshots are in `/tmp/claude-0/-home-user-Grasp/7dc5511d-5343-5974-bf8f-fc1da947af43/scratchpad/panelE/` (shortened to `E/` below).

**How the play was driven:**
- **Input:** real synthetic touch, using an in-page "finger" bot for Strike, Slice, Smash and Catch.
- **Ronit:** phone 390×844, English, a fresh profile. She played as a real visitor (`navigator.webdriver` hidden), so the gift, event twists and welcome gift were all live.
- **Omer, desktop:** 1280×800 was used for screenshots only. Synthetic mouse input is unreliable for the bot, so his actual play ran on the phone viewport.

**Where I used hooks:**
1. To jump to late stages, I seeded `profile.adv` with 63 stages cleared and a mid set of upgrades (`o2.py`).
2. I used Easy for worlds 6–8, because the bot could not survive them on Normal.
3. "God mode" topped hearts back up to 2 so whole boss fights could be watched (`o4.py`, stages 56 and 64).
4. `adventure.finishTest` showed what happens after stage 64 (`o5.py`).
5. `__grasp.setDate` simulated the next day for Ronit.
6. CDP `setWebLifecycleState frozen` simulated locking the phone.

**About the bot:** it is roughly a good human. Its deaths on Normal bosses are evidence of a difficulty spike, not a precise measurement.

---

## Persona 1: Ronit, 35, casual mobile player

### "Would play again tomorrow" (1–10)

| Mode | Score | Why |
|---|---|---|
| Strike Adventure | 7 | Under 20 s from launch to the first slap, and a stage takes 20–35 s: a perfect bus loop. |
| Frenzy | 6 | Clear, and "New best" pulls you back, but a run is over in 30–50 s with nothing to come back for. |
| Daily | 3 | "Steel day": 61 s, 18 hits, **0 walls broken**. It felt like I failed at a game I didn't understand. |
| Slice | 5 | Juicy. But the second round drops from 5 to 3 hearts and ended in 25 s with a score of 18. |
| Smash stage | 5 | Satisfying crunch, but ~107 s of tapping a full-screen brick wall is long for one stop. |
| Catch the Stars | 7 | The most "my kind of game": one thumb, readable with sound off, 60 s, 3 stars. |
| Weekly event | 4 | Lovely page, but I never claimed anything, and on Monday it was all gone. |
| Shop | 4 | Six upgrades and themes, but the sound switch is hidden in here. |

### Top 3 delights
1. **Instant start.** The gift pops, then Strike tile → map → stage 1, with the first hit about 13 s after load (`E/r03_map_first.png`, `E/r11_t004.png`).
2. **The clear card is clear.** It explains the stars ("Lost 2 hearts — clear without losing a heart for ★★★"), the rank and the next goal (`E/r13_9card.png`).
3. **Catch the Stars and the event page look polished and adult-friendly** (`E/r62_stars_t040.png`, `E/r20_event_page.png`).

### Top 5 frustrations
1. **Event rewards I'd earned vanished on Monday.** Sunday: 319 points, 6 tiers reached, nothing claimed. Monday: fresh event, no coins, no sticker, no hat, and no message (`E/r20_event_page.png`, `E/r85_event_monday.png`).
2. **The game does not pause when I lock the phone or switch apps.** On resume the ball is already in flight, with no pause sheet. In the freeze test a heart was lost; the bot was paused for 2.5 s after resuming, so that heart alone isn't proof, but the missing pause is clear in the code (`E/r87_after_freeze.png`).
3. **Steel daily plus overheat.** The twist says "hit them hard", but hard hits overheat, and overheated hits only dent steel. Result: 0 of 4 walls (`E/r32_daily_t040.png`, `E/r33_daily_card.png`).
4. **Out-of-context pop-ups.** "NEW UNLOCKED! Glass walls" appears after a Slice round, and on top of the Strike fail card it blocks Try again (`E/r24_home_after_slice.png`, `E/o14_card_2.png`).
5. **No mute on the start screen.** Sound is on by default and the only toggles are in the Shop header and the pause menu (`E/r70_shop_top.png`). The start screen is also crowded and reads as a kids' app: Sandbox, Busy Board, Shapes, Tremorti and an egg (`E/r02_start_after_gift.png`).

### Quotes
- "I opened it at the bus stop and was slapping bricks before the doors closed. Love that."
- "I got a whole row of prizes on the event page and never pressed the little chests. Monday morning they're gone? That's the moment I delete an app."
- "Steel day: I hit everything, the bar went orange, nothing broke. What was I supposed to do?"
- "Half the tiles are for toddlers. I'd hide this app from people on the bus."

### What would make it Ronit's daily 5-minute habit (for adults)
- **One "Today" card on top:**
  - three short beats: one daily challenge, one event round, today's next Adventure stage;
  - one tap each;
  - a reward that fills over all three.
- **Never take earned rewards away:** auto-grant whatever is unclaimed at rollover ("While you were away: +45 coins, sticker").
- **Pause on hide, with a resume countdown.** Remember a run in progress if the app is killed.
- **A grown-up mode:** hide the toddler tiles behind "Kids corner", put a mute toggle on the start screen, and keep the voice off by default.
- **Make the daily fair for any adult:** no twist that cancels a core verb; show a par score and a "beat yesterday" line.
- **Gentle, adult notifications:** local reminders for "your daily is ready" and "the event ends tomorrow" (the PWA is already installable).

---

## Persona 2: Omer, 24, core gamer (Hades, Hollow Knight, Celeste)

### "Would play again tomorrow" (1–10)

| Mode | Score | Why |
|---|---|---|
| Strike Adventure | 6 | The core slap-and-aim feels good, and armor, keystones, turrets and closing walls add texture. But world 1 is done in ~6.5 min, and stages are 20–40 s puzzles with no build. |
| Bosses | 5 | Phases, telegraphs and weak points are real design. But every boss uses the same 4–5 attack verbs, and the late ones are HP sponges. |
| Endless | 3 | Ended at level 2 in 67 s on Normal. A legacy mode now; the Road unlocks feel random. |
| Frenzy | 5 | Good 30–40 s score attack (best 22, x2.14). There is no leaderboard beyond my own best. |
| Smash stages + bosses | 3 | Stages 12 and 20 were 3-starred on the first try in ~60 s at 5 taps/s. The boss never fights back. |

### Top 3 delights
1. **The hit system has real depth.** Tiers, aim reticle, PERFECT timing, rally speed-up, keystone collapses and weak-spot lines are a skill ceiling worth mastering (`E/o2a_12_a2_t004.png`).
2. **The boss frame is right.** Phase checkpoints refill hearts. Shields need a SUPER or PERFECT hit. Shots can be returned. The octopus' ink and tentacles and the mothership's abduct are genuinely new attacks (`E/o2a_16_a1_t040.png`, `E/o2b_56_a2_t080.png`).
3. **Each world has its own wall rule** (asteroid, force field, coral, jelly, gummy, choco), and they stack on later stages.

### Top 5 frustrations
1. **No long-form arc, and no ending.**
   - No story at all: only world and boss names.
   - Pace for a skilled player: world 1 took ~6.5 min (stages 20–35 s each) plus several boss attempts, so the 64 stages are about 1–2 hours.
   - Beating the Candy King gives "World 8 done!" with a **Next** button and "Tap Next for the next stage". There is no next stage; it drops back to the map (`E/o5_64_win4.png`, `E/o5_after64_final.png`).
2. **Builds don't combine.**
   - Run powers last one stage and there are 7 of them (`E/o11_power.png`). Upgrades are 6 flat stat bumps, at most level 3.
   - There are no synergies and no choices inside a stage.
   - Coins are starved: the whole Adventure pays about 1,100 coins (64 first clears × ~6, star chests 435, album 240), while maxing the upgrades costs ~4,800.
3. **Late bosses are sponges with a shared moveset.**
   - The Candy King has 740 HP and attacks only with `shot / shield / wall / charge`, plus a passive "sugar rush" (`BOSS_DEFS`, index.html:8128).
   - With god mode the bot needed ~336 s to take it to 14%, and ~195 s for the octopus.
   - A boss fail resets from 100% even at 4% left (`E/o18_card_3.png`).
4. **The Normal difficulty wall from world 2 on.**
   - With a mid set of upgrades the bot died on the Glass Queen twice (18–21% left), the Robot in 23–36 s and the Dragon in 19–37 s.
   - Stage 43 on Easy killed it in 13 s.
   - There is no mid setting, no assist toggle and no practice mode. The Easy/Normal switch is a 10 px pill on the Strike tile.
5. **Readability collapses in climactic moments.** Candy King phase 3 shows all at once: "Returned!", "Sugar rush!", "Blocked! +11", "Medium", "Early", a ×3 COMBO pop and confetti, with the weak point hidden behind summoned walls (`E/o4_64_phase3.png`). The same pattern shows on Lava Dragon (`E/o2a_40_a1_t015.png`) and stage 59 (`E/o2b_59_a2_t020.png`).

### Quotes
- "The slap with aim and timing is legit. I'd grind PERFECT chains."
- "I beat the final boss and the card said 'Tap Next for the next stage'. There is no next stage. That's the credits?"
- "Seven run powers that last one stage isn't a build, it's a coupon."
- "Candy King took five minutes of the same four attacks. Hollow Knight bosses are short and mean, not long and padded."

### Design spec: long-form depth that fits the existing Strike

**1. Meta progression: "The Workshop", replacing the flat stat Shop**
- **A new currency, Shards.** They drop from bosses, PERFECT streaks of 5 or more, and the first clear of each wall kind. Coins stay for cosmetics.
- **A talent tree with three branches, about 8 nodes each:**
  - **Power:** e.g. Heavy ball → "SUPER hits leave a burning brick for 2 s".
  - **Control:** e.g. Wider reach → "a curve shot on a sideways flick".
  - **Rhythm:** e.g. Perfect window → "PERFECT ×3 charges a Focus slow-mo".
- **Respec for free.** Reuse `ECONOMY.upgrades` and `upgLv()` as each node's stat hook.

**2. Run builds: turn the stage pick into a world run**
- **Powers last for the whole world, not one stage** (8 stages). Pick 1 of 3 after every stage, so a world run ends with 7 boons.
- **Two rarities**, with about 20 boons that tag-combine. Tags:
  - Fire: `rp_fire`, burn, TNT chain;
  - Split: `rp_split`, multiball, ricochet;
  - Shield: shield, return shots;
  - Tempo: rally, slow-mo, PERFECT.
- **Duo boons** when two tags are owned, e.g. "Fire + Split: split balls are fireballs".
- **Shown as cards on the map** next to the world band. A failed stage costs one boon, not the whole run.
- **Code fit:** extend `RUN_POWERS` / `runPowerStart` / `pickRunPower` and keep `adv.power` as an array.

**3. Encounter and boss variety**
- **A signature attack for every boss** that isn't shared, and remove at least one generic attack from late bosses.
  - Candy King: "Gumdrop rain" (bricks that land on your side and must be slapped away); "Taffy" that slows the ball inside a band.
  - Mothership: "Gravity well" that bends shots.
  - Dragon: "Breath sweep" that forces a lane change.
- **Tighter fights:**
  - Cut late HP so a good player wins in 90–120 s.
  - Add a stagger state: three weak-point hits in a row → a 4 s punish window, ×2 damage.
  - Keep phase checkpoints for retries ("restart from phase 2" after a fail).
- **Elite stages:** every world's stage 4 becomes a mini-boss (Turret Captain, Creep Engine, Coral Hydra) using the existing turret, creep and coral systems.
- **Wall modifiers, Hades "Heat" style:** after 64, unlock "Pact" toggles (+turret rate, −1 heart, steel everywhere, no assist) that multiply score and shards.

**4. Secrets and mastery**
- **A hidden stage per world:** break a keystone in a specific order, or clear stage 7 without missing → a hidden portal node on the map ("7½").
- **Golden challenges per stage**, shown on the node: no heat over 50%, PERFECT ×10, under 30 s. Gold medals unlock boss rematches with new patterns ("Ascended Golem").
- **World 9, "The Workshop of the Grasp":** an endgame tower that mixes all wall kinds and remixes the bosses, unlocked by 192 stars.

**5. Story at kid-safe tone, in light touches**
- A 2–3 line comic before each world and after each boss. Each boss is a corrupted "Keeper" of a world; the cow and monkey guests are the narrators.
- The final card after stage 64 is a real ending: a cutscene, then "New Game+ / Pacts unlocked". Replace the dead **Next**.
- Album pages carry lore lines, so stickers become a codex.

**6. Difficulty options**
- Easy / **Normal** / **Hard** / **Custom** (assist sliders: reach, timing window, heart count, boss HP). Move the switch onto the map's stage-start banner.
- A "practice boss phase" button on a boss node after the first attempt.

---

## Prioritized fixes and features

### P1
1. **Unclaimed event rewards auto-grant at rollover.** Where: `evEnsure()`, index.html:15355. Why: they were silently wiped for Ronit, a retention killer.
2. **Pause on `visibilitychange`, `pagehide` and `blur`.** Open the pause sheet in Strike, Slice, Smash and the camera games, and resume with a 3-2-1. Where: the handler at index.html:14507, which only resets `lastFrame` today. Why: casual players are interrupted constantly.
3. **Stage 64 ending.**
   - Replace Next with "The End / Continue" and add a finale screen plus post-game unlocks.
   - Where: the `advNext` path at index.html:9204, and the card that shows "Tap Next for the next stage".
4. **Steel daily is unwinnable for normal hits.** Turn off heat in steel dailies, or let medium hits break steel there. Where: `challengeCfg`, the `HEAT` constants and the daily mods.
5. **Queue NEW UNLOCKED (Road) cards until Home or the Endless map.** Never show them over an Adventure or Slice card. Where: `#newCard` / the Road unlock trigger.

### P2
6. **Boss rework:**
   - a signature attack per boss, Candy King first;
   - late boss HP targeting 90–120 s;
   - a stagger window;
   - restart from the last phase after a fail.
   - Where: `BOSS_DEFS` (index.html:8117–8128), `rbPickAttack`.
7. **World-long run powers with tag synergies.** Where: `RUN_POWERS` (index.html:7455).
8. **A difficulty step between Easy and Normal (or assist sliders),** visible on the stage banner. Normal's world 2+ bosses killed a strong bot repeatedly.
9. **Clutter cap in boss fights:** at most 2 floating texts at once, and the weak point always drawn on top. Where: the `addFloater` / `blockRect` layout.
10. **Start screen for adults:**
    - a mute toggle in the top bar;
    - a "Kids corner" folder for Sandbox, Busy Board and Shapes;
    - move the Tremorti link to settings.

### P3
11. **The ★ badges on tiles mix meanings:** "★ 80" (Slice best score), "★ 3" (Smash stars), "★ 355 · L1" (daily best). Use distinct icons.
12. **Smash late stages have no fail pressure** (3★ first try). Add boss attacks (falling debris to swipe away) or a combo meter.
13. **Slice:** the drop from 5 hearts to 3 between rounds is jarring. Keep 5 for the session, or explain it.
14. **Economy:** Adventure pays about 1,100 coins against a ~4,800 upgrade tree. Pay coins for 3★ replays or medals, or move power to a shard currency.
15. **A "+1" floater sits on top of the hearts pill** in boss fights (`E/o2a_48_a2_t040.png`, `E/o2a_40_a1_t015.png`).

---

## Bugs with repro steps

1. **Event rewards lost at week rollover**
   - Repro: reach several tiers on Sunday without opening chests → `__grasp.setDate('<next Monday>')` → reload.
   - Result: `profile.event` is reset and `evx` stays empty; there's no grant and no notice.
   - Evidence: `r4.py`, `q.py`; the earlier claimable list was `[0..5]`.
2. **No auto-pause when the app is hidden or frozen**
   - Repro: Strike stage, ball in flight → CDP `Page.setWebLifecycleState frozen` for 5 s → `active`.
   - Result: `menu.open` is false, play continues and a heart is lost (`E/r87_after_freeze.png`). Only `index.html:14507` reacts to visibility.
3. **Dead "Next" after the final boss**
   - Repro: clear stage 64.
   - Result: the card offers Next and says "Tap Next for the next stage"; Next only opens the map (`E/o5_64_win4.png`).
4. **Road "NEW UNLOCKED" modal blocks Adventure and Slice cards**
   - Repro: fresh profile → play Slice twice (Lv 2) → the Home/start screen shows "Glass walls" unlocked (`E/r24_home_after_slice.png`).
   - Also: on a Strike fail card it covers Try again until dismissed (`E/o14_card_2.png`).
   - Also: after the world-7 boss it shows "Steel walls", which the Adventure had used for many stages already (`E/o4_56_end.png`).
5. **Steel daily: 0 walls in 61 s with 18 hits** (casual bot, 2026-10-11 "Steel day")
   - The heat bar was orange throughout (`E/r32_daily_t040.png`).
6. **Boss card shows "Best 0 · Bronze at 0"** when a boss stage's score is 0 (seen via `finishTest`; low priority, partly a hook artifact) (`E/o5_64_win4.png`).
7. **Smash city scene shows two suns** behind the robot boss (already in the backlog, still present) (`E/o41_smash12_t040.png`).

Not product bugs: synthetic mouse `pointerdown` throws a harmless `setPointerCapture` NotFoundError (headless artifact). No other page errors came up in any session.
