#!/usr/bin/env python3
"""
Builds data/morph.js — the root and grammar of every word in every verse the
site shows, so tapping a word in a verse can explain it.

Source: the Quranic Arabic Corpus morphology (Jaussen/Dukes), mirrored as a
plain tab-separated file. Each line is one SEGMENT of a word:

    83:1:2:1 <tab> ٱل <tab> P <tab> DET|PREF|LEM:ال

Several segments make one word: prefixes (wa-, al-, bi-), the stem that carries
the root, and suffixes (attached pronouns). This script glues them back into
one entry per word and turns the corpus's shorthand into plain English.

Run it after fetch_verses.py:   python3 build_morph.py
"""

import json, os, re, sys, urllib.request

HERE      = os.path.dirname(os.path.abspath(__file__))
VERSES_JS = os.path.join(HERE, "data", "verses.js")
MORPH_JS  = os.path.join(HERE, "data", "morph.js")
CACHE     = os.path.join(HERE, ".morph-cache.txt")
SOURCE    = ("https://raw.githubusercontent.com/mustafa0x/quran-morphology"
             "/master/quran-morphology.txt")

# ---------------------------------------------------------------- vocabulary

# The word class, as the corpus names it -> what we call it on screen.
KIND = {
    "PN": "Proper noun", "ADJ": "Adjective", "PRON": "Pronoun",
    "DEM": "Demonstrative", "REL": "Relative pronoun", "T": "Time word",
    "LOC": "Place word", "P": "Preposition", "CONJ": "Joining word",
    "SUB": "Subordinating word", "DET": "The (definite article)",
    "NEG": "Negative particle", "INTG": "Question particle",
    "VOC": "Calling particle", "EMPH": "Emphatic lām",
    "ACC": "Accusative particle", "CERT": "Certainty particle",
    "RET": "Retraction particle", "PREV": "Preventive mā",
    "AMD": "Amendment particle", "PRO": "Prohibition particle",
    "CIRC": "Circumstantial particle", "RES": "Restriction particle",
    "AVR": "Aversion particle", "CAUS": "Causal particle",
    "COND": "Conditional particle", "EQ": "Equalisation particle",
    "EXH": "Exhortation particle", "EXL": "Explanation particle",
    "EXP": "Exceptive particle", "FUT": "Future particle",
    "INC": "Inceptive particle", "INL": "Qurʾanic initials",
    "INT": "Interpretation particle", "RSLT": "Result particle",
    "SUR": "Surprise particle", "IMPN": "Imperative verbal noun",
    "REM": "Resumption particle", "ANS": "Answer particle",
    "ATT": "Attention particle", "ADDR": "Term of address",
    "PRP": "Purpose particle", "SUP": "Supplemental particle",
}

FORM = {"1": "Form I", "2": "Form II", "3": "Form III", "4": "Form IV",
        "5": "Form V", "6": "Form VI", "7": "Form VII", "8": "Form VIII",
        "9": "Form IX", "10": "Form X", "11": "Form XI", "12": "Form XII"}

PERSON = {
    "1S": "I", "1P": "we", "2MS": "you (m. sing.)", "2FS": "you (f. sing.)",
    "2MD": "you two", "2FD": "you two (f.)", "2MP": "you (m. pl.)",
    "2FP": "you (f. pl.)", "3MS": "he / it", "3FS": "she / it",
    "3MD": "they two", "3FD": "they two (f.)", "3MP": "they (m.)",
    "3FP": "they (f.)",
}

NOUN_SHAPE = {"MS": "masculine singular", "FS": "feminine singular",
              "MD": "masculine dual", "FD": "feminine dual",
              "MP": "masculine plural", "FP": "feminine plural",
              "M": "masculine", "F": "feminine",
              "S": "singular", "D": "dual", "P": "plural"}

CASE = {"NOM": "nominative — the subject",
        "ACC": "accusative — the object",
        "GEN": "genitive — after a preposition"}

MOOD = {"MOOD:IND": "indicative", "MOOD:SUBJ": "subjunctive",
        "MOOD:JUS": "jussive"}

# Short plain-English glosses for the little pieces that attach to a word.
PREFIX_GLOSS = {
    "و": "and", "ف": "so / then", "ال": "the", "ٱل": "the", "ب": "with / by",
    "ل": "for / to", "ك": "like", "س": "will (future)", "أ": "(question)",
    "ي": "", "ت": "", "ن": "", "ا": "",
}


