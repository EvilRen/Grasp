# Grasp: handoff for a new conversation

Read this first, then NOTES.md (deploy, phone findings) and DESIGN.md (game design research and decisions).

## The project
- **Grasp:** a hand-gesture browser game for a parent and a young child. They speak Hebrew and play on a phone.
  - The whole game is one file: `index.html`, about 9,000 lines.
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
  - Break **all** walls to clear a stage; 1–3 stars; instant retry.
  - Portal travel to the next world after a boss.
  - Stored in `profile.adv`.
- **Endless:** the old run, behind a button on the map. It has lives, levels, worlds, perks and a "road" of unlocks by player level (`ROAD`).
- **Animals:** the cow from road level 1 (and from Adventure stage 2), animals every 4–6 serves from run level 2. The monkey unlocks at player level 7.
- **Serve:** the ball waits until the player hits it.

Around the games:
- **Meta:** coins, XP and player level, 3 daily missions, a shop (labelled), the Grippy commentator, and a daily challenge (seeded run with its own streak).
- **Daily habit** (`profile.habit`):
  - a 7-day gift calendar that pops up on the first open of the day;
  - a play-streak flame;
  - a "3 stages today" chest;
  - star chests on the map at 10, 25, 45, 70 and 100 stars;
  - a "Tomorrow: day N gift" line on end cards.
- **Sticker album** (`profile.album`): a sticker for each stage's first 3-star clear, 40 in total, all drawn in code. A full page of 8 pays 30 coins once.
- **Music:** one loop per Adventure world, only while a stage is being played.
- **Economy:** coins are deliberately scarce, about 15–35 per run; shop items cost 120–1000. The numbers are in the `ECONOMY` table.

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
  - `tests/run_fast.sh` runs every suite in parallel: 3 jobs, one shared server, about 10 minutes for 24 runs.
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
