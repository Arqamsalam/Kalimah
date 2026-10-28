#!/usr/bin/env python3
"""
Turns the Arabic that the guides write in English letters back into Arabic
script, for the site to show.

    "Compare Infiṭār 82:6 — mā gharraka bi-rabbika'l-Karīm"
 -> "Compare Infiṭār 82:6 — ⟦مَا غَرَّكَ بِرَبِّكَ ٱلْكَرِيمِ|mā gharraka bi-rabbika'l-Karīm⟧"

Nothing is guessed. A run of English letters becomes Arabic only when it can
be found: in the verse the note points at ("82:6 —"), in the word's own verse,
anywhere in its surah, anywhere in the Qur'an, among the dictionary forms of
Qur'anic words, among the verb tables, or among the common particles. The
Arabic always comes from that source, never from spelling the letters out.

Each converted span keeps the original letters beside the Arabic — ⟦arabic|latin⟧
— so the site can show the Arabic while its matching and its quiz still read
the guide's own words. Surah names, grammar terms and names in an English
sentence are left as they are.

The guides mark their Arabic in *italics*. build.py hands over every phrase a
guide italicises, and a run found among them is read more generously than one
in plain text — a lone "min" or "bi" is only turned into Arabic there.

Source: the Quranic Arabic Corpus morphology — the same file build_morph.py
uses (.morph-cache.txt).
"""

import json, os, re, unicodedata
from collections import defaultdict

HERE     = os.path.dirname(os.path.abspath(__file__))
SARF_JS  = os.path.join(HERE, "data", "sarf.js")

OPEN, SEP, CLOSE  = "⟦", "|", "⟧"

# ------------------------------------------------------------- Arabic script

FATHA, DAMMA, KASRA = "\u064e", "\u064f", "\u0650"
TAN_F, TAN_D, TAN_K = "\u064b", "\u064c", "\u064d"
SHADDA, SUKUN       = "\u0651", "\u0652"
DAGGER, MADDA       = "\u0670", "\u0653"
HAMZA_A, HAMZA_B    = "\u0654", "\u0655"
WASLA, TATWEEL      = "\u0671", "\u0640"
MARKS = set(FATHA + DAMMA + KASRA + TAN_F + TAN_D + TAN_K + SHADDA + SUKUN + DAGGER + MADDA + HAMZA_A + HAMZA_B)

# recitation marks — pause signs and small letters — as fetch_verses.py drops them
def strip_marks(s):
    return re.sub("[\u06d6-\u06ed]", "", s)

CONS = {"ب": "b", "ت": "t", "ث": "th", "ج": "j", "ح": "ḥ", "خ": "kh", "د": "d", "ذ": "dh",
        "ر": "r", "ز": "z", "س": "s", "ش": "sh", "ص": "ṣ", "ض": "ḍ", "ط": "ṭ", "ظ": "ẓ",
        "ع": "ʿ", "غ": "gh", "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
        "ه": "h", "و": "w", "ي": "y", "ء": "ʾ", "أ": "ʾ", "إ": "ʾ", "ؤ": "ʾ", "ئ": "ʾ",
        "ة": "t", "ى": "y", "ا": "", "ٱ": "", "آ": "ʾ"}
SUN = set("تثدذرزسشصضطظلن")
VOWEL = {FATHA: "a", DAMMA: "u", KASRA: "i"}


def units(word):
    """letter + the marks on it.  A hamza written on a tatweel (مَـَٔابًا)
    is a letter of its own."""
    word = re.sub(TATWEEL + "([" + FATHA + DAMMA + KASRA + "]*)" + HAMZA_A, "ء\\1", word)
    out = []
    for ch in word:
        if ch == TATWEEL:
            continue
        if ch in MARKS and out:
            out[-1][1].append(ch)
        elif ch in CONS:
            out.append([ch, []])
    return out


