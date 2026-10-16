# The pet's 3D dragon: sources and licence

Both models are from **Quaternius, "Ultimate Monsters"** (https://quaternius.com/packs/ultimatemonsters.html, October 2022), released under
**CC0 1.0 Universal (public domain dedication)**, https://creativecommons.org/publicdomain/zero/1.0/.

| File | Mirror path (under `Assets/Ultimate Monsters/`) | sha256 of the source .gltf | sha256 of the .glb here |
| --- | --- | --- | --- |
| `Flying_Dragon.glb` (265 KB, 4,562 triangles) | `Flying/glTF/Dragon.gltf` | `5438bbaada52a6f6859f7f50c406f63771a4406403c41691add013be6243433a` | `ddf7af28c9180ee048990c537e74fce38cac2ca29659ff2f6494cd883baf41a3` |
| `Flying_Dragon_Evolved.glb` (555 KB, 7,440 triangles) | `Flying/glTF/Dragon_Evolved.gltf` | `36bb52a2de81571389cfe9957346d43d25e75687b6f766b8e792a50df90ee2f3` | `6b2e94d772402c9a2f7cf38506093e5aad3cd4a9436f63ddc3349e38ac8de882` |

- Copy used: the mirror https://github.com/mika314/KitchenSink at commit `ac3ac2a898cbd111a0a94a0cc45783112740e496` (2023-03-11). Its
  `Assets/Ultimate Monsters/License.txt` reads "License: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication" (the header names another pack:
  Quaternius reuses one License.txt template; the licence line is what counts). The official site
  (github.com/Quaternius/quaternius.github.io, commit `c219437bd230a5e66e1b523dbd8ee2bcf0dfb90b`, 2026-10-15) still lists this pack as CC0.
- Conversion: each `.gltf` (embedded base64 buffer) was repacked as a binary `.glb`. The data is unchanged: same meshes, materials, skeleton
  and animations (Death, Fast_Flying, Flying_Idle, Headbutt, HitReact, No, Punch, Yes). No textures (material colours only). At run time the
  game tints the `Dragon_Main` / `Dragon_Secondary` material colours to the pet's chosen colour and brightens `Eye_White`; the files are untouched.
- Quaternius' newer "Quaternius Asset License (QAL) v1.0" (2026) does **not** affect these files: they come from a 2023 copy distributed under
  CC0, CC0 cannot be revoked, and the QAL itself (section 7) says its changes do not apply retroactively to assets obtained under an earlier
  licence. (Even under the QAL, shipping the models inside the game is allowed; do not republish them as a standalone asset pack.)
- Everything else around the dragon (the egg, hats, scarf, bow tie, glasses, crown, event hats, cookie, hearts, crumbs, poof) is made in code
  in `index.html` (the `pet3d` block).

`/vendor/GLTFLoader.js` is `examples/js/loaders/GLTFLoader.js` from the npm package `three@0.128.0` (registry.npmjs.org, MIT licence,
© 2010-2021 three.js authors), unchanged (sha256 `5c15967ba830918a9caea6338712c994c354bccd4edc4569bde411c3ec06a3e6`), matching the
self-hosted `/vendor/three.min.js` r128.
