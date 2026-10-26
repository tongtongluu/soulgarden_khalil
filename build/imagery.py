"""Step e: imagery and colour analysis of the full lyrics in raw/lyrics.

Counts come from a hand-built lexicon, matched greedily longest-term-first so
that e.g. 桃花 is not also counted as 花. Palettes, moods and hover quotes are
hand-curated (EDITORIAL below). Only derived data is written; no lyric passages.

Output: data/soulboy_imagery.json
"""
import os

from common import DATA, RAW, read_json, write_json

LEXICON = {
    "nature_plants": "桃花 柳樹 玫瑰 原上草 草 花 春花 蝴蝶 燕子 青蛙 蛇 烏龜 原野 樹",
    "sky_weather": "春風 北風 風 雲堆 雲煙 多雲天 雲 暴雨天 雨 晴天 悶雷 雷 閃電 電 天空 春光",
    "water": "河水 河 二泉 泉 地中海 海 水",
    "light_fire": "燭光 燈籠 點亮 彩虹 光 rays blazin",
    "night_moon": "月 漆黑 夜夜 晚上 夜 失了幾次眠 睡眠 睡",
    "city_street": "街頭 街上 街 路旁 路上 路 城裡 城 小巷 酒家 新聞 報紙 cappuccino 咖啡 電影 搞笑片 手機 電話 上班 下班 科場 試場 早場 尾場",
    "body_gesture": "雙目 雙眼 眼睛 眼神 眼淚 熱淚 流淚 淚 眼 臉孔 臉 頭 手 心 笑 吻 脈 跳 舞 眨 墨鏡",
    "time_memory": "小時候 歷史 從前 往事 記得 想起 當年 每天 今天 明天 星期 永遠 時間 舊 年 歲 夏天 冬日 三月 winter spring summer fall",
    "people_relationships": "表妹 妹妹 媽媽 老爸 老婆 女人 朋友 friend 祖先 人類 聽眾 小姐 叔叔 情男情女 homies 家",
    "cosmos": "宇宙 地球 太陽 sun 世界 world 神",
}
# Terms consumed first and counted nowhere: they contain a lexicon character
# but are not imagery (光榮 = glory).
STOP = "光榮"

COLOURS = {"紅": "red", "綠": "green", "藍": "blue", "黑": "black", "白": "white",
           "金": "gold", "彩虹": "rainbow"}
COLOUR_STOP = "青蛙 晴 明白 坦白 紅與不紅"  # not colours: 青蛙 (frog), 明白/坦白 (understand/frank), 紅與不紅 (famous or not)


def tokenize(text, lexicon):
    """Greedy longest-first scan. lexicon: {term: category or None}."""
    terms = sorted(lexicon, key=len, reverse=True)
    low = text.lower()
    hits = {}
    i = 0
    while i < len(low):
        for t in terms:
            if low.startswith(t.lower(), i):
                cat = lexicon[t]
                if cat:
                    hits.setdefault(cat, {}).setdefault(t, 0)
                    hits[cat][t] += 1
                i += len(t)
                break
        else:
            i += 1
    return hits


