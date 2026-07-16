# JLPT Word King -- Terminal

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A terminal flashcard app for studying JLPT vocabulary (N5 through N1), no
audio required. For each word you get the expression, its reading, part of
speech, meaning, and an example sentence with its own reading and English
translation.

Data comes from the same word/sentence set as the
[jlpt_word_king](../jlpt_word_king) Flutter app. Sentence readings (kana)
aren't in that source data, so `build_data.py` computes them locally with
[pykakasi](https://github.com/miurahr/pykakasi) and bakes everything into a
single `data/study.sqlite` this app ships with -- no dependency on the
source repo at runtime.

The bundled word/sentence data is third-party content under its own
licenses (JMdict, CC BY-SA 4.0; Tatoeba, CC BY 2.0 FR) -- see
[ATTRIBUTION.md](ATTRIBUTION.md). This repo's MIT license (below) covers
only the code in this repo, not that data.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`data/study.sqlite` is already built and checked in. To regenerate it (e.g.
after the source repo's word data changes):

```bash
.venv/bin/python build_data.py --source /path/to/jlpt_word_king/app/assets/db/prebuilt.sqlite
```

## Run

```bash
.venv/bin/python run.py
```

## Controls

| Key | Action |
| --- | --- |
| `↑` / `↓`, Enter | Select a level on the start screen |
| `Space` / `Enter` | Flip the card (show meaning + example sentence) |
| `→` / `n` / `l` | Next word |
| `←` / `p` / `h` | Previous word |
| `s` | Toggle shuffle |
| `Esc` / `Backspace` | Back to level select |
| `q` | Quit |
