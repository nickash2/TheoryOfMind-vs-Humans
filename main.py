from typing import List
from src.player import Player, HumanPlayer, ZeroOrderPlayer
from src.wildperudo import WildPerudoGame


def main():
    print("Welcome to Wild Perudo!")

    players: List[Player] = [
        HumanPlayer(name="You", num_dice=5),
        ZeroOrderPlayer(name="ZeroOrderPlayer", num_dice=5),
    ]

    game = WildPerudoGame(players)

    game.start_game(max_rounds=10)

if __name__ == "__main__":
    main()
