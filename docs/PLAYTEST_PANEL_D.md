# Panel D playtest: Shira (10, Hebrew, collector) and Eitan (8, DCD)

I played the frozen snapshot on a 390×844 touch phone. My server on port 8795 is stopped. The process on port 8796 belongs to panelE, so I left it running. No project files or git were touched.

All screenshots are in `/tmp/claude-0/-home-user-Grasp/7dc5511d-5343-5974-bf8f-fc1da947af43/scratchpad/panelD/`. Scripts are there too: `s*.py` for Shira, `e*.py` for Eitan, shared helpers in `common.py`.

**How the input was driven:**
- **Taps:** real CDP touch events.
- **Gestures where timing matters:** in-page touch PointerEvents on rAF. These are the Strike serve, Slice swipes and the Smash swipes. CDP round-trips took about 50 ms each, so CDP alone gave wrong swipe speeds.
- **Strike rallies:** a "kid finger" model that follows the incoming ball with a lag, an offset and a little shake.
- **Camera games:** the `fake_vision` stub, throttled to about 9 scans/s like a phone's CPU tracker, with a 5 Hz shake and frame dropouts.
- **Hooks used to skip ahead:**
  - Shapes: `setLevel(7)`.
  - Strike: `profile.adv.unlocked = 16`, to try stages 5, 10 and 12.
  - Slice: a still fruit with no gravity, to measure the swipe-speed gate; and 1 heart left, to reach the end card quickly.
  - Strike serve tests: `serveReady()` and lives reset between attempts.

The real date was Sunday 2026-10-11, so both kids arrived on the **last day of Fruit Frenzy**.

---

## Shira, 10 (Hebrew UI)

| Mode | Again tomorrow? | Why |
|---|---|---|
| Pet (hatch, feed, wardrobe) | 8 | Cute and alive, with a daily reason to visit. But on day 1 she has only 2 colours and a scarf, the room is empty, and growing takes about 15 days. |
| Air Painting (touch) | 8 | The neon, rainbow, mirror and sparkle brushes look beautiful and saving works. There is no pink, no stamps, no undo and no gallery. |
| Weekly event page | 7 | Gorgeous, and has an exclusive pet hat. But it is a Slice event, she arrived on its last day facing a 900-point track, and one mission is "cut 150 fruits". |
| Daily gift | 7 | A clear 7-day calendar. "Open!" then needs a second tap ("יש!"). |
| Bubble Pop | 6 | Pretty, but she scored 159 against a 65-point bar for 3 stars, and nothing gets harder. |
| Catch the Stars | 6 | Cute cookies and candy, also 3 stars too easily (225 against 80), and the hint covers the basket. |
| Strike stages 1–2 and the map | 6 | Satisfying, and the stickers are nice. Both stages cleared with 3 stars (24 s and 42 s). It feels industrial or sporty, not cute, and "Legend" on stage 2 means nothing. |
| Busy Board guitar | 6 | Chords and the rock pedal are fun, but the guitar body sits below the fold and the rest of the board is for toddlers. |
| Sticker album | 5 | World 1's stickers are a hammer, brick, wrench, saw and bucket. The cute ones (fish, cupcake, seahorse) only come at stages 41–64. Nothing can be shared. |
| Shop themes | 4 | Only Gym, Basketball and Baseball. Coins buy nothing for the pet or for painting. |
| Shapes | 3 | "This is for babies." Six levels, no mistakes, fast. |

**Top 3 delights**
1. Hatching the egg and seeing the pet wear a scarf and a sky colour (`shira_07_hatch.png`, `shira_11_wardrobe.png`).
2. The neon flower picture with a rainbow, mirror butterfly and sparkles, saved as a PNG with the Grasp mark (`shira_drawing.png`).
3. The event page, its sticker shelf and the claim animation (`shira_13_event_page.png`, `shira_44_event_claim_anim.png`).

