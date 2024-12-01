
# Requirements
- Python >=3.10
## Creating the environment

You'd need to create a virtual environment using `venv` first, as I use some external libraries essential for running the code.

```bash
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```
## Running the code
After that, you can select what players you'd like to play against each other in the `main.py` file, alongside the max rounds and execute it as follows:

```bash
python3 main.py
```

# Note:
As of now, only `HumanPlayer` and `ZeroOrderPlayer` work as expected, they will be further expanded on, in the future!