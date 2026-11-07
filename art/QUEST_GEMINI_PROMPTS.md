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

### The button row, re-run (one prompt, three pieces)

Six of the nine pieces measured as usable and are in the game. The top row — the three button shapes, the pieces
that matter most, since Start and End turn are what the whole screen is built around — came back as **ovals**:
1.81 : 1 instead of the 4 : 1 asked for, with a silhouette whose top edge rises and falls 38 px across the middle
where the panels' varies by one. Stretched to a real button that reads as a flat lens with no room at its ends for
a word, and a rim that changes thickness along its length.

The word "lozenge" is what did it: it was read as a gem shape. This re-run never names a shape in the abstract. It
builds the outline out of named parts, says what each end is a copy of, and states the test the piece has to pass.

```
A single flat technical sheet of three EMPTY painted interface buttons for a painterly fairytale-sci-fi deck-building
game, side by side in one horizontal row. These are empty containers that lettering will be drawn on top of later,
in code — so no piece may carry any lettering of its own.

THE SHAPE OF THE IMAGE:
The finished image is 2048 pixels wide by 1024 pixels tall. It is divided into three equal upright cells by two
perfectly straight vertical lines at exactly 1/3 and 2/3 of the width. Each cell holds exactly ONE button, centred
in its cell, drawn straight on with no perspective and no tilt.

THE SHAPE OF EACH BUTTON — this is the whole point of the sheet, so build it exactly this way:
Each button is a long, flat, horizontal BAR, about 4.5 times as wide as it is tall, filling about 92% of its cell's
width. Picture a rectangle with a half-circle stuck on each end — the shape of a running track, a pill, a capsule.
  * Its TOP edge is a single straight horizontal line, perfectly level, running the entire width of the button
    between the two rounded ends. It does not arch, bulge, dome or curve upward in the middle, by any amount.
  * Its BOTTOM edge is the same straight horizontal line, mirrored.
  * Only the two ENDS are round: each end is a clean half-circle whose diameter is exactly the height of the bar.
It is NOT an oval, NOT an ellipse, NOT a lens, NOT an egg, NOT a shield and NOT a gem. An oval — a shape whose top
edge curves all the way across — is the one thing this sheet must not contain. If the middle of the top edge sits
even slightly higher than the point where the rounded end meets it, the piece is wrong and unusable.

THE TEST THE SHAPE MUST PASS:
The button will be cut into three vertical strips — left end, middle, right end — and the middle strip stretched to
make the button wider or narrower. So the middle of the button must be the same from left to right: take any two
vertical lines through the middle half of the button, and everything along them must match — the same height, the
same rim thickness top and bottom, the same colours at the same heights. Nothing in the middle may be wider in one
place than another, and nothing may sit at the centre that does not repeat all the way along.

THE BACKGROUND, AND THE ONLY KEYING COLOUR:
Every pixel that is not part of a button is FLAT PURE MAGENTA #FF00FF — solid, uniform, unshaded, with no gradient,
no texture, no glow and no shadow in it. Each button's silhouette ends hard against that magenta: no drop shadow,
no outer glow, no soft halo, nothing spilling outside the shape. Light and depth live INSIDE the silhouette only.
Do not draw the dividing lines between the cells: leave plain magenta between the buttons.

THE THREE BUTTONS — identical construction and identical light, only the metal changes:
  Left: polished warm gold, bright and lit, the most valuable-looking object on the sheet.
  Middle: polished jade green, the same construction and the same light, bright and inviting.
  Right: dark blued steel with a thin gold rim, deliberately quieter than the other two.

WHERE THE ORNAMENT MAY GO:
Each button is richly worked — engraved filigree, hammered metal, a polished inlay line following the edge, a small
raised rivet, and one small faceted gem set into each rounded end. All of it must sit either in the two rounded ends
or in a narrow band hugging the top and bottom edges, no thicker than about one fifth of the button's height. The
long middle face between those bands is a quiet, calm, even surface: no filigree, no rivets, no scrollwork, no
pattern, no vignette, no spotlight, no scratches, no highlight bloom. It may shade smoothly from lighter at the top
to darker at the bottom, like a rounded surface lit from above, and that shading must be identical all the way
across from left to right.

LIGHT AND MATERIAL:
One light source, above and slightly to the left, the same for all three. Each button reads as a solid thing with
thickness: a lit upper edge, a soft occluded lower edge, a crisp bevel where the face meets the rim. The metal is
real and worked — hammer marks, wear on the raised edges, a little age in the recesses — not smooth plastic and not
a flat vector shape.

COLOUR:
The game's palette: near-black violet #0F0B20 and deep indigo #1D1636 for the dark metal, warm gold #F2C14E for the
gold, bright jade #45D6C2 and #3DDC84 for the green, cream #F6EFE2 as the brightest highlight. Nothing pastel,
nothing washed out, nothing neon.

SYMMETRY:
Each button must be perfectly symmetrical left to right and top to bottom, so it can be mirrored for a right-to-left
language without the ornament reading backwards.

WHAT MUST NOT BE IN THE IMAGE:
No letters, no words, no numbers, no runes, no glyphs, no logos, no watermark, no caption, no label, and no writing
of any kind anywhere in the picture — not on the buttons, not in the magenta, not in the margins. No icons, no
swords, no shields, no hearts, no coins, no faces, no creatures, no hands, no cursor, no arrow. No picture frame
around the sheet, no dividing lines drawn in, no numbering. Nothing may be labelled with its own name. Do not render
any of the words of this description into the image.
```

