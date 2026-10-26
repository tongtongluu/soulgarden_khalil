"""Step f: data/songs.json, one compact object per track for the visual.

Seven imagery weights from build/imagery_lexicon.json (normalised to sum 1),
audio features from data/soulboy_features.json, palette and quote from the
hand-curated EDITORIAL table in imagery.py.
"""
import os

from common import DATA, RAW, read_json, write_json
from imagery import EDITORIAL, tokenize

CATS = ["love", "light", "sun", "night", "nature", "water", "solitude"]


def main():
    spec = read_json(os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagery_lexicon.json"))
    lex = {w: None for w in spec["_stop"]}
    for c in CATS:
        for w in spec[c]:
            lex[w] = c
    album = read_json(os.path.join(DATA, "soulboy_tracks.json"))
    feats = {f["trackNumber"]: f["reccobeats"] for f in read_json(os.path.join(DATA, "soulboy_features.json"))["tracks"]}
    energies = [feats[t["trackNumber"]]["energy"] for t in album["tracks"]]
    lo, hi = min(energies), max(energies)
    songs = []
    for t in album["tracks"]:
        n = t["trackNumber"]
        text = read_json(os.path.join(RAW, "lyrics", f"{n:02d}.json")).get("plainLyrics") or ""
        hits = tokenize(text, lex)
        counts = {c: sum(hits.get(c, {}).values()) for c in CATS}
        total = sum(counts.values())
        weights = {c: round(counts[c] / total, 3) if total else round(1 / 7, 3) for c in CATS}
        f = feats[n]
        songs.append({
            "album": "Soulboy", "year": 2005, "track": n, "name": t["trackName"],
            "tempo": round(f["tempo"], 2), "energy": round(f["energy"], 2), "valence": round(f["valence"], 2),
            "intensity": round((f["energy"] - lo) / (hi - lo), 3),
            "weights": weights, "sparse": total == 0, "hits": counts,
            "palette": [h for h, _ in EDITORIAL[n]["palette"]],
            "quote": EDITORIAL[n]["quote"],
            "preview_url": t["previewUrl"], "apple_url": t["trackViewUrl"], "artwork": t["artworkUrl600"],
        })
    write_json(os.path.join(DATA, "songs.json"), songs)
    for s in songs:
        print(s["track"], s["name"], s["hits"], s["sparse"])


if __name__ == "__main__":
    main()