def translit(word, first=True):
    """One Arabic word in the guides' scheme, case ending kept.  first: the
    word starts a phrase, so its wasla is spoken.  An article lām that melts
    into a sun letter comes out as LAM_SUN, for forms() to write both ways."""
    u = units(word)
    out = []
    n = len(u)
    nxt = lambda i: u[i + 1] if i + 1 < n else (None, [])
    for i, (ch, mk) in enumerate(u):
        vowel = next((VOWEL[m] for m in mk if m in VOWEL), "")
        tan = next(({TAN_F: "an", TAN_D: "un", TAN_K: "in"}[m] for m in mk if m in (TAN_F, TAN_D, TAN_K)), "")
        prev = out[-1] if out else ""
        nch, nmk = nxt(i)
        bare = not (vowel or tan or SHADDA in mk or HAMZA_A in mk or HAMZA_B in mk or MADDA in mk)
        unvowelled = lambda m: not any(x in VOWEL or x in (TAN_F, TAN_D, TAN_K, SHADDA) for x in m)
        # hamzat al-waṣl: ٱ, or a bare alif before the article's lām or a
        # consonant with sukūn — spoken only at the start of a phrase
        if ch == "ٱ" or (ch == "ا" and bare and (
                (nch == "ل" and unvowelled(nmk)) or
                SUKUN in nmk or (i == 0 and (SHADDA in nmk or (nch and nch != "ل" and unvowelled(nmk)))))):
            if i == 0 and first:
                out.append("a" if nch == "ل" else "i")
            continue
        if ch == "آ" or (ch == "ا" and MADDA in mk):
            if prev.endswith("a"):
                out[-1] = prev[:-1] + "ā"          # سَآءَ: a long ā before the hamza
            else:
                out.append(("ʾ" if i else "") + "ā")
            continue
        if ch == "ا" and not (HAMZA_A in mk or HAMZA_B in mk):
            if vowel or tan:
                out.append(vowel or tan)
            elif prev.endswith("a"):
                out[-1] = prev[:-1] + "ā"
            elif prev.endswith(("an", "ū")) or not prev or (prev.endswith("w") and SUKUN in u[i - 1][1]):
                pass                               # the alif of -an, the silent alif after -ū and -aw
            elif prev.endswith(("i", "u")):
                pass                               # bi + alif of the article
            else:
                out.append("ā")
            continue
        if ch == "ى" and not vowel and SHADDA not in mk and not (i and SUKUN in u[i - 1][1] and DAGGER not in mk):
            if prev.endswith("an"):
                continue                           # هُدًى: the yāʾ is only a seat
            if prev.endswith("a"):
                out[-1] = prev[:-1] + "ā"
            elif prev.endswith("i"):
                out[-1] = prev[:-1] + "ī"
            else:
                out.append("ā")
            continue
        if ch in "وي" and not vowel and not tan and SHADDA not in mk and SUKUN not in mk and DAGGER not in mk:
            short, long_ = {"و": ("u", "ū"), "ي": ("i", "ī")}[ch]
            if prev.endswith(short):
                out[-1] = prev[:-1] + long_
                continue
        c = CONS[ch]
        if ch == "ل" and not vowel and SHADDA not in mk and nch in SUN and SHADDA in nmk \
                and i >= 1 and u[i - 1][0] in "اٱ":
            out.append(LAM_SUN)                    # al-shams ~ ash-shams
            continue
        if SHADDA in mk:
            c = c + c
        seg = c
        if DAGGER in mk:
            seg += "ā"
        elif tan:
            seg += tan
        elif vowel:
            seg += vowel
        out.append(seg)
    return "".join(out)


LAM_SUN = "\x01"


def expand(t):
    """both spellings of an article before a sun letter"""
    return {t.replace(LAM_SUN, "l"), t.replace(LAM_SUN, "")}