def spaced(root):
    return " ".join(list(root)) if root else ""


def fetch_source():
    if os.path.exists(CACHE) and os.path.getsize(CACHE) > 1_000_000:
        return open(CACHE, encoding="utf-8").read().splitlines()
    print("  downloading the morphology file (about 6 MB)...", flush=True)
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "kalimah/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        text = r.read().decode("utf-8")
    open(CACHE, "w", encoding="utf-8").write(text)
    return text.splitlines()


def surah_numbers():
    src = open(VERSES_JS, encoding="utf-8").read()
    data = json.loads(re.search(r"const VERSES\s*=\s*(\{.*\});?\s*$", src, re.S).group(1))
    return data


def parse(lines, wanted):
    """location -> list of segments, for the surahs we actually show."""
    words = {}
    for line in lines:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 4:
            continue
        loc, arabic, broad, feats = parts[0], parts[1], parts[2], parts[3]
        bits = loc.split(":")
        if len(bits) != 4:
            continue
        s, v, w, _seg = bits
        if s not in wanted:
            continue
        f = feats.split("|")
        tags = set(t for t in f if ":" not in t)
        root = lemma = ""
        vform = ""
        mood = ""
        for t in f:
            if t.startswith("ROOT:"):
                root = t[5:]
            elif t.startswith("LEM:"):
                lemma = t[4:]
            elif t.startswith("VF:"):
                vform = t[3:]
            elif t.startswith("MOOD:"):
                mood = t
        words.setdefault((s, v, int(w)), []).append(
            dict(ar=arabic, broad=broad, tags=tags, root=root,
                 lemma=lemma, vform=vform, mood=mood))
    return words


def describe(seg):
    """Turn one stem segment into (kind, [detail phrases])."""
    tags = seg["tags"]
    detail = []

    if seg["broad"] == "V":
        kind = "Verb"
        if seg["vform"] and seg["vform"] in FORM:
            detail.append(FORM[seg["vform"]])
        if "PERF" in tags:
            detail.append("past tense")
        elif "IMPF" in tags:
            detail.append("present / future tense")
        elif "IMPV" in tags:
            detail.append("command")
        if "PASS" in tags:
            detail.append("passive (it is done to it)")
        for code, words in PERSON.items():
            if code in tags:
                detail.append(words)
                break
        if seg["mood"] in MOOD and seg["mood"] != "MOOD:IND":
            detail.append(MOOD[seg["mood"]] + " mood")
        return kind, detail

    # nouns, adjectives, participles, particles
    kind = None
    for tag in ("PN", "ADJ", "PRON", "DEM", "REL", "T", "LOC"):
        if tag in tags:
            kind = KIND[tag]
            break
    if kind is None and "INTG" in tags:
        kind = "Question word"
    if kind is None and "NEG" in tags:
        kind = "Negative particle"
    if kind is None and seg["broad"] == "N":
        if "ACT_PCPL" in tags:
            kind = "Active participle"
        elif "PASS_PCPL" in tags:
            kind = "Passive participle"
        elif "VN" in tags:
            kind = "Verbal noun (maṣdar)"
        else:
            kind = "Noun"
    if kind is None:
        for tag in tags:
            if tag in KIND:
                kind = KIND[tag]
                break
    if kind is None:
        kind = "Particle"

    if "ACT_PCPL" in tags and kind != "Active participle":
        detail.append("active participle")
    if "PASS_PCPL" in tags and kind != "Passive participle":
        detail.append("passive participle")
    if "VN" in tags and not kind.startswith("Verbal"):
        detail.append("verbal noun")
    if seg["vform"] and seg["vform"] in FORM and seg["broad"] == "N":
        detail.append("from a " + FORM[seg["vform"]] + " verb")
    if seg["broad"] == "N":
        for code in ("MD", "FD", "MP", "FP", "MS", "FS", "M", "F"):
            if code in tags:
                detail.append(NOUN_SHAPE[code])
                break
    for code, words in PERSON.items():
        if code in tags and "PRON" in tags:
            detail.append(words)
            break
    if "DET" in tags:
        detail.append("definite (has al-)")
    elif "INDEF" in tags:
        detail.append("indefinite")
    for c in ("NOM", "ACC", "GEN"):
        if c in tags:
            detail.append(CASE[c])
            break
    return kind, detail


