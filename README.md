# Kalimah

A word-by-word Qur'an vocabulary reference. Every word carries its root, what it
means in that verse, the rhetorical point, the grammar, why that exact word was
chosen, and a memory hook — plus flashcards, a quiz, never-forget traps, and the
threads that run between surahs.

Currently **19 surahs, 451 words**.

---

## Adding a surah — the whole process

1. Go to the **`guides`** folder on GitHub.
2. Click **Add file → Upload files**.
3. Drag in the new `.md` guide.
4. Click **Commit changes**.

That's it. About a minute later the website has the new surah in it — the word
list, the flashcards, the quiz, the traps and the threads, all built automatically.

You never touch the HTML.

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
python3 build.py        # rebuilds data/surahs.js from guides/
python3 -m http.server  # then open http://localhost:8000
```

No installs, no dependencies — just Python 3 and a browser.

---

## What's in here

```
index.html              the whole website (HTML, CSS and JavaScript in one file)
data/surahs.js          generated — every surah's data. Don't edit by hand.
build.py                turns guides/*.md into data/surahs.js
guides/*.md             the source guides
guides/_manual.json     Al-Qiyāmah (75) and Al-Mursalāt (77), typed in by hand
                        rather than parsed — they came from image sheets
.github/workflows/      rebuilds and republishes on every push
```

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