Cut it with `--only=btn_gold,btn_jade,btn_steel`. The slicer already reports the test this row failed: it measures
how far each silhouette's top and bottom edges rise and fall across the middle 60% of the width, and refuses
anything over 6 px. The panels measure 0 to 1 px; this row measured 38 to 41.

---

## The icons (one prompt, twenty-five pieces)

The owner, looking at the victory screen: there are a lot of bad graphics. The trophy, the crown, the sword and the
coin on that screen are the last things still drawn in code — flat vector shapes with no light in them, sitting on a
painted forest. There are twenty-five of them (`Q_IC` in index.html) and they appear on every screen in the game:
on card faces, in a monster's intent bubble, on the status row, in the top bar, on the doors, in the shop.

A five by five grid, one icon per cell. The order below is the order the slicer reads them in.

| | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **1** | `dmg` | `blk` | `heal` | `en` | `gold` |
| **2** | `str` | `weak` | `vul` | `poi` | `thorns` |
| **3** | `draw` | `disc` | `loop` | `all` | `call` |
| **4** | `skull` | `crown` | `trophy` | `chest` | `shop` |
| **5** | `fire` | `lock` | `cut` | `mystery` | `help` |

**The size they are actually used at decides everything.** These are drawn between 13 and 22 css pixels — about 40
to 66 real pixels on a phone. That is why the prompt asks for two or three big shapes with a heavy dark outline and
nothing fine: a painted icon with delicate detail is a smudge at 16 px, and worse than the flat one it replaced.

`help` is an open book rather than a question mark on purpose. Every other prompt in this file forbids writing in
the image, and asking for one punctuation mark as a shape invites the generator to letter the rest of the sheet —
which it has done before, printing a section heading onto a card plate.