def forms(word, first=True, pausal=True, weak=False):
    """the shapes a guide may write a word in: with its case ending, and in
    pause (no ending, -ah for tāʾ marbūṭah, -ā for -an), the article spoken
    or melted into a sun letter"""
    base = translit(word, first=first)
    res = {base}
    if pausal:
        res.add(re.sub(r"(un|in|u|i|a)$", "", base))
        if base.endswith("an"):
            res |= {base[:-2], base[:-2] + "ā"}
        res |= {re.sub(r"iy$", "ī", r) for r in list(res)}
        res |= {re.sub(r"uw$", "ū", r) for r in list(res)}
        if word.rstrip("".join(MARKS)).endswith("ة"):
            stem = re.sub(r"t(un|in|an|u|i|a)?$", "", base)
            res.add(stem + "h")
            if not weak:                           # nāḍira for nāḍirah: tried last, since janna is جَنَّ
                res.discard(stem)
            else:
                res.add(stem)
    if re.search("لل" + "[" + FATHA + SHADDA + "]{2}" + "ه", word):
        res |= {r.replace("llah", "llāh") for r in res}
    u = units(word)
    if u and u[0][0] in "ٱا" and base[:1] in ("a", "i"):
        res |= {v + r[1:] for r in list(res) for v in "aiu"}   # ٱلْتَفَّتِ: il-, not al-
    out = set()
    for r in res:
        if r:
            out |= expand(r)
    return out


# ------------------------------------------------------------- Latin, loosely
def lat(s):
    """the comparison key: no case, no dots or lengths, no ʿ ʾ, digraphs as one
    letter, doubled letters once — the same as lat() in index.html"""
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    for a, b in (("kh", "x"), ("sh", "$"), ("th", "8"), ("dh", "9"), ("gh", "g")):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z$89]", "", s)
    return re.sub(r"(.)\1+", r"\1", s)


def skey(s):
    """the strict key: long vowels, doubled letters, ʿayn, the dotted letters
    and a final hamza all still count — ʿalaqah (a clot) and ʿalāqah (a
    relationship) stay apart, so do karam and karram, ʿaṣr and asr, rajāʾ
    and rajā.  Only a hamza inside or at the start of a word is let go: the
    guides write al-akram for al-ʾakram."""
    s = unicodedata.normalize("NFD", str(s).lower())
    s = re.sub("ʾ(?![\\s\\-]|$)", "", s)
    for a, b in (("a\u0304", "A"), ("i\u0304", "I"), ("u\u0304", "U"), ("h\u0323", "H"), ("s\u0323", "S"),
                 ("d\u0323", "D"), ("t\u0323", "T"), ("z\u0323", "Z"), ("ʿ", "3"), ("ʾ", "2")):
        s = s.replace(a, b)
    s = "".join(c for c in s if not unicodedata.combining(c))
    for a, b in (("kh", "x"), ("sh", "$"), ("th", "8"), ("dh", "9"), ("gh", "g")):
        s = s.replace(a, b)
    return re.sub(r"[^a-zAIUHSDTZ$8923]", "", s)


def ratio(a, b):
    """1 − edit distance / longer length"""
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if not la or not lb:
        return 0.0
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
        prev = cur
    return 1 - prev[lb] / max(la, lb)


