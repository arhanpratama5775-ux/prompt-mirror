# changelog

what changed and when.

---

## 0.3.0 - 2026-05-27

- rewrote README (the old one was... a lot)
- fresh repo start

## 0.2.0 - 2026-05-27

### new stuff
- `prompt-mirror trend` — see how your AI usage changes over time (monthly activity, topic evolution, behavior shifts)
- PDF export — `prompt-mirror analyze --format pdf`
- visualizations — topic charts, time patterns, question types
  - `prompt-mirror visualize conversations.json --output charts/`

### security
- path traversal protection on all file paths
- 500MB file size limit (your exports shouldn't be that big)
- output filename sanitization
- better .gitignore so you don't accidentally commit your chat history

### fixes
- gemini conversations now get proper titles instead of generic ones
- better memory handling for large files
- division by zero in trend analysis (whoops)
- empty prompts edge case
- sorting is now deterministic (results are consistent)

### other
- cross-platform fonts for PDF (works on mac/windows too now)
- encoding fallback for weird file encodings (UTF-8-sig, UTF-16, Latin-1, CP1252)
- better timezone error messages
- HTML escaping in PDFs
- text truncation for long content in PDF tables

## 0.1.0 - 2026-05-20

the beginning.

- chatgpt, claude, gemini export support
- topic analysis (10 categories)
- time pattern analysis
- question type detection (how, why, what, should, etc.)
- behavioral pattern detection
- reflection questions
- output formats: text, json, markdown
- timezone-aware analysis
- CLI commands: analyze, stats, topics, guide

---

## upgrading

```bash
cd prompt-mirror
git pull origin main
pip install -e ".[all]"
```

that's it.

---

## maybe later (roadmap)

- web interface
- more AI platforms (perplexity, etc.)
- custom topic definitions
- batch processing
- before/after comparison reports
- i18n for topic detection
- ML-based topic classification
- note-taking app integrations
- scheduled reports

no promises on timelines. it's done when it's done.
