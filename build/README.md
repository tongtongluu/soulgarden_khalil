# Build scripts

Python 3 standard library only. Run from this folder, in order:

```sh
python3 fetch_itunes.py    # → data/soulboy_tracks.json
python3 fetch_lyrics.py    # → raw/lyrics/NN.json   (private, git-ignored)
python3 fetch_features.py  # → raw/audio/NN.m4a (private) + data/soulboy_features.json
python3 coverage.py        # → data/coverage.md
python3 imagery.py         # → data/soulboy_imagery.json (detailed imagery, colour, palette)
python3 songs.py           # → data/songs.json (7 weights from imagery_lexicon.json + features)
python3 fetch_discography.py  # → data/discography.json (10 studio albums, iTunes track lists)
```

## Sources

- **iTunes Search / Lookup API**, storefront `tw` (falls back to `hk`, `cn`, `us`). Album: *Soulboy*, collectionId 201549018, 14 tracks.
- **LRCLIB** `/api/search`, artist `方大同` / `Khalil Fong`, traditional and simplified title variants. A match needs the same artist and title and a duration within 3 s of iTunes. Confidence is `high` at ≤1 s, `medium` at ≤3 s.
- **ReccoBeats** `POST /v1/analysis/audio-features`, uploading each 30 s iTunes preview. Spotify IDs need Spotify API credentials, so the `/v1/track?ids=` route is not used. The endpoint does not return key or mode.
- **librosa**: not installed, so tempo / RMS / spectral centroid / key from the previews are skipped. `fetch_features.py` computes them when `import librosa` works.

## Imagery

- `imagery.py`: 10 detailed categories and colour words, counted with a greedy longest-first lexicon match over the full LRCLIB lyrics. Choruses count each time they repeat. Palette, mood and hover quote (≤15 characters) are hand-curated, not measured.
- `songs.py`: 7 weights (love, light, sun, night, nature, water, solitude) from `imagery_lexicon.json`, normalised to sum to 1. Equal weights and `sparse: true` when a track has fewer than 4 hits in total. `intensity` is energy min-max normalised across the album.

- `stoplist.txt`: words that match a lexicon group but are not something you can see (time words, verbs, abstract words). `songs.py` drops them from the `imagery` counts; "fall" is kept only on lines that list the seasons. Later albums should be segmented into whole words with jieba before matching, and write `imagery` and `terms` per song into `data/songs.json`.

- `rhythm.json`: measured rhythm per Soulboy track (numpy onset/beat analysis of the 30 s previews). `songs.py` uses its `tempo_measured` as `tempo` (the ReccoBeats tempo was often not a pulse in the clip) and copies `meter`, `beats_per_bar` and `feel`.

## What is not published

`raw/` holds full lyrics and preview audio and is in `.gitignore`. Only derived data goes in `data/`.

## Caveats

- Features describe the 30 s preview, not the whole song.
- iTunes gives some tracks a 2005-07-22 release date and others 2005-11-16; the album record says 2005-11-16.
