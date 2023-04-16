import os
import threading
import json
import uuid
from pathlib import Path
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') # need a different backend for multithreading
import numpy as np

class DictSharedMemory():
    """The simplest most stupid shared memory implementation that uses json to store the entries.
    """

    def __init__(self, file_loc=None):
        """Initialize the shared memory. In the current architecture the memory always consists of a set of soltuions or evaluations.
        Moreover, the project is designed around LLMs for the proof of concepts, so we treat all entry content as a string.
        """
        if file_loc is not None:
            self.file_loc = Path(file_loc)
            if not self.file_loc.exists():
                self.file_loc.touch()

        self.lock = threading.Lock()

    def add_entry(self, score, agent_id, agent_cycle, entry):
        """Add an entry to the internal memory.
        """
        with self.lock:
            entry_id = str(uuid.uuid4())
            data = {}
            epoch = datetime.datetime.utcfromtimestamp(0)
            epoch = (datetime.datetime.utcnow() - epoch).total_seconds()
            data[entry_id] = {"agent":agent_id, "epoch": epoch, "score": score, "cycle": agent_cycle, "content": entry}
            status = self.write_to_file(data)
            self.plot_performance()
            return status
    
    def get_top_n(self, n):
        """Get the top n entries from the internal memory.
        """
        raise NotImplementedError
    
    def write_to_file(self, data):
        """Write the internal memory to a file.
        """
        if self.file_loc is not None:
            with open(self.file_loc, "r") as f:
                try:
                    file_data = json.load(f)
                except:
                    file_data = {}

            file_data = file_data | data
            with open(self.file_loc, "w") as f:
                json.dump(file_data, f, indent=4)

                f.flush()
                os.fsync(f.fileno())


            return True
        
    def plot_performance(self):
        """Plot the performance of the swarm.
        TODO: move it to the logger
        """
        with open(self.file_loc, "r") as f:
            shared_memory = json.load(f)
            # f.flush()
            # os.fsync(f.fileno())

        df = pd.DataFrame.from_dict(shared_memory, orient="index")
        df["agent"] = df["agent"].astype(int)
        df["epoch"] = df["epoch"].astype(float)
        df["score"] = df["score"].astype(float)
        df["cycle"] = df["cycle"].astype(int)
        df["content"] = df["content"].astype(str)

        fig = plt.figure(figsize=(20, 5))
        df = df.sort_values(by="epoch")
        df = df.sort_values(by="epoch")

        x = df["epoch"].values - df["epoch"].min()
        y = df["score"].values

        # apply moving average
        if len(y) < 20:
            window_size = len(y)
        else:
            window_size = len(y)//10
        try:
            y_padded = np.pad(y, (window_size//2, window_size//2), mode="reflect")
            y_ma = np.convolve(y_padded, np.ones(window_size)/window_size, mode="same")
            y_ma = y_ma[window_size//2:-window_size//2]

            #moving max
            y_max_t = [np.max(y[:i]) for i in range(1, len(y)+1)]

            plt.plot(x, y_ma, label="Average score of recently submitted solutions")
            plt.plot(x, y_max_t, label="Best at time t")
            plt.plot()
            plt.ylim([0, 1.02])
            plt.xlabel("Time (s)")
            plt.ylabel("Score")
            plt.legend()
            plt.title("Average score of recently submitted solutions")
            plt.tight_layout()
            plt.savefig(self.file_loc.parent / "performance.png")
        except:
            pass

        plt.close(fig)
