# Kalimah

A word-by-word Qur'an vocabulary reference. Every word carries its root, what it
means in that verse, the rhetorical point, the grammar, why that exact word was
chosen, and a memory hook — plus flashcards, a quiz, never-forget traps, and the
threads that run between surahs.

Tap the verse pill on any word's card — or open a surah's **Read** tab — and the
verse itself opens: the Arabic, every word glossed in English below it, and the
translation. The word you are studying is picked out in gold.

Then tap any word inside a verse. A card opens under it with that word's
three-letter root, its dictionary form, what it is grammatically (verb Form II,
past tense, passive, "she/it"), and the little pieces stuck to its front and
back — the *wa-*, the *al-*, the attached pronoun. If the root turns up anywhere
else on the site, it says where.

Currently **20 surahs, 480 words, 492 verses, 2,078 words of Qur'an text**.

English is set in Source Serif 4 — the surah names, the meanings, the notes and
the translations all read like a printed book, while the sans-serif stays on the
controls. The whole type scheme is one block at the end of the stylesheet marked
`the reading voice`.

The surfaces are glass: every panel is translucent and blurs whatever is
behind it, lit by a soft colour wash fixed to the page, with a bright hairline
along its top edge. The whole effect lives in one block at the end of the
stylesheet, marked `liquid glass`, and is driven by tokens — turn `--glass-blur`
down or drop the block entirely and everything falls back to solid cards.

---

## Adding a surah — the whole process

1. Go to the **`guides`** folder on GitHub.
2. Click **Add file → Upload files**.
3. Drag in the new `.md` guide.
4. Click **Commit changes**.

That's it. About a minute later the website has the new surah in it — the word
list, the flashcards, the quiz, the traps and the threads, all built automatically.

You never touch the HTML.

If you are building locally rather than letting GitHub do it, run the three
scripts in order — `build.py` for the vocabulary, `fetch_verses.py` for that
surah's Qur'an text, then `build_morph.py` for its roots and grammar.

### What the file has to look like

The build script reads the same format your existing guides use. The parts it
looks for:

| In the file | Becomes |
|---|---|
| `# Surah Al-ʿAlaq (96) — …` on the first line | the surah name and number |
| `**Order:** mushaf (v.1–19)` | the verse count |
| `## ⭐ The One Thing That Makes This Surah Special` | the gold callout on the surah page |
| `## The Big Picture` (a numbered list) | "The surah in N moves" |
| Each `**1. الْكَلِمَة — *al-kalimah*** · v.3` block | one word entry |
| `## ⚠️ Never-Forget Traps` (a numbered list) | the traps section |
| `## 🔗 Connect It to…` (a table) | the threads to other surahs |

Inside a word block it reads these six lines, in any order:

```
- **Root feeling:** …
- **Here it means:** …
- **Word magic:** …
- **Grammar bite:** …
- **Why this exact word:** …
- 🧠 **Never forget:** …
```

Only *Here it means* and the Arabic word are required; anything missing is simply
left out of that word's card. Stars, warning signs and bold markers are stripped
automatically — write the guide however you normally would.

**Length is handled for you.** The guides run several paragraphs per field; the
site shows the opening claim only — one or two sentences per category — and puts
everything else behind a "Show the full note" tap on the word's card. Nothing is
lost, and no card is a wall of text. The limits are the `BUDGET` line near the top
of `build.py` if you ever want them looser or tighter.

---

## Running it on your own machine (optional)

```bash
python3 build.py         # rebuilds data/surahs.js from guides/
python3 fetch_verses.py  # pulls the Qur'an text for any surah not yet fetched
python3 build_morph.py   # rebuilds data/morph.js — root and grammar per word
python3 -m http.server   # then open http://localhost:8000
```

No installs, no dependencies — just Python 3 and a browser. `fetch_verses.py` and
`build_morph.py` are the parts that need the internet; add `--all` to
`fetch_verses.py` to re-pull every surah, which is what you do after changing
which translation it uses. `build_morph.py` keeps its 6 MB source file in
`.morph-cache.txt` so it only downloads it once.

---

## What's in here

```
index.html              the whole website (HTML, CSS and JavaScript in one file)
data/surahs.js          generated — every surah's vocabulary. Don't edit by hand.
data/verses.js          generated — the Qur'an text and word-by-word. Same.
data/morph.js           generated — root, base form and grammar per word. Same.
build.py                turns guides/*.md into data/surahs.js
fetch_verses.py         pulls data/verses.js from the Quran.com API
build_morph.py          builds data/morph.js from the Quranic Arabic Corpus
guides/*.md             the source guides
guides/_manual.json     Al-Qiyāmah (75) and Al-Mursalāt (77), typed in by hand
                        rather than parsed — they came from image sheets
.github/workflows/      rebuilds and republishes on every push
```

### Where the Qur'an text comes from

`fetch_verses.py` reads the Quran.com API, which serves the Uthmani text and the
word-by-word glosses of the Quranic Arabic Corpus. The verse translation is
**Saheeh International**; the translation number is the `TRANSLATION` line near
the top of the script, with the other options listed beside it. The Clear Quran
(Khattab) is not among them — it isn't openly licensed, so no free API carries it.

One deliberate change is made to the text on the way in: the Qur'anic recitation
marks (waqf signs and the small superscript letters, U+06D6–U+06ED) are removed.
They are pause and tajwīd aids rather than part of a word's spelling, and the
Amiri webfont has no glyphs for several of them, which breaks the letter joins on
screen. The dagger alef, which is a real long ā, is kept.

### Where the root and grammar come from

`build_morph.py` reads the Quranic Arabic Corpus morphology — the scholarly
word-by-word tagging of the whole Qur'an. Every word there is split into
segments (the *wa-*, the *al-*, the stem that carries the root, the attached
pronoun), each with its own tag. The script glues the segments back into one
word and turns the corpus shorthand into plain English: `PERF|VF:2|PASS|3FS`
becomes "Form II · past tense · passive · she / it". The translation table sits
near the top of the script if any wording needs changing.

`build.py` also holds a table of all 114 surah names (Arabic name, English name,
Makkan/Madinan). If a name ever needs correcting, it's near the top of that file.

---

## Publishing it

**Settings → Pages → Source: GitHub Actions.** The site goes live at
`https://<your-username>.github.io/<repo-name>/`.

To use your own domain, add it under **Settings → Pages → Custom domain** and
point a CNAME record at `<your-username>.github.io`.

---

## Notes

Transliteration follows a light academic scheme. The glosses are study notes for
learning vocabulary, not a translation of the Qur'an.
