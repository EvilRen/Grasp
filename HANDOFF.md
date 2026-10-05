# Grasp: handoff for a new conversation

Read this first, then NOTES.md (deploy, phone findings) and DESIGN.md (game design research and decisions).

## The project
- **Grasp:** a hand-gesture browser game for a parent and a young child. They speak Hebrew and play on a phone.
  - The whole game is one file: `index.html`, about 10,400 lines.
  - Live: https://grasp-weld.vercel.app/ (Tremorti, a tremor meter, is at `/tremorti/`).
  - Repo `evilren/grasp`. Vercel deploys `main` automatically on every push.
- **Stack:**
  - Canvas 2D, plus a three.js r128 WebGL renderer for Strike (falls back to 2D on its own).
  - Matter.js and MediaPipe hands (CPU tracker on phones).
  - Sound effects and music generated with Web Audio.
  - `t()` for translation, English and Hebrew, with right-to-left layout.
  - Profile in localStorage, where every access is in try/catch and every field is validated on load.
  - Seeded random numbers: `strikeRand(channel)`.
  - Test hooks on `window.__grasp`.

## Games (start screen: one grid of 6 tiles, tap = play)
Sandbox, Slice (katana), Smash (five scenes to smash, free play + stages), Busy Board (toddler widgets), Strike, Shapes (shape sorter with levels, colours and spoken names).

**Strike** is the main game: a 3D corridor where you slap a ball into walls of bricks.
- **The Strike tile:** opens the **Adventure** saga map.
  - 40 stages: 5 worlds × 8, the 8th stage of each world a boss.
  - Break **all** walls to clear a stage; 3 hearts; stars: 3 = no heart lost, 2 = one lost, 1 = more.
  - The stage start banner has a small line "★★★ = don't lose a heart"; the clear card has a line under the stars ("Lost 1 heart — clear without losing a heart for ★★★", or "Perfect — no hearts lost!").
  - Clear card: Next / **Play again** / Map. Fail card ("So close!"): **Try again** / Map. Success cards say "Play again" (HE "לשחק שוב"), only a fail says "Try again" (HE "שוב").
  - Portal travel to the next world after a boss.
  - Stored in `profile.adv`.
- **Endless:** the old run, behind a button on the map. It has lives, levels, worlds, perks and a "road" of unlocks by player level (`ROAD`).
- **Animals:** the cow from road level 1 (and from Adventure stage 2), animals every 4–6 serves from run level 2. The monkey unlocks at player level 7.
- **Serve (pull back, then flick):** the ball waits (`strike.waiting`; round start, level start, after a miss; Adventure, Endless, Daily) and follows the hand / finger / mouse (x within the middle 60%, a little of y, kept low above the meter), "Pull back, then flick!" / "משכו אחורה וזרקו קדימה!".
  - A tap does nothing and a swipe through the ball does not serve (player feedback: "no matter where I tap, the ball fires").
  - Launch: the pointer / hand moves **down** ≥ 6% of the screen height (`PULL_MIN`, within 1.5 s; a ring closes round the ball, a band to the finger, then "Now flick it up!" with rising arrows), then a fast **flick up** (gate `FLICK_GATE` 0.35 px/ms screen-scaled). It launches at the flick's peak; power = peak speed → the usual tiers (`speedTier`) and the hit-meter pop; a gentle sideways aim (≤ `AIM_MAX`). A slow drift back up un-arms it; a flick with no pull-back does nothing.
  - Touch: while the finger is down (lifting at the end of the flick still serves; a new touch restarts the pull). Mouse: with or without the button. Camera: the hand (raw tracker samples count for the flick speed).
  - Code: `pullTick` / `waitTick` / `playerServe(force, now, aim)` (force: a tier or a speed); hooks `strike.pull`, `strike.lastServe { tier, v, aim, flick }`, `strike.ui.serve { charge, armed, text }`; `playerServe(power)` stays the test hook. First serve ever: the one-time tip `tipFlick` (`tipOnce('flick')`).
