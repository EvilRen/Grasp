# Quest — the card frames (one prompt, one image)

Quest's cards are drawn on the canvas: Grasp paints the picture, the title, the cost number and the rules text itself,
in English or in Hebrew, over an **empty frame**. So the art you make here carries no text and no symbols at all — only
the frame. That is what keeps the game bilingual and what keeps every card razor-sharp at any size.

Nine frames are needed: three card types (attack, skill, power) × three rarities (common, uncommon, rare). They come
from **one** image: a 3 × 3 sheet. Paste the block below into Gemini as-is, save the result as `art/quest_frames_raw.png`,
and run:

```
python3 tools/quest_frames.py art/quest_frames_raw.png --check   # measures the sheet against qLay(); writes nothing
python3 tools/quest_frames.py art/quest_frames_raw.png           # slices, keys the magenta out, writes assets/quest/frame_*.webp
```

Until those files exist the game paints the same nine frames in code, to the same layout, so nothing breaks and nothing
moves when they land. Replacing one later is a drop-in: same filename, no code change.

---

## The prompt

```
A single flat sheet of nine EMPTY fantasy trading-card frames, laid out as a strict 3-column × 3-row grid, for a
painterly fairytale-sci-fi deck-building game.

THE SHAPE OF THE IMAGE — read this first, it decides everything else:
The finished image must be PORTRAIT, clearly taller than it is wide: about 1448 pixels wide by 2048 pixels tall, a
1 : 1.42 width-to-height ratio. Do NOT output a square image. The sheet is three cards wide and three cards tall, and
each card is itself 1 : 1.42, so the whole sheet carries exactly the same 1 : 1.42 shape as one card. A square sheet
gives square cells and squat cards, which is wrong.

GRID — this is a technical sheet, so the geometry must be exact:
The image is divided into nine identical rectangular cells by two perfectly straight vertical lines at exactly 1/3 and
2/3 of the width and two perfectly horizontal lines at exactly 1/3 and 2/3 of the height. Every cell holds exactly one
card frame, upright, centred in its cell, filling about 94% of the cell, with a small empty margin all round. All nine
frames are the SAME SIZE, in the SAME POSITION within their cell, and share IDENTICAL internal geometry — only the
colour and the ornament change between them. Each card is a portrait rectangle with rounded corners, taller than it is
wide, in a 1 : 1.42 width-to-height ratio.

COLUMNS — the card's type, which sets its colour:
Column 1 (left): ATTACK. Deep crimson and oxblood metal, hot ember-red rim light.
Column 2 (middle): SKILL. Dark teal and verdigris metal, cold bioluminescent cyan rim light.
Column 3 (right): POWER. Dark bronze and antique gold metal, warm amber rim light.

ROWS — the card's rarity, which sets how ornate it is:
Row 1 (top): COMMON. Plain cast metal. Simple bevelled border, no filigree, no gems.
Row 2 (middle): UNCOMMON. The same frame with a finer bevel, a thin polished inlay line running inside the border,
and one small faceted gem set into the bottom edge of the border, on the centreline.
Row 3 (bottom): RARE. The same frame in polished gold-touched metal, with engraved filigree scrollwork curling out of
all four corners, a glowing inlay line, and three small faceted gems set into the bottom edge of the border, evenly
spaced on the centreline.

THE ONE HOLE — the most important part:
Exactly ONE area of each frame is cut away, and it must be filled with FLAT PURE MAGENTA #FF00FF — a solid, uniform,
unshaded keying colour with no gradient, no texture, no glow and no shadow inside it, so it can be cut to transparency:
  1. THE PICTURE WINDOW: a rounded rectangle starting 11.5% of W from the left and 10% of H from the top, 77% of W
     wide and 39.5% of H tall (W and H are that card's own width and height, measured from its top-left corner). The
     frame's metal surrounds it as a recessed, bevelled opening with a crisp inner lip.

THE TWO PLATES — these are NOT holes. Paint them as real metal, do not cut them out and do not make them magenta:
  2. THE TITLE PLATE: a rounded horizontal bar starting 9.5% of W from the left and 53.5% of H from the top, 81% of W
     wide and 10% of H tall. An inlaid nameplate sitting proud of the surface, with a lit top edge — smooth, blank,
     polished metal, completely unmarked.
  3. THE RULES PANEL: a rounded rectangle starting 10% of W from the left and 69.5% of H from the top, 80% of W wide
     and 20.5% of H tall. A sunken, slightly recessed tablet of smooth dark stone or darkened metal in the lower half,
     blank and unmarked, with a gentle inner shadow along its top edge.
Both plates must be completely smooth and empty: the game prints the card's name on the plate and its rules on the
panel, in English or in Hebrew, so anything drawn there would sit underneath live text.
There is NO fourth opening. Do not cut a socket, a disc, a jewel mount or a hole of any kind into either top
corner — the game paints an opaque cost gem over that corner itself and would hide it completely.

SYMMETRY — as important as the measurements:
The frame must be exactly symmetric left to right: its left half is the mirror image of its right half. Both top
corners are plain and identical, carrying the same ornament as each other, with no socket, mount, badge or
emblem in either one, and nothing that a disc covering 29.6% of the card's width would half-cover. The three
openings are all centred on the card's vertical centreline.
The background of the whole sheet — everything outside the nine cards — is also flat pure magenta #FF00FF.
Do not draw a transparency checkerboard. Do not draw a grey and white chequered pattern of little squares in the
picture window or anywhere on the sheet. The window is not transparent and is not a checker pattern: it is painted
a solid flat magenta, the same magenta as the background, as if filled with one pot of paint.

ORNAMENT — what the metal carries instead of writing:
The frame's raised decoration is purely ornamental geometry: scrollwork, interlocking knotwork, spirals, bevels,
rivets, leaf and vine motifs, faceted studs. Decorative shapes only. There is no writing anywhere on the frame, no
alphabet, no runic script, no engraved characters, no inscription along the border, and no marking of any kind on
the title plate — the title plate is a completely smooth, unmarked, flat magenta bar.

STYLE: painterly digital illustration, the feel of a premium hand-painted deck-builder. Dramatic rim light from the
top-left (the whole game is lit from the top-left; the frame is never mirrored, so this direction holds in every
language), deep shadow falling to the bottom-right, so the metal reads as sculpted and three-dimensional. Faint
bioluminescent flecks caught along the bevels. Rich, low-key, cinematic; crisp readable silhouettes; uncluttered.

ABSOLUTELY NOT: no text, no letters, no numbers, no words, no runes, no icons, no symbols, no swords, no shields, no
illustration or character or landscape of any kind, nothing at all inside the magenta picture window and nothing on
either plate. No drop shadows on the magenta. No watermark, no signature, no border around the sheet, no caption, no
label, no grid lines drawn on the image. Only the nine empty frames on magenta. And the image is PORTRAIT, about
1448 x 2048 — taller than it is wide, never square.
```

