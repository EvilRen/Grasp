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

**Applied: the daily habit**
- *Gift calendar:* on the first open of each local day a calendar of 7 boxes pops up on the start screen; today's box glows and bounces, and a tap anywhere on it opens the box with a burst, a sound and the coins flying to the coin pill (a look flies to the Shop). Prizes: 5, 8, 10 coins, a cheap look (or 12 coins), 15, 20, then a big chest (40 coins + a look). A missed day starts the week again at day 1, with a gentle line; after day 7 it cycles. The gift chip in the top bar reopens it any time.
- *Play streak:* a flame in the top bar counts the days in a row with a finished round of any game. It pulses the first time it grows on a day; a "Play today to keep your 4-day streak!" line shows while today is still to play. (The daily challenge keeps its own streak.)
- *3 stages today:* a chest in the Adventure map's header fills with every stage cleared today (replays count) and shakes at 3; it pays 10 coins.
- *Star chests:* chests beside the path at 10 / 25 / 45 / 70 / 100 stars (15 / 25 / 35 / 50 / 80 coins; the last one also a look). The next one shows "26 / 45".
- *Come back tomorrow:* once today's gift is open, the stage card and the round-over card say "Tomorrow: day 3 gift".
- All the numbers are in `ECONOMY` (gifts, stageChest, starChests): about 100 coins and 2 looks a week for showing up, next to the 15-35 a run.

**Applied: the sticker album and world music**
- *Sticker album:* the first 3-star clear of each Adventure stage peels a sticker onto the clear card (40 drawn stickers, 8 per world: tools, glass garden, robots, jungle animals, volcano dragons and gems). The Album button in the map header opens one page per world. Missing stickers show as silhouettes with the stage number and three stars ("Get 3 ★ on stage 12"). A full page pays `ECONOMY.album.page` (30 coins) once, with confetti. Players who had 3-star stages before the album get those stickers as new ones.
- *World music:* each world has its own quiet loop (playful square lead, airy bells, mechanical saw, marimba, dramatic minor). It plays only while a stage is being played and ducks under the stage and boss banners. A 100 ms lookahead timer schedules the notes, so nothing runs per frame. Mute silences it.

## v4: challenge (after a 60-second playtest with a 13-year-old)

**Feedback:** "Breaking the ball was really not a challenge: if I hit hardest it just breaks all the walls. He didn't get excited."

**Why it was flat:** a SUPER slap cleared a whole wall *and flew on* through the next ones, so the best move was always "hit as hard as
you can"; aim did not matter; nothing pushed back, so you could not really lose; and there was no number to beat.

**What action games that hook teens do:** every hit is a decision (Breakout / Arkanoid aim, *Peggle*'s orange pegs, *Angry Birds*'
weak points and keystones), power has a cost (heat / stamina bars in shooters and fighting games), the world fights back (projectiles,
a closing wall), and a score chase with ranks and records (S-ranks, "NEW RECORD!", combo multipliers in *Tetris Effect*, *Beat Saber*).

**Applied (all Strike; B and C mainly the Adventure, sensible in Endless / the daily too):**
- *A hard hit is no "break everything" button:* the ball meets one wall and comes back off it. The damage is a bounded blast by tier
  (soft: a chip; medium: the brick + a neighbour; hard: a plus; SUPER: the 3x3; the fireball power-up: a radius-2 diamond). A wall down
  to its last quarter collapses, so nobody chases the last scattered brick.
- *Aim matters:* the hit's direction picks the landing point (a reticle shows it). Armored bricks take 2-3 hits (cracks per hit),
  glowing weak spots crack a whole row and column, a keystone brings down what rests on it, gold pays a bonus. One good shot beats three
  wild ones.
- *Overheat:* hard and SUPER hits heat the hand; at full heat every hit is soft for 3 s (steam, sizzle). Soft / medium hits and time cool
  it. It forces mixing the hits instead of SUPER spam. Shown only while warm, as a slim bar under the hearts pill.
- *Real risk:* world 1's first four stages stay a gentle on-ramp; from world 2 the pace climbs (x1.1-1.38 on top of the level curve), the
  reach shrinks, the walls stand closer, turret bricks shoot slow shots you must slap away (or lose a heart), from stage 12 the front
  wall closes in, and some world 3+ stages serve two balls at once (each one missed costs a heart). Stages can be failed for real; 3 stars
  still means "no heart lost".
