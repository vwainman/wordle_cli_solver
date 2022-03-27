from collections import OrderedDict
from copy import deepcopy
from itertools import product
from miscellaneous import *
from operator import countOf
from os import path
from pathvalidate import ValidationError, validate_filename, sanitize_filename
import pickle
from scipy.stats import entropy
import sys
from tqdm import tqdm

class WordleSolver:
    """Solve a wordle puzzle by utilizing information theory"""
    WORD_LENGTH: int = 5
    OPTIMAL_FIRST_GUESS: str = "salet"

    def __init__(self, 
                 answer_words: set, 
                 allowed_words: set, 
                 guess_n: int,
                 game_answer: str,
                 show_output: bool,
                 pickle_file_name: str = "answer_optimal_guesses") -> None:
        self.answer_words: list = answer_words
        self.allowed_words: list = allowed_words
        self.words_scores: OrderedDict = OrderedDict()
        self.guess_n: int = guess_n
        self.show_output: bool = show_output
        self.answer: str = game_answer
        self.pickle_file_path: str = self.__validate_file_name(pickle_file_name) + ".pickle"
        self.answer_entropy_guesses: dict = self.__read_dict_pickle()
        
    def __validate_file_name(self, file_name) -> str:
        try:
            validate_filename(file_name)
            fname: str = file_name
        except ValidationError as e:
            print(f"{e}\n", file=sys.stderr)
            print(f"Sanitizing filename...")
            fname: str = sanitize_filename(fname) 
        return fname
        
    def __read_dict_pickle(self) -> dict():
        if path.isfile(self.pickle_file_path):
            with open(self.pickle_file_path, "rb") as f:
                try:
                    return pickle.load(f)
                except Exception as e: 
                    print(f"{self.pickle_file_path} failed to load due to {e}")
        return dict() 
    
    def __save_optimal_guess(self, optimal_guess: str) -> None:
        """If the game answer is known, we can save the results of the entropy optimal guess for future solves"""
        if self.answer is not None: # answer is known, we can save the optimal inputs of that game 
            if self.answer not in self.answer_entropy_guesses:
                self.answer_entropy_guesses[self.answer] = [optimal_guess]
            elif optimal_guess not in self.answer_entropy_guesses[self.answer]:
                self.answer_entropy_guesses[self.answer].append(optimal_guess)
            
    def _Wordle__update_solver_info(self, answer_words: set, allowed_words: set, guess_n: int) -> None:
        self.answer_words: set = answer_words
        self.allowed_words: set = allowed_words
        self.guess_n: int = guess_n
        
    def _Wordle__write_dict_pickle(self) -> None:
        with open(self.pickle_file_path, "wb") as f:
            try:
                pickle.dump(self.answer_entropy_guesses, f)
            except Exception as e:
                print(f"Pickle dump unsuccessful due to {e}")
    
    def get_top_n_word_scores(self, n: int) -> OrderedDict:
        """Retrieve the nth highest score words, if possible
        
        Keyword arguments:
        - n: an unsigned integer value
        """
        all_scores: OrderedDict = deepcopy(self.words_scores)
        n: int = len(all_scores) if len(all_scores) < n else n
        n_scores: OrderedDict = OrderedDict()
        for _ in range(n):
            key: str = max(all_scores, key=all_scores.get)
            n_scores[key] = all_scores[key]
            del all_scores[key]
        return n_scores
    
    def get_optimal_guess(self, game_mode:str = "answer_known") -> str:
        """produce an optimal word based on probability and expected information"""
        assert game_mode in ["answer_known", "answer_unknown"]
        assert self.guess_n > 0
        
        if self.guess_n == 1:
            top_scoring_word: str = WordleSolver.OPTIMAL_FIRST_GUESS  
        elif game_mode == "answer_known":
            if self.answer in self.answer_entropy_guesses and len(self.answer_entropy_guesses[self.answer]) >= self.guess_n:
                entropy_guesses: list = self.answer_entropy_guesses[self.answer]
                top_scoring_word: str = entropy_guesses[self.guess_n - 1]
            # if there's only one answer left, avoid any calculations
            elif len(self.answer_words) == 1:
                top_scoring_word: str = self.answer_words.pop()
            # otherwise, use one step entropy to find the optimal next guess
            else:
                self.words_scores: OrderedDict = self.__assign_scores_to_possible_guesses()
                top_scores: OrderedDict = self.get_top_n_word_scores(10) if len(self.words_scores) > 10 else self.get_top_n_word_scores(len(self.words_scores))
                if self.show_output:
                    for word, score in top_scores.items():
                        print(f"{word}: {score}")
                top_scoring_word: str = max(top_scores, key=top_scores.get) 
                top_score: float = top_scores[top_scoring_word]

                # try to use a word that's in answer_words if there are multiple words with the same top score
                if countOf(top_scores.values(), top_score) > 1:
                    for word, score in self.words_scores.items():
                        if score == top_score and word in self.answer_words:
                            top_scoring_word: str = word
            # save the optimal parameters of this game if answer is known
            self.__save_optimal_guess(top_scoring_word)
        else:
            self.words_scores: OrderedDict = self.__assign_scores_to_possible_guesses()
            top_scores: OrderedDict = self.get_top_n_word_scores(10) if len(self.words_scores) > 10 else self.get_top_n_word_scores(len(self.words_scores))
            top_scoring_word: str = max(top_scores, key=top_scores.get) 
            top_score: float = top_scores[top_scoring_word]

            # try to use a word that's in answer_words if there are multiple words with the same top score
            if countOf(top_scores.values(), top_score) > 1:
                for word, score in self.words_scores.items():
                    if score == top_score and word in self.answer_words:
                        top_scoring_word: str = word 
        
        return top_scoring_word

    def __assign_scores_to_possible_guesses(self) -> OrderedDict:
        """assign an individual score to each word based on single step entropy"""
        word_scores: OrderedDict = OrderedDict()

        pbar = tqdm(self.allowed_words, disable = not self.show_output)
        for guess in pbar:
            guess_score: float = self.__entropy_score(guess)
            word_scores[guess] = guess_score
            
        return word_scores

    def __entropy_score(self, guess: str) -> float:
        """assign a score to the guess based on 1 step entropy
        NOTE: E[info] = sum(probability(pattern_i) * log2(1/probability(pattern_i)) over all patterns
        Keyword arguments:
        - guess: a valid Wordle word (lowercase ascii string five chars long)
        """
        
        pattern_match_counts: list = []

        for wordle_pattern in product([char_is_green,
                                       char_is_yellow_safe,
                                       char_is_grey],
                                      repeat = WordleSolver.WORD_LENGTH):
            pattern_match_count: int = 0
            for possible_answer in self.answer_words:
                if all([wordle_pattern[letter_i](guess, letter_i, possible_answer) for letter_i in range(WordleSolver.WORD_LENGTH)]):
                    pattern_match_count += 1
            pattern_match_counts.append(pattern_match_count)
        probabilities: list = [float(specific_count)/len(self.answer_words) for specific_count in pattern_match_counts]
        
        return entropy(probabilities, base=2)