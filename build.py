#!/usr/bin/env python3
"""
Kalimah — build script.

Reads every  guides/*.md  ("Never-Forget Vocabulary Guide" format)
plus         guides/_manual.json  (surahs entered by hand)
and writes   data/surahs.js       (the file the website loads).

Run it with:   python3 build.py
Nothing else in the site needs to change when you add a surah.
"""
import re, os, json, glob, sys

HERE    = os.path.dirname(os.path.abspath(__file__))
GUIDES  = os.path.join(HERE, "guides")
OUT     = os.path.join(HERE, "data", "surahs.js")

# ---------------------------------------------------------------- surah names
# num: (name, arabic, english, place).  Add or correct entries freely.
SURAH_META = {
1:("Al-Fātiḥah","الفاتحة","The Opening","Makkan"),2:("Al-Baqarah","البقرة","The Cow","Madinan"),
3:("Āl ʿImrān","آل عمران","The Family of ʿImrān","Madinan"),4:("An-Nisāʾ","النساء","The Women","Madinan"),
5:("Al-Māʾidah","المائدة","The Table Spread","Madinan"),6:("Al-Anʿām","الأنعام","The Cattle","Makkan"),
7:("Al-Aʿrāf","الأعراف","The Heights","Makkan"),8:("Al-Anfāl","الأنفال","The Spoils of War","Madinan"),
9:("At-Tawbah","التوبة","The Repentance","Madinan"),10:("Yūnus","يونس","Jonah","Makkan"),
11:("Hūd","هود","Hūd","Makkan"),12:("Yūsuf","يوسف","Joseph","Makkan"),
13:("Ar-Raʿd","الرعد","The Thunder","Madinan"),14:("Ibrāhīm","إبراهيم","Abraham","Makkan"),
15:("Al-Ḥijr","الحجر","The Rocky Tract","Makkan"),16:("An-Naḥl","النحل","The Bee","Makkan"),
17:("Al-Isrāʾ","الإسراء","The Night Journey","Makkan"),18:("Al-Kahf","الكهف","The Cave","Makkan"),
19:("Maryam","مريم","Mary","Makkan"),20:("Ṭā-Hā","طه","Ṭā-Hā","Makkan"),
21:("Al-Anbiyāʾ","الأنبياء","The Prophets","Makkan"),22:("Al-Ḥajj","الحج","The Pilgrimage","Madinan"),
23:("Al-Muʾminūn","المؤمنون","The Believers","Makkan"),24:("An-Nūr","النور","The Light","Madinan"),
25:("Al-Furqān","الفرقان","The Criterion","Makkan"),26:("Ash-Shuʿarāʾ","الشعراء","The Poets","Makkan"),
27:("An-Naml","النمل","The Ant","Makkan"),28:("Al-Qaṣaṣ","القصص","The Stories","Makkan"),
29:("Al-ʿAnkabūt","العنكبوت","The Spider","Makkan"),30:("Ar-Rūm","الروم","The Romans","Makkan"),
31:("Luqmān","لقمان","Luqmān","Makkan"),32:("As-Sajdah","السجدة","The Prostration","Makkan"),
33:("Al-Aḥzāb","الأحزاب","The Combined Forces","Madinan"),34:("Sabaʾ","سبإ","Sheba","Makkan"),
35:("Fāṭir","فاطر","The Originator","Makkan"),36:("Yā-Sīn","يس","Yā-Sīn","Makkan"),
37:("Aṣ-Ṣāffāt","الصافات","Those Ranged in Ranks","Makkan"),38:("Ṣād","ص","Ṣād","Makkan"),
39:("Az-Zumar","الزمر","The Troops","Makkan"),40:("Ghāfir","غافر","The Forgiver","Makkan"),
41:("Fuṣṣilat","فصلت","Explained in Detail","Makkan"),42:("Ash-Shūrā","الشورى","The Consultation","Makkan"),
43:("Az-Zukhruf","الزخرف","The Gold Adornments","Makkan"),44:("Ad-Dukhān","الدخان","The Smoke","Makkan"),
45:("Al-Jāthiyah","الجاثية","The Kneeling","Makkan"),46:("Al-Aḥqāf","الأحقاف","The Sand Dunes","Makkan"),
47:("Muḥammad","محمد","Muḥammad","Madinan"),48:("Al-Fatḥ","الفتح","The Victory","Madinan"),
49:("Al-Ḥujurāt","الحجرات","The Private Chambers","Madinan"),50:("Qāf","ق","Qāf","Makkan"),
51:("Adh-Dhāriyāt","الذاريات","The Winnowing Winds","Makkan"),52:("Aṭ-Ṭūr","الطور","The Mount","Makkan"),
53:("An-Najm","النجم","The Star","Makkan"),54:("Al-Qamar","القمر","The Moon","Makkan"),
55:("Ar-Raḥmān","الرحمن","The Most Merciful","Madinan"),56:("Al-Wāqiʿah","الواقعة","The Inevitable","Makkan"),
57:("Al-Ḥadīd","الحديد","The Iron","Madinan"),58:("Al-Mujādilah","المجادلة","The Pleading Woman","Madinan"),
59:("Al-Ḥashr","الحشر","The Exile","Madinan"),60:("Al-Mumtaḥanah","الممتحنة","She Who Is Examined","Madinan"),
61:("Aṣ-Ṣaff","الصف","The Ranks","Madinan"),62:("Al-Jumuʿah","الجمعة","Friday","Madinan"),
63:("Al-Munāfiqūn","المنافقون","The Hypocrites","Madinan"),64:("At-Taghābun","التغابن","Mutual Loss and Gain","Madinan"),
65:("Aṭ-Ṭalāq","الطلاق","Divorce","Madinan"),66:("At-Taḥrīm","التحريم","The Prohibition","Madinan"),
67:("Al-Mulk","الملك","The Sovereignty","Makkan"),68:("Al-Qalam","القلم","The Pen","Makkan"),
69:("Al-Ḥāqqah","الحاقة","The Inevitable Reality","Makkan"),70:("Al-Maʿārij","المعارج","The Ascending Stairways","Makkan"),
71:("Nūḥ","نوح","Noah","Makkan"),72:("Al-Jinn","الجن","The Jinn","Makkan"),
73:("Al-Muzzammil","المزمل","The Enshrouded One","Makkan"),74:("Al-Muddaththir","المدثر","The Cloaked One","Makkan"),
75:("Al-Qiyāmah","القيامة","The Resurrection","Makkan"),76:("Al-Insān","الإنسان","Man","Madinan"),
77:("Al-Mursalāt","المرسلات","Those Sent Forth","Makkan"),78:("An-Nabaʾ","النبإ","The Great News","Makkan"),
79:("An-Nāziʿāt","النازعات","Those Who Pull Out","Makkan"),80:("ʿAbasa","عبس","He Frowned","Makkan"),
81:("At-Takwīr","التكوير","The Folding Up","Makkan"),82:("Al-Infiṭār","الانفطار","The Cleaving","Makkan"),
83:("Al-Muṭaffifīn","المطففين","Those Who Give Short Measure","Makkan"),
84:("Al-Inshiqāq","الانشقاق","The Splitting Open","Makkan"),85:("Al-Burūj","البروج","The Towering Constellations","Makkan"),
86:("Aṭ-Ṭāriq","الطارق","The Night-Comer","Makkan"),87:("Al-Aʿlā","الأعلى","The Most High","Makkan"),
88:("Al-Ghāshiyah","الغاشية","The Overwhelming","Makkan"),89:("Al-Fajr","الفجر","The Dawn","Makkan"),
90:("Al-Balad","البلد","The City","Makkan"),91:("Ash-Shams","الشمس","The Sun","Makkan"),
92:("Al-Layl","الليل","The Night","Makkan"),93:("Aḍ-Ḍuḥā","الضحى","The Morning Brightness","Makkan"),
94:("Ash-Sharḥ","الشرح","The Relief","Makkan"),95:("At-Tīn","التين","The Fig","Makkan"),
96:("Al-ʿAlaq","العلق","The Clinging Clot","Makkan"),97:("Al-Qadr","القدر","The Night of Decree","Makkan"),
98:("Al-Bayyinah","البينة","The Clear Proof","Madinan"),99:("Az-Zalzalah","الزلزلة","The Earthquake","Madinan"),
100:("Al-ʿĀdiyāt","العاديات","The Chargers","Makkan"),101:("Al-Qāriʿah","القارعة","The Striking Calamity","Makkan"),
102:("At-Takāthur","التكاثر","Rivalry in Increase","Makkan"),103:("Al-ʿAṣr","العصر","The Declining Day","Makkan"),
104:("Al-Humazah","الهمزة","The Slanderer","Makkan"),105:("Al-Fīl","الفيل","The Elephant","Makkan"),
106:("Quraysh","قريش","Quraysh","Makkan"),107:("Al-Māʿūn","الماعون","Small Kindnesses","Makkan"),
108:("Al-Kawthar","الكوثر","Abundance","Makkan"),109:("Al-Kāfirūn","الكافرون","The Disbelievers","Makkan"),
110:("An-Naṣr","النصر","Divine Support","Madinan"),111:("Al-Masad","المسد","The Palm Fibre","Makkan"),
112:("Al-Ikhlāṣ","الإخلاص","Sincerity","Makkan"),113:("Al-Falaq","الفلق","The Daybreak","Makkan"),
114:("An-Nās","الناس","Mankind","Makkan"),
}

