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
- **In-game screen (minimal):** one round pause button in the top corner (tap, Escape or a camera dwell) opens a sheet: Resume, Restart, Sound, Language, Stats, Home. The HUD is one slim row: hearts + a walls pill (Adventure: walls broken / stage walls; Endless: walls toward the next level). No score, progress line, NEXT card, streak chip, perk badges or bottom power bar. Other modes keep the full 5-icon toolbar.
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

**Smash** (rebuilt; player feedback: "it's a bit poor, allow smashing much more"):
- **Tile:** opens the **Smash map** (`#smashMap`): a big **Free play** button, then 20 stages in 5 scene groups (4 each, stars, locks). `/smash` opens the map too.
- **Scenes** (all drawn in code, `SM_BUILD` / `SM_ART` / `SM_BG`; every thing = one Matter body, kinds in `SMK`, materials in `SMM`): `wall` (a full-screen brick wall; behind it a room with its own tiled wall; behind that a treasure cave: layers 0 / 1 / 2, front first), `room` (window, frames, clock, ceiling lamps, shelves with jars / plants / books / bottles, table with plates and cups, TV on a cabinet, vase, floor lamp), `city` (buildings of stacked floors that collapse floor by floor, cars driving round, street lamps, a tree, a water tower, a hydrant), `blocks` (lettered toy towers, balloons, surprise boxes with confetti and toys), `food` (watermelons, pumpkins, tomatoes, oranges, apples on crates; shelves of eggs and bottles; juice splats painted on the scene).
- Each thing breaks its own way (debris, juice, sparks, sound: glass / clink / spark / pop / splat / confetti / crunch / wood / splash / clack...). Fragile things break when they fall or are knocked hard (`fr`, chain reactions: a shelf drops its jars, a building collapses floor by floor, the tower's tank bursts). Wall tiles are grid data drawn into one canvas each (`smTileWall`), cleared cell by cell.
- **Input:** a tap = a punch at that point; a swipe = a sweep along the path (strength by speed, `smStrength`); camera: any contact of the hand (a resting hand knocks every 220 ms).
- **Meter:** share of the scene's value broken; shown full at `SMASH_CLEAR` (90%), then everything left goes up ("Smashed!"). **Free play:** the next scene slides in (wall → room → city → blocks → food → round again, fuller each lap), 6 coins + 15 XP a scene, no clock, no losing. **Stages:** `smashPlan(n)` (scene, variant, clock 120 s on stage 1, shorter each stage); stars by time left (★★★ ≥ 45% left, ★★ ≥ 20%); start banner with the ★★★ line; card like Strike's: Next / **Play again** / Map, fail: **Try again** / Map; `ECONOMY.smashStage` (first clear 3 + stars, replay only stars added); saved in `profile.smash { stars, unlocked }` (validated).
- **Screen:** the pause button + sheet as in Strike (`minChrome` for Smash too); HUD = one pill: the meter (stages: + clock + stars still in reach). Voice: start, `smashClear`, `smashScene`, `smashHurry` (10 s left), advClear / advPerfect / advFail on stage cards.
- **Performance:** debris pooled by shape (`smPiece` / `smRetire`), fades after `SMASH_PIECE_MS`, cap `SMASH_MAX_PIECES` 140 / 80 on a phone; resting bodies sleep (`engine.enableSleeping` while in Smash); stacks keep upright (`lock`: no rotation) until disturbed; stats flushed to `track()` once a second ('brick', 'car', 'wall', 'smash' → `stats.smashed`).
- Hooks: `__grasp.sm` (build, punch, sweep, breakObj, breakTo, stage, free, plan, snd, heard, pieces, cap, pool...). Tests: `test_smash` (map, scenes, sounds, debris, chains, free play, pause, mouse / touch / camera) and `test_smash2` (stages, stars, cards, profile, voice; screenshots `tests/out/smash2_*.png`).

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
- `/strike` (opens the Adventure map), `/smash` (opens the Smash map), `/slice`, `/busy`, `/shapes`, `/sandbox` (and with a trailing slash): `vercel.json` rewrites them to `/index.html`; the page starts that game with the remembered input (touch until the camera is picked). Any other path = the start screen (on Vercel only these six are rewritten; `/tremorti/` and the `/tremor` redirect unchanged).
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
  - `tests/run_fast.sh` runs every suite in parallel: 3 jobs, one shared server, about 12 minutes for 28 runs (26 suites incl. `adventure`, `habit`, `album`, `hudmin`, `challenge`, plus `strike2` and `strike3` again in 3D).
  - `challenge` covers v4 (the blast + bounce, aim, armor / weak spot / keystone / gold, overheat, turrets, closing walls, two balls, the ramp, combo, score / record / ranks / map badges, profile validation; screenshots `tests/out/challenge_*.png`, EN / HE, phone, 3D).
  - `routes` covers the direct links, pushState / Back / Forward, unknown paths and assets at a sub-path (EN / HE; screenshots `tests/out/route_*.png`). `serve` covers the pull-back + flick serve on mouse, touch (synthetic pointer events, `__gest`) and the camera stub (screenshots `tests/out/serve_*.png`).
  - `smash` + `smash2` cover Smash (see above).
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
- **Phone check:** fist vs pinch detection in Smash; Smash scenes' density / stage clocks with a real child; phone CPU with many bodies.
- **Monkey art:** waiting for the user's images.
- **v4 not yet checked on a real phone:** the difficulty curve with a real hand (world 2's pace / reach, turret shots, closing walls), whether the overheat feels fair, the rank thresholds (`RANK_K`) against real scores, the reticle's readability.
- **Possible next steps:**
  - more worlds after world 5;
  - a level ladder for Shapes too;
  - a stage-select difficulty tune after phone feedback;
  - a share card for stars;
  - extra effects in the 3D renderer for world travel.
