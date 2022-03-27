from copy import deepcopy
from colorama import Fore, Back, Style
from miscellaneous import *
import random
from solver import WordleSolver
from wordle_exceptions import *


class Wordle:

    WORDLE_LENGTH: int = 5
    MAX_GUESS_N: int = 6
    GAME_OVER_OUTPUT: str = "GAME OVER"
    BAD_INPUT_OUTPUT: str = "Invalid input. Use a valid lowercase five letter word."
    INTRO_OUTPUT: str = ("---Wordle---\nThe aim of the game is to guess an"
                         " unknown five-letter word within six guesses.\nEach guess"
                         f" provides a hint for each letter.\n- {Fore.GREEN}Green{Fore.RESET}"
                         " indicates an exact letter match at that particular position.\n-"
                         f" {Fore.YELLOW}Yellow{Fore.RESET} indicates"
                         " that the letter at that position is elsewhere in the answer."
                         f"\n- {Back.WHITE}{Fore.BLACK}Grey{Style.RESET_ALL}"
                         " infers that the letter is not found in the answer.\n")
    OUTRO_LOSS_OUTPUT: str = "You lost. The answer was "
    OUTRO_WIN_OUTPUT: str = "You won!"
    LETTER_COLOR_SCHEMA: dict = {
        "grey_letters": set(),
        "yellow_idx_letters": {0: [], 1: [], 2: [], 3: [], 4: []},
        "grey_for_idx_letters": {0: [], 1: [], 2: [], 3: [], 4: []},
        "green_idx_letter": {0: "", 1: "", 2: "", 3: "", 4: ""}
    }
    ACTIVE_WORDLE_INTRO: str = ("Follow the prompts to find an optimal word for your active wordle.\n"
                                "g = green, _ = grey, y = yellow, / = grey at index only\n")
    GAME_OVER_REMINDER: str = "GAME OVER: You must reset this Wordle variable to replay or solve an active Wordle"

    def __init__(self,
                 answer_words: set,
                 allowed_words: set,
                 show_output: bool = True,
                 is_automated: bool = False,
                 use_hints: bool = True) -> None:
        self.use_hints: bool = use_hints
        self.original_answer_words: set = answer_words
        self.original_allowed_words: set = allowed_words
        self.answer_words: set = answer_words
        self.allowed_words: set = allowed_words
        self.all_info: dict = deepcopy(Wordle.LETTER_COLOR_SCHEMA)
        self.row_info: dict = deepcopy(Wordle.LETTER_COLOR_SCHEMA)
        self.solver: WordleSolver = None
        self.show_output: bool = show_output
        self.is_automated: bool = is_automated
        self.game_over: bool = False
        self.__game_in_session: bool = False
        self.excluded_answers: set = set()

        self.answer: str = random.choice(tuple(answer_words))
        self.current_guess: str = ""
        self.current_letter_i: int = 0
        self.guess_n: int = 0
        self.used_guesses = []
        self.drawn_squares = []

        if len(allowed_words) == 0 or len(answer_words) == 0:
            raise InvalidSet(self, "empty set(s)")
        elif len(answer_words) > len(allowed_words):
            raise InvalidSet(self, "subset larger than superset")
        elif not answer_words.issubset(allowed_words):
            raise InvalidSet(self, "subset not in superset")
        self.__game_output(Wordle.INTRO_OUTPUT)

    def reset(self) -> None:
        """Reset game attributes.

        Keyword arguments:
        - exclude_solutions -- set of answer words to exclude from the set of original possible answers
        """
        self.answer_words: set = self.original_answer_words
        self.allowed_words: set = self.original_allowed_words
        usable_answers = self.original_answer_words - self.excluded_answers
        if len(usable_answers) == 0:  # no game can be created
            return
        self.answer: str = random.choice(tuple(usable_answers))
        self.current_guess: str = ""
        self.guess_n: int = 0
        self.all_info: dict = deepcopy(Wordle.LETTER_COLOR_SCHEMA)
        self.row_info: dict = deepcopy(Wordle.LETTER_COLOR_SCHEMA)
        self.solver: WordleSolver = None
        self.game_over: bool = False
        self.__game_in_session: bool = False

    def solve_active_wordle(self, n_guesses_so_far: int = 0) -> None:
        # TODO: REFACTOR!
        """solve a user's ongoing Wordle puzzle with recommended guesses calculated via entropy"""
        print(Wordle.ACTIVE_WORDLE_INTRO)
        optimal_guess: str = ""
        colors: str = ""
        game_has_guesses: bool = False if n_guesses_so_far == 0 else True
        self.guess_n = 1

        while 0 > n_guesses_so_far > Wordle.MAX_GUESS_N - 1:
            print(
                f"You can only have a guess number between 0 and {Wordle.MAX_GUESS_N - 1} for assistance")
            n_guesses_so_far = int(
                input("How many guesses have you made so far?"))

        if self.__game_in_session:
            self.reset()

        self.__setup_solver(use_solver=True)
        while not self.game_over:
            while True:
                if game_has_guesses:
                    if optimal_guess == "":  # no solutions generated so far, take user inputs
                        self.current_guess: str = input(
                            f"guess n = {self.current_guess_n} word: ").lower()
                        while not self.current_guess.isalpha() or len(self.current_guess) != Wordle.WORDLE_LENGTH:
                            self.current_guess: str = input(
                                "your word can only contain five ascii letters, try again").lower()
                    else:
                        self.current_guess: str = optimal_guess
                    colors: str = input(
                        "resulting color information (e.g _g_y_)?: ").lower()
                    while not string_is_valid(string=colors, must_have_chars=["g", "y", "/", "_"]) or len(colors) != Wordle.WORDLE_LENGTH:
                        colors: str = input(f"your colors don't have five of the required symbols, recall that:\n" +
                                            "g = green, _ = grey, y = yellow, / = grey at index only\n").lower()
                    self.__color_active_guess(colors)

                for i, letter in enumerate(self.current_guess):
                    if colors[i] == "_":
                        self.row_info["grey_letters"].add(letter)
                    elif colors[i] == "g":
                        self.row_info["green_idx_letter"][i] = letter
                    elif colors[i] == "y":
                        self.row_info["yellow_idx_letters"][i].append(letter)
                    elif colors[i] == "/":
                        self.row_info["grey_for_idx_letters"][i].append(letter)
                    else:
                        raise ValueError(
                            f"{colors[i]} isn't a valid color symbol, you must use '_', 'g', 'y', or '/'")
                self.__update_after_guess()
                self.guess_n += 1

                if self.guess_n == Wordle.WORDLE_LENGTH - 1:
                    # last possible guess
                    self.game_over = True
                    break
                elif n_guesses_so_far <= self.guess_n:
                    # provide solver info
                    break

            if colors == "ggggg" or self.guess_n == Wordle.WORDLE_LENGTH:
                print("Game Over!")
                return

            self.__update_solver(use_solver=True)
            print("Calculating...", flush=True)
            optimal_guess: str = self.solver.get_optimal_guess(
                game_mode="answer_unknown")
            print(f"Try '{optimal_guess}' for your next guess", flush=True)
            game_has_guesses = True

    def play(self):
        """play a fresh game of Wordle"""
        self.__setup_solver()
        self.__game_in_session = True

        while not self.game_over:
            self.play_next_guess()

        self.__game_output(self.__get_game_outcome_output())
        self.__save_solver_info()
        self.reset()

    def __setup_solver(self, use_solver: bool = False) -> None:
        if self.is_automated or use_solver:
            self.solver: WordleSolver = WordleSolver(answer_words=self.answer_words.copy(),
                                                     allowed_words=self.allowed_words.copy(),
                                                     guess_n=1,
                                                     game_answer=self.answer,
                                                     show_output=self.show_output)

    def __update_solver(self, use_solver: bool = False) -> None:
        if self.is_automated or use_solver:
            self.solver.__update_solver_info(answer_words=self.answer_words,
                                             allowed_words=self.allowed_words,
                                             guess_n=self.guess_n)

    def __save_solver_info(self, use_solver: bool = False) -> None:
        if self.is_automated or use_solver:
            self.solver.__write_dict_pickle()

    def play_and_drop_answer(self):
        """play a game of Wordle but remove the
           answer from the pool of possible answers for
           subsequent games"""
        self.__setup_solver()
        self.__game_in_session = True

        while not self.game_over:
            self.play_next_guess()

        self.__game_output(self.__get_game_outcome_output())
        self.__save_solver_info()
        self.excluded_answers.add(self.answer)

    def play_next_guess(self) -> None:
        """play the next row's guess"""
        if self.guess_n < Wordle.MAX_GUESS_N and self.current_guess != self.answer:
            self.guess_n += 1
            self.__update_solver()
            self.current_guess: str = self.solver.get_optimal_guess(
            ) if self.is_automated else self.__get_player_guess()
            self.__process_guess()
            if self.use_hints and self.current_guess != self.answer:
                sample_answers: list = random.sample(self.answer_words, 10) if len(
                    self.answer_words) >= 10 else list(self.answer_words)
                if len(sample_answers) > 1:
                    self.__game_output(f"hints: {', '.join(sample_answers)}")
                else:
                    self.__game_output(f"hint: {sample_answers[0]}")

        else:
            self.game_over = True

    def __game_output(self, output: str) -> None:
        """print various game outputs if output is enabled"""
        if self.show_output:
            print(output, flush=True)

    def __get_game_outcome_output(self) -> str:
        """get the string for the correct game outcome"""
        if not self.game_over:
            raise GameOver(self)

        if self.current_guess != self.answer:
            return Wordle.OUTRO_LOSS_OUTPUT + self.answer
        else:
            return Wordle.OUTRO_WIN_OUTPUT

    def __get_player_guess(self) -> str:
        """validate user input for a Wordle guess"""
        player_guess: str = ""
        valid_input: bool = True

        if self.game_over:
            raise GameOver(self)

        while player_guess not in self.allowed_words:
            if not valid_input:
                self.__game_output(Wordle.BAD_INPUT_OUTPUT)
            player_guess: str = input(f"{self.guess_n}: ")
            valid_input: bool = False

        return player_guess

    def __color_active_guess(self, colors: str) -> None:
        """color the output of a user's active external Wordle guess"""
        colored_output: str = ""

        for i in range(Wordle.WORDLE_LENGTH):
            if colors[i] == "g":
                colored_output += f"{Fore.GREEN}{self.current_guess[i]}{Fore.RESET}"
            elif colors[i] == "y":
                colored_output += f"{Fore.YELLOW}{self.current_guess[i]}{Fore.RESET}"
            elif colors[i] == "_":
                colored_output += f"{Back.WHITE}{Fore.BLACK}{self.current_guess[i]}{Style.RESET_ALL}"
            elif colors[i] == "/":
                colored_output += self.current_guess[i]
            else:
                raise ValueError(f"{colors[i]} isn't a valid symbol")

        print(f"{self.guess_n}: {colored_output}")

    def __process_guess(self) -> None:
        """color the output and update the puzzle's known information"""
        colored_output: str = ""

        # compare the letters between answer and guess at each index to determine a label
        for i in range(Wordle.WORDLE_LENGTH):
            if char_is_green(self.current_guess, i, self.answer):
                colored_output += f"{Fore.GREEN}{self.current_guess[i]}{Fore.RESET}"
                self.row_info["green_idx_letter"][i] = self.current_guess[i]
            elif char_is_yellow(self.current_guess, i, self.answer):
                colored_output += f"{Fore.YELLOW}{self.current_guess[i]}{Fore.RESET}"
                self.row_info["yellow_idx_letters"][i].append(
                    self.current_guess[i])
            elif char_is_grey(self.current_guess, i, self.answer):
                colored_output += f"{Back.WHITE}{Fore.BLACK}{self.current_guess[i]}{Style.RESET_ALL}"
                self.row_info["grey_letters"].add(self.current_guess[i])
            elif char_is_grey_at_idx(self.current_guess, i, self.answer):
                colored_output += f"{self.current_guess[i]}"
                self.row_info["grey_for_idx_letters"][i].append(
                    self.current_guess[i])
            else:
                raise UnclassifiedLetter(self, i)

        self.__game_output(f"{self.guess_n}: {colored_output}")
        self.__update_after_guess()

    def __update_after_guess(self) -> None:
        self.__update_word_sets()
        for key, _ in self.all_info.items():
            if key == "yellow_idx_letters" or key == "grey_for_idx_letters":
                for i in self.all_info[key]:
                    self.all_info[key][i] = self.all_info[key][i] + \
                        self.row_info[key][i]
            else:
                self.all_info[key].update(self.row_info[key])
        self.row_info: dict = deepcopy(Wordle.LETTER_COLOR_SCHEMA)

    def __update_word_sets(self) -> None:
        """update each set to reflect the most up to date information"""
        allowed_words_subset: set = set()
        answer_words_subset: set = set()

        # allowed words: drop all grey letters
        # - maintain a set of words that a user can use
        for allowed_word in self.allowed_words:
            for letter in allowed_word:
                if letter in self.row_info["grey_letters"]:
                    break
            else:
                allowed_words_subset.add(allowed_word)

        # answer words: drop all words that don't reflect known info
        # - maintain a set of words that could possibly be the answer
        for answer in self.answer_words:
            for i, letter in enumerate(answer):
                trimmed_answer: str = answer[:i] + answer[i +
                                                          1:] if Wordle.WORDLE_LENGTH > i else answer[:i]
                compatible_yellow: bool = True
                for yellow_letter in self.row_info["yellow_idx_letters"][i]:
                    if yellow_letter not in trimmed_answer:
                        compatible_yellow: bool = False
                grey_for_idx: bool = False
                for grey_idx_letter in self.row_info["grey_for_idx_letters"][i]:
                    if grey_idx_letter == answer[i]:
                        grey_for_idx: bool = True
                # omit words with grey letters
                if letter in self.row_info["grey_letters"]:
                    break
                # omit words without known green letters in the right spot
                elif self.row_info["green_idx_letter"][i] != "" and self.row_info["green_idx_letter"][i] != letter:
                    break
                # omit words with yellow letters that are absent
                elif not compatible_yellow:
                    break
                # omit words with a letter at an index that is elsewhere correctly in the word
                elif grey_for_idx:
                    break
            else:
                # word matches all above conditions
                answer_words_subset.add(answer)

        self.allowed_words: set = allowed_words_subset
        self.answer_words: set = answer_words_subset

        for length in [len(self.answer_words), len(self.allowed_words)]:
            assert length > 0, "Your wordle game doesn't match up with the available answers and/or words provided"
