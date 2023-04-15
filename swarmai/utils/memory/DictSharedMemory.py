import os
import threading
import json
import uuid
from pathlib import Path
import datetime

class DictSharedMemory():
    """Super simple shared memory implementation that uses a dictionary to store the entries.
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
            data[entry_id] = {"agent":agent_id, "epoch": epoch, "score": score, "cycle": agent_cycle, "content": entry}
            status = self.write_to_file(data)
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