# ------------------------------------------------------------- the lexicon
class Lexicon:
    """Every word of the Qur'an, its dictionary form, and the verb tables —
    each filed under the Latin keys a guide could write it as."""

    def __init__(self, corpus_lines, verses=None):
        self.words = {}                 # (s, v) -> [word dicts], in order
        self.single = defaultdict(lambda: defaultdict(int))   # key -> arabic -> count
        segs = defaultdict(list)
        for line in corpus_lines:
            p = line.rstrip("\n").split("\t")
            if len(p) < 4:
                continue
            bits = p[0].split(":")
            if len(bits) != 4:
                continue
            s, v, w, _ = bits
            f = p[3].split("|")
            lem = next((t[4:] for t in f if t.startswith("LEM:")), "")
            segs[(int(s), int(v), int(w))].append((p[1], set(t for t in f if ":" not in t), lem))
        shown = verses or {}
        for (s, v, w) in sorted(segs):
            parts = segs[(s, v, w)]
            text = strip_marks("".join(x[0] for x in parts))
            q = shown.get(str(s), {}).get(str(v))
            if q and w <= len(q["w"]):
                text = strip_marks(q["w"][w - 1][0])          # the site's own spelling
            else:
                text = text.replace(FATHA + DAGGER, FATHA + TATWEEL + DAGGER)
            self.words.setdefault((s, v), []).append({"ar": text, "segs": parts})
            for ar in self.variants(parts, text):
                self.file(ar)
            for _, _, lem in parts:
                if lem and len(units(lem)) > 1:
                    self.file(strip_marks(lem))
        self.lead = defaultdict(list)   # first 3 letters of a word's key -> where it stands
        for (s, v), ws in self.words.items():
            for i, wd in enumerate(ws):
                wd["keys"] = {skey(f) for f in forms(wd["ar"])}
                wd["head"] = {skey(x) for x in expand(translit(wd["ar"]))}
                wd["inner"] = {skey(x) for x in expand(translit(wd["ar"], first=False))}
                wd["last"] = {skey(f) for f in forms(wd["ar"], first=False)}
                wd["vmap"], wd["vweak"] = {}, {}
                for var in sorted(self.variants(wd["segs"], wd["ar"]) | {wd["ar"]}, key=len, reverse=True):
                    for f in forms(var) | expand(translit(var, first=False)):
                        wd["vmap"][skey(f)] = var
                    for f in forms(var, weak=True):
                        wd["vweak"].setdefault(skey(f), var)
                for k in {k[:3] for k in wd["keys"] | wd["inner"] if k}:
                    self.lead[k].append((s, v, i))
        self.wcache = {}
        self.add_sarf()

    def file(self, ar):
        """file one spelling under its strict keys.  exact: the key of the
        word as spelled, case ending and all; otherwise a pausal shape"""
        base = {skey(x) for x in expand(translit(ar))}
        for f in forms(ar):
            k = skey(f)
            self.single[k][ar] += 1000 if k in base else 1     # janna: جَنَّ, not جَنَّة in pause

    @staticmethod
    def variants(parts, text):
        """the word, and the word without its wa-/fa-/bi-/al- and without its
        attached pronoun — the guides cite all of these"""
        out = {text}
        core = list(parts)
        while core and "PREF" in core[0][1] and len(core) > 1:
            core = core[1:]
            out.add(strip_marks("".join(x[0] for x in core)))
        bare = [x for x in core if "SUFF" not in x[1]]
        if bare and len(bare) < len(core):
            out.add(strip_marks("".join(x[0] for x in bare)))
        stem = [x for x in bare if "PREF" not in x[1]]
        if stem:
            # with the article gone, a sun letter loses the shadda it gave it
            t = strip_marks("".join(x[0] for x in stem))
            if t and t[0] in CONS and len(t) > 1 and t[1] == SHADDA:
                t = t[0] + t[2:]
            elif len(t) > 2 and t[1] in MARKS and t[2] == SHADDA:
                t = t[0] + t[1] + t[3:]
            out.add(t)
        return {o for o in out if len(units(o)) > 1 and o[:1] in CONS}

    def add_sarf(self):
        if not os.path.exists(SARF_JS):
            return
        src = open(SARF_JS, encoding="utf-8").read()
        m = re.search(r"const SARF\s*=\s*(\{.*?\});", src, re.S)
        if not m:
            return
        for row in json.loads(m.group(1)).values():
            for cell in row[:11]:
                if not isinstance(cell, str):
                    continue
                for ar in re.split(r"[،,/]\s*", cell):
                    ar = ar.strip()
                    if ar.startswith("لَا "):
                        ar = ar[4:]
                    if ar and " " not in ar and len(units(ar)) > 1:
                        self.file(ar)

    def window_keys(self, s, v, i, m):
        """the Latin keys words i..i+m of a verse can be written as: the first
        with its waṣla spoken, the last in pause or not"""
        ck = (s, v, i, m)
        if ck in self.wcache:
            return self.wcache[ck]
        ws = self.words[(s, v)][i:i + m]
        keys = {""}
        for j, wd in enumerate(ws):
            if m == 1:
                opts = wd["keys"] | wd["inner"]
            elif j == 0:
                opts = wd["head"] | wd["inner"] | wd["keys"]
            elif j == m - 1:
                opts = wd["last"]
            else:
                opts = wd["inner"] | wd["last"]
            keys = {k + o for k in keys for o in opts}
            if len(keys) > 256:
                keys = set(sorted(keys)[:256])
        self.wcache[ck] = keys
        return keys

    # --------------------------------------------------------- finding a run
    def in_verse(self, s, v, key, ntok, loose_ok, weak=False):
        """the run in one verse; loose_ok lets a near spelling count, for the
        verse a note is pointing at; weak, a tāʾ marbūṭah written -a"""
        ws = self.words.get((s, v))
        if not ws:
            return None
        if weak:
            return next((wd["vweak"][key] for wd in ws if key in wd["vweak"]), None) if ntok <= 2 else None
        best = None
        lk = lat(key) if loose_ok else None
        if ntok <= 2:
            for wd in ws:
                if key in wd["vmap"]:
                    return wd["vmap"][key]
        for m in range(max(1, ntok - 1), ntok + 3):
            for i in range(0, len(ws) - m + 1):
                ks = self.window_keys(s, v, i, m)
                if key in ks:
                    return " ".join(w["ar"] for w in ws[i:i + m])
                if lk and abs(m - ntok) <= 1:
                    loose = {lat(k) for k in ks}
                    if any(abs(len(x) - len(lk)) <= 3 for x in loose):
                        r = max(ratio(x, lk) for x in loose if abs(len(x) - len(lk)) <= 3)
                        if r >= 0.88 and (best is None or r > best[0]):
                            best = (r, " ".join(w["ar"] for w in ws[i:i + m]))
        return best[1] if best else None

    def anywhere(self, key, ntok, only=None, prefer=None):
        """an exact run in one surah (only), or anywhere — the surah it is
        quoted from first"""
        spots = self.lead.get(key[:3], []) + self.lead.get(key[:2], []) + self.lead.get(key[:1], [])
        if only is not None:
            spots = [x for x in spots if x[0] == only]
        elif prefer:
            spots = sorted(spots, key=lambda x: x[0] != prefer)
        for (s, v, i) in spots:
            n = len(self.words[(s, v)])
            if ntok <= 2 and key in self.words[(s, v)][i]["vmap"]:
                return self.words[(s, v)][i]["vmap"][key]
            for m in range(max(1, ntok - 1), ntok + 3):
                if i + m > n:
                    break
                if key in self.window_keys(s, v, i, m):
                    return " ".join(w["ar"] for w in self.words[(s, v)][i:i + m])
        return None

    def one_word(self, latin, exact=False):
        c = self.single.get(skey(latin))
        if not c:
            return None
        best = max(c.items(), key=lambda x: (x[1], -len(x[0])))
        if exact and best[1] < 1000:
            return None
        return best[0]


