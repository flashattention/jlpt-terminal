# Data attribution & licensing

This repo's own source code is MIT-licensed (see `LICENSE`). The study
data bundled in `data/study.sqlite` comes from third-party sources under
their own, different licenses -- the MIT license above covers the code,
not that data.

## Vocabulary, readings, definitions, part of speech (`words` table)

Sourced from the "JLPT N5 to N1 Japanese Vocabulary" Anki deck
(https://ankiweb.net/shared/info/1550984460), built by
https://github.com/coolmule0/JLPT-N5-N1-Japanese-Vocabulary-Anki (GPL-3.0),
which generates its data by querying https://jisho.org for each word's
JLPT tag. Jisho's dictionary entries are themselves drawn from JMdict,
published by the Electronic Dictionary Research and Development Group
(EDRDG), Monash University: https://www.edrdg.org/jmdict/j_jmdict.html

JMdict is licensed under a Creative Commons Attribution-ShareAlike Licence
(CC BY-SA 4.0) -- https://www.edrdg.org/edrdg/licence.html. That license
requires (a) crediting EDRDG/JMdict as the source, which this document
does, and (b) that works incorporating JMdict data be redistributed under
the same license. So treat `data/study.sqlite`'s `words` table as
**CC BY-SA 4.0**, not MIT: if you redistribute this database, carry this
notice and the ShareAlike term with it.

## Example sentences (`sentences` table)

From [Tatoeba](https://tatoeba.org), fetched via its public search API.
15,221 of the 15,224 sentences bundled here came back from that API
explicitly licensed **CC BY 2.0 FR** (Creative Commons Attribution 2.0
France); the remaining 3 didn't carry a license tag in the API response
(only relevant to audio reuse per Tatoeba's terms) but fall under
Tatoeba's site-wide default of CC BY 2.0 FR for text content.

CC BY 2.0 FR requires citing each sentence's original author when reusing
it. **Known gap:** neither this repo's `build_data.py` nor the upstream
`jlpt_word_king` ETL pipeline it copies from currently retains Tatoeba's
per-sentence author usernames or sentence IDs, so this app cannot yet
produce that per-sentence credit. Anyone distributing this app beyond
casual/personal use should re-fetch the Tatoeba data with the `username`
and sentence `id` fields (both present in Tatoeba's API response) and
publish an attribution list -- see Tatoeba's own guidance:
https://en.wiki.tatoeba.org/articles/show/using-the-tatoeba-corpus

## Sentence readings (`sentences.reading` column)

Computed locally by `build_data.py` from the Tatoeba sentence text above,
using [pykakasi](https://github.com/miurahr/pykakasi) (GPL-3.0-or-later;
used here only as an offline build-time dependency, not distributed as
part of this app). As a mechanical transformation of Tatoeba text, treat
these readings as inheriting the same CC BY 2.0 FR terms as the sentence
they're derived from.
