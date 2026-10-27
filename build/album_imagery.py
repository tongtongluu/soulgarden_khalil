"""Imagery, love and line counts for one album's lyrics (raw/<slug>/lyrics), in the page's CAT_IDS order.

Usage: python3 album_imagery.py <slug> [--lines]
Output: data/<slug>_imagery.json; with --lines, also prints every lyric line with its hits (for reading, never saved)

Matching: the 10-group LEXICON from imagery.py, longest term first. Words in stoplist.txt and the idioms below
are consumed before anything shorter can match inside them and are never counted. jieba is not installed here,
so this is longest-match plus an idiom stoplist rather than real word segmentation.
"""
import json
import os
import re
import sys

from common import DATA, RAW, write_json
from imagery import LEXICON, STOP, tokenize

# the page's group order (CAT_IDS in index.html); terms are written as word:index:count
CAT_IDS = ["body_gesture", "time_memory", "people_relationships", "city_street", "cosmos",
           "sky_weather", "nature_plants", "light_fire", "night_moon", "water"]
# idioms and compounds in which a single imagery character is not an image (from the Soulboy lexicon notes)
IDIOMS = "大家 成家 國家 耐心 傷人心 翻臉 從頭 拿手 眨眼 過眼雲煙 風光 日日夜夜 心裡話 路過 滿臉春風".split()
# simplified -> traditional, only for characters in the lexicon, stoplist and idioms; applied only to lyrics
# that are written in simplified characters
S2T = str.maketrans(
    "风云泪头脸双灯笼烛点树乌龟闷电报纸闻话机场时间岁记历从旧远爱妈众听类阳试脉镜闪烟过里满国伤当几岁见后这么们说会还来对开进让长发样",
    "風雲淚頭臉雙燈籠燭點樹烏龜悶電報紙聞話機場時間歲記歷從舊遠愛媽眾聽類陽試脈鏡閃煙過裡滿國傷當幾歲見後這麼們說會還來對開進讓長發樣")
SIMPLIFIED_ONLY = set("爱么说们这时间个来过还会见后风云发听让长对开进头里样")
TRAD_ONLY = set("愛麼說們這時間個來過還會見後風雲發聽讓長對開進頭裡樣")


def stoplist():
    words = [l.split("#")[0].strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stoplist.txt"), encoding="utf-8")]
    return [w for w in words if w and w != "fall"]


def lexicon():
    lex = {STOP: None}
    for g, words in LEXICON.items():
        for w in words.split():
            lex[w] = g
    for w in stoplist() + IDIOMS:
        lex[w] = None          # consumed, never counted
    return lex


def hits_in(line, lex):
    hits = tokenize(line, lex)
    out = []
    for g, ws in hits.items():
        for w, c in ws.items():
            # "fall" counts only as the season, on a line that lists the seasons
            if w == "fall" and not re.search(r"\b(winter|spring|summer)\b", line, re.I):
                continue
            out.append((line.lower().find(w.lower()), w, g, c))
    return sorted(out)


def main():
    slug, show = sys.argv[1], "--lines" in sys.argv
    lex = lexicon()
    tracks = json.load(open(os.path.join(DATA, f"{slug}_tracks.json"), encoding="utf-8"))["tracks"]
    out = []
    for t in tracks:
        n = t["trackNumber"]
        ly = json.load(open(os.path.join(RAW, slug, "lyrics", f"{n:02d}.json"), encoding="utf-8"))
        text = (ly.get("plainLyrics") or "") if ly.get("matched") else ""
        simplified = sum(ch in SIMPLIFIED_ONLY for ch in text) > sum(ch in TRAD_ONLY for ch in text)
        match_text = text.translate(S2T) if simplified else text
        counts = {g: 0 for g in CAT_IDS}
        terms = {}
        if show:
            print(f"===== {n} {t['trackName']}" + (" (simplified, converted for matching)" if simplified else ""))
        stanzas = re.split(r"\n\s*\n", match_text.strip()) if match_text.strip() else []
        for si, st in enumerate(stanzas, 1):
            lines = st.split("\n")
            if show:
                print(f"-- S{si} ({len(lines)})")
            for li, line in enumerate(lines, 1):
                h = hits_in(line, lex)
                for _, w, g, c in h:
                    counts[g] += c
                    terms[(w, g)] = terms.get((w, g), 0) + c
                if show:
                    print(f"  {li:2d} {line}   ->", " ".join(f"{w}[{g}]x{c}" if c > 1 else f"{w}[{g}]" for _, w, g, c in h))
        love = text.count("愛") + text.count("爱") + len(re.findall(r"\blove\b", text, re.I))
        out.append({
            "track": n, "name": t["trackName"], "has_lyrics": bool(text.strip()), "simplified_source": simplified,
            "line_count": sum(1 for l in text.splitlines() if l.strip()),
            "imagery": counts,
            "terms": [f"{w}:{CAT_IDS.index(g)}:{c}" for (w, g), c in sorted(terms.items(), key=lambda kv: (-kv[1], kv[0][0]))],
            "love": love,
        })
    write_json(os.path.join(DATA, f"{slug}_imagery.json"), {
        "method": "Longest-match over the 10-group lexicon, with stoplist.txt and an idiom stoplist consumed first (no jieba). Simplified lyrics are converted to traditional for matching only.",
        "cat_ids": CAT_IDS, "tracks": out})
    if not show:
        for x in out:
            print(x["track"], x["name"], x["line_count"], x["love"], sum(x["imagery"].values()), x["terms"][:6])


if __name__ == "__main__":
    main()