```
A single flat technical sheet of twenty-five painted fantasy game icons, laid out as a strict 5-column by 5-row
grid, for a painterly fairytale-sci-fi deck-building game.

THE SHAPE OF THE IMAGE:
The finished image is SQUARE, 2048 by 2048 pixels, divided into twenty-five identical square cells by four evenly
spaced vertical lines and four evenly spaced horizontal lines. Each cell holds exactly ONE icon, centred in its
cell, upright, drawn straight on with no perspective and no tilt, filling about 70% of its cell so that a clear
empty margin surrounds it on all four sides. No icon may touch, overlap or cross a cell boundary, and no two icons
may touch each other.

THE BACKGROUND, AND THE ONLY KEYING COLOUR:
Every pixel that is not part of an icon is FLAT PURE MAGENTA #FF00FF — solid, uniform, unshaded, with no gradient,
no texture, no glow and no shadow in it. Each icon's silhouette ends hard against that magenta: no drop shadow, no
outer glow, no soft halo, no reflection spilling outside the shape. Light and depth live INSIDE the silhouette
only. Do not draw the lines between the cells: leave plain magenta between the icons.

HOW THESE WILL BE USED, WHICH DECIDES HOW TO DRAW THEM:
Each icon will be shown very small — about the size of a word on a phone screen — on top of a detailed painted
background. So each must be built from only TWO OR THREE large, simple, bold shapes with a clear silhouette, a
strong dark outline all the way round, and strong light-to-dark contrast inside. No thin lines, no fine engraving,
no small ornament, no scattered sparkles, no tiny parts, no clutter. Each icon must still be recognisable as a
black silhouette with no colours at all. Every icon has the same visual weight and the same thickness of outline,
so that they look like one set.

THE TWENTY-FIVE ICONS, in reading order, left to right and then down:
Row 1: a short broad sword, blade upward. A round shield. A heart. A glowing faceted crystal. A gold coin seen face
on.
Row 2: a clenched armoured fist. A sword snapped in half. A shield with a jagged crack across it. A round-bellied
potion bottle with a stopper, full of liquid. A circle woven out of thorny briar.
Row 3: a single playing card lifting off the top of a small stack. A single playing card tumbling away and falling.
A thick circular arrow curling round to meet its own tail. A three-pointed starburst, like one blow landing in
three places at once. A curved war horn.
Row 4: a skull. A crown. A two-handled trophy cup. A closed treasure chest with a domed lid. A drawstring money
pouch, tied at the neck and bulging.
Row 5: a campfire: three logs and a flame. A padlock, body and shackle. A pair of open scissors. A swirling spiral
portal. An open book, seen from above, both pages showing.

COLOUR — each icon is mostly one metal or material, so that colour alone tells them apart at a glance:
The sword, the broken sword and the scissors are pale steel with a gold-bound grip. The shield and the cracked
shield are deep teal and silver. The heart is deep crimson. The crystal is bright jade green, lit from inside. The
coin, the crown, the trophy, the chest's fittings and the pouch's drawstring are warm gold. The fist is dark iron.
The potion is bright poison green glass. The thorn ring is dark bramble brown. The cards are cream with a dark
indigo back. The circular arrow and the starburst are bright jade. The horn is bone and gold. The skull is bone
white. The campfire is orange flame on dark logs. The padlock is iron with a gold body. The portal is violet and
magenta-free deep purple, swirling. The book is cream pages in a dark indigo cover.
The palette they live in: near-black violet #0F0B20, deep indigo #1D1636, warm gold #F2C14E, jade #45D6C2 and
#3DDC84, crimson #FF5A6E, bone #F6EFE2. Nothing pastel, nothing washed out, nothing neon. IMPORTANT: no part of any
icon may be magenta, pink or purple-pink, because that colour is cut away as the background — the portal must be
clearly violet-blue, never pink.

LIGHT AND MATERIAL:
One light source, above and slightly to the left, the same for all twenty-five. Each icon is painted and solid,
with a lit top edge and a shaded underside, so it reads as an object rather than a flat symbol. The metal is real
and worked, with a little wear on its raised edges.

WHAT MUST NOT BE IN THE IMAGE:
No letters, no words, no numbers, no runes, no glyphs, no punctuation, no logos, no watermark, no caption, no label,
and no writing of any kind anywhere in the picture — not on the icons, not on the open book's pages, not on the
cards, not in the magenta, not in the margins. The book's pages and the playing cards are blank. No hands, no
faces, no creatures, no cursor. No picture frame around the sheet, no grid lines drawn in, no numbering of the
cells. Nothing may be labelled with its own name. Do not render any of the words of this description into the
image.
```

