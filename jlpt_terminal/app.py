"""Terminal flashcard app for JLPT vocabulary (N5-N1), no audio.

Level-select screen -> flashcard study screen. Each card shows the word,
its reading, part of speech, meaning, and (once flipped) an example
sentence with its own reading and English translation.
"""

from __future__ import annotations

import random

from rich.markup import escape
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, ListItem, ListView, Static

from .db import LEVELS, Sentence, StudyDatabase, Word

LEVEL_LABELS = {
    "N5": "N5 -- Beginner",
    "N4": "N4 -- Upper beginner",
    "N3": "N3 -- Intermediate",
    "N2": "N2 -- Upper intermediate",
    "N1": "N1 -- Advanced",
}


def _sentence_credit(sentence: Sentence) -> str:
    """Tatoeba's CC BY terms require crediting each sentence's author."""
    who = sentence.author_username or "an anonymous Tatoeba contributor"
    credit = f"-- {who}, Tatoeba"
    if sentence.tatoeba_id:
        credit += f" #{sentence.tatoeba_id}"
    if sentence.license:
        credit += f" ({sentence.license})"
    return credit


class LevelSelectScreen(Screen):
    BINDINGS = [Binding("q", "quit_app", "Quit")]

    def __init__(self, db: StudyDatabase):
        super().__init__()
        self._db = db

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        counts = self._db.level_counts()
        items = []
        for level in LEVELS:
            label = f"{LEVEL_LABELS[level]}  ({counts.get(level, 0)} words)"
            items.append(ListItem(Static(label), name=level))
        total = sum(counts.values())
        items.append(ListItem(Static(f"All levels  ({total} words)"), name="ALL"))
        with Center():
            with Middle():
                with Vertical(id="level-menu"):
                    yield Static("JLPT Word King -- Terminal", id="title")
                    yield Static("Choose a level to study", id="subtitle")
                    yield ListView(*items, id="level-list")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        level = event.item.name
        chosen = None if level == "ALL" else level
        words = self._db.words_for_level(chosen)
        if not words:
            return
        self.app.push_screen(StudyScreen(words, level_label=level))

    def action_quit_app(self) -> None:
        self.app.exit()


class StudyScreen(Screen):
    BINDINGS = [
        Binding("enter", "flip", "Flip card"),
        Binding("space", "flip_or_next", "Flip / Next"),
        Binding("right,n,l", "next_word", "Next"),
        Binding("left,p,h", "prev_word", "Previous"),
        Binding("s", "shuffle", "Shuffle"),
        Binding("escape,backspace", "back", "Back to levels"),
        Binding("q", "quit_app", "Quit"),
    ]

    def __init__(self, words: list[Word], level_label: str):
        super().__init__()
        self._original_order = list(words)
        self._words = list(words)
        self._index = 0
        self._flipped = False
        self._level_label = level_label
        self._shuffled = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Center():
            with Middle():
                with Vertical(id="card"):
                    yield Static(id="card-body")
        yield Static(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_card()

    @property
    def _current(self) -> Word:
        return self._words[self._index]

    def _refresh_card(self) -> None:
        w = self._current
        body = self.query_one("#card-body", Static)
        expression = escape(w.expression)
        reading = escape(w.reading)
        pos = f" [{escape(w.part_of_speech)}]" if w.part_of_speech else ""

        if not self._flipped:
            text = (
                f"[b]{expression}[/b]\n\n"
                f"[dim]{reading}[/dim]{pos}\n\n"
                f"[dim italic](press space to reveal meaning, space again for next)[/dim italic]"
            )
        else:
            lines = [
                f"[b]{expression}[/b]  [dim]{reading}[/dim]{pos}",
                "",
                f"[b]Meaning:[/b] {escape(w.definitions)}",
            ]
            if w.sentences:
                sentence = w.sentences[0]
                lines += [
                    "",
                    f"[b]Example:[/b] {escape(sentence.japanese_text)}",
                    f"[dim]{escape(sentence.reading)}[/dim]",
                    f"[i]{escape(sentence.english_text)}[/i]",
                    f"[dim italic]{escape(_sentence_credit(sentence))}[/dim italic]",
                ]
            else:
                lines += ["", "[dim](no example sentence available)[/dim]"]
            text = "\n".join(lines)

        body.update(text)

        status = self.query_one("#status-bar", Static)
        shuffle_note = " (shuffled)" if self._shuffled else ""
        status.update(
            f"{self._level_label}  --  word {self._index + 1}/{len(self._words)}{shuffle_note}"
        )

    def action_flip(self) -> None:
        self._flipped = not self._flipped
        self._refresh_card()

    def action_flip_or_next(self) -> None:
        if self._flipped:
            self.action_next_word()
        else:
            self.action_flip()

    def action_next_word(self) -> None:
        self._index = (self._index + 1) % len(self._words)
        self._flipped = False
        self._refresh_card()

    def action_prev_word(self) -> None:
        self._index = (self._index - 1) % len(self._words)
        self._flipped = False
        self._refresh_card()

    def action_shuffle(self) -> None:
        current_word = self._current
        self._shuffled = not self._shuffled
        self._words = list(self._original_order)
        if self._shuffled:
            random.shuffle(self._words)
        self._index = self._words.index(current_word)
        self._flipped = False
        self._refresh_card()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_quit_app(self) -> None:
        self.app.exit()


class JlptTerminalApp(App):
    CSS = """
    #level-menu {
        width: 60;
        height: auto;
        border: round $accent;
        padding: 1 2;
    }
    #title {
        text-style: bold;
        content-align: center middle;
        width: 100%;
        padding-bottom: 1;
    }
    #subtitle {
        color: $text-muted;
        content-align: center middle;
        width: 100%;
        padding-bottom: 1;
    }
    #level-list {
        height: auto;
    }
    #card {
        width: 80;
        height: auto;
        min-height: 12;
        border: round $accent;
        padding: 2 3;
    }
    #card-body {
        width: 100%;
    }
    #status-bar {
        width: 100%;
        content-align: center middle;
        color: $text-muted;
        padding: 1 0;
    }
    """

    TITLE = "JLPT Word King -- Terminal"

    def __init__(self, db_path: str | None = None):
        super().__init__()
        self._db = StudyDatabase(db_path)

    def on_mount(self) -> None:
        self.push_screen(LevelSelectScreen(self._db))

    def on_unmount(self) -> None:
        self._db.close()


def main() -> None:
    JlptTerminalApp().run()


if __name__ == "__main__":
    main()
