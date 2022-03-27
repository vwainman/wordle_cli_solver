from wordle import *
from tqdm import tqdm


class SimulateGameStats:
    """Simulate Wordle games and collect statistics"""

    def __init__(self, wordle: Wordle) -> None:
        self.game: Wordle = wordle
        self.n_games: int = 0
        self.wins: int = 0
        self.losses: int = 0
        self.avg_n_guesses: int = 0
        self.total_n_guesses: int = 0
        self.guess_counts: dict = {
            i: 0 for i in range(1, self.game.MAX_GUESS_N + 1)}
        # where {"answer_word": [guess1, guess2, ..., final_guess]}
        self.game_guesses: dict = dict()
        self.answer_entropy_guesses: dict = None

    def simulate_all_games(self) -> None:
        """Simulate all possible wordle games"""
        n_games_possible = len(self.game.answer_words)
        for _ in tqdm(range(n_games_possible), total=n_games_possible):
            self.n_games += 1
            self.game.play_and_drop_answer()
            if self.game.guess == self.game.answer:
                self.wins += 1
            else:
                self.losses += 1
            self.total_n_guesses += self.game.guess_n
            self.avg_n_guesses = float(self.total_n_guesses)/self.n_games
            self.guess_counts[self.game.guess_n] += 1
            self.game.reset()
