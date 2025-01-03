from typing import List
from src.player import Player, HumanPlayer, ZeroOrderPlayer, FirstOrderPlayer
from src.wildperudo import WildPerudoGame
from data.data_collector import DataCollector


def main():
    print("Welcome to Wild Perudo!")

    players: List[Player] = [
        ZeroOrderPlayer(name="ToM1", num_dice=5),
        ZeroOrderPlayer(name="ToM0", num_dice=5),
    ]

    game = WildPerudoGame(players)

    winner, loser = game.start_game(max_rounds=10000)

    data = DataCollector(game.scores.items())
    data.save_game_csv("data/results.csv")
    data.plot_game(plot_type="bar")


if __name__ == "__main__":
    main()
