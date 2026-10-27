"""Numpy rhythm analysis used for rhythm.json (no librosa): spectral-flux onset envelopes, a DP beat tracker,
accent periodicity at 3 vs 4 beats, and the position of the off-beat. Needs numpy and ffmpeg.

Usage: python3 rhythm_core.py <audio> <tempo> [<audio> <tempo> ...]   prints raw measurements as JSON
"""
import sys, json, subprocess, numpy as np
SR, N, H = 22050, 2048, 256

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

def envelopes(y):
    win = np.hanning(N)
    frames = np.lib.stride_tricks.sliding_window_view(np.pad(y, N // 2), N)[::H] * win
    S = np.abs(np.fft.rfft(frames, axis=1))
    logS = np.log1p(100 * S)
    flux = np.maximum(0, np.diff(logS, axis=0)).sum(1)
    freqs = np.fft.rfftfreq(N, 1 / SR)
    lo = S[:, (freqs > 30) & (freqs < 150)].sum(1)
    lo_flux = np.maximum(0, np.diff(np.log1p(lo)))
    hi = S[:, (freqs > 2000) & (freqs < 8000)]
    hi_flux = np.maximum(0, np.diff(np.log1p(hi), axis=0)).sum(1)
    def norm(x): x = x - np.convolve(x, np.ones(16) / 16, "same"); x = np.maximum(x, 0); return x / (x.std() + 1e-9)
    return norm(flux), norm(lo_flux), norm(hi_flux)

def beat_track(env, bpm):
    fps = SR / H; period = 60 / bpm * fps
    # dynamic-programming beat tracker (Ellis 2007) with a fixed period
    n = len(env); score = env.copy(); back = -np.ones(n, int)
    for t in range(n):
        lo, hi = int(t - 2 * period), int(t - period / 2)
        if hi <= 0: continue
        lo = max(lo, 0); prev = np.arange(lo, hi)
        pen = -100 * (np.log((t - prev) / period)) ** 2
        k = np.argmax(score[prev] + pen); score[t] = env[t] + score[prev][k] + pen[k]; back[t] = prev[k]
    t = int(np.argmax(score[-int(period):]) + n - int(period)); beats = []
    while t >= 0: beats.append(t); t = back[t]
    return np.array(beats[::-1]), period

def meter_scores(env_lo, env_all, beats):
    # beat-synchronous accent: low-band (kick) plus overall onset, max within ±2 frames of each beat
    acc = np.array([env_lo[max(0, b - 2):b + 3].max() * 0.6 + env_all[max(0, b - 2):b + 3].max() * 0.4 for b in beats])
    acc = (acc - acc.mean()) / (acc.std() + 1e-9)
    def ac(l): return float(np.mean(acc[:-l] * acc[l:])) if len(acc) > l + 4 else 0.0
    def contrast(g):
        best = 0
        for ph in range(g):
            on = acc[ph::g]; off = np.delete(acc, np.arange(ph, len(acc), g))
            best = max(best, on.mean() - off.mean())
        return float(best)
    return {"ac2": ac(2), "ac3": ac(3), "ac4": ac(4), "ac6": ac(6), "c3": contrast(3), "c4": contrast(4), "nbeats": len(beats)}

def swing(env, beats):
    pos, w = [], []
    for a, b in zip(beats[:-1], beats[1:]):
        seg = env[a:b]; L = b - a
        if L < 8: continue
        lo, hi = int(L * 0.3), int(L * 0.8)
        k = lo + int(np.argmax(seg[lo:hi])); pos.append(k / L); w.append(seg[k])
    pos, w = np.array(pos), np.array(w)
    if not len(pos): return None, 0, {}
    strong = w > np.percentile(w, 40)
    hist, edges = np.histogram(pos[strong], bins=10, range=(0.3, 0.8))
    # triplet energy: onsets near 1/3 and 2/3 vs near 1/2
    def near(c, d=0.05): return float(np.mean(np.abs(pos[strong] - c) < d))
    return float(np.median(pos[strong])), float(strong.sum()), {"near_half": near(0.5), "near_two_thirds": near(0.667), "near_third": near(0.333), "hist": hist.tolist()}

if __name__ == "__main__":
    out = []
    for path, tempo in zip(sys.argv[1::2], sys.argv[2::2]):
        y = load(path); allf, lof, hif = envelopes(y)
        beats, period = beat_track(allf + lof, float(tempo))
        m = meter_scores(lof, allf, beats)
        ratio, nstrong, sw = swing(hif + 0.5 * allf, beats)
        # local tempo check: autocorrelation of the onset envelope around the given period and its double/half
        fps = SR / H; e = allf - allf.mean(); acf = np.correlate(e, e, "full")[len(e) - 1:]; acf /= acf[0]
        def acf_at(p): p = int(round(p)); return float(acf[p - 2:p + 3].max()) if p + 3 < len(acf) else 0
        out.append({"path": path, "tempo": float(tempo), "dur": round(len(y) / SR, 1), **{k: round(v, 3) if isinstance(v, float) else v for k, v in m.items()},
                    "swing_median": round(ratio, 3) if ratio else None, **{k: (round(v, 3) if isinstance(v, float) else v) for k, v in sw.items()},
                    "acf_T": round(acf_at(period), 3), "acf_2T": round(acf_at(2 * period), 3), "acf_T/2": round(acf_at(period / 2), 3), "acf_2T/3": round(acf_at(period * 2 / 3), 3), "acf_T/3": round(acf_at(period / 3), 3)})
    print(json.dumps(out, ensure_ascii=False, indent=1))
    