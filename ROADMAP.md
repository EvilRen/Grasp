# Grasp: roadmap to 9–10

Author: Maya (senior mobile game designer persona). Date: 11 Oct 2026.

Based on: a replay of the current `main` snapshot, which includes the panel fixes. Played on a 390×844 touch phone in EN and HE. Covered: first open, Strike stage 1 (9 bot runs at 3 skill levels), Frenzy, Slice (3 rounds), Smash stage 1, Sandbox, Busy Board, Shapes, Bubble Pop via the picker, and the day-2 return. Screenshots are in `scratchpad/maya/`.

The work already in progress is counted as Phase 1: the new start screen, the simpler end cards and gentler retention. The planned backlog is built in below, cut down or dropped.

Caveat: the suites and my bots run Strike with the 2D renderer. Real phones get 3D. Nothing in this document has been checked with a real hand on a real phone. That gap is itself root cause #3.

---

## 1. Where we are

### Scores by mode (my re-score, then → now)

| Mode | Then | Now | Why, in one line | "9–10" means (observable) |
|---|---|---|---|---|
| Frenzy + duel | 7 | **7** | The rally ramp is good. But a run is about 30 s, and the end card has 7 tappable things. | Median run 45–90 s. A "NEW RECORD" in at least 1 of 3 runs for a week-1 player. The card has 3 actions. A teen sends a duel without prompting. |
| Shapes | 7 | **8** | Full screen, tap-tap and huge shapes work for a 2-year-old. There is no ladder and no variety after about level 10. | A 2.5-year-old places a shape within 10 s, with no adult help. 10 minutes of play without asking to leave. A level ladder with new shape sets. |
| Strike / Adventure | 6 | **6.5** | The fingertip ring fixed occlusion and the Easy pace is faster. **But a child returning 75% of balls fails stage 1 in 20–30 s (6/6 of my runs). Only a 90% bot clears it.** The tile opens a map, not a game. The 2D corridor is a dark wireframe. | First win within 60 s of the first tap. Stages 1–3 cannot be failed. A 7-year-old clears world 1 in session 1–2. Each world looks and sounds different at a glance. |
| Smash | 6 | **6.5** | Waves no longer stick. Stage 1 took 98 s at 3 taps/s for 2★. The wall scene is a phone-sized brick texture you tap 2–5 times per brick, which feels like work, not destruction. | Something big breaks within 3 s. Every 10 s there is a chain reaction a child points at. Stage length 45–75 s for a kid. |
| Busy Board | 6 | **7** | Instruments come first and fill the width, and the scroll works. It is still a vertical list of widgets with no surprises. | A 2-year-old finds a new reaction every minute for 5 minutes. No text. No dead widget. |
| Camera games (Drums, Bubbles, Paint, Stars) | n/a | **6** | Bubbles is a good toddler toy and Calm is remembered. A camera failure shows raw `TypeError: …` text to the family (seen in HE; my camera stub caused it). The ask sheet still shows before the first bubble. | Camera on to first hit in ≤ 5 s. The hand is lost less than 5% of the time. Zero technical text. Drums and Stars work at the tracker's real rate. |
| Meta / first-time flow | 5 | **5** | First open is a gift pop-up before any play. The start screen has 23 tappable things, including a 14 px Tremorti link and 40×17 / 27×17 (HE) Easy/Normal targets. Progress is split across 6 currencies: coins, XP/level, stars, snacks, event points, stickers. Cards upsell ("Only 121 coins to the Beach ball!"). | Day 1: play before any pop-up. At most 7 tappable things on first open. One progress bar a child can explain. No upsell to anyone under 9. |
| Slice | 3 | **4** | It no longer freezes and has 5 hearts. But rounds last 22–29 s for a 60%-accurate kid, there are 1–2 fruit on a near-empty navy screen, and it is slow to learn. | 60 s rounds with 3–6 fruit always on screen. Combo moments every 5 s. A kid replays 3 times or more unprompted. |
| Sandbox | 3 | **3.5** | The toy box helps, but everything falls into a pile at the bottom of an empty dark screen. It has a text hint and no goal. | Cut (see the kill list). |

### Scores by player type

