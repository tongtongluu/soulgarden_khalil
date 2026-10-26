"""Step d: write data/coverage.md (preview / lyrics / features per track)."""
import os

from common import DATA, RAW, read_json


def main():
    album = read_json(os.path.join(DATA, "soulboy_tracks.json"))
    feats = {t["trackNumber"]: t for t in read_json(os.path.join(DATA, "soulboy_features.json"))["tracks"]}
    rows = ["| # | Track | Preview | Lyrics (LRCLIB) | Features |", "|---|---|---|---|---|"]
    for t in album["tracks"]:
        n = t["trackNumber"]
        lp = os.path.join(RAW, "lyrics", f"{n:02d}.json")
        ly = read_json(lp) if os.path.exists(lp) else {}
        if ly.get("matched"):
            kinds = "+".join(k for k, f in (("plain", "plainLyrics"), ("synced", "syncedLyrics")) if ly.get(f))
            lyr = f"{kinds}, id {ly['lrclibId']}, {ly['confidence']}"
        else:
            lyr = "none"
        f = feats.get(n, {})
        fe = "ReccoBeats" if f.get("reccobeats") else "none"
        if f.get("librosa"):
            fe += " + librosa"
        rows.append(f"| {n} | {t['trackName']} | {'yes' if t.get('previewUrl') else 'no'} | {lyr} | {fe} |")
    with open(os.path.join(DATA, "coverage.md"), "w", encoding="utf-8") as fh:
        fh.write("# Soulboy coverage\n\n" + "\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
