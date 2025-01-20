import random
from typing import List, Tuple
from .game import Dice, Bid
from scipy.stats import binom


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
        """Make a more strategic opening or raising bid considering wild dice."""
        known_dice = self.dice.values
        wild_count = known_dice.count(1)  # Wild dice are face value '1'

        # Count dice for each face, including wild dice as any face
        face_counts = {
            i: known_dice.count(i) + wild_count for i in range(2, 7)
        }  # For faces 2-6
        face_counts[1] = wild_count  # Wild dice can be used for any face

        # If no current bid, make an opening bid based on the most common face
        if not current_bid:
            # Choose the most common face including wild dice
            most_common_face = max(face_counts, key=face_counts.get)
            bid_count = face_counts[most_common_face]
            bid_count = max(1, bid_count)  # Ensure minimum count of 1
            return Bid(count=bid_count, face=most_common_face)

        # Otherwise, raise the bid strategically
        min_raise = current_bid.count + 1
        # If a bid count exceeds the total number of dice in the game, it should be capped
        max_possible_dice = sum(
            player.num_dice for player in self.players
        )  # Total dice in the game
        if min_raise > max_possible_dice:
            min_raise = max_possible_dice  # Prevent the count from exceeding the number of dice in the game

        for face, count in face_counts.items():
            # Consider raising to a face with more known dice or wild dice
            if count > min_raise or (count == min_raise and face >= current_bid.face):
                return Bid(count=min_raise, face=face)

        # If no better option, just raise the count on the current face
        return Bid(count=min_raise, face=current_bid.face)

    def decide_challenge(self, current_bid: Bid, total_players: int) -> bool:
        """Decide whether to challenge the current bid considering wild dice."""
        if not current_bid:
            return False  # Cannot challenge if there's no bid

        # Get the total number of dice in the game
        total_dice = sum(player.num_dice for player in self.players)

        # The number of dice you already know for the current bid's face
        known_dice = self.dice.values
        wild_count = known_dice.count(1)  # Wild dice are face value '1'
        estimated_known_matches = known_dice.count(current_bid.face) + wild_count

        # The remaining dice from all players that are not yours
        remaining_dice = total_dice - len(known_dice)

        # Probability of a die showing the value of current_bid.face
        prob_match = (
            1 / 3
        )  # Wild Perudo variant: Wild dice are 1/3 chance of matching the bid face

        # Total estimated matches (including wild dice)
        estimated_matches = estimated_known_matches + remaining_dice * prob_match

        # Calculate the probability of fewer than current_bid.count dice matching the bid
        # We will use the binomial distribution to calculate this probability
        challenge_prob = binom.cdf(current_bid.count - 1, remaining_dice, prob_match)

        # Challenge if the bid is unlikely (probability is low)
        if (
            challenge_prob < 0.5
        ):  # If the probability of matching the bid is less than 50%, challenge
            return True

        return False


