import random


class Dice:
    """Represents the dice a player holds."""
    def __init__(self, num_dice: int):
        self.num_dice = num_dice
        self.values = []

    def roll(self):
        """Rolls all dice and updates their values."""
        self.values = [random.randint(1, 6) for _ in range(self.num_dice)]
        return self.values


class Bid:
    """Represents a bid in Wild Perudo."""
    def __init__(self, count: int, face: int):
        self.count = count
        self.face = face

    def __repr__(self):
        return f"{self.count} {self.face}s"

    def is_higher_than(self, other) -> bool:
        """Checks if this bid is higher than another bid."""
        # Convert counts for comparison (wild ones count double)
        self_effective = self.count * 2 if self.face == 1 else self.count
        other_effective = other.count * 2 if other.face == 1 else other.count

        # Higher count always wins
        if self_effective > other_effective:
            return True
        # If counts are equal, higher face wins
        if self_effective == other_effective:
            return self.face > other.face
        return False

    def is_valid_raise(self, current_bid) -> bool:
        """Checks if this is a valid raise from the current bid."""
        if self.count > current_bid.count:
            return True
        if self.count == current_bid.count and self.face > current_bid.face:
            return True
        return False