**Top 5 frustrations**
1. **Nothing cute to collect or buy.** The Shop is all sports and Strike gear (`shira_40_shop3.png`), and the first stickers are tools (`shira_38_album.png`).
2. **Paint is missing things.** There is no pink, no stamps and no undo. The drawing is gone after a reload. Two toasts cover the top of the picture when she saves (`shira_21_paint_saved.png`).
3. **The pet runs out of things to do fast.** Pink is locked until "Kid" (2+ days), the room has nothing in it, and the cap is 5 snacks a day. The naming sheet asks "איך נקרא לו?", which assumes a boy.
4. **Bubbles and Catch the Stars are too easy.** 3 stars on the first try, with no levels to climb (`shira_29_bubbles_card.png`).
5. **The event doesn't suit her.** It came on its last day, in a game she isn't into (Slice), with missions sized for a full week (`shira_13_event_page.png`).

**Quotes**
- "אני רוצה ורוד! ולמה אין לה מיטה בחדר?" ("I want pink! And why doesn't her room have a bed?")
- "המדבקות פה זה פטיש ולבנה… איפה החיות?" ("The stickers here are a hammer and a brick… where are the animals?")
- "הציור יצא מהמם, אני שולחת לנועה!" ("My drawing came out gorgeous, I'm sending it to Noa!") Then, after a reload: "איפה הציור שלי?!" ("Where's my drawing?!")
- "בועות זה קל מדי, תנו לי שלב 2." ("Bubbles is too easy, give me level 2.")

---

## Eitan, 8 (fine-motor difficulties)

He tapped 20–40 px off target, double-tapped 20–30% of the time, reacted 0.5–0.85 s late, made slow and wobbly swipes, and rested now and then.

| Mode | Again tomorrow? | Why |
|---|---|---|
| Shapes | 9 | Huge pieces, tap-tap, and a wrong hole costs nothing. Levels 1–6 took 9–22 s each with 32 px error. The only hitch: a double tap picks a shape and drops it again (3 times in one level-7 round). |
| Catch the Stars, camera | 9 | 3 stars (112 points) even with a shaky hand and 25% dropped frames. Play paused only about 4% of the time. |
| Bubble Pop | 8 | 2 stars with 32 px error and 850 ms reactions: 25 pops from 56 taps. The pop radius forgives a lot. |
| Catch the Stars, touch | 8 | 62–85 points (2–3 stars) with a slow finger. Misses never punish. |
| Strike stages 1–2 (Easy) | 7 | Very forgiving. Stage 1: 38 s, 3 stars. Stage 2: 41 s, 2 stars. Stage 3: 39 s, 3 stars. Stage 5 was a 126 s slog: 2 hearts lost, 1 star. A pull-back shorter than 51 px (6% of the screen) never serves and says nothing. |
| Air Drums, touch | 7 | Tapping pads works. |
| Air Drums, camera | 5 | A smooth strike slower than about 0.4 px/ms never makes a sound. At 0.25–0.35 px/ms every one of 4 tries only showed "Harder!". Shaky strikes did play, because the tremor itself adds speed. |
| Menus and cards | 5 | The card buttons are big. But there are tiny targets, two tap-through bugs and a hidden difficulty switch (see the bugs below). |
| Smash stage 1 | 3 | 150 taps in 125 s reached only 43%: "So close!", then failed. The clock assumes about 3 taps a second. Free play has no clock and is the better fit. |
| Slice | 2 | Rounds lasted 6–11 s and he cut 1 fruit in 8 swipes. Swipes slower than about 0.2–0.3 px/ms don't cut, and every missed fruit costs a heart. |

**Top 3 delights**
1. Shapes: big, chunky, and impossible to fail (`eitan_06_shapes_L1_end.png`).
2. Bubble Pop and Catch the Stars: success even with a messy hand (`eitan_17_bubbles_card.png`, `eitan_22_stars_cam_card.png`).
3. A 3-star Strike stage 1 with a slow finger, and a new sticker (`eitan_10_s1_card.png`).

**Top 5 frustrations**
1. **Slice ends almost at once** and slow swipes don't cut (`eitan_12_slice_slow028.png`).
2. **Smash fails him after 2 minutes of hard tapping** (`eitan_14_smash2_card.png`).
3. **Drums by camera stay silent** for his slow strikes and only say "Harder!" (`eitan_20_drums_camera.png`).
4. **His double taps and near-misses do things he didn't mean.**
   - Tapping beside the gift popup throws the gift away and opens the pet room (`eitan_02_gift_miss.png`).
   - A double tap on Home opens the pet room (`eitan_25_dbl_home_150.png`).
   - A tap on the bottom of the Strike tile switched Strike to Normal (`eitan_24_after_tile_bottom_tap.png`).