| Player | Now | Why | "9–10" means |
|---|---|---|---|
| Toddler 2–4 | **6** | Shapes, Busy and Bubbles are good. The way in is not: 23 targets, text, a pop-up, the Tremorti link, Camera/Touch toggles, Share/Duel/Shop one tap away. | Opens "Little ones" and plays 10 minutes alone. There are 5 or fewer things to tap on any screen, no text needed, no way out without the parent gate, and nothing that fails or ends badly. |
| Kid 6–9 | **6** | Strike stage 1 fails them. Slice is short and sparse. Smash grinds. Catch the Stars and Bubbles work. | First win within 60 s. Asks "can I play again?" on day 2 (the D1 proxy). Can name their pet and their favourite world. |
| Teen 12–14 | **6.5** | Bosses, Frenzy, duels and themes are real depth. The look is "kids' app" and the first hour is too easy and then gated. | Plays 20 minutes in session 1. Sends 1 or more duels or replays in week 1. Chases 3★ and records without being told to. |
| Parent | **5.5** | Daily-gift pop-up, streak flame, scarce coins and upsell lines. Tremorti sits on the kids' screen. Raw error text. No parent area. | Would recommend it to another parent. Can see play time, switch off shop, events and camera, and trusts that the camera stays on the phone. Nothing nags. |
| Camera player | **6** | Coasting and home dwell fixed the worst of it. But the camera is still a layer added on top of touch games, not the core. | Plays a 5-minute camera session without touching the phone, including menus. Under 1 hand-loss pause per minute. Every camera mode has a reason to use the camera. |

---

## 2. Gap analysis: root causes

1. **Breadth beats depth.** We have 10 games, 4 Strike sub-modes (Adventure, Endless, Frenzy, Daily) and 9 meta systems. The quality spread is 3.5 to 8. The weak modes set the average and the first impression, because a child taps a tile at random.
2. **The first minute is not designed.** First open shows a pop-up before play. The Strike tile opens a map. Stage 1 can be lost. Instructions are text, while the core audience can't read, or reads Hebrew slowly. "First win" is luck.
3. **Tuning comes from bots and suites, not hands.** HANDOFF lists more than 40 "not yet checked on a real phone" items: feel thresholds, loudness, 3D cost, tracker rate. We have shipped features faster than we have validated them.
4. **There is no art direction or world.** Strike 2D, Slice and Sandbox are a navy dot-grid. Busy, Shapes and Smash are rich and tactile. The pet lives in a corner. Nothing says "this is one game with one hero."
5. **The meta is a free-to-play playbook, not a family one.** Scarce coins, streaks, daily pop-ups, upsell lines, duels on fail cards and 6 progress currencies. That is noise for a 4–8-year-old and lowers trust for the parent.
6. **Session shapes are wrong.** Some loops are too short (Slice 20–30 s, Frenzy about 30 s). Others are grindy (Smash wall 98 s, boss fights 3–4 min for a child). Each mode needs a 45–90 s arc that ends on a high.
7. **The camera is second-class.** It is the product's unique selling point (the game is called "Grasp"), but most modes are touch-first. Camera thresholds are tuned per mode, failures show technical text, and there is no "magic" that only hands can do.
8. **A 16.8k-line single file with no performance truth.** Headless has no GPU, so cost on mid-range phones is unknown. Every change risks regressions and slows the agents.

---

## 3. The plan

Each phase is 1–2 weeks of agent work. Each ends with the playtest loop (§6). A phase ships only if no mode or player score drops.

### Phase 1: The front door and the first 60 seconds (finish the in-progress work, plus the FTUE)

**Goal:** every player type gets a win before anything else happens.

**Changes:**
- **Start screen (in progress).**
  - Hero "Play Strike" opens the next stage directly. On first launch it opens stage 1, not the map.
  - "Little ones" tile, tab bar Play / Shop / Pet / Events, and a ⋯ More sheet holding Daily, Missions, Road, Tremorti, Language and Install.
  - Hide everything until it is earned. Show one pop-up at a time.
  - **Acceptance:** at most 7 tappable things on first open (check with the `VIS` probe in `scratchpad/maya/mc.py`). Every target is at least 44×44 px, including Easy/Normal in HE. No scrolling at 360×740.
- **No pop-up before the first finished round.** The gift calendar first appears on day 2. After that it appears only after a round, never on open.
- **Stages 1–3 cannot be failed.** A miss costs a star, not a heart, using a "bumper" glow that returns the ball once per miss. Hearts start at stage 4.
  - **Acceptance:** `advSim` and my bot at skill 0.6 clear stage 1 in at most 60 s in 10/10 runs. Today 0/6 at skill 0.6–0.75.
