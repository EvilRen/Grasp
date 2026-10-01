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