5. **Long fights wear him out.** Strike stage 5 took 126 s and he lost 2 hearts. Then the card says "Bronze · Silver at 700" when he scored 1,710 (`eitan_11_stage5_slow.png`).

**Quotes**
- "I didn't press that! Why is the egg room open?"
- "I'm swiping! It's not cutting!" (after Slice ended at second 11)
- "It says Harder but I'm hitting it…"
- "Shapes is my favourite. Can I do 10 more?"

**Could it be therapeutic?** Yes, with an assist mode. These modes already exercise the right things:
- Catch the Stars by camera: reaching and crossing the midline.
- Bubble Pop with two hands: using both hands, plus a calm mode.
- Drums "Follow the light": motor sequencing and memory.
- Shapes: eye-hand coordination and rotation.
- Paint with Mirror on: both hands working together.

What is missing is control over speed, the gesture thresholds, round length and fail states, plus a way for a parent or occupational therapist to track progress.

---

## Prioritized fixes

### P1: Assist ("Helper") mode, for Eitan and every younger player

One per-profile switch in the pause sheet and a parent area, with a few sliders.

1. **Input safety (all screens)**
   - Ignore input for about 450 ms after any screen change.
   - Treat a second tap on the same target within 350 ms as one tap. This fixes Shapes' pick-and-drop.
   - A backdrop tap must never pass through to the screen below, and must never dismiss an unclaimed reward.
   - All DOM targets at least 48 px, and close (X) buttons 48 px with padding.
   - Move Strike's Easy/Normal choice off the tile and onto the Adventure map or into settings.
2. **Speed**
   - A game-speed multiplier of 0.6, 0.8 or 1.0, applied to:
     - Slice gravity and spawn rate
     - Catch the Stars falling speed
     - Bubble rise speed
     - Strike `paceK`
   - Smash clock off, or doubled.
   - Rounds of 30, 60 or 90 s.
3. **Gesture thresholds**
   - Slice: in helper mode lower `SLICE_MIN_SPEED` from 0.45 to about 0.15, widen the cut by about 30%, and make missed fruit cost no heart (or give 3× the hearts).
   - Drums: a gentle mode where any downward entry into a pad faster than about 0.12 px/ms plays a soft hit (or a 400 ms dwell does). Always play a sound; replace "Harder!" with "Nice! Try a bit faster".
   - Strike: an option to tap the ball to serve, `PULL_MIN` at 3% of the screen instead of 6%, a wider magnet, and a hint when a pull is too short.
   - Smash: bricks break in 1 hit, and swipes count stronger.
4. **Failure and fatigue**
   - No fail cards in helper mode: "Keep going", plus a bonus for every 25% smashed.
   - A short-session prompt after about 8 minutes ("Great work, take a break and feed Bubu").
5. **Parent / OT view**
   - Per-game numbers: tap accuracy, reaction time, swipe speed, a reach map, and a weekly trend.
   - Adjustable thresholds.
   - Can reuse the Tremorti journal and report code.

### P1: Shira's collecting and creating

1. **Paint**
   - Add pink, brown and black.
   - Stamp brushes: heart, star, paw, flower and the pet's face.
   - Undo.
   - Autosave a 12-slot gallery in localStorage.
   - "Hang it in the pet room" puts a drawing on the room's wall.
   - Show the save toasts at the bottom, not over the picture.
2. **Pet**
   - Room decor sold for coins in the Shop: wallpaper, bed, rug, plant, toys. This gives coins a creative use.
   - One wardrobe item unlocked per day of visits.
   - A neutral naming prompt ("איך נקרא לחיה שלך?").
   - A pet photo card to share.
3. **Shop:** a cute Strike theme (Candy, Pet Park or Unicorn) around 150 coins, basket skins for Catch the Stars, and bubble colour packs.

