import random
from typing import List, Tuple
from .game import Dice, Bid


class Player:
    """Represents a player in the game. This is the base class for all players."""

    def __init__(self, name: str, num_dice: int):
        self.name = name
        self.num_dice = num_dice
        self.dice = Dice(num_dice)
        self.current_bid = None
        self.players = []

    def set_players(self, players: List["Player"]):
        """Sets the list of players in the game."""
        self.players = players

    def roll_dice(self):
        """Rolls the dice for this player."""
        return self.dice.roll()

    def make_bid(self, current_bid: Bid) -> Bid:
        """Makes a bid for the current round."""
        if current_bid is None:
            # First bid: Start with a low bid
            return Bid(1, random.randint(2, 6))

        # Increase the bid count or raise the face value
        count = current_bid.count + 1
        face = current_bid.face
        if random.random() > 0.5:  # 50% chance to increase face value
            face = min(current_bid.face + 1, 6)

        return Bid(count, face)

    def decide_challenge(self, current_bid: Bid, total_players: int) -> bool:
        """Decides whether to challenge the bid. To be implemented by subclasses."""
        raise NotImplementedError("This method should be implemented by subclasses.")


class ZeroOrderPlayer(Player):
    def __init__(self, name: str, num_dice: int):
        super().__init__(name, num_dice)

    def make_bid(self, current_bid: Bid) -> Bid:
        """Makes a bid based on the zero-order ToM logic."""
        if current_bid is None:
            return Bid(1, random.randint(2, 6))

        # Zero-order strategy: Increase the bid count, or increment the face value randomly
        count = current_bid.count + 1
        face = current_bid.face
        if random.random() > 0.5:  # 50% chance to increase face value
            face = min(current_bid.face + 1, 6)

        return Bid(count, face)

    def decide_challenge(self, current_bid: Bid, total_players: int) -> bool:
        """Zero-order agent challenges based on statistical likelihood."""
        # Calculate the number of dice that are unseen to this player
        unseen_dice = total_players * self.dice.num_dice - len(self.dice.values)

        # Estimate how many of the unseen dice are likely to be the same as the current bid face
        # Assuming fair dice rolls, the likelihood of seeing a specific face is roughly 1/6.
        estimated_count = (
            unseen_dice / 6
        )  # Expected number of matching faces in unseen dice

        # Count the agent's own dice that match the current bid face (including wild ones)
        total_count = self.dice.values.count(current_bid.face) + self.dice.values.count(
            1
        )  # Include wild ones

        total_count += estimated_count

        # If the total count (including estimates for unseen dice) is less than the bid count, challenge
        return total_count < current_bid.count


class FirstOrderPlayer(Player):
    def __init__(self, name: str, num_dice: int):
        super().__init__(name, num_dice)

    def set_players(self, players: List["Player"]):
        """Sets the list of players in the game."""
        self.players = players

    def make_bid(self, current_bid: Bid) -> Bid:
        """Makes a bid based on first-order ToM logic."""
        if current_bid is None:
            return Bid(1, random.randint(2, 6))  # Start with a random low bid

        total_dice = sum(player.num_dice for player in self.players)
        predicted_count = current_bid.count + 1
        predicted_face = current_bid.face

        # Calculate the probability of the current bid being accurate
        face_probability = (1 / 6) * total_dice
        wild_probability = (1 / 6) * total_dice
        total_probability = face_probability + wild_probability

        # Interpret the opponent's bid based on the bid count (interpretive ToM)
        # If the opponent made a high bid, we infer they might have many matching dice
        interpretation_factor = self.interpret_opponent_bid(current_bid)

        # Combine predictive and interpretive logic
        if total_probability + interpretation_factor < current_bid.count:
            predicted_count = current_bid.count + 1
            predicted_face = current_bid.face
        else:
            predicted_face = min(current_bid.face + 1, 6)

        return Bid(predicted_count, predicted_face)

    def interpret_opponent_bid(self, current_bid: Bid) -> int:
        """Interpret the opponent's current bid. High counts suggest many matching dice or bluffing."""
        if (
            current_bid.count >= 6
        ):  # If the opponent bid is high, they might have matching dice
            return 2  # A small bonus to interpret a stronger hand (may assume they have matching dice)
        elif current_bid.count <= 2:  # Low count might indicate they don't have much
            return -1  # Penalty to interpret a weak hand
        else:
            return 0  # Neutral interpretation

    def decide_challenge(self, current_bid: Bid, total_players: int) -> bool:
        """First-order agent decides to challenge based on predictions and interpretation of opponent's behavior."""
        total_dice_count = 0
        for player in self.players:
            if player.name != self.name:
                total_dice_count += player.dice.values.count(current_bid.face)
                total_dice_count += player.dice.values.count(1)  # Include wild dice

        total_dice = sum(player.num_dice for player in self.players)
        face_probability = (1 / 6) * total_dice
        wild_probability = (1 / 6) * total_dice
        total_probability = face_probability + wild_probability

        # Add interpretive factor to account for the opponent's likely hand
        interpretation_factor = self.interpret_opponent_bid(current_bid)
        total_probability += interpretation_factor

        # Challenge if total predicted dice (with interpretation) are less than the bid
        if total_probability < current_bid.count:
            return True  # Challenge if the prediction is not sufficient

        return False  # Otherwise, don't challenge


class HumanPlayer(Player):
    """Represents a human player in the game."""

    def make_bid(self, current_bid: Bid) -> Bid:
        """Prompts the human player to make a bid."""
        print(f"Current bid: {current_bid}" if current_bid else "No current bid.")
        while True:
            try:
                count = int(input("Enter the count of dice for your bid: "))
                face = int(input("Enter the face value of dice for your bid (1-6): "))
                new_bid = Bid(count, face)
                if current_bid is None or new_bid.is_valid_raise(current_bid):
                    return new_bid
                print("Invalid bid. You must raise the bid.")
            except ValueError:
                print("Invalid input. Please enter numbers only.")

    def decide_challenge(self, current_bid: Bid, total_players: int) -> bool:
        """Asks the human player whether they want to challenge."""
        print(f"Current bid: {current_bid}")
        while True:
            choice = (
                input("Do you want to challenge the bid? (yes/no): ").strip().lower()
            )
            if choice in ["yes", "y"]:
                return True
            if choice in ["no", "n"]:
                return False
            print("Invalid input. Please enter 'yes' or 'no'.")
