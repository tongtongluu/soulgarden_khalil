"""Step g: the ten studio albums on iTunes (tw storefront) with their track lists.

iTunes lists one edition per album. Where that edition looks like a reissue
(tracks dated later than the rest, bonus tracks, singles folded in) the note
says so; no standard edition with fewer tracks is listed on iTunes tw or hk.

Output: data/discography.json
"""
import os

from common import DATA, get_json, write_json

ALBUMS = [
    ("Soulboy", "Soulboy", 2005, 201549018,
     "Tracks 2, 3, 11-14 are dated 2005-11-16, the rest 2005-07-22: likely a reissue that added tracks to the July original."),
    ("This Love", "愛愛愛", 2006, 220365864,
     "Track 9 詩人的情人 is dated 2006-12-31, the rest 2006-06-09; tracks 12-13 are a cover and a remix. Likely a reissue."),
    ("Wonderland", "未來", 2007, 272875165, ""),
    ("Orange Moon", "橙月", 2008, 313404785, ""),
    ("Timeless", "可啦思刻", 2009, 537029543, "Covers album. iTunes lists 9 tracks."),
    ("15", "15", 2011, 540055014, ""),
    ("Back to Wonderland", "回到未來", 2012, 577983280, ""),
    ("Dangerous World", "危險世界", 2014, 1579903639,
     "Includes short interludes (Welcome 7s, Soundcheck 34s, Weather Report 61s, Boarding 21s) and a 17-minute closing track."),
    ("Journey to the West", "西遊記", 2016, 1587171414,
     "iTunes edition 'JTW西遊記' has 21 tracks, including a marked bonus demo (track 11) and the 2016 singles."),
    ("The Dreamer", "夢想家", 2024, 1772124855, ""),
]


def main():
    out = []
    for album, zh, year, cid, note in ALBUMS:
        _, res = get_json("https://itunes.apple.com/lookup", {"id": cid, "entity": "song", "country": "tw"})
        coll = res["results"][0]
        tracks = sorted((r for r in res["results"] if r.get("wrapperType") == "track"),
                        key=lambda r: (r.get("discNumber", 1), r["trackNumber"]))
        out.append({
            "album": album, "zh": zh, "year": year, "collectionId": cid,
            "itunesName": coll["collectionName"], "trackCount": len(tracks),
            "editionNote": note or None,
            "tracks": [{"n": r["trackNumber"], "name": r["trackName"],
                        "seconds": round(r.get("trackTimeMillis", 0) / 1000)} for r in tracks],
        })
        print(album, cid, len(tracks))
    write_json(os.path.join(DATA, "discography.json"), out)


if __name__ == "__main__":
    main()
