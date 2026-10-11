# New game for players aged 16–28: concept ratings (personas Noam 17, Lior 26)

Ratings out of 10, in the order: would try / would still play after a week / would share.

| Concept | Noam 17 | Lior 26 |
|---|---|---|
| Hand Wizard (roguelite: draw spell symbols) | 7 / 4 / 6 | 8 / 7 / 4 |
| Reflex Arena (Wordle-style daily 60 s reaction gauntlet) | 8 / 5 / 7 | 4 / 2 / 2 |
| Shadow Heist (stealth with a slow, steady hand) | 4 / 2 / 3 | 6 / 4 / 2 |
| Hand Kaiju (a giant hand smashing a 3D city) | 9 / 3 / 9 | 6 / 2 / 3 |

**Recommendation:** a hybrid prototype. Hand Wizard as the core, Kaiju-style explosions and clip moments, and a Reflex-style daily emoji share.

**Why it wins:**
- It is the only concept that scores well with both personas; Lior gives 7 for still playing after a week.
- Drawing a symbol takes 0.8–1.5 s, which gives 10–20 tracking points at 9–15 Hz. That is enough for a $1-style recognizer, and the 150–250 ms tracking lag hurts less here than in a reflex game.
- Touch play is a full game on its own, not a fallback.
- Sharing needs no server, because the code already has daily seeds, duel links and replay clips.

**One-week prototype scope:**
- **Spells:** 3 symbols (circle = shield, zigzag = lightning, triangle = fire) and 3 fusions of two symbols.
- **Recognition:** the same recognizer for touch and camera, with a debug overlay showing the recognized symbol, its confidence and the tracking rate in Hz.
- **Fights:** 3 enemy types, each telegraphing its attack 1.5–2 s ahead; 3 floors and a boss.
- **Relics:** pick 1 of 3 after each room, 6 relics in total.
- **Feel:** screen shake and a short hit-stop on impact.
- **Daily dungeon and polish:** a daily dungeon seeded by date with an emoji share; a replay clip on a win; EN and HE.

**Out of scope:** shop, meta progression, the pet, friend ghosts, two hands, final art, more than 3 symbols.

**Go/no-go after the owner plays it on a phone:**
- **Recognition:** at least 90% correct with the camera and 95% with touch, over 50 casts; fewer than 1 wrong cast per minute.
- **Performance:** tracking at least 9 Hz, the game at least 30 fps, and at most 250 ms from the end of the drawing to the spell.
- **Fun:** testers start a second and third run on their own, a run lasts 5–8 minutes, and deaths feel like "my fault" rather than "the game didn't get me".
- **No-go:** camera recognition under 85%, or "that's not what I drew" more than once in a run.
  - Fallback: "Shadow Beasts" (static hand poses that each turn the character into a different animal), or a small Kaiju mode inside Smash.

**Persona ideas:**
- Noam: "Jutsu Duel", a ninja duel with hand signs against a friend's ghost through a link (only one-hand poses would work with the current tracking).
- Lior: "Shadow Beasts", where static hand poses turn the character into animals with different abilities, mid-stage.
