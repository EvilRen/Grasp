# Playtest panel findings (6 personas, frozen snapshot of main before the weekly event shipped)
Screenshots: scratchpad/panelA (Noa 2.5 / Ari 7), panelB (Daniel 13 / Maya game designer), panelC (Dana parent / Yossi 9 camera).

## Batch 1: bugs (all confirmed by 2 or more personas unless noted)
1. **Slice freeze (critical).**
   - In `sliceTick` (~index.html:2653 at snapshot), `cutAlong(slice.last, p, now)` can end the round: bomb → `hitBomb` → `sliceLoseLife` sets `slice.last = null`.
   - The same line then reads `p.x - slice.last.x` for `trailFx`, which throws. The whole rAF loop dies, the game is frozen, there is no card, and only a reload helps.
   - Fix: read the trail delta before calling `cutAlong`, or return after it when `slice.over` is set. Also make `frame()` resilient: wrap the tick in try/catch so one exception never kills the loop; schedule rAF first.
2. **Smash waves stuck.**
   - Bodies hit hard tunnel through the floor or out past the sides (seen at y = 48967, y = 131004, x = −44). They never break, but they still count in `smash.total`, so `smMeter()` stalls at 0.70–0.80 below the 0.85 clear.
   - Result: free play sits on an empty cave, and stage 1 fails at "70%".
   - Fix:
     - Break and credit anything whose body leaves `[-60, W+60] × [-200, H+150]`.
     - Thicker floor and wall bodies, and CCD-like clamping.
     - A backstop: end the wave when everything still alive is off-screen.
     - Toddler aid: if nothing has been hit for 8 s, pulse the remaining things or auto-advance (free play).
3. **Tap-through.**
   - Tapping Home (or any canvas card button) on an end card goes home on pointerdown. The same tap's click then lands on DOM under it, e.g. `#petInfoBtn`, which opens the pet room.
   - Fix: `preventDefault` on the pointer/touch that triggers card actions, and ignore DOM clicks for about 400 ms after `goHome()`.
4. **Duplicate i18n key `rpTitle`.** The run-power title is overridden by the replay title ("Your best moment"). Rename the run-power key in EN and HE.
5. **Replay pill in Hebrew.** The thumbnail overlaps the label "הילוך חוזר".
6. **Camera wording in touch mode.**
   - End cards say "Wave for the next stage / Wave to try again / Tap or wave to play again". Use "Tap Next" for touch and keep "Wave…" for the camera only.
   - The Daily panel's primary button is "Turn on camera". Make "Play" primary and the camera option secondary.
7. **Missing monkey art.** `/assets/guests/monkey_*.png` returns 404 on every Strike or camera-game load. Don't request files that don't exist; keep a list of present art.
8. **Toast covers the pet room header and its X.** Never draw toasts over modal headers.
9. **Pluralisation.** "Clear 1 more stages today" (EN, and check HE).
10. **Untranslated "Strike" in the HE Shop themes subtitle.**
11. **Canvas Hebrew bidi.** "+1" shows as "1+", and the streak pill reads "רצף 7×!". Use LTR marks / isolate numbers.
12. **Sticker slot placeholder.** It shows as a black rectangle during the card animation.
13. **Frenzy card has no Map button** (it was opened from the map).
14. **Missions on end cards ignore the mode.** For example, "Crumple 2 cars" on a Frenzy card.
15. **Meta pill.** The XP pill says "180 XP to: Glass walls" but opens the Shop. It should open the Road.
16. **Tremorti.** Rates outside about 3–12 Hz should say "unusual for tremor, possibly a measurement artefact" instead of "clear rhythm, typical of action tremor". A synthetic 18.2 Hz spiral got the essential-tremor wording.

## Batch 2: feel and clarity fixes
- **Strike hand occlusion (top feel problem, raised by 3 personas).**
  - On touch, the big see-through drawn hand covers the ball, the wall and the boss weak point. Replace it with a small fingertip ring or trail. On camera, draw the hand smaller, at about 25–35% opacity or as an outline near the ball.
  - Always draw the ball, aim ring and weak points above the hand.
  - Floating labels ("Hard", "Early", "SUPER!", "WALL +90", tips) must not stack on top of the ball; offset them away from it.
- **Camera hand-loss pause.**
  - Any gap over 400 ms pauses the game, shows the no-hand card, then a 3-2-1. At realistic loss rates that is 18–42% of playtime.
  - Coast through gaps under about 1 s with the last cursor. Never pause the free modes (drums, paint, Calm bubbles, Busy, Sandbox). In timed modes show a quiet "hand?" chip, and skip the 3-2-1 if the gap was under 2 s.
  - No-hand card: hide the technical text (CPU, scans/s, "switch the detection engine?") behind "more". Show "Show me your hand 👋" and the picture.
- **Camera everywhere once chosen.**
  - Keep the camera running on the Adventure and Smash maps, the start screen and the camera picker.
  - Allow selecting start tiles, picker items and map nodes by holding the hand over them (dwell). The map dwell code exists but never gets a cursor because the camera is off.
  - Home by hand must not stop the camera.
- **Air Drums.** Gentle strikes are missed about 38% of the time. Lower `DRUM.hitV` a little, or accept a downward move over 2 samples. Show a "harder!" cue on near misses.
- **Paint.** The fist-shake erase needs a confirm or a longer hold.
- **One serve instruction in Strike.** The banner, "Pull back, then flick!" and a 3-line tip all show at once. Keep one.
- **Easy Strike pacing.**
  - On Easy a still finger returns every ball, but soft hits barely progress (1 of 4 walls in 150 s). Stage 1 takes about 95 s.
  - Target 30–45 s for stage 1: a faster base pace, and a soft hit that still breaks 2 bricks on stages 1–3.
  - Frenzy: ramp +8–10% per hit for the first 10 hits.
- **Ranks.**
  - Inflated: "Legend" on stage 1, and "Diamond" with 1 star.
  - A rank needs at least 2★. Make par harder so Legend means something, or keep ranks only on the map.
- **Slice.** Rounds of 4–25 s, sparse fruit. Give a 2 s spawn grace, 5 hearts in the first round, slightly bigger and slower fruit on phones, and more fruit per wave later.
- **Busy Board for toddlers.**
  - Scroll on any vertical drag that doesn't start a widget gesture.
  - Make 1×1 widgets about 175 px (fill the width).
  - Put piano, xylophone and guitar near the top.
  - Replace the 5-line hint with 2 words or an animated finger.
- **Bubble Pop (toddler).**
  - It takes 3 taps before the first bubble (picker banner + camera prompt + "play with touch"). Show the camera prompt once per device and drop the duplicate banner in the picker.
  - Remember Calm. Keep at least 4–5 bubbles on screen in Calm.
- **Sandbox.** The hint covers the only objects. Start the objects mid-screen and give it a tiny goal or a toy box.
- **Pet.** Hatching gives 1 starter snack so the first Feed works. Unlock one wearable at Baby.
- **Economy.**
  - Daniel had about 60 coins after a dozen runs; the cheapest power is 80 and themes cost 300–500.
  - Make the first upgrade affordable after session 1: a day-1 starter gift of 80 coins, or about 2× payouts for the first 3 days.
  - Add a first theme around 150, and show a "next purchase" goal on the map.
