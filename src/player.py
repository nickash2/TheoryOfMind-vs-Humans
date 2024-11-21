import random
from typing import List, Tuple
from .game import Dice, Bid

class Player:
    """Represents a player in the game. This is the base class for all players."""
    def __init__(self, name: str, num_dice: int):
        self.name = name
        self.dice = Dice(num_dice)
        self.current_bid = None

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
        estimated_count = unseen_dice / 6  # Expected number of matching faces in unseen dice

        # Count the agent's own dice that match the current bid face (including wild ones)
        total_count = self.dice.values.count(current_bid.face) + self.dice.values.count(1)  # Include wild ones

        # Total estimated count (including agent's dice and unseen dice estimation)
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
        
        # Predictive logic: Based on the opponent's dice, predict their behavior
        # In this case, we assume they are likely to increase the bid in a reasonable way.
        predicted_count = current_bid.count + 1  # We predict the opponent will at least increase the count.
        predicted_face = current_bid.face
        
        # Interpretative logic: Look at the opponent's dice to see if there's a higher likelihood of matching faces
        for player in self.players:
            if player.name != self.name:
                # Assume the opponent will bid based on their own dice
                if player.dice.values.count(current_bid.face) > 1:  # They likely have more dice of the same value
                    predicted_face = current_bid.face
                elif player.dice.values.count(1) > 0:  # They have wild dice, so they might bid more aggressively
                    predicted_face = min(current_bid.face + 1, 6)  # We expect them to raise the face value

        return Bid(predicted_count, predicted_face)

    def decide_challenge(self, current_bid: Bid, total_players: int) -> bool:
        """First-order agent decides to challenge based on predictions of the opponent's behavior."""
        # Estimate the total number of dice that would match the current bid based on the opponent's dice
        total_dice_count = 0
        for player in self.players:
            if player.name != self.name:
                total_dice_count += player.dice.values.count(current_bid.face)
                total_dice_count += player.dice.values.count(1)  # Include wild dice

        # First-order player will challenge if they believe the opponent's bid is unlikely to be accurate
        if total_dice_count < current_bid.count:
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
            choice = input("Do you want to challenge the bid? (yes/no): ").strip().lower()
            if choice in ['yes', 'y']:
                return True
            if choice in ['no', 'n']:
                return False
            print("Invalid input. Please enter 'yes' or 'no'.")