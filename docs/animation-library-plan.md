# Animation Archive: Operating Plan

## Goal
Build a growing library of reusable AI-generated 3D animation clips, approximately 30 seconds each. Clips are tagged once and reused across future songs.

## Monthly workflow
1. Generate a batch of candidate clips during a planned Azure GPU session.
2. Validate MP4 readability, duration, dimensions, file size and visual quality.
3. Assign stable IDs and metadata: category, Turkish keywords, characters, action, environment, mood, loopability, prompt ID, source model and license.
4. Publish approved MP4s as GitHub Release assets; never commit MP4s into normal Git history.
5. Add their HTTPS release asset URLs to animation_library/catalog.json.
6. For each song, normalize lyrics and rank approved clips by tags and keywords.
7. Download only selected clips, repeat loopable clips until audio duration is covered, render and run QC.
8. Delete temporary downloads, song source copies and finished song outputs according to cleanup policy. Never delete release assets or catalog entries.

## File naming
Use ASCII slugs for stable filenames while keeping Turkish labels in metadata: category_subject_action_sequence.mp4.

Examples: animal_rabbit_hop_001.mp4, animal_bear_dance_001.mp4, farm_lamb_run_001.mp4, group_animals_dance_001.mp4.

Each clip should have a sidecar JSON record that is validated before being added to the catalog.

## Storage
The normal Git repository holds source code and small metadata. GitHub Releases are the first archive backend so MP4 binaries do not inflate Git history. Each asset must remain below GitHub's 2 GiB per-release-asset limit. Do not download the whole archive on every song run.

## Quality rules
- Do not catalog a clip unless it is playable and approved.
- Keep loopable=false when the first/last frames have an obvious discontinuity.
- Keep character design consistent using stable prompt references when the chosen video model supports them.
- Never mark a procedural placeholder as an AI-generated 3D clip.
- If no suitable match exists, report that the catalog needs more coverage; do not fabricate assets.
