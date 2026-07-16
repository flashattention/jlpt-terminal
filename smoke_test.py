import asyncio

from textual.widgets import Static

from jlpt_terminal.app import JlptTerminalApp, LevelSelectScreen, StudyScreen


def card_text(screen: StudyScreen) -> str:
    return str(screen.query_one("#card-body", Static).content)


async def run() -> None:
    app = JlptTerminalApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, LevelSelectScreen)

        await pilot.press("enter")
        assert isinstance(app.screen, StudyScreen), "did not enter study screen"
        screen = app.screen
        first_word = screen._current
        assert not screen._flipped
        front_text = card_text(screen)
        assert first_word.expression in front_text
        assert first_word.reading in front_text
        assert first_word.definitions not in front_text, "meaning leaked before flip"

        await pilot.press("space")
        assert screen._flipped, "card did not flip"
        back_text = card_text(screen)
        assert first_word.definitions in back_text, "meaning missing after flip"
        if first_word.sentences:
            sentence = first_word.sentences[0]
            assert sentence.japanese_text in back_text
            assert sentence.reading in back_text
            assert sentence.english_text in back_text

        await pilot.press("right")
        assert not screen._flipped, "flip state should reset on next"
        second_word = screen._current
        assert second_word.expression != first_word.expression

        await pilot.press("left")
        assert screen._current.expression == first_word.expression, (
            "prev did not return to first word"
        )

        # wraparound: prev from index 0 goes to the last word
        await pilot.press("left")
        assert screen._index == len(screen._words) - 1, "prev did not wrap around"
        await pilot.press("right")
        assert screen._index == 0, "next did not wrap back to start"

        await pilot.press("s")
        assert screen._shuffled
        await pilot.press("s")
        assert not screen._shuffled

        await pilot.press("escape")
        assert isinstance(app.screen, LevelSelectScreen), "did not go back to level select"

        await pilot.press("q")
        assert not app.is_running or app._exit

    print("SMOKE TEST PASSED")


asyncio.run(run())
