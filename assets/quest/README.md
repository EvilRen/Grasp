# assets/quest/

The art Quest loads. Every file here is optional: the game paints the same thing in code to the same layout
(`qLay()` in index.html), so a missing file is never a hole — it is simply the painted version.

```
frame_attack.webp  frame_attack_u.webp  frame_attack_r.webp   the card frames: a column per card type,
frame_skill.webp   frame_skill_u.webp   frame_skill_r.webp    _u uncommon, _r rare (a starter and a
frame_power.webp   frame_power_u.webp   frame_power_r.webp    common share the plain one)
art/<card id>.webp                                            a card's own picture for its window (optional)
```

The frames carry **no text and no symbols** — Grasp draws the title, the cost and the rules over them, in English or
in Hebrew. Make them from the one prompt in `art/QUEST_GEMINI_PROMPTS.md`, measure the sheet against the layout the code
draws to with `python3 tools/quest_frames.py art/quest_frames_raw.png --check`, and slice it with
`python3 tools/quest_frames.py art/quest_frames_raw.png`. Run `--check` first: a frame whose window is a few
percent off crops every illustration, and nothing shows that until the art is in the game.

The frame carries **no cost socket** and is symmetric left to right. In Hebrew `qLay()` moves the cost gem to the
other corner, but `qPaintGem()` paints an opaque gem of exactly the gem radius, so a socket cut in the art would be
invisible anyway — measured, cutting one changes 2.06% of the pixels in that corner, which is only the
semi-transparent shadow ring at 1.04r. Keeping the frame symmetric means it never has to be mirrored per language,
which is what would otherwise flip its rim light away from the game's top-left convention.

Still to come: `icons/` (the status and resource icons), `enemies/`, `lands/`.
