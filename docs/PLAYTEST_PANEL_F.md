## Panel F report: Quest after the art pass — Noa (9, the game's own audience) and Yoav (adult, plays deck-builders)

Both personas played the live build on port 8799 at 390×844, Noa in English and Yoav in Hebrew. The
server is stopped and no project files or git were touched by the session. Scripts, screenshots and
`metrics.json` are in `/tmp/claude-0/-home-user-Grasp/da932b2f-d8ce-5ad6-adc7-b51e0bbe077a/scratchpad/panelF/`
(shortened to `F/` below).

**How the play was driven:** real clicks on the canvas's own hit rectangles for the How-to-play cards
and the screen buttons; `__grasp.quest` hooks to seed a run and to play a fight out, because a bot that
plays cards well is not what this panel is measuring. Every tap rectangle on every screen was read back
from `__grasp.quest.btns()` and measured. Contrast was measured from the screenshots themselves, as
WCAG ratios between the text and what sits behind it — the first attempt sampled the canvas through
`getImageData` and returned zeros for everything, because the page has several canvases and it read the
wrong one.

**What this panel is for:** the art is in — frames, 58 card pictures, 33 monsters, 3 heroes, 4 painted
lands, a display face. This asks whether the interface on top of it still works for the two people who
have to read it.

---

## What the numbers say

| Measure | Result |
|---|---|
| Load to the hero pick | 0.89 s (EN), 0.97 s (HE) |
| A full fight, bot-played | 1.6 s (EN), 1.4 s (HE) |
| Page errors across both runs | none |
| Screens visited | pick, doors, fight, reward, camp fire, shop, mystery, treasure, deck |

### Tap targets under 44 px, every screen, both languages

| Target | Size | Where |
|---|---|---|
| A relic chip | 26 × 26 | the top bar, one per relic, on every screen |
| The deck chip | 80 × 30 | the top bar, on every screen |

Card rectangles are excluded: a fanned hand overlaps on purpose and the fan is wider than any one card.
Everything else — doors, hero cards, run lengths, Start, End turn, the camp fire's two buttons, every
shop button — clears 44 px comfortably.

### Contrast, measured from the shots (4.5:1 is the bar for text this size)

| Text | Ratio |
|---|---|
| Land and room line | 15.8:1 |
| End turn label | 12.7:1 |
| Card name on its plate | 13.1:1 |
| Energy number in the orb | 14.1:1 |
| Rest button label | 13.8:1 |
| Door label | 13.9:1 |
| Health numbers, top strip | 10.9:1 |
| Hero one-liner | 12.3:1 |
| **Hero name on the chosen hero** | **3.5:1** |

One failure, and it is specific: the chosen hero's card is lit gold, and cream lettering on a gold-lit
plate loses most of its separation. The two unchosen cards are fine — this only bites on the one the
player has selected, which is the one they are reading.

---

## Persona 1: Noa, 9, the age the game is built for

### What worked

1. **The fight reads at a glance.** Monster, its intent above it, health under it, hand at the bottom,
   one bright button. She did not have to hunt for anything (`F/noa_04_fight.png`).
2. **The intent number is the biggest thing in its bubble.** A sword and an 8, in crimson, on a dark
   pill. That is the one number a child has to act on and it wins the bubble.
3. **End turn is obviously the thing to press.** It is the only solid bright object on the screen.
   This was the fix from the last round and it landed.

### What did not

1. **The relic chips are 26 px.** They sit in the top bar and they are tappable — tapping one explains
   what the relic does — but a 9-year-old's fingertip is about 10 mm. These are the smallest targets in
   the game and they hold the only explanation of a relic she owns.
2. **The chosen hero's name is hard to read** (3.5:1, above). The card she has just picked is the one
   whose name has gone faint.
3. **The shop offered the same card twice** (`F/yoav_06_shop.png`: Meteor at 120 gold, twice, in a
   five-card shop). Nothing is broken, but with 120 gold of her 49 she is looking at two identical
   things she cannot afford, in a shop that only has five slots.

---

## Persona 2: Yoav, adult, reads Hebrew, plays deck-builders

### What worked

1. **It looks like a deck-builder now, not a kids' app with cards in it.** Painted frames, rarity in
   the metal, a painted land behind the fight.
2. **The Hebrew lays out properly.** The top bar mirrors, the cost gem moves to the corner the eye
   starts from, the fan reverses. Nothing is left stranded on the wrong side (`F/yoav_04_fight.png`).
3. **The card face is readable at hand size** — name, cost and the rules row all separate (13.1:1).

### What did not

1. **Two icon languages on one screen.** The shop draws its own pouch, coin, sword and shield, and then
   prints 💰 beside every price, ❤️ on the healing button, 🏮 for the relic and 📖 in the top bar. A
   drawn gold coin and an emoji money bag sit 40 px apart in the same row. Whichever is right, both at
   once reads as unfinished.
2. **The least useful button is the one dressed as primary.** In the shop, "Leave" carries the gold
   rim; buying a card, removing a card and healing are all teal. Gold should mark the thing worth
   doing, and leaving a shop is what you do when there is nothing left to do.
3. **The land is named but not shown.** "Enchanted Forest · Room 1 of 7" sits above a painting of the
   enchanted forest, with a 🌲 emoji in front of it. The emoji adds nothing the painting is not
   already saying.

---

## The list, in the order I would fix it

1. **Grow the relic chips and the deck chip to 44 px.** Two sizes, no design decision in it.
2. **Darken the chosen hero's plate, or ink its name.** 3.5:1 on the card the player has selected.
3. **Finish the icons.** Prices, the healing button, relics, events and the land marker are the last
   emoji. Drawn icons beside emoji is worse than either alone.
4. **Move the gold rim off Leave.** Primary marks the action worth taking.
5. **The shop can stock the same card twice, by construction.** I checked rather than guessed:
   `shopStock` concatenates two independent `rewardCards` draws, so a card drawn into the first three
   can be drawn again into the last two. That is in the rules, not the drawing, so it is the owner's
   call — I would not change it as part of a visual pass.

Nothing here is a rules change and nothing here is a regression: no page errors, and the balance
simulation is unchanged.
