# Why Krumit's Tale is addictive, and what Grasp borrows from it

Source game: Meteorfall: Krumit's Tale (Slothwerks, 2020). A deck-building roguelite on a 3×3 tile grid,
portrait, one-handed, offline, "tap out a dungeon or two".

## The hooks

| Krumit's Tale | Why it works | Grasp version |
|---|---|---|
| You see the enemy's next attack before you act | Anticipation, planning, no unfair deaths | **Telegraph**: "Next: TNT wall" shown at the far end of the corridor before it slides in |
| Gold from every kill; buy gear vs. cash out | Constant small rewards + a real decision | **Coins** for every brick/fruit/car, spent on **unlocks**; **perk pick** (1 of 3) between Strike levels |
| Lots of cards, five heroes, nine modes, loot | Variety and "ooh, a shiny" | **Collection**: ball skins, hand skins, katana skins, trails; locked badges on the start screen |
| Daily challenge with a leaderboard | A reason to come back today | **Daily run**: date-seeded Strike run, local best, 7-day strip, streak flame |
| Short dungeons, portrait, offline | Fits a spare minute | Rounds already short; **"One more?"** on the end card with the distance to the next unlock |
| Offbeat narrator, Adventure-Time art | Charm, laughter, memorable | **Commentator** bubble with kid-friendly lines (EN/HE) reacting to events |
| Roguelite randomness, near-misses | Every run different, "rage-quit but one more" | **Missions** (3 per day), **hit streak** multiplier, "Close one!" on near-miss hits |

## Build order (each pushed to `main` on its own)
1. Meta core: coins, XP, 3 daily missions, unlockable collection, profile in localStorage; start-screen panels.
2. Strike run: perk pick between levels, next-wall telegraph, hit streak + near-miss.
3. Daily challenge: seeded run, local best/history/streak, share text.
4. Commentator + "one more?" teaser.

## Pacing and long-term pull (v2, after play-testing)

**Problem seen in play:** within seconds of a first run the player gets power-ups, perk picks,
flying animals and new wall types. Everything is revealed in one session, so there is nothing
left to want, and the run has no build-up.

**What retention-focused games do** (tension and release; spaced reward ladders; gated unlocks;
roguelite meta-progression as in Hades and Vampire Survivors):
1. *Tension and release at every scale* — a level builds toward a climax, then a calm beat with a reward.
2. *Rapid early wins, spaced mid-game goals* — quick confidence first, then rewards get rarer and bigger.
3. *Gate new content behind account progress* — an XP bar unlocks features over days, not minutes.
4. *Each run moves you forward even when you lose* — meta currency/unlocks carry over.
5. *Variable rewards* — occasional surprises on top of predictable payouts.

**Applied to Strike**
- *Run arc:* levels 1–2 are pure core (ball + bricks). Power-ups from level 3 and rare; perk picks
  every other level from 3; flying animals from level 4 and rare.
- *Level arc:* walls close in and the heartbeat speeds up; the last wall of a level is a glowing
  "final wall"; clearing it gives a calm 3 s release with the banner and reward.
- *Meta gating:* wall kinds, power-up kinds, animals and perks unlock by player level across runs
  ("New! Glass walls" toast on the next run; locked ones shown as silhouettes with "Lv 6").
  About 15 unlocks spread over player levels 1–20, so new things keep arriving for days.
- *Worlds:* 5 worlds × 6 levels, a boss closes each world, a world map shows progress, and
  beating a boss unlocks the next world as a checkpoint start.
- *Rewards:* a treasure chest after each boss with a random prize (coins, a skin, a rare perk).