### What to do with the result

`tools/quest_icons.py`, written the way `quest_plates.py` ended up: find the pieces rather than cut at fixed
fractions (the generator does not centre its cells), key the magenta, trim each to its own bounds, and write
`assets/quest/icons/<name>.webp` in the order of the table above. Then `qIcon` draws the painted file when it is
there and falls back to the code-drawn shape when it is not, exactly as `qCard` already does with the frames — so
a missing or rejected icon costs nothing.

Check each one at the size it is used, not at the size it was drawn. The failure to watch for is an icon that is
beautiful at 400 px and a grey smudge at 16.

---

## The relics (one prompt, eighteen pieces)

Eighteen relics, every one of them still an emoji — the honey pot, the phoenix feather, the iron boots — sitting in
gold-rimmed medallions along the top bar, in the reward card, in the chest and in the shop.

**The size they are used at.** The medallion in the top bar is the small one, and it moves: the row takes the space
it has, so a player holding three relics sees the symbol at about 28 px and one holding eight sees it at 18. The
reward and chest screens draw it at 40 and 46, the shop at 28. So the art must hold together at **18 px** and may
not depend on anything that only appears above 40.

**What the first icon sheet got wrong, and what this prompt does about it.** Gemini ignored the list of
twenty-five names entirely and invented its own set of generic fantasy items — a key, a helmet, a bow, a pelt —
none of which the game has a slot for. It also drew runes on a scroll and letters on three stones after being told
not to write anything, and it gave each cell its own duller purple panel instead of one flat magenta, so the sheet
had two background colours.

So this prompt numbers the eighteen items, says outright that there are to be no substitutions and no extras,
forbids writing a second time at the point where it is tempting (the map), and states that the magenta is one
single value everywhere including inside the cells.

| | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| **1** | `heart` | `book` | `core` | `clover` | `boot` | `whet` |
| **2** | `pot` | `lantern` | `bag` | `feather` | `snail` | `thorn` |
| **3** | `tea` | `map` | `star` | `magnet` | `egg` | `venom` |