# ------------------------------------------------------------- the notes
LETTER = "A-Za-zÀ-ÖØ-öø-ɏḀ-ỿ"
TOKEN = re.compile("[ʿʾ'’‘]?[" + LETTER + "ʿʾ]+(?:[-'’‘ʿʾ]+[" + LETTER + "ʿʾ]+)*")
MARKED = re.compile("[ʿʾāīūḥṣḍṭẓĀĪŪḤṢḌṬẒ]|'l-|['’][" + LETTER + "]")
REF = re.compile(r"(?<![\d:])(\d{1,3}):(\d{1,3})(?:\s*[–-]\s*(\d{1,3}))?|\bv\.?\s*(\d{1,3})(?:\s*[–-]\s*(\d{1,3}))?")
NOT_ARABIC = re.compile(r"[cepovx]")       # letters the scheme never uses
JOIN = re.compile("[" + LETTER + "]['’](?:l|[a-zḍṭṣẓ]{1,2})-")   # rabbika'l-Karīm, Allāhu'ṣ-ṣamad
PATTERN = re.compile(r"f[aiuāīū]{0,2}[ʿ']{1,2}[aiuāīū]{0,2}l")   # afʿal, fāʿil, mafʿūl — patterns, not words
PARTICLES = {"bi": "بِ", "wa": "وَ", "fa": "فَ", "li": "لِ", "la": "لَ", "ka": "كَ", "sa": "سَ",
             "al": "ال", "lā": "لَا", "mā": "مَا", "fī": "فِي", "min": "مِنْ", "ʿan": "عَنْ",
             "ilā": "إِلَى", "ʿalā": "عَلَى", "thumma": "ثُمَّ", "kallā": "كَلَّا", "qad": "قَدْ",
             "lam": "لَمْ", "lan": "لَنْ", "hal": "هَلْ", "inna": "إِنَّ", "anna": "أَنَّ",
             "idhā": "إِذَا", "idh": "إِذْ", "law": "لَوْ", "bal": "بَلْ", "aw": "أَوْ", "am": "أَمْ",
             "huwa": "هُوَ", "hiya": "هِيَ", "yā": "يَا", "dhū": "ذُو", "dhī": "ذِي", "dhā": "ذَا", "hum": "هُمْ", "man": "مَنْ", "in": "إِنْ", "an": "أَنْ"}