---

## What the slicer expects

`tools/quest_frames.py` cuts the sheet into exact thirds, so the only thing that matters is that the grid is even and
nothing crosses a cell boundary. It writes, in reading order:

| | attack | skill | power |
|---|---|---|---|
| **common** | `frame_attack.webp` | `frame_skill.webp` | `frame_power.webp` |
| **uncommon** | `frame_attack_u.webp` | `frame_skill_u.webp` | `frame_power_u.webp` |
| **rare** | `frame_attack_r.webp` | `frame_skill_r.webp` | `frame_power_r.webp` |

(A starter card and a common card share the plain frame, so nine files cover all fifty-odd cards.)

If Gemini drifts — uneven cells, a stray symbol, text in a plate — regenerate rather than patch: the layout in the code
is fixed, and a frame whose window is a few percent off will crop the picture.

---

## The rare row, re-run (one prompt, three frames)

The second sheet's rare row came back with the ATTACK frame gold instead of crimson, so a rare attack reads as a power
card. Only that row needs redoing; the common and uncommon rows ship as they are. This prompt asks for the three rare
frames side by side, described to match the row already in the game — gold filigree corners, an arched window, faceted
gems — with the colour separation corrected.

Save as `art/quest_rares_raw.png`, then:

```
python3 tools/quest_frames.py art/quest_rares_raw.png --row rare --check    # measure first
python3 tools/quest_frames.py art/quest_rares_raw.png --row rare            # writes the three *_r.webp
```

