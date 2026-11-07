# Quest — Gemini prompts for the three missing board panels

The board at `quest_art_direction_board.png` is complete except for the backdrop strip and a
clean icon row. These three prompts fill the gaps. Paste **one block at a time** into Gemini —
one prompt, one image. Do not ask for a sheet or a grid; Gemini composes multi-panel sheets by
labelling them, and a label is the one thing this board cannot have.

**Save the results into `panels/` under these exact names**, then re-run the compositor:

| Save as | From prompt |
|---|---|
| `panels/bg_forest.png` | A |
| `panels/bg_cosmic.png` | B |
| `panels/icons.png` | C (replaces the current `icons.webp`) |

```bash
python3 art/art-direction/build_board.py
```

`build_board.py` accepts `.webp`, `.png`, `.jpg` or `.jpeg` and cover-crops each panel into its
cell, so the framing does not need to be exact — only the aspect ratio and the style.

---

## Why these prompts are shaped the way they are

Gemini is far more eager to add captions than Z-Image is. Three habits defeat it:

1. **Name the artefact, not the subject.** Open with "a single finished painting", never "an
   art board" or "a sheet" — the latter reads as *infographic*, and infographics get labels.
2. **Forbid the frame, not just the words.** "No caption, no title, no label, no border, no
   margin, no card, no UI panel" — Gemini adds text *inside decorations*, so removing the
   decoration removes the text.
3. **Describe the ornament you want.** Saying "no runes" produces runes; saying "purely
   ornamental spirals and knotwork with no writing of any kind" does not. This is the same
   trick that fixed the SKILL card in `QUEST_ART_DIRECTION_PROMPTS.md`.

---

## Prompt A — enchanted forest backdrop  (ask for 16:9 widescreen)

```
A single finished painting, filling the entire frame edge to edge, in a wide 16:9 cinematic
widescreen shape.

SUBJECT: a luminous enchanted forest at night, seen as a battle backdrop looking into the
depth of the wood. Colossal ancient trees with gnarled exposed roots frame the left and right.
Bioluminescent teal spores and glowing motes drift through the air. Patches of softly glowing
moss and pale mushrooms cluster along the roots. A single faint shaft of warm antique gold
light breaks through the dense canopy from high on the left. Low teal ground mist pools across
the floor. The centre foreground is deliberately empty and clear -- an open arena with no
creature, no figure and no character of any kind standing in it.

STYLE: painterly digital illustration, oil and gouache brushwork with crisp rendered edges,
the look of premium hand-painted collectible card game key art. Dramatic rim lighting, soft
volumetric glow, gentle bioluminescence, deep atmospheric depth, rich but uncluttered, very
high detail, cinematic contrast, low-key and moody.

COLOUR: a deep dark near-black base. Teal is the dominant accent, antique gold is the warm
secondary, and crimson appears only as a faint distant spark. No other hues.

ABSOLUTELY NOT: no text, no letters, no words, no numbers, no captions, no titles, no labels,
no logo, no watermark, no signature. No border, no frame, no margin, no matte, no card, no UI
panel, no vignette strip. The painting must bleed to all four edges. Nothing in this image is
an annotation of anything.
```

## Prompt B — cosmic star-portal backdrop  (ask for 16:9 widescreen)

```
A single finished painting, filling the entire frame edge to edge, in a wide 16:9 cinematic
widescreen shape.

SUBJECT: a vast swirling star-portal in deep space, seen as a battle backdrop. A great
circular rift of radiant antique gold and teal energy hangs in the centre distance, its rim
burning brightest. Swirling violet and crimson nebula clouds spiral inward toward it.
Scattered brilliant stars and slowly drifting broken stone fragments catch the rim light along
their edges. The near foreground is a dark empty platform of shattered rock, deliberately
clear -- no creature, no figure and no character of any kind standing on it.

STYLE: painterly digital illustration, oil and gouache brushwork with crisp rendered edges,
the look of premium hand-painted collectible card game key art. Dramatic rim lighting, soft
volumetric glow, gentle bioluminescence, deep atmospheric depth, rich but uncluttered, very
high detail, cinematic contrast, low-key and moody.

COLOUR: a deep dark near-black base. Antique gold and teal carry the portal; violet and
crimson stay in the nebula as deep desaturated support, never brighter than the gold.

ABSOLUTELY NOT: no text, no letters, no words, no numbers, no captions, no titles, no labels,
no logo, no watermark, no signature. No border, no frame, no margin, no matte, no card, no UI
panel. The painting must bleed to all four edges. No constellation that spells anything.
```

## Prompt C — the six UI icons  (ask for a wide 21:9 banner)

The current icon row fails because the sword overlaps the poison droplet and reads as five
icons, not six. The fix is to state the spacing as a hard rule and to give each icon its own
share of the width.

```
A single finished painting of exactly six separate fantasy mobile-game interface icons,
arranged in one straight horizontal row on a plain deep near-black background, in a wide
21:9 banner shape.

LAYOUT -- this is the strict part: the width is divided into six equal invisible columns, and
exactly one icon sits centred in each column. Every icon is the same visual size and sits on
the same horizontal centreline. There is a clear empty gap of dark background between every
pair of neighbours. No icon touches, overlaps, crosses in front of or casts onto any other
icon. Six distinct separated objects, never five, never seven.

THE SIX, strictly left to right:
  1. a faceted glowing teal energy crystal, standing upright
  2. an antique silver and teal heraldic shield, plain and smooth-faced
  3. a steel sword with a crimson-wrapped hilt, standing perfectly upright, point to the top
  4. a glowing toxic green poison droplet, teardrop shape, point to the top
  5. a bold antique gold arrow pointing straight up
  6. a glowing crimson heart

STYLE: all six share one identical painterly digital illustration style -- oil and gouache
brushwork with crisp rendered edges, chunky compact forms, bold simple instantly readable
silhouettes, soft volumetric glow around each, teal and gold rim light, subtle inner shading.
Premium game asset sheet quality, clean and uncluttered, very high detail.

COLOUR: deep dark near-black background. Teal, antique gold and crimson accents, plus the one
toxic green on the droplet only.

ABSOLUTELY NOT: no text, no letters, no words, no numbers, no digits, no captions, no labels
under or beside the icons, no tooltips, no counters, no badges, no logo, no watermark, no
signature. No boxes, frames, plates, circles or buttons behind the icons -- each icon floats
free on the dark background.
```

---

## Prompt D — replacement for the teal card frame

The teal frame in hand has runic lettering baked into the title plate and along the border.
Grasp paints the card's title itself, in English or Hebrew, over that plate -- so any lettering
in the art ends up underneath live text. It has to go.

Two things to change when regenerating, both already specified in `art/QUEST_GEMINI_PROMPTS.md`:

1. **The openings must be flat pure magenta `#FF00FF`, not a checkerboard.** Gemini cannot
   output an alpha channel; asked for transparency it *paints a grey checkerboard*, which
   `tools/quest_frames.py` cannot key out. Flat magenta it can key perfectly.
2. **Replace the rune instruction.** Swap any "runes" or "runic" wording for:

   > the metal carries purely ornamental raised scrollwork, interlocking knotwork, spirals and
   > leaf motifs -- decorative shapes only, with no writing, no alphabet, no runes and no
   > characters of any kind anywhere on the frame, and the title plate is a completely smooth
   > unmarked flat magenta bar.

The violet-and-gold frame does not have this problem -- its plate is clean. Only its openings
need to be regenerated as flat magenta instead of checkerboard.
