"""Step c: audio features per track.

Downloads each iTunes 30s preview to raw/audio/<NN>.m4a (never published), then
uploads it to ReccoBeats' audio-feature analysis endpoint. Spotify IDs are not
available without Spotify API credentials, so the /v1/track?ids= route is not used.
If librosa is importable, also computes tempo, mean RMS, spectral centroid and key.

Output: data/soulboy_features.json
"""
import json
import os
import time
import urllib.request
import uuid

from common import DATA, RAW, UA, get, read_json, write_json

RECCO = "https://api.reccobeats.com/v1/analysis/audio-features"
FIELDS = ["tempo", "energy", "valence", "danceability", "acousticness", "instrumentalness",
          "speechiness", "liveness", "loudness", "key", "mode"]

try:
    import librosa  # noqa: F401
    import numpy as np
    HAVE_LIBROSA = True
except ImportError:
    HAVE_LIBROSA = False


def download(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return True
    status, body = get(url, accept="*/*")
    if status != 200:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(body)
    return True


def recco_upload(path):
    boundary = uuid.uuid4().hex
    with open(path, "rb") as f:
        data = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"audioFile\"; "
            f"filename=\"{os.path.basename(path)}\"\r\nContent-Type: audio/mp4\r\n\r\n").encode() \
        + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(RECCO, data=body, method="POST", headers={
        "User-Agent": UA, "Accept": "application/json",
        "Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]


KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]


def librosa_features(path):
    y, sr = librosa.load(path, sr=22050, mono=True)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    best = max(((np.corrcoef(chroma, np.roll(prof, k))[0, 1], k, m)
                for m, prof in (("major", MAJOR), ("minor", MINOR)) for k in range(12)))
    return {
        "tempo": round(float(np.atleast_1d(tempo)[0]), 1),
        "rmsMean": round(float(librosa.feature.rms(y=y).mean()), 5),
        "spectralCentroidMean": round(float(librosa.feature.spectral_centroid(y=y, sr=sr).mean()), 1),
        "estimatedKey": f"{KEYS[best[1]]} {best[2]}",
    }


def main():
    album = read_json(os.path.join(DATA, "soulboy_tracks.json"))
    out_tracks = []
    for t in album["tracks"]:
        n = t["trackNumber"]
        rec = {"trackNumber": n, "trackName": t["trackName"], "trackId": t["trackId"],
               "featureSource": None, "reccobeats": None, "librosa": None, "errors": []}
        audio = os.path.join(RAW, "audio", f"{n:02d}.m4a")
        if not t.get("previewUrl") or not download(t["previewUrl"], audio):
            rec["errors"].append("preview download failed")
            out_tracks.append(rec)
            continue
        status, res = recco_upload(audio)
        if status == 200 and isinstance(res, dict):
            rec["reccobeats"] = {k: res.get(k) for k in FIELDS if k in res}
            rec["featureSource"] = "reccobeats analysis of 30s iTunes preview"
        else:
            rec["errors"].append(f"reccobeats HTTP {status}: {res}")
        if HAVE_LIBROSA:
            try:
                rec["librosa"] = librosa_features(audio)
            except Exception as e:
                rec["errors"].append(f"librosa: {e}")
        print(n, t["trackName"], rec["reccobeats"] or rec["errors"])
        out_tracks.append(rec)
        time.sleep(1)
    write_json(os.path.join(DATA, "soulboy_features.json"), {
        "collectionId": album["collectionId"],
        "note": "Features describe the 30-second iTunes preview, not the full track.",
        "librosaAvailable": HAVE_LIBROSA,
        "tracks": out_tracks,
    })


if __name__ == "__main__":
    main()