- **Show, don't tell.**
  - Every first-time instruction becomes an animated finger plus at most 3 words. Shapes already does this; apply it to Strike's serve, Slice and Smash.
  - Each instruction is voiced in HE and EN. Pre-render the clips; don't rely on device TTS.
- **End cards (in progress).** Stars and score, Next, at most 2 secondary buttons, one Share. Share only on a record or a boss.
  - No Duel on fail cards or stages 1–3. No upsell line. The Replay pill only for moments scoring 50 or more.
- **Gentle retention (in progress).**
  - The calendar pauses and never resets.
  - No streak flame for children under 9. The flame moves into the parent area.
  - No "x coins to…" lines.
- **Errors.** No technical text anywhere a child can see it. The no-camera card says "Camera is resting, play with your finger 👆". Details go behind "More help" in the parent area.

**Moves:** meta 5→7, toddler 6→7, kid 6→7, parent 5.5→7, Strike 6.5→7.

**Risks:**
- Teens find stages 1–3 trivial. Mitigation: stars still track misses, and a "skip to stage 4" chip appears after a 3★ clear.
- Hiding features hurts discovery. Mitigation: unlock with a celebration ("New: Frenzy!").

**Verify:**
- Automated:
  - Tappable count and target size per screen, EN and HE.
  - Pop-up order on day 1 and day 2 (`__grasp.setDate`).
  - Stage 1–3 clear rate for the kid bot.
  - A grep for `Error`/`TypeError` in any visible DOM or canvas text.
- Phone (parent): hand the phone over cold. Time from tap to first "yay". Did the child need you to read anything?

### Phase 2: Fix or cut the bottom; build "Little ones"

**Goal:** no mode below 7. Toddlers get a safe walled garden.

**Changes:**
- **Little ones space.**
  - Holds Shapes, Busy Board, Bubble Pop (Calm) and Paint.
  - Big icons, no text, no coins, stars, cards or fail states.
  - Exit is behind a parent gate: hold two fingers for 3 s. The gate also stops the browser's Back gesture.
  - Volume cap. An optional "bedtime" timer set by the parent.
- **Sandbox: cut as a tile.** Its physics toys become one Busy Board widget, a "toy chute": drop toys into the box and they rattle down a ramp.
- **Slice: one-week rebuild, then decide.**
  - A 60 s timed round instead of lives.
  - 3–6 fruit always on screen. Bombs only after 20 s, and never on the first visit.
  - A combo "slow-mo" every 5 combos.
  - A bright kitchen or dojo backdrop instead of navy.
  - Juice on every cut: a splash decal that stays, plus a pitch that rises with the combo.
  - **Gate:** if the kid bot's median round is under 45 s, or the phone check scores under 7, **remove Slice** and drop Fruit Frenzy from the event rotation.
- **Smash:**
  - Front-load destruction: wave 1 of every stage is all 1-hit fragile things.
  - The wall scene's bricks take 1 hit, and a 3×3 area cracks per tap.
  - Cap stage length at 75 s for the kid sim.
  - A "mega chain" moment in every wave: a TNT barrel or a falling shelf.
- **Shapes level ladder** (parked backlog item 2): a map with 20 levels and new sets (animals, fruit, vehicles). The shape names are spoken.
- **Busy Board:** a "surprise" layer. Every 20 interactions a widget does something new (the door reveals the pet, a switch turns the lights off and stars come out).

**Moves:** Slice 4→7 (or cut), Sandbox gone (the average rises), Smash 6.5→7.5, Shapes 8→8.5, Busy 7→8, toddler 7→8.5, parent 7→8.

**Risk:** the parent gate frustrates the parent. Verify it on iOS Safari and Android Chrome.

**Verify:**
- Automated:
  - Slice sim: round length and the count of fruit on screen.
  - Smash sim: time to first break, at most 3 s.
  - Little ones: no DOM or canvas text, at most 5 targets, and every exit path requires the gate (try Back, Escape, edge swipes).
- Phone (parent): toddler alone for 10 minutes. Count the times they got "stuck" or left the space.

### Phase 3: Strike, the flagship (feel, look and one hero)

**Goal:** Strike reaches 8.5. It becomes the game's identity.

**Changes:**
- **Art direction bible.** One page of palette, lighting and shape language:
  - Toy-like, warm key light, soft rim, saturated accents per world.
  - Applied to Strike 2D and 3D, Slice, Smash backdrops, cards, the map and the start screen.
  - Replace the navy dot-grid everywhere.
  - Each world's corridor must be recognisable from a thumbnail; check it with a pixel-histogram test per world.