class FirstOrderPlayer(Player):
    def __init__(self, name: str, num_dice: int):
        super().__init__(name, num_dice)
        self.opponent_models = {}  # Store mental models of opponents

    def set_players(self, players: List["Player"]):
        self.players = players
        for player in players:
            if player.name != self.name:
                # Initialize mental model for each opponent
                self.opponent_models[player.name] = {
                    "risk_tolerance": 0.5,  # How likely they are to make risky bids
                    "bluff_tendency": 0.5,  # How often they bluff
                    "challenge_threshold": 0.6,  # When they tend to challenge
                    "believed_dice": [],  # What we think they might have
                }

    def update_opponent_model(self, opponent_name: str, bid: Bid, was_bluff: bool):
        """Update our mental model of an opponent based on their actions"""
        model = self.opponent_models[opponent_name]

        # Update bluff tendency
        if was_bluff:
            model["bluff_tendency"] = (model["bluff_tendency"] * 0.9) + 0.1
        else:
            model["bluff_tendency"] = model["bluff_tendency"] * 0.9

        # Update risk tolerance based on bid aggressiveness
        total_dice = sum(player.num_dice for player in self.players)
        bid_risk = bid.count / total_dice
        if bid_risk > 0.5:
            model["risk_tolerance"] = (model["risk_tolerance"] * 0.9) + 0.1
        else:
            model["risk_tolerance"] = model["risk_tolerance"] * 0.9

    def simulate_opponent_thinking(self, opponent_name: str, current_bid: Bid) -> float:
        """Simulate what the opponent might be thinking about the current game state"""
        model = self.opponent_models[opponent_name]

        # Simulate opponent's perspective of total probable dice
        total_dice = sum(player.num_dice for player in self.players)
        expected_dice = (total_dice / 6) + (total_dice / 6)  # Face + Wilds

        # Factor in opponent's risk tolerance and bluff tendency
        if current_bid.count > expected_dice:
            belief_strength = (
                (1 - model["risk_tolerance"])
                * 0.7  # Lower risk tolerance = more skeptical
                + (1 - model["bluff_tendency"])
                * 0.3  # Higher bluff tendency = more skeptical
            )
        else:
            belief_strength = 0.8  # More likely to believe reasonable bids

        return belief_strength

    def make_bid(self, current_bid: Bid) -> Bid:
        """Make a bid using first-order ToM reasoning"""
        known_dice = self.dice.values
        wild_count = known_dice.count(1)

        # Handle initial bid
        if not current_bid:
            # Count dice for each face, including wild dice as any face
            face_counts = {i: known_dice.count(i) + wild_count for i in range(2, 7)}
            face_counts[1] = wild_count  # Wild dice can be used for any face

            # Choose the most common face including wild dice
            most_common_face = max(face_counts, key=face_counts.get)
            bid_count = face_counts[most_common_face]
            bid_count = max(1, bid_count)  # Ensure minimum count of 1
            return Bid(count=bid_count, face=most_common_face)

        # Get the last bidder
        last_bidder = [p for p in self.players if p.name != self.name][
            0
        ]  # Simplified for 2 players

        # Simulate what opponent might be thinking
        opponent_belief = self.simulate_opponent_thinking(last_bidder.name, current_bid)

        # If we think opponent is skeptical, make a more conservative bid
        if opponent_belief < 0.4:
            return Bid(count=current_bid.count, face=current_bid.face)
        # If we think opponent believes current bid, we can be more aggressive
        else:
            return Bid(count=current_bid.count + 1, face=current_bid.face)

    def decide_challenge(self, current_bid: Bid, total_players: int) -> bool:
        """Decide whether to challenge using first-order ToM"""
        last_bidder = [p for p in self.players if p.name != self.name][
            0
        ]  # Simplified for 2 players
        model = self.opponent_models[last_bidder.name]

        # Consider what we know about the opponent
        if model["bluff_tendency"] > 0.7:
            # We think they bluff often
            challenge_threshold = 0.5
        elif model["risk_tolerance"] > 0.7:
            # We think they make risky bids
            challenge_threshold = 0.6
        else:
            challenge_threshold = 0.7

        # Calculate probability considering opponent's model
        total_dice = sum(player.num_dice for player in self.players)
        expected_dice = (total_dice / 6) + (total_dice / 6)  # Face + Wilds

        if current_bid.count > expected_dice * challenge_threshold:
            return True
        return False


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


