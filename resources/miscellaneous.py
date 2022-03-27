from os import getcwd, path
from math import log2
import pandas as pd

SAME_LEN_REQ_OUTPUT: str = "guess must be the same length as answer"


def load_words_from_cwd_folder(folder_name: str, file_name: str) -> set:
    folder_dir: str = path.join(getcwd(), folder_name)
    words_file_fp: str = path.join(folder_dir, file_name)
    with open(words_file_fp, "r") as f:
        word_set: set = {w for w in f.read().split("\n")}
    return word_set


def is_invalid_string(string: str, valid_chars: str) -> bool:
    for char in string:
        if char not in valid_chars:
            return True
    return False


def validate_string_list(word_list: list, valid_length: int, valid_chars: str) -> bool:
    # empty list
    if len(word_list) == 0:
        return False
    # invalid characters/list element type
    for word in word_list:
        if not isinstance(word, str) or is_invalid_string(word, valid_chars):
            return False
    return True


def get_letter_stats_df(words: list) -> pd.DataFrame:
    lower_alphabet_count: dict = {letter: 0 for letter in ascii_lowercase}
    df: pd.DataFrame = pd.DataFrame.from_dict(data=lower_alphabet_count.copy(),
                                              orient="index",
                                              columns=["total_count"])
    WORD_LENGTH: int = max(len(w) for w in words)

    for i in range(WORD_LENGTH):
        df[f"idx_{i}_count"] = 0
        df[f"idx_{i}_rel_freq"] = 0

    for word in words:
        for i, letter in enumerate(word):
            row = df.loc[letter]
            row["total_count"] += 1
            row[f"idx_{i}_count"] += 1

    df["total_rel_freq"] = df["total_count"]/sum(df["total_count"])
    for letter in ascii_lowercase:
        for i in range(WORD_LENGTH):
            df[f"idx_{i}_rel_freq"] = df[f"idx_{i}_count"] / \
                sum(df[f"idx_{i}_count"])

    return df


def char_is_green(guess: str, letter_i: int, answer: str) -> bool:
    """check that the guess letter matches answer's letter at that index"""
    return guess[letter_i] == answer[letter_i]


def char_is_yellow(guess: str, letter_i: int, answer: str) -> bool:
    """check that the guess letter at that index was misplaced"""
    if words_have_diff_lengths(guess, answer):
        raise ValueError(SAME_LEN_REQ_OUTPUT)

    # check that the letter is actually in answer
    if not guess[letter_i] in answer:
        return False
    # letter in both guess and answer, but has duplicates in guess and potential duplicates in answer
    elif guess.count(guess[letter_i]) > 1:
        return is_viable_duplicate(guess, letter_i, answer)
    # letter at i is both in guess and answer, check that it's not green
    else:
        return not char_is_green(guess, letter_i, answer)


def is_viable_duplicate(guess: str, letter_i: int, answer: str) -> bool:
    """According to the colour, check to see if the duplicate letter is viable"""

    duplicate_letter: str = guess[letter_i]
    n_greens: int = n_greens_with_letter(guess, duplicate_letter, answer)
    n_possible_yellows: int = answer.count(duplicate_letter) - n_greens
    i: int = 0
    while n_possible_yellows > 0 and i <= letter_i:
        if guess[i] == duplicate_letter and duplicate_letter != answer[i]:
            n_possible_yellows -= 1
            if i == letter_i:
                return True
        i += 1
    return False


def char_is_yellow_safe(guess: str, letter_i: int, answer: str) -> bool:
    """check that guess letter at that index is misplaced in the answer"""
    # WARNING - does not account for potential duplicate letters
    return guess[letter_i] in answer and guess[letter_i] != answer[letter_i]


def char_is_grey(guess: str, letter_i: int, answer: str) -> bool:
    """Check that guess letter at that index is nonexistent in the answer.
       Should the guess letter exist, verify that it isn't a duplicate dud"""
    # letter not in answer
    if guess[letter_i] not in answer:
        return True
    # letter in answer but may be an irrelevant duplicate
    elif guess.count(guess[letter_i]) > 1:
        return not is_viable_duplicate(guess, letter_i, answer)
    else:
        # single letter is in answer
        return False


def char_is_grey_at_idx(guess: str, letter_i: int, answer: str) -> bool:
    """check that the guess letter is nonexistent at that index but elsewhere in the answer"""
    if words_have_diff_lengths(guess, answer):
        raise ValueError(SAME_LEN_REQ_OUTPUT)

    return guess[letter_i] != answer[letter_i] and guess[letter_i] in answer


def n_greens_with_letter(guess: str, duplicate_letter: str, answer: str) -> int:
    """count the number of correctly positioned occurences for a particular letter"""
    if words_have_diff_lengths(guess, answer):
        raise ValueError(SAME_LEN_REQ_OUTPUT)

    count: int = 0
    for i in range(len(guess)):
        if guess[i] == duplicate_letter and answer[i] == duplicate_letter:
            count += 1
    return count


def get_information_bits_gained(old_set: set, new_set: set) -> float:
    """determine the number of times the pool of answer words was cut in half"""
    old_size: int = len(old_set)
    new_size: int = len(new_set)
    if old_size == 0 or new_size == 0 or new_size > old_size:
        raise ValueError(
            f"old set size = {old_size}, new set size = {new_size}, can't divide by zero or the set has gotten bigger")

    return abs(log2(float(new_size)/old_size))


def words_have_diff_lengths(word1: str, word2: str) -> bool:
    """check that both string arguments passed matches in length"""
    return len(word1) != len(word2)


def string_is_valid(string: str, must_have_chars: list) -> bool:
    for char in string:
        if char not in must_have_chars:
            return False

    return True
