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

## v3: a ladder to climb, and a reason to come back every day (after play-testing)

**Feedback:** "This is still not the game I want to come back to, to climb the ladder of levels and play every day."
Idea from the player: *all the walls break, and when they are broken you move on to another world.*

**Why the current Strike does not pull you back**
1. *Progress is lost.* A run ends when the lives run out and starts over (at best at a world checkpoint).
   The climb is invisible: nothing on screen says "you are on step 17 of 40".
2. *No clear finish line in a session.* Walls keep coming. A level ends after N walls, but you never "beat" a stage you can point at.
3. *No mastery loop.* There is no score per stage to improve, so there is no reason to replay a stage.
4. *Worlds change too quietly.* A new world is a palette change and a banner, not a trip somewhere new.
5. *The daily reasons are weak.* The daily challenge and missions are there, but there is no gift for showing up and no streak to protect.

**What saga and daily-habit games do** (Candy Crush, Angry Birds, Cut the Rope, Duolingo, Clash Royale chests):
- *A saga map.* There is a winding path of numbered stages and you always see the next one. Progress is never lost: you only replay the stage you failed.
- *Short, finishable stages* with a clear goal ("break every wall") and an instant retry.
- *1–3 stars per stage.* Stars feed a meta goal (star chests) and pull you back to perfect old stages.
- *Worlds as places.* Each world has its own look and a travel moment between worlds, plus a boss stage at the end of each world.
- *Daily habit.* There is a 7-day gift calendar with a big day-7 prize and a streak to protect.
  A small "play 3 stages today" chest gives every visit a goal.
  The end card promises tomorrow's gift: "come back tomorrow".

**Applied: Strike Adventure**
- *Stages:* 5 worlds × 8 stages. Each stage is a fixed set of walls (4 at first, up to about 10), and you must break **all** of them.
  Clearing the last wall ends the stage; the boss stage closes the world.
- *Stars:* 3 for no lives lost, 2 for one lost, 1 for more. A fail offers "Try again" at once, and the map keeps every star.
- *World travel:* when a world's boss falls, the far wall bursts into a portal. The corridor flies through it and morphs into the next world's look, with a banner.
- *Map:* the Strike tile opens a winding map with the current stage pulsing and stars under each node. Star chests sit on the path. "Endless" keeps the old run.
- *Daily:* a 7-day gift calendar on the first open of the day, a streak flame, and a "3 stages today" chest.
