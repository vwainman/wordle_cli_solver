def print_relevant_vars_attrs(object: object, keys: list):
    attrs = vars(object)
    for key in keys:
        print(f"{key}:{attrs[key]}")


class GameOver(Exception):
    """User attempted to continue the game after it ended"""

    def __init__(self, wordle: object) -> None:
        if wordle.guess == wordle.answer or wordle.guess_n > 6:
            print("The game is over, call the reset class"
                  " method to play again")
        else:
            print_relevant_vars_attrs(
                wordle, keys=["answer", "guess", "guess_n", "game_over",
                              "all_info"])


class UnclassifiedLetter(Exception):
    """User guess letter was unlabeled"""

    def __init__(self, wordle: object, letter_i) -> None:
        print(
            f"letter situated at index {letter_i} was not able to be labeled")
        print_relevant_vars_attrs(wordle, keys=["answer", "guess", "all_info"])


class InvalidSet(Exception):
    """Answer words or/and allowed words set is invalid"""

    def __init__(self, wordle: object, condition: str) -> None:
        if condition == "empty set(s)":
            print("Allowed words set or answer words set is empty")
        elif condition == "subset larger than superset":
            print("Answer words set should not be "
                  "larger than allowed words set")
        elif condition == "subset not in superset":
            print("Some answer words are not in the allowed words set:")
            for word in wordle.answer_words:
                if word not in wordle.allowed_words:
                    print(f"{word} is absent from allowed words")