- **Hit feel by tier.** Each tier gets its own sound, hit-stop and camera kick: soft is a tap, SUPER is a boom. Then one tuning pass on a real phone with the ±90 ms PERFECT window.
- **Simpler for kids.**
  - On Easy: no overheat, no turrets before world 3, closing walls only from world 4.
  - Boss fights capped at 90 s for the kid sim (today 3–4 min). Hard mode keeps everything.
- **Hero and story, smaller than in the backlog.**
  - The pet is the hero, running ahead in the corridor and cheering on hits.
  - Each world's boss holds one friend captive. Beating the boss frees the friend, who joins the pet's room.
  - One wordless 3-panel cutscene per world, 8 in total, skippable, drawn in code like the bosses.
  - **Don't build** a cutscene engine, dialogue or a text story.
- **Frenzy:** the run starts at +20% speed so a skilled teen's run reaches 60–90 s of escalation. The card shows score, best and 3 buttons.
- **Merge Strike's modes:** Adventure, Frenzy, and Daily (Phase 6). Endless leaves the UI; keep the code for the suites.

**Moves:** Strike 7→8.5, Frenzy 7→8, teen 6.5→8, kid 7→8.

**Risks:**
- An art pass across a 16.8k-line file causes regressions. Mitigation: extract the art and palette tokens first (see Phase 4's file split).
- The 3D GPU cost of richer corridors. Mitigation: gate on the Phase 4 performance budget.

**Verify:**
- Automated:
  - A per-world screenshot diff.
  - Boss sim length per world.
  - A Frenzy run-length distribution for bots at 0.85 and 0.95.
- Phone: does a 13-year-old play 20 minutes? Does a 7-year-old say what the pet is doing?

### Phase 4: Phone truth (performance, audio, camera quality, split the file)

**Goal:** what we tuned in headless holds on a mid-range phone with real hands.

**Changes:**
- **Performance.**
  - Reference devices: one Galaxy A14/A15-class Android phone and one iPhone 11-class.
  - Budget: Strike 3D at 50 fps or more, with p95 frame under 25 ms. Start screen JS under 4 ms a frame. Memory under 300 MB.
  - Camera tracker at 8 scans/s or more during play.
  - Tooling:
    - A `?debug=perf` HUD (fps, p95, tracker scans/s, quality level) the parent can screenshot.
    - CI runs every mode with CDP CPU throttling ×4 as a proxy.
    - The replay ring shrinks when `deviceMemory ≤ 4`.
    - Stop the 22 start-screen CSS layers at `gfx0`.
- **Audio.**
  - One mix bus with gains per category: music, sfx, voice, crowd.
  - An offline render of every sfx with a peak and RMS band test, so nothing is more than 6 dB louder than the median.
  - Every mode has either a music bed or a deliberate silence.
  - Recorded HE and EN voice clips replace device TTS for core lines (he-IL TTS is missing on many Androids).
- **Camera quality.**
  - One shared gesture layer, with the strike, dwell and pinch thresholds defined in one place.
  - Calibrate it in a 10-second "wave hello" step on the first camera use: measure the tracker rate and the hand size, then scale the thresholds.
  - Every camera-mode screen can be controlled by hand, including cards and sheets.
- **Split `index.html`** into ES modules: core, each mode, meta, art and i18n. Keep a single-file build for Vercel. This is the enabler for Phases 5–7.

**Moves:** camera 6→8, every mode +0.5 from smoothness and sound, parent trust +0.5.

**Risks:**
- The split breaks the 43 suites. Mitigation: build output identical byte-for-byte at first, then refactor.
- The parent may not own a mid-range Android. Use BrowserStack or a borrowed phone.

**Verify:**
- Automated: the throttled-CPU frame-time suite, the loudness suite, gesture replays from recorded landmark traces.
- Phone: the perf HUD screenshots per mode, and a 5-minute camera-only session counting pauses.

### Phase 5: Hand magic and collectibles (the reasons to come back)

**Goal:** give the camera a "wow" and give kids something to collect that has a face.

**Changes:**
- **Hand magic, 3 gestures only, camera modes only:**
  - Open palm toward the camera = shield.
  - Fist, then open = fireball.
  - Two hands apart = slow-mo.
  - Touch players get the same powers as buttons that charge with play.
  - **Gate:** each gesture needs at most a 3% false-positive rate on the recorded traces before it ships.
- **Collectible friends, not 50 procedural creatures.**
  - 24 creatures: 8 hand-designed bases × 3 colour or element variants. Each has a name, a sound and a reaction in the pet room.
  - They **replace** stickers as the album entries, so no new currency is added. The 8 rescued boss friends are the "legendaries."
  - **Don't** generate them fully procedurally: kids attach to designed characters, and random ones look cheap.
- **Secrets and surprises:** one per mode, triggered by play, with no UI. Examples:
  - Hit the moon in world 6.
  - Slice a fruit 3 times in the air.
  - Tap the clock in the Smash room 5 times.
  - A secret found unlocks a creature variant.

**Moves:** camera 8→9, kid 8→9, teen 8→8.5, meta 7→8.5.

**Risk:** gesture misfires feel unfair. Keep them optional, with a cooldown and a visible "charging" ring.

### Phase 6: Content cadence and procedural content (sustain 9)

**Goal:** something new every day and every week without hand-building it.

**Changes:**
- **Daily generated stage.** It replaces today's Daily (a seeded Endless run). It is one Strike stage from `advPlan` and a date seed, with its own sticker or creature chance and a duel link.
- **Procedural Smash rooms:** a room grammar of furniture slots, materials and a chain-reaction setpiece. Free play becomes endless variety.
- **Event calendar:** keep the weekly rotation, but only feature modes that score 7 or higher. Add 4 seasonal events tied to the family's calendar (Hanukkah, Purim costumes for the pet, Pesach, summer) with pet costumes.
- **Monthly drop:** one Busy Board widget, one Smash room set and one Shapes set.
- **Don't build** "endless worlds after 64". No child reaches stage 64 for months, and the daily stage plus Frenzy already cover endless play. Revisit only if a profile reaches 48.

**Moves:** sustains 9 across week 2 and later. Meta 8.5→9.

### Phase 7: Parent trust and accessibility (lock in 9–10)

**Goal:** a parent would recommend it, and every child can play it.

**Changes:**
- **Parent area** behind the gate:
  - Play time today and this week.
  - Switches for Shop, Events, Camera, Voice and the streak.
  - Tremorti.
  - A privacy line: "The camera never leaves this phone; no ads, no purchases."
  - Export or reset the profile.
- **Accessibility:**
  - Tier colours safe for colour-blind players, with shape cues as well as colour.
  - A reduced-motion audit of every mode.
  - A left-hand camera mirror option.
  - All targets at least 44 px.
  - A large-text mode for menus.
- **Hebrew:**
  - A bidi audit of canvas strings. The HE Smash card's quote marks „הבא” render oddly.
  - Every voiced line in HE.
  - The RTL map path.
  - Numbers kept LTR everywhere.

**Moves:** parent 8→9.5, toddler 8.5→9, every mode +0.25.

---

## 4. Backlog verdicts (summary)

| Backlog item | Verdict |
|---|---|
| Hero and story | **Smaller.** The pet as hero, 8 wordless cutscenes, rescued friends (Phase 3). No dialogue or engine. |
| Collectible creatures (~50, procedural) | **Smaller and designed.** 24 that replace stickers (Phase 5). |
| Secrets and surprises | **Yes,** cheap and delightful. One per mode (Phase 5). |
| Hand magic powers | **Yes, after Phase 4.** 3 gestures, with a false-positive gate. |
| Endless worlds after 64 | **No** (for now). |
| Procedural Smash rooms | **Yes** (Phase 6). |
| Daily generated stage | **Yes.** It replaces the Daily run (Phase 6). |
| Shapes level ladder (parked) | **Yes** (Phase 2). |

## 5. Kill / cut list

- **Sandbox** as a tile. It becomes a Busy Board widget.
- **Slice**, unless the Phase 2 rebuild reaches 7. Fruit Frenzy stays out of the event rotation until it does.
- **Endless button.** Its code stays for the suites.
- **XP, player level and the Road** as a separate system. Unlocks move to star milestones on the map, so one progress bar remains. Snacks stay pet-only.
- **Ranks** (Bronze…Legend) on cards. Stars and score are enough.
- **Duel on fail cards and stages 1–3.** Share on every card. The Replay pill on low moments.
- **Upsell lines, the streak flame for children, and the gift pop-up on open.**
- **Tremorti link** on the kids' start screen. It moves to the parent area.
- **Overheat and turrets on Easy** in worlds 1–2.

---

## 6. Measurement: how we know it's 9–10 without analytics

### A. The playtest loop, every phase (about 1 day)

1. **Persona re-run.** The same 7 personas (Noa 2.5, Ari 7, Yossi 9 camera, Daniel 13, Dana parent, Maya designer, plus a "mid-range phone" persona) replay with the scripts in `scratchpad/panel*` and `scratchpad/maya`. Same device sizes, EN and HE, with screenshots.
2. **Simulated-player metrics** run in CI (table B).
3. **A 20-minute parent session on the real phone** with the kids, using checklist C.
4. **Fill in the scorecard** (D). **Gate:** no score drops. If a mode misses its phase target twice, it goes on the kill list.

### B. Automated proxies (tests and simulations)

| Metric | How | Target for 9 |
|---|---|---|
| Time to first win, from first tap | Kid bot (skill 0.6 / 0.75) from a fresh profile | ≤ 60 s, 10/10 runs |
| Stage 1–3 fail rate | `advSim` plus the bot | 0% |
| Round length per mode | Bot medians (Slice, Frenzy, Smash, bosses, Stars) | 45–90 s; bosses ≤ 90 s for a kid |
| Dead time | Longest gap with no on-screen response to input | ≤ 3 s in any mode |
| Screen load | Tappable count per screen (`VIS` probe); Little ones count; text on Little ones screens | ≤ 7 (≤ 5 in Little ones); no text needed |
| Pop-ups before first play / per session | DOM sheet log | 0 / ≤ 1 |
| Technical text visible | DOM and canvas text grep | 0 |
| Performance | ×4 CPU throttle, p95 frame | < 25 ms in every mode |
| Loudness | Offline render | Every sfx within ±6 dB of the median; peak ≤ 0.3 |
| Camera | Recorded landmark traces at 6 / 9 / 15 scans/s | Strike return ≥ 85%; gesture false positives ≤ 3%; ≤ 1 pause per minute |

### C. Phone checklist for the parent (yes/no, with notes)

- [ ] The child started playing without you reading anything to them.
- [ ] First "yay" (or a laugh) within 1 minute.
- [ ] The toddler stayed in Little ones for 10 minutes and never got out alone.
- [ ] The 7-year-old cleared a stage on the first visit.
- [ ] The next day the child asked to play again. **This is our D1 retention proxy.**
- [ ] The 13-year-old played over 15 minutes, or sent a duel or replay, unprompted.
- [ ] A 5-minute camera session without touching the phone; count the "Hand?" pauses: ___.
- [ ] No stutter you noticed; the perf HUD's p95 was ___ ms in Strike.
- [ ] Nothing was too loud; the Hebrew voice was clear.
- [ ] Nothing made you, the parent, uncomfortable: nagging, buying, strangers, the camera.

### D. Scorecard template (copy for each phase)

```
Phase: __   Date: __   Build: <commit>   Phone(s): __

| Mode / Player   | Prev | Now | Target | Evidence (metric / screenshot / quote) |
|-----------------|------|-----|--------|----------------------------------------|
| Strike          |      |     |        |                                        |
| Frenzy + duel   |      |     |        |                                        |
| Smash           |      |     |        |                                        |
| Shapes          |      |     |        |                                        |
| Busy Board      |      |     |        |                                        |
| Slice           |      |     |        |                                        |
| Camera games    |      |     |        |                                        |
| Meta / FTUE     |      |     |        |                                        |
| Toddler 2–4     |      |     |        |                                        |
| Kid 6–9         |      |     |        |                                        |
| Teen 12–14      |      |     |        |                                        |
| Parent          |      |     |        |                                        |
| Camera player   |      |     |        |                                        |
Automated (B): first win __ s | stage 1–3 fails __ | dead time __ s | max tappables __ | p95 __ ms | pop-ups __
Phone (C): __ / 10 yes   Gate passed: Y/N   Next phase changes: __
```

### Expected trajectory

| | Now | P1 | P2 | P3 | P4 | P5 | P6–7 |
|---|---|---|---|---|---|---|---|
| Mode average (shipped modes) | 6.1 | 6.5 | 7.6 | 8.1 | 8.5 | 8.8 | **9+** |
| Toddler / Kid / Teen / Parent / Camera | 6 / 6 / 6.5 / 5.5 / 6 | 7 / 7 / 6.5 / 7 / 6 | 8.5 / 7.5 / 7 / 8 / 6.5 | 8.5 / 8 / 8 / 8 / 7 | 8.5 / 8.5 / 8 / 8.5 / 8 | 8.5 / 9 / 8.5 / 8.5 / 9 | **9 / 9 / 9 / 9.5 / 9** |
