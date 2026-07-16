"""Read-only data access for the study database built by build_data.py."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass, field

_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "study.sqlite"
)

LEVELS = ["N5", "N4", "N3", "N2", "N1"]


@dataclass
class Sentence:
    japanese_text: str
    reading: str
    english_text: str


@dataclass
class Word:
    id: int
    expression: str
    reading: str
    part_of_speech: str
    definitions: str
    jlpt_level: str
    sentences: list[Sentence] = field(default_factory=list)


class StudyDatabase:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or _DEFAULT_DB_PATH
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"Study database not found at {self.db_path}. "
                "Run `python build_data.py` first."
            )
        self._con = sqlite3.connect(self.db_path)

    def close(self) -> None:
        self._con.close()

    def level_counts(self) -> dict[str, int]:
        rows = self._con.execute(
            "SELECT jlpt_level, COUNT(*) FROM words GROUP BY jlpt_level"
        ).fetchall()
        counts = {level: 0 for level in LEVELS}
        counts.update(dict(rows))
        return counts

    def words_for_level(self, level: str | None) -> list[Word]:
        """`level=None` returns words for every level, N5 first."""
        if level is None:
            order = " ".join(f"WHEN '{lv}' THEN {i}" for i, lv in enumerate(LEVELS))
            query = (
                "SELECT id, expression, reading, part_of_speech, definitions, "
                f"jlpt_level FROM words ORDER BY CASE jlpt_level {order} END, id"
            )
            rows = self._con.execute(query).fetchall()
        else:
            rows = self._con.execute(
                "SELECT id, expression, reading, part_of_speech, definitions, "
                "jlpt_level FROM words WHERE jlpt_level = ? ORDER BY id",
                (level,),
            ).fetchall()

        words = [
            Word(
                id=r[0],
                expression=r[1],
                reading=r[2],
                part_of_speech=r[3],
                definitions=r[4],
                jlpt_level=r[5],
            )
            for r in rows
        ]
        self._attach_sentences(words)
        return words

    def _attach_sentences(self, words: list[Word]) -> None:
        if not words:
            return
        by_id = {w.id: w for w in words}
        placeholders = ",".join("?" * len(words))
        rows = self._con.execute(
            "SELECT ws.word_id, s.japanese_text, s.reading, s.english_text "
            "FROM word_sentences ws JOIN sentences s ON s.id = ws.sentence_id "
            f"WHERE ws.word_id IN ({placeholders})",
            [w.id for w in words],
        ).fetchall()
        for word_id, japanese_text, reading, english_text in rows:
            by_id[word_id].sentences.append(
                Sentence(japanese_text=japanese_text, reading=reading, english_text=english_text)
            )