- *Score chase:* a combo multiplier (x2 after 3 returns in a row ... x8) pops by the pill only when it changes; the clear card shows the
  score, a rank (Bronze, Silver, Gold, Diamond, Legend by multiples of the stage's par), the stage's best and a "NEW RECORD!" moment with
  a fanfare and the voice. The map shows each stage's best rank as a gem and an overall rank, a reason to replay old stages.
- *Juice:* shake scaled to what broke, an 80 ms hit-stop on a SUPER impact, a crack sound per armor level, crack lines racing from a weak spot.
- *Economy unchanged:* no coins for bricks, gold or records; the score and ranks are their own reward.

## v5: addictive (perfect timing, juice, upgrades, run powers)

**Ask:** "maybe something is missing in the visuals or mechanics to make it addictive". What rhythm and arcade games that hook do: a timing
skill with instant, loud feedback (*Beat Saber*, *Rhythm Heaven*, *Wii Sports* tennis' sweet spot), juice that scales with the impact
(hit-stop, shake, debris at the camera), meta progress that makes coins mean power (*Jetpack Joyride*, *Archero*'s talents), and a small
random choice between levels (roguelite boons, *Hades*).

- *Perfect timing:* a ring closes on the spot where the incoming ball will be at its ideal moment (a third into the hit window); a swing that
  meets it within ±90 ms (wider for a fast ball, +15% a 'Perfect window' level, at most 30% of the window so Normal's short window is not all
  PERFECT; ±200 ms = Good) is **PERFECT!**: a 90 ms hit-stop, flash rings and a gold edge flash, its own sting, x2 points for the hit, one tier
  more power (to SUPER at most: the blast stays bounded) and a perfect streak ("PERFECT ×3"). A hand held still is never PERFECT; Early / Late
  show small, only for a real swing. The contact time is the hand's nearest pass in the path memory; the camera's lag (50 ms) is taken off. The
  serve: once pulled back a ring breathes in to the ball every 700 ms; a flick launched as it closes is PERFECT (+1 tier).
- *Juice:* hit-stop (0-110 ms) and shake (capped 3.2 px) scale with the bricks broken; 1-4 big chunks fly at the camera (2D debris and 3D
  chunks); a white flash, a ring and a thump on each wall down; a bass thump under SUPER; the stage's last wall: a 0.6 s slow-motion beat with
  the camera nudged forward (proj and the 3D camera). prefers-reduced-motion: shake at most 0.6 px, a 250 ms beat, no camera move.
- *No clutter:* one big message at a time (each up >= 0.45 s, at most 3 waiting, PERFECT cuts in); every floating text is laid out each
  frame clear of the others and of the banners / spotlight / tag / combo pop / HUD (or not drawn); the "New! ..." spotlight waits for the
  stage / level banner, sits under the combo pop; the combo pop sits under the tag pill on a phone.
- *Permanent upgrades* (Shop, "Power (forever)" section first): Heavier ball (a medium / hard hit blasts one shape wider 12% a level; level
  3: +1 damage to armor), Extra heart (+1 / +2), Cool hands (heat x0.85 a level, cooling x1.35), Wider reach (+5% a level), Lucky (+0.22 gold
  bricks a wall a level, a coin per gold brick), Perfect window (+15%). Prices 80-160 for the first level (~3-4 runs) up to 600. Adventure and
  Endless only: **the daily ignores them** (a fair run, the same for everyone). Stars still mean "no heart lost"; maxed reach never undoes the
  world 3+ ramp (it stays under world 1's on-ramp).
- *Run powers:* the clear card's Next shows 3 of 7 (Magnet paddle, Split shot, Shield, Fire start, Slow-mo start, Combo keeper, Extra
  heart) on the perk cards; tap or point-and-hold (20 s: the first). It lasts the next stage only (a fail keeps it for the retry); none after
  a boss stage (the map). A small badge by the HUD pill shows it. One stage keeps every pick fresh and the loop short: clear, pick, play.

## Smash v3: toys that end fast get dropped (after a phone playtest)

**Feedback:** "The fist wall-breaking game ends so fast, I finished every stage in one to two seconds. You know what kids do with toys that end so fast?"
v2 was tuned with an auto-play bot, not a hand: one tap broke a thing, a swipe cleared a row of them (each frame of the swipe hit again), a broken
shelf or a building's ground floor took everything above it down, and the meter filled in seconds.

**What keeps a smashing toy alive:** resistance you can feel (cracks that grow, a deeper knock each hit, only the last hit pays off), a place that
keeps going (*Smash Hit*, *Stack Ball*, endless runners: the scene moves on and you travel through it), rising tension (things ahead already
creaking), and a climax (a boss with a health bar, phases, and a big victory moment).

**Applied:**
- *Tougher things:* 2-5 hits by size and material (glass and china 2, furniture 4, building floors 4-5, melons 5); cracks drawn over the thing
  grow with each hit, it wobbles, the knock drops in pitch; bricks crack before they fall out.
- *Weak chains:* a fall is one hit's worth and never ends a thing that was not cracked yet (a shelf drops its jars: they crack; already cracked
  ones shatter); a building loses one floor, not all; debris never hurts. A swipe hits each thing it crosses once (no mass clear).
- *Waves and travel:* a stage is 3-5 waves; at 85% of a wave the scene scrolls on (down the street, the next room, along the market, the next
  wall) and the next part slides in, so the screen keeps filling. A thin track in the HUD shows how far through the scene you are, with the
  boss's crown at its end.
- *Tension:* the waves ahead arrive with hairline cracks and a tremble; during a wave untouched things start creaking by themselves.
- *A boss at the end of every scene* (a treasure safe, a giant TV, a giant robot, a crowned block tower, a giant melon): 50-60 hp, harder hits
  hurt more, cracks, then pieces fall off, then it shakes and glows; a big blast, confetti and the voice.
- *Measured, not guessed:* a simulated child on a phone (3 taps a second, a third of them at empty spots, some swipes) takes ~65-130 s a stage
  and ~90 s a free-play scene; a good player (5 accurate taps a second) about half that. Clocks are ~1.3x the child's time; ★★★ needs 40%
  of the clock left (about the good player's pace).

## Rally and Frenzy: faster and faster (parent's idea)

**Ask:** "Maybe a mode where every hit makes the ball faster and faster." Both: a rally speed-up in normal play, and a separate Frenzy mode.

**Why it works** (*Pong*'s rising volley, *Breakout*'s speed-up after N hits, table-tennis rallies, *Super Hexagon* / *Flappy Bird* / *Beat
Saber* endless modes): a rally that keeps getting faster is tension you build yourself; the number of hits in a row is the simplest score a child
understands, and "one more, I can beat 23" is the pull.

**Applied: the rally (Adventure, Endless, daily)**
- Every return: +5% ball speed; a miss: back to the stage's base speed. Capped so it stays returnable on a phone: +70%, world 1's gentle first
  four stages +45%, Endless on Easy +60%. It replaces the old "every 5 returns +5% pace" step while on.
- Fairness: the reach grows by a third of the speed-up, and the PERFECT / Good windows already widen with the ball's speed.
- You can see and hear it: the ball heats white -> yellow -> orange -> blazing (glow, a heat trail, embers at the top), speed lines streak from the
  vanishing point, each return's whoosh rises in pitch, and a small "x1.4 SPEED" pop (every +20%, "MAX SPEED!" at the cap) shares the combo pop's
  place; nothing is drawn at the base speed (no permanent clutter).
- Faster pays: points x (1 + half the speed-up) on top of the combo (at most x1.35); a chance of one tier more power (0.6 x the speed-up, at most
  50%), still capped at SUPER so the blast stays bounded.
- Overheat never punishes speed twice: the bonus tier adds no heat (the hand's own tier counts), and a hard hit heats the hand less the faster
  the rally (/ the speed factor).

**Applied: Frenzy (טירוף)**
- A button beside Endless on the Adventure map ("Frenzy ⚡", its best under it) and the link /frenzy.
- The pure skill chase: the rally with no cap (+4% a hit), one heart: the run ends on a miss. The very first miss is shielded (a cyan ring on the
  heart, "Shield!", the speed drops back halfway) so a child is never out instantly.
- Walls still come (clean brick walls, no specials, no heat, no upgrades, no levels or boss): blasting them is the satisfying side, the rally is
  the challenge.
- Score = hits in a row (the HUD pill counts them), plus the top speed; the best is kept, NEW RECORD! with the record fanfare and the voice, and a
  share line ("Grasp Frenzy ⚡ 34 hits in a row · top speed ×2.4").

## Real bosses (each world's stage 8)

**Ask (parent, for a 13-year-old):** "real boss battles". The old boss was a brick wall with a face that crept forward: one more thing to hit hard.

**What makes a boss fight exciting** (*Zelda* / *Cuphead* / *Punch-Out!!*): a character with a name and an entrance; a health bar that visibly drops; phases
that change the fight and the look (it gets angry, breaks apart); attacks you read from a wind-up and answer with the right move (deflect, break,
dodge, knock back); weak points that reward aim; a big payoff when it falls.

**Applied:**
- *The stage is the fight:* stage 8 / 16 / 24 / 32 / 40 has no walls. The boss walks (the dragon flies) in after the stage banner with a roar, its name drops
  in, the voice calls it; a health bar with its name in the world's colour sits under the hearts.
- *Five bosses drawn in code* (glossy cartoon, light from the top-left, ink outlines; 2D in perspective, 3D as a textured plane at its depth): Brick Golem
  (rocks), Glass Queen (mirror shards, a crystal shield, spinning mirror blades), Steel Robot (rockets, an energy shield, a claw arm, a charge), Jungle King
  Kong (barrels, chest-drum charge, a swinging log), Lava Dragon (fireballs, tail sweep, flies side to side). Sport themes keep the arena; the boss keeps its look.
- *Read and answer:* every attack has a wind-up (a '!' and a sound): a slow projectile you slap back (it hurts the boss), a shield only a SUPER or PERFECT
  hit breaks (the timing skill pays off), mini-walls to break first, a charge a hit knocks back (else a heart), a spinning arm that blocks the balls that
  meet it (time or aim around it). A glowing weak point takes x3; the aim ring shows where the ball will land.
- *Phases at 66% / 33%:* a roar, more kinds of attack and shorter gaps; cracks, then missing pieces, sparks and an angry face. The hearts come back at each new
  phase (a checkpoint, so a long fight stays fair for a careful child); 3 stars still means no heart lost.
- *Balance, measured with a simulated player* (not guessed): world 1 ~45-65 s for a careful child (who usually survives it), ~30-40 s for a good player;
  world 5 ~2 minutes for a good player and hard. Boss stages use a calmer ball than their world's stages (the boss is the threat).
- *Payoff:* an explosion in its colours, its pieces at the camera, slow motion, confetti, "Victory!", the coins by the usual rules, the trip to the next world.
- *Endless keeps its boss wall* (its suites check exact timings; a real boss there is a later step).

## Challenge a friend

**Ask (parent, for a 13-year-old):** challenge a friend to beat your score on the same layout.

**What works** (*Wordle*'s shared result, *Clash Royale* friendly battles, ghost races in racing games): one tap to send, a link that opens straight into
the same challenge, the rival's number visible while you play, a clear verdict and a one-tap reply.

**Applied:**
- *One button* on the stage card (clear or fail), the Frenzy card and the Endless card: "Challenge a friend". The name is asked once (optional) and kept.
  The share sheet (or the clipboard) gets "I scored 1234 on Grasp stage 12 — can you beat me? 💥" and a short link.
- *The same run:* an Adventure stage is already seeded by its number; every Endless / Frenzy run now carries its own seed (in the link), so the friend gets the
  same walls, bricks, power-ups and guests. The daily and the stages keep their seeds. No server: the link is the whole challenge.
- *While playing:* "Beat 1234 (from Dana)" with a bar and the friend's ghost; passing it: "You passed Dana!" and a cheer.
- *The verdict:* WIN / LOSE / TIE with both scores above the card, and "Send back" (the same challenge with your score).
- *Safe links:* every parameter is checked and clamped, a name keeps only letters, digits and a few marks, anything broken is ignored.
