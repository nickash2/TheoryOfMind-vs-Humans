# Wild Perudo with Theory Of Mind Agents
In Wild Perudo, gameplay retains the bluffing and bidding mechanics of Perudo; players bid on the aggregate face values of dice, considering that ones are wild and count as any value, making them an important element in satisfying bids. 

Bets involving ones are doubly potent, outranking other bids based on a weighted scale. If a bid is challenged, all dice are revealed to verify its validity. Unlike traditional Perudo, no players lose dice or are eliminated; instead, outcomes influence a scoring mechanism for agents to adapt their strategies.

The implementations provided is an experiment with Theory Of Mind Agents, in comparison with how they play against human players.

## Requirements
- Python >= 3.10

## Creating the environment

You'll need to create a virtual environment using `venv` first and download the required libraries:

```bash
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```
## Running the code
After that, you can select what players you'd like to play against each other in the `main.py` file `players` list, alongside the `max_rounds` and execute it as follows:

```bash
python3 main.py
```

# Note:
As of now, only `HumanPlayer` and `ZeroOrderPlayer` work as expected, they will be further expanded on in the future!