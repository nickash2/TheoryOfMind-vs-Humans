from typing import List
from .player import Player, HumanPlayer, FirstOrderPlayer
from typing import Tuple


class WildPerudoGame:
    """Main game logic for Wild Perudo."""

    def __init__(self, players: List[Player], callback=None, **kwargs):
        self.players = players
        self.current_bid = None
        self.current_player_idx = 0
        self.scores = {player.name: 0 for player in players}
        self.callback = callback

        # Share the list of players with each player
        for player in players:
            player.set_players(self.players)

    def print_scores(self):
        """Prints the current scores."""
        print("\nCurrent Scores:")
        for player_name, score in self.scores.items():
            print(f"{player_name}: {score}")

    def play_turn(self):
        """Plays a single turn of the game."""
        player = self.players[self.current_player_idx]
        print(f"\n{player.name}'s turn.")

        # Show the current player's dice, hide the other player's dice
        if isinstance(player, HumanPlayer):
            print(f"Your dice: {player.dice.values}")
        else:
            print(f"Agent's dice: {player.dice.values}")

        if self.current_bid:
            print(f"Current bid: {self.current_bid}")

            if player.decide_challenge(self.current_bid, len(self.players)):
                print(f"{player.name} challenges the bid!")
                if self.resolve_challenge(player):
                    return  # End the round after resolving the challenge

        # Otherwise, make a new bid
        new_bid = player.make_bid(self.current_bid)
        if self.current_bid and not new_bid.is_valid_raise(self.current_bid):
            print(f"{player.name} made an invalid bid. They lose the game!")

            # Eliminate the player from the game
            self.players.pop(self.current_player_idx)

            # Check if there is only one player left, the game ends immediately
            if len(self.players) == 1:
                print(f"{self.players[0].name} is the last remaining player!")
                print(f"{self.players[0].name} wins the game!")
                self.print_scores()
                exit()

            # Print the current scores
            self.print_scores()

            # Adjust the player index to account for the removed player
            self.current_player_idx %= len(self.players)
            return
        else:
            print(f"{player.name} bids: {new_bid}")
            self.current_bid = new_bid

        # Move to the next player for the next turn
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

    def resolve_challenge(self, challenger: Player):
        """Resolves a challenge."""
        print("Revealing dice...")
        total_dice = []
        for player in self.players:
            total_dice.extend(player.dice.values)
            print(f"{player.name}: {player.dice.values}")

        # Count wild dice and bid face dice, ensuring no double counting
        wild_dice = total_dice.count(1)
        bid_face_dice = total_dice.count(self.current_bid.face)
        if (
            self.current_bid.face == 1
        ):  # Wild dice shouldn't double count if bid face is 1
            effective_count = bid_face_dice
        else:
            effective_count = bid_face_dice + wild_dice

        bidder = self.get_current_bidder()

        # Evaluate the challenge
        if effective_count >= self.current_bid.count:
            print(f"The bid was correct! The bidder ({bidder.name}) wins this round!")
            self.scores[bidder.name] += 1
        else:
            print(
                f"The bid was incorrect! The challenger ({challenger.name}) wins this round!"
            )
            self.scores[challenger.name] += 1

        # Reset the bid and indicate the round is over
        self.current_bid = None
        return True

    def get_current_bidder(self) -> Player:
        """Returns the player who made the current bid."""
        return self.players[(self.current_player_idx - 1) % len(self.players)]

    def start_game(self, max_rounds: int = 10) -> Tuple[Player, Player]:
        """Starts the game loop."""
        round_count = 0
        while round_count < max_rounds:
            print(f"\n--- Round {round_count + 1} ---")

            # Re-roll dice at the start of each round, not after each turn
            for player in self.players:
                player.roll_dice()

            # Keep playing turns for this round until there's a winner
            round_winner_found = False
            while not round_winner_found:
                for player in self.players:
                    self.play_turn()
                    if self.current_bid is None:  # Round ends if the bid is resolved
                        round_winner_found = True
                        break  # Exit the loop once a winner is found for this round

            # After a round is completed, move to the next round
            round_count += 1

        # Game over, calculate final results
        print("\nGame Over! Final Scores:")
        for player_name, score in self.scores.items():
            print(f"{player_name}: {score}")

        # Determine the winner based on scores
        if len(self.players) > 1:
            winner = max(self.scores, key=self.scores.get)
            loser = min(self.scores, key=self.scores.get)
            if self.scores[winner] == 0:
                print("No winner! It's a tie!")
            else:
                print(f"The winner is {winner} with {self.scores[winner]} points!")
        else:
            # If only one player remains, they are the winner
            winner = self.players[0].name
            print(f"The winner is {winner}!")

        return (winner, loser if len(self.players) > 1 else None)