class FirstOrderPlayer2(Player):
    def __init__(self, name: str, num_dice: int):
        super().__init__(name, num_dice)
        self.opponent_models = {}
        self.bid_history = []  # Track bid history for pattern recognition

    def set_players(self, players: List["Player"]):
        super().set_players(players)
        for player in players:
            if player.name != self.name:
                self.opponent_models[player.name] = {
                    "risk_profile": 0.5,  # Risk-taking tendency
                    "bluff_frequency": 0.5,  # Frequency of bluffing
                    "aggression_level": 0.5,  # Bidding aggression
                    "challenge_threshold": 0.6,  # When they typically challenge
                    "last_known_dice": None,
                    "bid_patterns": [],  # Track bidding patterns
                    "believed_strategy": "unknown",  # Inferred strategy
                }

    def interpret_opponent_action(self, opponent_name: str, action: dict):
        """Interpretative ToM: Understand why opponent made their move"""
        model = self.opponent_models[opponent_name]

        if action["type"] == "bid":
            bid = action["bid"]
            previous_bid = action["previous_bid"]

            # Analyze bid aggressiveness
            if previous_bid:
                bid_jump = bid.count - previous_bid.count
                if bid_jump > 2:
                    model["aggression_level"] = min(
                        1.0, model["aggression_level"] + 0.1
                    )
                    model["risk_profile"] = min(1.0, model["risk_profile"] + 0.05)

            # Analyze face value selection
            total_dice = sum(p.num_dice for p in self.players)
            expected_count = total_dice / 3  # Approximate probability

            if bid.count > expected_count * 1.5:
                model["bluff_frequency"] = min(1.0, model["bluff_frequency"] + 0.1)

        elif action["type"] == "challenge":
            # Update challenge behavior model
            success = action["success"]
            if success:
                model["challenge_threshold"] = max(
                    0.3, model["challenge_threshold"] - 0.05
                )
            else:
                model["challenge_threshold"] = min(
                    0.9, model["challenge_threshold"] + 0.05
                )

    def predict_opponent_action(self, opponent_name: str, current_bid: Bid) -> dict:
        """Predictive ToM: Predict opponent's next likely action"""
        model = self.opponent_models[opponent_name]
        total_dice = sum(p.num_dice for p in self.players)

        # Predict likelihood of challenge
        challenge_likelihood = 0.0
        if current_bid:
            expected_dice = (total_dice / 6) + (total_dice / 6)  # Face + Wilds
            if current_bid.count > expected_dice * model["challenge_threshold"]:
                challenge_likelihood = 0.7 * model["risk_profile"]

        # Predict next bid if they don't challenge
        predicted_bid = None
        if current_bid:
            if model["aggression_level"] > 0.7:
                predicted_bid = Bid(current_bid.count + 2, current_bid.face)
            else:
                predicted_bid = Bid(current_bid.count + 1, current_bid.face)

        return {
            "challenge_likelihood": challenge_likelihood,
            "predicted_bid": predicted_bid,
            "believed_strategy": model["believed_strategy"],
        }

    def make_bid(self, current_bid: Bid) -> Bid:
        """Make bid using first-order ToM reasoning"""
        if not current_bid:
            return self._make_initial_bid()

        # Get opponent and interpret their last action if it was a bid
        opponent = [p for p in self.players if p.name != self.name][0]

        # Interpret the opponent's last bid
        self.interpret_opponent_action(
            opponent.name,
            {
                "type": "bid",
                "bid": current_bid,
                "previous_bid": self.bid_history[-1] if self.bid_history else None,
            },
        )

        # Add current bid to history
        self.bid_history.append(current_bid)

        # Get prediction after interpretation
        prediction = self.predict_opponent_action(opponent.name, current_bid)

        # Strategic bid based on prediction and interpretation
        if prediction["challenge_likelihood"] > 0.6:
            return self._make_conservative_bid(current_bid)
        else:
            return self._make_aggressive_bid(current_bid)

    def decide_challenge(self, current_bid: Bid, total_players: int) -> bool:
        """Decide challenge using first-order ToM"""
        opponent = [p for p in self.players if p.name != self.name][0]

        # Interpret the opponent's last bid before deciding to challenge
        self.interpret_opponent_action(
            opponent.name,
            {
                "type": "bid",
                "bid": current_bid,
                "previous_bid": self.bid_history[-1] if self.bid_history else None,
            },
        )

        model = self.opponent_models[opponent.name]

        # Calculate probability considering opponent model
        total_dice = sum(p.num_dice for p in self.players)
        expected_dice = (total_dice / 6) + (total_dice / 6)

        # Adjust threshold based on interpreted model
        threshold = 1.3
        if model["bluff_frequency"] > 0.7:
            threshold *= 0.8
        if model["risk_profile"] > 0.7:
            threshold *= 0.9

        return current_bid.count > expected_dice * threshold

    def _make_initial_bid(self) -> Bid:
        """Helper method for making initial bid"""
        known_dice = self.dice.values
        wild_count = known_dice.count(1)
        face_counts = {i: known_dice.count(i) + wild_count for i in range(2, 7)}
        face_counts[1] = wild_count
        most_common_face = max(face_counts, key=face_counts.get)
        return Bid(count=max(1, face_counts[most_common_face]), face=most_common_face)

    def _make_conservative_bid(self, current_bid: Bid) -> Bid:
        """Make a conservative bid based on known dice"""
        return Bid(current_bid.count + 1, current_bid.face)

    def _make_aggressive_bid(self, current_bid: Bid) -> Bid:
        """Make an aggressive bid based on opponent model"""
        return Bid(current_bid.count + 2, current_bid.face)