DROP = "⭐⚠️🧠✅❌"

def clean(s):
    if not s: return ""
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    for ch in DROP: s = s.replace(ch, " ")
    s = s.replace("***", "").replace("**", "").replace("`", "")
    s = re.sub(r"(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"\1", s)
    s = s.replace("*", "")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^[-–—:·•]\s*", "", s)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = s.replace("( ", "(").replace(" )", ")").replace("“ ", "“").replace(" ”", "”")
    s = re.sub(r"\s+\.", ".", s).strip()
    if s and "a" <= s[0] <= "z": s = s[0].upper() + s[1:]
    return s

def para_clean(block_lines):
    paras, cur = [], []
    for ln in block_lines:
        if ln.strip().startswith("|"): continue          # drop markdown tables
        if not ln.strip():
            if cur: paras.append(" ".join(cur)); cur = []
            continue
        cur.append(ln.strip())
    if cur: paras.append(" ".join(cur))
    return [p for p in (clean(x) for x in paras) if p]

FIELD_RE = re.compile(r"^\s*-\s+(?:🧠\s*)?\*\*([^:*]+?)\s*:\*\*\s*(.*)$")
HEAD_RE  = re.compile(r"^\*\*(\d+)\.\s*(.+?)\*\*\s*·\s*v\.?\s*(.+?)\s*$")

def field_key(label):
    l = label.lower().split("—")[0].strip()
    for prefix, key in (("root feeling","root"), ("here it means","meaning"),
                        ("word magic","magic"), ("grammar bite","grammar"),
                        ("why this","why"), ("never forget","note")):
        if l.startswith(prefix): return key
    return None

def parse_words(lines):
    words, i = [], 0
    while i < len(lines):
        m = HEAD_RE.match(lines[i])
        if not m:
            i += 1; continue
        title = m.group(2)
        verse = clean(m.group(3))
        alt = re.search(r"\(\s*and\s+v\.?\s*([\d,\s–-]+)\)", verse)
        verse = re.sub(r"\s*\([^)]*\)?\s*$", "", verse).strip()
        if alt: verse += " · " + alt.group(1).strip()
        verse = verse.rstrip(" ·,").replace(" · SAJDAH VERSE", "").replace(", repeated v.6", "–6")
        parts = re.split(r"\s+—\s+", title, maxsplit=1)
        ar = clean(parts[0])
        tr = re.sub(r"\s*\([^)]*\)\s*$", "", clean(parts[1]) if len(parts) > 1 else "").strip()
        fields, cur, buf = {}, None, []
        i += 1
        while i < len(lines):
            ln = lines[i]
            if HEAD_RE.match(ln) or ln.startswith("## ") or ln.startswith("---"): break
            fm = FIELD_RE.match(ln)
            if fm:
                if cur: fields[cur] = buf
                cur = field_key(fm.group(1)); buf = [fm.group(2)]
                if cur is None: cur, buf = "_skip", []
            elif cur is not None:
                buf.append(ln)
            i += 1
        if cur: fields[cur] = buf
        w = {"ar": ar, "tr": tr, "v": verse}
        for k in ("root", "meaning", "magic", "grammar", "why", "note"):
            ps = para_clean(fields.get(k, []))
            if ps: w[k] = ("\n" if k == "magic" else " ").join(ps)
        if w.get("ar") and w.get("meaning"): words.append(w)
    return words

def section(lines, title_sub):
    out, on = [], False
    for ln in lines:
        if ln.startswith("## "): on = title_sub.lower() in ln.lower(); continue
        if ln.startswith("# "): on = False; continue
        if on: out.append(ln)
    return out

def numbered_list(lines):
    items, cur = [], None
    for ln in lines:
        m = re.match(r"^\s*\d+\.\s+(.*)$", ln)
        if m:
            if cur: items.append(clean(cur))
            cur = m.group(1)
        elif cur is not None and ln.strip() and not ln.startswith("#"):
            cur += " " + ln.strip()
        elif cur is not None and not ln.strip():
            items.append(clean(cur)); cur = None
    if cur: items.append(clean(cur))
    return [i for i in items if i]

def links_table(lines):
    rows = []
    for ln in lines:
        if not ln.strip().startswith("|"): continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 3 or set(cells[0]) <= set("-: "): continue
        if cells[0].lower().startswith("word here"): continue
        rows.append({"w": clean(cells[0]), "e": clean(cells[1]), "t": clean(cells[2])})
    return rows

def parse_file(path):
    raw = open(path, encoding="utf-8").read()
    lines = raw.split("\n")
    m = re.search(r"#\s*Surah\s+(.+?)\s*\((\d+)\)", lines[0])
    if not m: raise ValueError("first line must look like:  # Surah Al-ʿAlaq (96) — ...")
    fallback, num = clean(m.group(1)), int(m.group(2))
    vm = re.search(r"\(v\.\s*1\s*[–-]\s*(\d+)\)", raw)
    meta = SURAH_META.get(num, (fallback, "", "", "Makkan"))

    one = section(lines, "One Thing That Makes")
    special = para_clean(one)
    hook = ""
    for ln in one:
        if "The hook" in ln: hook = clean(re.sub(r".*The hook:?\*{0,2}", "", ln))
    special = [p for p in special if not p.lower().startswith("the hook")]

    return {
        "num": num, "name": meta[0], "ar": meta[1], "en": meta[2],
        "verses": int(vm.group(1)) if vm else 0, "place": meta[3],
        "blurb": hook or (special[0] if special else ""),
        "special": special,
        "big": numbered_list(section(lines, "The Big Picture")),
        "traps": numbered_list(section(lines, "Never-Forget Traps")),
        "links": links_table(section(lines, "Connect It")),
        "words": parse_words(lines),
    }

# ------------------------------------------------------------------ write out
def js(v): return json.dumps(v, ensure_ascii=False)
ORDER = ["ar","tr","v","rk","root","meaning","magic","grammar","why","note"]

def emit(surahs):
    out = ["""/* Generated by build.py — do not edit by hand.
   Add a guide to guides/ and re-run:  python3 build.py             */
const SURAHS = ["""]
    for s in surahs:
        out.append("{")
        out.append(f"  num:{s['num']}, name:{js(s['name'])}, ar:{js(s['ar'])}, en:{js(s['en'])}, "
                   f"verses:{s['verses']}, place:{js(s['place'])},")
        out.append(f"  blurb:{js(s['blurb'])},")
        for k in ("special", "big", "traps"):
            if s.get(k): out.append(f"  {k}:[" + ",".join(js(x) for x in s[k]) + "],")
        if s.get("links"):
            out.append("  links:[" + ",".join("{w:%s,e:%s,t:%s}" % (js(r["w"]), js(r["e"]), js(r["t"]))
                                              for r in s["links"]) + "],")
        out.append("  words:[")
        for w in s["words"]:
            out.append("  {" + ", ".join(f"{k}:{js(w[k])}" for k in ORDER if w.get(k)) + "},")
        if out[-1].endswith(","): out[-1] = out[-1][:-1]
        out.append("  ]"); out.append("},")
    if out[-1] == "},": out[-1] = "}"
    out.append("];")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(out) + "\n")

def main():
    by_num, problems = {}, []

    manual = os.path.join(GUIDES, "_manual.json")
    if os.path.exists(manual):
        for s in json.load(open(manual, encoding="utf-8")):
            by_num[s["num"]] = s
            print(f"  {s['num']:>3}  {s['name']:<16} {len(s['words']):>3} words   (hand-entered)")

    for path in sorted(glob.glob(os.path.join(GUIDES, "*.md"))):
        try:
            s = parse_file(path)
            if not s["words"]: raise ValueError("no words found — check the file format")
            by_num[s["num"]] = s
            print(f"  {s['num']:>3}  {s['name']:<16} {len(s['words']):>3} words   {os.path.basename(path)}")
        except Exception as e:
            problems.append(f"  !!  {os.path.basename(path)}: {e}")

    surahs = [by_num[k] for k in sorted(by_num)]
    emit(surahs)
    print(f"\n  {len(surahs)} surahs, {sum(len(s['words']) for s in surahs)} words  ->  data/surahs.js")
    if problems:
        print("\nSkipped:"); print("\n".join(problems)); sys.exit(1)

if __name__ == "__main__":
    main()
