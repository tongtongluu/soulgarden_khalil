"""Tempo candidates from onset autocorrelation, then meter and feel measured at the top two candidates.

Usage: python3 rhythm_candidates.py <audio> <given_tempo> [...]   (the rhythm JSON is chosen by reading these numbers)
"""
import sys, json, numpy as np
from rhythm_core import load, envelopes, beat_track, meter_scores, SR, H
fps = SR / H
def acf_of(env):
    e = env - env.mean(); a = np.correlate(e, e, "full")[len(e) - 1:]; return a / a[0]
def at(acf, p): p = int(round(p)); return float(acf[max(1, p - 1):p + 2].max()) if p + 2 < len(acf) else 0.0
def candidates(env):
    acf = acf_of(env); out = []
    for bpm in np.arange(55, 200, 0.5):
        p = 60 / bpm * fps
        s = sum(at(acf, p * m) / m ** 0.5 for m in (1, 2, 4))
        out.append((s, float(bpm)))
    out.sort(reverse=True); top = []
    for s, b in out:
        if all(abs(b - t[1]) > 4 for t in top): top.append((round(s, 2), b))
        if len(top) == 3: break
    return top, acf
res = []
for path, given in zip(sys.argv[1::2], sys.argv[2::2]):
    y = load(path); allf, lof, hif = envelopes(y)
    top, acf = candidates(allf)
    rows = []
    for s, T in top[:2]:
        P = 60 / T * fps
        beats, _ = beat_track(allf + lof, T)
        m = meter_scores(lof, allf, beats)
        env = hif + 0.5 * allf; bins = np.zeros(24)
        for a, b in zip(beats[:-1], beats[1:]):
            L = b - a
            if L < 12: continue
            for k in range(L): bins[int(k / L * 24)] += env[a + k]
        bins /= bins.max()
        rows.append({"T": T, "score": s, "acf": {"T": round(at(acf, P), 2), "2T": round(at(acf, 2 * P), 2), "4T": round(at(acf, 4 * P), 2), "T/2": round(at(acf, P / 2), 2), "T/3": round(at(acf, P / 3), 2)},
                     "ac3": round(m["ac3"], 2), "ac4": round(m["ac4"], 2), "c3": round(m["c3"], 2), "c4": round(m["c4"], 2),
                     "half": round(float(bins[11:13].mean()), 2), "thirds": round(float((bins[7:9].mean() + bins[15:17].mean()) / 2), 2),
                     "offbeat": round(float((np.argmax(bins[9:19]) + 9 + 0.5) / 24), 3)})
    res.append({"path": path[-6:-4], "given": float(given), "top": top, "rows": rows})
for r in res: print(json.dumps(r, ensure_ascii=False))