# grammar and study terms — Arabic, but the guides use them as terms, the way
# English uses "haiku"; they stay in English letters
KEEP = """maṣdar maṣādir iḍāfah sukūn hamzah hamza shaddah shadda tanwīn fatḥah fatḥa ḍammah ḍamma
kasrah kasra tāʾ marbūṭah marbūṭah alif lām mīm nūn wāw yāʾ hāʾ tāʾ fiʿl ḥarf ḥurūf mubtadaʾ
khabar ḥāl tamyīz mafʿūl fāʿil jamʿ mufrad muthannā nakirah maʿrifah majhūl maʿlūm iltifāt sajʿ
jinās qasam istifhām tawkīd taʿajjub tafkhīm tankīr taʿrīf ḥaṣr qaṣr faṣl waṣl ījāz iṭnāb kināyah
istiʿārah tashbīh majāz muḍāriʿ māḍī nahy mabnī muʿrab marfūʿ manṣūb majrūr majzūm ʿaṭf badal
naʿt ṣifah mawṣūl ḍamīr ishārah ẓarf jawāb sharṭ bāb wazn ṣīghah mubālaghah sūrah
makkī madanī tafsīr tajwīd waqf ḥadīth sunnah ṣaḥābah sīrah fiqh balāghah naḥw ṣarf tajnīs
ṭibāq muqābalah tadmīn taqdīm taʾkhīr ḥadhf idghām ikhfāʾ qalqalah madd ghunnah
bāʾ thāʾ jīm ḥāʾ khāʾ dāl dhāl rāʾ zāy zāʾ sīn shīn ṣād ḍād ṭāʾ ẓāʾ ʿayn ghayn fāʾ qāf kāf
juzʾ ajzāʾ manqūṣ maqṣūr mamdūd mushaddad muḍāf muḍāf ilayh zāʾidah muṭlaq maṣdariyyah
muṣḥaf tawḥīd sunnah sūrat""".split()

