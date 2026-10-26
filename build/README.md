# Build scripts

Python 3 standard library only. Run from this folder, in order:

```sh
python3 fetch_itunes.py    # → data/soulboy_tracks.json
python3 fetch_lyrics.py    # → raw/lyrics/NN.json   (private, git-ignored)
python3 fetch_features.py  # → raw/audio/NN.m4a (private) + data/soulboy_features.json
python3 coverage.py        # → data/coverage.md
```

## Sources

- **iTunes Search / Lookup API**, storefront `tw` (falls back to `hk`, `cn`, `us`). Album: *Soulboy*, collectionId 201549018, 14 tracks.
- **LRCLIB** `/api/search`, artist `方大同` / `Khalil Fong`, traditional and simplified title variants. A match needs the same artist and title and a duration within 3 s of iTunes. Confidence is `high` at ≤1 s, `medium` at ≤3 s.
- **ReccoBeats** `POST /v1/analysis/audio-features`, uploading each 30 s iTunes preview. Spotify IDs need Spotify API credentials, so the `/v1/track?ids=` route is not used. The endpoint does not return key or mode.
- **librosa**: not installed, so tempo / RMS / spectral centroid / key from the previews are skipped. `fetch_features.py` computes them when `import librosa` works.

## What is not published

`raw/` holds full lyrics and preview audio and is in `.gitignore`. Only derived data goes in `data/`.

## Caveats

- Features describe the 30 s preview, not the whole song.
- iTunes gives some tracks a 2005-07-22 release date and others 2005-11-16; the album record says 2005-11-16.
