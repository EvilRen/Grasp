# Grasp: handoff for a new conversation

Read this first, then NOTES.md (deploy, phone findings) and DESIGN.md (game design research and decisions).

## The project
- **Grasp:** a hand-gesture browser game for a parent and a young child. They speak Hebrew and play on a phone.
  - The whole game is one file: `index.html`, about 9,100 lines.
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
Sandbox, Slice (katana), Smash (fist, walls, cars), Busy Board (toddler widgets), Strike, Shapes (shape sorter with levels, colours and spoken names).

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
- `/strike` (opens the Adventure map), `/smash`, `/slice`, `/busy`, `/shapes`, `/sandbox` (and with a trailing slash): `vercel.json` rewrites them to `/index.html`; the page starts that game with the remembered input (touch until the camera is picked). Any other path = the start screen (on Vercel only these six are rewritten; `/tremorti/` and the `/tremor` redirect unchanged).
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
  - `tests/run_fast.sh` runs every suite in parallel: 3 jobs, one shared server, about 10 minutes for 26 runs (24 suites incl. `adventure`, `habit`, `album`, `hudmin`, plus `strike2` and `strike3` again in 3D).
  - `routes` covers the direct links, pushState / Back / Forward, unknown paths and assets at a sub-path (EN / HE; screenshots `tests/out/route_*.png`). `serve` covers the pull-back + flick serve on mouse, touch (synthetic pointer events, `__gest`) and the camera stub (screenshots `tests/out/serve_*.png`).
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
- **Phone check:** fist vs pinch detection in Smash.
- **Monkey art:** waiting for the user's images.
- **Possible next steps:**
  - more worlds after world 5;
  - a level ladder for Shapes too;
  - a stage-select difficulty tune after phone feedback;
  - a share card for stars;
  - extra effects in the 3D renderer for world travel.