The slicer finds the cards by their gutters, so the three need only be clearly separated — they do not have to sit on
exact thirds.


### Why the first rare re-run failed, and the rule it produced

The colours came back right (crimson / teal / gold) and the ratio was the best of any sheet at 1.428 against 1.42.
But the generator had painted the words **THE TITLE PLATE** and **THE RULES PANEL** onto the plates themselves, in
capitals, reading them off this file's own section headings. No measurement catches that — `--check` only sees that
the plate is solid metal, which it is, with writing on it.

So: never head a section with the name of a part in capitals. A generator treats a capitalised noun phrase sitting
above a description as a caption to render. Describe each region in a sentence instead, and state outright that no
part of the image may be labelled with its own name.

The same run also deepened the arched window to a tall dome when asked for a "gently arched top", dropping the
picture window to 72.6% of the rectangle qLay draws into — worse than the 89.9% it was trying to improve. The other
two rarities use a plain rounded rectangle, so the rare row should too; the filigree already carries the tier.

---

## The interface plates (one prompt, nine pieces)

The owner, twice: the buttons look like a slide deck. They do, and the reason is that every plate in the game is
drawn in code — a rounded rectangle with a gradient. The paintings are finished; the chrome sitting on them is not.
This sheet replaces the chrome with painted metal, and the owner chose the ornate end of the scale.

Nine pieces, cut the same way the card frames are: exact thirds, magenta keyed out, each piece trimmed to its own
bounds. The pieces do **not** share an aspect ratio — a wide pill and a tall card sit in cells of the same size, each
with magenta around it, and the trim sorts them out.

**Why the centres must be flat.** A button is 180 px wide on one screen and 260 on another, so the art cannot be used
at one size. The three pills are stretched horizontally: left cap, stretched middle, right cap. That works only if the
middle is identical in every column of pixels — a top-to-bottom bevel is fine and wanted, a left-to-right change is
not. The six panels are nine-sliced, so their inner field must be flat in both directions. This is also what makes
them readable: the ornament is in the border, the text sits on a quiet field.

Resolution is enough even where a piece looks small on the sheet: a stretched middle costs nothing, so only the caps
and corners need pixels, and they get the full cell.