class ImprovedFirstOrderPlayer(Player):
    def __init__(self, name: str, num_dice: int):
        super().__init__(name, num_dice)
        self.opponent_models = {}
        self.bid_history = []  # Track all bids in the game
        self.round_history = []  # Track outcomes of previous rounds

    def set_players(self, players: List["Player"]):
        super().set_players(players)
        for player in players:
            if player.name != self.name:
                # Initialize different possible models for the opponent
                self.opponent_models[player.name] = {
                    "models": {
                        "conservative": {
                            "weight": 0.33,
                            "params": {"risk": 0.3, "bluff": 0.2},
                        },
                        "aggressive": {
                            "weight": 0.33,
                            "params": {"risk": 0.7, "bluff": 0.6},
                        },
                        "balanced": {
                            "weight": 0.34,
                            "params": {"risk": 0.5, "bluff": 0.4},
                        },
                    },
                    "last_action": None,
                    "bid_patterns": [],
                }

    def interpretative_tom(self, opponent_name: str, current_bid: Bid) -> None:
        """Interpretative ToM: Understanding why the opponent acted as observed"""
        models = self.opponent_models[opponent_name]["models"]

        # Current game context
        total_dice = sum(p.num_dice for p in self.players)
        my_dice = self.dice.values
        expected_dice = total_dice / 6

        # Analyze the bid in context
        if self.bid_history:
            bid_jump = current_bid.count - self.bid_history[-1].count
            face_change = current_bid.face != self.bid_history[-1].face
        else:
            bid_jump = current_bid.count
            face_change = False

        # Update model weights based on observed action
        for model_name, model in models.items():
            likelihood = 1.0

            if model_name == "conservative":
                # Conservative players make smaller jumps and stay with same face
                likelihood *= 1.2 if bid_jump <= 1 else 0.8
                likelihood *= 1.2 if not face_change else 0.8

            elif model_name == "aggressive":
                # Aggressive players make larger jumps and change faces
                likelihood *= 1.2 if bid_jump >= 2 else 0.8
                likelihood *= 1.2 if face_change else 0.8

            # Update weight
            model["weight"] *= likelihood

        # Normalize weights
        total_weight = sum(model["weight"] for model in models.values())
        for model in models.values():
            model["weight"] /= total_weight

    def predictive_tom(self, opponent_name: str, current_bid: Bid) -> dict:
        """Predictive ToM: What will the opponent do next?"""
        models = self.opponent_models[opponent_name]["models"]

        # Get the most likely model
        best_model = max(models.items(), key=lambda x: x[1]["weight"])
        model_params = best_model[1]["params"]

        # Current game context
        total_dice = sum(p.num_dice for p in self.players)
        my_dice = self.dice.values
        expected_dice = total_dice / 6

        # Predict challenge probability
        challenge_prob = 0.0
        if current_bid:
            if current_bid.count > expected_dice * (2.0 - model_params["risk"]):
                challenge_prob = 0.7
            if len(self.bid_history) > 3:  # If game has gone on for a while
                challenge_prob += 0.1

        # Predict next bid based on model
        likely_bid = None
        if current_bid:
            if model_params["risk"] > 0.6:  # Aggressive model
                likely_bid = Bid(current_bid.count + 2, current_bid.face)
            else:  # Conservative model
                likely_bid = Bid(current_bid.count + 1, current_bid.face)

        return {
            "challenge_probability": challenge_prob,
            "likely_bid": likely_bid,
            "model_confidence": best_model[1]["weight"],
        }

    def make_bid(self, current_bid: Bid) -> Bid:
        """Make bid using first-order ToM reasoning"""
        if current_bid:
            self.bid_history.append(current_bid)

        opponent = [p for p in self.players if p.name != self.name][0]

        # First, interpret opponent's last action if there was one
        if current_bid:
            self.interpretative_tom(opponent.name, current_bid)

        # Then, predict opponent's next action
        prediction = self.predictive_tom(opponent.name, current_bid)

        # Make decision based on both interpretative and predictive insights
        if not current_bid:
            return self._make_opening_bid()

        if prediction["challenge_probability"] > 0.6:
            return self._make_safe_bid(current_bid)
        else:
            return self._make_strategic_bid(current_bid, prediction)

    def _make_opening_bid(self) -> Bid:
        """Make an opening bid based on known dice"""
        known_dice = self.dice.values
        wild_count = known_dice.count(1)
        face_counts = {i: known_dice.count(i) + wild_count for i in range(2, 7)}
        face_counts[1] = wild_count
        most_common_face = max(face_counts, key=face_counts.get)
        return Bid(count=max(1, face_counts[most_common_face]), face=most_common_face)

    def _make_safe_bid(self, current_bid: Bid) -> Bid:
        """Make a conservative bid when we predict opponent might challenge"""
        known_dice = self.dice.values
        wild_count = known_dice.count(1)
        matching_dice = known_dice.count(current_bid.face) + wild_count

        if matching_dice >= current_bid.count:
            return Bid(current_bid.count + 1, current_bid.face)
        else:
            return Bid(current_bid.count, current_bid.face)

    def _make_strategic_bid(self, current_bid: Bid, prediction: dict) -> Bid:
        """Make a bid based on prediction and known dice"""
        known_dice = self.dice.values
        wild_count = known_dice.count(1)

        # If we have a strong hand, be more aggressive
        matching_dice = known_dice.count(current_bid.face) + wild_count
        if matching_dice >= current_bid.count:
            return Bid(current_bid.count + 2, current_bid.face)

        # Otherwise, make a moderate raise
        return Bid(current_bid.count + 1, current_bid.face)

    def decide_challenge(self, current_bid: Bid, total_players: int) -> bool:
        """Decide whether to challenge using first-order ToM"""
        opponent = [p for p in self.players if p.name != self.name][0]

        # Use our opponent model to inform challenge decision
        model = self.opponent_models[opponent.name]["models"]
        best_model = max(model.items(), key=lambda x: x[1]["weight"])

        # Calculate basic probability
        total_dice = sum(p.num_dice for p in self.players)
        expected_dice = total_dice / 6 + total_dice / 6  # Face + Wilds

        # Adjust threshold based on opponent model
        threshold = 1.3
        if best_model[0] == "aggressive":
            threshold *= 0.9
        elif best_model[0] == "conservative":
            threshold *= 1.1

        return current_bid.count > expected_dice * threshold
