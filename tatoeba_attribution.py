"""Look up each example sentence's Tatoeba id + contributing author.

`prebuilt.sqlite` (the source this app's `build_data.py` copies from) never
stored a sentence's Tatoeba id or author username -- only its text and
license. Tatoeba's CC BY terms require crediting the original author when
reusing a sentence, so this fills that gap using Tatoeba's own published
bulk export (https://tatoeba.org/en/downloads, "Detailed Sentences",
updated weekly) rather than live per-sentence API calls: querying Tatoeba's
`/api_v0/sentence/{id}` endpoint one at a time for ~15k sentences hits an
unpublished but very real rate limit (confirmed via 429 responses well
before finishing), where downloading their per-language TSV once and doing
a local text lookup is a single ~4MB request.

The export is cached to disk (it's refreshed by Tatoeba weekly, so we don't
need to redownload it on every build) and only covers Japanese ("jpn")
sentences.
"""

from __future__ import annotations

import bz2
import csv
import os
import sys
from dataclasses import dataclass

import requests

_EXPORT_URL = "https://downloads.tatoeba.org/exports/per_language/jpn/jpn_sentences_detailed.tsv.bz2"
_USER_AGENT = "jlpt-terminal/1.0 (offline study-app asset builder; attribution lookup)"


@dataclass
class Attribution:
    tatoeba_id: int | None
    author_username: str | None
    license: str | None = None


def _download_export(cache_path: str) -> None:
    print(
        f"  [attribution] downloading Tatoeba's Japanese sentence export "
        f"(~4MB, updated weekly) to {cache_path}",
        file=sys.stderr,
    )
    session = requests.Session()
    session.headers["User-Agent"] = _USER_AGENT
    response = session.get(_EXPORT_URL, timeout=120)
    response.raise_for_status()
    tmp_path = f"{cache_path}.tmp"
    with open(tmp_path, "wb") as f:
        f.write(response.content)
    os.replace(tmp_path, cache_path)


def _load_export(cache_path: str, refresh: bool) -> dict[str, Attribution]:
    """Returns japanese_text -> Attribution, parsed from Tatoeba's bulk
    "Detailed Sentences" export (columns: id, lang, text, username,
    date_added, date_modified; username is `\\N` when there's no linked
    account).
    """
    if refresh or not os.path.exists(cache_path):
        _download_export(cache_path)

    by_text: dict[str, Attribution] = {}
    with bz2.open(cache_path, mode="rt", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) < 4:
                continue
            sentence_id, _lang, text, username = row[0], row[1], row[2], row[3]
            by_text[text] = Attribution(
                tatoeba_id=int(sentence_id),
                author_username=None if username == "\\N" else username,
            )
    print(f"  [attribution] loaded {len(by_text)} Japanese sentences from export", file=sys.stderr)
    return by_text


class AttributionFetcher:
    def __init__(self, cache_path: str, refresh: bool = False, **_ignored):
        # **_ignored absorbs the old live-API constructor's
        # max_workers/requests_per_second kwargs so build_data.py doesn't
        # need to change its call site.
        self._by_text = _load_export(cache_path, refresh)

    def fetch_all(self, texts: list[str]) -> dict[str, Attribution]:
        result: dict[str, Attribution] = {}
        unmatched = 0
        for text in texts:
            attribution = self._by_text.get(text)
            if attribution is None:
                unmatched += 1
                attribution = Attribution(tatoeba_id=None, author_username=None)
            result[text] = attribution
        print(
            f"  [attribution] matched {len(texts) - unmatched}/{len(texts)} "
            "sentences against the export",
            file=sys.stderr,
        )
        return result
