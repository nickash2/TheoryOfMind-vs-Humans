import pandas as pd
import numpy as np
import matplotlib.pyplot as plt



class DataCollector:
    def __init__(self, data):
        self.data = pd.DataFrame(data, columns=["Player", "Score"])
    

    def save_game_csv(self, directory: str = "data/results.csv"):
        self.data.to_csv(directory, index=False)

    def plot_game(self, directory: str = "data/results.png", plot_type: str = "bar" ):
        fig, ax = plt.subplots()
        if plot_type == "bar":
            self.data.plot(kind="bar", x="Player", y="Score", ax=ax)
        elif plot_type == "line":
            self.data.plot(kind="line", x="Player", y="Score", ax=ax)
        else:
            raise ValueError("Invalid plot type")
        plt.savefig(directory)
