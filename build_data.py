#!/usr/bin/env python3
"""Build the self-contained study database this app ships with.

Reads the JLPT word/sentence data produced by the jlpt_word_king Flutter
app's ETL pipeline (`prebuilt.sqlite`), adds a hiragana reading for every
example sentence (computed locally with pykakasi -- the source data only
has readings for words, not sentences), looks up each sentence's Tatoeba id
and contributing author (also missing from the source data -- see
`tatoeba_attribution.py`), and writes the result to `data/study.sqlite`.
The terminal app only ever reads that output file, so after running this
once the app has no dependency on the source repo.

Usage:
    .venv/bin/python build_data.py [--source PATH_TO_prebuilt.sqlite]
    .venv/bin/python build_data.py --skip-attribution  # fast, no network
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys

import pykakasi

from tatoeba_attribution import Attribution, AttributionFetcher

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SOURCE = os.path.join(
    _HERE, "..", "jlpt_word_king", "app", "assets", "db", "prebuilt.sqlite"
)
DEFAULT_OUTPUT = os.path.join(_HERE, "data", "study.sqlite")
DEFAULT_ATTRIBUTION_CACHE = os.path.join(_HERE, ".tatoeba_sentences_detailed.tsv.bz2")


def to_hiragana_reading(kks: pykakasi.kakasi, text: str) -> str:
    return "".join(chunk["hira"] for chunk in kks.convert(text))


def build(
    source_path: str,
    output_path: str,
    skip_attribution: bool = False,
    attribution_cache_path: str = DEFAULT_ATTRIBUTION_CACHE,
    refresh_attribution_export: bool = False,
) -> None:
    if not os.path.exists(source_path):
        raise SystemExit(
            f"Source database not found: {source_path}\n"
            "Pass --source /path/to/prebuilt.sqlite"
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.exists(output_path):
        os.remove(output_path)

    src = sqlite3.connect(source_path)
    dst = sqlite3.connect(output_path)
    try:
        dst.executescript(
            """
            CREATE TABLE words (
                id INTEGER NOT NULL PRIMARY KEY,
                expression TEXT NOT NULL,
                reading TEXT NOT NULL,
                part_of_speech TEXT NOT NULL DEFAULT '',
                definitions TEXT NOT NULL,
                jlpt_level TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE sentences (
                id INTEGER NOT NULL PRIMARY KEY,
                japanese_text TEXT NOT NULL,
                reading TEXT NOT NULL DEFAULT '',
                english_text TEXT NOT NULL DEFAULT '',
                license TEXT NOT NULL DEFAULT '',
                tatoeba_id INTEGER,
                author_username TEXT
            );

            CREATE TABLE word_sentences (
                word_id INTEGER NOT NULL REFERENCES words (id),
                sentence_id INTEGER NOT NULL REFERENCES sentences (id),
                PRIMARY KEY (word_id, sentence_id)
            );
            """
        )

        words = src.execute(
            "SELECT id, expression, reading, part_of_speech, definitions, "
            "jlpt_level FROM words"
        ).fetchall()
        dst.executemany(
            "INSERT INTO words (id, expression, reading, part_of_speech, "
            "definitions, jlpt_level) VALUES (?, ?, ?, ?, ?, ?)",
            words,
        )
        print(f"  copied {len(words)} words")

        sentences = src.execute(
            "SELECT id, japanese_text, english_text, license FROM sentences"
        ).fetchall()

        attributions: dict[str, Attribution] = {}
        if not skip_attribution:
            print("Looking up Tatoeba sentence ids + authors...", file=sys.stderr)
            fetcher = AttributionFetcher(
                cache_path=attribution_cache_path,
                refresh=refresh_attribution_export,
            )
            attributions = fetcher.fetch_all([s[1] for s in sentences])

        kks = pykakasi.kakasi()
        enriched = []
        for i, (sid, japanese_text, english_text, license_) in enumerate(sentences, start=1):
            reading = to_hiragana_reading(kks, japanese_text)
            attribution = attributions.get(japanese_text)
            tatoeba_id = attribution.tatoeba_id if attribution else None
            author_username = attribution.author_username if attribution else None
            # Prefer the license already recorded in the source DB (no
            # network round-trip needed); fall back to whatever the
            # attribution lookup found, if anything.
            resolved_license = license_ or (attribution.license if attribution else "") or ""
            enriched.append(
                (sid, japanese_text, reading, english_text, resolved_license, tatoeba_id, author_username)
            )
            if i % 1000 == 0 or i == len(sentences):
                print(f"  processed {i}/{len(sentences)} sentences")
        dst.executemany(
            "INSERT INTO sentences (id, japanese_text, reading, english_text, "
            "license, tatoeba_id, author_username) VALUES (?, ?, ?, ?, ?, ?, ?)",
            enriched,
        )

        pairs = src.execute("SELECT word_id, sentence_id FROM word_sentences").fetchall()
        dst.executemany(
            "INSERT OR IGNORE INTO word_sentences (word_id, sentence_id) VALUES (?, ?)",
            pairs,
        )
        print(f"  copied {len(pairs)} word-sentence links")

        dst.execute("CREATE INDEX idx_words_level ON words (jlpt_level)")
        dst.execute(
            "CREATE INDEX idx_word_sentences_word ON word_sentences (word_id)"
        )
        dst.commit()
        print(f"Wrote {output_path}")
    finally:
        src.close()
        dst.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--skip-attribution",
        action="store_true",
        help="Skip the Tatoeba id/author lookup (fast, no network calls; "
        "tatoeba_id/author_username end up NULL for every sentence)",
    )
    parser.add_argument(
        "--attribution-cache",
        default=DEFAULT_ATTRIBUTION_CACHE,
        help="Local path for Tatoeba's bulk Japanese sentence export "
        "(downloaded once, then reused across runs)",
    )
    parser.add_argument(
        "--refresh-attribution-export",
        action="store_true",
        help="Redownload Tatoeba's sentence export even if a cached copy "
        "exists (it's updated weekly upstream)",
    )
    args = parser.parse_args()
    build(
        os.path.abspath(args.source),
        os.path.abspath(args.output),
        skip_attribution=args.skip_attribution,
        attribution_cache_path=os.path.abspath(args.attribution_cache),
        refresh_attribution_export=args.refresh_attribution_export,
    )


if __name__ == "__main__":
    main()