def lead_shadda_off(ar):
    """مُّكَرَّمَةٍ quoted on its own: that first shadda belongs to the word
    before it (the -in of the last word melting in), so it goes"""
    m = re.match("^([^" + "".join(MARKS) + "])([" + "".join(MARKS) + "]*)", ar)
    if m and SHADDA in m.group(2):
        return m.group(1) + m.group(2).replace(SHADDA, "") + ar[m.end():]
    return ar


def first_upper(s):
    return next((c.isupper() for c in s if c.isalpha() and c not in "ʿʾ"), False)


def caps(s):
    letters = [c for c in s if c.isalpha() and c not in "ʿʾ"]
    return len(letters) >= 2 and all(c.isupper() for c in letters)


class Converter:
    def __init__(self, lexicon, keep=(), names=(), english=()):
        self.lx = lexicon
        self.keep = {skey(k) for k in keep}        # terms that stay in letters
        self.names = {skey(k) for k in names}      # surah names, kept when written as names
        self.english = set(english)                # plain words the guides use as English
        self.cache = {}
        self.log = []

    def refs(self, text, at, surah, end=None):
        """the verses a note points at before position `at`: "Infiṭār 82:6 —",
        "(80:13)", "v.3" — nearest first; and one just after it: "zalzala (99:1)" """
        out = []
        if end is not None:
            m = REF.match(text, end + len(re.match(r"[\s(]{0,3}", text[end:]).group(0)))
            if m and m.group(1) and 1 <= int(m.group(1)) <= 114:
                out.append((int(m.group(1)), int(m.group(2))))
        near = []
        for m in REF.finditer(text, 0, at):
            if at - m.end() > 140:
                continue
            if m.group(1):
                a, b = int(m.group(1)), int(m.group(2))
                c = int(m.group(3)) if m.group(3) else b
                if 1 <= a <= 114:
                    near[:0] = [(a, x) for x in range(b, min(c, b + 12) + 1)]
            else:
                b = int(m.group(4)); c = int(m.group(5)) if m.group(5) else b
                near[:0] = [(surah, x) for x in range(b, min(c, b + 12) + 1)]
        return out + near

    def find(self, latin, ctx, refs, italic):
        key = skey(latin)
        if len(key) < 2:
            return None
        ntok = latin.count(" ") + len(JOIN.findall(latin)) + 1
        ckey = (latin, ctx.get("surah"), tuple(ctx.get("verses", ())), tuple(refs[:6]), italic)
        if ckey in self.cache:
            return self.cache[ckey]
        s = ctx.get("surah")
        near = list(refs[:6]) + [(s, v) for v in ctx.get("verses", ())]
        hit = None
        if len(key) <= 3 and latin.lower() in PARTICLES:
            hit = PARTICLES[latin.lower()] if italic else None
            self.cache[ckey] = hit
            return hit
        if len(key) <= 2:
            return None
        for (a, b) in near:                         # the verse the note is about
            # a near spelling only for a longer quote — one word must be spelled
            # exactly, or ʿAbbās (the lion) would pass for ʿabasa (he frowned)
            hit = self.lx.in_verse(a, b, key, ntok, loose_ok=ntok >= 2 and len(key) >= 10)
            if hit:
                break
        if not hit and ntok == 1:                    # a word spelled exactly, ending and all
            hit = self.lx.one_word(latin, exact=True)
        if not hit and ntok == 1:                    # nāḍira for the verse's نَّاضِرَةٌ
            for (a, b) in near:
                hit = self.lx.in_verse(a, b, key, ntok, False, weak=True)
                if hit:
                    break
        if not hit and s and len(key) >= 4:          # anywhere in this surah
            hit = self.lx.anywhere(key, ntok, only=s)
        if not hit and ntok == 1:
            hit = self.lx.one_word(latin)
        if not hit and (ntok > 1 or len(key) >= 7):  # anywhere in the Qur'an
            hit = self.lx.anywhere(key, ntok, prefer=(refs[0][0] if refs else s))
        if hit:
            hit = lead_shadda_off(hit)
        self.cache[ckey] = hit
        return hit

    def eligible(self, toks, italic):
        words = [t.group(0) for t in toks]
        if any(NOT_ARABIC.search(w.lower()) for w in words):
            return False
        latin = " ".join(words)
        if skey(latin) in self.keep or any(PATTERN.search(w.lower()) for w in words):
            return False
        if first_upper(words[0]) and not caps(words[0]) and skey(latin) in self.names:
            return False
        if len(words) == 1:
            w = words[0]
            if w.lower() in self.english and not MARKED.search(w):
                return False
            if not italic and not caps(w) and first_upper(w) and not w.lower().startswith(("al-", "wa-", "fa-", "bi-")):
                return False                       # a name in an English sentence: Infiṭār, Mūsā
        if not italic and not all(MARKED.search(w) or caps(w) for w in words):
            return False
        if any(skey(w) in self.keep and not caps(w) for w in words) and len(words) < 3:
            return False
        return True

    def convert(self, text, ctx):
        """text -> text with ⟦arabic|latin⟧ spans.  ctx: surah, verses (the
        word's own), italic (the phrases its guide writes in italics)"""
        if not text or OPEN in text:
            return text
        toks = [Tok(t) for t in TOKEN.finditer(text)]
        runs, cur = [], []
        for t in toks:
            if cur and (cur[-1].poss or text[cur[-1].end():t.start()] != " "):
                runs.append(cur); cur = []
            cur.append(t)
        if cur:
            runs.append(cur)
        ital = ctx.get("italic") or set()
        repl = []
        for run in runs:
            i = 0
            while i < len(run):
                done = False
                for j in range(min(len(run), i + 9) - 1, i - 1, -1):
                    sub = run[i:j + 1]
                    a, b = sub[0].start(), sub[-1].end()
                    latin = text[a:b]
                    italic = norm(latin) in ital or (a == 0 and norm(latin[:1].lower() + latin[1:]) in ital)
                    if not self.eligible(sub, italic):
                        continue
                    if a and text[a - 1] == "-" and (a == 1 or not text[a - 2].isalnum()):
                        continue
                    ar = self.find(latin, ctx, self.refs(text, a, ctx.get("surah"), b), italic)
                    if ar:
                        repl.append((a, b, ar, latin))
                        self.log.append((latin, ar, italic))
                        i = j + 1; done = True
                        break
                if not done:
                    i += 1
        merged = []
        for r in repl:
            if merged and text[merged[-1][1]:r[0]] == " ":
                p = merged[-1]
                merged[-1] = (p[0], r[1], p[2] + " " + r[2], text[p[0]:r[1]])
            else:
                merged.append(r)
        repl = merged
        res, last = [], 0
        for a, b, ar, latin in repl:
            res.append(text[last:a]); res.append(OPEN + ar + SEP + latin + CLOSE); last = b
        res.append(text[last:])
        return "".join(res)


class Tok:
    """a token, less any English possessive ('s) on the end"""
    def __init__(self, m):
        g = m.group(0)
        self.poss = bool(re.search("['’]s$", g))
        self.text = g[:-2] if self.poss else g
        self.a = m.start()
        self.b = m.start() + len(self.text)
    def start(self): return self.a
    def end(self): return self.b
    def group(self, _=0): return self.text


def norm(s):
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", s.strip()))


def ngrams(span):
    """every run of words inside an italic span, so a run of the note can be
    looked up whole or in part"""
    ws = [t.group(0) for t in TOKEN.finditer(span)]
    out = set()
    for i in range(len(ws)):
        for j in range(i + 1, min(len(ws), i + 9) + 1):
            out.add(norm(" ".join(ws[i:j])))
    return out
