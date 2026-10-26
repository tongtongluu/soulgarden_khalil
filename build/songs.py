"""Step f: data/songs.json, one compact object per track for the visual.

Seven imagery weights from build/imagery_lexicon.json (normalised to sum 1),
raw counts for the 10 imagery groups from imagery.py (same as soulboy_imagery.json),
audio features from data/soulboy_features.json, palette and quote from the
hand-curated EDITORIAL table in imagery.py.
"""
import os
import re

from common import DATA, RAW, read_json, write_json
from imagery import EDITORIAL, LEXICON, STOP, tokenize

SPARSE_BELOW = 4  # fewer total hits than this: too little evidence, use equal weights
# words that match a lexicon group but are not something you can see (see stoplist.txt)
STOPLIST = [l.split("#")[0].strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stoplist.txt"), encoding="utf-8")]
STOPLIST = [w for w in STOPLIST if w and w != "fall"]
CATS = ["love", "light", "sun", "night", "nature", "water", "solitude"]


def main():
    spec = read_json(os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagery_lexicon.json"))
    lex = {w: None for w in spec["_stop"]}
    for c in CATS:
        for w in spec[c]:
            lex[w] = c
    groups = {STOP: None}
    for g, words in LEXICON.items():
        for w in words.split():
            groups[w] = g
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
        ghits = tokenize(text, groups)
        for w in STOPLIST:
            for g in ghits.values():
                g.pop(w, None)
        # "fall" is stoplisted only as a verb: keep it on lines that list the seasons
        if "time_memory" in ghits and "fall" in ghits["time_memory"]:
            seasons = sum(1 for line in text.splitlines() if re.search(r"\bfall\b", line, re.I)
                          and re.search(r"\b(winter|spring|summer)\b", line, re.I))
            ghits["time_memory"]["fall"] = seasons
        imagery = {g: sum(ghits.get(g, {}).values()) for g in LEXICON}
        love_zh = text.count("愛") + text.count("爱")
        love_en = len(re.findall(r"\blove\b", text, re.IGNORECASE))
        sparse = total < SPARSE_BELOW
        weights = {c: round(1 / 7, 3) if sparse else round(counts[c] / total, 3) for c in CATS}
        f = feats[n]
        songs.append({
            "album": "Soulboy", "year": 2005, "track": n, "name": t["trackName"],
            "tempo": round(f["tempo"], 2), "energy": round(f["energy"], 2), "valence": round(f["valence"], 2),
            "intensity": round((f["energy"] - lo) / (hi - lo), 3),
            "weights": weights, "sparse": sparse, "hits": counts, "imagery": imagery,
            "love": love_zh + love_en,  # 愛 + 爱 + English "love"
            "love_en": love_en,
            "palette": [h for h, _ in EDITORIAL[n]["palette"]],
            "quote": EDITORIAL[n]["quote"],
            "preview_url": t["previewUrl"], "apple_url": t["trackViewUrl"], "artwork": t["artworkUrl600"],
        })
    write_json(os.path.join(DATA, "songs.json"), songs)
    for s in songs:
        print(s["track"], s["name"], s["hits"], s["sparse"])


if __name__ == "__main__":
    main()