```
A single flat technical sheet of nine EMPTY painted interface plates for a painterly fairytale-sci-fi deck-building
game, laid out as a strict 3-column × 3-row grid. These are empty containers that lettering will be drawn on top of
later, in code — so no piece may carry any lettering of its own.

THE SHAPE OF THE IMAGE:
The finished image is SQUARE, 2048 by 2048 pixels. It is divided into nine identical square cells by two perfectly
straight vertical lines at exactly 1/3 and 2/3 of the width, and two perfectly horizontal lines at exactly 1/3 and
2/3 of the height. Each cell holds exactly ONE plate, centred in its cell, upright, drawn straight on with no
perspective and no tilt. The plates are NOT all the same size or shape: each row below states its own proportion.
Nothing may touch or cross a cell boundary.

THE BACKGROUND, AND THE ONLY KEYING COLOUR:
Every pixel that is not part of a plate is FLAT PURE MAGENTA #FF00FF — a solid, uniform, unshaded colour with no
gradient, no texture, no glow and no shadow in it. That means all the empty space between and around the plates, and
the area outside each plate's rounded corners. Each plate's own silhouette must end hard against that magenta: no
drop shadow, no outer glow, no soft halo, no reflection spilling outside the shape. Light and depth live INSIDE the
silhouette only.

ROW 1 — three wide pressable plates, each a long horizontal lozenge with fully rounded ends, about 4 units wide to 1
unit tall, filling about 90% of its cell's width:
  Left: polished warm gold metal, bright and lit, the most valuable-looking object on the sheet.
  Middle: polished jade-green metal with the same construction and the same light, bright and inviting.
  Right: dark blued steel with a thin gold rim, deliberately quieter than the other two.

ROW 2 — three rectangular plates with softly rounded corners, about 2 units wide to 1 unit tall, filling about 85% of
its cell's width:
  Left: dark blued steel with a thin pewter rim, quiet.
  Middle: the identical plate, but its metal is warm gold and it is lit as though a lamp sits just above it.
  Right: the identical plate in cold dead grey iron, unlit, as though it has been left in the dark.

ROW 3 — three larger pieces:
  Left: an upright rectangular plaque with softly rounded corners, taller than it is wide, about 1 unit wide to 1.3
  units tall, in dark blued steel with a gold rim.
  Middle: a large upright panel with softly rounded corners, about 1 unit wide to 1.2 units tall, in dark blued steel
  with a heavier gold rim — this one is a window that a whole screen of writing will sit inside.
  Right: a long, low, shallow strip with softly rounded corners, about 5 units wide to 1 unit tall, in dark pewter —
  a small nameplate that a single line will sit on.

HOW ORNATE, AND EXACTLY WHERE THE ORNAMENT MAY GO — this decides whether the sheet is usable:
All nine plates are richly worked: engraved filigree scrollwork, hammered metal, raised rivets, a polished inlay line
following the edge, and a small faceted gem set into each corner where there is room for one. But every bit of that
ornament, and every rivet, gem, scroll and bevel, must sit entirely within a narrow band hugging the plate's outer
edge, no thicker than about one sixth of the plate's SHORTER side. Inside that band the plate's face is a quiet,
calm, EVEN field of its own colour — no filigree, no rivets, no scrollwork, no pattern, no vignette, no spotlight, no
scratches, no highlight blooms crossing it.
  On the three lozenges in row 1, that inner face may shade smoothly from lighter at the top to darker at the bottom,
  like a convex surface lit from above — but it must be IDENTICAL all the way across from left to right, so that any
  vertical slice through the middle of the plate looks the same as any other.
  On the six plates in rows 2 and 3, the inner face must be flat and even in BOTH directions: the same tone in the
  middle as at the inner edge of the border band.

LIGHT AND MATERIAL:
One light source, above and slightly to the left, the same for all nine. Each plate reads as a solid thing with
thickness: a lit upper edge, a soft occluded lower edge, a crisp bevel where the face meets the border band. The
metal is real and worked — hammer marks, wear on the raised edges, a little age in the recesses — not smooth plastic
and not a flat vector shape.

COLOUR:
The game's palette: near-black violet #0F0B20 and deep indigo #1D1636 for the dark metal, warm gold #F2C14E for the
gold, bright jade #45D6C2 and #3DDC84 for the green, with cream #F6EFE2 as the brightest highlight. Nothing
pastel, nothing washed out, nothing neon.

SYMMETRY:
Every plate must be perfectly symmetrical left to right, so that it can be mirrored for a right-to-left language
without the ornament reading backwards. No piece may have a feature on one side that it lacks on the other.

WHAT MUST NOT BE IN THE IMAGE:
No letters, no words, no numbers, no runes, no glyphs, no logos, no watermark, no caption, no label, and no writing of
any kind anywhere in the picture, including on the plates themselves, in the magenta, or in the margins. No icons, no
swords, no shields, no hearts, no coins, no faces, no creatures, no hands, no cursor, no arrow. No picture frame
around the whole sheet, no grid lines drawn in, no numbering of the cells. Nothing may be labelled with its own name.
Do not render any of the words of this description into the image.
```

