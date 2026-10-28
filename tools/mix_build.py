#!/usr/bin/env python3
"""Mix (the merge + discover game): check the item list and write assets/mix/mix.json.

  python3 tools/mix_build.py            (reads tools/mix_items.txt; prints the checks; writes the JSON only when every hard check passes)

tools/mix_items.txt, one entry a line ('#' starts a comment):
  cat: <id> | <emoji> | <English> | <Hebrew>
  item: <id> | <emoji> | <English> | <Hebrew> | <cat id> [| <badge emoji>]
  <a> + <b> = <c>                     (a recipe; a + a is a merge of two of the same)
The four base items are water, fire, earth, air (they come from the sources; no recipe makes them).
A badge is a small second emoji drawn in the item's corner, for two items that share an emoji (big wave = 🌊 + ⬆️): (emoji, badge) is unique.
Hard checks: ids, names, emoji (Unicode 13 or older: they show on phones from 2020 on), every recipe's items exist, a pair makes one thing,
nothing makes a base item or itself, every item has a recipe and can be reached from the base four. Soft checks (printed): counts, merges
(a + a), dead ends, depth.
JSON: { v, base, cats: [{ id, e, en, he }], items: [{ id, e, b?, en, he, c, d (depth: steps from the base) }], r: [[a, b, c], ..] }."""
import json, os, re, sys, unicodedata, hashlib
from collections import defaultdict, deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'tools', 'mix_items.txt'); OUT = os.path.join(ROOT, 'assets', 'mix', 'mix.json')
BASE = ['water', 'fire', 'earth', 'air']
# Unicode 14 emoji (2021: too new for many phones); anything newer has no name in Python 3.11's Unicode 14 tables and fails too
U14 = set(range(0x1FAE0, 0x1FAE8)) | set(range(0x1FAF0, 0x1FAF7)) | {0x1F7F0, 0x1FA7B, 0x1FA7C, 0x1F979, 0x1F9CC} | set(range(0x1FAA9, 0x1FAAD)) | \
      set(range(0x1FAB7, 0x1FABB)) | set(range(0x1FAC3, 0x1FAC6)) | set(range(0x1FAD7, 0x1FADA)) | set(range(0x1F6DD, 0x1F6E0))

def emoji_ok(s):
    if not s: return 'empty'
    for ch in s:
        o = ord(ch)
        if o in (0xFE0F, 0x200D) or 0x1F3FB <= o <= 0x1F3FF: continue
        if o in U14: return 'Unicode 14 (too new): U+%X' % o
        try: unicodedata.name(ch)
        except ValueError: return 'unknown / too new: U+%X' % o
    return ''

