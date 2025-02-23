from typing import List
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from src.player import (
    Player,
    ImprovedFirstOrderPlayer,
    ZeroOrderPlayer,
    HumanPlayer,
)
from src.wildperudo import WildPerudoGame


def main():
    print("Welcome to Wild Perudo!")

    # Configuration
    N_RUNS = 1  # Number of game iterations
    PLAYER_CONFIG = [
        ("Human 1", HumanPlayer),
        ("ToM1", ImprovedFirstOrderPlayer),
    ]

    # Initialize data collection
    results = {name: [] for name, _ in PLAYER_CONFIG}

    # Run multiple games
    for _ in range(N_RUNS):
        # Create fresh players for each game
        players = [cls(name=name, num_dice=5) for name, cls in PLAYER_CONFIG]

        game = WildPerudoGame(players)
        game.start_game(max_rounds=5)

        # Collect results
        for name in results.keys():
            results[name].append(game.scores[name])

    # Convert to DataFrame for analysis
    df = pd.DataFrame(results)

    # Calculate statistics using numpy
    stats = pd.DataFrame(
        {
            "Mean": df.mean(),
            "Std": df.std(),
            "Median": df.median(),
            "Min": df.min(),
            "Max": df.max(),
        }
    )

    # Save and display results
    df.to_csv("data/aggregated_results.csv", index=False)
    stats.to_csv("data/game_statistics.csv")

    print("\nGame Statistics:")
    print(stats)


if __name__ == "__main__":
    main()
