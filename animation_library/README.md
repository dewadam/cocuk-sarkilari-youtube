# Reusable 3D Animation Library

This library stores reusable, AI-generated 3D animation clips for the children's-song pipeline. The target clip length is about 30 seconds.

## Storage rules
- Keep metadata and the searchable index in animation_library/catalog.json.
- Keep MP4 binaries out of normal Git history. Publish them as GitHub Release assets and store their stable HTTPS download URLs in asset_url.
- Never delete the animation archive when cleaning up monthly song inputs/outputs.
- Generated song videos and temporary downloads are disposable; approved archive clips and catalog records are persistent.

## Catalog fields
- clip_id: unique stable ID, e.g. ANIM_000001
- file_name: descriptive MP4 name
- category, tags, keywords: categories and Turkish search terms
- characters, actions, environments, moods: structured matching fields
- duration_seconds, loopable, approved, prompt_id, asset_url

## Commands
Validate the catalog:
~~~bash
python app/animation_catalog.py validate
~~~
Search by Turkish phrase:
~~~bash
python app/animation_catalog.py search "tavşan zıplıyor çiftlik" --loopable-only
~~~
Create a lyric-matched playlist:
~~~bash
python app/select_animation_clips.py --lyrics songs/TR002_Hayvan_Dostlarim/lyrics.txt --repeat-to-seconds 120 --output output/TR002/playlist.json
~~~
The selector performs deterministic tag/keyword matching without a paid AI call. A future renderer/download step should fetch only the selected release assets, not the whole archive.
