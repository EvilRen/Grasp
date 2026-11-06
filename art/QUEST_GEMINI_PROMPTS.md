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

THE OPENINGS — these are holes, and this is the most important part:
Each frame has three empty areas, and every one of them must be filled with FLAT PURE MAGENTA #FF00FF — a solid,
uniform, unshaded keying colour with no gradient, no texture, no glow and no shadow inside it, so it can be cut to
transparency. Measured as percentages of that card's own width (W) and height (H), from the card's top-left corner:
  1. THE PICTURE WINDOW: a rounded rectangle starting 11.5% of W from the left and 10% of H from the top, 77% of W
     wide and 39.5% of H tall. The frame's metal surrounds it as a recessed, bevelled opening with a crisp inner lip.
  2. THE TITLE PLATE: a rounded horizontal bar starting 9.5% of W from the left and 53.5% of H from the top, 81% of W
     wide and 10% of H tall. It sits proud of the surface like an inlaid nameplate, with a lit top edge.
  3. THE RULES PANEL: a rounded rectangle starting 10% of W from the left and 69.5% of H from the top, 80% of W wide
     and 20.5% of H tall. A sunken, slightly recessed tablet in the lower half.
There is NO fourth opening. Do not cut a socket, a disc, a jewel mount or a hole of any kind into either top
corner — the game paints an opaque cost gem over that corner itself and would hide it completely.

SYMMETRY — as important as the measurements:
The frame must be exactly symmetric left to right: its left half is the mirror image of its right half. Both top
corners are plain and identical, carrying the same ornament as each other, with no socket, mount, badge or
emblem in either one, and nothing that a disc covering 29.6% of the card's width would half-cover. The three
openings are all centred on the card's vertical centreline.
The background of the whole sheet — everything outside the nine cards — is also flat pure magenta #FF00FF.
Do not draw a transparency checkerboard. Do not draw a grey and white chequered pattern of little squares in any
opening or anywhere on the sheet. The openings are not transparent and are not a checker pattern: they are painted
a solid flat magenta, the same magenta everywhere, as if filled with one pot of paint.

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
illustration or character or landscape of any kind, nothing at all inside any of the three magenta openings. No drop
shadows on the magenta. No watermark, no signature, no border around the sheet, no caption, no label, no grid lines
drawn on the image. Only the nine empty frames on magenta.
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