OBJECT_WHO = {"1S": "me", "1P": "us", "2MS": "you", "2FS": "you",
              "2MP": "you all", "2FP": "you all", "3MS": "him / it",
              "3FS": "her / it", "3MP": "them", "3FP": "them",
              "3MD": "them two", "2MD": "you two"}
OWNER_WHO = {"1S": "my", "1P": "our", "2MS": "your", "2FS": "your",
             "2MP": "your (pl.)", "2FP": "your (pl.)", "3MS": "his / its",
             "3FS": "her / its", "3MP": "their", "3FP": "their",
             "3MD": "their (two)", "2MD": "your (two)"}


def attachment(seg, stem):
    """A short line for a prefix or suffix segment, or None to ignore it."""
    tags = seg["tags"]
    ar = seg["ar"]
    if "PREF" in tags:
        for tag in ("CONJ", "RSLT", "SUP", "DET", "EMPH", "FUT", "INTG", "P",
                    "REM", "SUB", "PRP", "VOC"):
            if tag in tags:
                plain = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", ar).replace("\u0671", "\u0627")
                gloss = PREFIX_GLOSS.get(plain, "")
                name = {"CONJ": "and", "RSLT": "so / then", "SUP": "then",
                        "DET": "the",
                        "EMPH": "certainly (emphatic lām)", "FUT": "will (future)",
                        "INTG": "(makes it a question)", "P": gloss or "preposition",
                        "REM": "and so (resuming)", "SUB": "that",
                        "PRP": "so that", "VOC": "O — (calling)"}[tag]
                return f"{ar} — {name}"
        return None

    if "SUFF" in tags or "PRON" in tags:
        code = next((c for c in PERSON if c in tags), None)
        if not code:
            return None
        stem_person = next((c for c in PERSON if c in stem["tags"]), None)
        if stem["broad"] == "V":
            # The verb stem already states its doer. A pronoun ending that
            # matches it IS that doer — saying it twice only adds noise.
            if code == stem_person:
                return None
            return f"{ar} — {OBJECT_WHO.get(code, PERSON[code])} (receiving the action)"
        return f"{ar} — {OWNER_WHO.get(code, PERSON[code])} (the owner)"
    return None


def build_word(segs):
    stem = None
    for s in segs:
        if "PREF" not in s["tags"] and "SUFF" not in s["tags"]:
            stem = s
            break
    if stem is None:
        stem = max(segs, key=lambda s: len(s["ar"]))

    kind, detail = describe(stem)
    entry = {"k": kind}
    if detail:
        entry["d"] = detail
    if stem["root"]:
        entry["r"] = spaced(stem["root"])
    if stem["lemma"]:
        entry["l"] = stem["lemma"]

    extras = []
    for s in segs:
        if s is stem:
            continue
        line = attachment(s, stem)
        if line:
            extras.append(line)
    if extras:
        entry["x"] = extras
    return entry


def main():
    verses = surah_numbers()
    wanted = set(verses.keys())
    print("  reading morphology for %d surahs..." % len(wanted))
    words = parse(fetch_source(), wanted)

    out = {}
    missing = 0
    for s, chapter in verses.items():
        out[s] = {}
        for v, obj in chapter.items():
            n = len(obj["w"])
            row = []
            for i in range(1, n + 1):
                segs = words.get((s, v, i))
                if not segs:
                    missing += 1
                    row.append({})
                    continue
                row.append(build_word(segs))
            out[s][v] = row

    body = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    with open(MORPH_JS, "w", encoding="utf-8") as f:
        f.write("/* Generated by build_morph.py — do not edit by hand.\n"
                "   Root, lemma and grammar for every word of every verse shown.\n"
                "   Source: the Quranic Arabic Corpus morphology.            */\n")
        f.write("const MORPH = " + body + ";\n")

    total = sum(len(r) for c in out.values() for r in c.values())
    roots = len({w.get("r") for c in out.values() for r in c.values()
                 for w in r if w.get("r")})
    print("\n  %d words, %d distinct roots, %d unmatched  ->  data/morph.js  (%.0f KB)"
          % (total, roots, missing, os.path.getsize(MORPH_JS) / 1024))


if __name__ == "__main__":
    main()