EDITORIAL = {
    1: {"mood": ["reflective", "grateful"], "quote": "life and love",
        "palette": [["#F2E6D0", "warm cream: a spoken, welcoming opener"],
                    ["#D9A441", "amber: soul and R&B warmth"],
                    ["#5B3A29", "deep brown: vinyl-era soul roots"]]},
    2: {"mood": ["tender", "nostalgic", "protective"], "quote": "好像變了晴天",
        "palette": [["#7A8691", "storm grey: the cloudy and rainstorm days"],
                    ["#8EC5E8", "clear sky blue: she turns them sunny"],
                    ["#F6D365", "sunlight yellow: childhood laughter"],
                    ["#F4B6C2", "soft pink: affection for a little sister"]]},
    3: {"mood": ["wistful", "restless", "pastoral"], "quote": "春風一吹想起誰",
        "palette": [["#F4A6A0", "peach blossom: the wind blows the peach trees red"],
                    ["#8DB86B", "willow green: the wind blows the willows green"],
                    ["#C0392B", "rose red: roses brought up from underground"],
                    ["#EEF1F4", "cloud white: scattered cloud banks"],
                    ["#6F9FAF", "river teal: wrinkled river water"]]},
    4: {"mood": ["comfortable", "longing", "devoted"], "quote": "約好去看地中海 的藍",
        "palette": [["#1F6FB2", "Mediterranean blue: the one colour named"],
                    ["#9A9A9A", "pavement grey: the busy, dull roadside"],
                    ["#E8D9C0", "warm beige: easy everyday companionship"]]},
    5: {"mood": ["admonishing", "tender"], "quote": "你要對你的女人好",
        "palette": [["#E7A1B0", "Venus rose: the 'world of Venus'"],
                    ["#B49A7A", "faded sepia: the one old photograph left"],
                    ["#7D4E57", "muted plum: quarrels and regret"]]},
    6: {"mood": ["smitten", "shy", "earnest"], "quote": "我想在街上遇到你",
        "palette": [["#F7C6C7", "blush: a single smile is enough"],
                    ["#C2A27C", "old-film sepia: romance from old movies"],
                    ["#6E7F91", "street blue-grey: hoping to meet on the street"]]},
    7: {"mood": ["nervous", "restrained", "flustered"], "quote": "眼睛在說話",
        "palette": [["#4B3B6B", "dim violet: a slow dance floor"],
                    ["#E0B84C", "glint gold: blinking, talking eyes"],
                    ["#C94C4C", "pulse red: a racing heart a doctor should check"]]},
    8: {"mood": ["dignified", "melancholic", "hopeful"], "quote": "為人們奏出彩虹",
        "palette": [["#14141A", "night black: blindness, dark north wind, round sunglasses"],
                    ["#9E1B1B", "blood red: erhu strings that cut the fingers"],
                    ["#E8A23B", "candle gold: candlelight and lanterns lit along the way"],
                    ["#C9CED6", "moon silver: the moon over the spring"],
                    ["#7B6FD0", "rainbow violet: the rainbow he plays for people"]]},
    9: {"mood": ["pleading", "idealistic", "communal"], "quote": "很大的宇宙的小地球上",
        "palette": [["#0B1D3A", "space navy: a huge universe"],
                    ["#2E6DA4", "earth blue: the small planet"],
                    ["#F5C242", "sun yellow: everyone under one sun"],
                    ["#A9745A", "warm brown: every skin colour"]]},
    10: {"mood": ["urgent", "defiant", "celebratory"], "quote": "我們要彩虹世界",
         "palette": [["#BDBAB2", "newsprint grey: chaos in the papers"],
                     ["#F26B1D", "blazing orange: rays of the sun, keep it blazing"],
                     ["#7B4FD8", "rainbow violet: a rainbow world"],
                     ["#2FB673", "rainbow green: unity and movement"]]},
    11: {"mood": ["contemplative", "regretful", "philosophical"], "quote": "天飛過幾多蝴蝶",
         "palette": [["#A47C48", "ochre: ancestors tying knots in string"],
                     ["#DDE7F5", "lightning white-blue: flashes of lightning"],
                     ["#F0C75E", "butterfly yellow: butterflies over the sky"],
                     ["#6F8F5A", "wilderness green: open plains"],
                     ["#8C8C94", "smoke grey: everything passes like smoke and cloud"]]},
    12: {"mood": ["hurried", "nostalgic", "wry"], "quote": "趕來趕去趕什麼",
         "palette": [["#707780", "rush-hour grey: hurrying between shifts and exams"],
                     ["#7FA36B", "riverbank green: look at the scenery on both banks"],
                     ["#E3B778", "warm lamp: reunions always postponed"]]},
    13: {"mood": ["yearning", "patient", "bittersweet"], "quote": "庭前春花為你開",
         "palette": [["#F3B5C4", "blossom pink: spring flowers in the courtyard"],
                     ["#23304A", "swallow ink: swallows back under the beam"],
                     ["#9CCB7A", "spring green: spring light that won't return"],
                     ["#9DB8D9", "tear blue: cheeks full of hot tears"]]},
    14: {"mood": ["playful", "flirtatious", "casual"], "quote": "因為我只想認識你",
         "palette": [["#E8D6BF", "cappuccino foam: the café order"],
                     ["#6F4E37", "coffee brown: a café table"],
                     ["#F1C27D", "warm café light: an easy first conversation"]]},
}


def main():
    lex = {STOP: None}
    for cat, words in LEXICON.items():
        for w in words.split():
            lex[w] = cat
    col_lex = {w: None for w in COLOUR_STOP.split()}
    col_lex.update({w: c for w, c in COLOURS.items()})

    album = read_json(os.path.join(DATA, "soulboy_tracks.json"))
    tracks = []
    for t in album["tracks"]:
        n = t["trackNumber"]
        ly = read_json(os.path.join(RAW, "lyrics", f"{n:02d}.json"))
        text = ly.get("plainLyrics") or ""
        hits = tokenize(text, lex)
        counts = {cat: sum(hits.get(cat, {}).values()) for cat in LEXICON}
        colours = {}
        for c, terms in tokenize(text, col_lex).items():
            colours[c] = sum(terms.values())
        nature = counts["nature_plants"] + counts["sky_weather"] + counts["water"]
        city = counts["city_street"]
        ed = EDITORIAL[n]
        assert len(ed["quote"]) <= 15
        tracks.append({
            "trackNumber": n,
            "trackName": t["trackName"],
            "lyricLines": sum(1 for line in text.splitlines() if line.strip()),
            "imageryCounts": counts,
            "imageryTerms": {cat: hits[cat] for cat in LEXICON if cat in hits},
            "colourWords": colours,
            "natureVsCity": {"nature": nature, "city": city,
                             "natureShare": round(nature / (nature + city), 2) if nature + city else None},
            "palette": [{"hex": h, "reason": r} for h, r in ed["palette"]],
            "mood": ed["mood"],
            "hoverQuote": ed["quote"],
        })
    write_json(os.path.join(DATA, "soulboy_imagery.json"), {
        "collectionId": album["collectionId"],
        "method": ("Counts: greedy longest-first match of a hand-built lexicon over LRCLIB plainLyrics "
                   "(repeated choruses count each time). nature = nature_plants + sky_weather + water; "
                   "city = city_street. "
                   "Palette, mood and hoverQuote are hand-curated interpretation, not measured."),
        "categories": list(LEXICON),
        "tracks": tracks,
    })
    for x in tracks:
        print(x["trackNumber"], x["trackName"], x["imageryCounts"], x["colourWords"], x["natureVsCity"])


if __name__ == "__main__":
    main()
