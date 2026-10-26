"""Step a: find the 2005 Soulboy studio album on iTunes and save its track list.

Output: data/soulboy_tracks.json
"""
import os
import sys

from common import DATA, get_json, write_json

COUNTRIES = ["tw", "hk", "cn", "us"]


def find_album(country):
    _, res = get_json("https://itunes.apple.com/search", {
        "term": "khalil fong soulboy", "entity": "album", "country": country, "limit": 50})
    albums = (res or {}).get("results", [])
    # Original studio album: titled exactly Soulboy, released 2005, by Khalil Fong.
    hits = [a for a in albums
            if a.get("collectionName", "").strip().lower() == "soulboy"
            and a.get("releaseDate", "").startswith("2005")]
    return hits, albums


def main():
    for country in COUNTRIES:
        hits, albums = find_album(country)
        print(f"[{country}] {len(albums)} albums, {len(hits)} candidate(s)")
        for a in albums:
            print("   ", a.get("collectionId"), a.get("collectionName"), a.get("releaseDate"), a.get("trackCount"))
        if hits:
            album = hits[0]
            break
    else:
        sys.exit("No 2005 Soulboy album found in any storefront")

    cid = album["collectionId"]
    _, res = get_json("https://itunes.apple.com/lookup", {"id": cid, "entity": "song", "country": country})
    songs = [r for r in res["results"] if r.get("wrapperType") == "track"]
    songs.sort(key=lambda s: (s.get("discNumber", 1), s["trackNumber"]))
    tracks = []
    for s in songs:
        art = s.get("artworkUrl100", "")
        tracks.append({
            "trackNumber": s["trackNumber"],
            "trackName": s["trackName"],
            "trackId": s["trackId"],
            "trackTimeMillis": s.get("trackTimeMillis"),
            "previewUrl": s.get("previewUrl"),
            "trackViewUrl": s.get("trackViewUrl"),
            "artworkUrl600": art.replace("100x100bb", "600x600bb") if art else None,
            "releaseDate": s.get("releaseDate"),
            "collectionId": s["collectionId"],
            "collectionViewUrl": s.get("collectionViewUrl"),
        })
    out = {
        "source": f"iTunes Search/Lookup API, country={country}",
        "collectionId": cid,
        "collectionName": album["collectionName"],
        "artistName": album.get("artistName"),
        "albumReleaseDate": album.get("releaseDate"),
        "trackCount": album.get("trackCount"),
        "collectionViewUrl": album.get("collectionViewUrl"),
        "artworkUrl600": album.get("artworkUrl100", "").replace("100x100bb", "600x600bb"),
        "tracks": tracks,
    }
    write_json(os.path.join(DATA, "soulboy_tracks.json"), out)
    print(f"Saved {len(tracks)} tracks from collection {cid} ({country})")


if __name__ == "__main__":
    main()
