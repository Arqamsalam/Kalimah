#!/usr/bin/env python3
"""
Pulls the Qur'an text for every surah in data/surahs.js and writes data/verses.js.

For each verse it stores:
  t   the Uthmani Arabic text of the whole verse
  e   the English translation (M.A.S. Abdel Haleem by default)
  w   the word-by-word list: [arabic, english, transliteration] per word

Run it after adding a surah:   python3 fetch_verses.py
It skips surahs that are already in data/verses.js unless you pass --all, or
unless the translation below has changed since they were fetched: then it
pulls them all again by itself.

Source: the Quran.com API (api.quran.com/api/v4), which serves the
Quranic Arabic Corpus word-by-word data.
"""

import json, re, sys, time, urllib.request, urllib.error, os

HERE        = os.path.dirname(os.path.abspath(__file__))
SURAHS_JS   = os.path.join(HERE, "data", "surahs.js")
VERSES_JS   = os.path.join(HERE, "data", "verses.js")
# Which English translation appears under each verse. Change the number and
# the next run fetches every surah again in the new one. The API's English
# options (as it listed them in October 2026):
#   85  M.A.S. Abdel Haleem         20  Saheeh International
#   84  Mufti Taqi Usmani           19  Pickthall
#   22  Yusuf Ali                   95  Maududi (Tafhim)
#   203 Hilali & Khan              149  Bridges
# The Clear Quran (Khattab, 131) is not among them: the free API returns it
# empty. If the chosen one ever comes back empty, FALLBACK is used instead, so
# the site never loses its English.
TRANSLATION = 85
FALLBACK    = 20
NAMES = {131: "The Clear Quran, Dr. Mustafa Khattab", 20: "Saheeh International",
         85: "M.A.S. Abdel Haleem", 84: "Mufti Taqi Usmani", 19: "Pickthall",
         22: "Yusuf Ali", 95: "Maududi (Tafhim)", 203: "Hilali & Khan", 149: "Bridges"}
API         = ("https://api.quran.com/api/v4/verses/by_chapter/{n}"
               "?words=true&word_fields=text_uthmani&fields=text_uthmani"
               "&translations={t}&per_page=300&language=en")

RESOURCES   = "https://api.quran.com/api/v4/resources/translations?language=en"

SUP_RE = re.compile(r"<sup\b[^>]*>.*?</sup>", re.S)   # footnote markers, number and all
# Qur'anic recitation marks (waqf signs, small letters). They are pause and
# tajwid aids, not part of a word's spelling, and the Amiri webfont has no
# glyphs for several of them \u2014 which breaks the letter joins on screen. The
# dagger alef (U+0670) is a real long \u0101 and is deliberately NOT in this set.
ANNOT_RE = re.compile("[\u06D6-\u06ED\u08F0-\u08FF]")
TAG_RE = re.compile(r"<[^>]+>")                       # any other stray markup


def ar(s):
    return ANNOT_RE.sub("", s or "").strip()


def surah_numbers():
    src = open(SURAHS_JS, encoding="utf-8").read()
    return sorted({int(m) for m in re.findall(r"\bnum:\s*(\d+)", src)})


def existing():
    """the verses already fetched, and the translation they were fetched in
    (files from before it was recorded are Saheeh International)"""
    if not os.path.exists(VERSES_JS):
        return {}, None
    src = open(VERSES_JS, encoding="utf-8").read()
    m = re.search(r"const VERSES\s*=\s*(\{.*\});?\s*$", src, re.S)
    t = re.search(r"const VERSES_TRANSLATION\s*=\s*(\{.*?\});", src)
    meta = json.loads(t.group(1)) if t else {"id": 20}
    if meta.get("clean", 1) != CLEANER:
        meta["id"] = None                      # cleaned the old way: fetch again
    return (json.loads(m.group(1)) if m else {}), meta.get("id")


def get(url, tries=4):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "kalimah/1.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if attempt == tries - 1:
                raise
            print("    retry (%s)" % e)
            time.sleep(2 + attempt * 3)


