# START HERE: state of the Grasp project (for a new conversation)

Read in this order:
1. This file: where things stand, what's open, how to work.
2. `HANDOFF.md`: the full technical reference. It covers every game and system, the workflow, tests, deploy and the open items.
3. `DESIGN.md`: the design reasoning by version (pacing, saga, challenge, addictive, rally, worlds, events …).
4. `docs/PLAYTEST_FINDINGS.md`: findings from the 6-persona playtest. Most are fixed; see "Panel fixes" in HANDOFF.
5. `ROADMAP.md` (if it exists): Maya's plan to bring everything to 9–10. It may not have finished; see below.

## Where we stopped (latest)
- **Home v2 is live on main (90a87bf):** new start screen, simple end cards, gentler retention.
- **Phase 1 of ROADMAP.md, partly done and NOT on main.** It is on branch `ccr-61aa39be-e8m1zx` (commits "Phase 1 …"). The helper was stopped at the user's request, so the full test run has not been done.
  - Items 1–16 of the brief: see `git log origin/main..ccr-61aa39be-e8m1zx` and HANDOFF "Phase 1".
  - To continue:
    1. Check which items are missing.
    2. Finish `tests/test_phase1.py`.
    3. Run `tests/run_fast.sh`.
    4. Ship.
- **Panel D/E reports:** `docs/PLAYTEST_PANEL_D.md`, `docs/PLAYTEST_PANEL_E.md`.

## Live
- Site: https://grasp-weld.vercel.app/. Vercel deploys `main` automatically.
- Tremorti: https://grasp-weld.vercel.app/tremorti/
- Repo: `evilren/grasp`. Work branch: `ccr-61aa39be-e8m1zx`.

## What's in the game (short)
- **Strike** (the main game, a brick-breaker in a 3D corridor):
  - **Adventure:** 64 stages in 8 worlds, a real boss every 8th stage, stars, ranks, album, star chests.
  - **Other modes:** Endless, Frenzy and Daily.
  - **Systems:** upgrades, run powers, sport themes (Gym, Basketball, Baseball), challenge-a-friend links (`/duel`) and replay sharing.
- **Smash:** destructible scenes with waves, a scrolling scene and a boss; free play and 20 stages.
- **Slice**, **Busy Board** (including an electric guitar), **Shapes** (toddler tap-tap, big shapes), **Sandbox**.
- **Camera games:** Air Drums, Bubble Pop, Air Painting, Catch the Stars.
- **Meta:**
  - coins (scarce economy), XP and the road;
  - daily gift, missions and streak;
  - weekly event (6 rotating events with a reward track);
  - a pet that grows, a sticker album, the Shop;
  - voice lines, music, a graphics pass with auto quality.
- **Installable** as an app (PWA, works offline). Direct links: `/strike` `/smash` `/slice` `/busy` `/shapes` `/sandbox` `/frenzy` `/drums` `/bubbles` `/paint` `/stars` `/duel`.
- **Tremorti** (tremor meter):
  - measurement, interpretation by tremor type, a journal and trends;
  - a 3-minute full check, a doctor report, a spiral test;
  - accuracy down to 1.5 Hz.

## What was running when this session ended (check its state)
Background helpers write to the shared branch `ccr-61aa39be-e8m1zx`. When they finish, run tests and ship.
1. **New start screen, simple end cards, gentler retention for parents.** Approved by the user. Status: in progress (a WIP commit is on the branch, not on main).
   - Start screen: a big "▶ Play Strike — Stage N" button, a "Little ones" tile, a bottom tab bar (Play / Shop / Pet / Events), a ⋯ More sheet, hide-until-earned, one popup at a time.
   - End cards: stars + score, Next + 2 buttons, one Share button; no missions, XP or upsell.
   - Gentler retention: the gift calendar pauses (no reset) and there are no streak nags.

   To check: `git log origin/ccr-61aa39be-e8m1zx`, look for "home2". If unfinished, finish it from the spec in this item, then run `tests/run_fast.sh` and ship.