### P2
1. **Sticker book:** a free-placement page to decorate with earned stickers, then share it. Make the world 1 stickers animal builders instead of tools.
2. **Bubble Pop / Catch the Stars ladder:** 10 levels with growing speed, and star bars scaled by level. Today 159 against 65 and 225 against 80 means no challenge for a 10-year-old.
3. **Social:** a "Beat my bubbles" duel link like Strike's, and "gift a sticker" or a pet-visit link.
4. **Daily return reasons:**
   - A daily drawing prompt ("draw a cat") that pays a sticker.
   - The pet asks for a specific colour or treat.
   - The day-4 "new look" gift gives a pet item.
5. **Weekly event:** scale the goals for someone joining late, and add Paint Week and Pet Week to the rotation.
6. **Strike clear card:** when stars cap the rank, say "2★ for Silver", not "Silver at 700".

### P3
1. Busy Board on a phone: start scrolled so the guitar body is in view, or lay the guitar flatter.
2. Catch the Stars: move the touch hint off the basket's catch zone, and stop items spawning under ⏸.
3. Hebrew: "לבוש" for an equipped ball, hand or theme should be "בשימוש" or "נבחר".
4. Smash: "So close!" at 43% should read "Good try! 43%".
5. Start screen on 390×844: the bottom quarter is empty. Room for today's goals or a mini album strip.

---

## Bugs, with repro steps

1. **The gift popup's backdrop dismisses the gift and passes the tap through.**
   - Steps: fresh profile → the first open shows the gift popup (sheet spans y 230–614) → tap the backdrop at (195, 180).
   - Result: the gift closes unclaimed (coins stay 0) and the event page opens. At (195, 630) the pet room opens instead.
   - Screenshots: `gifttest_26_gift_backdrop_180.png`, `gifttest_26_gift_backdrop_630.png`, `eitan_02_gift_miss.png`.
2. **A double tap on a canvas card's Home acts on the start screen.**
   - Steps: finish a Slice round → tap Home at (256, 574) twice, 150, 300 or 600 ms apart.
   - Result: the pet room opens every time. A single tap behaves correctly. `clickGuard` only swallows the first tap's own click.
   - Screenshot: `eitan_25_dbl_home_150.png`.
3. **Tapping the Strike tile's lower part changes difficulty instead of opening Strike.**
   - The Easy/Normal segment is 38×17 / 55×17 px inside the tile.
   - Steps: EN, touch → tap (214, 437).
   - Result: `localStorage.strikeDiff` becomes `normal`, Strike does not open, and nothing tells the player.
   - Screenshot: `eitan_24_after_tile_bottom_tap.png`.
4. **The pet's name sheet can be lost.**
   - Steps: hatch the egg with 5 taps, then tap the pet 3 more times within about 1.5 s.
   - Result: the name sheet never appears. Without the extra taps it does. Reloading while the sheet is open also loses it for good; the only way left to name the pet is the pencil in the room.
5. **The Strike clear card contradicts itself.**
   - Steps: clear stage 5 with 1 star.
   - Result: "Score 1,710 · Bronze" with "Best 1,710 · Silver at 700".
   - Screenshot: `eitan_11_stage5_slow.png`.
6. **Shapes: a double tap on a shape picks it and drops it again.**
   - Tap log in a level-7 run: 3 entries of `deselect` with reason `again`.
7. **Paint: unsaved drawings disappear on reload, and the save toasts cover the canvas top.**
   - After a reload, `paint.ink` is 0.
   - Screenshot: `shira_21_paint_saved.png`.
8. **A slow camera drum strike never plays.**
   - Steps: camera, stub at about 9 scans/s → strike a pad smoothly at 0.25 or 0.35 px/ms.
   - Result: 4 of 4 tries show only the "Harder!" cue, with no sound. At 0.45 px/ms every try hits.
   - Not a crash, but it fails slow movers.
9. **The camera prompt's two buttons sit 10 px apart.** "Play with touch" and "Turn on camera" are side by side, so a tap 20–30 px off can switch the camera on by mistake (`eitan_16_cam_prompt.png`).

No page errors were logged in any run.