- **In-game screen (minimal):** one round pause button in the top corner (tap, Escape or a camera dwell) opens a sheet: Resume, Restart, Sound, Language, Stats, Home. The HUD is one slim row: hearts + a walls pill (Adventure: walls broken / stage walls; Endless: walls toward the next level). No score, progress line, NEXT card, streak chip, perk badges or bottom power bar.
- **Hit meter:** never on screen permanently. On a hit (or serve) a small power arc pops up just above the hit point, fills to the hit's power in the tier colour (soft / medium / hard / SUPER, `METER_ZONES`, `speedTier`, `TIER_COL`) with the tier's name, and fades within 1 s (`METER_POP_MS`, `drawMeterPop`, hook `strike.ui.meterPop`). Same in 2D and 3D (it is drawn on the 2D overlay).
- **v4 "challenge" (playtest: "hitting hardest just breaks all the walls", a 13-year-old was not excited):** see DESIGN.md "v4: challenge".
  - **Bounded blast, always a bounce:** the hit ball meets ONE wall and comes back off it (never through, never a second wall a flight). What breaks (`BLAST`, `blastTargets`, `smashWall` → `hurtBrick` / `breakBrick`): soft = a chip (1 dmg, 1 brick), medium = the brick (2) + a neighbour on the ball's side (1), hard = a plus (2 / 1), SUPER = the 3x3 (3 / 2), fireball = a radius-2 diamond (3, steel too). Glass: 3x3 on any hit; steel (`STEEL_DMG`): dents under soft / medium. A hole still lets the ball through (clean, or clipping its edges). A wall down to its last quarter collapses (`maybeCollapse`, `COLLAPSE_AT`). SUPER / fireball impact: an 80 ms hit-stop (`strike.stopUntil`), shake by bricks broken.
  - **Aim:** `slapLaunch` → `aimBall`: the hit's direction (contact offset + hand motion; a serve's flick) picks a landing point on the wall ahead (`AIM_SPREAD`), lateral speed solved so it lands there (spin curve included); a dashed reticle on that wall (`drawChallengeFx`, `ui.aimMarks`).
  - **Special bricks** (`specialBricks`, from `challengeCfg()`: an Adventure stage's plan, Endless by level, nothing with `extrasOff` / the test flag `strike.noSpecials`): plain bricks 1 hp; **armored** (2-3 hp, `k.max`, crack levels `crackLevel`, an 'armor' tock per level), **weak spot** (glowing cyan: breaks its row + column, `strike.cracks` crack lines), **keystone** (bottom half: what rests on it, one column each side, comes down), **gold** (+25 x combo), **turret** (red eye, 2 hp: shoots back). 2D overlays drawn over the fog (`specialBrickSprite`); 3D as icon planes in `g3BuildWall`.
  - **Overheat** (`HEAT`, `heatHit`, `heatTick`, `overheated`): hard +0.28 / SUPER +0.45, medium -0.12 / soft -0.3, time -0.06/s; full = 3 s of forced-soft hits, steam, sizzle, 'Overheat!' (tip `tipHeat`, voice 'overheat'); a slim heat bar under the HUD pill only while warm (`ui.heatBar`). No heat with `extrasOff`.
  - **Turrets** (`turretTick`, `fireShot`, `deflectShot`, `shotHits`, `strike.shots`): a slow shot at the near plane every `turretMs`; slapped = it flies back and chips its turret (+5, combo grows); missed = a heart. **Walls closing in** (`creep`, `w.cz`, `crushWall`, `CRUSH_Z`): the front wall creeps while the ball is in play; at the player: a heart, shoved back (red frame / vignette past a quarter, `creepDanger`). **Two-ball stages** (`plan.balls`): every ball missed costs a heart.
  - **Adventure ramp** (`advPlan`): walls 4..8 (`[4,4,5,6,6][w] + (i-1)/3`), stages 1-4 gentle (`paceK` 0.9, `reachK` 1.08, 2 weak spots, no armor); then `paceK` 1.1-1.38, `reachK` 0.93-0.82, `gapK` 0.9-0.75, `magK` 0.5 (applied by `advK()`), armor from stage 5 (hp 2, 3 from world 3), turrets from stage 10, closing walls from 12, two balls on some world 3+ stages. Stars unchanged (3 = no heart lost).
  - **Combo** (`comboMul`, `COMBO_STEP` 3, `COMBO_MAX` 8; `streakMul()` returns it): every point x the combo; a pop by the walls pill when it changes (`ui.comboPop`, `ui.comboBox`), a grey x1 on a miss. The old streak toast is no longer drawn (state, sound and voice kept).
  - **Score chase:** the clear card shows the score, its **rank** (`RANKS` Bronze / Silver / Gold / Diamond / Legend at `RANK_K` x the stage's par `stagePar(n)`), and NEW RECORD! (beating a previous best: 'record' fanfare + voice) or the best + the next rank's score. `profile.adv.best[n]` (validated on load). The map: a rank gem on each cleared stop (`.anode .rk`), the overall rank chip in the footer (`#advRank`, `overallRank()`). Endless' card: best combo = `strike.bestMul`.
- **v5 "addictive":** see DESIGN.md "v5: addictive". Code: the block `v5 (addictive)` before the turrets.
  - **Perfect timing:** `TIMING`, `hitZone`, `timingWin`, `judgeTiming(err, sp, winMs)` (pure), `hitTiming(b, now)` (ballTick), `serveTiming(armedAt, now)` (waitTick), `timingFx`; `strikeHit(b, now, force, tm)` / `slapLaunch(..., tm)` / `playerServe(..., tm)`; ring `drawTimingRing` (`ui.timingRing`). State: `perfStreak`, `bestPerf`, `perfects`, `timings`, `lastTiming`. Test flag `strike.noTiming` (test_serve sets it; extrasOff also off).
  - **Juice:** `JUICE`, `juiceImpact` (from smashWall: `strike.juice`, `juiceLog`), `spawnChunk` (+ `g3Shatter(..., boost)`), `wallFlashFx`, `stageSlowmo` + `camPush` (in `proj` and the 3D camera), `drawJuiceFx`, sfx `perfect` / `thump`. `reducedMotion()` (matchMedia or `strike.reducedMotion`) also scales `shakeScreen` everywhere.
  - **Floaters:** always `addFloater(f)` (never `strike.floaters.push`); no small per-brick / per-hit "+n" pops any more (clutter; WALL +n, BOSS +n, GOLD, PERFECT, combo and record stay); `tickStrikeFloaters`, `drawStrikeFloaters` (after the banners), `blockRect(name, r)` for anything text-like on the overlay (`ui.blocks` per frame), `ui.floaterRects`, `strike.floatLog`. The spotlight waits for banners.
  - **Upgrades:** `ECONOMY.upgrades`, `profile.upg` (validated), `upgLv` (0 in the daily / `strike.noUpgrades`), `buyUpgrade`, `renderUpgrades` (`#cpower`, `#upgs .upg`), `upgStats()`.
  - **Run powers:** `RUN_POWERS`, `openRunPick` from `advNext` (`runPickDue`), the perk cards with `strike.perkMode === 'run'`, `pickRunPower`, `runPowerStart` (resetStrike), `adv.power` / `adv.pendingPower` (hooks `__grasp.adventure.power / pendingPower`), shield in `loseLife`, combo keeper in `streakReset`, `splitBall`, badge `drawRunBadge`. Test flag `strike.noRunPick`.
- **Rally + Frenzy ("faster and faster", parent: "maybe a mode where every hit makes the ball faster and faster"):** see DESIGN.md "Rally and Frenzy". Code: the block `the rally` before `PACE_UP_EVERY`.
  - **Rally (Adventure, Endless, daily):** `RALLY`, `strike.rally` (returns since the last miss), `rallyK()` (x speed: +5% a return, cap `rallyCap()`: +70%, world 1's gentle stages +45%, Endless on Easy +60%), folded into `speedMul()` (so the ball, the aim and the timing window all follow it); `rallyUp` (in `strikeHit`; replaces the old every-5-returns `paceUp` while on), `rallyMiss` (in `strikeMiss`: back to x1). Points x `rallyPtsMul` (1 + 0.5 x the speed-up) on top of the combo (`scorePts`); power: `slapLaunch` gives a chance `0.6 x (k-1)` (max 50%) of one tier more (`q.boost`, never past SUPER), heat counts the hand's own tier (`q.heatTier`) and a hard hit heats / k; reach x `rallyReach()`. Visuals: `drawRallyFx` (overlay, 2D + 3D: speed lines, the ball's glow + heat trail, embers when blazing; colour `rallyCol(rallyHeat(k))` white -> yellow -> orange -> blazing; `ui.rally`), sfx `rally` (pitch x k), the pop `drawSpeedPop` ("x1.4 SPEED" every +20%, "MAX SPEED!" at the cap, grey on a lost rally; `ui.speedPop` / `ui.speedBox`, beside the HUD pill or under it / the combo pop). Off with `extrasOff` and the test flag `strike.noRally` (test_challenge's helpers set it unless a suite sets `NO_RALLY = False`).
  - **Frenzy (טירוף):** the map footer's `#advFrenzy` (its best under it, `#advFrenzySub`) and `/frenzy` (`ROUTE_MODES` has 'frenzy'; `routeNow()` says 'frenzy' while it plays; vercel.json rewrites it). `frenzy { on, armed, result }`, `strikeFrenzy(how)`, armed into `startGame`. An Endless level-1 run with: 1 heart + `strike.shield` 1 (the first miss: the rally halves), the uncapped rally (+4% a hit), clean walls (`challengeCfg` = none), no heat, no upgrades, no tickets, no levels / boss (`wallCleared`); the HUD pill = hits (⚡n), a cyan ring on the heart while shielded; `frenzyOver` (from `loseLife`): `profile.frenzy { best, top, runs }` (validated), NEW RECORD! (sfx + voice 'record'), the end card (`drawEndCard` with `title`, `share`), Share = `frenzyShareText()` / `shareFrenzy()` (`shareText0`). Hooks `__grasp.rally`, `__grasp.frenzy`.

**Smash** (rebuilt; player feedback: "it's a bit poor, allow smashing much more"):
- **Tile:** opens the **Smash map** (`#smashMap`): a big **Free play** button, then 20 stages in 5 scene groups (4 each, stars, locks). `/smash` opens the map too.
- **Scenes** (all drawn in code, `SM_BUILD` / `SM_ART` / `SM_BG`; every thing = one Matter body, kinds in `SMK`, materials in `SMM`): `wall` (a full-screen brick wall; behind it a room with its own tiled wall; behind that a treasure cave: layers 0 / 1 / 2, front first), `room` (window, frames, clock, ceiling lamps, shelves with jars / plants / books / bottles, table with plates and cups, TV on a cabinet, vase, floor lamp), `city` (buildings of stacked floors that collapse floor by floor, cars driving round, street lamps, a tree, a water tower, a hydrant), `blocks` (lettered toy towers, balloons, surprise boxes with confetti and toys), `food` (watermelons, pumpkins, tomatoes, oranges, apples on crates; shelves of eggs and bottles; juice splats painted on the scene).
- Each thing breaks its own way (debris, juice, sparks, sound: glass / clink / spark / pop / splat / confetti / crunch / wood / splash / clack...). Fragile things break when they fall or are knocked hard (`fr`, chain reactions: a shelf drops its jars, a building collapses floor by floor, the tower's tank bursts). Wall tiles are grid data drawn into one canvas each (`smTileWall`), cleared cell by cell.
- **Input:** a tap = a punch at that point; a swipe = a sweep along the path (strength by speed, `smStrength`); camera: any contact of the hand (a resting hand knocks every 220 ms).
- **v3 "it ends far too fast"** (parent on a phone: "I finished every stage in one to two seconds"; v2 had been tuned with a bot): see DESIGN.md "Smash v3".
  - **Tough things:** `SMK.hp` 2-5 (glass / china 2, furniture 4, floors 4-5 by variant, melons / pumpkins 5; eggs, books, balloons, bulbs 1). `smHit` → `smDamage(o, dmg, ..., fall)`: `o.hits`, cracks by stage `smCrackLv` (1..4, sprite `smCrackSprite(o, lv)`: the same branches growing; lv 0 = hairline), a wobble + squash (`smDrawObj`), sfx `smcrack` (arg = stage: deeper each hit); only the last hit breaks. Wall cells: `T.hp` / `T.chp` (bricks 2, glazed tiles 1), cracks drawn once into the wall's canvas (`smTileCrack`), tap radius `cw * (0.8 + 0.4k)`.
  - **One hit per swipe:** a hit id (`smNewId`, `smash.pidSeq`); a swipe is one stroke id (`smash.strokeId`, kept through short speed dips; the camera renews it every 700 ms) so a swipe hits each thing / cell once (`T.st`). Taps: a new id each.
  - **Weak chains:** `smImpacts` queues every fragile thing in a hard knock; `smDamage(..., fall=true)`: one hit's worth, ≥ 600 ms apart, and never the end of a thing not yet cracked (an uncracked jar falling off a broken shelf cracks; a cracked one shatters). Debris never touches things (mask).
  - **Waves + scroll:** `smash.waves` (stage: `SMASH_WAVES` 3/4/4/5, the wall `SMASH_WAVES_AT` 3/3/4/4; free play 3, then 4 from the 2nd lap), `smBuildWave(w)` (seeded per wave, fuller later: `smWaveV`), the wave's meter `smMeter` (this wave's things / walls only). At `SMASH_CLEAR` (0.85) `smScrollStart`: the next wave (or the boss) is built a screen to the right, everything sleeps and rides along (`smScrollTick`, `SMASH_SCROLL_MS` 1100; backdrop pans mirrored `smash.bgX`; splats slide), leftovers are removed at `smScrollEnd`; tag "Onward! 2/3". Wall scene: the treasure only on its last wave.
  - **Tension:** later waves arrive with hairline cracks (`o.hair`) and a tremble (`o.tremAt`); during a wave `smTensionTick` cracks + trembles an untouched thing every 1.2-3.2 s (cosmetic).
  - **Boss** (`SM_BOSS`: wall safe, room TV, city robot, blocks crowned block tower, food melon; art `SM_BOSS_ART` + `smFace`): `smBuildBoss`, hp `SMASH_BOSS_HP` 50/55/60/60 (free play 50); `smBossHit`: tap 1, fast swipe 2, very fast 3; phases at 2/3 (pieces fall off, holes `smBossHoleSprite`) and 1/3 (shakes, red glow); `smBossDown` → phase 'boom' (clock stopped, `SMASH_BOSS_MS`) → `smClear` ('Smashed!', coins / stars). Health bar under the HUD pill (`drawSmashBossBar`, `ui.bossBar`), voice `smashBoss` on arrival.
  - **HUD:** the pill's bar is now the progress track (`smProgress`: waves, then the boss; a dot per wave end, a crown at the end; `ui.trackBox`, alias `ui.meterBox`).
  - **Clocks:** `SMASH_CLOCK` per stage (85-165 s) ≈ 1.3 × a simulated child; stars ★★★ ≥ 40% left, ★★ ≥ 15% (`SMASH_STAR3/2`).
  - **Simulated player** (test-only, `__grasp.sm.sim({ player: 'kid' | 'good', seed, maxS, noClock })`, `smSim`): steps the real logic and Matter on a virtual clock, nothing drawn. Kid: ~3 actions/s, a fifth swipes, 60% of taps aimed (wobbly), the rest at empty spots; good: 5 accurate taps/s. Measured on a phone (child / good, s): stage 1 ~95 / 60, 4 ~110 / 80, 5 ~64 / 32, 9 ~72 / 36, 12 ~127 / 70, 13 ~65 / 33, 17 ~81 / 37, 20 ~116 / 61; free play's first scene ~90.
- **Screen:** the pause button + sheet as in Strike (`minChrome` for Smash too); HUD = one pill: the progress track (stages: + clock + stars still in reach), the boss's bar under it. Voice: start, `smashBoss`, `smashClear`, `smashScene`, `smashHurry` (10 s left), advClear / advPerfect / advFail on stage cards.
- **Performance:** debris pooled by shape (`smPiece` / `smRetire`), fades after `SMASH_PIECE_MS`, cap `SMASH_MAX_PIECES` 140 / 80 on a phone; resting bodies sleep (`engine.enableSleeping` while in Smash); stacks keep upright (`lock`: no rotation) until disturbed; stats flushed to `track()` once a second ('brick', 'car', 'wall', 'smash' → `stats.smashed`).
- Hooks: `__grasp.sm` (build, punch, sweep, hit, breakObj, breakTo, nextWave, toBoss, win, sim, wave / waves / seg / boss / progress / waveLog, stage, free, plan, snd, heard, pieces, cap, pool...). Tests: `test_smash` (map, scenes, multi-hit cracks, one hit per swipe, weak chains, waves / scroll / tension, the boss, sounds, debris, free play, pause, mouse / touch / camera) and `test_smash2` (stages, clocks, stars, cards, profile, voice, the stage-length simulation; screenshots `tests/out/smash2_*.png`, `tests/out/smash3_*.png`).

**Busy Board** (toddler widgets: switches, buttons, knobs, sliders, zipper, door, piano, xylophone, lights, spinner, and the **electric guitar**):
- Layout (`layoutBusy` / `busyPack`): first-fit grid, 1x1 first, then blocks (the guitar), tall, wide. Portrait phone 2 columns (board scrolls), tablet 3; landscape tries 4..10 columns and keeps the count giving the biggest cells (desktop 1280x800: 10 columns, cell 111, no scroll; the wide rows stay full width).
- **Guitar** (`makeGuitar`, the block after the spinner; `__grasp.busy.widgets[18]`): span [2,3] on a portrait phone (stood up: neck up, strum = sideways swipe), [3,2] on a tablet, [6,2] in landscape (laid flat). Local frame u along the strings, v across (`toScreen` / `toLocal`, `geom()` cached per size).
  - 6 strings: crossing them strums (`strumTo`: every string crossed between two samples, in crossing order, direction-aware: dir +1 = low E to high E, -1 = up; notes offset by where they were crossed), a tap plucks the nearest (`pluck`, re-pluck guard `GTR_REPLUCK_MS`). Strings wobble (`wobble`, decaying) and glow in the chord colour; the amp's speaker pulses (`state.level`).
  - 4 chord buttons on the neck (`GTR_CHORDS` G green star / C red heart / D blue moon / Em yellow sun, 6-string voicings): a tap latches the chord and strums it once; a tap on the held chord = back to the default open E5 power chord (`GTR_DEFAULT`). Touch here is single-pointer (two fingers = their midpoint), so chords latch rather than need holding.
  - ROCK pedal (`state.dist`, labels `gtrRock` / `gtrClean`): crossfades the clean path into the waveshaper crunch, strums once. Whammy arm (grab the ball tip): push toward the strings = dive (to -3 semitones), pull = up (+1.5); springs back; bends every ringing note (`gtrSetRate`). Poking the amp strums.
  - Input: mouse / one-finger touch (= pinch → grab/drag/drop), camera point (press/move), open-hand / hovering mouse fast swipe (`sweep`, only mid-swipe so a jumping cursor does not strum). The xylophone's sweep now also fills in the bars a fast hand jumps over between frames.
  - Sound (`gtrChain`, built once per AudioContext): Karplus-Strong buffer per pitch (`gtrBuffer`, cached by period; playbackRate corrects the pitch), one voice per string (a new pluck chokes the old), max `GTR_MAX_VOICES` 8; clean / pre-gain + `WaveShaper` + cab low-pass; tone low-pass; dry + a 0.7 s noise-IR convolver; `DynamicsCompressor` limiter; out 0.6. Muted: nothing is built or played (`gtrHush` on mute, reset, leaving). Counted in `busy.sounds.guitar` (pedal: `stomp`).
  - Hooks `__grasp.gtr` { voices, made, dist, rate, rates(), peak() (analyser on the output), chain(), chords, def }; widget `state.log` ({ i, f, dir, chord, dist, at, heard }), `stringPos(i)`, `chordPos(k)`, `whammyPos()`.
  - Tests: `tests/test_guitar.py` (strum down / up order, tap, chords, pedal chain, no clipping, whammy, mute, amp, camera point + open-hand swipe, phone EN / HE, re-flow on 4 more screen sizes; screenshots `tests/out/guitar_desktop.png`, `guitar_phone.png`, `guitar_phone_he.png`). Not yet heard on a real phone: the KS tone and crunch, loudness vs the other widgets, CPU with the convolver.

**Shapes: toddler play** (parent: "the shapes game is hard for my 2-year-old because of the drag on the phone"; they chose tap-tap, then asked for an easier drag too). Code: the block `toddler help` after `shapesGrab`; constants `SHAPE_TAP_SLOP` 20, `SHAPE_TOUCH_LIFT` 40, `SHAPE_GRACE_MS` 120 / `SHAPE_EDGE_GRACE_MS` 700, `SHAPE_PALM` 90.
- **Tap a shape, then tap a hole** (touch and mouse click-click; camera unchanged): `shapesPtrDown/Move/Up` (from the canvas pointer handlers) track one press (`shapes.press`); a press that moved < 20 px, no second finger, not palm-sized (contact > 90 px) = a tap (`shapes.taps`, handled first in `shapesTick` → `shapesTap`; a grab made by that press is undone). Tap a shape = picked (`shapes.sel`, `shapesSelect`: hop, wiggle, gold glow, bob, sfx `boop`; every free hole pulses, no hint which; `ui.selFx`, `ui.holePulse`); the same shape again / an empty spot = dropped (`shapesDeselect`), another shape = switch, a drag = dropped. Then a hole (hit radius max(1.35 S, 36)) → `shapesFly`: anim `fly` on an arc to the hole's live position (follows rocking / sliding), the right hole turns it to fit → `placeShape` (the usual clunk, chime, burst, name); a wrong hole → boing, flies home, **no mistake counted**. Grabs in mouse / touch now need a press that is still down (fast taps never grab).
- **Touch-drag help** (`shapeAssist()`: touch only; mouse drags stay exact for older kids; `__grasp.shapes.assist` overrides): grab radius `shapeGrabR` 1.75 S (nearest wins); the shape sits 40 px above the finger, smoothed (~55 ms); magnet holes (`shapeMagnetR`: 2.4 / 2.0 / 1.6 S on levels 1-3 / 4-7 / 8+, weaker on harder levels on purpose): pulled in and turned, let go inside (shape or finger) = drops in at any angle; over another hole = the usual boing; let go within `shapeHelpR` (4.2 / 3.4 / 2.6 S) of its own hole = it flies in (`why: 'help'`); else it stays where dropped on the mat. A lifted finger keeps the shape for 120 ms (700 ms at the screen edge) and a finger back down carries on; a second finger never drops it; `pointercancel` = it just settles (no hole judged).
- **First play:** `tipOnce('shapesTap')` ("Tap a shape, then tap its hole!" / "הקישו על צורה ואז על החור שלה!") + a cartoon finger demo (`drawShapeDemo`, 2 loops, ends on the first touch). Hints / descriptions now say tap-tap.
- Hooks `__grasp.shapes` { sel, press, tapLog, magnet, demo, assist, grabR, magnetR, helpR, heldInfo, slop, lift (both now scaled, see big shapes); shapes[i].selected / selK / flyTo / hx / hy }. Tests: `tests/test_shapes.py` `tap_tests` (phone EN / HE) + `click_click`; screenshots `tests/out/shapes_tap_{demo,selected,flight,flight_wrong,placed}_{en,he}.png`, `shapes_drag_magnet.png`. Not yet tried with the real child: the hop / glow strength, the 20 px slop, the magnet sizes.

**Shapes: big shapes for a toddler** (parent: "very big in the first levels"; the layout below is superseded by "the whole screen", kept for the history). `layoutShapes` now searches every hole-grid / mat-grid column count (rows centred; a row offset by half a cell nests closer, `shapeRows` / `shapeRowYs`) and keeps the biggest S that fits (bisection, cap below).
- Cap = max(classic, min(`SHAPE_BIG[level]` × base, 11.5% of the height)); base = clamp(min(W,H)·0.13, 34, 70), classic = the old cap (`shapeClassicS`). `SHAPE_BIG` 1.5 on levels 1-3, then 1.3 / 1.2 / 1.12 / 1.06, 1 from level 8. Never smaller than before (the old layouts are among the candidates; cells are tighter: holes 2.5 S upright / 2.75 S rotated, mat 2.5 × 2.35 S). Level 3 now has 4 shapes (was 5) so levels 1-3 can be very big; level 4 = 5.
- Measured S (shape ≈ 2 S across), levels 1-8: 360×740 59 / 56 / 56 / 43 / 41 / 40 / 41 / 34 (was 37 / 42 / 36 / 36 / 36 / 36 / 29 / 28: L1-3 shape = 33 / 31 / 31% of the width); 390×844 65 / 65 / 65 / 48; 412×915 69 / 69 / 69 / 51; desktop 1280×800 92 / 92 / 92 / 88 / 74 (was 70 / 63 / 59 / 56); landscape 740×360 38 (was 34).
- `shapes.big` = S / classic (≥ 1) scales the aids: finger lift `shapeLift()` 40 × min(1.6, big), tap slop `shapeSlop()` 20 × min(1.5, big), the min grab (44) and hole-tap (36) radii, burst / ring widths, the pick glow, hole pulse, the finger demo (`ui.demo.scale`, ≤ 1.8). Grab / magnet / help / reach / arc were already × S. Hooks `__grasp.shapes` { S, big, grid { hc, mc, cap, classic }, slop, lift }. The release help (fly-in within `shapeHelpR`) now needs a real drag (`press.maxD` ≥ slop): with big shapes 4.2 S covers most of the mat, so a touch-and-let-go (two fingers, a palm) must not send a shape in.
- Tests: `test_shapes.py` `big_tests` (sizes vs the old `CLASSIC` table, ≥ 30% width on phones L1-3, gradual shrink, pixel test of the real outlines: no overlaps on the mat / in the box, all inside the mat / lid, levels 1-10 at 360×740 (EN / HE), 390×844, 412×915, 1280×800, 740×360; tap-tap and touch drag at levels 1 and 3, EN / HE); screenshots `tests/out/shapes_big_*.png`. Not yet tried with the child.

**Shapes: the whole screen** (parent, phone screenshot of level 1: "not utilizing the best space; no one cares about level 1 or money in this game").
- No HUD in play: the level title, the progress dots (`drawShapeHud`, removed) and the coin pill are gone (`drawCoinPill` returns at once in Shapes, no +n floaters); only the ⏸ pill. Levels / stars / coins still work; the level-done card (stars, +coins), the short "Level N" banner and the end card stay.
- `layoutShapes`: the mat starts at the top (safe area + 10 px gutter) beside the ⏸ pill (`shapeZones()`: the pill's / camera preview's corner; no home spot under it, else the shapes start under it: `mat.top`) and the box reaches the bottom safe area (`shapeSafe()` reads the env() insets from a probe); both full width minus 10 px. Stacked (box ~55% of the height, clamped to what fits); landscape / desktop also try side by side (box at the left, mat at the right) and take it only if S is > 3% bigger.
- The search: every hole / mat grid as rows or columns (`shapeGrid`: a short line nests into its neighbour; the mat puts its short line first), biggest S by bisection. Cells are measured on the real outlines (`shapeCells`: rasterised spans, `shapeSpans` / `shapeSpansHit`, cached per kind set; holes 1.08 S + 0.08 S gap, mat S + 0.25 S; an upright crescent is nudged 0.24 S right, `SHAPE_OFFX`); rotated holes use the outline radii (`SHAPE_RAD`). Cap = max(classic, min(`SHAPE_BIG` x 15.5% of the short side, 15% of the height)).
- Rocking: the box is sized so its turned corners (at ±rock) stay in its region (`boxIn`); sliding: `box.slideAmp` = up to 1.1 S, at least 0.6 S (was always 1.1 S). The hint toast sits above the box (stacked) or at the bottom (side by side).
- Measured S (shape ≈ 2 S across), levels 1-10: 360×740 73 / 68 / 66 / 50 / 48 / 45 / 48 / 37 / 38 / 31 (L1 = 41% of the width; was 59 = 33%); 390×844 80 / 77 / 76 / 54 …; 412×915 85 / 81 / 80 / 58 / 57 / 57 / 55 / 46 / 47 / 40 (L1 41%, was 69); desktop 1280×800 120 (cap) / 120 / 120 / 106 / 96 / 86 …; landscape 740×360 54 / 54 / 54 / 50 / 45 / 42 …. Never below the old sizes (`PREV` in the test). Layout cost: ~10 ms a level build on a desktop CPU.
- Aids are unchanged and still scale (grab 1.75 S, magnet 2.4 S, help 4.2 S, lift / slop / demo × `shapes.big`, capped 1.6 / 1.5 / 1.8).
- Tests: `test_shapes.py` `hud_tests` (EN / HE: no level title / coins drawn in play, the card and the banner still there; a spy on `textSprite` / `coinSprite`), `big_layout` (L1 ≥ 40% of a phone's width, ≥ `PREV` and the classic size, mat + box ≥ 90% of the usable height and width, no overlaps / holes inside the lid at both slide ends / no home under the pill / the rocking box on screen and clear of the mat; 360×740 EN / HE, 390×844, 412×915, 1280×800, 740×360); `test_menu.py` now checks the shapes (not a mat + title strip) stay clear of the ⏸. Screenshots `tests/out/shapes_full_*.png`. Not yet tried with the child.

**Corner menu (every game):** in play, every mode (Sandbox, Slice, Smash, Busy Board, Strike, Shapes) shows only the round ⏸ pause button in the top-right corner (same corner in EN and HE); the start screen hides the toolbar.
- One code path: `MENU_MODES` / `menuMode()`, `syncChromeMode()` (body `minChrome`), `openMenu` / `closeMenu`, `menuTick(now)` → `menuDwellTick` (camera: a point / pinch / fist held 600 ms). Strike and Smash call `menuTick` in their own tick (after their maps); the other modes from `frame()`. Escape / P toggle it in any mode (not over a map or the start screen).
- The sheet sets `pause.on`, which each mode already honours: Sandbox physics stop (and a held body is dropped; no grab while the sheet is open); Slice fruit, the spawn clock and a wave's unborn fruit wait; Shapes: the rocking / sliding box (`shapes.clock`), `phaseAt`, `levelStart` (the stars' par time) and the shapes' animations wait; Busy Board: `busyQuiet()` (slider tone, guitar) on open, the board does not tick. End-card dwell / wave-to-restart are off while it is open.
- Shapes' Home in the sheet: the round-over card first (as before), the sheet closes.
- Tests: `tests/test_menu.py` (every mode: only the button, the corner, no overlap with the mode's HUD on phone EN / HE and desktop, the sheet, freeze / Resume, Escape / P, a click beside, Sound, Language, Stats, Restart, Home, camera dwell; screenshots `tests/out/menu_<mode>_{en,he}.png`). Suites click toolbar buttons through `menu_click` (test_sandbox.py's header; test_chrome has a copy).

Around the games:
- **Meta:** coins, XP and player level, 3 daily missions, a shop (labelled), Grippy the cheering **voice** (see below), and a daily challenge (seeded run with its own streak).
- **Daily habit** (`profile.habit`):
  - a 7-day gift calendar that pops up on the first open of the day;
  - a play-streak flame;
  - a "3 stages today" chest;
  - star chests on the map at 10, 25, 45, 70 and 100 stars.
  - The "Tomorrow: day N gift" line on end cards was **removed** (player feedback: noise). The calendar stays on the start screen; the end cards keep "Wave for the next stage".
- **Grippy = voice only** (player feedback: the hand + speech bubbles did not help). Nothing is drawn: no `#grippy`, no hand in the gift / NEW UNLOCKED sheets, the Collection toggle is a speaker icon "Voice / קול" (still `profile.grippy`).
  - `grippySay(ev)` keeps its API; it speaks a 1–3 word line (`GRIPPY.en/he`) with `speechSynthesis` via `speakLine()` (shared with Shapes' names), HE voice when the UI is Hebrew.
  - Voiced events only: start (and daily), lastLife, boss, bossDown (Endless only), newBest, levelUp (Strike level), world, close (≤ once / 45 s), advClear / advPerfect (not on a boss stage with a world trip: "New world!" then), advFail, shapesLevel. Everything else returns false.
  - ≥ 8 s between lines (`GRIPPY_GAP`), never while a ball is close; skipped when muted, off, no speechSynthesis or no voice for the language. World music ducks while he talks (`grippy.duckUntil` in `musicDucked`).
  - Onboarding tips (gold brick, perk, guest) show once as the hint toast (`tipOnce` → `showHint(text)`); the serve is the start hint itself.
  - Hooks: `__grasp.grippy` { said, skipped (why), tips, ducking, say, cool }. Tests stub speechSynthesis (`test_grippy`, `test_shapes`); screenshots `tests/out/voice_*.png`.
- **Sticker album** (`profile.album`): a sticker for each stage's first 3-star clear, 40 in total, all drawn in code. A full page of 8 pays 30 coins once.
- **Music:** one loop per Adventure world, only while a stage is being played.
- **Economy:** coins are deliberately scarce, about 15–35 per run; shop items cost 120–1000. The numbers are in the `ECONOMY` table.

## Direct links (per game URL)
- `/strike` (opens the Adventure map), `/smash` (opens the Smash map), `/slice`, `/busy`, `/shapes`, `/sandbox`, `/frenzy` (Strike's Frenzy run) (and with a trailing slash): `vercel.json` rewrites them to `/index.html`; the page starts that game with the remembered input (touch until the camera is picked). Any other path = the start screen (on Vercel only these seven are rewritten; `/tremorti/` and the `/tremor` redirect unchanged).
- Entering a game pushes its path (`routeEnter`, in `startGame` and `openAdvMap`); Home goes to `/` (`history.back()` when the game was entered from the start screen, else `replaceState`); the browser Back from a game = Home (`goHome`), Forward re-enters. Hook `__grasp.route { modes, of, now, log }`.
- The page's own URLs are root-absolute (`/assets/guests/...`, `/tremorti/`) so they load at `/strike`.
- Tests serve through `tests/serve.py` (http.server + vercel.json's rewrites), used by `run_fast.sh` and the suites' own fallback server (`test_sandbox.py`, `test_chrome.py`).

## Art
- `art/GEMINI_PROMPTS.md` holds the ready-to-paste prompts for Gemini.
- Cow sprites are in `assets/guests/cow_{in,happy,dizzy,squash}.png`, 256×256 with a transparent background.
- **Monkey art is pending from the user.** Once they send `monkey_{in,happy,dizzy,squash}` images, process them like the cow's and save them to `assets/guests/`. The code loads them automatically; until then the monkey is drawn in code.
- **Processing steps:** remove the green background, remove the green edge tint, shrink the edges slightly, trim, 256×256 PNG. Uses Pillow and numpy.

## Workflow (important)
- **Branch:** develop on `ccr-61aa39be-e8m1zx`.
- **Saving work:** commit WIP with `git push origin ccr-61aa39be-e8m1zx`.
- **Shipping**, only after the tests pass:
  ```
  git fetch origin && git reset --soft origin/main && git commit -m "..."
  git push --force-with-lease origin ccr-61aa39be-e8m1zx && git push origin ccr-61aa39be-e8m1zx:main
  ```
- **Tests:**
  - `tests/run_fast.sh` runs every suite in parallel: 3 jobs, one shared server, about 13 minutes for 32 runs (30 suites incl. `menu`, `guitar`, `adventure`, `habit`, `album`, `hudmin`, `challenge`, `frenzy`, plus `strike2` and `strike3` again in 3D).
  - `addict` covers v5 (timing judge / PERFECT / serve ring, juice + reduced motion, no-overlap floaters, upgrades, run powers; screenshots `tests/out/addict_*.png`).
  - `challenge` covers v4 (the blast + bounce, aim, armor / weak spot / keystone / gold, overheat, turrets, closing walls, two balls, the ramp, combo, score / record / ranks / map badges, profile validation; screenshots `tests/out/challenge_*.png`, EN / HE, phone, 3D).
  - `frenzy` covers the rally (growth, caps, reset on a miss, speed / reach, visuals + sfx scaling, the pop, points, power, heat, noRally) and Frenzy (map button EN / HE, /frenzy, shield, uncapped growth, end on a miss, record / best / share, profile validation; screenshots `tests/out/frenzy_*.png`, phone EN / HE, 3D).
  - `routes` covers the direct links, pushState / Back / Forward, unknown paths and assets at a sub-path (EN / HE; screenshots `tests/out/route_*.png`). `serve` covers the pull-back + flick serve on mouse, touch (synthetic pointer events, `__gest`) and the camera stub (screenshots `tests/out/serve_*.png`).
  - `smash` + `smash2` cover Smash (see above).
  - `menu` covers the corner menu in Sandbox / Slice / Busy Board / Shapes (see Corner menu).
  - `hudmin` covers the minimal in-game screen, the pause sheet, the hit-meter pop (2D and 3D) and the clear card's stars line / buttons on a phone (screenshots `tests/out/hud_min_*.png`, `tests/out/fix_*.png`).
  - `tests/run_fast.sh adventure habit` runs only the named suites. Use that before a small ship.
  - Logs are in `tests/out/logs/`, screenshots in `tests/out/`.
  - `tests/run.sh` is the old sequential runner (over 30 minutes).
- **Browser fix:** if Playwright says its browser is missing, `tests/fix_browsers.sh` links the installed Chromium under the expected name. `run_fast.sh` calls it automatically.
- **Timing flakes:** the container is slow and tests flake under load. Fix them with condition polling (`page.wait_for_function`, sampling a few times), never by loosening a real assertion.
- **Old suites:** `strike.extrasOff` keeps the old suites' timings exact. Suites start the old run through the Endless button.
- **Big features:** delegate each one to a background helper agent with a detailed prompt. Let it commit WIP to the branch only, then review its screenshots and ship.

## How the user works
- Hebrew, short replies ("don't write me so much"), small frequent ships, progress visible often, no long waits.
- They like AskUserQuestion to settle the goal. When they say "don't ask, I'm going to sleep", decide everything yourself.
- They test on a phone with their child and send screenshots and feedback.

## Open items
- **Not yet checked on a real phone:**
  - Adventure feel with a real hand;
  - the hit-meter pop's size and placement with a real hand;
  - camera hold-to-select on the map;
  - music balance and phone CPU;
  - 3D performance;
  - cow size in play;
  - the gift pop-up.
- **Phone check:** fist vs pinch detection in Smash; Smash v3 with a real child (stage lengths came from a simulated player: are 2-5 hits too many for a 4-year-old? is the boss too long? clocks fair?); the scroll's smoothness and phone CPU with many bodies; the crack sound's pitch steps.
- **Monkey art:** waiting for the user's images.
- **v5 not yet checked on a real phone:** whether ±90 ms PERFECT feels fair with a real hand / the camera (the 50 ms camera lag is a guess), the ring's readability, chunk size and shake comfort, upgrade prices vs real coin income, which run powers kids pick.
- **Rally / Frenzy not yet checked on a real phone:** whether +70% (world 1: +45%) is still returnable with a real hand / the camera, the speed lines' and glow's CPU cost on a phone, whether Frenzy's +4% steps give runs of a fun length (and if the shield is enough for a small child), the whoosh's loudness.
- **v4 not yet checked on a real phone:** the difficulty curve with a real hand (world 2's pace / reach, turret shots, closing walls), whether the overheat feels fair, the rank thresholds (`RANK_K`) against real scores, the reticle's readability.
- **Possible next steps:**
  - more worlds after world 5;
  - a level ladder for Shapes too;
  - a stage-select difficulty tune after phone feedback;
  - a share card for stars;
  - extra effects in the 3D renderer for world travel.

## Parked backlog (the user said: "keep everything not built aside, we'll come back to it")
Not started. Ask the user before picking one up.
1. **Strike real boss battles:** bosses with health bars, attack patterns and weak points to hit. The user picked this for a 13-year-old.
2. **Challenge a friend:** share a link to a seeded stage or run; the friend tries to beat your score on the same layout. The user picked this too.
3. **More worlds after world 5:** new themes, music and stickers.
4. **A level ladder for Shapes:** a map and stars like Adventure.
5. **Monkey art:** process `monkey_{in,happy,dizzy,squash}` like the cow's (the pipeline is in Art) once the user sends the images.
6. **Smaller items:**
   - a share card for stars;
   - 3D effects for world travel;
   - the city scene briefly shows two suns while scrolling;
   - the wall scene's arriving wave looks like the old wall;
   - unknown URL paths get a 404 page instead of the start screen (only the game paths are rewritten).