2. **Maya's roadmap to 9–10.** She is the expert-designer persona; the plan goes to `ROADMAP.md`. If it's missing, rerun: re-score the current build and write phases, gap analysis, a cut list and measurement.
3. **Second testing panel (4 personas):** Shira 10 (collecting and creativity), Eitan 8 (fine-motor difficulties, needs an accessibility/assist mode), Ronit 35 (casual, 5-minute sessions), Omer 24 (long single-player depth). Read-only reviews; their findings were not saved yet. Rerun them on a snapshot of main if needed; method in "Testing panels" below.
4. **New game concept for players aged 16–28.** Two gamer personas (Noam 17, Lior 26) were rating 4 concepts. The user found the first proposals boring and wants reasons for every recommendation.
   - **Hand Wizard:** a roguelite where you draw spell symbols in the air or on screen; a daily dungeon with an emoji share.
   - **Reflex Arena:** a Wordle-style daily 60-second reaction gauntlet.
   - **Shadow Heist:** a stealth game using slow, steady hand movement.
   - **Hand Kaiju:** a giant hand smashing a 3D city.

   **Result:** see `docs/GAME_CONCEPTS_16-28.md`. Recommendation: a Hand Wizard hybrid with a one-week prototype and go/no-go criteria. Waiting for the user to decide.

## Agreed backlog (in order, after the items above)
1. **Hero + story:** the pet is the hero, bosses kidnapped its friends, rescue one per world with short funny cutscenes.
2. **Collectible creatures:** about 50, procedurally generated (body, colour, ears, patterns), rare, with small helper powers, hidden across all games.
3. **Secrets and surprises:** secret stages, hidden doors, rare events (a rainbow, a golden boss), easter eggs.
4. **Hand magic powers:** camera gestures that work in every game (fist = earthquake, open hand = shield, point = laser).
5. **Procedural generation:**
   - endless Adventure worlds after stage 64;
   - procedural Smash rooms and cities;
   - a daily generated stage, the same for everyone.
6. **From HANDOFF's parked list:**
   - a level ladder for Shapes;
   - a real boss in Endless;
   - monkey art (waiting for the user's images);
   - small visual nits.
7. **The user also asked for:**
   - **2 players on one phone:** offered; parked behind the above.
   - **A parent corner:** a screen-time limit and parent-only settings; offered, not chosen yet.

## Not checked on a real phone
Tracked in HANDOFF "Open items".
- **Feel:** camera feel, PERFECT timing, boss difficulty (the Octopus may be too hard for a child), rally top speed.
- **Performance:** 3D performance and replay capture cost.
- **Sound and reminders:** the Hebrew voice, music balance, Tremorti reminders.

## How the user works
- Hebrew, short replies.
- Use **AskUserQuestion** to settle goals, and explain *why* you recommend something.
- Small, frequent ships with visible progress.
- They test on a phone with their kids and send screenshots.
- When they say "don't ask, I'm going to sleep", decide everything yourself.
- They want the games to feel loved and addictive (single-player; no online/server for now).

## How we work (short; full version in HANDOFF "Workflow")
- **Big features:** give one to a background helper with a detailed brief. Tell it: commit WIP to the branch only, never push to main, never stash or reset the shared tree, add a test suite, and run `tests/run_fast.sh`.
- **Shipping:**
  1. Rerun failing suites once to confirm a flake.
  2. `git fetch && git reset --soft origin/main && git commit -m "…" && git push --force-with-lease origin ccr-61aa39be-e8m1zx && git push origin ccr-61aa39be-e8m1zx:main`
  3. To ship only some files (e.g. Tremorti) while a helper's WIP is on the branch, use a temporary `git worktree` from `origin/main`.
- **Tests:**
  - `tests/run_fast.sh [suites…]` runs about 45 suites in parallel, ~12–15 minutes for all.
  - Port 8765 must be free first; a stale server gets reused silently.
  - Under load the suites flake on timing; rerun alone to confirm.
- **Testing panels (personas):**
  1. Make a worktree snapshot of `origin/main` in the scratchpad and copy `tests/vendor`.
  2. Each read-only persona agent serves the snapshot on its own port with a renamed copy of `tests/serve.py`, plays with Playwright like a human, takes screenshots and writes a report.
