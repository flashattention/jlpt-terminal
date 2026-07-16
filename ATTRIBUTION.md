# Data attribution & licensing

This repo's own source code is MIT-licensed (see `LICENSE`). The study
data bundled in `data/study.sqlite` comes from third-party sources under
their own, different licenses -- the MIT license above covers the code,
not that data. The actual license terms for the data are in
[LICENSE-DATA](LICENSE-DATA); this document explains where each piece of
data came from and how attribution is handled in practice.

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
it. `build_data.py` fulfils this: it matches every sentence's text against
Tatoeba's own bulk export ("Detailed Sentences" at
https://tatoeba.org/en/downloads, per-language TSV, updated weekly) and
stores that sentence's Tatoeba id and contributing author's username in
`sentences.tatoeba_id` / `sentences.author_username`
(`tatoeba_attribution.py`). The app displays that credit
("-- username, Tatoeba #id (license)") under every example sentence once
the card is flipped -- see `_sentence_credit()` in `jlpt_terminal/app.py`.
15,220 of 15,224 sentences (99.97%) matched; the rest, plus any sentence
with no linked Tatoeba account, show as "an anonymous Tatoeba contributor,"
matching how Tatoeba itself displays them.

(Earlier iteration note: this was originally implemented by querying
Tatoeba's live per-sentence API once per sentence, which turned out to hit
an unpublished rate limit after a few hundred requests -- full backfill at
a request rate that avoided errors projected to ~27 hours. The bulk export
above has the same data already and took 12 seconds to match all 15,224
sentences locally, so that's what `build_data.py` uses.)

The export is cached at `.tatoeba_sentences_detailed.tsv.bz2` so re-running
`build_data.py` doesn't redownload it every time; pass
`--refresh-attribution-export` to force a fresh copy, or
`--skip-attribution` to skip this step entirely (fast, but leaves every
sentence's id/author NULL).

## Sentence readings (`sentences.reading` column)

Computed locally by `build_data.py` from the Tatoeba sentence text above,
using [pykakasi](https://github.com/miurahr/pykakasi) (GPL-3.0-or-later;
used here only as an offline build-time dependency, not distributed as
part of this app). As a mechanical transformation of Tatoeba text, treat
these readings as inheriting the same CC BY 2.0 FR terms as the sentence
they're derived from.
