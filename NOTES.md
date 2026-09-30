# Project notes

## Live URLs
- Grasp (production, deploys from `main`): https://grasp-weld.vercel.app/
- Tremorti (tremor meter): https://grasp-weld.vercel.app/tremorti/

## Deploy
Vercel project `grasp-weld` is linked to the GitHub repo `evilren/grasp`. Every push to `main`
deploys on its own; nothing else is needed. The Claude Vercel connector has no write access,
so deploys are never done from the connector.

Old Vercel projects to delete in the dashboard: grasp-hand-physics, grasp-hands, grasp-play,
grasp-play-2 … grasp-play-6.

## Grasp modes
Sandbox, Slice (katana), Smash (fist, walls, cars), Busy Board (18 toddler widgets), Strike (3D corridor, walls).
Each mode has a Playwright suite under tests/.

## Working branch
Claude develops on `ccr-61aa39be-e8m1zx` and fast-forwards `main` to it after tests pass.

## Tests
`bash tests/run.sh` (Grasp) and `bash tremorti/tests/run.sh` (Tremorti). Headless Chromium,
fake camera, stubbed hand tracker. Real hand detection and real sensors are only verified on a phone.

## Phone findings
- Samsung / Brave / Android: the GPU hand tracker runs but never finds a hand. Phones now start on
  the CPU tracker; confirmed working ("tracked Right", ~9 scans/s).