### What to do with the result

`tools/quest_plates.py` (to be written alongside the sheet) cuts the nine cells, keys the magenta the same way
`quest_frames.py` does, trims each piece to its own bounds, and measures each one's border band — the thickness, in
pixels, of the ornamented edge on each side — into `assets/quest/plates.json`, so `qBtn` can nine-slice a plate at
any size without the insets being hard-coded. The same measure-and-adapt contract the card frames use: the art
states its own geometry and the code reads it, rather than the art being made to fit a number in the code.

If Gemini drifts, regenerate rather than patch. The two failures to watch for, both fatal to a stretched plate: a
centre field that is not even (a vignette or a highlight bloom shows up as a seam the moment the plate is stretched),
and ornament that creeps inward past the border band (it gets stretched and smeared).

---

## The interface plates (one prompt, nine pieces)

The owner, twice: the buttons look like a slide deck. They do, and the reason is that every plate in the game is
drawn in code — a rounded rectangle with a gradient. The paintings are finished; the chrome sitting on them is not.
This sheet replaces the chrome with painted metal, and the owner chose the ornate end of the scale.

Nine pieces, cut the way the card frames are: exact thirds, magenta keyed out, each piece trimmed to its own bounds.
The pieces do **not** share an aspect ratio — a wide lozenge and a tall plaque sit in cells of the same size, each
with magenta around it, and the trim sorts them out.

**Why the centres must be flat.** A button is 180 px wide on one screen and 260 on another, so one fixed picture
cannot serve. The three lozenges are stretched horizontally: left cap, stretched middle, right cap. That works only
if the middle is identical in every column of pixels — a top-to-bottom bevel is fine and wanted, a left-to-right
change is not. The six panels are nine-sliced, so their inner field must be flat in both directions. This is also
what keeps them readable: the ornament is in the border, the lettering sits on a quiet field.

Resolution is enough even where a piece looks small on the sheet. A stretched middle costs nothing, so only the caps
and corners need pixels, and each of those gets a full cell.