def main():
    errs, warns = [], []
    cats, items, recipes = {}, {}, []
    for n, raw in enumerate(open(SRC, encoding='utf-8'), 1):
        line = raw.split('#', 1)[0].strip() if not raw.strip().startswith('item:') and not raw.strip().startswith('cat:') else raw.strip()
        if line.startswith('#') or not line: continue
        if line.startswith('cat:'):
            f = [x.strip() for x in line[4:].split('|')]
            if len(f) != 4: errs.append('%d: cat needs 4 fields' % n); continue
            if f[0] in cats: errs.append('%d: cat %s twice' % (n, f[0]))
            cats[f[0]] = { 'id': f[0], 'e': f[1], 'en': f[2], 'he': f[3] }
        elif line.startswith('item:'):
            f = [x.strip() for x in line[5:].split('|')]
            if len(f) not in (5, 6): errs.append('%d: item needs 5 or 6 fields: %s' % (n, line)); continue
            iid = f[0]
            if not re.fullmatch(r'[a-z][a-z0-9_]{0,23}', iid): errs.append('%d: bad id %r' % (n, iid))
            if iid in items: errs.append('%d: item %s twice' % (n, iid))
            it = { 'id': iid, 'e': f[1], 'en': f[2], 'he': f[3], 'c': f[4] }
            if len(f) == 6 and f[5]: it['b'] = f[5]
            for k in ('e', 'b'):
                if k in it:
                    w = emoji_ok(it[k])
                    if w: errs.append('%d: %s emoji %s: %s' % (n, iid, it[k], w))
            if not it['en'] or not it['he']: errs.append('%d: %s needs both names' % (n, iid))
            if re.search(r'[A-Za-z]', it['he']): warns.append('%d: %s Hebrew name has Latin letters: %s' % (n, iid, it['he']))
            items[iid] = it
        else:
            m = re.fullmatch(r'([a-z0-9_]+)\s*\+\s*([a-z0-9_]+)\s*=\s*([a-z0-9_]+)', line)
            if not m: errs.append('%d: cannot read: %s' % (n, line)); continue
            recipes.append((m.group(1), m.group(2), m.group(3), n))
    for iid, it in items.items():
        if it['c'] not in cats: errs.append('item %s: unknown cat %s' % (iid, it['c']))
    for b in BASE:
        if b not in items: errs.append('base item %s missing' % b)
    seen_e = {}
    for iid, it in items.items():
        k = (it['e'], it.get('b', ''))
        if k in seen_e: errs.append('items %s and %s look the same (%s%s): give one a badge' % (seen_e[k], iid, it['e'], it.get('b', '')))
        seen_e[k] = iid
    for lang in ('en', 'he'):
        names = defaultdict(list)
        for iid, it in items.items(): names[it[lang].lower()].append(iid)
        for nm, ids in names.items():
            if len(ids) > 1: errs.append('%s name %r used by %s' % (lang, nm, ids))
    pairs, makes = {}, defaultdict(list)
    for a, b, c, n in recipes:
        for x in (a, b, c):
            if x not in items: errs.append('%d: unknown item %s' % (n, x))
        key = tuple(sorted((a, b)))
        if key in pairs: errs.append('%d: %s + %s already makes %s' % (n, a, b, pairs[key]))
        pairs[key] = c
        if c in BASE: errs.append('%d: nothing makes a base item (%s)' % (n, c))
        if c in (a, b): errs.append('%d: %s makes itself' % (n, c))
        makes[c].append(key)
    for iid in items:
        if iid not in BASE and not makes[iid]: errs.append('item %s: no recipe makes it' % iid)
    # reachability and depth (a recipe works once both its items are reached)
    depth = { b: 0 for b in BASE if b in items }; changed = True
    while changed:
        changed = False
        for (a, b), c in pairs.items():
            if a in depth and b in depth and c in items:
                d = max(depth[a], depth[b]) + 1
                if c not in depth or d < depth[c]: depth[c] = d; changed = True
    for iid in items:
        if iid not in depth: errs.append('item %s cannot be reached from the base four' % iid)
    used = set(x for k in pairs for x in k)
    dead = [i for i in items if i not in used]
    self_m = sum(1 for (a, b) in pairs if a == b)
    by_cat = defaultdict(int)
    for it in items.values(): by_cat[it['c']] += 1
    print('items %d, cats %d, recipes %d (merges a + a: %d), recipes per item %.2f' % (len(items), len(cats), len(pairs), self_m, len(pairs) / max(1, len(items) - 4)))
    print('dead ends (make nothing): %d (%.0f%%)' % (len(dead), 100 * len(dead) / max(1, len(items))))
    if depth: print('depth: max %d; per depth %s' % (max(depth.values()), [sum(1 for v in depth.values() if v == d) for d in range(max(depth.values()) + 1)]))
    print('per cat:', dict(by_cat))
    if not 340 <= len(items) <= 360: warns.append('items: %d (want 340-360)' % len(items))
    if self_m < 60: warns.append('merges a + a: %d (want 60+)' % self_m)
    if len(dead) > 0.3 * len(items): warns.append('too many dead ends')
    for c, k in by_cat.items():
        if k < 8: warns.append('cat %s has only %d items' % (c, k))
    for w in warns: print('WARN', w)
    for e in errs: print('ERROR', e)
    if errs: print('NOT WRITTEN: %d errors' % len(errs)); sys.exit(1)
    data = { 'base': BASE, 'cats': list(cats.values()), 'items': [dict(it, d=depth[i]) for i, it in items.items()], 'r': [[a, b, c] for (a, b), c in pairs.items()] }
    data['v'] = hashlib.sha1(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:8]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('written', OUT, os.path.getsize(OUT), 'bytes, v', data['v'])

if __name__ == '__main__': main()
