"""Step b: fetch lyrics per track from LRCLIB, matched by duration.

Output: raw/lyrics/<NN>.json (never published)
"""
import os

from common import DATA, RAW, get_json, read_json, write_json

API = "https://lrclib.net/api/search"
ARTISTS = ["方大同", "Khalil Fong"]
TOLERANCE_S = 3.0

# Traditional -> simplified, only for characters in this album's titles.
T2S = str.maketrans("風麼說們總結趕場著來認識", "风么说们总结赶场着来认识")


def title_variants(name):
    out = [name]
    s = name.translate(T2S)
    if s != name:
        out.append(s)
    return out


def candidates(track):
    seen = {}
    queries = []
    for title in title_variants(track["trackName"]):
        for artist in ARTISTS:
            queries.append({"artist_name": artist, "track_name": title})
        queries.append({"q": f"{title} 方大同"})
    for q in queries:
        status, res = get_json(API, q)
        if status != 200 or not isinstance(res, list):
            continue
        for r in res:
            seen.setdefault(r["id"], (r, q))
    return list(seen.values())


def score(track, rec):
    target = track["trackTimeMillis"] / 1000
    dur = rec.get("duration") or 0
    diff = abs(dur - target)
    artist = (rec.get("artistName") or "")
    artist_ok = "方大同" in artist or "khalil" in artist.lower()
    names = [n.lower() for n in title_variants(track["trackName"])]
    title_ok = (rec.get("trackName") or "").strip().lower() in names
    has_text = bool(rec.get("plainLyrics") or rec.get("syncedLyrics"))
    return diff, artist_ok, title_ok, has_text


def main():
    album = read_json(os.path.join(DATA, "soulboy_tracks.json"))
    for t in album["tracks"]:
        cands = candidates(t)
        best = None
        for rec, q in cands:
            diff, artist_ok, title_ok, has_text = score(t, rec)
            if not (artist_ok and title_ok and diff <= TOLERANCE_S):
                continue
            key = (not has_text, not rec.get("syncedLyrics"), diff)
            if best is None or key < best[0]:
                best = (key, rec, q, diff)
        path = os.path.join(RAW, "lyrics", f"{t['trackNumber']:02d}.json")
        if best is None:
            out = {"trackNumber": t["trackNumber"], "trackName": t["trackName"], "matched": False,
                   "candidatesSeen": len(cands)}
            print(f"{t['trackNumber']:2d} {t['trackName']}: no match ({len(cands)} candidates)")
        else:
            _, rec, q, diff = best
            instrumental = bool(rec.get("instrumental"))
            confidence = "high" if diff <= 1.0 else "medium"
            out = {
                "trackNumber": t["trackNumber"],
                "trackName": t["trackName"],
                "matched": True,
                "lrclibId": rec["id"],
                "lrclibTrackName": rec.get("trackName"),
                "lrclibArtistName": rec.get("artistName"),
                "lrclibAlbumName": rec.get("albumName"),
                "lrclibDuration": rec.get("duration"),
                "durationDiffSeconds": round(diff, 2),
                "confidence": confidence,
                "instrumental": instrumental,
                "query": q,
                "plainLyrics": rec.get("plainLyrics"),
                "syncedLyrics": rec.get("syncedLyrics"),
            }
            print(f"{t['trackNumber']:2d} {t['trackName']}: id={rec['id']} diff={diff:.1f}s "
                  f"{confidence} plain={bool(rec.get('plainLyrics'))} synced={bool(rec.get('syncedLyrics'))}"
                  f"{' instrumental' if instrumental else ''}")
        write_json(path, out)


if __name__ == "__main__":
    main()
