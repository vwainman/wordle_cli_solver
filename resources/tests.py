from miscellaneous import *
import pytest
from typing import Union

# checking for yellow with possible duplicates


@pytest.mark.parametrize("guess, letter_i, answer, expected", [
    ("fiver", 0, "theft", False),  # not in answer, not yellow
    ("maker", 1, "trace", True),  # misplaced single occurence, yellow
    ("tratt", 4, "trace", False),  # letter is green in answer, not yellow
    ("sense", 3, "sunns", True),  # double occurence - one green, yellow
    ("yukky", 2, "kooky", True),  # first instance is yellow, 2nd green
    ("yukky", 3, "kooky", False),  # same as above but checking 2nd instance
])
def test_char_is_yellow(guess: str,
                        letter_i: int,
                        answer: str,
                        expected: bool) -> Union(AssertionError, bool):
    assert char_is_yellow(guess, letter_i, answer) == expected