```
A single flat technical sheet of exactly EIGHTEEN painted fantasy treasure objects, laid out as a strict 6-column
by 3-row grid, for a painterly fairytale-sci-fi deck-building game.

THE LIST IS FIXED. The eighteen objects are listed below and numbered 1 to 18. Draw those eighteen, in that order,
reading left to right along the top row, then the middle row, then the bottom row. Do not substitute a different
object for any of them, do not add an object that is not on the list, do not leave one out, and do not reorder
them. The list is not a suggestion of a theme — it is the contents of the picture.

THE SHAPE OF THE IMAGE:
The finished image is 2048 pixels wide by 1024 pixels tall, divided into eighteen identical square cells by five
evenly spaced vertical lines and two evenly spaced horizontal lines. Each cell holds exactly ONE object, centred in
its cell, upright, drawn straight on with no perspective and no tilt, filling about 72% of its cell so that a clear
empty margin surrounds it on all four sides. No object may touch, overlap or cross a cell boundary, and no two
objects may touch each other.

THE BACKGROUND, AND THE ONLY KEYING COLOUR:
Every pixel that is not part of an object is FLAT PURE MAGENTA #FF00FF — ONE single colour everywhere, the same
value in the gaps between the cells as inside each cell, solid, uniform and unshaded, with no gradient, no texture,
no glow and no shadow in it. Do not give the cells their own panel, tile, square, border or darker background: each
object floats directly on the same magenta that fills the rest of the sheet. Each object's silhouette ends hard
against that magenta: no drop shadow, no outer glow, no soft halo, nothing spilling outside the shape.

HOW THESE WILL BE USED, WHICH DECIDES HOW TO DRAW THEM:
Each object will usually be shown very small, about the size of a letter on a phone screen, inside a round
medallion. So each must be built from ONE large bold shape with at most two smaller parts, with a clear outline all
the way round and strong light-to-dark contrast inside. No thin lines, no fine engraving, no chain mail, no small
rivets, no scattered sparkles, no clutter, nothing that disappears when the picture is made small. Each object must
still be told apart from the other seventeen as a plain black silhouette with no colour at all, and each must be a
different colour from its neighbours so it can also be told apart by colour alone.

THE EIGHTEEN OBJECTS:
1. A plump heart, deep rich crimson red, with a thin gold rim.
2. A thick closed book standing upright, dark indigo leather cover, gold clasp and gold page edges.
3. A glowing bright jade crystal held in a dark metal collar, lit from inside.
4. A four-leaf clover, fresh grass green, on a short stem.
5. One heavy armoured boot, brown leather with dark steel plates.
6. A rectangular grey whetstone with one worn hollow along its top.
7. A round-bellied clay honey pot, warm amber, with honey running down one side.
8. A hanging lantern with a glass belly and a warm orange flame inside, a ring on top.
9. A brown leather drawstring pouch, tied at the neck, with gold coins spilling from it.
10. One single large feather standing upright, burning orange and gold at its edges.
11. A snail with a tall spiral shell, the shell warm tan, the body pale grey.
12. A thorny green stem bearing one open rose. The rose is DEEP DARK RED, like wine — it must not be pink or
    magenta in any part.
13. A round white teacup on a saucer, with steam curling from it.
14. A rolled parchment map, partly unrolled, pale cream paper with dark edges. Its surface is completely BLANK: no
    writing, no runes, no symbols, no lines, no drawn coastlines, no compass, nothing marked on it at all.
15. A jagged shard of starlight, pale gold and white, glowing.
16. A horseshoe magnet, red at the curve with bare steel tips.
17. A speckled dragon egg, deep teal green with darker spots.
18. One single curved fang, bone white, with a drop of bright green venom at its point.

LIGHT AND MATERIAL:
One light source, above and slightly to the left, the same for all eighteen. Each object is painted and solid, with
a lit top edge and a shaded underside, so it reads as a real thing rather than a flat symbol, with a little wear
and age on it. They all look like they belong in one set.

COLOUR:
The palette they live in: near-black violet #0F0B20, deep indigo #1D1636, warm gold #F2C14E, jade #45D6C2 and
#3DDC84, crimson #FF5A6E, bone #F6EFE2. Nothing pastel, nothing washed out, nothing neon. IMPORTANT: no part of any
object may be magenta, pink or purple-pink, because that colour is cut away as the background. The rose is the one
to watch: it is dark wine red, never pink.

WHAT MUST NOT BE IN THE IMAGE:
No letters, no words, no numbers, no runes, no glyphs, no inscriptions, no punctuation, no logos, no watermark, no
caption, no label, and no writing or marking of any kind anywhere in the picture — not on the book, not on the map,
not on the whetstone, not on any object, not in the magenta, not in the margins. No hands, no faces, no creatures
beyond the snail, no cursor, no arrow. No picture frame around the sheet, no grid lines drawn in, no panels behind
the objects, no numbering of the cells. Nothing may be labelled with its own name. Do not render any of the words
of this description into the image.
```

### What to do with the result

`tools/quest_icons.py`, built the way `quest_plates.py` ended up: find the pieces rather than cut at fixed
fractions, key the magenta, trim each to its own bounds, and write `assets/quest/relics/<name>.webp` in the order
of the table. `qEmoji(R0.e, ...)` becomes a call that draws the painted file when it is there and falls back to the
emoji when it is not, so a relic that is rejected or missing costs nothing.

Check every one of them at 18 px before shipping any of them, not at the size it was drawn. That check is what
condemned the first icon sheet, where a shield's lion and a helmet's mail were a brown smudge at the size the game
actually uses them.

---