# bump when clean_en() changes, so the next run fetches the verses again
CLEANER = 2


def clean_en(s):
    """the translation as plain text. A footnote or tag between two words
    leaves a space behind ("man<sup>a</sup>from"), and the spaces that
    leaves next to punctuation and quote marks are taken out again."""
    s = SUP_RE.sub(" ", s or "")
    s = TAG_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r"([‘“(\[])\s+", r"\1", s)
    s = re.sub(r"\s+([’”)\]])(?=[\s,.;:!?’”)\]]|$)", r"\1", s)
    return s.strip()


def list_english():
    """what the API does offer in English, so a better id can be picked"""
    try:
        rows = get(RESOURCES).get("translations", [])
    except Exception as e:
        print("     (couldn't list the translations: %s)" % e)
        return
    for t in sorted(rows, key=lambda t: t.get("id", 0)):
        if (t.get("language_name") or "").lower() == "english":
            print("     %4s  %s" % (t.get("id"), t.get("name") or t.get("author_name")))


def has_english(num, tid):
    data = get(API.format(n=num, t=tid))
    return bool((data["verses"][0].get("translations") or [{}])[0].get("text"))


def fetch(num, tid):
    data = get(API.format(n=num, t=tid))
    if not (data["verses"][0].get("translations") or [{}])[0].get("text"):
        raise SystemExit("Translation %s returned nothing for surah %d." % (tid, num))
    out = {}
    for v in data["verses"]:
        key = v["verse_key"].split(":")[1]
        tr  = v.get("translations") or [{}]
        words = []
        for w in v.get("words", []):
            if w.get("char_type_name") != "word":
                continue                      # skip the end-of-verse number glyph
            words.append([
                ar(w.get("text_uthmani")),
                clean_en((w.get("translation") or {}).get("text")),
                ((w.get("transliteration") or {}).get("text") or "").strip(),
            ])
        out[key] = {
            "t": ar(v.get("text_uthmani")),
            "e": clean_en(tr[0].get("text")),
            "w": words,
        }
    return out


def main():
    store, had = existing()
    nums = surah_numbers()
    tid = TRANSLATION
    if not has_english(nums[0], tid):
        print("  !! translation %d came back empty — using %d (%s) instead"
              % (tid, FALLBACK, NAMES.get(FALLBACK, FALLBACK)))
        list_english()
        tid = FALLBACK
    if "--all" in sys.argv:
        store = {}
    elif had != tid:
        print("  the translation is now %s, or its text is cleaned differently — fetching every surah again"
              % NAMES.get(tid, tid))
        store = {}

    for n in nums:
        if str(n) in store:
            print("  %3d  already have it" % n)
            continue
        print("  %3d  fetching..." % n, flush=True)
        store[str(n)] = fetch(n, tid)
        time.sleep(0.4)                        # be polite to the API

    for k in list(store):
        if int(k) not in nums:
            del store[k]                       # surah no longer in the site

    os.makedirs(os.path.dirname(VERSES_JS), exist_ok=True)
    body = json.dumps(store, ensure_ascii=False, separators=(",", ":"))
    with open(VERSES_JS, "w", encoding="utf-8") as f:
        f.write("/* Generated by fetch_verses.py — do not edit by hand.\n"
                "   Qur'an text and word-by-word data from the Quran.com API.\n"
                "   Translation: %s.  */\n" % NAMES.get(tid, tid))
        f.write("const VERSES_TRANSLATION = " +
                json.dumps({"id": tid, "name": NAMES.get(tid, "translation %d" % tid), "clean": CLEANER},
                           ensure_ascii=False) + ";\n")
        f.write("const VERSES = " + body + ";\n")

    v = sum(len(s) for s in store.values())
    w = sum(len(x["w"]) for s in store.values() for x in s.values())
    print("\n  %d surahs, %d verses, %d words  ->  data/verses.js  (%.0f KB)"
          % (len(store), v, w, os.path.getsize(VERSES_JS) / 1024))


if __name__ == "__main__":
    main()