```
A single flat technical sheet of nine EMPTY painted interface plates for a painterly fairytale-sci-fi deck-building
game, laid out as a strict 3-column by 3-row grid. These are empty containers that lettering will be drawn on top of
later, in code — so no piece may carry any lettering of its own.

THE SHAPE OF THE IMAGE:
The finished image is SQUARE, 2048 by 2048 pixels. It is divided into nine identical square cells by two perfectly
straight vertical lines at exactly 1/3 and 2/3 of the width, and two perfectly horizontal lines at exactly 1/3 and
2/3 of the height. Each cell holds exactly ONE plate, centred in its cell, upright, drawn straight on with no
perspective and no tilt. The plates are NOT all the same size or shape: each row below states its own proportion.
Nothing may touch or cross a cell boundary.

THE BACKGROUND, AND THE ONLY KEYING COLOUR:
Every pixel that is not part of a plate is FLAT PURE MAGENTA #FF00FF — a solid, uniform, unshaded colour with no
gradient, no texture, no glow and no shadow in it. That means all the empty space between and around the plates, and
the area outside each plate's rounded corners. Each plate's silhouette must end hard against that magenta: no drop
shadow, no outer glow, no soft halo, no reflection spilling outside the shape. Light and depth live INSIDE the
silhouette only.

ROW 1 — three wide pressable plates, each a long horizontal lozenge with fully rounded ends, about 4 units wide to 1
unit tall, filling about 90% of its cell's width:
  Left: polished warm gold metal, bright and lit, the most valuable-looking object on the sheet.
  Middle: polished jade-green metal, the same construction and the same light, bright and inviting.
  Right: dark blued steel with a thin gold rim, deliberately quieter than the other two.

ROW 2 — three rectangular plates with softly rounded corners, about 2 units wide to 1 unit tall, filling about 85% of
its cell's width:
  Left: dark blued steel with a thin pewter rim, quiet.
  Middle: the identical plate, but its metal is warm gold and it is lit as though a lamp sits just above it.
  Right: the identical plate in cold dead grey iron, unlit, as though it has been left in the dark.

ROW 3 — three larger pieces:
  Left: an upright plaque with softly rounded corners, taller than it is wide, about 1 unit wide to 1.3 units tall,
  in dark blued steel with a gold rim.
  Middle: a large upright panel with softly rounded corners, about 1 unit wide to 1.2 units tall, in dark blued steel
  with a heavier gold rim — this one is a window that a whole screen of writing will sit inside.
  Right: a long, low, shallow strip with softly rounded corners, about 5 units wide to 1 unit tall, in dark pewter —
  a small nameplate that a single line will sit on.

HOW ORNATE, AND EXACTLY WHERE THE ORNAMENT MAY GO — this decides whether the sheet is usable:
All nine plates are richly worked: engraved filigree scrollwork, hammered metal, raised rivets, a polished inlay line
following the edge, and a small faceted gem set into each corner where there is room for one. But every bit of that
ornament — every rivet, gem, scroll and bevel — must sit entirely within a narrow band hugging the plate's outer
edge, no thicker than about one sixth of the plate's SHORTER side. Inside that band the plate's face is a quiet,
calm, EVEN field of its own colour: no filigree, no rivets, no scrollwork, no pattern, no vignette, no spotlight, no
scratches, no highlight blooms crossing it.
  On the three lozenges in row 1, that inner face may shade smoothly from lighter at the top to darker at the bottom,
  like a convex surface lit from above — but it must be IDENTICAL all the way across from left to right, so that any
  vertical slice through the middle of the plate looks the same as any other.
  On the six plates in rows 2 and 3, the inner face must be flat and even in BOTH directions: the same tone in the
  middle as at the inner edge of the border band.

LIGHT AND MATERIAL:
One light source, above and slightly to the left, the same for all nine. Each plate reads as a solid thing with
thickness: a lit upper edge, a soft occluded lower edge, a crisp bevel where the face meets the border band. The
metal is real and worked — hammer marks, wear on the raised edges, a little age in the recesses — not smooth plastic
and not a flat vector shape.

COLOUR:
The game's palette: near-black violet #0F0B20 and deep indigo #1D1636 for the dark metal, warm gold #F2C14E for the
gold, bright jade #45D6C2 and #3DDC84 for the green, cream #F6EFE2 as the brightest highlight. Nothing pastel,
nothing washed out, nothing neon.

SYMMETRY:
Every plate must be perfectly symmetrical left to right, so that it can be mirrored for a right-to-left language
without the ornament reading backwards. No piece may have a feature on one side that it lacks on the other.

WHAT MUST NOT BE IN THE IMAGE:
No letters, no words, no numbers, no runes, no glyphs, no logos, no watermark, no caption, no label, and no writing of
any kind anywhere in the picture — not on the plates, not in the magenta, not in the margins. No icons, no swords, no
shields, no hearts, no coins, no faces, no creatures, no hands, no cursor, no arrow. No picture frame around the whole
sheet, no grid lines drawn in, no numbering of the cells. Nothing may be labelled with its own name. Do not render
any of the words of this description into the image.
```

### What to do with the result

`tools/quest_plates.py` — to be written alongside the sheet — cuts the nine cells, keys the magenta the way
`quest_frames.py` does, trims each piece to its own bounds, and measures each one's border band (its thickness in
pixels on each side) into `assets/quest/plates.json`, so `qBtn` can nine-slice a plate at any size without the insets
being hard-coded. That is the same measure-and-adapt contract the card frames use: the art states its own geometry
and the code reads it, rather than the art being made to fit a number in the code.

If Gemini drifts, regenerate rather than patch. Two failures to watch for, both fatal to a stretched plate: a centre
field that is not even (a vignette or a highlight bloom becomes a visible seam the moment the plate is stretched),
and ornament that creeps inward past the border band (it gets stretched and smeared).