## The events and the last symbols (one prompt, fourteen pieces)

The last emoji in the game. Eight of them are the event screens, where the symbol is drawn at 76 px in the middle
of a painted land — the single worst graphic left. Four are the headings of the how-to pages, drawn at 54 px. The
last two are the coach's pointing hand, 40 px, and a monster face used in the how-to.

These are drawn much larger than the twenty-five symbols were, so detail is allowed here, nearer the relics than
the icons. The monster face is the exception: it also appears small, so it is asked for as a bold shape.

| | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **1** | `ev_well` | `ev_shrine` | `ev_merchant` | `ev_chest` | `ev_fountain` |
| **2** | `ev_robot` | `ev_portal` | `ev_feast` | `map` | `door` |
| **3** | `cards` | `hourglass` | `finger` | `monster` | |

Four things in this prompt are there because a previous sheet got them wrong, and each cost real time:

* **The list is numbered and closed.** The first icon sheet was given twenty-five names and returned its own set of
  generic fantasy items — a key, a helmet, a bow — none of which the game has a slot for.
* **One symbol is one connected shape.** A sword drawn snapped into two separate halves was read as two pieces, and
  every name after it in its row was written to the wrong file: the cracked shield was saved as the potion.
* **One flat magenta, no panel behind anything.** Both icon sheets gave each cell its own duller square. It keyed
  out, but it is one more thing that can go wrong.
* **PNG, not JPEG.** The plates sheet arrived as a JPEG, and a 2 px line the generator drew across one plate became
  a soft 6 px dip that no threshold could remove without smearing the artwork on every other piece. That plate had
  to be abandoned.

