"""Fetch any studio album the same way as Soulboy: iTunes tracks and previews, LRCLIB lyrics, ReccoBeats features.

Usage: python3 fetch_album.py <slug> <collectionId>   e.g.  python3 fetch_album.py thislove 220365864

Output: data/<slug>_tracks.json, data/<slug>_features.json,
        raw/<slug>/lyrics/NN.json and raw/<slug>/audio/NN.m4a (private, git-ignored)
"""
import os
import sys
import time

from common import DATA, RAW, get_json, write_json
from fetch_features import FIELDS, download, recco_upload

LRCLIB = "https://lrclib.net/api/search"
ARTISTS = ["方大同", "Khalil Fong"]
TOLERANCE_S = 3.0
# traditional -> simplified for characters that occur in his song titles
T2S = str.maketrans("風麼說們總結趕場著來認識愛蘇麗與兒遊帶詩後見歲會這過",
                    "风么说们总结赶场着来认识爱苏丽与儿游带诗后见岁会这过")


def tracks_for(cid):
    _, res = get_json("https://itunes.apple.com/lookup", {"id": cid, "entity": "song", "country": "tw"})
    album = res["results"][0]
    songs = sorted((r for r in res["results"] if r.get("wrapperType") == "track"),
                   key=lambda s: (s.get("discNumber", 1), s["trackNumber"]))
    return album, [{
        "trackNumber": s["trackNumber"], "trackName": s["trackName"].strip(), "trackId": s["trackId"],
        "trackTimeMillis": s.get("trackTimeMillis"), "previewUrl": s.get("previewUrl"),
        "trackViewUrl": s.get("trackViewUrl"), "releaseDate": s.get("releaseDate"),
        "collectionId": s["collectionId"], "collectionViewUrl": s.get("collectionViewUrl"),
        "artworkUrl600": (s.get("artworkUrl100") or "").replace("100x100bb", "600x600bb") or None,
    } for s in songs]


def lyrics_for(t):
    names = [t["trackName"]]
    if t["trackName"].translate(T2S) != t["trackName"]:
        names.append(t["trackName"].translate(T2S))
    seen = {}
    for name in names:
        for q in [{"artist_name": a, "track_name": name} for a in ARTISTS] + [{"q": f"{name} 方大同"}]:
            status, res = get_json(LRCLIB, q)
            if status == 200 and isinstance(res, list):
                for r in res:
                    seen.setdefault(r["id"], (r, q))
    target = (t["trackTimeMillis"] or 0) / 1000
    best = None
    for r, q in seen.values():
        artist = r.get("artistName") or ""
        if "方大同" not in artist and "khalil" not in artist.lower():
            continue
        title = (r.get("trackName") or "").strip().lower()
        if title not in [n.lower() for n in names]:
            continue
        diff = abs((r.get("duration") or 0) - target)
        if diff > TOLERANCE_S:
            continue
        key = (not (r.get("plainLyrics") or r.get("syncedLyrics")), not r.get("syncedLyrics"), diff)
        if best is None or key < best[0]:
            best = (key, r, q, diff)
    if not best:
        return {"trackNumber": t["trackNumber"], "trackName": t["trackName"], "matched": False, "candidatesSeen": len(seen)}
    _, r, q, diff = best
    return {"trackNumber": t["trackNumber"], "trackName": t["trackName"], "matched": True, "lrclibId": r["id"],
            "lrclibTrackName": r.get("trackName"), "lrclibArtistName": r.get("artistName"), "lrclibAlbumName": r.get("albumName"),
            "lrclibDuration": r.get("duration"), "durationDiffSeconds": round(diff, 2),
            "confidence": "high" if diff <= 1.0 else "medium", "instrumental": bool(r.get("instrumental")),
            "query": q, "plainLyrics": r.get("plainLyrics"), "syncedLyrics": r.get("syncedLyrics")}


def main():
    slug, cid = sys.argv[1], int(sys.argv[2])
    album, tracks = tracks_for(cid)
    write_json(os.path.join(DATA, f"{slug}_tracks.json"), {
        "source": "iTunes Search/Lookup API, country=tw", "collectionId": cid, "collectionName": album["collectionName"],
        "artistName": album.get("artistName"), "albumReleaseDate": album.get("releaseDate"), "trackCount": len(tracks),
        "collectionViewUrl": album.get("collectionViewUrl"),
        "artworkUrl600": (album.get("artworkUrl100") or "").replace("100x100bb", "600x600bb"), "tracks": tracks})
    feats = []
    for t in tracks:
        n = t["trackNumber"]
        ly = lyrics_for(t)
        write_json(os.path.join(RAW, slug, "lyrics", f"{n:02d}.json"), ly)
        rec = {"trackNumber": n, "trackName": t["trackName"], "trackId": t["trackId"], "featureSource": None, "reccobeats": None, "errors": []}
        audio = os.path.join(RAW, slug, "audio", f"{n:02d}.m4a")
        if not t["previewUrl"] or not download(t["previewUrl"], audio):
            rec["errors"].append("preview download failed")
        else:
            status, res = recco_upload(audio)
            if status == 200 and isinstance(res, dict):
                rec["reccobeats"] = {k: res.get(k) for k in FIELDS if k in res}
                rec["featureSource"] = "reccobeats analysis of 30s iTunes preview"
            else:
                rec["errors"].append(f"reccobeats HTTP {status}: {res}")
            time.sleep(1)
        feats.append(rec)
        print(n, t["trackName"], "lyrics:" + ("yes" if ly["matched"] else "NO"),
              ("instrumental" if ly.get("instrumental") else ""), "preview:" + ("yes" if t["previewUrl"] else "NO"),
              "features:" + ("yes" if rec["reccobeats"] else "NO " + "; ".join(rec["errors"])))
    write_json(os.path.join(DATA, f"{slug}_features.json"), {
        "collectionId": cid, "note": "Features describe the 30-second iTunes preview, not the full track.", "tracks": feats})


if __name__ == "__main__":
    main()