```
A single flat technical sheet of exactly FOURTEEN painted fantasy game symbols for a painterly fairytale-sci-fi
deck-building game, arranged in three rows: five across the top row, five across the middle row, and four across
the bottom row, left aligned, with the fifth position of the bottom row left empty.

SAVE THE IMAGE AS A PNG, not a JPEG. Hard edges and flat colour must stay hard and flat.

THE LIST IS FIXED. The fourteen symbols are listed below and numbered 1 to 14. Draw those fourteen, in that order,
reading left to right along the top row, then the middle row, then the bottom row. Do not substitute a different
object for any of them, do not add a symbol that is not on the list, do not leave one out, and do not reorder them.
The list is not a suggestion of a theme — it is the contents of the picture.

THE SHAPE OF THE IMAGE:
2400 pixels wide by 1440 pixels tall. Each symbol is centred in its own position, upright, drawn straight on with
no perspective and no tilt, filling about 70% of the space it has, with a clear empty margin all round. No symbol
may touch, overlap or cross into a neighbour's space, and no two symbols may touch each other.

ONE SYMBOL IS ONE CONNECTED SHAPE:
Do not draw any symbol as two or more separate pieces with background showing between them. Every part of a symbol
must be joined to the rest of it. A symbol made of loose pieces is cut up wrongly by the tool that reads this sheet.

THE BACKGROUND, AND THE ONLY KEYING COLOUR:
Every pixel that is not part of a symbol is FLAT PURE MAGENTA #FF00FF — ONE single colour everywhere, the same
value behind every symbol as in the gaps between them, solid, uniform and unshaded, with no gradient, no texture,
no glow and no shadow in it. Do not give any symbol its own panel, tile, square, border, circle or darker
background: each floats directly on the magenta. Each symbol's silhouette ends hard against that magenta: no drop
shadow, no outer glow, no soft halo, nothing spilling outside the shape. Do not draw any lines between the symbols.

HOW THESE WILL BE USED:
Most of these are shown at about the size of a thumbnail on a phone, on top of a detailed painted background. Each
needs a clear bold silhouette and a strong dark outline all the way round, and must still be told apart from the
other thirteen as a plain black shape with no colour at all. Detail inside is welcome, but nothing so fine that it
turns to mush when the picture is made small.

THE FOURTEEN SYMBOLS:
1. A stone wishing well: a round grey stone wall, a little wooden roof on two posts, a bucket hanging under it.
2. An old shrine: a small weathered stone archway, standing alone, moss growing on it, grey-green stone.
3. A friendly old wizard standing, in a deep blue robe and a tall pointed hat, with a long white beard and a
   wooden staff. Kindly, not frightening.
4. A locked chest: dark wood bound in black iron, with a heavy iron padlock hanging on the front.
5. A fairy: a small winged figure, glowing, with pale jade-green light around her and translucent wings. Her light
   is green and gold — never pink.
6. A small lost robot standing, boxy and rusty, with one round glowing cyan eye and short stubby arms.
7. A standing portal: a tall stone archway with swirling violet and deep blue light filling the opening. The light
   is violet and blue, never pink.
8. A feast: a big roast on a wooden platter with a round loaf of bread beside it, joined as one shape.
9. A folded paper map, open and flat, pale cream paper with worn edges, with one simple dark dotted line crossing
   it and a small red cross at its end. No letters, no numbers, no compass, no coastlines, nothing else on it.
10. A closed wooden door seen face on: planks bound with two black iron bands and a round iron ring handle.
11. A fan of three playing cards, held together and spread, cream faces, dark indigo backs, completely blank.
12. An hourglass in a dark wooden frame, clear glass, warm gold sand running through it.
13. A pointing hand: a cartoon glove in cream with a dark outline, index finger pointing straight up, the other
    fingers curled, seen face on.
14. A monster's face: one round creature's head, bright green, with two big round eyes and a wide toothy grin,
    bold and simple so it still reads when it is tiny.

FIGURES:
The wizard, the fairy, the robot and the monster face are the only figures in the picture. No other symbol may have
a face, a figure, hands or eyes.

LIGHT AND MATERIAL:
One light source, above and slightly to the left, the same for all fourteen. Each symbol is painted and solid, with
a lit top edge and a shaded underside, so it reads as a real thing rather than a flat drawing. They all look like
they belong in one set.

COLOUR:
The palette: near-black violet #0F0B20, deep indigo #1D1636, warm gold #F2C14E, jade #45D6C2 and #3DDC84, crimson
#FF5A6E, bone #F6EFE2. Nothing pastel, nothing washed out, nothing neon. IMPORTANT: no part of any symbol may be
magenta, pink or purple-pink, because that colour is cut away as the background. The fairy's glow and the portal's
light are the two to watch: both are green-gold and violet-blue, never pink.

WHAT MUST NOT BE IN THE IMAGE:
No letters, no words, no numbers, no runes, no glyphs, no inscriptions, no punctuation, no logos, no watermark, no
caption, no label, and no writing or marking of any kind anywhere in the picture — not on the map, not on the
cards, not on the shrine, not on any symbol, not in the magenta, not in the margins. No cursor, no arrow. No
picture frame around the sheet, no grid lines drawn in, no panels behind the symbols, no numbering of the
positions. Nothing may be labelled with its own name. Do not render any of the words of this description into the
image.
```

### What to do with the result

`python3 tools/quest_icons.py art/quest_events_raw.png --set=events --check` first, then without `--check`. The
set is already in the tool, writing into `assets/quest/icons/` with the event pieces prefixed `ev_` so they cannot
collide with a `Q_IC` name.

Then three small changes in the game, none of them art: `qDrawEvent` draws `ev_<id>` instead of the event's emoji,
the how-to page headings take their painted symbol instead of theirs, and `qFinger` draws the hand. Each falls back
to the emoji when a file is missing, the way the heroes, monsters and relics already do.

That leaves the emoji sitting inside the how-to sentences — ⚔️ 💀 🔥 🛒 🎁 ❓ 👑 ⚡ 🛡️ — which is a code job rather
than an art one: those strings have to be split so an icon can be drawn where the emoji is, and in Hebrew that has
to happen without disturbing the line's direction.
